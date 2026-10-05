"""Account for every dated roster identity outside the declared hitter cohort."""
from pathlib import Path
import json
import gzip
import polars as pl
from universal_baseball.storage import sha256_file
from assemble_hitter_base_inputs_2025 import OLD

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/generated/hitter-forecast-population-2025-review'


def write(p,o):
    assert not p.exists(),f'Preserve {p}'
    p.write_text(json.dumps(o,indent=2,allow_nan=False,default=str)+'\n',encoding='utf8',newline='\n')


def main():
    OUT.mkdir(parents=True,exist_ok=True);assert not (OUT/'review.json').exists()
    roster_path=ROOT/'reports/generated/hitter-rosters-2025-source/year-end-2025.parquet'
    membership_path=ROOT/'reports/generated/hitter-base-inputs-2025/membership.parquet'
    pitcher_path=OLD/'opportunity-history-sources-v2/tables/pitcher_snapshots.parquet'
    hitter_path=OLD/'opportunity-history-sources-v2/tables/hitter_snapshots.parquet'
    roster=pl.read_parquet(roster_path);members=pl.read_parquet(membership_path)
    pitchers=pl.read_parquet(pitcher_path).filter(pl.col('snapshot_year')==2025);hitters=pl.read_parquet(hitter_path)
    outside=roster.join(members.select('player_id'),on='player_id',how='anti')
    pitcher_ids=set(pitchers['player_id']);source_paths=[roster_path,membership_path,pitcher_path,hitter_path,Path(__file__),
        ROOT/'docs/hitter-2025-availability-source-contract.md'];dated={}
    for p in sorted((roster_path.parent/'captures').glob('*-2025-12-31.json.gz')):
        source_paths.append(p)
        with gzip.open(p,'rt',encoding='utf8') as f:payload=json.load(f)
        for r in payload['roster']:
            pid=r['person']['id']
            if pid in set(outside['player_id']):
                assert pid not in dated,'Conflicting roster identity'
                dated[pid]=dict(source_path=str(p),player_name=r['person']['fullName'],
                    roster_position_code=r['position']['code'],parent_team_id=r.get('parentTeamId'),
                    roster_status=r['status']['code'])
    assert set(dated)==set(outside['player_id'])
    rows=[]
    for r in outside.iter_rows(named=True):
        pid=r['player_id'];e=dated[pid]
        status=('saved_2025_pitcher_role' if pid in pitcher_ids else 'dated_roster_pitcher_hint_no_2025_role_snapshot'
                if e['roster_position_code']=='1' else 'unmodeled_nonpitcher_entrant_or_returner')
        history=hitters.filter((pl.col('player_id')==pid)&(pl.col('snapshot_year')<=2025))
        rows.append(dict(**r,**e,coverage_class=status,prior_hitter_snapshot_rows=history.height,
            interpretation='Not a hitter candidate by saved pitcher role; incidental batting is not admission.' if pid in pitcher_ids else
                'Dated roster position is a role hint, not certified historical talent or a current-person position lookup.'
                if e['roster_position_code']=='1' else 'Known rostered non-pitcher outside domestic hitter eligibility. Talent forecast remains missing, not zero.'))
    ledger=pl.DataFrame(rows);ledger.write_parquet(OUT/'roster-outside-ledger.parquet')
    gaps=[r for r in rows if r['coverage_class']=='unmodeled_nonpitcher_entrant_or_returner']
    assert {r['player_id'] for r in gaps}=={592122,823550,808959}
    assert len(outside)==670 and sum(r['coverage_class']=='saved_2025_pitcher_role' for r in rows)==662
    mixed=members.join(pitchers.select('player_id'),on='player_id',validate='1:1')
    mixed.write_parquet(OUT/'mixed-role-members.parquet')
    write(OUT/'known-coverage-gaps.json',dict(players=gaps,interpretation='These gaps are not eligible zero forecasts or evidence of no MLB ability.',
        later_January_signings='Not inventoried by a December-31 population; any later additions must use origin-known evidence and remain separate.',
        foreign_talent_model_certified=False,protected_outcomes_used=False))
    write(OUT/'review.json',dict(fixed_hitter_population=4030,year_end_roster_members=1175,roster_members_inside=505,
        roster_members_outside=670,saved_pitcher_role_outside=662,dated_roster_pitcher_hint_outside=5,
        unmodeled_nonpitcher_rostered=3,mixed_role_inside=len(mixed),membership_changed=False,
        source_player_walkthrough_status='complete_for_membership_classification',universal_coverage_claim_allowed=False,
        qualification='December-31 domestic-history hitter universe plus continued recent-debut exits. Newly rostered foreign hitters are explicit missing forecasts; January additions are not inventoried.',
        candidate_fitted=False,candidate_frozen=False,protected_outcomes_used=False,
        input_hashes={str(p):sha256_file(p) for p in source_paths},
        output_hashes={str(p):sha256_file(p) for p in OUT.iterdir() if p.suffix in ['.json','.parquet']}))
    print(f'All 670 roster identities outside cohort accounted for; three unmodeled non-pitchers: {[r["player_name"] for r in gaps]}.',flush=True)


if __name__=='__main__':main()
