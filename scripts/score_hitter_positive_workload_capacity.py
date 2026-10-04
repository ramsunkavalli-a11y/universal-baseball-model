"""Reporting-only repair: explicitly restore row-ID order after prediction joins."""
import test_hitter_positive_workload_capacity as r
from test_hitter_positive_workload_capacity import (
    ROOT,OUT,FIXED,SETTINGS,read,write,verify,pl,np,joblib,threadpool_limits,
    forecast,value_score,paired,current,location,trace,sha256_file)
from pathlib import Path


def score():
    p=read(OUT/'preflight.json');verify(p['source_hashes']);verify(p['baseline_hashes'])
    heads=read(OUT/'fit-report.json')['heads']
    assert not (OUT/'scores.json').exists()
    write('reporting-amendment.json',dict(change='Sort the combined forecasts by row_id after joins; original equality check compared different row order. No missing rows or changed anchor values after canonical sorting.',
        original_runner_sha256=sha256_file(Path(r.__file__)),scorer_path=str(Path(__file__)),scorer_sha256=sha256_file(Path(__file__)),
        new_fits=0,training_or_features_changed=False,comparison_or_targets_changed=False,original_failed_before_scores=True))
    q=pl.read_parquet(current.OUT/'scored-predictions.parquet').sort('row_id');f=pl.read_parquet(current.OUT/'features.parquet')
    with threadpool_limits(limits=2):
        for arm in SETTINGS:
            pieces=[]
            for h in [n for n in heads if n['arm']==arm]:
                verify({h['path']:h['sha256'],h['prediction_path']:h['prediction_sha256']})
                saved=pl.read_parquet(h['prediction_path']).sort('row_id')
                te=f.filter(pl.col('row_id').is_in(saved['row_id'].to_list())).sort('row_id')
                assert te['row_id'].equals(saved['row_id'])
                raw=joblib.load(h['path']).predict(te.select(p['features']).to_numpy())
                assert np.allclose(raw,saved[arm+'_raw_conditional_pa'],atol=1e-10,rtol=0);pieces.append(saved)
            q=q.join(pl.concat(pieces),on='row_id',validate='1:1').sort('row_id')
            z=forecast(q[arm+'_raw_conditional_pa'],q['preseason_p'],q['preseason_rate'],q['origin_replacement_rate'])
            for key,val in z.items():assert np.allclose(val,q[arm+'_'+key],atol=1e-10,rtol=0)
    anchor=pl.read_parquet(current.OUT/'scored-predictions.parquet').sort('row_id')
    assert len(q)==30506 and q.select(anchor.columns).equals(anchor)
    scopes=[('all',q),('public',location.public(q)),('current_MLB',q.filter(pl.col('pa_0')>0)),
        ('absent_prior_debut',q.filter((pl.col('prior_debut')==1)&(pl.col('pa_0')==0))),
        ('upper_never_debut',q.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Upper minors'))),
        ('lower_never_debut',q.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Lower minors'))),
        ('thin_new_draftee',q.filter((pl.col('draft_known')==1)&(pl.col('draft_year')==pl.col('origin_year'))&
            (pl.sum_horizontal('minor_pa_0','minor_pa_1','minor_pa_2','pa_0','pa_1','pa_2')<150)))]
    scopes.extend((f'current_PA_{lo}_{hi}',q.filter(pl.col('pa_0').is_between(lo,hi))) for lo,hi in [(1,199),(200,399),(400,599),(600,10000)])
    scopes.extend((f'origin_{y}',q.filter(pl.col('origin_year')==y)) for y in sorted(q['origin_year'].unique()))
    scores=[];intervals=[]
    with threadpool_limits(limits=2):
        for scope,g in scopes:
            if not len(g):continue
            scores.append(dict(scope=scope,rows=len(g),people=g['player_id'].n_unique(),actual_pa=int(g['next_pa'].sum()),actual_value=float(g['next_value'].sum()),
                scores={a:value_score(g,a) for a in ['preseason',*SETTINGS]+(['steamer'] if scope=='public' else [])}))
            if scope in ['all','public','upper_never_debut','lower_never_debut','current_MLB','absent_prior_debut']:
                intervals.extend(dict(scope=scope,**paired(g,a,b,metric)) for a,b in [('deep_hist','preseason'),('lightgbm','preseason'),('lightgbm','deep_hist')] for metric in ['pa','value'])
    write('scores.json',scores);write('intervals.json',intervals)
    q.write_parquet(OUT/'scored-predictions.parquet');chosen={}
    def choose(g,why):assert len(g);chosen.setdefault(int(g['row_id'][0]),[]).append(why)
    for pid,y in FIXED:choose(q.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y)),'fixed before fit')
    for arm in SETTINGS:
        for metric in ['pa','value']:
            a=q.with_columns(((pl.col('preseason_'+metric)-pl.col('next_'+metric))**2-(pl.col(arm+'_'+metric)-pl.col('next_'+metric))**2).alias('gain'))
            choose(a.sort('gain','row_id',descending=[True,False]),arm+' largest '+metric+' gain')
            choose(a.sort('gain','row_id'),arm+' largest '+metric+' harm')
        a=q.with_columns((pl.col(arm+'_value')-pl.col('next_value')).alias('error'))
        choose(a.sort('error','row_id',descending=[True,False]),arm+' value false high')
        choose(a.sort('error','row_id'),arm+' value false low')
        choose(a.filter(pl.col('next_pa').is_between(200,600)).with_columns(pl.col('error').abs().alias('abs_error')).sort('abs_error','row_id'),arm+' ordinary active value')
    counts=pl.read_parquet(ROOT/'reports/generated/practical-hitter-v31/counts.parquet');profiles=pl.read_parquet(OUT/'profiles.parquet');cases=[]
    with threadpool_limits(limits=2):
        for rid,selection in chosen.items():
            row=q.filter(pl.col('row_id')==rid).row(0,named=True);te=f.filter(pl.col('row_id')==rid);x=te.select(p['features']).to_numpy();paths={}
            cell=next(c for c in p['cells'] if c['year']==row['origin_year'] and c['fold']==row['outer_fold'])
            for arm,h in [('preseason',cell['baseline_head'])]+[(n['arm'],n) for n in heads if n['year']==row['origin_year'] and n['fold']==row['outer_fold']]:
                model=joblib.load(h['path']);raw=float(model.predict(x)[0])
                col='preseason_raw_conditional_pa' if arm=='preseason' else arm+'_raw_conditional_pa'
                assert np.isclose(raw,row[col],atol=1e-10,rtol=0)
                if arm=='lightgbm':
                    contrib=model.booster_.predict(x,pred_contrib=True)[0];assert np.isclose(contrib.sum(),raw,atol=1e-10,rtol=0)
                    paths[arm]=dict(reference=float(contrib[-1]),raw_prediction=raw,feature_effects=[dict(feature=n,input=float(v),path_effect=float(t)) for n,v,t in zip(p['features'],x[0],contrib[:-1]) if t],interpretation='Saved LightGBM additive contributions, not causal between-model differences')
                else:paths[arm]=trace(model,x[0],p['features'])
            peers=q.filter((pl.col('origin_year')==row['origin_year'])&(pl.col('stage')==row['stage'])&(pl.col('prior_debut')==row['prior_debut'])&(pl.col('player_id')!=row['player_id'])).with_columns(
                (((pl.col('age')-row['age'])/3)**2+((pl.col('pa_0')-row['pa_0'])/250)**2+((pl.col('AAA_0_pa')-row['AAA_0_pa'])/250)**2+((pl.col('AA_0_pa')-row['AA_0_pa'])/250)**2+
                ((pl.col('minor_pa_0')-row['minor_pa_0'])/250)**2+(pl.col('quality_0')-row['quality_0'])**2+2*(pl.col('new_scout_rank_score_0')-row['new_scout_rank_score_0'])**2+
                (pl.col('source_position')!=row['source_position']).cast(pl.Float64)).alias('distance')).sort('distance','player_id').head(4)
            cols=['row_id','player_id','player_name','origin_year','target_year','outer_fold','age','stage','source_position','prior_debut','pa_0','minor_pa_0',
                'preseason_p','preseason_conditional_pa','preseason_pa','preseason_rate','preseason_value','next_pa','next_value','next_batting_rate',
                'on_40man','needs_availability_scenario']+[a+'_'+n for a in SETTINGS for n in ['raw_conditional_pa','conditional_pa','pa','value']]
            origin={n:row[n] for n in cols}
            if not origin['next_pa']:origin['next_batting_rate']=None
            peer_rows=peers.select(*cols,'distance').to_dicts()
            for peer in peer_rows:
                if not peer['next_pa']:peer['next_batting_rate']=None
            cases.append(dict(origin=origin,selection=selection,information_date=cell['information_date'],actual_inputs=te.select(p['features']).row(0,named=True),
                saved_conditional_paths=paths,profiles=profiles.filter(pl.col('row_id')==rid).to_dicts(),
                source_history=counts.filter((pl.col('player_id')==row['player_id'])&pl.col('season').is_between(row['origin_year']-2,row['origin_year'])).sort('season','bucket').to_dicts(),
                actual_history=counts.filter((pl.col('player_id')==row['player_id'])&(pl.col('season')==row['target_year'])&(pl.col('bucket')=='MLB')).to_dicts(),
                peers=peer_rows,peer_limit='Origin-known broad stage, separate exposure, age, position, rank and summary quality; not exact injury, rights or contact matches'))
    write('cases.json',cases);write('verification.json',dict(new_heads_replayed=70,baseline_conditional_heads_replayed_before_fits=35,
        current_columns_exact=True,all_PA_value_products_exact=True,probability_hitting_unchanged=True,player_walkthrough_status='pending',cases=len(cases),
        protected_outcomes_used=False,output_hashes={str(OUT/n):sha256_file(OUT/n) for n in ['scores.json','intervals.json','cases.json','scored-predictions.parquet']}))
    for s in scores[:7]:print(s['scope'],{a:tuple(round(v[m],5) for m in ['pa_rmse','pa_mae','value_rmse','pa_total']) for a,v in s['scores'].items()},flush=True)
    for c in cases:
        row=c['origin'];print(row['row_id'],row['player_name'],row['origin_year'],'PA',tuple(round(row[a+'_pa'],2) for a in ['preseason',*SETTINGS]),'actual',row['next_pa'],flush=True)
    print('Scores provisional until every selected player is reviewed.',flush=True)


if __name__=='__main__':score()
