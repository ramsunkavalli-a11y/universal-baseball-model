"""Separate arithmetic and source-membership replay of the count calibration."""
from collections import defaultdict
from pathlib import Path
import gzip
import json
import math

import numpy as np
import polars as pl
from scipy.stats import betabinom,binom,nbinom,poisson

from universal_baseball.storage import sha256_file

ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/'reports/model-evidence/defense-count-reliability-v20'
OUT=ROOT/'reports/generated/defense-count-reliability-v20'
SOURCE=ROOT/'reports/generated/defense-minor-counts-v18'


def read(p):
    with gzip.open(p,'rt',encoding='utf8') as f:return json.load(f)


def write(p,v):
    assert not p.exists()
    with gzip.open(p,'wt',encoding='utf8') as f:json.dump(v,f,allow_nan=False,separators=(',',':'))


def channel(row,c):
    if c==0:return row['errors']-row['throwingErrors'],row['chances']
    if c==1:return row['throwingErrors'],row['chances']
    if c==2:return row['assists'],row['outs']
    return row['putOuts'],row['outs']


def scopes(r):
    a=r['age'];band='unknown' if a is None else '<=19' if a<=19 else '20-22' if a<=22 else '23-25' if a<=25 else '26+'
    return [('position_level_age',r['position'],r['level'],band),('position_level',r['position'],r['level']),
            ('position_age',r['position'],band),('position',r['position'])]


def dist(mean,k,n,c):
    if k is None or mean==0 or (c<2 and mean==1):return binom(n,mean) if c<2 else poisson(n*mean)
    return betabinom(n,mean*k,(1-mean)*k) if c<2 else nbinom(mean*k,k/(k+n))


def close(a,b):
    assert math.isclose(a,b,rel_tol=1e-7,abs_tol=1e-8),(a,b)


def independently_score(rs):
    q=[r for r in rs if r['target_status']=='observed_positive_exposure'];by=defaultdict(list)
    for r in q:by[r['player_id']].append(r)
    def weighted(fn):return np.mean([np.mean([fn(r) for r in v]) for v in by.values()])
    arms={}
    for arm in ('baseline','candidate'):
        impossible=sum(r[arm+'_impossible'] for r in q)
        arms[arm]=dict(impossible_rows=impossible,mean_nll=None if impossible else float(weighted(lambda r:r[arm+'_loss'])),
                      rate_rmse=math.sqrt(weighted(lambda r:(r[arm+'_mean']-r['target_count']/r['target_exposure'])**2)),
                      rate_bias=float(weighted(lambda r:r[arm+'_mean']-r['target_count']/r['target_exposure'])),
                      coverage90=float(weighted(lambda r:r[arm+'_covered'])),width90=float(weighted(lambda r:r[arm+'_upper']-r[arm+'_lower'])))
    paired=defaultdict(list)
    for r in q:
        if not r['baseline_impossible'] and not r['candidate_impossible']:paired[r['player_id']].append(r)
    delta=np.array([np.mean([r['candidate_loss']-r['baseline_loss'] for r in v]) for pid,v in sorted(paired.items())])
    if not len(delta):return arms,None
    rng=np.random.default_rng(20020)
    boots=[float(delta[rng.integers(0,len(delta),len(delta))].mean()) for _ in range(2000)]
    return arms,dict(mean_nll_delta=float(delta.mean()),interval95=np.quantile(boots,[.025,.975]).tolist(),people=len(delta))


def main():
    pre=read(PUBLIC/'preflight.json.gz');summary=read(PUBLIC/'summary.json.gz')
    for record in (pre,summary):
        for p,h in record['hashes'].items():assert sha256_file(Path(p))==h,p
    levels=read(PUBLIC/'source-levels.json.gz');groups=read(PUBLIC/'reference-groups.json.gz')
    evaluation=read(PUBLIC/'evaluation.json.gz');pred=pl.read_parquet(OUT/'predictions.parquet').to_dicts()
    assert len(pred)==len(evaluation)==pre['rows']
    raw=pl.read_parquet(SOURCE/'counts.parquet').filter(pl.col('position_code').is_in([str(p) for p in range(3,10)])).to_dicts()
    origins=pl.read_parquet(SOURCE/'origins.parquet').filter(pl.col('position').is_between(3,9)).to_dicts()
    originmap={(r['origin_year'],r['player_id'],r['position']):r for r in origins}
    aggregates=defaultdict(lambda:dict(outs=0,putOuts=0,assists=0,errors=0,chances=0,throwingErrors=0,source_indices=[]))
    for i,r in enumerate(raw):
        key=(r['season'],r['player_id'],int(r['position_code']),r['normalized_level']);a=aggregates[key]
        a['outs']+=r['fielding_outs'];a['source_indices'].append(i)
        for f in ('putOuts','assists','errors','chances','throwingErrors'):
            assert r[f+'_status']=='recorded';a[f]+=r[f]
    expectedkeys=sorted(k for k in aggregates if k[:3] in originmap)
    assert len(expectedkeys)==len(levels)
    for key,r in zip(expectedkeys,levels,strict=True):
        assert key==(r['origin_year'],r['player_id'],r['position'],r['level'])
        for f,v in aggregates[key].items():assert r[f]==v,(key,f)
        for f in ('age','age_band','prior_current_MLB_fielding'):assert r[f]==originmap[key[:3]][f]
    tables=defaultdict(list)
    for year in (2018,2021,2022):
        for i,r in enumerate(levels):
            if not year-2<=r['origin_year']<=year:continue
            channels=[0,1]+([2] if r['position'] in (4,5,6) else [3] if r['position'] in (7,8,9) else [])
            for c in channels:
                if channel(r,c)[1]<=0:continue
                for scope in scopes(r):tables[(year,scope,c)].append(i)
    notes={};groupsby={g['group_id']:g for g in groups}
    for i,g in enumerate(groups):
        year,fold,c=g['origin_year'],g['fold'],g['channel'];scope=tuple(g['scope'])
        ids=[i for i in tables[year,scope,c] if levels[i]['player_id']%5!=fold]
        assert ids==g['source_row_indices'];people=sorted({levels[i]['player_id'] for i in ids});assert people==g['people']
        by=defaultdict(list)
        for j in ids:by[levels[j]['player_id']].append(channel(levels[j],c))
        rates=np.mean([np.mean([x/n for x,n in v]) for v in by.values()])
        second=np.mean([np.mean([(x/n)**2 for x,n in v]) for v in by.values()])
        inv=np.mean([np.mean([1/n for x,n in v]) for v in by.values()]);count=len(by)
        variance=max(0.,second-rates*rates)*count/(count-1) if count>1 else 0.
        between=max(0.,(variance-rates*(1-rates)*inv)/(1-inv)) if c<2 and inv<1 else max(0.,variance-rates*inv) if c>=2 else 0.
        if c<2:between=min(between,rates*(1-rates)*(1-1e-9))
        k=rates*(1-rates)/between-1 if c<2 and between>0 else rates/between if c>=2 and between>0 else None
        if count<30 or rates<=0 or (c<2 and rates>=1):k=None;between=0.
        note=read(PUBLIC/'fits'/f"{g['group_id']}.json.gz");assert note['preflight_hash']==sha256_file(PUBLIC/'preflight.json.gz')
        close(note['baseline']['mean'],rates);close(note['baseline']['between_variance'],between)
        assert (note['baseline']['strength'] is None)==(k is None)
        if k is not None:close(note['baseline']['strength'],k)
        xs=np.array([sum(x for x,n in v) for pid,v in sorted(by.items())]);ns=np.array([sum(n for x,n in v) for pid,v in sorted(by.items())])
        assert int(xs.sum())==g['source_count'] and int(ns.sum())==g['source_exposure']
        candidate=note['candidate'];close(candidate['point_mean'],float(xs.sum()/ns.sum()))
        point_loss=-float(dist(candidate['point_mean'],None,ns,c).logpmf(xs).sum());close(point_loss,candidate['point_loss'])
        valid=[]
        for start in candidate['starts']:
            loss=-float(dist(start['mean'],start['strength'],ns,c).logpmf(xs).mean())
            assert math.isclose(loss,start['average_loss'],abs_tol=1e-6,rel_tol=1e-6),(g['group_id'],loss,start['average_loss'])
            if start['success']:valid.append((loss,start['mean'],start['strength']))
        if candidate['status']=='count_likelihood':
            chosen=-float(dist(candidate['mean'],candidate['strength'],ns,c).logpmf(xs).mean())
            assert math.isclose(chosen,min(v[0] for v in valid),abs_tol=1e-6)
            assert chosen+1e-6<point_loss/len(xs)
        elif candidate['status']=='point_likelihood_selected':assert point_loss/len(xs)<=min(v[0] for v in valid)+1.01e-6
        notes[g['group_id']]=note
        if i%200==0:print(f'Reference membership and likelihood replay: {i+1}/{len(groups)}',flush=True)
    expected=[]
    for i,r in enumerate(levels):
        if r['origin_year'] not in (2018,2021,2022) or r['prior_current_MLB_fielding']:continue
        cs=[0,1]+([2] if r['position'] in (4,5,6) else [3] if r['position'] in (7,8,9) else [])
        expected.extend((r['origin_year'],r['player_id'],r['position'],r['level'],c,i) for c in cs)
    actual=[(r['origin_year'],r['player_id'],r['position'],r['level'],r['channel'],r['source_row_index']) for r in evaluation]
    assert actual==expected
    for i,(e,r) in enumerate(zip(evaluation,pred,strict=True)):
        for field,value in e.items():assert r[field]==value,(i,field)
        source=levels[e['source_row_index']];c=e['channel'];g=groupsby[e['group_id']]
        for scope in scopes(source):
            ids=[j for j in tables[e['origin_year'],scope,c] if levels[j]['player_id']%5!=e['fold']]
            if len({levels[j]['player_id'] for j in ids})>=30:break
        assert list(scope)==g['scope']
        x,n=channel(source,c);assert (x,n)==(e['current_count'],e['current_exposure'])
        target=aggregates.get((e['origin_year']+1,e['player_id'],e['position'],e['level']))
        if target is None:assert e['target_count'] is None and e['target_exposure'] is None
        else:assert channel(target,c)==(e['target_count'],e['target_exposure'])
        for arm in ('baseline','candidate'):
            prior=notes[e['group_id']][arm];mu,k=prior['mean'],prior['strength']
            if k is None or mu==0 or (c<2 and mu==1):postmean=mu;postk=None;weight=var=0.
            else:
                postk=k+n;postmean=(k*mu+x)/postk;weight=n/postk
                var=postmean*(1-postmean)/(postk+1) if c<2 else postmean/postk
            close(r[arm+'_mean'],postmean);close(r[arm+'_weight'],weight);close(r[arm+'_latent_variance'],var)
            assert (r[arm+'_strength'] is None)==(postk is None)
            if postk is not None:close(r[arm+'_strength'],postk)
            if e['target_status']!='observed_positive_exposure':continue
            distribution=dist(postmean,postk,e['target_exposure'],c)
            loss=-float(distribution.logpmf(e['target_count']));assert r[arm+'_impossible']==(not math.isfinite(loss))
            if math.isfinite(loss):close(r[arm+'_loss'],loss)
            else:assert r[arm+'_loss'] is None
            lo,hi=map(float,distribution.ppf([.05,.95]));close(lo,r[arm+'_lower']);close(hi,r[arm+'_upper'])
            assert r[arm+'_covered']==(lo<=e['target_count']<=hi)
            close(float(distribution.var()),r[arm+'_predictive_variance'])
        if i%10000==0:print(f'Posterior and future count replay: {i+1}/{len(pred)}',flush=True)
    for year in (2018,2021,2022):
        arms,paired=independently_score([r for r in pred if r['origin_year']==year]);saved=summary['origins'][str(year)]
        for arm,metrics in arms.items():
            for key,value in metrics.items():
                if value is None:assert saved['arms'][arm][key] is None
                else:close(value,saved['arms'][arm][key])
        if paired:
            close(paired['mean_nll_delta'],saved['paired']['mean_nll_delta'])
            np.testing.assert_allclose(paired['interval95'],saved['paired']['interval95'],atol=1e-12,rtol=0)
    # All group metrics/intervals are rechecked, not only the three headlines.
    for g in summary['groups']:
        rs=[r for r in pred if r['origin_year']==g['origin_year'] and r[g['column']]==g['value']]
        if not any(r['target_status']=='observed_positive_exposure' for r in rs):continue
        arms,paired=independently_score(rs)
        for arm,m in arms.items():
            for key,value in m.items():
                if value is None:assert g['score']['arms'][arm][key] is None
                else:close(value,g['score']['arms'][arm][key])
        if paired:
            close(paired['mean_nll_delta'],g['score']['paired']['mean_nll_delta'])
            np.testing.assert_allclose(paired['interval95'],g['score']['paired']['interval95'],atol=1e-12,rtol=0)
    paths=[Path(__file__),PUBLIC/'preflight.json.gz',PUBLIC/'summary.json.gz',OUT/'predictions.parquet',
           PUBLIC/'reference-groups.json.gz',PUBLIC/'source-levels.json.gz',PUBLIC/'evaluation.json.gz']
    paths.extend(PUBLIC/'fits'/f"{g['group_id']}.json.gz" for g in groups)
    write(PUBLIC/'independent-review.json.gz',dict(reference_groups_replayed=len(groups),source_level_rows_replayed=len(levels),
        forecasts_replayed=len(pred),all_memberships_and_cutoffs=True,all_posteriors_and_distributions=True,
        scores_and_2000_person_bootstraps_replayed=True,source_screen_not_MLB_talent=True,player_walkthrough_status='pending',
        hashes={str(p):sha256_file(p) for p in paths}))
    print(dict(independent_replay='pass',forecasts=len(pred),groups=len(groups)),flush=True)


if __name__=='__main__':main()
