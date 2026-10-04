"""Prefit support, locked conditional means, independent replay and cases."""
import json
import sys
import warnings
from pathlib import Path
import joblib
import lightgbm
import sklearn
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.storage import sha256_file
from universal_baseball.forecast_validation import preflight
from universal_baseball.hitter_positive_workload import SETTINGS,learner,forecast
from universal_baseball.histogram_prediction_trace import trace
from universal_baseball.practical_hitter_v30 import score as value_score
from fit_practical_hitter_v31 import weights
from score_practical_hitter_v31 import paired
import evaluate_hitter_preseason_readiness_v68 as current
import diagnose_hitter_workload_location as location

ROOT=current.ROOT;OUT=ROOT/'reports/generated/hitter-positive-workload-capacity'
EVIDENCE=ROOT/'reports/model-evidence/hitter-positive-workload-capacity'
FIXED=[(592450,2024),(456781,2022),(458015,2023),(474832,2023),(665487,2022),
       (694671,2023),(701762,2024),(668804,2018),(666163,2023)]
warnings.filterwarnings('ignore',message='X does not have valid feature names, but LGBMRegressor was fitted with feature names')


def read(p):return json.loads(Path(p).read_text(encoding='utf8'))


def write(name,obj):
    OUT.mkdir(parents=True,exist_ok=True);p=OUT/name
    assert not p.exists(),f'Preserve sealed receipt: {p}'
    p.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n')


def verify(paths):
    for p,h in paths.items():assert sha256_file(Path(p))==h,p


def prepare():
    final=read(ROOT/'reports/generated/hitter-error-budget/final-report.json')
    assert final['player_walkthrough_status']=='complete';verify(final['evidence_hashes'])
    old=read(current.OUT/'preflight.json');verify(old['input_hashes'])
    releases=read(current.SOURCE/'source-report.json')['release_evidence']
    f=pl.read_parquet(current.OUT/'features.parquet');q=pl.read_parquet(current.OUT/'scored-predictions.parquet')
    assert len(f)==63282 and len(q)==30506 and q['target_year'].max()==2025
    names=old['pa_features'];assert len(names)==251 and not any(n.startswith('next_') for n in names)
    checks=[];profiles=[];cells=[];hashes={};baseline_replays=0
    with threadpool_limits(limits=2):
        for c in old['cells']:
            y,k=c['year'],c['fold'];tr=f.filter(pl.col('row_id').is_in(c['training_row_ids'])).filter(pl.col('next_pa')>0).sort('row_id')
            te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id');v=q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            assert te['row_id'].equals(v['row_id']) and not (tr['target_year']==2020).any()
            assert len(tr)==c['conditional_training_rows']
            npth=current.OUT/f'fit-{y}-{k}.json';note=read(npth);h=next(h for h in note['heads'] if h['head']=='conditional_pa')
            verify({h['path']:h['sha256']});assert len(tr)==h['training_rows'] and tr['player_id'].n_unique()==h['training_people']
            assert tr['target_year'].max()==h['max_target_year']<=y
            assert np.allclose(joblib.load(h['path']).predict(te.select(names).to_numpy()),v['preseason_raw_conditional_pa'],atol=1e-10,rtol=0)
            hashes[str(npth)]=sha256_file(npth);hashes[h['path']]=h['sha256'];baseline_replays+=1
            assert releases[str(y+1)]['date']==c['information_date']
            assert max(releases[str(t)]['date'] for t in tr['target_year'].unique())<c['information_date']
            for arm in SETTINGS:
                s,n=preflight(tr,te,cutoff=y,fold=k,features=names,expected_keys=te.select('row_id','horizon').iter_rows())
                checks.append(dict(arm=arm,year=y,fold=k,information_date=c['information_date'],**n))
            def tagged(g):
                return current.tagged(g).with_columns(pl.when(pl.col('pa_0')==0).then(0)
                    .when(pl.col('pa_0')<200).then(1).when(pl.col('pa_0')<400).then(2)
                    .when(pl.col('pa_0')<600).then(3).otherwise(4).alias('prior_pa_band'))
            a,b=tagged(tr),tagged(te)
            for kind,keys in [('broad',['prior_debut','stage','age_band','rank_band']),
                              ('refined',['prior_debut','stage','age_band','rank_band','new_draftee','thin_pro']),
                              ('workload',['prior_debut','stage','age_band','prior_pa_band']),
                              ('workload_refined',['prior_debut','stage','age_band','rank_band','prior_pa_band','new_draftee','thin_pro'])]:
                count=a.group_by(keys).agg(pl.col('player_id').n_unique().alias('profile_people'))
                profiles.append(b.select('row_id',*keys).join(count,on=keys,how='left',validate='m:1').with_columns(
                    pl.col('profile_people').fill_null(0),pl.lit(kind).alias('kind'),pl.lit(y).alias('outer_year'),pl.lit(k).alias('outer_fold')))
            cells.append(dict(year=y,fold=k,training_row_ids=tr['row_id'].to_list(),test_row_ids=te['row_id'].to_list(),
                information_date=c['information_date'],baseline_head=h,prior_pa_range=[float(tr['pa_0'].min()),float(tr['pa_0'].max())]))
    OUT.mkdir(parents=True,exist_ok=True);pl.concat(profiles,how='diagonal_relaxed').write_parquet(OUT/'profiles.parquet')
    paths=[Path(__file__),ROOT/'src/universal_baseball/hitter_positive_workload.py',ROOT/'tests/test_hitter_positive_workload.py',
        ROOT/'docs/hitter-positive-workload-capacity-contract.md',current.OUT/'features.parquet',current.OUT/'scored-predictions.parquet',
        current.OUT/'preflight.json',ROOT/'reports/generated/hitter-error-budget/final-report.json',OUT/'profiles.parquet',
        ROOT/'scripts/fit_practical_hitter_v31.py',ROOT/'src/universal_baseball/forecast_validation.py',
        current.SOURCE/'source-report.json',Path(current.__file__),Path(location.__file__),
        ROOT/'scripts/score_practical_hitter_v31.py',ROOT/'src/universal_baseball/practical_hitter_v30.py',
        ROOT/'src/universal_baseball/histogram_prediction_trace.py',ROOT/'reports/generated/practical-hitter-v31/counts.parquet']
    write('preflight.json',dict(new_fits=0,checks_before_fits=70,checks=checks,cells=cells,features=names,settings=SETTINGS,
        versions=dict(sklearn=sklearn.__version__,lightgbm=lightgbm.__version__),baseline_conditional_replays=baseline_replays,
        baseline_hashes=hashes,source_hashes={str(p):sha256_file(p) for p in paths},fixed_cases=FIXED,
        protected_outcomes_used=False,player_walkthrough_status='pending'))
    print('All seventy actual active-subset preflights saved; thirty-five current heads replayed before fitting.',flush=True)


def fit():
    p=read(OUT/'preflight.json');verify(p['source_hashes']);verify(p['baseline_hashes'])
    f=pl.read_parquet(current.OUT/'features.parquet');q=pl.read_parquet(current.OUT/'scored-predictions.parquet');notes=[]
    with threadpool_limits(limits=2):
        for c in p['cells']:
            y,k=c['year'],c['fold'];tr=f.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id')
            te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id');v=q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            for arm in SETTINGS:
                note_path=OUT/f'{arm}-{y}-{k}.json'
                if note_path.exists():
                    h=read(note_path);verify({h['path']:h['sha256'],h['prediction_path']:h['prediction_sha256']});notes.append(h);continue
                model=learner(arm);model.fit(tr.select(p['features']).to_numpy(),tr['next_pa'].to_numpy(),sample_weight=weights(tr))
                raw=model.predict(te.select(p['features']).to_numpy());terms=forecast(raw,v['preseason_p'],v['preseason_rate'],v['origin_replacement_rate'])
                prediction=v.select('row_id').with_columns([pl.Series(arm+'_'+name,x) for name,x in terms.items()])
                mp=OUT/f'{arm}-{y}-{k}.joblib';pp=OUT/f'{arm}-{y}-{k}.parquet';joblib.dump(model,mp,compress=3);prediction.write_parquet(pp)
                h=dict(arm=arm,year=y,fold=k,path=str(mp),sha256=sha256_file(mp),prediction_path=str(pp),prediction_sha256=sha256_file(pp),
                    training_rows=len(tr),training_people=tr['player_id'].n_unique(),settings=model.get_params(),
                    negative_raw=int((raw<1).sum()),high_raw=int((raw>800).sum()),raw_min=float(raw.min()),raw_max=float(raw.max()))
                write(note_path.name,h);notes.append(h);print(arm,y,k,'saved',flush=True)
    assert len(notes)==70;write('fit-report.json',dict(heads=notes,new_heads=70,player_walkthrough_status='pending',protected_outcomes_used=False))


def score():
    p=read(OUT/'preflight.json');verify(p['source_hashes']);verify(p['baseline_hashes']);heads=read(OUT/'fit-report.json')['heads']
    assert not (OUT/'scores.json').exists();q=pl.read_parquet(current.OUT/'scored-predictions.parquet').sort('row_id');f=pl.read_parquet(current.OUT/'features.parquet')
    with threadpool_limits(limits=2):
        for arm in SETTINGS:
            pieces=[]
            for h in [n for n in heads if n['arm']==arm]:
                verify({h['path']:h['sha256'],h['prediction_path']:h['prediction_sha256']});saved=pl.read_parquet(h['prediction_path']).sort('row_id')
                te=f.filter(pl.col('row_id').is_in(saved['row_id'])).sort('row_id');raw=joblib.load(h['path']).predict(te.select(p['features']).to_numpy())
                assert np.allclose(raw,saved[arm+'_raw_conditional_pa'],atol=1e-10,rtol=0);pieces.append(saved)
            q=q.join(pl.concat(pieces),on='row_id',validate='1:1')
            z=forecast(q[arm+'_raw_conditional_pa'],q['preseason_p'],q['preseason_rate'],q['origin_replacement_rate'])
            for key,val in z.items():assert np.allclose(val,q[arm+'_'+key],atol=1e-10,rtol=0)
    anchor=pl.read_parquet(current.OUT/'scored-predictions.parquet').sort('row_id');assert q.select(anchor.columns).equals(anchor)
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
    q.write_parquet(OUT/'scored-predictions.parquet')
    chosen={}
    def choose(g,why):assert len(g);chosen.setdefault(int(g['row_id'][0]),[]).append(why)
    for pid,y in FIXED:choose(q.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y)),'fixed before fit')
    for arm in SETTINGS:
        for metric in ['pa','value']:
            a=q.with_columns(((pl.col('preseason_'+metric)-pl.col('next_'+metric))**2-(pl.col(arm+'_'+metric)-pl.col('next_'+metric))**2).alias('gain'))
            choose(a.sort('gain','row_id',descending=[True,False]),arm+' largest '+metric+' gain');choose(a.sort('gain','row_id'),arm+' largest '+metric+' harm')
        a=q.with_columns((pl.col(arm+'_value')-pl.col('next_value')).alias('error'))
        choose(a.sort('error','row_id',descending=[True,False]),arm+' value false high');choose(a.sort('error','row_id'),arm+' value false low')
        choose(a.filter(pl.col('next_pa').is_between(200,600)).with_columns(pl.col('error').abs().alias('abs_error')).sort('abs_error','row_id'),arm+' ordinary active value')
    counts=pl.read_parquet(ROOT/'reports/generated/practical-hitter-v31/counts.parquet');profiles=pl.read_parquet(OUT/'profiles.parquet');cases=[]
    with threadpool_limits(limits=2):
        for rid,selection in chosen.items():
            r=q.filter(pl.col('row_id')==rid).row(0,named=True);te=f.filter(pl.col('row_id')==rid);x=te.select(p['features']).to_numpy();paths={}
            cell=next(c for c in p['cells'] if c['year']==r['origin_year'] and c['fold']==r['outer_fold'])
            for arm,h in [('preseason',cell['baseline_head'])]+[(n['arm'],n) for n in heads if n['year']==r['origin_year'] and n['fold']==r['outer_fold']]:
                model=joblib.load(h['path']);raw=float(model.predict(x)[0]);col='preseason_raw_conditional_pa' if arm=='preseason' else arm+'_raw_conditional_pa'
                assert np.isclose(raw,r[col],atol=1e-10,rtol=0)
                if arm=='lightgbm':
                    contrib=model.booster_.predict(x,pred_contrib=True)[0];assert np.isclose(contrib.sum(),raw,atol=1e-10,rtol=0)
                    paths[arm]=dict(reference=float(contrib[-1]),raw_prediction=raw,feature_effects=[dict(feature=n,input=float(v),path_effect=float(t)) for n,v,t in zip(p['features'],x[0],contrib[:-1]) if t],interpretation='Saved LightGBM additive contributions, not causal between-model differences')
                else:paths[arm]=trace(model,x[0],p['features'])
            peers=q.filter((pl.col('origin_year')==r['origin_year'])&(pl.col('stage')==r['stage'])&(pl.col('prior_debut')==r['prior_debut'])&(pl.col('player_id')!=r['player_id'])).with_columns(
                (((pl.col('age')-r['age'])/3)**2+((pl.col('pa_0')-r['pa_0'])/250)**2+((pl.col('AAA_0_pa')-r['AAA_0_pa'])/250)**2+((pl.col('AA_0_pa')-r['AA_0_pa'])/250)**2+
                ((pl.col('minor_pa_0')-r['minor_pa_0'])/250)**2+(pl.col('quality_0')-r['quality_0'])**2+2*(pl.col('new_scout_rank_score_0')-r['new_scout_rank_score_0'])**2+
                (pl.col('source_position')!=r['source_position']).cast(pl.Float64)).alias('distance')).sort('distance','player_id').head(4)
            cols=['row_id','player_id','player_name','origin_year','target_year','outer_fold','age','stage','source_position','prior_debut','pa_0','minor_pa_0',
                'preseason_p','preseason_conditional_pa','preseason_pa','preseason_rate','preseason_value','next_pa','next_value','next_batting_rate',
                'on_40man','needs_availability_scenario']+[a+'_'+n for a in SETTINGS for n in ['raw_conditional_pa','conditional_pa','pa','value']]
            origin={n:r[n] for n in cols}
            if not origin['next_pa']:origin['next_batting_rate']=None
            peer_rows=peers.select(*cols,'distance').to_dicts()
            for peer in peer_rows:
                if not peer['next_pa']:peer['next_batting_rate']=None
            cases.append(dict(origin=origin,selection=selection,information_date=cell['information_date'],actual_inputs=te.select(p['features']).row(0,named=True),
                saved_conditional_paths=paths,profiles=profiles.filter(pl.col('row_id')==rid).to_dicts(),
                source_history=counts.filter((pl.col('player_id')==r['player_id'])&pl.col('season').is_between(r['origin_year']-2,r['origin_year'])).sort('season','bucket').to_dicts(),
                actual_history=counts.filter((pl.col('player_id')==r['player_id'])&(pl.col('season')==r['target_year'])&(pl.col('bucket')=='MLB')).to_dicts(),
                peers=peer_rows,peer_limit='Origin-known broad stage, separate exposure, age, position, rank and summary quality; not exact injury, rights or contact matches'))
    write('cases.json',cases);write('verification.json',dict(new_heads_replayed=70,baseline_conditional_heads_replayed_before_fits=35,
        current_columns_exact=True,all_PA_value_products_exact=True,probability_hitting_unchanged=True,player_walkthrough_status='pending',cases=len(cases),
        protected_outcomes_used=False,output_hashes={str(OUT/n):sha256_file(OUT/n) for n in ['scores.json','intervals.json','cases.json','scored-predictions.parquet']}))
    for s in scores[:7]:print(s['scope'],{a:tuple(round(v[m],5) for m in ['pa_rmse','pa_mae','value_rmse','pa_total']) for a,v in s['scores'].items()},flush=True)
    for c in cases:
        r=c['origin'];print(r['row_id'],r['player_name'],r['origin_year'],'PA',tuple(round(r[a+'_pa'],2) for a in ['preseason',*SETTINGS]),'actual',r['next_pa'],flush=True)
    print('Scores provisional until every selected player is reviewed.',flush=True)


if __name__=='__main__':{'prepare':prepare,'fit':fit,'score':score}[sys.argv[1]]()
