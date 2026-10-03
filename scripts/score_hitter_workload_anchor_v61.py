"""Replay every direct/adjustment head and prepare actual player reviews."""
from datetime import date
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.storage import sha256_file
from universal_baseball.practical_hitter_v30 import score
from universal_baseball.histogram_prediction_trace import trace
from universal_baseball.hitter_observed_return import as_of
from score_practical_hitter_v31 import paired
import evaluate_hitter_workload_anchor_v61 as e

FIXED=[(592450,2022),(592450,2016),(665487,2022),(680574,2024),
       (666158,2023),(677551,2023),(694671,2023),(670541,2022)]


def main():
    pre=e.read(e.OUT/'preflight.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(e.Path(p))==h,p
    f=pl.read_parquet(e.OUT/'features.parquet');q=pl.read_parquet(e.OUT/'predictions.parquet')
    base=pl.read_parquet(e.BASE/'scored-predictions.parquet')
    assert q.select(base.columns).equals(base.sort('row_id'))
    replayed=0;clips={}
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            z=q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            for h in e.read(e.OUT/f"fit-{c['year']}-{c['fold']}.json")['heads']:
                assert sha256_file(e.Path(h['path']))==h['sha256']
                m=joblib.load(h['path']);v=m.predict(te.select(h['features']).to_numpy());a=h['arm']
                assert np.allclose(v,z[a+'_head_output'],atol=1e-10,rtol=0)
                raw=v+(te['workload_reference'].to_numpy()if a=='anchor61'else 0)
                assert np.allclose(raw,z[a+'_raw_pa'],atol=1e-10,rtol=0)
                pred=e.forecast(raw,z['hard_unavailable'].to_numpy()|z['reported_retired'].to_numpy())
                assert np.allclose(pred,z[a+'_pa'],atol=1e-10,rtol=0)
                clips.setdefault(a,[0,0]);clips[a][0]+=h['clip_low'];clips[a][1]+=h['clip_high'];replayed+=1
    assert replayed==70
    enriched=q.join(f.select('row_id',*e.ADDED),on='row_id',validate='1:1')
    pub=q.filter((pl.col('pa_0')>0)&pl.col('steamer_index').is_not_null()&pl.col('zips_index').is_not_null())
    assert len(pub)==2627
    groups=[('all',q),('public_broad',pub),('public_legacy',pub.filter(pl.col('v24_pa').is_not_null())),
        ('current_mlb',q.filter(pl.col('pa_0')>0)),('never_debut',q.filter(pl.col('prior_debut')==0)),
        ('absent_former_regular',q.filter((pl.col('pa_0')==0)&((pl.col('pa_1')>=300)|(pl.col('pa_2')>=300)))),
        ('brief_mlb',q.filter(pl.col('pa_0').is_between(1,199))),
        ('large_regular',q.filter(pl.col('pa_0')>=600))]
    groups += [('origin_'+str(y),q.filter(pl.col('origin_year')==y))for y in sorted(q['origin_year'].unique())]
    groups += [('stage_'+s,q.filter(pl.col('stage')==s))for s in sorted(q['stage'].unique())]
    groups += [(s,enriched.filter(pl.col(s)>0))for s in e.ADDED[2:]]
    scores=[];intervals=[]
    for name,g in groups:
        if not len(g):continue
        arms=['repaired',*e.ARMS]+(['steamer']if name.startswith('public')else [])
        scores.append(dict(scope=name,rows=len(g),people=g['player_id'].n_unique(),
            actual_pa=int(g['next_pa'].sum()),actual_value=float(g['next_value'].sum()),
            scores={a:score(g,a)for a in arms}))
        if name in ['all','public_broad','current_mlb','never_debut','absent_former_regular']:
            for a,b in [('direct61','repaired'),('anchor61','repaired'),('anchor61','direct61')]:
                intervals.extend(dict(scope=name,**paired(g,a,b,metric))for metric in ['pa','value'])
    e.write('scores.json',scores);e.write('intervals.json',intervals)
    chosen={}
    def choose(g,why):
        r=g.row(0,named=True);chosen.setdefault(r['row_id'],[]).append(why)
    for pid,y in FIXED:choose(q.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y)),'fixed diagnostic')
    for a in e.ARMS:
        r=q.with_columns(((pl.col('repaired_value')-pl.col('next_value'))**2-
            (pl.col(a+'_value')-pl.col('next_value'))**2).alias('gain'),
            (pl.col(a+'_value')-pl.col('next_value')).alias('error'))
        for label,g in [('largest delivered gain',r.sort('gain',descending=True)),
            ('largest delivered harm',r.sort('gain')),('false high',r.sort('error',descending=True)),
            ('false low',r.sort('error')),('ordinary',r.filter(pl.col('next_pa').is_between(200,600)).sort(pl.col('error').abs()))]:
            choose(g,a+': '+label)
    raw=pl.read_parquet(e.ROOT/'reports/generated/practical-hitter-v31/counts.parquet')
    support=pl.read_parquet(e.OUT/'profile-support.parquet')
    oldcontext=pl.read_parquet(e.STATUS/'context.parquet');records=e.read(e.STATUS/'records.json')
    cases=[]
    with threadpool_limits(limits=2):
        for rid,reasons in chosen.items():
            row=enriched.filter(pl.col('row_id')==rid).row(0,named=True)
            te=f.filter(pl.col('row_id')==rid);heads={}
            cell=next(c for c in pre['cells']if c['year']==row['origin_year']and c['fold']==row['outer_fold'])
            for h in e.read(e.OUT/f"fit-{row['origin_year']}-{row['outer_fold']}.json")['heads']:
                m=joblib.load(h['path']);names=h['features'];x=te.select(names).to_numpy()[0]
                heads[h['arm']]=dict(path_trace=trace(m,x,names),target=h['target'],
                    all_inputs=dict(zip(names,map(float,x))),training_players=h['training_players'],
                    enabled_availability_inputs=[n for n in names if n.startswith('op_')])
            peers=enriched.filter((pl.col('origin_year')==row['origin_year'])&
                (pl.col('stage')==row['stage'])&(pl.col('prior_debut')==row['prior_debut'])&
                (pl.col('player_id')!=row['player_id'])).with_columns(
                (((pl.col('age')-row['age'])/3)**2+((pl.col('pa_0')-row['pa_0'])/300)**2+
                 ((pl.col('pa_1')-row['pa_1'])/300)**2+
                 ((pl.col('workload_reference')-row['workload_reference'])/300)**2+
                 ((pl.col('minor_pa_0')-row['minor_pa_0'])/300)**2).alias('distance'))
            peers=peers.sort('distance','player_id').head(4)
            known=as_of(records.get(str(row['player_id']),[]),date(row['origin_year'],12,31))
            known=[r for r in known if r['available_date']>=date(row['origin_year']-1,1,1)]
            cases.append(dict(origin=row,selection=reasons,heads=heads,
                reference_by_year={str(row['origin_year']-lag):dict(actual_pa=row[f'pa_{lag}'],
                    average_team_games=pre['season_average_completed_games'][str(row['origin_year']-lag)],
                    annual_workload_reference=float(te[f'annual_workload_reference_{lag}'][0]))for lag in range(3)},
                source_history=raw.filter((pl.col('player_id')==row['player_id'])&
                    pl.col('season').is_between(row['origin_year']-2,row['origin_year'])).sort('season','bucket').to_dicts(),
                availability_context=oldcontext.filter(pl.col('row_id')==rid).row(0,named=True),
                cutoff_records=known,profile_support=support.filter(pl.col('row_id')==rid).row(0,named=True),
                added_feature_support=cell['exposed_players'],
                peers=peers.select('player_name','age','pa_0','pa_1','minor_pa_0','workload_reference',
                    'on_40man','repaired_pa','direct61_pa','anchor61_pa','next_pa','next_value').to_dicts()))
    e.write('cases.json',cases)
    e.write('verification.json',dict(replayed_heads=replayed,evaluation_rows=len(q),
        clipping_by_arm=clips,baseline_columns_bit_exact=True,batting_rate_bit_exact=True,
        reference_addback_verified=True,probabilities_fitted=False,cases=len(cases),
        player_walkthrough_status='pending',protected_outcomes_used=False,frozen_forecast_changed=False))
    print('All 70 heads replayed; scores and '+str(len(cases))+' cases ready for actual review.',flush=True)
    for s in scores[:8]:print(s['scope'],{a:(round(v['pa_rmse'],3),round(v['pa_mae'],3),round(v['value_rmse'],5))for a,v in s['scores'].items()},flush=True)


if __name__=='__main__':main()
