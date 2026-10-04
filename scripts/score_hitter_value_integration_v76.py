"""Independent replays, common-unit scores and mandatory saved-model cases."""
import numpy as np
import polars as pl
import joblib
from sklearn.metrics import mean_poisson_deviance
from threadpoolctl import threadpool_limits
from universal_baseball.hitter_compatible_value import UNIT, envelope
from universal_baseball.hitter_value_integration import contribution, poisson_trace
from universal_baseball.histogram_prediction_trace import trace
from universal_baseball.mlb_event_logit import VALUES
from universal_baseball.practical_hitter_v30 import score
from score_practical_hitter_v31 import paired, rate_score
from score_hitter_compatible_value_v63 import linear_trace
from evaluate_hitter_readiness_v49 import logit_trace
from prepare_practical_hitter_v33 import safe_matrix
import evaluate_hitter_value_integration_v76 as e

ARMS=['current','bridge','direct','active','counts']


def peers(source, row):
    """Origin-only matching, including production profile and upper-level exposure."""
    r=row
    upper=r['AA_0_pa']+r['AAA_0_pa']
    eligible=source.filter((pl.col('origin_year')==r['origin_year'])&
        (pl.col('stage')==r['stage'])&(pl.col('prior_debut')==r['prior_debut'])&
        (pl.col('player_id')!=r['player_id']))
    distance=((pl.col('age')-r['age'])/3)**2+((pl.col('pa_0')-r['pa_0'])/250)**2
    distance+=((pl.col('minor_pa_0')-r['minor_pa_0'])/250)**2
    distance+=((pl.col('AA_0_pa')+pl.col('AAA_0_pa')-upper)/250)**2
    distance+=4*(pl.col('scout_rank_score_0')-r['scout_rank_score_0'])**2
    distance+=sum(((pl.col('translated_'+v)-r['translated_'+v])/.75)**2 for v in ['K','UBB','HR'])
    distance+=((pl.col('pooled_mlb_quality')-r['pooled_mlb_quality'])/2)**2
    return eligible.with_columns(distance.alias('comparison_distance')).sort('comparison_distance','player_id').head(4)


def main():
    scoring=e.read(e.OUT/'scoring-contract.json');e.verify(scoring['hashes'])
    pre=e.read(e.OUT/'preflight.json');e.verify(pre['input_hashes'])
    q=pl.read_parquet(e.OUT/'predictions.parquet').sort('row_id')
    anchor=pl.read_parquet(e.previous.OUT/'scored-predictions.parquet').sort('row_id')
    assert len(q)==30506 and q.select(anchor.columns).equals(anchor)
    source_parts=[];replayed=0
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            te=pl.read_parquet(e.OUT/f"features-{c['fold']}.parquet").filter(
                pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            pred=q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            assert te['row_id'].equals(pred['row_id'])
            note=e.read(e.OUT/f"fit-{c['year']}-{c['fold']}.json")
            for h in note['heads']:
                e.verify({h['path']:h['sha256']})
                value=joblib.load(h['path']).predict(te.select(pre['features']).to_numpy())
                column=h['head']+'_raw' if h['head'] in ['direct','active'] else 'counts_raw_'+h['head'][6:]
                assert np.allclose(value,pred[column],atol=1e-10,rtol=0)
                replayed+=1
            source_parts.append(te)
    source=pl.concat(source_parts).sort('row_id');assert source['row_id'].equals(q['row_id'])
    assert np.allclose(source['next_value'],q['next_value'],atol=1e-10,rtol=0)
    assert source['next_pa'].equals(q['next_pa'])
    tags=e.tagged(source).select('row_id','new_draftee','thin_pro','upper_exposure_band','rank_band')
    q=q.join(tags,on='row_id',validate='1:1').sort('row_id')
    hard=q['hard_unavailable'].to_numpy()|q['reported_retired'].to_numpy()
    assert np.allclose(q['active_value'],np.where(hard,0,q['current_p']*q['active_raw']),atol=1e-10,rtol=0)
    assert np.allclose(q['direct_value'],np.where(hard,0,q['direct_raw']),atol=1e-10,rtol=0)
    countmean=q.select(['counts_mean_'+v for v in e.EVENTS]).to_numpy()
    pa,val=contribution(countmean,source['origin_index'].to_numpy(),source['value_replacement_rate'].to_numpy())
    assert np.allclose(pa,q['counts_pa'],atol=1e-10,rtol=0)
    assert np.allclose(val,q['counts_value'],atol=1e-10,rtol=0)
    assert (countmean[hard]==0).all()
    for a in ARMS:
        low,high=envelope(q[a+'_pa'].to_numpy(),source['origin_index'].to_numpy(),source['value_replacement_rate'].to_numpy())
        q=q.with_columns(pl.Series(a+'_incompatible',(q[a+'_value'].to_numpy()<low-1e-8)|
                              (q[a+'_value'].to_numpy()>high+1e-8)))
    assert q['counts_incompatible'].sum()==0
    public=q.filter((pl.col('pa_0')>0)&pl.col('steamer_index').is_not_null()&pl.col('zips_index').is_not_null())
    assert len(public)==2627
    scopes=[('all',q),('public_broad',public),('never_debut',q.filter(pl.col('prior_debut')==0)),
        ('upper_never_debut',q.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Upper minors'))),
        ('lower_never_debut',q.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Lower minors'))),
        ('new_draftee',q.filter(pl.col('new_draftee'))),('thin_pro',q.filter(pl.col('thin_pro'))),
        ('current_brief',q.filter(pl.col('pa_0').is_between(1,199))),
        ('current_partial',q.filter(pl.col('pa_0').is_between(200,399))),
        ('current_regular',q.filter(pl.col('pa_0')>=400)),
        ('absent_former_regular',q.filter((pl.col('pa_0')==0)&(pl.col('prior_debut')==1)&(pl.col('regular_window')>=1)))]
    for y in sorted(q['origin_year'].unique()):
        scopes += [('origin_'+str(y),q.filter(pl.col('origin_year')==y)),
            ('never_origin_'+str(y),q.filter((pl.col('origin_year')==y)&(pl.col('prior_debut')==0)))]
    scopes += [('stage_'+s,q.filter(pl.col('stage')==s)) for s in sorted(q['stage'].unique())]
    results=[];intervals=[]
    with threadpool_limits(limits=2):
        for label,g in scopes:
            if g.is_empty():continue
            arms=ARMS+(['steamer'] if label=='public_broad' else [])
            results.append(dict(scope=label,rows=len(g),people=g['player_id'].n_unique(),actual_pa=float(g['next_pa'].sum()),
                actual_value=float(g['next_value'].sum()),scores={a:score(g,a) for a in arms},
                physical_incompatibilities={a:int(g[a+'_incompatible'].sum()) for a in ARMS},
                counts_caps=int(g['counts_capped'].sum())))
            if label in ['all','public_broad','never_debut','upper_never_debut','lower_never_debut']:
                for a in ['direct','active','counts']:
                    intervals.append(dict(scope=label,**paired(g,a,'current','value')))
                intervals.append(dict(scope=label,**paired(g,'counts','current','pa')))
                intervals.append(dict(scope=label,**paired(g,'counts','bridge','value')))
    diagnostics=[]
    for v in e.EVENTS:
        actual=source['count_'+v].to_numpy();raw=q['counts_raw_'+v].to_numpy();mean=q['counts_mean_'+v].to_numpy()
        assert (raw>0).all()
        deviances=[]
        for y in sorted(q['target_year'].unique()):
            mask=q['target_year'].to_numpy()==y
            deviances.append(mean_poisson_deviance(actual[mask],raw[mask]))
        diagnostics.append(dict(event=v,actual_total=float(actual.sum()),raw_total=float(raw.sum()),final_total=float(mean.sum()),
            raw_head_equal_year_deviance=float(np.mean(deviances)),zero_mean_positive_actual=int(((mean==0)&(actual>0)).sum()),
            interpretation='Mean/count accounting diagnostic, not calibrated season distribution or independent-event likelihood'))
    rate_context={a:rate_score(public,a+'_rate') for a in ['current','steamer','zips']}
    for r in rate_context.values():
        r['unit']='Fixed-event batting wins per 600 PA on common origin environment; public conversion context only'
    e.write('public-rate-context.json',dict(scores=rate_context,zips_PA_not_carried_in_fixed_anchor=True,
        qualification='ZiPS provides an existing matched batting-rate context here, not an invented season PA/value comparison. New signed heads are not converted to talent grades.'))
    e.write('scores.json',results);e.write('intervals.json',intervals);e.write('event-diagnostics.json',diagnostics)
    # Separate, pre-score-declared response sensitivity. No oracle forecast recentering.
    unit=pl.read_parquet(e.VALUE/'features.parquet').filter(pl.col('row_id').is_in(q['row_id'].to_list())).sort('row_id')
    assert unit['row_id'].equals(q['row_id'])
    origin_index=unit.select(['origin_env_'+v for v in e.EVENTS]).to_numpy()@VALUES
    target_index=unit.select(['target_env_'+v for v in e.EVENTS]).to_numpy()@VALUES
    delta=unit['next_pa'].to_numpy()*(target_index-origin_index)*UNIT/600
    assert np.allclose(unit['common_value_label']-unit['relative_value_label'],delta,atol=1e-10,rtol=0)
    relative=unit.select('row_id',pl.col('relative_value_label').alias('relative_actual_value'))
    neutral_results=[];neutral_intervals=[]
    with threadpool_limits(limits=2):
        for label,g in scopes:
            if g.is_empty():continue
            g=g.join(relative,on='row_id',validate='1:1').with_columns(pl.col('relative_actual_value').alias('next_value'))
            arms=ARMS+(['steamer'] if label=='public_broad' else [])
            neutral_results.append(dict(scope=label,rows=len(g),actual_pa=float(g['next_pa'].sum()),
                actual_relative_value=float(g['next_value'].sum()),scores={a:score(g,a) for a in arms}))
            if label in ['all','public_broad','never_debut','upper_never_debut','lower_never_debut']:
                for a in ['direct','active','counts']:
                    neutral_intervals.append(dict(scope=label,**paired(g,a,'current','value')))
    e.write('season-relative-sensitivity.json',dict(scores=neutral_results,intervals=neutral_intervals,
        labels_independently_verified=True,forecasts_unchanged=True,target_environment_not_given_to_forecasts=True,
        claim='Secondary response check; signed heads trained common-origin, not a matched neutral-training comparison'))
    q.write_parquet(e.OUT/'scored-predictions.parquet')
    selected={}
    def choose(g,reason):
        assert len(g);selected.setdefault(int(g['row_id'][0]),[]).append(reason)
    for pid,y in e.FIXED:
        choose(q.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y)),'fixed diagnostic')
    for a in ['direct','active','counts']:
        g=q.with_columns(((pl.col('current_value')-pl.col('next_value'))**2-
            (pl.col(a+'_value')-pl.col('next_value'))**2).alias('gain'))
        choose(g.sort('gain',descending=True),a+' largest value gain')
        choose(g.sort('gain'),a+' largest value harm')
    errors=q.with_columns((pl.col('counts_pa')-pl.col('next_pa')).alias('error'))
    choose(errors.sort('error',descending=True),'counts largest PA false high')
    choose(errors.sort('error'),'counts largest PA false low')
    choose(errors.filter(pl.col('next_pa').is_between(200,600)).sort(pl.col('error').abs()),'counts ordinary active')
    history=pl.read_parquet(e.COUNTS);profiles=pl.read_parquet(e.OUT/'profile-support.parquet');cases=[]
    oldcols=e.read(e.previous.OUT/'preflight.json')['pa_features']
    ratecols=e.read(e.ROOT/'reports/generated/practical-hitter-numeric-repair-v53/preflight.json')['rate_features']
    with threadpool_limits(limits=2):
        for rid,reasons in selected.items():
            r=q.filter(pl.col('row_id')==rid).row(0,named=True);s=source.filter(pl.col('row_id')==rid)
            row=s.row(0,named=True);y,k=r['origin_year'],r['outer_fold'];x=s.select(pre['features']).to_numpy()[0]
            note=e.read(e.OUT/f'fit-{y}-{k}.json');traces={}
            for h in note['heads']:
                m=joblib.load(h['path'])
                traces[h['head']]=poisson_trace(m,x,pre['features']) if h['head'].startswith('count_') else trace(m,x,pre['features'])
            current={}
            for h in e.read(e.previous.OUT/f'fit-{y}-{k}.json')['heads']:
                m=joblib.load(h['path']);sx=s.select(oldcols).to_numpy()[0]
                current[h['head']]=logit_trace(m,sx,oldcols) if h['head']=='participation' else trace(m,sx,oldcols)
            h=next(h for h in e.read(e.ROOT/f'reports/generated/practical-hitter-numeric-repair-v53/fit-{y}-{k}.json')['heads'] if h['head']=='rate')
            current['rate']=linear_trace(joblib.load(h['path']),safe_matrix(s,ratecols)[0],ratecols)
            comparison=peers(source,row)
            comparable=q.select('row_id',*[a+'_'+m for a in ARMS for m in ['pa','value']],'next_pa','next_value')
            comparison=comparison.join(comparable,on='row_id',validate='1:1')
            fields=['row_id','player_id','player_name','age','stage','pa_0','minor_pa_0','AA_0_pa','AAA_0_pa',
                'scout_rank_score_0','translated_K','translated_UBB','translated_HR','pooled_mlb_quality','comparison_distance',
                *[a+'_'+m for a in ARMS for m in ['pa','value']],'next_pa','next_value']
            # Actual future response is added only AFTER origin-only peer selection.
            fields=list(dict.fromkeys(fields));comparison=comparison.drop('next_pa','next_value').join(
                q.select('row_id','next_pa','next_value'),on='row_id',validate='1:1')
            component=[]
            for i,v in enumerate(e.EVENTS):
                n=r['counts_mean_'+v]
                component.append(dict(event=v,mean=n,raw_mean=r['counts_raw_'+v],
                    contribution=float(n*((VALUES[i]-row['origin_index'])*UNIT/600+row['value_replacement_rate']))))
            assert np.isclose(sum(c['contribution'] for c in component),r['counts_value'],atol=1e-10)
            actualinputs={n:row[n] for n in pre['features']}
            cases.append(dict(origin=r,selection=reasons,actual_inputs=actualinputs,
                legacy_display_differences={n:dict(old_display=r[n],actual_input=v) for n,v in actualinputs.items() if n in r and r[n]!=v},
                origin_environment={v:row['origin_env_'+v] for v in e.EVENTS},replacement=row['value_replacement_rate'],
                season_relative_actual_value=float(unit.filter(pl.col('row_id')==rid)['relative_value_label'][0]),
                translated_profile={n:row[n] for n in row if n.startswith(('translated_','translation_'))},
                source_history=history.filter((pl.col('player_id')==r['player_id'])&pl.col('season').is_between(y-2,y)).sort('season','bucket').to_dicts(),
                actual_history=history.filter((pl.col('player_id')==r['player_id'])&(pl.col('season')==y+1)&(pl.col('bucket')=='MLB')).to_dicts(),
                saved_traces=traces,current_saved_traces=current,event_contributions=component,
                training_profiles=profiles.filter(pl.col('row_id')==rid).to_dicts(),
                peers_selected_without_outcomes=comparison.select(fields).to_dicts(),
                peer_limit='Closer on measured upper-level exposure/production than age-only controls, not equivalent position, health, scouting detail or actual future roster openings'))
    e.write('cases.json',cases)
    e.write('verification.json',dict(new_heads_replayed=replayed,expected_heads=350,
        all_original_anchor_columns_bit_exact=True,PA_and_value_accounting_verified=True,
        count_means_nonnegative=True,count_physical_incompatibilities=0,cases=len(cases),
        player_walkthrough_status='pending',current_candidate_changed=False,protected_outcomes_used=False))
    for z in results[:7]:
        print(z['scope'],{a:(round(s['pa_rmse'],3),round(s['pa_mae'],3),round(s['value_rmse'],6)) for a,s in z['scores'].items()},flush=True)
    print('All scored results provisional; actual player reviews pending.',len(cases),flush=True)


if __name__=='__main__':main()
