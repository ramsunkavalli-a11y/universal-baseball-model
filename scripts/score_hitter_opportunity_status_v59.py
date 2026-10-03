"""Replay all heads and prepare the required source-to-forecast reviews."""
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.storage import sha256_file
from universal_baseball.practical_hitter_v30 import score
from universal_baseball.histogram_prediction_trace import trace
from score_practical_hitter_v31 import paired
from score_hitter_readiness_v49 import probability_score
from evaluate_hitter_readiness_v49 import logit_trace
import evaluate_hitter_opportunity_status_v59 as e


def main():
    pre=e.read(e.OUT/'preflight.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(e.Path(p))==h,p
    source=pl.read_parquet(e.OUT/'features.parquet')
    q=pl.read_parquet(e.OUT/'predictions.parquet')
    baseline=pl.read_parquet(e.base.OUT/'scored-predictions.parquet')
    assert q.select(baseline.columns).equals(baseline.sort('row_id'))
    assert q['status_rate'].equals(q['repaired_rate'])
    replayed=0
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            te=source.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            f=q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            for h in e.read(e.OUT/f"fit-{c['year']}-{c['fold']}.json")['heads']:
                assert sha256_file(e.Path(h['path']))==h['sha256']
                m=joblib.load(h['path']);x=te.select(h['features']).to_numpy()
                out=m.predict_proba(x)[:,1] if h['head']=='participation' else m.predict(x)
                column='status_raw_p' if h['head']=='participation' else 'status_raw_conditional_pa'
                assert np.allclose(out,f[column],atol=1e-10,rtol=0)
                replayed+=1
    assert np.allclose(q['status_p']*q['status_conditional_pa'],q['status_pa'],atol=1e-10,rtol=0)
    enriched=q.join(source.select('row_id',*e.FEATURES),on='row_id',validate='1:1')
    pub=q.filter((pl.col('pa_0')>0)&pl.col('steamer_index').is_not_null()&pl.col('zips_index').is_not_null())
    assert len(pub)==2627
    groups=[('all',q),('public_broad',pub),('public_legacy',pub.filter(pl.col('v24_pa').is_not_null())),
        ('current_mlb',q.filter(pl.col('pa_0')>0)),
        ('never_debut',q.filter(pl.col('prior_debut')==0)),
        ('absent_former_regular',q.filter((pl.col('pa_0')==0)&((pl.col('pa_1')>=300)|(pl.col('pa_2')>=300)))),
        ('brief_mlb',q.filter(pl.col('pa_0').is_between(1,199))),
        ('large_regular',q.filter(pl.col('pa_0')>=600))]
    groups += [('origin_'+str(y),q.filter(pl.col('origin_year')==y)) for y in sorted(q['origin_year'].unique())]
    groups += [('stage_'+s,q.filter(pl.col('stage')==s)) for s in sorted(q['stage'].unique())]
    groups += [(name,enriched.filter(pl.col(name)>0)) for name in e.FEATURES[2:]]
    results=[];intervals=[]
    for name,g in groups:
        if not len(g):continue
        arms=['repaired','status']+(['steamer'] if name.startswith('public') else [])
        results.append(dict(scope=name,rows=len(g),people=g['player_id'].n_unique(),
            actual_pa=int(g['next_pa'].sum()),actual_value=float(g['next_value'].sum()),
            scores={a:score(g,a) for a in arms},
            probabilities={a:probability_score(g,a) for a in ['repaired','status']}))
        if name in ['all','public_broad','current_mlb','never_debut','absent_former_regular']:
            intervals.extend(dict(scope=name,**paired(g,'status','repaired',metric)) for metric in ['pa','value'])
    e.write('scores.json',results);e.write('intervals.json',intervals)
    chosen={}
    def choose(g,why):
        row=g.row(0,named=True);chosen.setdefault(row['row_id'],[]).append(why)
    for pid,y in [(592450,2022),(680574,2024),(666158,2023),(665487,2022),
                  (677551,2023),(645801,2023),(694671,2023)]:
        choose(q.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y)),'fixed diagnostic')
    ranked=q.with_columns(
        ((pl.col('repaired_value')-pl.col('next_value'))**2-(pl.col('status_value')-pl.col('next_value'))**2).alias('gain'),
        (pl.col('status_value')-pl.col('next_value')).alias('error'))
    for why,g in [('largest delivered gain',ranked.sort('gain',descending=True)),
                  ('largest delivered harm',ranked.sort('gain')),
                  ('false high',ranked.sort('error',descending=True)),
                  ('false low',ranked.sort('error')),
                  ('ordinary',ranked.filter(pl.col('next_pa').is_between(200,600)).sort(pl.col('error').abs()))]:
        choose(g,why)
    raw=pl.read_parquet(e.ROOT/'reports/generated/practical-hitter-v31/counts.parquet')
    context=pl.read_parquet(e.OUT/'context.parquet')
    records=e.read(e.OUT/'records.json')
    profile=pl.read_parquet(e.OUT/'profile-support.parquet')
    anchor_pre=e.read(e.base.OUT/'preflight.json');cases=[]
    with threadpool_limits(limits=2):
        for rid,reasons in chosen.items():
            o=q.filter(pl.col('row_id')==rid).row(0,named=True)
            te=source.filter(pl.col('row_id')==rid);heads={};old_heads={};probes={}
            cell=next(c for c in pre['cells'] if c['year']==o['origin_year'] and c['fold']==o['outer_fold'])
            for h in e.read(e.OUT/f"fit-{o['origin_year']}-{o['outer_fold']}.json")['heads']:
                model=joblib.load(h['path']);names=h['features'];x=te.select(names).to_numpy()[0]
                heads[h['head']]=logit_trace(model,x,names) if h['head']=='participation' else trace(model,x,names)
                zero=x.copy()
                for i,n in enumerate(names):
                    if n in e.FEATURES[2:]:zero[i]=0
                value=model.predict_proba(zero[None,:])[0,1] if h['head']=='participation' else model.predict(zero[None,:])[0]
                probes[h['head']]=dict(status_signals_neutralized=float(value),
                    interpretation='Fixed-fit mechanical sensitivity, not a healthy player, causal estimate or validated alternative.')
            for h in e.read(e.base.OUT/f"fit-{o['origin_year']}-{o['outer_fold']}.json")['heads']:
                if h['head']=='rate':continue
                model=joblib.load(h['path']);names=anchor_pre['pa_features'];x=te.select(names).to_numpy()[0]
                old_heads[h['head']]=logit_trace(model,x,names) if h['head']=='participation' else trace(model,x,names)
            peers=q.filter((pl.col('origin_year')==o['origin_year'])&
                (pl.col('stage')==o['stage'])&(pl.col('prior_debut')==o['prior_debut'])&
                (pl.col('player_id')!=o['player_id'])).with_columns(
                    (((pl.col('age')-o['age'])/3)**2+
                     ((pl.col('pa_0')-o['pa_0'])/300)**2+
                     ((pl.col('pa_1')-o['pa_1'])/300)**2+
                     ((pl.col('minor_pa_0')-o['minor_pa_0'])/300)**2+
                     (pl.col('on_40man')-o['on_40man'])**2).alias('distance')
                ).sort('distance','player_id').head(4)
            known=[r for r in records.get(str(o['player_id']),[]) if r['available_date']<=f"{o['origin_year']}-12-31"
                and r['available_date']>=f"{o['origin_year']-1}-01-01"]
            cases.append(dict(origin=o,selection=reasons,
                source_history=raw.filter((pl.col('player_id')==o['player_id'])&
                    pl.col('season').is_between(o['origin_year']-2,o['origin_year'])).sort('season','bucket').to_dicts(),
                context=context.filter(pl.col('row_id')==rid).row(0,named=True),
                cutoff_records=known,actual_inputs={n:te[n][0] for n in anchor_pre['pa_features']+e.FEATURES},
                heads=heads,baseline_heads=old_heads,fixed_fit_probes=probes,
                head_feature_support=cell['feature_support'],
                training_profile=profile.filter(pl.col('row_id')==rid).to_dicts(),
                peers=peers.select('player_id','player_name','age','pa_0','pa_1','minor_pa_0','on_40man',
                    'repaired_p','status_p','repaired_conditional_pa','status_conditional_pa',
                    'repaired_pa','status_pa','repaired_rate','next_pa','next_batting_rate','next_value').to_dicts()))
    e.write('cases.json',cases)
    e.write('verification.json',dict(replayed_heads=replayed,evaluation_rows=len(q),
        baseline_columns_bit_exact=True,batting_rate_bit_exact=True,expected_pa_product_verified=True,
        conditional_clipped_rows=q.filter(pl.col('status_raw_conditional_pa')!=pl.col('status_conditional_pa')).height,
        cases=len(cases),player_walkthrough_status='pending',protected_outcomes_used=False,
        frozen_forecast_changed=False))
    for s in results[:8]:
        print(s['scope'],{a:{k:round(v[k],5) for k in ['pa_rmse','pa_mae','value_rmse','pa_total']} for a,v in s['scores'].items()},flush=True)
    print('Player review pending:',[(c['origin']['player_name'],c['origin']['origin_year'],c['selection']) for c in cases],flush=True)


if __name__=='__main__':
    main()
