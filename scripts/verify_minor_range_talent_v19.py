"""Replay fold identities, source-trace arithmetic, fits, tuning and scores."""
from collections import Counter,defaultdict
from pathlib import Path
import gzip
import hashlib
import json
import math

import numpy as np
import polars as pl

from run_hitter_finite_return_baseline import protections

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/generated/defense-minor-range-v19'
PUBLIC=ROOT/'reports/model-evidence/defense-minor-range-v19'
SOURCE=ROOT/'reports/generated/defense-minor-counts-v18'


def data(p):
    if Path(str(p)+'.gz').exists():
        with gzip.open(str(p)+'.gz','rt',encoding='utf8') as f:return json.load(f)
    return json.loads(p.read_text(encoding='utf-8-sig'))


def digest(p):
    if Path(str(p)+'.gz').exists():
        with gzip.open(str(p)+'.gz','rb') as f:return hashlib.sha256(f.read()).hexdigest()
    return hashlib.sha256(p.read_bytes()).hexdigest()


def near(a,b):
    assert np.allclose(a,b,rtol=1e-8,atol=1e-9), (a,b)


def weights(rs):
    ns=Counter(r['player_id'] for r in rs)
    return np.array([1/ns[r['player_id']] for r in rs])


def score(rs,key):
    rs=[r for r in rs if r['quality_rate'] is not None]
    if not rs:return None
    w=weights(rs);e=np.array([r[key]-r['quality_rate'] for r in rs])
    return dict(rows=len(rs),people=len(set(r['player_id'] for r in rs)),rmse=float(np.sqrt((w*e*e).sum()/w.sum())),
                mae=float((w*abs(e)).sum()/w.sum()),bias=float((w*e).sum()/w.sum()))


def same_scores(a,b):
    if a is None or b is None:assert a is b;return
    assert a['rows']==b['rows'] and a['people']==b['people']
    for k in ('rmse','mae','bias'):near(a[k],b[k])


def main():
    protections();assert not (OUT/'independent-review.json.gz').exists()
    report=data(OUT/'fit-report.json');pre=data(OUT/'run-preflight.json')
    for path,h in pre['hashes'].items():assert digest(Path(path))==h,path
    for path,h in report['hashes'].items():assert digest(Path(path))==h,path
    lab=pl.read_parquet(SOURCE/'labels.parquet').filter((pl.col('component')=='range')&(pl.col('window')==3)&(~pl.col('prior_current_MLB_fielding'))).to_dicts()
    key=lambda r:(r['origin_year'],r['player_id'],r['position'])
    lookup={key(r):r for r in lab};expected={key(r) for r in lab if r['origin_year'] in (2021,2022)}
    preds=pl.read_parquet(OUT/'predictions.parquet').to_dicts();assert len(preds)==len(expected) and {key(r) for r in preds}==expected
    cellrecords={};fitted=0;trace_checks=0
    unique={}
    for c in report['cells']:
        if c['tag'] in unique:assert c==unique[c['tag']], 'Shared inner cell changed across outer origins'
        unique[c['tag']]=c
    for cell in unique.values():
        tag=cell['tag'];audit=data(OUT/f'cells/{tag}-preflight.json');saved=data(OUT/f'cells/{tag}-fit.json')
        assert digest(OUT/f'cells/{tag}-preflight.json')==cell['preflight_hash']
        assert digest(Path(cell['feature_path']))==cell['feature_hash']
        tr=[lookup[tuple(k)] for k in audit['train_keys']];te=[lookup[tuple(k)] for k in audit['test_keys']]
        cutoff=audit['cutoff'];excluded=set(audit['excluded_folds'])
        train_expected={key(r) for r in lab if r['quality_rate'] is not None and r['window_end']<=cutoff and r['player_id']%5 not in excluded}
        assert set(map(tuple,audit['train_keys']))==train_expected
        test_expected={key(r) for r in lab if r['origin_year']==cutoff and r['player_id']%5==audit['held_fold']
                       and (audit['kind']=='outer' or r['player_id']%5!=audit['outer_fold'])}
        assert set(map(tuple,audit['test_keys']))==test_expected
        assert {r['player_id'] for r in tr}.isdisjoint(r['player_id'] for r in te)
        assert all(r['origin_year']==cutoff for r in te)
        assert audit['training_people']==len({r['player_id'] for r in tr})
        stage=defaultdict(set);joint=defaultdict(set)
        for r in tr:
            stage[r['level'],r['position']].add(r['player_id'])
            joint[r['level'],r['position'],r['age_band'],r['sample_band']].add(r['player_id'])
        features=pl.read_parquet(cell['feature_path']).to_dicts();ft=[r for r in features if r['scope']=='train'];fe=[r for r in features if r['scope']=='test']
        assert [key(r) for r in ft]==[key(r) for r in tr] and [key(r) for r in fe]==[key(r) for r in te]
        for r,source in zip([*ft,*fe],[*tr,*te],strict=True):
            traces=json.loads(r['level_trace']);sums=np.zeros(4);den=np.zeros(4)
            names=('glove_avoidance','throw_avoidance','infield_plays','outfield_plays')
            assert sum(t['outs'] for t in traces)==source['minor_outs']
            for t in traces:
                for s in t['signals']:
                    j=names.index(s['channel']);p=s['prior'];n=s['denominator'];x=s['numerator']
                    assert set(p['excluded_folds'])==excluded and max(p['reference_years'],default=source['origin_year'])<=source['origin_year']
                    assert 2020 not in p['reference_years']
                    expected_n=t['counts']['chances'] if j in (0,1) else t['outs']
                    expected_x=t['counts']['errors']-t['counts']['throwingErrors'] if j==0 else t['counts']['throwingErrors'] if j==1 else t['counts']['assists'] if j==2 else t['counts']['putOuts']
                    assert n==expected_n and x==expected_x
                    reliability=n/(n+p['strength']) if n>0 and p['strength'] is not None else 0.
                    near(s['reliability'],reliability)
                    raw=x/n if n else None;assert (s['raw_rate'] is None)==(raw is None)
                    if raw is not None:near(s['raw_rate'],raw)
                    deviation=reliability*(raw-p['mean']) if raw is not None else 0.
                    near(s['posterior_rate'],p['mean']+deviation);near(s['deviation'],-deviation if j in (0,1) else deviation)
                    sums[j]+=n*s['deviation'];den[j]+=n;trace_checks+=1
            signals=np.divide(sums,den,out=np.zeros(4),where=den>0);near(signals,r['signals'])
            age=source['age'];design=[((age if age is not None else audit['age_median'])-23)/5,int(age is None),math.log1p(source['minor_outs'])-math.log(1501)]
            design.extend(int(source['position']==p) for p in range(3,10))
            design.extend(int(source['level']==l) for l in ('AAA','AA','Aplus','A','Aminus','ADVANCED_ROOKIE','ROOKIE_COMBINED','COMPLEX','DSL'))
            near([*design,*signals],r['candidate_design'])
        for r,s in zip(te,audit['profile_rows'],strict=True):
            assert s['level_position_people']==len(stage[r['level'],r['position']])
            assert s['joint_people']==len(joint[r['level'],r['position'],r['age_band'],r['sample_band']])
            assert s['unseen_level_position']==(len(stage[r['level'],r['position']])==0)
        xt=np.array([r['candidate_design'] for r in ft]);xe=np.array([r['candidate_design'] for r in fe]);w=weights(tr)
        near(audit['train_feature_min'],xt.min(axis=0));near(audit['train_feature_max'],xt.max(axis=0))
        for i,s in enumerate(audit['profile_rows']):
            assert s['outside_feature_range']==((xe[i]<xt.min(axis=0))|(xe[i]>xt.max(axis=0))).tolist()
        valid=audit['training_people']>=30 and len({r['origin_year'] for r in tr})>=2
        assert valid==audit['fit_supported'];computed={}
        for name,fit in saved['fits'].items():
            arm,alpha=name.rsplit('-',1);x=xt if arm=='candidate' else xt[:,:19];xv=xe if arm=='candidate' else xe[:,:19]
            if not valid:assert fit is None;computed[name]=np.zeros(len(te));continue
            assert fit['alpha']==int(alpha);mu=np.average(x,axis=0,weights=w);ys=np.array([r['quality_rate'] for r in tr]);ym=np.average(ys,weights=w)
            scale=np.ones(x.shape[1])
            for j in [0,2,*range(19,x.shape[1])]:
                v=np.average((x[:,j]-mu[j])**2,weights=w);scale[j]=np.sqrt(v) if v>1e-20 else 1.
            near(fit['mean'],mu);near(fit['scale'],scale);near(fit['target_mean'],ym)
            z=(x-mu)/scale
            # Different solver from the model's normal equations.
            augmented=np.vstack([np.sqrt(w)[:,None]*z,np.sqrt(int(alpha))*np.eye(x.shape[1])])
            target=np.concatenate([np.sqrt(w)*(ys-ym),np.zeros(x.shape[1])])
            coefficients=np.linalg.lstsq(augmented,target,rcond=None)[0];near(coefficients,fit['coefficients'])
            computed[name]=ym+((xv-mu)/scale)@coefficients;fitted+=1
        unseen=np.array([r['unseen_level_position'] for r in audit['profile_rows']])
        for alpha in (10,100):computed[f'candidate-{alpha}'][unseen]=computed[f'baseline-{alpha}'][unseen]
        rs=saved['test_prediction_hash_input'];assert [key(r) for r in rs]==[key(r) for r in te]
        for i,r in enumerate(rs):
            for name,values in computed.items():near(r[name],values[i])
        cellrecords[tag]=rs
        print(f'Verified {tag}',flush=True)
    for t in report['tuning']:
        year,fold=t['origin'],t['outer_fold'];val=[]
        for c in unique.values():
            if c['kind']=='inner' and c['outer_fold']==fold and c['cutoff'] in t['validation_origins'] and c['fit_supported']:
                val.extend(cellrecords[c['tag']])
        scores={str(a):score(val,f"{t['arm']}-{a}") for a in (10,100)}
        for a in ('10','100'):same_scores(scores[a],t['scores'][a])
        selected=min((10,100),key=lambda a:(scores[str(a)]['rmse'],-a)) if scores['10'] is not None else 100
        assert t['selected_alpha']==selected
    for r in preds:
        source=lookup[key(r)];assert r['quality_rate']==source['quality_rate'] and r['quality_status']==source['quality_status']
        same=next(s for s in cellrecords[r['cell_tag']] if key(s)==key(r))
        near(r['baseline'],same[f"baseline-{r['baseline_alpha']}"])
        near(r['candidate'],r['baseline'] if r['support']['unseen_level_position'] else same[f"candidate-{r['candidate_alpha']}"])
    for overall in report['overall']:
        rs=[r for r in preds if r['origin_year']==overall['origin']]
        for arm in ('neutral','baseline','candidate'):same_scores(score(rs,arm),overall['scores'][arm])
        by=defaultdict(list)
        for r in rs:
            if r['quality_rate'] is not None:by[r['player_id']].append(r)
        errors=np.array([[np.mean([(r['baseline']-r['quality_rate'])**2 for r in s]),np.mean([(r['candidate']-r['quality_rate'])**2 for r in s]),
                          np.mean([abs(r['baseline']-r['quality_rate']) for r in s]),np.mean([abs(r['candidate']-r['quality_rate']) for r in s])] for _,s in sorted(by.items())])
        rng=np.random.default_rng(19019);ix=rng.integers(0,len(errors),size=(2000,len(errors)))
        values=errors[ix].mean(axis=1)
        near(np.quantile(np.sqrt(values[:,1])-np.sqrt(values[:,0]),[.025,.975]),overall['interval']['rmse_delta_interval'])
        near(np.quantile(values[:,3]-values[:,2],[.025,.975]),overall['interval']['mae_delta_interval'])
    for group in report['groups']:
        rs=[r for r in preds if r['origin_year']==group['origin'] and r[group['group']]==group['value']]
        for arm in ('neutral','baseline','candidate'):same_scores(score(rs,arm),group['scores'][arm])
    receipt=dict(status='fit_score_provenance_replayed_pending_raw_reference_and_player_review',fit_cell_uses=len(report['cells']),unique_fit_cells=len(unique),fitted_parameter_sets=fitted,
                 reference_trace_arithmetic_checks=trace_checks,population_rows=len(preds),player_walkthrough_status='pending',
                 raw_reference_group_replay='required in selected player walkthrough before disposition',no_2026_outcomes=True,
                 hashes={str(p):digest(p) for p in (Path(__file__),OUT/'run-preflight.json',OUT/'fit-report.json',OUT/'predictions.parquet')})
    payload=(json.dumps(receipt,indent=2)+'\n').encode()
    for folder in (OUT,PUBLIC):
        path=folder/'independent-review.json.gz';assert not path.exists();path.write_bytes(gzip.compress(payload,mtime=0))
    protections();print(json.dumps({k:v for k,v in receipt.items() if k!='hashes'}),flush=True)


if __name__=='__main__':main()
