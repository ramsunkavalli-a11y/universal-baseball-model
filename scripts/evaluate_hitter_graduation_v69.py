"""One matched graduation representation test; fixed talent and historical folds."""
from pathlib import Path
import sys
import joblib
import numpy as np
import polars as pl
from sklearn.ensemble import HistGradientBoostingClassifier,HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits
from universal_baseball.forecast_validation import preflight
from universal_baseball.prospect_graduation import overlay,FEATURES
from universal_baseball.storage import sha256_file
from universal_baseball.practical_hitter_v30 import score
from universal_baseball.histogram_prediction_trace import trace
from fit_practical_hitter_v31 import weights
from score_practical_hitter_v31 import paired
from score_hitter_readiness_v49 import probability_score
from evaluate_hitter_readiness_v49 import logit_trace
import evaluate_hitter_preseason_readiness_v68 as prior

ROOT=prior.ROOT
OUT=ROOT/'reports/generated/hitter-graduation-v69'
RAW=ROOT/'reports/generated/practical-hitter-v31/dated-stints.parquet'
FIXED=[(640457,2018),(641583,2018),(592450,2016),(694671,2023),(701762,2024),(666160,2016),(806956,2024),(666163,2023)]
read=prior.read


def write(n,obj):
    import json
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/n).write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False,default=str)+'\n',encoding='utf8')


def profile(f):
    return prior.tagged(f).with_columns(pl.any_horizontal([pl.col('scout_listed_1')==1,pl.col('scout_listed_2')==1]).alias('previously_listed'))


def prepare():
    assert not (OUT/'preflight.json').exists(),'Preserve prior experiment'
    report=read(prior.OUT/'report.json');assert report['player_walkthrough_status']=='complete'
    for k in ['input_hashes','output_hashes','review_code_hashes']:
        for p,h in report[k].items():assert sha256_file(Path(p))==h,p
    anchor=pl.read_parquet(prior.OUT/'features.parquet').sort('row_id')
    raw=pl.read_parquet(RAW).filter(pl.col('season')<=2024);new=overlay(anchor,raw).sort('row_id')
    assert new.select(anchor.columns).equals(anchor) and len(new)==63282
    # Independent cutoff sum: no future AB can contribute to a player/origin.
    mlb=raw.filter(pl.col('sport_id')==1);check=anchor.select('row_id','player_id','origin_year').join(mlb.select('player_id','season','at_bats'),on='player_id',how='left')
    check=check.group_by('row_id').agg(pl.when(pl.col('season')<=pl.col('origin_year')).then(pl.col('at_bats')).otherwise(0).sum().alias('ab')).sort('row_id')
    assert check['ab'].equals(new['observed_mlb_ab_lower_bound'])
    OUT.mkdir(parents=True,exist_ok=True);new.write_parquet(OUT/'features.parquet')
    pre=read(prior.OUT/'preflight.json');names=pre['pa_features']+FEATURES;assert len(names)==254
    supports=[];profiles=[];cells=[]
    for c in pre['cells']:
        checks={}
        for arm,f,cols in [('preseason',anchor,pre['pa_features']),('graduation',new,names)]:
            tr=f.filter(pl.col('row_id').is_in(c['training_row_ids']));te=f.filter(pl.col('row_id').is_in(c['test_row_ids']))
            for head,sub in [('participation',tr),('conditional_pa',tr.filter(pl.col('next_pa')>0))]:
                sup,note=preflight(sub,te,cutoff=c['year'],fold=c['fold'],features=cols,expected_keys=te.select('row_id','horizon').iter_rows())
                checks[arm+'_'+head]=note;supports.append(sup.with_columns(pl.lit(arm).alias('arm'),pl.lit(head).alias('head')))
                a,b=profile(overlay(sub,raw) if arm=='preseason' else sub),profile(overlay(te,raw) if arm=='preseason' else te)
                for kind,keys in [('broad',['stage','prior_debut','age_band','rank_band']),('graduation',['stage','prior_debut','age_band','scout_ab_graduated','previously_listed'])]:
                    counts=a.group_by(keys).agg(pl.col('player_id').n_unique().alias('profile_people'))
                    profiles.append(b.select('row_id',*keys).join(counts,on=keys,how='left',validate='m:1').with_columns(
                        pl.col('profile_people').fill_null(0),pl.lit(arm).alias('arm'),pl.lit(head).alias('head'),pl.lit(kind).alias('kind')))
        cells.append(dict(**{k:v for k,v in c.items() if k!='source_preflight'},source_preflight=checks))
    pl.concat(supports).write_parquet(OUT/'support.parquet');pl.concat(profiles,how='diagonal_relaxed').write_parquet(OUT/'profile-support.parquet')
    source_cases=[]
    for pid,y in FIXED:
        r=new.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y)).row(0,named=True)
        source_cases.append(dict(player_id=pid,origin_year=y,name=r['player_name'],inputs={n:r[n] for n in ['observed_mlb_ab_lower_bound',*FEATURES]},
            mlb_ab_history=mlb.filter((pl.col('player_id')==pid)&(pl.col('season')<=y)).select('season','at_bats','plate_appearances').sort('season').to_dicts()))
    write('source-check.json',dict(rows=len(new),reconstructed_all_ab=True,min_source_year=int(mlb['season'].min()),max_feature_year=2024,
        all_original_inputs_unchanged=True,fixed=source_cases,qualification='AB is an observed lower bound. Zero graduation indicator does not establish eligibility; service days are not reconstructed.'))
    paths=[RAW,prior.OUT/'features.parquet',prior.OUT/'preflight.json',prior.OUT/'report.json',prior.OUT/'scored-predictions.parquet',OUT/'features.parquet',
        OUT/'support.parquet',OUT/'profile-support.parquet',OUT/'source-check.json',ROOT/'docs/hitter-graduation-v69-contract.md',Path(__file__),
        ROOT/'src/universal_baseball/prospect_graduation.py',ROOT/'scripts/fit_practical_hitter_v31.py']
    write('preflight.json',dict(cells=cells,pa_features=names,prior_features=pre['pa_features'],settings=pre['settings'],
        checks_before_fits=140,input_hashes={str(p):sha256_file(p) for p in paths},protected_outcomes_used=False))
    print('All AB reconstructed; original inputs unchanged; 140 actual checks saved before fits.',flush=True)
    for c in source_cases:print(c['name'],c['origin_year'],c['inputs'],flush=True)


def fit():
    pre=read(OUT/'preflight.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    new=pl.read_parquet(OUT/'features.parquet');q=pl.read_parquet(prior.OUT/'scored-predictions.parquet');fits=[]
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y,k=c['year'],c['fold'];pp=OUT/f'forecast-{y}-{k}.parquet'
            if pp.exists():
                n=read(OUT/f'fit-{y}-{k}.json');assert sha256_file(pp)==n['prediction_sha256']
                for h in n['heads']:assert sha256_file(Path(h['path']))==h['sha256']
                fits.append(n);continue
            tr=new.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id');te=new.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            result=q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id');assert result['row_id'].equals(te['row_id'])
            oldnote=read(prior.OUT/f'fit-{y}-{k}.json');heads=[];raw={}
            for head,sub in [('participation',tr),('conditional_pa',tr.filter(pl.col('next_pa')>0))]:
                bh=next(h for h in oldnote['heads'] if h['head']==head);assert sha256_file(Path(bh['path']))==bh['sha256']
                bm=joblib.load(bh['path']);bx=te.select(pre['prior_features']).to_numpy()
                br=bm.predict_proba(bx)[:,1] if head=='participation' else bm.predict(bx)
                assert np.allclose(br,result['preseason_raw_p' if head=='participation' else 'preseason_raw_conditional_pa'],rtol=0,atol=1e-10)
                m=(HistGradientBoostingClassifier if head=='participation' else HistGradientBoostingRegressor)(**pre['settings'])
                m.fit(sub.select(pre['pa_features']).to_numpy(),sub['next_active' if head=='participation' else 'next_pa'].to_numpy(),sample_weight=weights(sub))
                x=te.select(pre['pa_features']).to_numpy();raw[head]=m.predict_proba(x)[:,1] if head=='participation' else m.predict(x)
                assert np.isfinite(raw[head]).all();mp=OUT/f'{head}-{y}-{k}.joblib';joblib.dump(m,mp,compress=3)
                heads.append(dict(head=head,path=str(mp),sha256=sha256_file(mp),prior_path=bh['path'],prior_sha256=bh['sha256'],
                    training_rows=len(sub),training_people=sub['player_id'].n_unique(),max_target_year=int(sub['target_year'].max())))
            p=raw['participation'].copy();p[result['hard_unavailable'].to_numpy()|result['reported_retired'].to_numpy()]=0
            cond=np.clip(raw['conditional_pa'],1,800)
            result=result.with_columns(pl.Series('graduation_raw_p',raw['participation']),pl.Series('graduation_p',p),
                pl.Series('graduation_raw_conditional_pa',raw['conditional_pa']),pl.Series('graduation_conditional_pa',cond),
                pl.Series('graduation_pa',p*cond),pl.col('baseline_rate').alias('graduation_rate'))
            result=result.with_columns((pl.col('graduation_pa')*(pl.col('baseline_rate')/600+pl.col('origin_replacement_rate'))).alias('graduation_value'))
            assert result.select(q.columns).equals(q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id'))
            result.write_parquet(pp);n=dict(year=y,fold=k,information_date=c['information_date'],heads=heads,prediction_sha256=sha256_file(pp))
            write(f'fit-{y}-{k}.json',n);fits.append(n);print(f'Graduation {y}/{k}: two heads saved, V68 replayed.',flush=True)
    result=pl.concat([pl.read_parquet(OUT/f"forecast-{c['year']}-{c['fold']}.parquet") for c in pre['cells']]).sort('row_id')
    assert len(result)==30506 and result.select(q.columns).equals(q.sort('row_id'))
    result.write_parquet(OUT/'predictions.parquet');write('fits.json',fits)


def scoring():
    pre=read(OUT/'preflight.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    source=pl.read_parquet(OUT/'features.parquet');q=pl.read_parquet(OUT/'predictions.parquet').sort('row_id')
    old=pl.read_parquet(prior.OUT/'scored-predictions.parquet').sort('row_id');assert q.select(old.columns).equals(old)
    replayed=0
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            te=source.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id');f=q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            n=read(OUT/f"fit-{c['year']}-{c['fold']}.json")
            for h in n['heads']:
                for arm,path,hsh,cols in [('graduation',h['path'],h['sha256'],pre['pa_features']),('preseason',h['prior_path'],h['prior_sha256'],pre['prior_features'])]:
                    assert sha256_file(Path(path))==hsh;m=joblib.load(path);x=te.select(cols).to_numpy()
                    pred=m.predict_proba(x)[:,1] if h['head']=='participation' else m.predict(x)
                    assert np.allclose(pred,f[arm+('_raw_p' if h['head']=='participation' else '_raw_conditional_pa')],rtol=0,atol=1e-10);replayed+=1
    assert np.allclose(q['graduation_pa'],q['graduation_p']*q['graduation_conditional_pa'],atol=1e-10)
    assert np.allclose(q['graduation_value'],q['graduation_pa']*(q['baseline_rate']/600+q['origin_replacement_rate']),atol=1e-10)
    q=q.join(source.select('row_id','observed_mlb_ab_lower_bound',*FEATURES),on='row_id',validate='1:1')
    public=q.filter((pl.col('pa_0')>0)&pl.col('steamer_index').is_not_null()&pl.col('zips_index').is_not_null());assert len(public)==2627
    scopes=[('all',q),('public_broad',public),('previously_ranked_graduates',q.filter(pl.col('scout_graduated_prior_score')>0)),
        ('never_debut',q.filter(pl.col('prior_debut')==0)),('upper_never_debut',q.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Upper minors'))),
        ('lower_never_debut',q.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Lower minors'))),('current_MLB',q.filter(pl.col('pa_0')>0)),
        ('first_year_top_picks',q.filter((pl.col('draft_known')==1)&(pl.col('draft_year')==pl.col('origin_year'))&(pl.col('pick_number')<=15)))]
    scopes += [('origin_'+str(y),q.filter(pl.col('origin_year')==y)) for y in sorted(q['origin_year'].unique())]
    scopes += [('stage_'+s,q.filter(pl.col('stage')==s)) for s in sorted(q['stage'].unique())]
    scores=[];intervals=[]
    with threadpool_limits(limits=2):
        for name,g in scopes:
            if not len(g):continue
            scores.append(dict(scope=name,rows=len(g),people=g['player_id'].n_unique(),actual_pa=float(g['next_pa'].sum()),actual_value=float(g['next_value'].sum()),
                scores={a:score(g,a) for a in ['baseline','preseason','graduation']+(['steamer'] if name=='public_broad' else [])},
                probability={a:probability_score(g,a) for a in ['baseline','preseason','graduation']}))
            if name in ['all','public_broad','previously_ranked_graduates','upper_never_debut']:
                intervals.extend(dict(scope=name,**paired(g,'graduation',a,metric)) for a in ['baseline','preseason'] for metric in ['pa','value'])
    write('scores.json',scores);write('intervals.json',intervals);q.write_parquet(OUT/'scored-predictions.parquet')
    chosen={}
    def choose(f,why):
        assert len(f);chosen.setdefault(f['row_id'][0],[]).append(why)
    for pid,y in FIXED:choose(q.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y)),'fixed before fit')
    err=q.with_columns(((pl.col('preseason_value')-pl.col('next_value'))**2-(pl.col('graduation_value')-pl.col('next_value'))**2).alias('gain'),
        (pl.col('graduation_value')-pl.col('next_value')).alias('error'))
    for why,f in [('largest offense gain',err.sort('gain',descending=True)),('largest offense harm',err.sort('gain')),('major false high',err.sort('error',descending=True)),
        ('major false low',err.sort('error')),('ordinary active',err.filter(pl.col('next_pa').is_between(200,600)).sort(pl.col('error').abs()))]:choose(f,why)
    counts=pl.read_parquet(ROOT/'reports/generated/practical-hitter-v31/counts.parquet');raw=pl.read_parquet(RAW).filter((pl.col('sport_id')==1)&(pl.col('season')<=2024))
    profiles=pl.read_parquet(OUT/'profile-support.parquet');cases=[]
    with threadpool_limits(limits=2):
        for rid,reasons in chosen.items():
            r=q.filter(pl.col('row_id')==rid).row(0,named=True);te=source.filter(pl.col('row_id')==rid)
            n=read(OUT/f"fit-{r['origin_year']}-{r['outer_fold']}.json");traces={};probes={}
            for h in n['heads']:
                traces[h['head']]={}
                for a,path,cols in [('preseason',h['prior_path'],pre['prior_features']),('graduation',h['path'],pre['pa_features'])]:
                    m=joblib.load(path);x=te.select(cols).to_numpy()[0]
                    traces[h['head']][a]=logit_trace(m,x,cols) if h['head']=='participation' else trace(m,x,cols)
                m=joblib.load(h['path']);x=te.select(pre['pa_features']).to_numpy();x[0,-3:]=0
                probes[h['head']]=float(m.predict_proba(x)[0,1] if h['head']=='participation' else m.predict(x)[0])
            peers=q.filter((pl.col('origin_year')==r['origin_year'])&(pl.col('stage')==r['stage'])&(pl.col('prior_debut')==r['prior_debut'])&(pl.col('scout_ab_graduated')==r['scout_ab_graduated'])&(pl.col('player_id')!=r['player_id'])).with_columns(
                (((pl.col('age')-r['age'])/3)**2+((pl.col('minor_pa_0')-r['minor_pa_0'])/250)**2+4*(pl.col('draft_rank')-r['draft_rank'])**2).alias('distance')).sort('distance','player_id').head(4)
            cases.append(dict(origin=r,selection=reasons,information_date=n['information_date'],actual_inputs={col:te[col][0] for col in pre['pa_features']},
                mlb_ab_history=raw.filter((pl.col('player_id')==r['player_id'])&(pl.col('season')<=r['origin_year'])).select('season','at_bats','plate_appearances').sort('season').to_dicts(),
                source_history=counts.filter((pl.col('player_id')==r['player_id'])&pl.col('season').is_between(r['origin_year']-2,r['origin_year'])).sort('season','bucket').to_dicts(),
                actual_history=counts.filter((pl.col('player_id')==r['player_id'])&(pl.col('season')==r['target_year'])&(pl.col('bucket')=='MLB')).to_dicts(),
                saved_traces=traces,candidate_fit_with_graduation_features_zero=probes,probe_interpretation='Artificial fixed-fit probe, not causality or a validated forecast; MLB exposure still present.',
                training_profiles=profiles.filter(pl.col('row_id')==rid).to_dicts(),peers=peers.select('player_id','player_name','age','minor_pa_0',*FEATURES,
                    'baseline_pa','preseason_pa','graduation_pa','baseline_value','preseason_value','graduation_value','next_pa','next_value').to_dicts()))
    write('cases.json',cases);write('verification.json',dict(replayed_heads=replayed,expected_heads=140,unchanged_hitting=True,unchanged_anchor_forecasts=True,
        PA_product_verified=True,corrected_value_verified=True,player_walkthrough_status='pending',cases=len(cases),protected_outcomes_used=False,
        frozen_forecast_changed=False,conditional_clips=int(((q['graduation_raw_conditional_pa']<1)|(q['graduation_raw_conditional_pa']>800)).sum())))
    for s in scores[:8]:print(s['scope'],{a:(round(v['pa_rmse'],3),round(v['pa_mae'],3),round(v['value_rmse'],6),round(v['pa_total'])) for a,v in s['scores'].items()},flush=True)
    print('Scores provisional until actual player review.',flush=True)


if __name__=='__main__':{'prepare':prepare,'fit':fit,'score':scoring}[sys.argv[1]]()
