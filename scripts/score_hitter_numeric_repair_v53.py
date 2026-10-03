"""Replay fits, score shared event units, and prepare actual player walkthroughs."""
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.mlb_event_logit import EVENTS,VALUES
from universal_baseball.histogram_prediction_trace import trace
from universal_baseball.storage import sha256_file
from universal_baseball.practical_hitter_v30 import score
from score_practical_hitter_v31 import rate_score,paired
from score_hitter_reliability_v50 import rate_interval
from score_hitter_readiness_v49 import probability_score
from prepare_practical_hitter_v33 import safe_matrix
import audit_hitter_public_units_v51 as public
import evaluate_hitter_numeric_repair_v53 as e


def ridge_trace(model,x,names):
    terms=x*model.coef_
    prediction=float(model.intercept_+terms.sum())
    assert np.isclose(prediction,model.predict(x[None,:])[0],atol=1e-10)
    return dict(reference=float(model.intercept_),raw_prediction=prediction,
        feature_effects=sorted([dict(feature=n,input=float(a),coefficient=float(b),effect=float(t))
            for n,a,b,t in zip(names,x,model.coef_,terms)],key=lambda x:abs(x['effect']),reverse=True),
        interpretation='Exact linear sum on scaled inputs, not causal attribution.')


def main():
    pre=e.read(e.OUT/'preflight.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(e.Path(p))==h,p
    source=pl.read_parquet(e.OUT/'features.parquet');base=pl.read_parquet(e.previous.OUT/'features.parquet')
    q=pl.read_parquet(e.OUT/'predictions.parquet');replayed=0
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            te=source.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            f=q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            note=e.read(e.OUT/f"fit-{c['year']}-{c['fold']}.json")
            for h in note['heads']:
                assert sha256_file(e.Path(h['path']))==h['sha256'];m=joblib.load(h['path']);head=h['head']
                names=pre['rate_features'] if head=='rate' else pre['pa_features']
                x=safe_matrix(te,names) if head=='rate' else te.select(names).to_numpy()
                out=m.predict_proba(x)[:,1] if head=='participation' else m.predict(x)
                col={'participation':'repaired_raw_p','conditional_pa':'repaired_raw_conditional_pa','rate':'repaired_rate'}[head]
                assert np.allclose(out,f[col],atol=1e-10,rtol=0);replayed+=1
            assert np.allclose(f['repaired_p']*f['repaired_conditional_pa'],f['repaired_pa'],atol=1e-10,rtol=0)
    # Preserve original predictions; reconcile actuals onto the origin units only.
    env=pl.read_parquet(public.previous.OUT/'features.parquet').select('row_id',*[stem+'_'+ev for stem in ['count','origin_env','target_env'] for ev in EVENTS])
    q=q.join(env,on='row_id',validate='1:1')
    counts=q.select(['count_'+ev for ev in EVENTS]).to_numpy();assert np.array_equal(counts.sum(1),q['next_pa'])
    oi=q.select(['origin_env_'+ev for ev in EVENTS]).to_numpy()@VALUES
    ti=q.select(['target_env_'+ev for ev in EVENTS]).to_numpy()@VALUES
    ai=np.divide(counts@VALUES,q['next_pa'].to_numpy(),out=np.zeros(len(q)),where=q['next_pa'].to_numpy()>0)
    active=q['next_pa'].to_numpy()>0
    assert np.allclose((ai[active]-ti[active])*public.UNIT,q['next_batting_rate'].to_numpy()[active])
    q=q.with_columns(pl.Series('origin_index',oi),pl.Series('actual_index',ai),pl.col('next_value').alias('old_actual_value'),
        pl.col('next_batting_rate').alias('old_actual_rate'),
        pl.Series('next_batting_rate',np.where(active,(ai-oi)*public.UNIT,0.)),
        pl.col('binary_scout_pa').alias('old_pa'),pl.col('binary_scout_rate').alias('old_rate'),pl.col('binary_scout_p').alias('old_p'))
    q=q.with_columns((pl.col('next_pa')*(pl.col('next_batting_rate')/600+pl.col('origin_replacement_rate'))).alias('next_value'),
        (pl.col('old_pa')*(pl.col('old_rate')/600+pl.col('origin_replacement_rate'))).alias('old_value'))
    p=pl.read_parquet(public.OUT/'predictions.parquet').select('row_id','steamer_index','zips_index','archive_steamer_pa',
        pl.col('steamer_rate').alias('common_steamer_rate'),pl.col('zips_rate').alias('common_zips_rate'))
    q=q.join(p,on='row_id',how='left',validate='1:1').with_columns(pl.col('archive_steamer_pa').alias('steamer_pa'),
        pl.col('common_steamer_rate').alias('steamer_rate'),pl.col('common_zips_rate').alias('zips_rate'))
    q=q.with_columns((pl.col('steamer_pa')*(pl.col('steamer_rate')/600+pl.col('origin_replacement_rate'))).alias('steamer_value'))
    pub=q.filter((pl.col('pa_0')>0)&pl.col('steamer_index').is_not_null()&pl.col('zips_index').is_not_null());assert len(pub)==2627
    scopes=[('all',q),('never_debut',q.filter(pl.col('prior_debut')==0)),
        ('upper_never_debut',q.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Upper minors'))),
        ('lower_never_debut',q.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Lower minors'))),
        ('current_regular',q.filter(pl.col('pa_0')>=400)),('public_broad',pub),('public_legacy',pub.filter(pl.col('v24_pa').is_not_null()))]
    scopes += [('origin_'+str(y),q.filter(pl.col('origin_year')==y)) for y in sorted(q['origin_year'].unique())]
    scopes += [('stage_'+s,q.filter(pl.col('stage')==s)) for s in sorted(q['stage'].unique())]
    results=[];intervals=[]
    for scope,g in scopes:
        arms=['old','repaired','pa_only','rate_only']+(['steamer'] if scope.startswith('public') else [])
        rates={a:rate_score(g,a+'_rate') for a in arms+(['zips'] if scope.startswith('public') else [])}
        for r in rates.values():r['unit']='fixed-event batting wins per 600 PA centered on the common origin MLB environment'
        results.append(dict(scope=scope,rows=len(g),people=g['player_id'].n_unique(),actual_pa=float(g['next_pa'].sum()),actual_value=float(g['next_value'].sum()),
            scores={a:score(g,a) for a in arms},rates=rates,probabilities={a:probability_score(g,a) for a in ['old','repaired']}))
        if scope in ['all','never_debut','upper_never_debut','public_broad','public_legacy']:
            intervals.extend(dict(scope=scope,**paired(g,'repaired','old',metric)) for metric in ['pa','value'])
            intervals.append(dict(scope=scope,**rate_interval(g,'repaired','old')))
    e.write('scores.json',results);e.write('intervals.json',intervals);q.write_parquet(e.OUT/'scored-predictions.parquet')
    selected={}
    def choose(rows,reason):
        o=rows.row(0,named=True);selected.setdefault(o['row_id'],[]).append(reason)
    for pid,y in [(701762,2024),(694671,2023),(641355,2016),(624413,2018),(806956,2024)]:
        choose(q.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y)),'fixed source diagnostic')
    a=q.with_columns(((pl.col('old_value')-pl.col('next_value'))**2-(pl.col('repaired_value')-pl.col('next_value'))**2).alias('gain'),
        (pl.col('repaired_value')-pl.col('next_value')).alias('error'))
    for why,rows in [('largest delivered gain',a.sort('gain',descending=True)),('largest delivered harm',a.sort('gain')),
        ('false high',a.sort('error',descending=True)),('false low',a.sort('error')),
        ('ordinary',a.filter(pl.col('next_pa').is_between(200,600)).sort(pl.col('error').abs()))]:choose(rows,why)
    history=pl.read_parquet(e.ROOT/'reports/generated/practical-hitter-v31/counts.parquet');profiles=pl.read_parquet(e.OUT/'profile-support.parquet');cases=[]
    with threadpool_limits(limits=2):
        for rid,reasons in selected.items():
            o=q.filter(pl.col('row_id')==rid).row(0,named=True);te=source.filter(pl.col('row_id')==rid);old=base.filter(pl.col('row_id')==rid)
            note=e.read(e.OUT/f"fit-{o['origin_year']}-{o['outer_fold']}.json");heads={};changes={}
            for h in note['heads']:
                model=joblib.load(h['path']);head=h['head'];names=pre['rate_features'] if head=='rate' else pre['pa_features']
                x=safe_matrix(te,names)[0] if head=='rate' else te.select(names).to_numpy()[0]
                if head=='rate':heads[head]=ridge_trace(model,x,names)
                elif head=='participation':heads[head]=e.previous.logit_trace(model,x,names)
                else:heads[head]=trace(model,x,names)
                xo=safe_matrix(old,names) if head=='rate' else old.select(names).to_numpy()
                raw=model.predict_proba(xo)[0,1] if head=='participation' else model.predict(xo)[0]
                changes[head]=dict(same_repaired_fit_with_old_inputs=float(raw),interpretation='Fixed-fit input sensitivity only; not a validated alternative forecast or causal effect.')
            for c in pre['source_changes']:
                name=c['feature'];changes[name]=dict(old=old[name][0],repaired=te[name][0])
            peers=q.filter((pl.col('origin_year')==o['origin_year'])&(pl.col('stage')==o['stage'])&(pl.col('prior_debut')==o['prior_debut'])&(pl.col('player_id')!=o['player_id'])).with_columns(
                (((pl.col('age')-o['age'])/3)**2+((pl.col('minor_pa_0')-o['minor_pa_0'])/250)**2+4*(pl.col('draft_rank')-o['draft_rank'])**2).alias('distance')).sort('distance','player_id').head(4)
            cases.append(dict(origin=o,selection=reasons,source_history=history.filter((pl.col('player_id')==o['player_id'])&pl.col('season').is_between(o['origin_year']-2,o['origin_year'])).sort('season','bucket').to_dicts(),
                corrected_inputs={n:te[n][0] for n in pre['pa_features']},numeric_changes_and_probes=changes,heads=heads,
                training_profile=profiles.filter(pl.col('row_id')==rid).to_dicts(),
                peers=peers.select('player_id','player_name','age','minor_pa_0','draft_rank','old_pa','repaired_pa','old_rate','repaired_rate','next_pa','next_batting_rate','next_value').to_dicts()))
    e.write('cases.json',cases);e.write('verification.json',dict(replayed_heads=replayed,expected_pa_product_verified=True,source_labels_unchanged=True,
        common_event_units_verified=True,cases=len(cases),player_walkthrough_status='pending',protected_outcomes_used=False,frozen_forecast_changed=False))
    for s in results[:7]:print(s['scope'],{a:(round(v['pa_rmse'],3),round(v['pa_mae'],3),round(v['value_rmse'],6),round(s['rates'][a]['rmse'],6) if s['rates'][a]['rmse'] else None,round(v['pa_total'])) for a,v in s['scores'].items()},flush=True)
    print('Actual source-to-fit cases prepared:',len(cases),'review pending.',flush=True)


if __name__=='__main__':main()
