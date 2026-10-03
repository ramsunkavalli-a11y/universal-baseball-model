"""Score common units and replay saved fits through real player cases."""
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from prepare_practical_hitter_v33 import safe_matrix
from score_practical_hitter_v31 import score,rate_score,paired
from score_hitter_reliability_v50 import rate_interval
from universal_baseball.hitter_compatible_value import envelope
from universal_baseball.histogram_prediction_trace import trace
from universal_baseball.storage import sha256_file
import evaluate_hitter_compatible_value_v63 as e


def linear_trace(model,x,names):
    t=x*model.coef_;p=float(model.intercept_+t.sum())
    assert np.isclose(p,model.predict(x[None,:])[0],atol=1e-10)
    return dict(reference=float(model.intercept_),raw_prediction=p,feature_effects=sorted([
        dict(feature=n,input=float(v),coefficient=float(c),effect=float(a)) for n,v,c,a in zip(names,x,model.coef_,t)],key=lambda o:abs(o['effect']),reverse=True),interpretation='Exact additive fitted terms on fixed scaled inputs; not causal effects.')


def main():
    pre=e.read(e.OUT/'preflight.json')
    for path,h in pre['input_hashes'].items():assert sha256_file(e.Path(path))==h
    source=pl.read_parquet(e.OUT/'features.parquet');q=pl.read_parquet(e.OUT/'predictions.parquet').sort('row_id')
    ev=source.filter(pl.col('row_id').is_in(q['row_id'].to_list())).sort('row_id');assert ev['row_id'].equals(q['row_id'])
    lo,hi=envelope(q['baseline_pa'].to_numpy(),q['origin_index'].to_numpy(),q['origin_replacement_rate'].to_numpy())
    q=q.with_columns(pl.Series('physical_low',lo),pl.Series('physical_high',hi))
    arms=['baseline',*e.ARMS]
    for arm in arms:q=q.with_columns(((pl.col(arm+'_value')<pl.col('physical_low')-1e-10)|(pl.col(arm+'_value')>pl.col('physical_high')+1e-10)).alias(arm+'_incompatible'))
    pub=q.filter((pl.col('pa_0')>0)&pl.col('steamer_index').is_not_null()&pl.col('zips_index').is_not_null());assert len(pub)==2627
    scopes=[('all',q),('public_broad',pub),('never_debut',q.filter(pl.col('prior_debut')==0)),
        ('upper_never_debut',q.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Upper minors'))),
        ('lower_never_debut',q.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Lower minors'))),
        ('current_brief',q.filter(pl.col('pa_0').is_between(1,199))),('current_partial',q.filter(pl.col('pa_0').is_between(200,399))),
        ('current_regular',q.filter(pl.col('pa_0')>=400)),
        ('absent_former_regular',q.filter((pl.col('pa_0')==0)&(pl.col('prior_debut')==1)&(pl.col('regular_window')>=1)))]
    scopes += [('origin_'+str(y),q.filter(pl.col('origin_year')==y)) for y in sorted(q['origin_year'].unique())]
    scopes += [('stage_'+s,q.filter(pl.col('stage')==s)) for s in sorted(q['stage'].unique())]
    results=[];intervals=[]
    for scope,g in scopes:
        if not len(g):continue
        aa=arms+(['steamer'] if scope=='public_broad' else [])
        rates={a:rate_score(g,a+'_rate') for a in ['baseline','common_rate']+(['steamer','zips'] if scope=='public_broad' else [])}
        for r in rates.values():r['unit']='fixed-event batting wins per 600 PA centered on common origin MLB environment; not official WAR'
        results.append(dict(scope=scope,rows=len(g),people=g['player_id'].n_unique(),actual_pa=float(g['next_pa'].sum()),actual_value=float(g['next_value'].sum()),scores={a:score(g,a) for a in aa},rates=rates,physical_incompatibilities={a:int(g[a+'_incompatible'].sum()) for a in arms}))
        if scope in ['all','public_broad','never_debut','upper_never_debut','lower_never_debut']:
            intervals.extend(dict(scope=scope,**paired(g,a,'baseline','value')) for a in e.ARMS)
            intervals.append(dict(scope=scope,**rate_interval(g,'common_rate','baseline')))
    e.write('scores.json',results);e.write('intervals.json',intervals)
    q.write_parquet(e.OUT/'scored-predictions.parquet')
    selected={}
    def choose(g,why):
        assert len(g);rid=g['row_id'][0];selected.setdefault(rid,[]).append(why)
    for pid,y in [(592450,2016),(592450,2022),(592450,2024),(691026,2023),(668715,2022),(680574,2024),(665487,2022),(701762,2024),(694671,2023),(665742,2017),(670541,2022)]:
        choose(q.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y)),'fixed baseball diagnostic')
    for arm in e.ARMS:
        g=q.with_columns(((pl.col('baseline_value')-pl.col('next_value'))**2-(pl.col(arm+'_value')-pl.col('next_value'))**2).alias('gain'),(pl.col(arm+'_value')-pl.col('next_value')).alias('error'))
        for why,sub in [('largest delivered gain',g.sort('gain',descending=True)),('largest delivered harm',g.sort('gain')),('false high',g.sort('error',descending=True)),('false low',g.sort('error')),('ordinary',g.filter(pl.col('next_pa').is_between(200,600)).sort(pl.col('error').abs()))]:choose(sub,arm+': '+why)
        incompatible=g.filter(pl.col(arm+'_incompatible'))
        if len(incompatible):choose(incompatible.sort(pl.col('error').abs(),descending=True),arm+': incompatible fixed-PA/value')
    history=pl.read_parquet(e.ROOT/'reports/generated/practical-hitter-v31/counts.parquet');profiles=pl.read_parquet(e.OUT/'profile-support.parquet');support=pl.read_parquet(e.OUT/'support.parquet');cases=[];replayed=0
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            te=source.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id');pred=q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            note=e.read(e.OUT/f"fit-{c['year']}-{c['fold']}.json")
            for h in note['heads']:
                arm=h['head'];m=joblib.load(h['path']);assert sha256_file(e.Path(h['path']))==h['sha256']
                names=pre['rate_features'] if arm=='common_rate' else pre['pa_features']
                x=safe_matrix(te,names) if arm=='common_rate' else te.select(names).to_numpy()
                assert np.allclose(m.predict(x),pred[arm+'_raw'],rtol=0,atol=1e-10);replayed+=1
        for rid,reasons in selected.items():
            o=q.filter(pl.col('row_id')==rid).row(0,named=True);te=source.filter(pl.col('row_id')==rid)
            note=e.read(e.OUT/f"fit-{o['origin_year']}-{o['outer_fold']}.json");heads={}
            for h in note['heads']:
                arm=h['head'];model=joblib.load(h['path']);names=pre['rate_features'] if arm=='common_rate' else pre['pa_features']
                x=safe_matrix(te,names)[0] if arm=='common_rate' else te.select(names).to_numpy()[0]
                heads[arm]=linear_trace(model,x,names) if arm=='common_rate' else trace(model,x,names)
            model=joblib.load(e.BASE/f"rate-{o['origin_year']}-{o['outer_fold']}.joblib")
            heads['baseline_rate']=linear_trace(model,safe_matrix(te,pre['rate_features'])[0],pre['rate_features'])
            peers=q.filter((pl.col('origin_year')==o['origin_year'])&(pl.col('stage')==o['stage'])&(pl.col('prior_debut')==o['prior_debut'])&(pl.col('player_id')!=o['player_id'])).with_columns(
                (((pl.col('age')-o['age'])/3)**2+((pl.col('minor_pa_0')-o['minor_pa_0'])/250)**2+((pl.col('pa_0')-o['pa_0'])/250)**2+4*(pl.col('draft_rank')-o['draft_rank'])**2).alias('distance')).sort('distance','player_id').head(4)
            year=o['origin_year']
            # V53 retained old descriptive columns alongside its corrected fits.
            # Report actual saved-model inputs, retaining the old display values.
            actual_inputs={n:te[n][0] for n in sorted(set(pre['rate_features']+pre['pa_features']))}
            legacy_display={n:o[n] for n,v in actual_inputs.items() if n in o and o[n]!=v}
            omitted_display=[n for n in actual_inputs if n not in o]
            o.update(actual_inputs)
            cases.append(dict(origin=o,legacy_display_inputs=legacy_display,legacy_omitted_input_columns=omitted_display,selection=reasons,source_history=history.filter((pl.col('player_id')==o['player_id'])&pl.col('season').is_between(year-2,year)).sort('season','bucket').to_dicts(),
                actual_history=history.filter((pl.col('player_id')==o['player_id'])&(pl.col('season')==year+1)&(pl.col('bucket')=='MLB')).to_dicts(),
                inputs=actual_inputs,heads=heads,
                actual_training_profiles=profiles.filter(pl.col('row_id')==rid).to_dicts(),training_support=support.filter(pl.col('row_id')==rid).to_dicts(),
                peers_selected_without_outcomes=peers.select('player_id','player_name','age','pa_0','minor_pa_0','draft_rank','baseline_pa','baseline_rate','common_rate_rate',*[a+'_value' for a in arms],'next_pa','next_batting_rate','next_value').to_dicts()))
    e.write('cases.json',cases);e.write('verification.json',dict(replayed_heads=replayed,baseline_pa_rate_exact=True,shared_reference_corrected=True,cases=len(cases),player_walkthrough_status='pending',protected_outcomes_used=False,frozen_forecast_changed=False))
    for s in results:print(s['scope'],{a:(round(v['value_rmse'],6),round(v['value_mae'],6),round(v['value_total'],2),s['physical_incompatibilities'].get(a)) for a,v in s['scores'].items()}, {a:round(v['rmse'],5) if v['rmse'] else None for a,v in s['rates'].items()},flush=True)
    print('Saved actual cases',len(cases),'review pending.',flush=True)


if __name__=='__main__':main()
