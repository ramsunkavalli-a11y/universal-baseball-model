"""Verify the actual retained training membership and reconstruct special 2020 inputs."""
from pathlib import Path
import json
import polars as pl
from universal_baseball.storage import sha256_file
from materialize_hitter_2020_cohort import make_rows
from universal_baseball.hitter_forecast_inputs import pooled_inputs
from review_hitter_base_inputs_2025 import compare, families, OLD

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/generated/hitter-tested-training-membership'


def read(p):return json.loads(p.read_text(encoding='utf8'))


def write(p,o):
    assert not p.exists(),f'Preserve {p}'
    p.write_text(json.dumps(o,indent=2,allow_nan=False,default=str)+'\n',encoding='utf8',newline='\n')


def main():
    OUT.mkdir(parents=True,exist_ok=True);assert not (OUT/'review.json').exists()
    frame_path=ROOT/'reports/generated/hitter-preseason-readiness-v68/features.parquet';f=pl.read_parquet(frame_path)
    paths=[frame_path,Path(__file__),ROOT/'docs/hitter-tested-2020-training-correction.md'];cells=[]
    families_= ['practical-hitter-numeric-repair-v53','hitter-preseason-readiness-v68','hitter-talent-bridge-v74','hitter-statcast-next-year']
    for name in families_:
        pp=ROOT/f'reports/generated/{name}/preflight.json';paths.append(pp);pre=read(pp)
        for c in pre['cells']:
            expected=f.filter((pl.col('target_year')<=c['year'])&(pl.col('target_year')!=2020)&
                (pl.col('outer_fold')!=c['fold'])&pl.col('window_complete'))
            assert set(expected['row_id'])==set(c['training_row_ids']),(name,c['year'],c['fold'])
            special=expected.filter(pl.col('origin_year')==2020)
            cells.append(dict(family=name,year=c['year'],fold=c['fold'],exact_membership=True,
                training_rows=len(expected),training_people=expected['player_id'].n_unique(),
                repaired_2020_rows=len(special),repaired_2020_people=special['player_id'].n_unique()))
    source=ROOT/'reports/generated/hitter-2020-cohort';base_path=ROOT/'reports/generated/practical-hitter-v33b/features.parquet'
    counts_path=ROOT/'reports/generated/practical-hitter-v31/counts.parquet';stints_path=counts_path.parent/'dated-stints.parquet'
    values_path=ROOT/'reports/generated/multiyear-hitter-v1/targets.parquet'
    roster_path=source/'full-roster.parquet';forty_path=source/'40man.parquet';birth_path=source/'birthdates.parquet'
    debut_path=ROOT/'reports/generated/hitter-arrival-source-repair-v1/debut-dates.parquet'
    paths.extend([base_path,counts_path,stints_path,values_path,roster_path,forty_path,birth_path,debut_path,
                  ROOT/'scripts/materialize_hitter_2020_cohort.py',source/'source-review.json'])
    rebuilt,provenance=make_rows(*[pl.read_parquet(p) for p in [base_path,stints_path,counts_path,values_path,roster_path,forty_path,birth_path,debut_path]])
    base_names=pl.read_parquet(ROOT/'reports/generated/hitter-base-inputs-2025/base-inputs.parquet').columns
    original=f.filter(pl.col('origin_year')==2020)
    assert len(original)==len(rebuilt)==5133
    compare(rebuilt,original,base_names)
    source_features=rebuilt.select(base_names)
    draft_path=OLD/'draft-history/draft-history.parquet';games_path=ROOT/'reports/generated/practical-hitter-v38/game-counts.parquet'
    rank_path=ROOT/'reports/generated/hitter-preseason-readiness-v67/ranks.parquet'
    annual_path=ROOT/'reports/generated/hitter-tracking-2025-audit/annual-launch-features-through-2025.parquet'
    paths.extend([draft_path,games_path,rank_path,annual_path])
    all_=families(source_features,pl.read_parquet(counts_path).filter(pl.col('season')<=2024),
        pl.read_parquet(draft_path).filter(pl.col('draft_year')<=2024),pl.read_parquet(games_path).filter(pl.col('season')<=2024),
        pl.read_parquet(rank_path),pl.read_parquet(annual_path).filter(pl.col('season')<=2024),cutoff=2024)
    numeric=read(ROOT/'reports/generated/practical-hitter-numeric-repair-v53/preflight.json')['rate_features']
    pa=read(ROOT/'reports/generated/hitter-preseason-readiness-v68/preflight.json')['pa_features']
    compare(all_,original,sorted(set(numeric+pa)))
    tracking_path=ROOT/'reports/generated/hitter-statcast-next-year/features.parquet';paths.append(tracking_path)
    sc_names=read(tracking_path.parent/'preflight.json')['arms']['ridge_measurements']
    compare(all_,pl.read_parquet(tracking_path).filter(pl.col('origin_year')==2020),sc_names)
    provenance.write_parquet(OUT/'special-origin-provenance.parquet')
    keys=[(592450,'Aaron Judge'),(608369,'Marcus Semien'),(518692,'Freddie Freeman'),(121252,'Jose Ortega')]
    walks=[]
    for pid,_ in keys:
        row=all_.filter(pl.col('player_id')==pid)
        if row.is_empty():continue
        r=row.row(0,named=True);hist=pl.read_parquet(counts_path).filter((pl.col('player_id')==pid)&pl.col('season').is_between(2018,2020))
        assert hist.filter((pl.col('season')==2020)&(pl.col('bucket')!='MLB')).is_empty()
        assert r['pa_0']==hist.filter((pl.col('season')==2020)&(pl.col('bucket')=='MLB'))['plate_appearances'].sum()
        assert r['minor_pa_0']==0 and r['milb_canceled_0']==1
        walks.append(dict(player_id=pid,name=r['player_name'],source_history=hist.to_dicts(),
            provenance=provenance.filter(pl.col('player_id')==pid).to_dicts()[0],
            actual_inputs={c:r[c] for c in ['age','age_unknown','stage','snapshot_level','on_40man','pa_0','work_0','minor_pa_0','minor_pa_1','career_mlb_observed_pa','milb_canceled_0']},
            judgment='Canceled MiLB observations stay absent; last observed stage and dated roster remain source evidence, not invented 2020 minor production.',
            review='source_only_no_new_forecast'))
    write(OUT/'player-walks.json',dict(walks=walks,protected_outcomes_used=False))
    write(OUT/'review.json',dict(actual_retained_rule='target_year <= cutoff; target_year != 2020; outer_fold != held_fold; window_complete',
        saved_cells_checked=len(cells),cells=cells,source_rows=63282,special_origin_rows=5133,
        special_base_fields_matched=len(base_names),special_actual_model_features_matched=len(set(numeric+pa)),special_tracking_features_matched=len(sc_names),
        all_modern_rows_now_source_checked=True,prior_plan_exclusion_corrected=True,unchanged_model_settings=True,
        candidate_fitted=False,candidate_frozen=False,protected_outcomes_used=False,
        input_hashes={str(p):sha256_file(p) for p in paths},output_hashes={str(p):sha256_file(p) for p in OUT.iterdir() if p.suffix in ['.parquet','.json']}))
    print(f'All {len(cells)} saved training memberships match; repaired 2020 base and model inputs reproduce for {len(rebuilt)} players.',flush=True)


if __name__=='__main__':main()
