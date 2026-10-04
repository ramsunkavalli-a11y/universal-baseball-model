"""Append the intended Maitan case without changing sealed forecasts or runner."""
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.storage import sha256_file
from score_hitter_prospect_pooling_v54 import linear_trace
from score_hitter_numeric_repair_v53 import ridge_trace
from prepare_practical_hitter_v33 import safe_matrix
import evaluate_hitter_smooth_preseason_v73 as e


def case(row,q,f,old,profiles,history,pre,selection):
    r=row.row(0,named=True);rid=r['row_id'];current=f.filter(pl.col('row_id')==rid);before=old.filter(pl.col('row_id')==rid)
    n=e.read(e.OUT/f"fit-{r['origin_year']}-{r['outer_fold']}.json");traces={};probes={}
    with threadpool_limits(limits=2):
        for h in n['heads']:
            traces[h['head']]={}
            for a,path,hsh,frame in [('smooth_preseason',h['path'],h['sha256'],current),('old_smooth',h['old_path'],h['old_sha256'],before)]:
                assert sha256_file(e.Path(path))==hsh
                traces[h['head']][a]=linear_trace(joblib.load(path),frame.select(pre['features']).to_numpy()[0],pre['features'],h['head']=='participation')
            m=joblib.load(h['path']);x=before.select(pre['features']).to_numpy()
            probes[h['head']]=float(m.predict_proba(x)[0,1] if h['head']=='participation' else m.predict(x)[0])
    peers=q.filter((pl.col('prior_debut')==0)&(pl.col('origin_year')==r['origin_year'])&(pl.col('stage')==r['stage'])&(pl.col('player_id')!=r['player_id'])).with_columns(
        (((pl.col('age')-r['age'])/3)**2+((pl.col('minor_pa_0')-r['minor_pa_0'])/250)**2+4*(pl.col('draft_rank')-r['draft_rank'])**2+
         (pl.col('new_scout_rank_score_0')-r['new_scout_rank_score_0'])**2).alias('distance')).sort('distance','player_id').head(4)
    c=dict(origin=r,selection=[selection],information_date=n['information_date'],
        actual_inputs={k:current[k][0] for k in pre['features']},old_scouting=before.select([k for k in pre['features'] if k.startswith('scout_')]).to_dicts()[0],
        new_scouting=current.select([k for k in pre['features'] if k.startswith('scout_')]).to_dicts()[0],saved_traces=traces,
        candidate_fit_with_old_rankings=probes,probe_interpretation='Same fitted candidate with old ranking inputs; mechanics only, not causality or a validated alternative.',
        source_history=history.filter((pl.col('player_id')==r['player_id'])&pl.col('season').is_between(r['origin_year']-2,r['origin_year'])).sort('season','bucket').to_dicts(),
        actual_history=history.filter((pl.col('player_id')==r['player_id'])&(pl.col('season')==r['target_year'])&(pl.col('bucket')=='MLB')).to_dicts(),
        training_profiles=profiles.filter(pl.col('row_id')==rid).to_dicts(),peers=peers.select('player_id','player_name','age','minor_pa_0','draft_rank',
            *[a+'_'+k for a in e.ARMS for k in ['pa','value']], 'next_pa','next_value').to_dicts())
    return c


def main():
    pre=e.read(e.OUT/'preflight.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(e.Path(p))==h,p
    q=pl.read_parquet(e.OUT/'scored-predictions.parquet');f=pl.read_parquet(e.OUT/'features.parquet')
    old=pl.read_parquet(e.smooth.OUT/'features.parquet');profiles=pl.read_parquet(e.OUT/'profile-support.parquet')
    history=pl.read_parquet(e.ROOT/'reports/generated/practical-hitter-v31/counts.parquet')
    row=q.filter((pl.col('player_id')==670867)&(pl.col('origin_year')==2017))
    assert len(row)==1 and row['player_name'][0]=='Kevin Maitan'
    extreme=q.filter(pl.col('prior_debut')==0).sort('smooth_preseason_raw_conditional_pa',descending=True).head(1)
    cases=[case(row,q,f,old,profiles,history,pre,'intended fixed Maitan case; ID correction documented separately'),
        case(extreme,q,f,old,profiles,history,pre,'ordered largest raw conditional PA; boundary and rare-column review')]
    e.write('additional-cases.json',cases)
    rate_root=e.ROOT/'reports/generated/practical-hitter-numeric-repair-v53'
    rp=e.read(rate_root/'preflight.json');rate_source=pl.read_parquet(rate_root/'features.parquet');rate_cases=[]
    for c in e.read(e.OUT/'cases.json')+cases:
        r=c['origin'];row=rate_source.filter(pl.col('row_id')==r['row_id'])
        h=next(h for h in e.read(rate_root/f"fit-{r['origin_year']}-{r['outer_fold']}.json")['heads'] if h['head']=='rate')
        assert sha256_file(e.Path(h['path']))==h['sha256']
        t=ridge_trace(joblib.load(h['path']),safe_matrix(row,rp['rate_features'])[0],rp['rate_features'])
        assert np.isclose(t['raw_prediction'],r['baseline_rate'],atol=1e-10,rtol=0)
        rate_cases.append(dict(player_id=r['player_id'],origin_year=r['origin_year'],player=r['player_name'],row_id=r['row_id'],
            actual_source_inputs={k:row[k][0] for k in rp['rate_features']},trace=t,head_path=h['path'],head_sha256=h['sha256']))
    e.write('fixed-hitting-traces.json',dict(cases=rate_cases,source_hashes={str(p):sha256_file(p) for p in [rate_root/'preflight.json',rate_root/'features.parquet',
        e.ROOT/'scripts/score_hitter_numeric_repair_v53.py',e.ROOT/'scripts/prepare_practical_hitter_v33.py']}))
    print('Maitan and ordered boundary case appended; original Burger case and every forecast retained.',flush=True)


if __name__=='__main__':main()
