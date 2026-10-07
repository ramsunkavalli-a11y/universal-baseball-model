"""Record reviewed integration and exact positional budget accounting, not deployment."""
from pathlib import Path
import json

import polars as pl

from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections,save

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/generated/defense-value-v12'
PUBLIC=ROOT/'reports/model-evidence/defense-value-v12'


def read(p):return json.loads(p.read_text(encoding='utf8'))


def main():
    protections();assert not (OUT/'final-review.json').exists()
    pre=read(OUT/'preflight.json');report=read(OUT/'report.json');verified=read(OUT/'independent-verification.json');walk=read(OUT/'player-walkthrough.json')
    for receipt in (pre,verified,walk):
        for group in ('hashes','output_hashes'):
            for p,h in receipt.get(group,{}).items():assert sha256_file(Path(p))==h,p
    assert walk['focal_cases']==19 and walk['records']==76 and walk['preserved_source_records']==36
    assert verified['all_six_person_bootstrap_intervals_replayed'] and verified['replacement_not_added_twice']
    doc=ROOT/'docs/defense-value-v12-player-review.md';resultdoc=ROOT/'docs/defense-value-v12-result.md'
    text=doc.read_text(encoding='utf8')
    assert all(x in text for x in ('Bailey','Realmuto','Raleigh','Murphy','Ruiz','Rafaela','Kwan','Smith','Judge','Acuña'))
    q=pl.read_parquet(ROOT/'reports/generated/defense-transition-v10/predictions.parquet')
    sourcepath=ROOT/'reports/generated/defense-position-opportunity-v7/source.parquet';source=pl.read_parquet(sourcepath)
    accounting=[];rates={2:12.5,3:-12.5,4:2.5,5:2.5,6:7.5,7:-7.5,8:2.5,9:-7.5,10:-17.5}
    for year in (2023,2024,2025):
        rows=q.filter(pl.col('target_year')==year);slots=[]
        full=source.filter(pl.col('is_mlb')&(pl.col('season')==year)&pl.col('position_code').is_in([str(p) for p in range(2,10)]))['fielding_outs'].sum()
        actual=sum(rows[f'actual_{p}'].sum() for p in range(2,10))
        for p,rate in rates.items():
            denom=162. if p==10 else 4374.
            actualcount=float(rows[f'actual_{p}'].sum())
            slot=dict(position=p,unit='DH starts approximation' if p==10 else 'fielding outs',actual_exposure=actualcount,
                actual_position_runs=actualcount*rate/denom)
            for arm in ('ratio','repair','transition'):
                count=float(rows[f'{arm}_{p}'].sum());slot[arm+'_exposure']=count
                slot[arm+'_position_runs']=count*rate/denom
                slot[arm+'_position_surplus_runs']=(count-actualcount)*rate/denom
            slots.append(slot)
        accounting.append(dict(target_year=year,matched_fielding_outs=actual,full_MLB_fielding_outs=int(full),
            omitted_fielding_outs=int(full)-actual,coverage_fraction=actual/full,slots=slots,
            actual_position_runs=sum(s['actual_position_runs'] for s in slots),
            predicted_position_runs={a:sum(s[a+'_position_runs'] for s in slots) for a in ('ratio','repair','transition')}))
    for d in (OUT,PUBLIC):save(d/'cohort-accounting.json',dict(years=accounting,forecast_rows=12432,
        source_scope='Whole fixed cohort, independent of complete-native measurement subset. No full-WAR target or cohort forcing.',
        source_hash=sha256_file(sourcepath),fits=0))
    primary=report['paired_intervals'][0];value=report['paired_intervals'][2]
    result=dict(player_walkthrough_status='complete',focal_cases=19,peer_records=57,
        execution_integrity_pass=True,MLB_history_skill_delivery_improvement=True,
        primary_defense_RMSE_difference=primary['mean_origin_RMSE_difference'],primary_defense_interval=primary['interval_95'],
        primary_expanded_value_RMSE_difference=value['mean_origin_RMSE_difference'],primary_expanded_interval=value['interval_95'],
        primary_source_measurement_scope='Complete defined-native subset only; all forecasts and partial participants retained.',
        positional_budget_reasonability_pass=False,lower_minors_skill_transport_validated=False,universal_calibration_approved=False,
        deployment_approved=False,full_WAR_claim=False,model_fits=0,protected_outcomes_used=False,forecast_or_explorer_changed=False,
        disposition='Retain useful qualified MLB history and modular research integration; fix position/DH budget, sparse transfer and current research export before complete defense layer.',
        hashes={str(p):sha256_file(p) for p in [Path(__file__),doc,resultdoc,OUT/'preflight.json',OUT/'report.json',OUT/'independent-verification.json',
            OUT/'player-walkthrough.json',OUT/'cohort-accounting.json',OUT/'predictions.parquet',OUT/'channel-predictions.parquet']})
    for d in (OUT,PUBLIC):save(d/'final-review.json',result)
    protections();print(json.dumps(result))


if __name__=='__main__':main()
