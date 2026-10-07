"""Protected-baseline future-MLB-range test, with source and quality preflights."""
from collections import Counter,defaultdict
from pathlib import Path
import argparse
import gzip
import json
from zipfile import ZipFile

import numpy as np
import polars as pl

from run_hitter_finite_return_baseline import protections
from run_minor_count_reliability_v20 import choices,measurements,group_statistics
from universal_baseball.storage import sha256_file
from universal_baseball.minor_count_reliability import fit_prior,posterior
from universal_baseball.minor_range_talent import design,ridge_fit,ridge_predict,person_weights,BASE_NAMES
from universal_baseball.minor_range_correction import audit,fit as correction_fit,profile_table,predict as correction_predict

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'reports/generated/defense-minor-counts-v18'
V20=ROOT/'reports/model-evidence/defense-count-reliability-v20'
V19=ROOT/'reports/model-evidence/defense-minor-range-v19'
OUT=ROOT/'reports/generated/defense-minor-correction-v21'
PUBLIC=ROOT/'reports/model-evidence/defense-minor-correction-v21'


def read(p):
    with gzip.open(p,'rt',encoding='utf8') as f:return json.load(f)


def write(p,v):
    assert not p.exists(),f'Preserve existing evidence: {p}'
    p.parent.mkdir(parents=True,exist_ok=True)
    with gzip.open(p,'wt',encoding='utf8',compresslevel=6) as f:json.dump(v,f,allow_nan=False,separators=(',',':'))


def key(r):return (r['origin_year'],r['player_id'],r['position'])


def population():
    return pl.read_parquet(SOURCE/'labels.parquet').filter((pl.col('component')=='range')&(pl.col('window')==3)&
        (~pl.col('prior_current_MLB_fielding'))).sort(['origin_year','player_id','position']).to_dicts()


def preparation():
    protections();assert not (PUBLIC/'preflight.json.gz').exists()
    for folder in (V19,V20):
        reviewed=read(folder/'final-review.json.gz');assert reviewed['player_walkthrough_status']=='complete'
    levels=read(V20/'source-levels.json.gz');pool=population();rowsby={key(r):r for r in pool}
    by=defaultdict(list)
    for i,r in enumerate(levels):by[key(r)].append(i)
    old=read(V19/'fit-report.json.gz');tuning={(r['origin'],r['outer_fold'],r['arm']):r['selected_alpha'] for r in old['tuning']}
    oldprior=read(V20/'reference-groups.json.gz')
    priorby={(g['origin_year'],(g['fold'],),tuple(g['scope']),g['channel']):g for g in oldprior}
    scope_tables={};groups={};requests={};cells=[]
    def request(r,excluded):
        requestkey=key(r)+(tuple(excluded),)
        if requestkey in requests:return requests[requestkey]['request_id']
        year=r['origin_year'];assert key(r) in by
        if year not in scope_tables:
            tables=defaultdict(list)
            for j,source in enumerate(levels):
                if not year-2<=source['origin_year']<=year:continue
                for c,x,n in measurements(source):
                    if n<=0:continue
                    for scope in choices(source):tables[tuple(scope)+(c,)].append(j)
            scope_tables[year]=tables
        parts=[]
        for j in by[key(r)]:
            source=levels[j]
            for c,x,n in measurements(source):
                for scope in choices(source):
                    gkey=(year,tuple(excluded),tuple(scope),c)
                    if gkey not in groups:
                        ids=[i for i in scope_tables[year].get(tuple(scope)+(c,),[]) if levels[i]['player_id']%5 not in excluded]
                        people=sorted({levels[i]['player_id'] for i in ids})
                        if len(people)<30 and scope[0]!='position':continue
                        assert ids and all(levels[i]['origin_year']<=year for i in ids)
                        gid='g'+str(len(groups)).zfill(5);reuse=priorby.get(gkey)
                        if reuse is not None:assert ids==reuse['source_row_indices'] and people==reuse['people']
                        groups[gkey]=dict(group_id=gid,origin_year=year,excluded_folds=list(excluded),scope=list(scope),channel=c,
                            source_row_indices=ids,people=people,reused_v20_group=None if reuse is None else reuse['group_id'])
                    group=groups[gkey]
                    if len(group['people'])>=30 or scope[0]=='position':break
                assert r['player_id'] not in group['people']
                parts.append(dict(source_row_index=j,channel=c,count=x,exposure=n,group_id=group['group_id']))
        rid='r'+str(len(requests)).zfill(5)
        requests[requestkey]=dict(request_id=rid,identity=list(key(r)),excluded_folds=list(excluded),parts=parts)
        return rid
    for year in (2021,2022):
        for fold in range(5):
            train=[r for r in pool if r['window_end']<=year and r['quality_rate'] is not None and r['player_id']%5!=fold]
            test=[r for r in pool if r['origin_year']==year and r['player_id']%5==fold]
            basepath=V19/'cells'/f'outer-{year}-{fold}-{fold}-fit.json.gz';saved=read(basepath)
            alpha=tuning[year,fold,'baseline'];baseline=saved['fits'][f'baseline-{alpha}'];assert baseline is not None
            # The saved comparison is the immutable benchmark, not a new penalty choice.
            savedkeys={tuple(k) for k in read(V19/'cells'/f'outer-{year}-{fold}-{fold}-preflight.json.gz')['train_keys']}
            assert {key(r) for r in train}==savedkeys
            outer=audit(train,test,year,[fold],min_people=50)
            nuisance=[];available=[]
            for held in range(5):
                if held==fold:continue
                innertrain=[r for r in train if r['player_id']%5!=held];innertest=[r for r in train if r['player_id']%5==held]
                check=audit(innertrain,innertest,year,sorted((fold,held)))
                nuisance.append(dict(held=held,audit=check))
                if check['fit_supported']:available.extend(key(r) for r in innertest)
            residualrows=[rowsby[k] for k in available]
            stage=defaultdict(set);joint=defaultdict(set)
            for r in residualrows:
                stage[r['position'],r['level']].add(r['player_id'])
                joint[r['position'],r['level'],r['age_band'],r['sample_band']].add(r['player_id'])
            testprofiles=[dict(identity=list(key(r)),stage_people=len(stage[r['position'],r['level']]),
                joint_people=len(joint[r['position'],r['level'],r['age_band'],r['sample_band']])) for r in test]
            reqtrain={str(key(r)):request(r,tuple(sorted({fold,r['player_id']%5}))) for r in train}
            reqtest={str(key(r)):request(r,(fold,)) for r in test}
            cells.append(dict(origin=year,fold=fold,outer_audit=outer,nuisance=nuisance,available_residual_keys=[list(k) for k in available],
                baseline_path=str(basepath),baseline_hash=sha256_file(basepath),baseline_alpha=alpha,baseline_fit=baseline,
                age_median=saved['age_median'],train_requests=reqtrain,test_requests=reqtest,test_profile_counts=testprofiles))
            print(dict(prepared_cell=[year,fold],training_people=outer['people'],test_people=len({r['player_id'] for r in test}),
                initially_supported_profiles=sum(r['stage_people']>=10 and r['joint_people']>=5 for r in testprofiles)),flush=True)
    assert len(cells)==10
    write(OUT/'requests.json.gz',list(requests.values()));write(OUT/'source-groups.json.gz',list(groups.values()));write(PUBLIC/'cells-preflight.json.gz',cells)
    paths=[Path(__file__),SOURCE/'labels.parquet',V20/'source-levels.json.gz',V20/'final-review.json.gz',V20/'reference-fits.zip',
        V20/'reference-groups.json.gz',V19/'fit-report.json.gz',V19/'final-review.json.gz',OUT/'requests.json.gz',OUT/'source-groups.json.gz',
        PUBLIC/'cells-preflight.json.gz',ROOT/'docs/defense-minor-correction-v21-contract.md',ROOT/'src/universal_baseball/minor_range_correction.py',
        ROOT/'src/universal_baseball/minor_count_reliability.py',ROOT/'src/universal_baseball/minor_range_talent.py',
        ROOT/'scripts/run_minor_count_reliability_v20.py',ROOT/'tests/test_minor_range_correction.py']
    paths.extend(Path(c['baseline_path']) for c in cells)
    write(PUBLIC/'preflight.json.gz',dict(before_any_new_estimation=True,previous_goal_turn='Progress: source reliability reviewed and pushed in 473e7a13.',
        source_groups=len(groups),source_requests=len(requests),cells=10,evaluation_rows=sum(len(c['outer_audit']['test_keys']) for c in cells),
        baseline_unchanged=True,count_penalty_fixed=100,no_count_tuning=True,no_2026_outcomes=True,player_walkthrough_status='pending',
        hashes={str(p):sha256_file(p) for p in paths}))
    print(dict(preparation_complete=True,groups=len(groups),reused=sum(g['reused_v20_group'] is not None for g in groups.values())),flush=True)


def check_preflight():
    pre=read(PUBLIC/'preflight.json.gz')
    for p,h in pre['hashes'].items():assert sha256_file(Path(p))==h,p
    return pre


def sources():
    protections();pre=check_preflight();assert not (PUBLIC/'sources-complete.json.gz').exists()
    levels=read(V20/'source-levels.json.gz');groups=read(OUT/'source-groups.json.gz');hashes={}
    with ZipFile(V20/'reference-fits.zip') as archive:
        for i,g in enumerate(groups):
            path=OUT/'priors'/f"{g['group_id']}.json.gz"
            if path.exists():note=read(path);assert note['preflight_hash']==sha256_file(PUBLIC/'preflight.json.gz')
            else:
                if g['reused_v20_group'] is not None:
                    old=json.loads(gzip.decompress(archive.read(g['reused_v20_group']+'.json.gz')).decode('utf8'))
                    prior=old['candidate'];baseline=old['baseline']
                else:
                    baseline,x,n=group_statistics(g,levels);prior=fit_prior(x,n,g['channel']<2,baseline)
                note=dict(group_id=g['group_id'],preflight_hash=sha256_file(PUBLIC/'preflight.json.gz'),
                    baseline=baseline,prior=prior,reused_v20_group=g['reused_v20_group'])
                write(path,note)
            hashes[str(path)]=sha256_file(path)
            if i%100==0:print(f'Count references ready: {i+1}/{len(groups)}',flush=True)
    write(PUBLIC/'sources-complete.json.gz',dict(groups=len(groups),new_prior_estimates=sum(g['reused_v20_group'] is None for g in groups),
        quality_fits=0,hashes=hashes,preflight_hash=sha256_file(PUBLIC/'preflight.json.gz')))


def signals(request,priors,levels):
    numerator=np.zeros(4);denominator=np.zeros(4);traces=[]
    for part in request['parts']:
        c=part['channel'];prior=priors[part['group_id']]['prior'];post=posterior(part['count'],part['exposure'],prior,c<2)
        delta=(post['mean']-prior['mean'])*(-1 if c<2 else 1)
        numerator[c]+=part['exposure']*delta;denominator[c]+=part['exposure']
        traces.append(dict(**part,level=levels[part['source_row_index']]['level'],prior=prior,posterior=post,deviation=delta))
    return np.divide(numerator,denominator,out=np.zeros(4),where=denominator>0),traces


def metric(rows,column):
    q=[r for r in rows if r['quality_rate'] is not None]
    if not q:return None
    w=person_weights(q);error=np.array([r[column]-r['quality_rate'] for r in q])
    return dict(rows=len(q),people=len({r['player_id'] for r in q}),rmse=float(np.sqrt(np.average(error**2,weights=w))),
                mae=float(np.average(abs(error),weights=w)),bias=float(np.average(error,weights=w)))


def paired(rows):
    by=defaultdict(list)
    for r in rows:
        if r['quality_rate'] is not None:by[r['player_id']].append(r)
    be=[];ce=[];bm=[];cm=[]
    for pid,rs in sorted(by.items()):
        b=np.array([r['baseline']-r['quality_rate'] for r in rs]);c=np.array([r['candidate']-r['quality_rate'] for r in rs])
        be.append(np.mean(b*b));ce.append(np.mean(c*c));bm.append(np.mean(abs(b)));cm.append(np.mean(abs(c)))
    if not be:return None
    rng=np.random.default_rng(21021);ix=rng.integers(0,len(be),size=(2000,len(be)))
    rd=np.sqrt(np.array(ce)[ix].mean(axis=1))-np.sqrt(np.array(be)[ix].mean(axis=1))
    md=np.array(cm)[ix].mean(axis=1)-np.array(bm)[ix].mean(axis=1)
    return dict(people=len(be),seed=21021,replicates=2000,rmse_delta_interval=np.quantile(rd,[.025,.975]).tolist(),
                mae_delta_interval=np.quantile(md,[.025,.975]).tolist())


def quality():
    protections();check_preflight();source=read(PUBLIC/'sources-complete.json.gz')
    for p,h in source['hashes'].items():assert sha256_file(Path(p))==h,p
    assert not (PUBLIC/'fit-report.json.gz').exists() and not (OUT/'nuisance-fits.json.gz').exists()
    cells=read(PUBLIC/'cells-preflight.json.gz');pool=population();rowsby={key(r):r for r in pool};levels=read(V20/'source-levels.json.gz')
    priors={p.stem.split('.')[0]:read(p) for p in (OUT/'priors').glob('*.json.gz')}
    requests={r['request_id']:r for r in read(OUT/'requests.json.gz')};feature_cache={};nuisance_fits=[];prepared=[];feature_records=[]
    old={key(r):r for r in pl.read_parquet(ROOT/'reports/generated/defense-minor-range-v19/predictions.parquet').to_dicts()}
    def feature(rid):
        if rid not in feature_cache:feature_cache[rid]=signals(requests[rid],priors,levels)
        return feature_cache[rid]
    for cell in cells:
        year,fold=cell['origin'],cell['fold'];residuals={}
        for nuisance in cell['nuisance']:
            checked=nuisance['audit'];tr=[rowsby[tuple(k)] for k in checked['training_keys']];te=[rowsby[tuple(k)] for k in checked['test_keys']]
            assert audit(tr,te,year,checked['excluded_folds'])==checked
            note=dict(origin=year,fold=fold,held=nuisance['held'],audit=checked,fit=None,held_predictions=[])
            if checked['fit_supported']:
                ages=[r['age'] for r in tr if r['age'] is not None];median=float(np.median(ages)) if ages else 23.
                xt=design(tr,np.zeros((len(tr),4)),median,False);xe=design(te,np.zeros((len(te),4)),median,False)
                model=ridge_fit(xt,np.array([r['quality_rate'] for r in tr]),person_weights(tr),cell['baseline_alpha'],BASE_NAMES)
                pred=ridge_predict(model,xe);note.update(fit=model,age_median=median)
                for r,p in zip(te,pred,strict=True):
                    residuals[key(r)]=r['quality_rate']-float(p)
                    note['held_predictions'].append(dict(identity=list(key(r)),baseline=float(p),quality=r['quality_rate'],residual=residuals[key(r)]))
            nuisance_fits.append(note)
        train=[rowsby[tuple(k)] for k in cell['available_residual_keys']];test=[rowsby[tuple(k)] for k in cell['outer_audit']['test_keys']]
        assert set(residuals)=={key(r) for r in train}
        st=np.array([feature(cell['train_requests'][str(key(r))])[0] for r in train]);se=np.array([feature(cell['test_requests'][str(key(r))])[0] for r in test])
        baseline=ridge_predict(cell['baseline_fit'],design(test,np.zeros((len(test),4)),cell['age_median'],False))
        assert np.allclose(baseline,[old[key(r)]['baseline'] for r in test],atol=1e-12,rtol=0)
        check=audit(train,test,year,[fold],min_people=50);assert np.isfinite(st).all() and np.isfinite(se).all()
        profiles=profile_table(train,st);profile_rows=[]
        for r,s in zip(test,se,strict=True):
            # Only count transport, not future outcomes, determines this gate.
            dummy=dict(scale=[1.]*4,coefficients=[0.]*4) if check['fit_supported'] else None
            gate=correction_predict(dummy,0.,r,s,profiles);profile_rows.append(dict(identity=list(key(r)),**gate))
        check.update(before_correction_fit=True,feature_names=['glove_avoidance','throw_avoidance','infield_plays','outfield_plays'],
            training_signals=st.tolist(),test_signals=se.tolist(),profile_rows=profile_rows,
            stage_bounds=[dict(position=k[0],level=k[1],lower=v[0].tolist(),upper=v[1].tolist()) for k,v in profiles['bounds'].items()])
        prepared.append((cell,train,test,st,se,baseline,profiles,residuals,check))
        for scope,rs,ss in [('train',train,st),('test',test,se)]:
            for r,s in zip(rs,ss,strict=True):
                rid=cell['train_requests' if scope=='train' else 'test_requests'][str(key(r))]
                feature_records.append(dict(origin=year,fold=fold,scope=scope,identity=list(key(r)),request_id=rid,signals=s.tolist(),
                    count_trace=feature(rid)[1],residual=residuals.get(key(r)) if scope=='train' else None))
    # ALL nuisance and correction preflights exist before ANY second-stage fit.
    write(OUT/'nuisance-fits.json.gz',nuisance_fits);write(OUT/'features.json.gz',feature_records)
    write(PUBLIC/'correction-preflights.json.gz',[v[-1] for v in prepared])
    outputs=[];fits=[]
    for cell,tr,te,st,se,base,profiles,residuals,check in prepared:
        model=correction_fit(st,[residuals[key(r)] for r in tr],tr) if check['fit_supported'] else None
        fits.append(dict(origin=cell['origin'],fold=cell['fold'],fit=model,training_keys=[list(key(r)) for r in tr]))
        for r,s,b in zip(te,se,base,strict=True):
            pred=correction_predict(model,float(b),r,s,profiles)
            outputs.append(dict(origin_year=r['origin_year'],player_id=r['player_id'],player_name=r['player_name'],position=r['position'],level=r['level'],
                age=r['age'],age_band=r['age_band'],sample_band=r['sample_band'],minor_outs=r['minor_outs'],quality_rate=r['quality_rate'],
                quality_status=r['quality_status'],future_opportunities=r['future_opportunities'],future_runs=r['future_runs'],fold=cell['fold'],
                old_selected=old[key(r)]['candidate'],signals=s.tolist(),**pred))
        print(dict(quality_cell=[cell['origin'],cell['fold']],correction_fit=model is not None,applied=sum(r['applied'] for r in outputs if r['origin_year']==cell['origin'] and r['fold']==cell['fold'])),flush=True)
    assert len(outputs)==13133 and len({key(r) for r in outputs})==len(outputs)
    write(OUT/'correction-fits.json.gz',fits);path=OUT/'predictions.parquet';assert not path.exists()
    pl.DataFrame(outputs,infer_schema_length=None).write_parquet(path)
    headline={};groups=[]
    for year in (2021,2022):
        rs=[r for r in outputs if r['origin_year']==year]
        headline[str(year)]=dict(scores={arm:metric(rs,arm) for arm in ('baseline','old_selected','candidate')},paired=paired(rs),
            population=len(rs),measured=sum(r['quality_rate'] is not None for r in rs),applied=sum(r['applied'] for r in rs),
            applied_measured=sum(r['applied'] and r['quality_rate'] is not None for r in rs),
            fallback_reasons=dict(Counter(reason for r in rs for reason in r['reasons'])))
        for column in ('position','level','age_band','sample_band','applied'):
            for value in sorted({r[column] for r in rs},key=str):
                q=[r for r in rs if r[column]==value]
                groups.append(dict(origin_year=year,column=column,value=value,population=len(q),
                    scores={arm:metric(q,arm) for arm in ('baseline','old_selected','candidate')},paired=paired(q)))
    failed=[];p=headline['2022'];stress=headline['2021']
    if p['scores']['candidate']['rmse']>=p['scores']['baseline']['rmse'] or p['paired']['rmse_delta_interval'][1]>=0:failed.append('no_supported_primary_RMSE_gain')
    if p['scores']['candidate']['mae']>p['scores']['baseline']['mae']*1.01:failed.append('primary_MAE_harm')
    if stress['scores']['candidate']['rmse']>stress['scores']['baseline']['rmse']*1.05:failed.append('stress_RMSE_harm')
    for g in groups:
        scores=g['scores']
        if g['origin_year']==2022 and g['column'] in ('position','level') and scores['baseline'] and scores['baseline']['people']>=20:
            if scores['candidate']['rmse']>scores['baseline']['rmse']*1.05:failed.append(f"group_RMSE_harm_{g['column']}_{g['value']}")
    paths=[path,OUT/'nuisance-fits.json.gz',OUT/'features.json.gz',OUT/'correction-fits.json.gz',PUBLIC/'correction-preflights.json.gz',
           PUBLIC/'preflight.json.gz',PUBLIC/'sources-complete.json.gz']
    write(PUBLIC/'fit-report.json.gz',dict(headline=headline,groups=groups,screen_failed_checks=failed,statistical_screen_pass=not failed,
        baseline_exact_replay=True,no_2026_outcomes=True,forecast_unchanged=True,independent_review_pending=True,player_walkthrough_status='pending',
        deployment_approved=False,hashes={str(p):sha256_file(p) for p in paths}))
    print(json.dumps(dict(headline=headline,screen_failed_checks=failed),indent=2),flush=True);protections()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['prepare','sources','quality']);args=parser.parse_args()
    {'prepare':preparation,'sources':sources,'quality':quality}[args.phase]()
