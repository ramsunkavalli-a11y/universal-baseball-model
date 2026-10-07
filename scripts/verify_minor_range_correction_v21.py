"""Independent source, residual, regression, fallback and score replay."""
from collections import Counter,defaultdict
from pathlib import Path
import gzip
import json
import math

import numpy as np
import polars as pl
from scipy.stats import betabinom,binom,nbinom,poisson

from universal_baseball.storage import sha256_file

ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/'reports/model-evidence/defense-minor-correction-v21'
OUT=ROOT/'reports/generated/defense-minor-correction-v21'
V20=ROOT/'reports/model-evidence/defense-count-reliability-v20'


def read(p):
    with gzip.open(p,'rt',encoding='utf8') as f:return json.load(f)


def write(p,v):
    assert not p.exists()
    with gzip.open(p,'wt',encoding='utf8') as f:json.dump(v,f,allow_nan=False,separators=(',',':'))


def close(a,b):
    np.testing.assert_allclose(a,b,atol=1e-9,rtol=1e-8)


def measurement(r,c):
    return (r['errors']-r['throwingErrors'],r['chances']) if c==0 else (r['throwingErrors'],r['chances']) if c==1 else (r['assists'],r['outs']) if c==2 else (r['putOuts'],r['outs'])


def scopekeys(r):
    a=r['age'];b='unknown' if a is None else '<=19' if a<=19 else '20-22' if a<=22 else '23-25' if a<=25 else '26+'
    return [('position_level_age',r['position'],r['level'],b),('position_level',r['position'],r['level']),('position_age',r['position'],b),('position',r['position'])]


def key(r):return r['origin_year'],r['player_id'],r['position']


def weights(rows):
    n=Counter(r['player_id'] for r in rows);return np.array([1/n[r['player_id']] for r in rows])


def design(rows,median,names):
    result=[]
    for r in rows:
        d=dict(age=((r['age'] if r['age'] is not None else median)-23)/5,age_unknown=int(r['age'] is None),
               log_outs=math.log1p(r['minor_outs'])-math.log(1501))
        d.update({f'position_{p}':int(r['position']==p) for p in range(3,10)})
        d.update({n:int(r['level']==n.removeprefix('level_')) for n in names if n.startswith('level_')})
        result.append([d[n] for n in names])
    return np.array(result)


def independent_baseline_fit(rows,median,model):
    x=design(rows,median,model['names']);w=weights(rows);y=np.array([r['quality_rate'] for r in rows])
    mu=np.average(x,axis=0,weights=w);ym=np.average(y,weights=w);scale=np.ones(x.shape[1])
    for j in (0,2):
        v=np.average((x[:,j]-mu[j])**2,weights=w);scale[j]=math.sqrt(v) if v>1e-20 else 1.
    z=(x-mu)/scale
    lhs=np.vstack((np.sqrt(w)[:,None]*z,math.sqrt(model['alpha'])*np.eye(x.shape[1])))
    rhs=np.concatenate((np.sqrt(w)*(y-ym),np.zeros(x.shape[1])))
    coef=np.linalg.lstsq(lhs,rhs,rcond=None)[0]
    close(mu,model['mean']);close(scale,model['scale']);close(ym,model['target_mean']);close(coef,model['coefficients'])
    return mu,scale,ym,coef


def independent_score(rows,arm):
    q=[r for r in rows if r['quality_rate'] is not None]
    if not q:return None
    w=weights(q);e=np.array([r[arm]-r['quality_rate'] for r in q])
    return dict(rows=len(q),people=len({r['player_id'] for r in q}),rmse=math.sqrt(np.average(e*e,weights=w)),
                mae=np.average(abs(e),weights=w),bias=np.average(e,weights=w))


def independent_interval(rows):
    by=defaultdict(list)
    for r in rows:
        if r['quality_rate'] is not None:by[r['player_id']].append(r)
    if not by:return None
    b=[];c=[];bm=[];cm=[]
    for pid,rs in sorted(by.items()):
        be=np.array([r['baseline']-r['quality_rate'] for r in rs]);ce=np.array([r['candidate']-r['quality_rate'] for r in rs])
        b.append(np.mean(be*be));c.append(np.mean(ce*ce));bm.append(np.mean(abs(be)));cm.append(np.mean(abs(ce)))
    rng=np.random.default_rng(21021);ix=rng.integers(0,len(b),size=(2000,len(b)))
    return dict(rmse_delta_interval=np.quantile(np.sqrt(np.array(c)[ix].mean(axis=1))-np.sqrt(np.array(b)[ix].mean(axis=1)),[.025,.975]),
                mae_delta_interval=np.quantile(np.array(cm)[ix].mean(axis=1)-np.array(bm)[ix].mean(axis=1),[.025,.975]))


def main():
    pre=read(PUBLIC/'preflight.json.gz');source=read(PUBLIC/'sources-complete.json.gz');report=read(PUBLIC/'fit-report.json.gz')
    resume=read(PUBLIC/'resume-preflight.json.gz')
    for record in (pre,source,report,resume):
        for p,h in record['hashes'].items():assert sha256_file(Path(p))==h,p
    assert source['preflight_hash']==sha256_file(PUBLIC/'preflight.json.gz')
    levels=read(V20/'source-levels.json.gz');groups=read(OUT/'source-groups.json.gz');requests=read(OUT/'requests.json.gz')
    all_labels=pl.read_parquet(ROOT/'reports/generated/defense-minor-counts-v18/labels.parquet').to_dicts()
    labels={key(r):r for r in all_labels if r['component']=='range' and r['window']==3 and not r['prior_current_MLB_fielding']}
    tables=defaultdict(list)
    for year in {g['origin_year'] for g in groups}:
        for i,r in enumerate(levels):
            if not year-2<=r['origin_year']<=year:continue
            for c in [0,1]+([2] if r['position'] in (4,5,6) else [3] if r['position'] in (7,8,9) else []):
                if measurement(r,c)[1]<=0:continue
                for scope in scopekeys(r):tables[year,scope,c].append(i)
    groupby={g['group_id']:g for g in groups};priors={}
    for i,g in enumerate(groups):
        ids=[j for j in tables[g['origin_year'],tuple(g['scope']),g['channel']] if levels[j]['player_id']%5 not in g['excluded_folds']]
        assert ids==g['source_row_indices'] and sorted({levels[j]['player_id'] for j in ids})==g['people']
        note=read(OUT/'priors'/f"{g['group_id']}.json.gz");assert note['preflight_hash']==sha256_file(PUBLIC/'preflight.json.gz')
        by=defaultdict(list)
        for j in ids:by[levels[j]['player_id']].append(measurement(levels[j],g['channel']))
        c=g['channel'];people=len(by)
        mean=float(np.mean([np.mean([x/n for x,n in rs]) for rs in by.values()]))
        second=float(np.mean([np.mean([(x/n)**2 for x,n in rs]) for rs in by.values()]))
        inverse=float(np.mean([np.mean([1/n for x,n in rs]) for rs in by.values()]))
        variance=max(0.,second-mean*mean)*people/(people-1) if people>1 else 0.
        between=max(0.,(variance-mean*(1-mean)*inverse)/(1-inverse)) if c<2 and inverse<1 else max(0.,variance-mean*inverse) if c>=2 else 0.
        if c<2:between=min(between,mean*(1-mean)*(1-1e-9))
        strength=mean*(1-mean)/between-1 if c<2 and between>0 else mean/between if c>=2 and between>0 else None
        if people<30 or mean<=0 or (c<2 and mean>=1):strength=None;between=0.
        close(mean,note['baseline']['mean']);close(between,note['baseline']['between_variance'])
        assert (strength is None)==(note['baseline']['strength'] is None)
        if strength is not None:close(strength,note['baseline']['strength'])
        x=np.array([sum(v[0] for v in rs) for pid,rs in sorted(by.items())]);n=np.array([sum(v[1] for v in rs) for pid,rs in sorted(by.items())])
        c=g['channel'];prior=note['prior'];mu,k=prior['mean'],prior['strength']
        if prior['status']=='optimization_failure_moment_fallback':
            close(mu,mean);assert (k is None)==(strength is None)
            if k is not None:close(k,strength)
        if g['reused_v20_group'] is not None:
            old=read(V20/'fits'/f"{g['reused_v20_group']}.json.gz");assert prior==old['candidate'] and note['baseline']==old['baseline']
        else:
            def dist(m,s):
                if s is None or m==0 or (c<2 and m==1):return binom(n,m) if c<2 else poisson(n*m)
                return betabinom(n,m*s,(1-m)*s) if c<2 else nbinom(m*s,s/(s+n))
            point=float(x.sum()/n.sum());close(point,prior['point_mean']);close(-dist(point,None).logpmf(x).sum(),prior['point_loss'])
            losses=[]
            for start in prior['starts']:
                loss=-float(dist(start['mean'],start['strength']).logpmf(x).mean())
                assert math.isclose(loss,start['average_loss'],rel_tol=1e-6,abs_tol=1e-6)
                if start['success']:losses.append(loss)
            if prior['status']=='count_likelihood':
                assert math.isclose(-float(dist(mu,k).logpmf(x).mean()),min(losses),rel_tol=1e-6,abs_tol=1e-6)
            elif prior['status']=='point_likelihood_selected':assert prior['point_loss']/len(x)<=min(losses)+1.01e-6
        priors[g['group_id']]=prior
        if i%250==0:print(f'Count source replay: {i+1}/{len(groups)}',flush=True)
    independent_signals={};independent_parts={}
    byscope=defaultdict(list)
    for i,r in enumerate(levels):byscope[key(r)].append(i)
    for r in requests:
        focal=labels[tuple(r['identity'])];num=np.zeros(4);den=np.zeros(4);parts=[]
        assert focal['player_id']%5 in r['excluded_folds']
        expected_parts=[(i,c,*measurement(levels[i],c)) for i in byscope[tuple(r['identity'])]
            for c in [0,1]+([2] if focal['position'] in (4,5,6) else [3] if focal['position'] in (7,8,9) else [])]
        assert expected_parts==[(p['source_row_index'],p['channel'],p['count'],p['exposure']) for p in r['parts']]
        for p in r['parts']:
            current=levels[p['source_row_index']];c=p['channel'];x,n=measurement(current,c);g=groupby[p['group_id']]
            assert key(current)==tuple(r['identity']) and (x,n)==(p['count'],p['exposure'])
            assert g['excluded_folds']==r['excluded_folds'] and focal['player_id'] not in g['people']
            for scope in scopekeys(current):
                ids=[j for j in tables[focal['origin_year'],scope,c] if levels[j]['player_id']%5 not in r['excluded_folds']]
                if len({levels[j]['player_id'] for j in ids})>=30 or scope[0]=='position':break
            assert list(scope)==g['scope']
            prior=priors[g['group_id']];mu,k=prior['mean'],prior['strength']
            assert not (n>0 and ((mu==0 and x>0) or (c<2 and mu==1 and x<n))),'Point prior contradicts current evidence'
            weight=0. if k is None or mu==0 or (c<2 and mu==1) else n/(k+n)
            delta=0. if n==0 else weight*(x/n-mu);delta*=(-1 if c<2 else 1)
            num[c]+=n*delta;den[c]+=n;parts.append((p,weight,delta))
        independent_signals[r['request_id']]=np.divide(num,den,out=np.zeros(4),where=den>0)
        independent_parts[r['request_id']]=parts
    features=read(OUT/'features.json.gz');fby={};trace_count=0
    for f in features:
        close(f['signals'],independent_signals[f['request_id']]);fby[f['origin'],f['fold'],f['scope'],tuple(f['identity'])]=f
        for t,(_,weight,delta) in zip(f['count_trace'],independent_parts[f['request_id']],strict=True):
            close(t['posterior']['weight'],weight);close(t['deviation'],delta);trace_count+=1
    tuning_pre=read(PUBLIC/'nuisance-tuning-preflight.json.gz');tuning=read(OUT/'nuisance-tuning-fits.json.gz')
    for p,h in tuning_pre['hashes'].items():assert sha256_file(Path(p))==h,p
    selected={};nested_values={}
    for tag,plan in tuning_pre['nested'].items():
        a=plan['audit'];tr=[labels[tuple(k)] for k in a['training_keys']];te=[labels[tuple(k)] for k in a['test_keys']]
        assert {key(r) for r in tr}=={key(r) for r in labels.values() if r['window_end']<=plan['validation_origin']
            and r['quality_rate'] is not None and r['player_id']%5 not in a['excluded_folds']}
        assert {key(r) for r in te}=={key(r) for r in labels.values() if r['origin_year']==plan['validation_origin']
            and r['player_id']%5==plan['validation_fold']}
        for r in tr+te:assert r['player_id']%5 not in plan['excluded_people_folds']
        saved=tuning['nested_fits'][tag];assert saved['fit_supported']==a['fit_supported']
        assert len({r['player_id'] for r in tr})==a['people']
        assert a['fit_supported']==(a['people']>=30 and len({r['origin_year'] for r in tr})>=2)
        assert all(r['window_end']<=plan['validation_origin'] for r in tr)
        assert {r['player_id'] for r in tr}.isdisjoint(r['player_id'] for r in te)
        assert len(tr)==len({key(r) for r in tr}) and len(te)==len({key(r) for r in te})
        if not saved['fit_supported']:continue
        for alpha,model in saved['fits'].items():
            assert int(alpha)==model['alpha']
            mu,sd,ym,coef=independent_baseline_fit(tr,saved['age_median'],model)
            vals=ym+((design(te,saved['age_median'],model['names'])-mu)/sd)@coef
            nested_values[tag,int(alpha)]=[(r,float(v)) for r,v in zip(te,vals,strict=True)]
    for parent in tuning['selected']:
        assert parent['nested_tags']==next(p['nested_tags'] for p in tuning_pre['nuisances']
            if (p['origin'],p['fold'],p['held'])==(parent['origin'],parent['fold'],parent['held']))
        scores={}
        for alpha in (10,100):
            values=[(r,v) for tag in parent['nested_tags'] for r,v in nested_values.get((tag,alpha),[]) if r['quality_rate'] is not None]
            for r,v in values:
                assert r['window_end']<=parent['origin'] and r['player_id']%5 not in (parent['fold'],parent['held'])
            if values:
                w=weights([r for r,v in values]);err=np.array([v-r['quality_rate'] for r,v in values]);scores[str(alpha)]=float(np.sqrt(np.average(err*err,weights=w)))
                close(scores[str(alpha)],parent['scores'][str(alpha)])
            else:scores[str(alpha)]=None;assert parent['scores'][str(alpha)] is None
            assert parent['validation_support'][str(alpha)]==dict(rows=len(values),people=len({r['player_id'] for r,v in values}))
        alpha=100 if scores['10'] is None or scores['100']<=scores['10'] else 10
        assert alpha==parent['selected_alpha'];selected[parent['origin'],parent['fold'],parent['held']]=alpha
    cells=read(PUBLIC/'cells-preflight.json.gz');nuisances=read(OUT/'nuisance-fits.json.gz');residuals={}
    for note in nuisances:
        year,outer,held=note['origin'],note['fold'],note['held'];a=note['audit'];tr=[labels[tuple(k)] for k in a['training_keys']];te=[labels[tuple(k)] for k in a['test_keys']]
        expected=[r for r in labels.values() if r['window_end']<=year and r['quality_rate'] is not None and r['player_id']%5 not in (outer,held)]
        assert {key(r) for r in tr}=={key(r) for r in expected} and {r['player_id'] for r in tr}.isdisjoint(r['player_id'] for r in te)
        if note['fit'] is None:assert not a['fit_supported'];continue
        assert note['fit']['alpha']==selected[year,outer,held]
        ages=[r['age'] for r in tr if r['age'] is not None];median=float(np.median(ages)) if ages else 23.;close(median,note['age_median'])
        mu,sd,ym,coef=independent_baseline_fit(tr,median,note['fit']);values=ym+((design(te,median,note['fit']['names'])-mu)/sd)@coef
        assert len(note['held_predictions'])==len(te)
        for r,v,saved in zip(te,values,note['held_predictions'],strict=True):
            assert saved['identity']==list(key(r));close(v,saved['baseline']);close(r['quality_rate']-v,saved['residual'])
            residuals[year,outer,key(r)]=r['quality_rate']-v
    fits=read(OUT/'correction-fits.json.gz');preflights=read(PUBLIC/'correction-preflights.json.gz')
    outputs=pl.read_parquet(OUT/'predictions.parquet').to_dicts();pby={key(r):r for r in outputs};old=pl.read_parquet(ROOT/'reports/generated/defense-minor-range-v19/predictions.parquet').to_dicts()
    assert set(pby)=={key(r) for r in old}
    for previous in old:
        current=pby[key(previous)];close(current['baseline'],previous['baseline']);close(current['old_selected'],previous['candidate'])
        assert current['quality_rate']==previous['quality_rate'] and current['quality_status']==previous['quality_status']
    for cell,note,check in zip(cells,fits,preflights,strict=True):
        year,fold=cell['origin'],cell['fold'];tr=[labels[tuple(k)] for k in note['training_keys']];te=[labels[tuple(k)] for k in cell['outer_audit']['test_keys']]
        s=np.array([independent_signals[cell['train_requests'][str(key(r))]] for r in tr]);w=weights(tr);y=np.array([residuals[year,fold,key(r)] for r in tr])
        close(s,check['training_signals']);model=note['fit']
        if model is not None:
            scale=np.sqrt(np.average(s*s,axis=0,weights=w));active=scale>1e-12;scale=np.where(active,scale,1.);z=s/scale
            lhs=np.vstack((np.sqrt(w)[:,None]*z,10*np.eye(4)));rhs=np.concatenate((np.sqrt(w)*y,np.zeros(4)))
            coef=np.linalg.lstsq(lhs,rhs,rcond=None)[0];coef[~active]=0
            close(scale,model['scale']);close(coef,model['coefficients']);assert model['alpha']==100 and model['intercept']==0
        stages=defaultdict(set);joints=defaultdict(set);indices=defaultdict(list)
        for i,r in enumerate(tr):
            k=(r['position'],r['level']);stages[k].add(r['player_id']);joints[k+(r['age_band'],r['sample_band'])].add(r['player_id']);indices[k].append(i)
        for r in te:
            saved=pby[key(r)];signal=independent_signals[cell['test_requests'][str(key(r))]];k=(r['position'],r['level'])
            stage=len(stages[k]);joint=len(joints[k+(r['age_band'],r['sample_band'])]);reasons=[]
            if model is None:reasons.append('unsupported_pooled_correction')
            if stage<10:reasons.append('fewer_than_ten_position_level_people')
            if joint<5:reasons.append('fewer_than_five_joint_profile_people')
            ix=indices.get(k);outside=[] if not ix else ((signal<s[ix].min(axis=0))|(signal>s[ix].max(axis=0))).tolist()
            if any(outside):reasons.append('count_signal_outside_position_level_range')
            assert reasons==saved['reasons'] and saved['applied']==(not reasons) and saved['stage_people']==stage and saved['joint_people']==joint
            terms=signal/scale*coef if not reasons else np.zeros(4)
            close(terms,saved['correction_terms']);close(terms.sum(),saved['correction']);close(saved['candidate'],saved['baseline']+terms.sum())
            if reasons:assert saved['candidate']==saved['baseline']
    records=[dict(origin_year=int(y),rows=[r for r in outputs if r['origin_year']==int(y)],saved=v) for y,v in report['headline'].items()]
    records.extend(dict(origin_year=g['origin_year'],rows=[r for r in outputs if r['origin_year']==g['origin_year'] and r[g['column']]==g['value']],saved=g) for g in report['groups'])
    for item in records:
        for arm in ('baseline','old_selected','candidate'):
            m=independent_score(item['rows'],arm);saved=item['saved']['scores'][arm]
            if m is None:assert saved is None
            else:
                for k,v in m.items():close(v,saved[k])
        interval=independent_interval(item['rows'])
        if interval:
            for k,v in interval.items():close(v,item['saved']['paired'][k])
    paths=[Path(__file__),PUBLIC/'preflight.json.gz',PUBLIC/'sources-complete.json.gz',PUBLIC/'fit-report.json.gz',
           PUBLIC/'resume-preflight.json.gz',
           PUBLIC/'nuisance-tuning-preflight.json.gz',OUT/'nuisance-tuning-fits.json.gz',
           OUT/'nuisance-fits.json.gz',OUT/'correction-fits.json.gz',OUT/'features.json.gz',OUT/'predictions.parquet']
    write(PUBLIC/'independent-review.json.gz',dict(source_groups_replayed=len(groups),source_requests_replayed=len(requests),
        source_trace_records_replayed=trace_count,nuisance_fits_replayed=sum(n['fit'] is not None for n in nuisances),
        correction_fits_replayed=sum(n['fit'] is not None for n in fits),forecasts_replayed=len(outputs),
        nuisance_penalty_selection_fully_player_separated=True,nested_baseline_cells_replayed=len(tuning_pre['nested']),
        all_cutoffs_and_people_exclusions=True,baseline_unchanged=True,real_fallback_replayed=True,
        group_scores_and_person_bootstraps=True,player_walkthrough_status='pending',
        hashes={str(p):sha256_file(p) for p in paths}))
    print(dict(independent_replay='pass',forecasts=len(outputs),sources=len(groups)),flush=True)


if __name__=='__main__':main()
