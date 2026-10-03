"""Document an actual dated-request counterexample without mutating forecasts."""
import gzip
import json
from pathlib import Path
import polars as pl
import prepare_hitter_joint_forest_v43 as e
from universal_baseball.storage import sha256_file


def main():
    old=e.r.OLD/'opportunity-history-sources-v2'
    raw=old/'captures/2024/full-roster-119.json.gz'
    payload=json.load(gzip.open(raw,'rt',encoding='utf8'))
    row=[s for s in payload['payload']['roster'] if s['person']['id']==808975];assert len(row)==1
    projected=old/'tables/2024/full_roster_details.parquet'
    roster=pl.read_parquet(projected).filter(pl.col('player_id')==808975)
    assert len(roster)==1 and roster['snapshot_year'][0]==2024
    source=pl.read_parquet(e.OUT/'features.parquet')
    stints=e.r.OUT/'dated-stints.parquet'
    first=pl.read_parquet(stints).filter((pl.col('season')<=2024)&(pl.col('plate_appearances')>0)).group_by('player_id').agg(pl.col('season').min().alias('first_observed_year'))
    q=source.join(first,on='player_id',how='left',validate='m:1').with_columns(
        ((pl.col('first_observed_year')<=pl.col('origin_year')).fill_null(False)|(pl.col('prior_debut')==1)|(pl.col('draft_known')==1)).alias('origin_evidence_bridge'))
    q.filter(~pl.col('origin_evidence_bridge')).write_parquet(e.OUT/'roster-only-source-rows.parquet')
    groups=q.group_by('origin_year').agg(pl.len().alias('rows'),(~pl.col('origin_evidence_bridge')).sum().alias('unverified_roster_only_rows'),
        pl.when(~pl.col('origin_evidence_bridge')).then(pl.col('next_pa')).otherwise(0).sum().alias('unverified_next_pa')).sort('origin_year').to_dicts()
    forty=e.r.ROOT/'reports/generated/hitter-arrival-source-repair-v1/year-end-rosters.parquet'
    forty_row=pl.read_parquet(forty).filter((pl.col('season')==2024)&(pl.col('player_id')==808975)).to_dicts()
    e.write('roster-source-audit.json',dict(requested_url=payload['requested_url'],stored_snapshot_date=payload['snapshot_date'],
        raw_returned_row=row,projected_roster_row=roster.to_dicts(),source_feature_row=q.filter((pl.col('origin_year')==2024)&(pl.col('player_id')==808975)).select(
            'row_id','player_id','player_name','age','age_unknown','source_position','team_id','on_40man','draft_known','prior_debut','origin_evidence_bridge','next_pa').to_dicts(),
        separate_40man_row=forty_row,signing_date='2025-01-03',signing_source='https://www.mlb.com/press-release/press-release-dodgers-sign-hyeseong-kim',
        source_hashes={str(p):sha256_file(p) for p in [raw,projected,stints,forty,e.OUT/'features.parquet']},groups=groups,
        eligibility_changed=False,forecast_inputs_changed=False,protected_outcomes_used=False,
        interpretation='FullRoster request date is not sufficient membership proof. No equivalent behavior of 40Man established from this case. Unverified rows retained; origin-supported subset is a qualification diagnostic, not improved eligibility.'))
    print(groups,flush=True)


if __name__=='__main__':main()
