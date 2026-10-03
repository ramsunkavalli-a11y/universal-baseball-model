"""Replay, score and prepare actual player evidence for the fixed vintage test."""
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.practical_hitter_v30 import score
from universal_baseball.histogram_prediction_trace import trace
from universal_baseball.storage import sha256_file
from score_practical_hitter_v31 import paired
from score_hitter_readiness_v49 import probability_score
from evaluate_hitter_readiness_v49 import logit_trace
import evaluate_hitter_preseason_readiness_v68 as e

def main():
    pre=e.read(e.OUT/'preflight.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    source=pl.read_parquet(e.OUT/'features.parquet');old=pl.read_parquet(e.base.OUT/'features.parquet')
    baseline=pl.read_parquet(e.VALUE/'scored-predictions.parquet').sort('row_id');q=pl.read_parquet(e.OUT/'predictions.parquet').sort('row_id')
    assert len(q)==30506 and q.select(baseline.columns).equals(baseline) and q['preseason_rate'].equals(q['baseline_rate'])
    replayed=0
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            te=source.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id');before=old.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            f=q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id');n=e.read(e.OUT/f"fit-{c['year']}-{c['fold']}.json")
            for h in n['heads']:
                for arm,path,hsh,frame in [('preseason',h['path'],h['sha256'],te),('baseline',h['baseline_path'],h['baseline_sha256'],before)]:
                    assert sha256_file(Path(path))==hsh;m=joblib.load(path);x=frame.select(pre['pa_features']).to_numpy()
                    pred=m.predict_proba(x)[:,1] if h['head']=='participation' else m.predict(x)
                    col=('preseason_raw_p' if h['head']=='participation' else 'preseason_raw_conditional_pa') if arm=='preseason' else ('repaired_raw_p' if h['head']=='participation' else 'repaired_raw_conditional_pa')
                    assert np.allclose(pred,f[col],rtol=0,atol=1e-10);replayed+=1
            assert np.allclose(f['preseason_pa'],f['preseason_p']*f['preseason_conditional_pa'],rtol=0,atol=1e-10)
            assert np.allclose(f['preseason_value'],f['preseason_pa']*(f['baseline_rate']/600+f['origin_replacement_rate']),rtol=0,atol=1e-10)
            assert f.filter(pl.col('hard_unavailable')|pl.col('reported_retired'))['preseason_pa'].sum()==0
    q=q.join(source.select('row_id',pl.col('scout_listed_0').alias('new_scout_listed_0'),pl.col('scout_rank_score_0').alias('new_scout_rank_score_0')),on='row_id',validate='1:1')
    public=q.filter((pl.col('pa_0')>0)&pl.col('steamer_index').is_not_null()&pl.col('zips_index').is_not_null());assert len(public)==2627
    scopes=[('all',q),('public_broad',public),('never_debut',q.filter(pl.col('prior_debut')==0)),
        ('upper_never_debut',q.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Upper minors'))),
        ('lower_never_debut',q.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Lower minors'))),
        ('current_MLB',q.filter(pl.col('pa_0')>0)),('newly_listed',q.filter((pl.col('scout_listed_0')!=1)&(pl.col('new_scout_listed_0')==1))),
        ('first_year_top_picks',q.filter((pl.col('draft_known')==1)&(pl.col('draft_year')==pl.col('origin_year'))&(pl.col('pick_number')<=15)))]
    scopes += [('origin_'+str(y),q.filter(pl.col('origin_year')==y)) for y in sorted(q['origin_year'].unique())]
    scopes += [('stage_'+s,q.filter(pl.col('stage')==s)) for s in sorted(q['stage'].unique())]
    scores=[];intervals=[]
    with threadpool_limits(limits=2):
        for name,g in scopes:
            if not len(g):continue
            scores.append(dict(scope=name,rows=len(g),people=g['player_id'].n_unique(),actual_pa=float(g['next_pa'].sum()),actual_value=float(g['next_value'].sum()),
                scores={a:score(g,a) for a in ['baseline','preseason']+(['steamer'] if name=='public_broad' else [])},
                probability={a:probability_score(g,a) for a in ['baseline','preseason']}))
            if name in ['all','public_broad','never_debut','upper_never_debut','newly_listed']:
                intervals.extend(dict(scope=name,**paired(g,'preseason','baseline',metric)) for metric in ['pa','value'])
    e.write('scores.json',scores);e.write('intervals.json',intervals);q.write_parquet(e.OUT/'scored-predictions.parquet')
    chosen={}
    def choose(frame,reason):
        assert len(frame);chosen.setdefault(frame['row_id'][0],[]).append(reason)
    for pid,y in e.FIXED:choose(q.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y)),'fixed before fit')
    err=q.with_columns(((pl.col('baseline_value')-pl.col('next_value'))**2-(pl.col('preseason_value')-pl.col('next_value'))**2).alias('gain'),
        (pl.col('preseason_value')-pl.col('next_value')).alias('error'))
    for why,g in [('largest offense gain',err.sort('gain',descending=True)),('largest offense harm',err.sort('gain')),
        ('major false high',err.sort('error',descending=True)),('major false low',err.sort('error')),
        ('ordinary active',err.filter(pl.col('next_pa').is_between(200,600)).sort(pl.col('error').abs()))]:choose(g,why)
    counts=pl.read_parquet(e.ROOT/'reports/generated/practical-hitter-v31/counts.parquet');profiles=pl.read_parquet(e.OUT/'profile-support.parquet');cases=[]
    scout=[n for n in pre['pa_features'] if n.startswith('scout_')]
    with threadpool_limits(limits=2):
        for rid,selection in chosen.items():
            r=q.filter(pl.col('row_id')==rid).row(0,named=True);te=source.filter(pl.col('row_id')==rid);before=old.filter(pl.col('row_id')==rid)
            note=e.read(e.OUT/f"fit-{r['origin_year']}-{r['outer_fold']}.json");traces={};probes={}
            for h in note['heads']:
                traces[h['head']]={}
                for arm,path,frame in [('baseline',h['baseline_path'],before),('preseason',h['path'],te)]:
                    m=joblib.load(path);x=frame.select(pre['pa_features']).to_numpy()[0]
                    traces[h['head']][arm]=logit_trace(m,x,pre['pa_features']) if h['head']=='participation' else trace(m,x,pre['pa_features'])
                m=joblib.load(h['path']);x=before.select(pre['pa_features']).to_numpy()
                probes[h['head']]=float(m.predict_proba(x)[0,1] if h['head']=='participation' else m.predict(x)[0])
            peers=q.filter((pl.col('origin_year')==r['origin_year'])&(pl.col('stage')==r['stage'])&(pl.col('prior_debut')==r['prior_debut'])&(pl.col('player_id')!=r['player_id'])).with_columns(
                (((pl.col('age')-r['age'])/3)**2+((pl.col('minor_pa_0')-r['minor_pa_0'])/250)**2+4*(pl.col('draft_rank')-r['draft_rank'])**2).alias('distance')).sort('distance','player_id').head(4)
            cases.append(dict(origin=r,selection=selection,information_date=note['information_date'],
                old_scouting=before.select(scout).to_dicts()[0],new_scouting=te.select(scout).to_dicts()[0],
                actual_inputs={n:te[n][0] for n in pre['pa_features']},saved_traces=traces,candidate_fit_with_old_rankings=probes,
                probe_interpretation='Fixed fitted model, reverting all twelve ranking-vintage inputs. Mechanics only, not causality or a validated forecast.',
                source_history=counts.filter((pl.col('player_id')==r['player_id'])&pl.col('season').is_between(r['origin_year']-2,r['origin_year'])).sort('season','bucket').to_dicts(),
                actual_history=counts.filter((pl.col('player_id')==r['player_id'])&(pl.col('season')==r['target_year'])&(pl.col('bucket')=='MLB')).to_dicts(),
                training_profiles=profiles.filter(pl.col('row_id')==rid).to_dicts(),
                peers=peers.select('player_id','player_name','age','minor_pa_0','draft_rank','baseline_p','preseason_p','baseline_conditional_pa','preseason_conditional_pa',
                    'baseline_pa','preseason_pa','baseline_value','preseason_value','next_pa','next_value','scout_listed_0','new_scout_listed_0','new_scout_rank_score_0').to_dicts()))
    e.write('cases.json',cases);e.write('verification.json',dict(replayed_heads=replayed,expected_heads=140,unchanged_hitting=True,
        unchanged_baseline_forecasts=True,PA_product_verified=True,corrected_value_verified=True,player_walkthrough_status='pending',cases=len(cases),
        protected_outcomes_used=False,frozen_forecast_changed=False,conditional_clips=int(((q['preseason_raw_conditional_pa']<1)|(q['preseason_raw_conditional_pa']>800)).sum())))
    for s in scores[:8]:print(s['scope'],{a:(round(v['pa_rmse'],3),round(v['pa_mae'],3),round(v['value_rmse'],6),round(v['pa_total'])) for a,v in s['scores'].items()},flush=True)
    print('Scores provisional until actual saved-model player review.',flush=True)

if __name__=='__main__':main()
