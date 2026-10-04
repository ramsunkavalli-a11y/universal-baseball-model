"""One matched employment-context opportunity test with fixed batting."""
from pathlib import Path
import sys
import joblib
import numpy as np
import polars as pl
from sklearn.ensemble import HistGradientBoostingClassifier,HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits
from universal_baseball.forecast_validation import preflight
from universal_baseball.hitter_employment_evidence import FEATURES,features
from universal_baseball.storage import sha256_file
from universal_baseball.practical_hitter_v30 import score
from universal_baseball.histogram_prediction_trace import trace
from fit_practical_hitter_v31 import weights
from score_practical_hitter_v31 import paired
from score_hitter_readiness_v49 import probability_score
from evaluate_hitter_readiness_v49 import logit_trace
import evaluate_hitter_preseason_readiness_v68 as prior
import audit_hitter_employment_v70b as source

ROOT=prior.ROOT;OUT=ROOT/'reports/generated/hitter-employment-v71';SOURCE=ROOT/'reports/generated/hitter-employment-v70b'
FIXED=[(664056,2023),(547180,2018),(446308,2016),(598265,2022),(474832,2022),(474832,2023),(694671,2023),(701762,2024)]
read=prior.read


def write(n,o):
    import json
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/n).write_text(json.dumps(o,indent=2,ensure_ascii=False,allow_nan=False,default=str)+'\n',encoding='utf8')


def profile(f):
    return prior.tagged(f).with_columns(pl.when(pl.col('pa_0')==0).then(0).when(pl.col('pa_0')<200).then(1).when(pl.col('pa_0')<400).then(2)
        .when(pl.col('pa_0')<600).then(3).otherwise(4).alias('work_band'),
        pl.when(pl.col('quality_present_0')==0).then(-1).when(pl.col('quality_0')<-.25).then(0).when(pl.col('quality_0')>.25).then(2).otherwise(1).alias('quality_band'))


def prepare():
    assert not (OUT/'preflight.json').exists(),'Preserve prior experiment'
    r=read(SOURCE/'report.json');assert r['player_walkthrough_status']=='complete'
    for k in ['source_hashes','output_hashes','review_hashes']:
        for p,h in r[k].items():assert sha256_file(Path(p))==h,p
    anchor=pl.read_parquet(prior.OUT/'features.parquet').sort('row_id');saved=pl.read_parquet(SOURCE/'features.parquet').sort('row_id')
    assert saved.select(anchor.columns).equals(anchor)
    lookup={}
    for year in range(2015,2025):
        folder='source-2015' if year==2015 else 'source';p=ROOT/f'reports/generated/hitter-injury-history-v2/{folder}/captures/transactions-{year}.json'
        for raw in read(p)['transactions']:
            if not raw.get('person',{}).get('id'):continue
            e=source.event(raw)
            if e:lookup.setdefault(e['player_id'],{})[e['transaction_id']]=e
    lookup={pid:list(rs.values()) for pid,rs in lookup.items()};rows=[];details=[]
    for a in saved.select('row_id','player_id','origin_year','on_40man','recorded_open_fa','fa_roster_conflict','employment_capture_scope').iter_rows(named=True):
        s=source.state(lookup.get(a['player_id'],[]),a['origin_year']) if a['origin_year']>=2015 else dict(recorded_open_fa=-1,latest_employment_date=None,latest_events=[])
        assert s['recorded_open_fa']==a['recorded_open_fa']
        x=features(a['origin_year'],s,a['fa_roster_conflict']==1);assert x['employment_capture_scope']==a['employment_capture_scope']
        rows.append(dict(row_id=a['row_id'],**x));details.append(dict(row_id=a['row_id'],player_id=a['player_id'],origin_year=a['origin_year'],
            latest_employment_date=s['latest_employment_date'],recorded_open_fa=s['recorded_open_fa'],fa_roster_conflict=a['fa_roster_conflict'],**x))
        if (a['player_id'],a['origin_year']) in FIXED:
            future=dict(transaction_id=-999,player_id=a['player_id'],available_date=f"{a['origin_year']+1}-01-01",status='attached')
            assert features(a['origin_year'],source.state(lookup.get(a['player_id'],[])+[future],a['origin_year']),a['fa_roster_conflict']==1)==x
    OUT.mkdir(parents=True,exist_ok=True);new=anchor.join(pl.DataFrame(rows),on='row_id',validate='1:1');assert new.select(anchor.columns).equals(anchor)
    new.write_parquet(OUT/'features.parquet');pl.DataFrame(details,infer_schema_length=None).write_parquet(OUT/'source-details.parquet')
    write('records.json',{str(pid):rs for pid,rs in lookup.items() if pid in set(anchor['player_id'])})
    pre=read(prior.OUT/'preflight.json');names=pre['pa_features']+FEATURES;assert len(names)==254
    supports=[];profiles=[];cells=[];exposed=[]
    for c in pre['cells']:
        checks={}
        for arm,f,cols in [('preseason',new,pre['pa_features']),('employment',new,names)]:
            tr=f.filter(pl.col('row_id').is_in(c['training_row_ids']));te=f.filter(pl.col('row_id').is_in(c['test_row_ids']))
            for head,sub in [('participation',tr),('conditional_pa',tr.filter(pl.col('next_pa')>0))]:
                sp,note=preflight(sub,te,cutoff=c['year'],fold=c['fold'],features=cols,expected_keys=te.select('row_id','horizon').iter_rows())
                checks[arm+'_'+head]=note;supports.append(sp.with_columns(pl.lit(arm).alias('arm'),pl.lit(head).alias('head')))
                a,b=profile(sub),profile(te)
                for kind,keys in [('broad',['stage','prior_debut','age_band','employment_year_known','employment_year_fa']),
                    ('refined',['stage','prior_debut','age_band','employment_year_known','employment_year_fa','on_40man','work_band','quality_band'])]:
                    counts=a.group_by(keys).agg(pl.col('player_id').n_unique().alias('profile_people'))
                    profiles.append(b.select('row_id',*keys).join(counts,on=keys,how='left',validate='m:1').with_columns(pl.col('profile_people').fill_null(0),
                        pl.lit(arm).alias('arm'),pl.lit(head).alias('head'),pl.lit(kind).alias('kind')))
                if arm=='employment':
                    g=sub.filter((pl.col('employment_year_fa')==1)&(pl.col('pa_0')>0))
                    exposed.append(dict(year=c['year'],fold=c['fold'],head=head,people=g['player_id'].n_unique(),origins=sorted(g['origin_year'].unique().to_list()),
                        zero_people=g.filter(pl.col('next_pa')==0)['player_id'].n_unique()))
        cells.append(dict(**{k:v for k,v in c.items() if k!='source_preflight'},source_preflight=checks))
    pl.concat(supports).write_parquet(OUT/'support.parquet');pl.concat(profiles,how='diagonal_relaxed').write_parquet(OUT/'profile-support.parquet');write('exposure-support.json',exposed)
    paths=[SOURCE/'report.json',SOURCE/'features.parquet',prior.OUT/'features.parquet',prior.OUT/'preflight.json',prior.OUT/'scored-predictions.parquet',OUT/'features.parquet',
        OUT/'source-details.parquet',OUT/'records.json',OUT/'support.parquet',OUT/'profile-support.parquet',OUT/'exposure-support.json',Path(__file__),
        ROOT/'docs/hitter-employment-v71-contract.md',ROOT/'src/universal_baseball/hitter_employment_evidence.py',ROOT/'scripts/fit_practical_hitter_v31.py',
        ROOT/'scripts/audit_hitter_employment_v70.py',ROOT/'scripts/audit_hitter_employment_v70b.py']
    write('preflight.json',dict(cells=cells,pa_features=names,prior_features=pre['pa_features'],settings=pre['settings'],checks_before_fits=140,
        input_hashes={str(p):sha256_file(p) for p in paths},source_hashes=r['source_hashes'],unchanged_hitting=True,protected_outcomes_used=False))
    print('All current evidence reconstructed; all original inputs exact; 140 checks saved before fits.',flush=True)


def fit():
    pre=read(OUT/'preflight.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    f=pl.read_parquet(OUT/'features.parquet');q=pl.read_parquet(prior.OUT/'scored-predictions.parquet');fits=[]
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y,k=c['year'],c['fold'];pp=OUT/f'forecast-{y}-{k}.parquet'
            if pp.exists():
                n=read(OUT/f'fit-{y}-{k}.json');assert sha256_file(pp)==n['prediction_sha256']
                for h in n['heads']:assert sha256_file(Path(h['path']))==h['sha256']
                fits.append(n);continue
            tr=f.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id');te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            result=q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id');assert result['row_id'].equals(te['row_id'])
            old=read(prior.OUT/f'fit-{y}-{k}.json');heads=[];raw={}
            for head,sub in [('participation',tr),('conditional_pa',tr.filter(pl.col('next_pa')>0))]:
                bh=next(h for h in old['heads'] if h['head']==head);assert sha256_file(Path(bh['path']))==bh['sha256']
                bm=joblib.load(bh['path']);bx=te.select(pre['prior_features']).to_numpy();pred=bm.predict_proba(bx)[:,1] if head=='participation' else bm.predict(bx)
                assert np.allclose(pred,result['preseason_raw_p' if head=='participation' else 'preseason_raw_conditional_pa'],atol=1e-10,rtol=0)
                m=(HistGradientBoostingClassifier if head=='participation' else HistGradientBoostingRegressor)(**pre['settings'])
                m.fit(sub.select(pre['pa_features']).to_numpy(),sub['next_active' if head=='participation' else 'next_pa'].to_numpy(),sample_weight=weights(sub))
                x=te.select(pre['pa_features']).to_numpy();raw[head]=m.predict_proba(x)[:,1] if head=='participation' else m.predict(x)
                assert np.isfinite(raw[head]).all();mp=OUT/f'{head}-{y}-{k}.joblib';joblib.dump(m,mp,compress=3)
                heads.append(dict(head=head,path=str(mp),sha256=sha256_file(mp),prior_path=bh['path'],prior_sha256=bh['sha256'],training_rows=len(sub),
                    training_people=sub['player_id'].n_unique(),max_target_year=int(sub['target_year'].max())))
            p=raw['participation'].copy();p[result['hard_unavailable'].to_numpy()|result['reported_retired'].to_numpy()]=0;cond=np.clip(raw['conditional_pa'],1,800)
            result=result.with_columns(pl.Series('employment_raw_p',raw['participation']),pl.Series('employment_p',p),pl.Series('employment_raw_conditional_pa',raw['conditional_pa']),
                pl.Series('employment_conditional_pa',cond),pl.Series('employment_pa',p*cond),pl.col('baseline_rate').alias('employment_rate'))
            result=result.with_columns((pl.col('employment_pa')*(pl.col('baseline_rate')/600+pl.col('origin_replacement_rate'))).alias('employment_value'))
            assert result.select(q.columns).equals(q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id'))
            result.write_parquet(pp);n=dict(year=y,fold=k,information_date=c['information_date'],heads=heads,prediction_sha256=sha256_file(pp));write(f'fit-{y}-{k}.json',n);fits.append(n)
            print(f'Employment {y}/{k}: both heads saved, V68 replayed.',flush=True)
    qnew=pl.concat([pl.read_parquet(OUT/f"forecast-{c['year']}-{c['fold']}.parquet") for c in pre['cells']]).sort('row_id')
    assert len(qnew)==30506 and qnew.select(q.columns).equals(q.sort('row_id'));qnew.write_parquet(OUT/'predictions.parquet');write('fits.json',fits)


def scoring():
    pre=read(OUT/'preflight.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    f=pl.read_parquet(OUT/'features.parquet');q=pl.read_parquet(OUT/'predictions.parquet').sort('row_id');old=pl.read_parquet(prior.OUT/'scored-predictions.parquet').sort('row_id')
    assert q.select(old.columns).equals(old) and q['employment_rate'].equals(q['baseline_rate']);replayed=0
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id');sub=q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            for h in read(OUT/f"fit-{c['year']}-{c['fold']}.json")['heads']:
                for a,path,hsh,cols in [('employment',h['path'],h['sha256'],pre['pa_features']),('preseason',h['prior_path'],h['prior_sha256'],pre['prior_features'])]:
                    assert sha256_file(Path(path))==hsh;m=joblib.load(path);x=te.select(cols).to_numpy();pred=m.predict_proba(x)[:,1] if h['head']=='participation' else m.predict(x)
                    assert np.allclose(pred,sub[a+('_raw_p' if h['head']=='participation' else '_raw_conditional_pa')],atol=1e-10,rtol=0);replayed+=1
    assert np.allclose(q['employment_pa'],q['employment_p']*q['employment_conditional_pa'],atol=1e-10)
    assert np.allclose(q['employment_value'],q['employment_pa']*(q['baseline_rate']/600+q['origin_replacement_rate']),atol=1e-10)
    q=q.join(f.select('row_id',*FEATURES),on='row_id',validate='1:1');current=q.filter(pl.col('pa_0')>0)
    public=current.filter(pl.col('steamer_index').is_not_null()&pl.col('zips_index').is_not_null());assert len(public)==2627
    scopes=[('all',q),('public_broad',public),('unsigned_current',current.filter((pl.col('employment_year_fa')==1)&(pl.col('on_40man')==0))),
        ('other_unlisted_current',current.filter((pl.col('on_40man')==0)&(pl.col('employment_year_fa')==0))),('listed_current',current.filter(pl.col('on_40man')==1)),
        ('upper_never_debut',q.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Upper minors'))),
        ('lower_never_debut',q.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Lower minors'))),('current_MLB',current)]
    scopes += [('origin_'+str(y),q.filter(pl.col('origin_year')==y)) for y in sorted(q['origin_year'].unique())]
    scopes += [('current_PA_'+str(k),current.filter(pl.col('work_band')==k)) for k in range(1,5)] if 'work_band' in q.columns else []
    # Diagnostic bands are recomputed from origin-known inputs, not future use.
    scopes += [('current_PA_'+str(k),profile(current).filter(pl.col('work_band')==k)) for k in range(1,5)]
    scopes += [('current_age_'+str(k),profile(current).filter(pl.col('age_band')==k)) for k in range(4)]
    scores=[];intervals=[]
    with threadpool_limits(limits=2):
        for name,g in scopes:
            if not len(g):continue
            scores.append(dict(scope=name,rows=len(g),people=g['player_id'].n_unique(),actual_pa=int(g['next_pa'].sum()),actual_value=float(g['next_value'].sum()),
                scores={a:score(g,a) for a in ['baseline','preseason','employment']+(['steamer'] if name=='public_broad' else [])},
                probability={a:probability_score(g,a) for a in ['baseline','preseason','employment']}))
            if name in ['all','public_broad','unsigned_current','listed_current','upper_never_debut']:
                intervals.extend(dict(scope=name,**paired(g,'employment',a,metric)) for a in ['baseline','preseason'] for metric in ['pa','value'])
    write('scores.json',scores);write('intervals.json',intervals);q.write_parquet(OUT/'scored-predictions.parquet');chosen={}
    def choose(g,why):
        assert len(g);chosen.setdefault(g['row_id'][0],[]).append(why)
    for pid,y in FIXED:choose(q.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y)),'fixed before fit')
    err=q.with_columns(((pl.col('preseason_value')-pl.col('next_value'))**2-(pl.col('employment_value')-pl.col('next_value'))**2).alias('gain'),
        (pl.col('employment_value')-pl.col('next_value')).alias('error'))
    for why,g in [('largest offense gain',err.sort('gain',descending=True)),('largest offense harm',err.sort('gain')),('major false high',err.sort('error',descending=True)),
        ('major false low',err.sort('error')),('ordinary active',err.filter(pl.col('next_pa').is_between(200,600)).sort(pl.col('error').abs()))]:choose(g,why)
    counts=pl.read_parquet(ROOT/'reports/generated/practical-hitter-v31/counts.parquet');profiles=pl.read_parquet(OUT/'profile-support.parquet')
    details=pl.read_parquet(OUT/'source-details.parquet');records=read(OUT/'records.json');cases=[]
    with threadpool_limits(limits=2):
        for rid,reasons in chosen.items():
            r=q.filter(pl.col('row_id')==rid).row(0,named=True);row=f.filter(pl.col('row_id')==rid);n=read(OUT/f"fit-{r['origin_year']}-{r['outer_fold']}.json");traces={};probes={}
            for h in n['heads']:
                traces[h['head']]={}
                for a,path,cols in [('preseason',h['prior_path'],pre['prior_features']),('employment',h['path'],pre['pa_features'])]:
                    m=joblib.load(path);x=row.select(cols).to_numpy()[0];traces[h['head']][a]=logit_trace(m,x,cols) if h['head']=='participation' else trace(m,x,cols)
                m=joblib.load(h['path']);x=row.select(pre['pa_features']).to_numpy();x[0,-3:]=0
                probes[h['head']]=float(m.predict_proba(x)[0,1] if h['head']=='participation' else m.predict(x)[0])
            peers=q.filter((pl.col('origin_year')==r['origin_year'])&(pl.col('stage')==r['stage'])&(pl.col('on_40man')==r['on_40man'])&(pl.col('player_id')!=r['player_id'])).with_columns(
                (((pl.col('age')-r['age'])/3)**2+((pl.col('pa_0')-r['pa_0'])/250)**2+((pl.col('minor_pa_0')-r['minor_pa_0'])/250)**2+4*(pl.col('draft_rank')-r['draft_rank'])**2).alias('distance')).sort('distance','player_id').head(4)
            cases.append(dict(origin=r,selection=reasons,information_date=n['information_date'],actual_inputs={col:row[col][0] for col in pre['pa_features']},
                employment_source=details.filter(pl.col('row_id')==rid).to_dicts()[0],
                dated_records=[e for e in records.get(str(r['player_id']),[]) if e['available_date']<=f"{r['origin_year']}-12-31"],
                source_history=counts.filter((pl.col('player_id')==r['player_id'])&pl.col('season').is_between(r['origin_year']-2,r['origin_year'])).sort('season','bucket').to_dicts(),
                actual_history=counts.filter((pl.col('player_id')==r['player_id'])&(pl.col('season')==r['target_year'])&(pl.col('bucket')=='MLB')).to_dicts(),
                saved_traces=traces,candidate_fit_with_new_inputs_zero=probes,probe_interpretation='Artificial no-observed-employment fixed-fit probe; roster/performance remain. Not causality or a validated forecast.',
                training_profiles=profiles.filter(pl.col('row_id')==rid).to_dicts(),
                peers=peers.select('player_id','player_name','age','pa_0','minor_pa_0',*FEATURES,'baseline_pa','preseason_pa','employment_pa','preseason_value','employment_value','next_pa','next_value').to_dicts()))
    write('cases.json',cases);write('verification.json',dict(replayed_heads=replayed,expected_heads=140,unchanged_hitting=True,unchanged_anchor_forecasts=True,
        PA_product_verified=True,corrected_value_verified=True,player_walkthrough_status='pending',cases=len(cases),protected_outcomes_used=False,
        frozen_forecast_changed=False,conditional_clips=int(((q['employment_raw_conditional_pa']<1)|(q['employment_raw_conditional_pa']>800)).sum())))
    for s in scores[:8]:print(s['scope'],{a:(round(v['pa_rmse'],3),round(v['pa_mae'],3),round(v['value_rmse'],6),round(v['pa_total'])) for a,v in s['scores'].items()},flush=True)
    print('Scores provisional until actual player review.',flush=True)


if __name__=='__main__':{'prepare':prepare,'fit':fit,'score':scoring}[sys.argv[1]]()
