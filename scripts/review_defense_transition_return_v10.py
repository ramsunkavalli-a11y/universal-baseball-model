"""Complete the sole recovered role trace and outcome-blind return comparisons."""

import polars as pl

from universal_baseball.defense_transition import allocate
from universal_baseball.storage import sha256_file
from run_defense_transition_v10 import OUT,PUBLIC,SOURCE,read,check
from run_hitter_finite_return_baseline import save


def main():
    check();q=pl.read_parquet(OUT/'predictions.parquet');records=q.to_dicts()
    focal=next(r for r in records if r['player_id']==656847 and r['origin_year']==2023)
    pool=[r for r in records if r['origin_year']==2023 and r['player_id']!=656847
          and r['transition_returning_history'] and r['transition_primary_role']==focal['transition_primary_role']]
    peers=sorted(pool,key=lambda r:(abs((r['age'] or 27)-(focal['age'] or 27)),
          abs(r['transition_evidence_PA']-focal['transition_evidence_PA']),r['row_id']))[:3]
    source=pl.read_parquet(SOURCE/'source.parquet');traces=[]
    for r in [focal,*peers]:
        model=read(OUT/f"model-{r['origin_year']}-{r['outer_fold']}.json")
        traces.append(dict(player_id=r['player_id'],player_name=r['player_name'],origin=r['origin_year'],age=r['age'],stage=r['stage'],
            current_PA=r['pa_0'],previous_PA=[r['pa_1'],r['pa_2']],expected_PA=r['preseason_pa'],actual_PA=r['next_pa'],
            original_unknown=r['repertoire_unknown'],transition_inputs={n:v for n,v in r.items() if n.startswith('transition_') and not n.startswith('transition_native_')},
            origin_rows=source.filter((pl.col('player_id')==r['player_id'])&pl.col('season').is_between(2021,2023)).to_dicts(),
            calculation=allocate(r,{tuple(t['key']):t for t in model['tables']}),
            actuals={str(p):r[f'actual_{p}'] for p in range(2,11)}))
    result=dict(selection='Sole recovered formerly unknown repertoire; same-origin returning dominant-role peers nearest by known age then MLB evidence PA, no future filter.',
        records=traces,first_partial_receipt='source-recovery-review.json contains only the focal record; this separate four-record review completes its announced comparisons.',
        forecast_parameters_unchanged=True,protected_outcomes_used=False,
        hashes={str(OUT/'predictions.parquet'):sha256_file(OUT/'predictions.parquet')})
    save(OUT/'return-history-review.json',result);save(PUBLIC/'return-history-review.json',result)
    print([(r['player_name'],r['expected_PA'],r['actual_PA'],r['calculation']['values'],r['actuals']) for r in traces])


if __name__=='__main__':main()
