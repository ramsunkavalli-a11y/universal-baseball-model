"""Exact linear-head accounting and unchanged-cohort prospect scores."""
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.storage import sha256_file
from universal_baseball.practical_hitter_v30 import score
from score_practical_hitter_v31 import rate_score,paired
from score_hitter_reliability_v50 import rate_interval
from score_hitter_readiness_v49 import probability_score
import evaluate_hitter_prospect_pooling_v54 as e


def linear_trace(model,x,names,classification=False):
    scaler,learner=model.steps[0][1],model.steps[1][1]
    z=scaler.transform(x[None,:])[0];coef=learner.coef_[0] if classification else learner.coef_
    intercept=float(learner.intercept_[0] if classification else learner.intercept_)
    raw=float(intercept+z@coef)
    expected=model.decision_function(x[None,:])[0] if classification else model.predict(x[None,:])[0]
    assert np.isclose(raw,expected,atol=1e-10)
    return dict(reference=intercept,raw_prediction=raw,linked_prediction=float(1/(1+np.exp(-raw))) if classification else raw,
        feature_effects=sorted([dict(feature=n,input=float(v),training_mean=float(mu),training_scale=float(sd),
            standardized_input=float(a),coefficient=float(b),effect=float(a*b))
            for n,v,mu,sd,a,b in zip(names,x,scaler.mean_,scaler.scale_,z,coef)],key=lambda t:abs(t['effect']),reverse=True),
        units='log odds then logistic link' if classification else ('response units'),
        interpretation='Exact standardized linear sum. Shared slopes borrow across profiles; sparse profile support and extrapolation remain. Not causal attribution.')


def main():
    pre=e.read(e.OUT/'preflight.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(e.Path(p))==h,p
    source=pl.read_parquet(e.OUT/'features.parquet');q=pl.read_parquet(e.OUT/'predictions.parquet');base=pl.read_parquet(e.previous.OUT/'scored-predictions.parquet')
    assert q.select(base.columns).equals(base.sort('row_id'))
    established=q.filter(pl.col('prior_debut')==1)
    for col in ['p','conditional_pa','pa','rate','value']:
        assert established['shared_'+col].equals(established['repaired_'+col]),col
    replayed=0
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            te=source.filter(pl.col('row_id').is_in(c['prospect_test_ids'])).sort('row_id')
            f=q.filter(pl.col('row_id').is_in(c['prospect_test_ids'])).sort('row_id')
            note=e.read(e.OUT/f"fit-{c['year']}-{c['fold']}.json")
            for h in note['heads']:
                assert sha256_file(e.Path(h['path']))==h['sha256'];m=joblib.load(h['path'])
                a=m.predict_proba(te.select(pre['features']).to_numpy())[:,1] if h['head']=='participation' else m.predict(te.select(pre['features']).to_numpy())
                expected={'participation':f['shared_p'].to_numpy(),'conditional_pa':f['shared_conditional_pa'].to_numpy(),'rate':f['shared_rate'].to_numpy()}[h['head']]
                if h['head']=='participation':a[f['hard_unavailable'].to_numpy()|f['reported_retired'].to_numpy()]=0
                elif h['head']=='conditional_pa':a=np.clip(a,1,800)
                assert np.allclose(a,expected,atol=1e-10,rtol=0);replayed+=1
            assert np.allclose(f['shared_pa'],f['shared_p']*f['shared_conditional_pa'],atol=1e-10,rtol=0)
    never=q.filter(pl.col('prior_debut')==0)
    pub=q.filter((pl.col('pa_0')>0)&pl.col('steamer_index').is_not_null()&pl.col('zips_index').is_not_null());assert len(pub)==2627
    scopes=[('all',q),('never_debut',never),('upper_never_debut',never.filter(pl.col('stage')=='Upper minors')),
        ('lower_never_debut',never.filter(pl.col('stage')=='Lower minors')),('public_broad_unchanged',pub)]
    scopes += [('never_origin_'+str(y),never.filter(pl.col('origin_year')==y)) for y in sorted(never['origin_year'].unique())]
    scopes += [('never_stage_'+s,never.filter(pl.col('stage')==s)) for s in sorted(never['stage'].unique())]
    scores=[];intervals=[]
    for scope,g in scopes:
        if not len(g):continue
        arms=['repaired','shared','prospect_pa_only','prospect_rate_only']+(['steamer'] if scope.startswith('public') else [])
        rates={a:rate_score(g,a+'_rate') for a in arms+(['zips'] if scope.startswith('public') else [])}
        for r in rates.values():r['unit']='fixed-event batting wins/600 on the common origin MLB environment'
        scores.append(dict(scope=scope,rows=len(g),people=g['player_id'].n_unique(),actual_pa=float(g['next_pa'].sum()),actual_value=float(g['next_value'].sum()),
            scores={a:score(g,a) for a in arms},rates=rates,probabilities={a:probability_score(g,a) for a in ['repaired','shared']}))
        if scope in ['all','never_debut','upper_never_debut','lower_never_debut']:
            intervals.extend(dict(scope=scope,**paired(g,'shared','repaired',metric)) for metric in ['pa','value'])
            intervals.append(dict(scope=scope,**rate_interval(g,'shared','repaired')))
    e.write('scores.json',scores);e.write('intervals.json',intervals)
    selected={}
    def choose(rows,reason):
        o=rows.row(0,named=True);selected.setdefault(o['row_id'],[]).append(reason)
    for pid,y in [(701762,2024),(694671,2023),(641355,2016),(624413,2018),(806956,2024)]:
        choose(never.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y)),'fixed diagnostic')
    g=never.with_columns(((pl.col('repaired_value')-pl.col('next_value'))**2-(pl.col('shared_value')-pl.col('next_value'))**2).alias('gain'),
        (pl.col('shared_value')-pl.col('next_value')).alias('error'))
    for why,ordered in [('largest delivered gain',g.sort('gain',descending=True)),('largest delivered harm',g.sort('gain')),
        ('false high',g.sort('error',descending=True)),('false low',g.sort('error')),
        ('ordinary active prospect',g.filter(pl.col('next_pa').is_between(100,600)).sort(pl.col('error').abs()))]:choose(ordered,why)
    history=pl.read_parquet(e.ROOT/'reports/generated/practical-hitter-v31/counts.parquet');profiles=pl.read_parquet(e.OUT/'profile-support.parquet');cases=[]
    with threadpool_limits(limits=2):
        for rid,reasons in selected.items():
            o=q.filter(pl.col('row_id')==rid).row(0,named=True);te=source.filter(pl.col('row_id')==rid)
            note=e.read(e.OUT/f"fit-{o['origin_year']}-{o['outer_fold']}.json");heads={}
            for h in note['heads']:heads[h['head']]=linear_trace(joblib.load(h['path']),te.select(pre['features']).to_numpy()[0],pre['features'],h['head']=='participation')
            peers=never.filter((pl.col('origin_year')==o['origin_year'])&(pl.col('stage')==o['stage'])&(pl.col('player_id')!=o['player_id'])).with_columns(
                (((pl.col('age')-o['age'])/3)**2+((pl.col('minor_pa_0')-o['minor_pa_0'])/250)**2+4*(pl.col('draft_rank')-o['draft_rank'])**2).alias('distance')).sort('distance','player_id').head(4)
            cases.append(dict(origin=o,selection=reasons,actual_inputs={n:te[n][0] for n in pre['features']},known_highest_current=te['known_highest_current'][0],
                source_history=history.filter((pl.col('player_id')==o['player_id'])&pl.col('season').is_between(o['origin_year']-2,o['origin_year'])).sort('season','bucket').to_dicts(),
                heads=heads,training_profile=profiles.filter(pl.col('row_id')==rid).to_dicts(),
                peers=peers.select('player_id','player_name','age','minor_pa_0','draft_rank','repaired_p','shared_p','repaired_pa','shared_pa','repaired_rate','shared_rate','next_pa','next_batting_rate','next_value').to_dicts()))
    e.write('cases.json',cases);e.write('verification.json',dict(replayed_heads=replayed,established_forecasts_bit_exact=True,
        whole_evaluation_population_retained=True,exact_linear_paths_reconstructed=True,cases=len(cases),player_walkthrough_status='pending',
        frozen_forecast_changed=False,protected_outcomes_used=False))
    for s in scores[:5]:print(s['scope'],{a:(round(v['pa_rmse'],3),round(v['pa_mae'],3),round(v['value_rmse'],6),round(s['rates'][a]['rmse'],4),round(v['pa_total'])) for a,v in s['scores'].items()},flush=True)
    print('Case identities:',[(c['origin']['player_name'],c['origin']['origin_year'],c['selection']) for c in cases],flush=True)


if __name__=='__main__':main()
