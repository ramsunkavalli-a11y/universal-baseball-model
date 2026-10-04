"""Add a genuinely ordinary case when value-selected success hides cancellation."""
import json
import joblib
import numpy as np
import polars as pl
from pathlib import Path
from threadpoolctl import threadpool_limits
from evaluate_hitter_prospect_workload_specialization import OUT, EARLIER, ROOT, read, write, verify, profile, highest, distance, trace, NEW
from universal_baseball.storage import sha256_file


def main():
    assert not (OUT/'ordinary-case-supplement.json').exists(), 'Preserve supplemental case'
    pre = read(OUT/'preflight.json'); verify(pre['input_hashes'])
    verify(read(OUT/'review-preparation.json')['hashes'])
    q = pl.read_parquet(OUT/'scored-predictions.parquet')
    eligible = q.filter((pl.col('prior_debut')==0)&pl.col('next_pa').is_between(100,600)&
        (abs(pl.col('baseline_rate')-pl.col('realized_season_rate'))<.5)&
        pl.all_horizontal([abs(pl.col(a+'_pa')-pl.col('next_pa'))<30 for a in ['preseason',*NEW]])).sort('row_id')
    assert len(eligible)
    result = eligible.row(0,named=True)
    f = profile(pl.read_parquet(EARLIER/'features.parquet'))
    f = f.with_columns(pl.Series('highest_level',[highest(r) for r in f.iter_rows(named=True)]))
    row = f.filter(pl.col('row_id')==result['row_id']); o = row.row(0,named=True)
    c = next(c for c in pre['cells'] if c['year']==o['origin_year'] and c['fold']==o['outer_fold'])
    paths = {}
    with threadpool_limits(limits=2):
        for history in ['restricted','extended']:
            for arm,h in [('preseason' if history=='restricted' else 'pooled_extended',c['controls'][history]),
                          ('prospect_'+history,read(OUT/f"prospect_{history}-{o['origin_year']}-{o['outer_fold']}.json"))]:
                verify({h['path']:h['sha256']})
                paths[arm] = trace(joblib.load(h['path']),row.select(pre['features']).to_numpy()[0],pre['features'])
                assert np.isclose(paths[arm]['raw_prediction'],result[arm+'_raw_conditional_pa'],atol=1e-8,rtol=0)
    peers = f.filter((pl.col('origin_year')==o['origin_year'])&(pl.col('prior_debut')==0)&
        (pl.col('dominant_level')==o['dominant_level'])&(pl.col('highest_level')==o['highest_level'])&
        (abs(pl.col('age')-o['age'])<=2)&(pl.col('age_unknown')==o['age_unknown'])&(pl.col('player_id')!=o['player_id']))
    peers = peers.with_columns(distance(peers,o).alias('distance')).sort('distance','player_id').head(4)
    peer_cols = ['row_id','player_id','player_name','origin_year','age','source_position','dominant_level','highest_level',
        'minor_pa_0','scout_rank_score_0','draft_rank','distance']
    peers = peers.select(peer_cols).join(q.select('row_id','preseason_pa',*[a+'_pa' for a in NEW],'next_pa','next_value'),on='row_id',validate='1:1').to_dicts()
    stints = pl.read_parquet(ROOT/'reports/generated/practical-hitter-v31/dated-stints.parquet')
    support = pl.read_parquet(OUT/'profile-support.parquet').filter(pl.col('row_id')==o['row_id'])
    out = dict(selection=dict(row_id=o['row_id'],eligible_rows=len(eligible),rule='First row ID with 100–600 actual PA, all three expected-PA errors below 30 and current rate error below .5 wins/600. Post-fit diagnostic only, no forecast change.'),
        origin=o,actual_inputs=row.select(pre['features']).row(0,named=True),
        dated_stats=stints.filter((pl.col('player_id')==o['player_id'])&pl.col('season').is_between(o['origin_year']-2,o['origin_year'])).sort('season','bucket').to_dicts(),
        target_stats=stints.filter((pl.col('player_id')==o['player_id'])&(pl.col('season')==o['target_year'])&(pl.col('bucket')=='MLB')).to_dicts(),
        forecasts={a:{v:result[a+'_'+v] for v in ['pa','conditional_pa','value']} for a in ['preseason','pooled_extended',*NEW]},
        fixed_probability=result['preseason_p'],fixed_batting_rate=result['baseline_rate'],
        reality={v:result[v] for v in ['next_pa','next_value','realized_season_rate']},saved_paths=paths,
        actual_fold_support=support.to_dicts(),peers=peers,mechanism_not_causality=True,
        hashes={str(p):sha256_file(p) for p in [OUT/'preflight.json',OUT/'scored-predictions.parquet',OUT/'cases.json',Path(__file__)]})
    write('ordinary-case-supplement.json',out)
    print(json.dumps({k:v for k,v in out.items() if k not in ['origin','actual_inputs','dated_stats','target_stats','saved_paths','hashes']},indent=2))
    print(json.dumps(dict(name=o['player_name'],origin_year=o['origin_year'],stats=[{k:s[k] for k in ['season','bucket','plate_appearances','home_runs','unintentional_walks','strike_outs']} for s in out['dated_stats']],
        top_paths={a:dict(reference=p['reference'],effects=p['feature_effects'][:5]) for a,p in paths.items()}),indent=2))


if __name__=='__main__':main()
