"""Exact existing smooth opportunity model; change only ranking vintage."""
from pathlib import Path
import sys,warnings
import joblib
import numpy as np
import polars as pl
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression,Ridge
from sklearn.exceptions import ConvergenceWarning
from threadpoolctl import threadpool_limits
from universal_baseball.forecast_validation import preflight
from universal_baseball.prospect_shared_history import materialize
from universal_baseball.storage import sha256_file
from universal_baseball.practical_hitter_v30 import score
from fit_practical_hitter_v31 import weights
from score_practical_hitter_v31 import paired
from score_hitter_readiness_v49 import probability_score
from score_hitter_prospect_pooling_v54 import linear_trace
import evaluate_hitter_preseason_readiness_v68 as trees
import evaluate_hitter_prospect_pooling_v54 as smooth

ROOT=trees.ROOT;OUT=ROOT/'reports/generated/hitter-smooth-preseason-v73';read=trees.read
FIXED=[(701762,2024),(694671,2023),(641355,2016),(624413,2018),(666160,2016),(669394,2017),(806956,2024),(677594,2021)]
ARMS=['baseline','preseason','old_smooth','smooth_preseason']


def write(n,o):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/n).write_text(trees.json.dumps(o,indent=2,ensure_ascii=False,allow_nan=False,default=str)+'\n',encoding='utf8')


def prepare():
    assert not (OUT/'preflight.json').exists(),'Preserve prior experiment'
    for p in [trees.OUT/'report.json',smooth.OUT/'report.json']:
        r=read(p);assert r['player_walkthrough_status']=='complete'
        for key in ['input_hashes','output_hashes','review_code_hashes']:
            for path,h in r.get(key,{}).items():assert sha256_file(Path(path))==h,path
    old=pl.read_parquet(smooth.OUT/'features.parquet').sort('row_id')
    new,names=materialize(pl.read_parquet(trees.OUT/'features.parquet').sort('row_id'))
    prior=read(smooth.OUT/'preflight.json');tree_pre=read(trees.OUT/'preflight.json');assert names==prior['features'] and old['row_id'].equals(new['row_id'])
    changed=[c for c in names if not old[c].equals(new[c])];assert all(c.startswith('scout_') for c in changed)
    assert old['next_pa'].equals(new['next_pa']) and old['next_active'].equals(new['next_active'])
    q=pl.read_parquet(trees.OUT/'scored-predictions.parquet');assert len(q)==30506
    OUT.mkdir(parents=True,exist_ok=True);new.write_parquet(OUT/'features.parquet');supports=[];profiles=[];cells=[]
    with threadpool_limits(limits=2):
        for c,d in zip(prior['cells'],tree_pre['cells']):
            assert (c['year'],c['fold'])==(d['year'],d['fold']) and c['test_row_ids']==d['test_row_ids']
            tr=new.filter(pl.col('row_id').is_in(d['training_row_ids'])&(pl.col('prior_debut')==0)).sort('row_id')
            assert tr['row_id'].to_list()==c['prospect_training_ids']
            before=old.filter(pl.col('row_id').is_in(c['prospect_test_ids'])).sort('row_id')
            te=new.filter(pl.col('row_id').is_in(c['prospect_test_ids'])).sort('row_id');checks={}
            old_note=read(smooth.OUT/f"fit-{c['year']}-{c['fold']}.json");saved=pl.read_parquet(smooth.OUT/f"forecast-{c['year']}-{c['fold']}.parquet").filter(pl.col('prior_debut')==0).sort('row_id')
            assert saved['row_id'].equals(te['row_id'])
            for arm,full,test in [('old_smooth',old,before),('smooth_preseason',new,te)]:
                training=full.filter(pl.col('row_id').is_in(c['prospect_training_ids'])).sort('row_id')
                for head,sub in [('participation',training),('conditional_pa',training.filter(pl.col('next_pa')>0))]:
                    sp,note=preflight(sub,test,cutoff=c['year'],fold=c['fold'],features=names,expected_keys=test.select('row_id','horizon').iter_rows())
                    checks[arm+'_'+head]=note;supports.append(sp.with_columns(pl.lit(arm).alias('arm'),pl.lit(head).alias('head')))
                    for kind,keys in [('broad',['stage','age_band','rank_band']),('refined',['stage','age_band','rank_band','new_draftee','thin_pro'])]:
                        a,b=trees.tagged(sub),trees.tagged(test);counts=a.group_by(keys).agg(pl.col('player_id').n_unique().alias('profile_people'))
                        profiles.append(b.select('row_id',*keys).join(counts,on=keys,how='left',validate='m:1').with_columns(pl.col('profile_people').fill_null(0),
                            pl.lit(arm).alias('arm'),pl.lit(head).alias('head'),pl.lit(kind).alias('kind')))
                    if arm=='old_smooth':
                        h=next(h for h in old_note['heads'] if h['head']==head);assert sha256_file(Path(h['path']))==h['sha256'];m=joblib.load(h['path'])
                        pred=m.predict_proba(before.select(names).to_numpy())[:,1] if head=='participation' else m.predict(before.select(names).to_numpy())
                        if head=='participation':pred[saved['hard_unavailable'].to_numpy()|saved['reported_retired'].to_numpy()]=0
                        else:pred=np.clip(pred,1,800)
                        assert np.allclose(pred,saved['shared_p' if head=='participation' else 'shared_conditional_pa'],atol=1e-10,rtol=0)
            cells.append(dict(**c,information_date=d['information_date'],checks=checks))
    pl.concat(supports).write_parquet(OUT/'support.parquet');pl.concat(profiles,how='diagonal_relaxed').write_parquet(OUT/'profile-support.parquet')
    paths=[trees.OUT/'report.json',trees.OUT/'features.parquet',trees.OUT/'preflight.json',trees.OUT/'scored-predictions.parquet',
        smooth.OUT/'report.json',smooth.OUT/'features.parquet',smooth.OUT/'preflight.json',smooth.OUT/'predictions.parquet',
        OUT/'features.parquet',OUT/'support.parquet',OUT/'profile-support.parquet',Path(__file__),ROOT/'src/universal_baseball/prospect_shared_history.py',
        ROOT/'scripts/fit_practical_hitter_v31.py',ROOT/'docs/hitter-smooth-preseason-v73-contract.md']
    write('preflight.json',dict(cells=cells,features=names,changed_features=changed,settings=prior['settings'],checks_before_fits=140,old_heads_replayed_before_fits=70,
        input_hashes={str(p):sha256_file(p) for p in paths},established_candidate_unchanged=True,unchanged_hitting=True,protected_outcomes_used=False))
    print('140 checks and 70 old-head replays completed before new fits; only eight ranking inputs differ.',flush=True)


def fit():
    pre=read(OUT/'preflight.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    f=pl.read_parquet(OUT/'features.parquet');old=pl.read_parquet(smooth.OUT/'features.parquet');anchor=pl.read_parquet(trees.OUT/'scored-predictions.parquet');fits=[]
    with threadpool_limits(limits=2),warnings.catch_warnings():
        warnings.simplefilter('error',ConvergenceWarning)
        for c in pre['cells']:
            y,k=c['year'],c['fold'];pp=OUT/f'forecast-{y}-{k}.parquet'
            if pp.exists():
                n=read(OUT/f'fit-{y}-{k}.json');assert sha256_file(pp)==n['prediction_sha256']
                for h in n['heads']:assert sha256_file(Path(h['path']))==h['sha256']
                fits.append(n);continue
            tr=f.filter(pl.col('row_id').is_in(c['prospect_training_ids'])).sort('row_id');te=f.filter(pl.col('row_id').is_in(c['prospect_test_ids'])).sort('row_id')
            before=old.filter(pl.col('row_id').is_in(c['prospect_test_ids'])).sort('row_id');q=anchor.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            mask=q['prior_debut'].to_numpy()==0;assert np.array_equal(q['row_id'].to_numpy()[mask],te['row_id'].to_numpy());heads=[];raw={a:{} for a in ['old_smooth','smooth_preseason']}
            old_note=read(smooth.OUT/f'fit-{y}-{k}.json')
            for head,sub in [('participation',tr),('conditional_pa',tr.filter(pl.col('next_pa')>0))]:
                h=next(h for h in old_note['heads'] if h['head']==head);assert sha256_file(Path(h['path']))==h['sha256'];bm=joblib.load(h['path'])
                bx=before.select(pre['features']).to_numpy();raw['old_smooth'][head]=bm.predict_proba(bx)[:,1] if head=='participation' else bm.predict(bx)
                s=pre['settings'];learner=LogisticRegression(C=s['logistic_C'],max_iter=s['max_iter'],tol=s['tol'],solver='lbfgs') if head=='participation' else Ridge(alpha=s['ridge_alpha'])
                m=make_pipeline(StandardScaler(),learner);m.fit(sub.select(pre['features']).to_numpy(),sub['next_active' if head=='participation' else 'next_pa'].to_numpy(),
                    **{('logisticregression' if head=='participation' else 'ridge')+'__sample_weight':weights(sub)})
                x=te.select(pre['features']).to_numpy();raw['smooth_preseason'][head]=m.predict_proba(x)[:,1] if head=='participation' else m.predict(x)
                assert np.isfinite(raw['smooth_preseason'][head]).all();mp=OUT/f'{head}-{y}-{k}.joblib';joblib.dump(m,mp,compress=3)
                heads.append(dict(head=head,path=str(mp),sha256=sha256_file(mp),old_path=h['path'],old_sha256=h['sha256'],training_people=sub['player_id'].n_unique(),
                    training_rows=len(sub),max_target_year=int(sub['target_year'].max())))
            for arm in ['old_smooth','smooth_preseason']:
                p=q['preseason_raw_p'].to_numpy().copy();cond=q['preseason_raw_conditional_pa'].to_numpy().copy();p[mask]=raw[arm]['participation'];cond[mask]=raw[arm]['conditional_pa']
                q=q.with_columns(pl.Series(arm+'_raw_p',p),pl.Series(arm+'_raw_conditional_pa',cond))
                p[q['hard_unavailable'].to_numpy()|q['reported_retired'].to_numpy()]=0;cond=np.clip(cond,1,800)
                q=q.with_columns(pl.Series(arm+'_p',p),pl.Series(arm+'_conditional_pa',cond),pl.Series(arm+'_pa',p*cond),pl.col('baseline_rate').alias(arm+'_rate'))
                q=q.with_columns((pl.col(arm+'_pa')*(pl.col('baseline_rate')/600+pl.col('origin_replacement_rate'))).alias(arm+'_value'))
                for col in ['pa','value']:assert q.filter(pl.col('prior_debut')==1)[arm+'_'+col].equals(q.filter(pl.col('prior_debut')==1)['preseason_'+col])
            assert q.select(anchor.columns).equals(anchor.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id'))
            q.write_parquet(pp);n=dict(year=y,fold=k,information_date=c['information_date'],heads=heads,prediction_sha256=sha256_file(pp));write(f'fit-{y}-{k}.json',n);fits.append(n)
            print(f'Same smooth model, fresh rankings {y}/{k}: two heads saved.',flush=True)
    q=pl.concat([pl.read_parquet(OUT/f"forecast-{c['year']}-{c['fold']}.parquet") for c in pre['cells']]).sort('row_id')
    assert len(q)==30506 and q.select(anchor.columns).equals(anchor.sort('row_id'));q.write_parquet(OUT/'predictions.parquet');write('fits.json',fits)


def scoring():
    pre=read(OUT/'preflight.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    f=pl.read_parquet(OUT/'features.parquet');old=pl.read_parquet(smooth.OUT/'features.parquet');q=pl.read_parquet(OUT/'predictions.parquet').sort('row_id')
    anchor=pl.read_parquet(trees.OUT/'scored-predictions.parquet').sort('row_id');assert q.select(anchor.columns).equals(anchor);replayed=0
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            te=f.filter(pl.col('row_id').is_in(c['prospect_test_ids'])).sort('row_id');before=old.filter(pl.col('row_id').is_in(c['prospect_test_ids'])).sort('row_id')
            sub=q.filter(pl.col('row_id').is_in(c['prospect_test_ids'])).sort('row_id')
            for h in read(OUT/f"fit-{c['year']}-{c['fold']}.json")['heads']:
                for a,path,hsh,frame in [('smooth_preseason',h['path'],h['sha256'],te),('old_smooth',h['old_path'],h['old_sha256'],before)]:
                    assert sha256_file(Path(path))==hsh;m=joblib.load(path);x=frame.select(pre['features']).to_numpy()
                    pred=m.predict_proba(x)[:,1] if h['head']=='participation' else m.predict(x)
                    assert np.allclose(pred,sub[a+('_raw_p' if h['head']=='participation' else '_raw_conditional_pa')],atol=1e-10,rtol=0);replayed+=1
    for arm in ARMS[2:]:
        assert np.allclose(q[arm+'_pa'],q[arm+'_p']*q[arm+'_conditional_pa'],atol=1e-10,rtol=0)
        assert np.allclose(q[arm+'_value'],q[arm+'_pa']*(q['baseline_rate']/600+q['origin_replacement_rate']),atol=1e-10,rtol=0)
    tagged=trees.tagged(f);q=q.join(tagged.select('row_id','rank_band','new_draftee','thin_pro'),on='row_id',validate='1:1');never=q.filter(pl.col('prior_debut')==0)
    public=q.filter((pl.col('pa_0')>0)&pl.col('steamer_index').is_not_null()&pl.col('zips_index').is_not_null());assert len(public)==2627
    scopes=[('all',q),('never_debut',never),('upper_never_debut',never.filter(pl.col('stage')=='Upper minors')),('lower_never_debut',never.filter(pl.col('stage')=='Lower minors')),
        ('public_broad',public),('new_draftees',never.filter(pl.col('new_draftee'))),('thin_pro',never.filter(pl.col('thin_pro')))]
    scopes += [('never_origin_'+str(y),never.filter(pl.col('origin_year')==y)) for y in sorted(never['origin_year'].unique())]
    scopes += [('rank_band_'+str(k),never.filter(pl.col('rank_band')==k)) for k in [-1,0,1,2,3]]
    scores=[];intervals=[]
    for name,g in scopes:
        if not len(g):continue
        scores.append(dict(scope=name,rows=len(g),people=g['player_id'].n_unique(),actual_pa=int(g['next_pa'].sum()),actual_value=float(g['next_value'].sum()),
            scores={a:score(g,a) for a in ARMS+(['steamer'] if name=='public_broad' else [])},probability={a:probability_score(g,a) for a in ARMS}))
        if name in ['never_debut','upper_never_debut','lower_never_debut','new_draftees']:
            intervals.extend(dict(scope=name,**paired(g,'smooth_preseason',a,metric)) for a in ['preseason','old_smooth'] for metric in ['pa','value'])
    write('scores.json',scores);write('intervals.json',intervals);q.write_parquet(OUT/'scored-predictions.parquet');chosen={}
    def choose(g,why):
        assert len(g);chosen.setdefault(g['row_id'][0],[]).append(why)
    for pid,y in FIXED:choose(never.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y)),'fixed before fit')
    err=never.with_columns(((pl.col('preseason_value')-pl.col('next_value'))**2-(pl.col('smooth_preseason_value')-pl.col('next_value'))**2).alias('gain'),
        (pl.col('smooth_preseason_value')-pl.col('next_value')).alias('error'))
    for why,g in [('largest offense gain',err.sort('gain',descending=True)),('largest offense harm',err.sort('gain')),('false high',err.sort('error',descending=True)),
        ('false low',err.sort('error')),('ordinary active',err.filter(pl.col('next_pa').is_between(100,600)).sort(pl.col('error').abs()))]:choose(g,why)
    history=pl.read_parquet(ROOT/'reports/generated/practical-hitter-v31/counts.parquet');profiles=pl.read_parquet(OUT/'profile-support.parquet');cases=[]
    with threadpool_limits(limits=2):
        for rid,reasons in chosen.items():
            r=q.filter(pl.col('row_id')==rid).row(0,named=True);row=f.filter(pl.col('row_id')==rid);before=old.filter(pl.col('row_id')==rid)
            n=read(OUT/f"fit-{r['origin_year']}-{r['outer_fold']}.json");traces={};probes={}
            for h in n['heads']:
                traces[h['head']]={}
                for a,path,frame in [('smooth_preseason',h['path'],row),('old_smooth',h['old_path'],before)]:
                    traces[h['head']][a]=linear_trace(joblib.load(path),frame.select(pre['features']).to_numpy()[0],pre['features'],h['head']=='participation')
                m=joblib.load(h['path']);x=before.select(pre['features']).to_numpy();probes[h['head']]=float(m.predict_proba(x)[0,1] if h['head']=='participation' else m.predict(x)[0])
            peers=never.filter((pl.col('origin_year')==r['origin_year'])&(pl.col('stage')==r['stage'])&(pl.col('player_id')!=r['player_id'])).with_columns(
                (((pl.col('age')-r['age'])/3)**2+((pl.col('minor_pa_0')-r['minor_pa_0'])/250)**2+4*(pl.col('draft_rank')-r['draft_rank'])**2+
                 (pl.col('new_scout_rank_score_0')-r['new_scout_rank_score_0'])**2).alias('distance')).sort('distance','player_id').head(4)
            cases.append(dict(origin=r,selection=reasons,information_date=n['information_date'],actual_inputs={c:row[c][0] for c in pre['features']},
                old_scouting=before.select([c for c in pre['features'] if c.startswith('scout_')]).to_dicts()[0],
                new_scouting=row.select([c for c in pre['features'] if c.startswith('scout_')]).to_dicts()[0],saved_traces=traces,candidate_fit_with_old_rankings=probes,
                probe_interpretation='Same fitted candidate with old ranking inputs; mechanics only, not causality or a validated alternative.',
                source_history=history.filter((pl.col('player_id')==r['player_id'])&pl.col('season').is_between(r['origin_year']-2,r['origin_year'])).sort('season','bucket').to_dicts(),
                actual_history=history.filter((pl.col('player_id')==r['player_id'])&(pl.col('season')==r['target_year'])&(pl.col('bucket')=='MLB')).to_dicts(),
                training_profiles=profiles.filter(pl.col('row_id')==rid).to_dicts(),
                peers=peers.select('player_id','player_name','age','minor_pa_0','draft_rank',*[a+'_'+c for a in ARMS for c in ['pa','value']], 'next_pa','next_value').to_dicts()))
    write('cases.json',cases);write('verification.json',dict(replayed_heads=replayed,expected_heads=140,unchanged_hitting=True,unchanged_established_candidate=True,
        PA_product_verified=True,offense_verified=True,player_walkthrough_status='pending',cases=len(cases),protected_outcomes_used=False,frozen_forecast_changed=False,
        clips={a:int(never.filter((pl.col(a+'_raw_conditional_pa')<1)|(pl.col(a+'_raw_conditional_pa')>800)).height) for a in ARMS[2:]}))
    for s in scores[:7]:print(s['scope'],{a:(round(v['pa_rmse'],3),round(v['pa_mae'],3),round(v['value_rmse'],6),round(v['pa_total'])) for a,v in s['scores'].items()},flush=True)
    print('Scores provisional until actual player review.',flush=True)


if __name__=='__main__':{'prepare':prepare,'fit':fit,'score':scoring}[sys.argv[1]]()
