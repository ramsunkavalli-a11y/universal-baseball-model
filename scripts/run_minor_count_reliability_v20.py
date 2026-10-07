"""Fixed source-count calibration gate, distinct from future MLB talent."""
from collections import Counter, defaultdict
from pathlib import Path
import argparse
import gzip
import json
import math

import numpy as np
import polars as pl

from run_hitter_finite_return_baseline import protections
from universal_baseball.storage import sha256_file
from universal_baseball.minor_range_talent import age_group, moments, CHANNELS
from universal_baseball.minor_count_reliability import fit_prior, posterior, predictive, validate_counts

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'reports/generated/defense-minor-counts-v18'
OUT=ROOT/'reports/generated/defense-count-reliability-v20'
PUBLIC=ROOT/'reports/model-evidence/defense-count-reliability-v20'
COUNT_FIELDS=('putOuts','assists','errors','chances','throwingErrors')
YEARS=(2018,2021,2022)


def read(path):
    with gzip.open(path,'rt',encoding='utf8') as stream:return json.load(stream)


def write(path,value):
    assert not path.exists(),f'Preserve completed or partial evidence: {path}'
    path.parent.mkdir(parents=True,exist_ok=True)
    with gzip.open(path,'wt',encoding='utf8',compresslevel=6) as stream:
        json.dump(value,stream,allow_nan=False,separators=(',',':'))


def measurements(row):
    result=[(0,row['errors']-row['throwingErrors'],row['chances']),(1,row['throwingErrors'],row['chances'])]
    if row['position'] in (4,5,6):result.append((2,row['assists'],row['outs']))
    if row['position'] in (7,8,9):result.append((3,row['putOuts'],row['outs']))
    for c,x,n in result:validate_counts([x],[n],c<2)
    return result


def choices(row):
    p,l,a=row['position'],row['level'],age_group(row['age'])
    return [('position_level_age',p,l,a),('position_level',p,l),('position_age',p,a),('position',p)]


def source_rows(raw,origins):
    """No future labels affect source eligibility or aggregation."""
    originmap={(r['origin_year'],r['player_id'],r['position']):r for r in origins}
    agg={}
    for i,r in enumerate(raw):
        pos=int(r['position_code']);key=(r['season'],r['player_id'],pos,r['normalized_level'])
        if key not in agg:
            agg[key]=dict(origin_year=key[0],player_id=key[1],position=pos,level=key[3],
                          player_name=r['player_name'],outs=0,source_indices=[],**{f:0 for f in COUNT_FIELDS})
        dest=agg[key];dest['outs']+=r['fielding_outs'];dest['source_indices'].append(i)
        for f in COUNT_FIELDS:
            assert r[f] is not None and r[f+'_status']=='recorded',(key,f)
            dest[f]+=r[f]
        assert r['chances_identity'] and r['throwing_subset_identity'],key
    rows=[]
    for key,r in sorted(agg.items()):
        o=originmap.get(key[:3])
        if o is None:continue
        assert r['chances']==r['putOuts']+r['assists']+r['errors']
        r=dict(r,age=o['age'],age_band=o['age_band'],prior_current_MLB_fielding=o['prior_current_MLB_fielding'])
        measurements(r);rows.append(r)
    by=defaultdict(int)
    for r in rows:by[r['origin_year'],r['player_id'],r['position']]+=r['outs']
    assert all(by[k]==r['minor_outs'] for k,r in originmap.items())
    return rows,agg


def prepare():
    protections()
    assert not (PUBLIC/'preflight.json.gz').exists(),'Preserve sealed population'
    review=json.loads((SOURCE/'final-review.json').read_text('utf8'))
    assert review['player_walkthrough_status']=='complete'
    for name in ('final-review','source-preflight','source-review','support-preflight','support-review','independent-review'):
        for p,h in json.loads((SOURCE/f'{name}.json').read_text('utf8'))['hashes'].items():
            assert sha256_file(Path(p))==h,p
    origins=pl.read_parquet(SOURCE/'origins.parquet').filter(pl.col('position').is_between(3,9)).to_dicts()
    raw=pl.read_parquet(SOURCE/'counts.parquet').filter(pl.col('position_code').is_in([str(p) for p in range(3,10)])).to_dicts()
    rows,future=source_rows(raw,origins)
    table={}
    for year in YEARS:
        scopes=defaultdict(list)
        for i,r in enumerate(rows):
            if not year-2<=r['origin_year']<=year:continue
            for c,x,n in measurements(r):
                if n<=0:continue
                for key in choices(r):scopes[tuple(key)+(c,)].append(i)
        table[year]=scopes
    groups={};cache={};evaluation=[]
    for source_index,r in enumerate(rows):
        year=r['origin_year']
        if year not in YEARS or r['prior_current_MLB_fielding']:continue
        fold=r['player_id']%5
        for c,x,n in measurements(r):
            for scope in choices(r):
                ck=(year,fold,tuple(scope),c)
                if ck not in cache:
                    ids=[i for i in table[year].get(tuple(scope)+(c,),[]) if rows[i]['player_id']%5!=fold]
                    people=sorted({rows[i]['player_id'] for i in ids})
                    cache[ck]=(ids,people)
                ids,people=cache[ck]
                if len(people)>=30:break
            gid='g'+str(len(groups)).zfill(5) if ck not in groups else groups[ck]['group_id']
            if ck not in groups:
                assert ids and r['player_id'] not in people
                ns=[next(v for cc,xx,v in measurements(rows[i]) if cc==c) for i in ids]
                xs=[next(v for cc,v,nn in measurements(rows[i]) if cc==c) for i in ids]
                groups[ck]=dict(group_id=gid,origin_year=year,fold=fold,scope=scope,channel=c,source_row_indices=ids,
                    people=people,source_rows=len(ids),source_count=sum(xs),source_exposure=sum(ns),
                    source_exposure_min=min(ns),source_exposure_max=max(ns),positive_source_records=sum(v>0 for v in xs),
                    chronology_pass=all(year-2<=rows[i]['origin_year']<=year for i in ids),
                    held_person_pass=all(rows[i]['player_id']%5!=fold for i in ids))
            key=(year+1,r['player_id'],r['position'],r['level']);target=future.get(key)
            if target is None:tx=tn=None;status='no_recorded_same_level_position'
            else:
                _,tx,tn=next(t for t in measurements(target) if t[0]==c)
                status='observed_positive_exposure' if tn>0 else 'recorded_zero_exposure_unknown_quality'
            evaluation.append(dict(origin_year=year,player_id=r['player_id'],player_name=r['player_name'],position=r['position'],
                level=r['level'],age=r['age'],age_band=r['age_band'],fold=fold,channel=c,source_row_index=source_index,
                group_id=gid,current_count=x,current_exposure=n,current_band='<20' if n<20 else '20-99' if n<100 else '100+',
                target_count=tx,target_exposure=tn,target_status=status))
    identities=[(r['origin_year'],r['player_id'],r['position'],r['level'],r['channel']) for r in evaluation]
    assert len(identities)==len(set(identities))
    assert all(g['chronology_pass'] and g['held_person_pass'] for g in groups.values())
    write(PUBLIC/'source-levels.json.gz',rows)
    write(PUBLIC/'reference-groups.json.gz',list(groups.values()))
    write(PUBLIC/'evaluation.json.gz',evaluation)
    paths=[SOURCE/'counts.parquet',SOURCE/'origins.parquet',SOURCE/'final-review.json',Path(__file__),
           ROOT/'docs/defense-count-reliability-v20-contract.md',ROOT/'src/universal_baseball/minor_count_reliability.py',
           ROOT/'src/universal_baseball/minor_range_talent.py',ROOT/'tests/test_minor_count_reliability.py',
           PUBLIC/'source-levels.json.gz',PUBLIC/'reference-groups.json.gz',PUBLIC/'evaluation.json.gz']
    write(PUBLIC/'preflight.json.gz',dict(before_any_estimation=True,rows=len(evaluation),groups=len(groups),
        previous_goal_turn='No defense progress: read-only Lovich diagnosis confirmed the separate batting defect.',
        no_2026_outcomes=True,forecast_unchanged=True,source_eligibility_uses_no_future_counts=True,
        coverage=[dict(origin_year=y,rows=sum(r['origin_year']==y for r in evaluation),
                     people=len({r['player_id'] for r in evaluation if r['origin_year']==y}),
                     target_status=dict(Counter(r['target_status'] for r in evaluation if r['origin_year']==y))) for y in YEARS],
        mean_bounds_errors=[-20,20],mean_bounds_plays=[-20,5],strength_bounds=[.001,1e6],starts=[1,100,10000],
        hashes={str(p):sha256_file(p) for p in paths},player_walkthrough_status='pending'))
    print(dict(population=len(evaluation),reference_groups=len(groups),before_any_fit=True),flush=True)


def group_statistics(group,rows):
    by=defaultdict(list);c=group['channel']
    for i in group['source_row_indices']:
        r=rows[i];_,x,n=next(t for t in measurements(r) if t[0]==c)
        by[r['player_id']].append((x,n))
    rates=[];second=[];inverse=[];x=[];n=[]
    for pid,rs in sorted(by.items()):
        rates.append(np.mean([a/b for a,b in rs]));second.append(np.mean([(a/b)**2 for a,b in rs]))
        inverse.append(np.mean([1/b for a,b in rs]));x.append(sum(a for a,b in rs));n.append(sum(b for a,b in rs))
    baseline=moments(float(np.mean(rates)),float(np.mean(second)),float(np.mean(inverse)),len(by),c<2)
    return baseline,x,n


def score(rows):
    observed=[r for r in rows if r['target_status']=='observed_positive_exposure']
    if not observed:return dict(rows=len(rows),people=0,observed_rows=0)
    totals={}
    for arm in ('baseline','candidate'):
        by=defaultdict(list)
        for r in observed:by[r['player_id']].append(r)
        impossible=sum(r[f'{arm}_impossible'] for r in observed)
        def mean_of(function):return float(np.mean([np.mean([function(r) for r in rs]) for rs in by.values()]))
        finite=[r for r in observed if not r[f'{arm}_impossible']]
        fb=defaultdict(list)
        for r in finite:fb[r['player_id']].append(r[f'{arm}_loss'])
        totals[arm]=dict(impossible_rows=impossible,mean_nll=None if impossible else mean_of(lambda r:r[f'{arm}_loss']),
            headline_loss_infinite=bool(impossible),finite_only_nll=float(np.mean([np.mean(v) for v in fb.values()])) if fb else None,
            rate_rmse=math.sqrt(mean_of(lambda r:(r[f'{arm}_mean']-r['target_count']/r['target_exposure'])**2)),
            rate_bias=mean_of(lambda r:r[f'{arm}_mean']-r['target_count']/r['target_exposure']),
            coverage90=mean_of(lambda r:float(r[f'{arm}_covered'])),width90=mean_of(lambda r:r[f'{arm}_upper']-r[f'{arm}_lower']))
    paired=[r for r in observed if not r['baseline_impossible'] and not r['candidate_impossible']]
    by=defaultdict(list)
    for r in paired:by[r['player_id']].append(r)
    if by:
        a=np.array([np.mean([r['candidate_loss']-r['baseline_loss'] for r in rs]) for pid,rs in sorted(by.items())])
        rng=np.random.default_rng(20020);boot=np.array([a[rng.integers(0,len(a),len(a))].mean() for _ in range(2000)])
        delta=dict(people=len(by),rows=len(paired),mean_nll_delta=float(a.mean()),interval95=np.quantile(boot,[.025,.975]).tolist(),
                   baseline_nll=float(np.mean([np.mean([r['baseline_loss'] for r in rs]) for rs in by.values()])),
                   candidate_nll=float(np.mean([np.mean([r['candidate_loss'] for r in rs]) for rs in by.values()])),
                   conditional_on_both_losses_finite=len(paired)!=len(observed),seed=20020,replicates=2000)
    else:delta=None
    return dict(rows=len(rows),people=len(by),observed_rows=len(observed),observed_people=len({r['player_id'] for r in observed}),
                status=dict(Counter(r['target_status'] for r in rows)),arms=totals,paired=delta)


def fit_and_score():
    protections();pre=read(PUBLIC/'preflight.json.gz')
    for p,h in pre['hashes'].items():assert sha256_file(Path(p))==h,p
    assert not (PUBLIC/'summary.json.gz').exists(),'Completed test must not be rerun'
    rows=read(PUBLIC/'source-levels.json.gz');groups=read(PUBLIC/'reference-groups.json.gz')
    fitted={};prehash=sha256_file(PUBLIC/'preflight.json.gz')
    for i,g in enumerate(groups):
        path=PUBLIC/'fits'/f"{g['group_id']}.json.gz"
        if path.exists():
            note=read(path);assert note['preflight_hash']==prehash and note['group_id']==g['group_id']
        else:
            baseline,x,n=group_statistics(g,rows);candidate=fit_prior(x,n,g['channel']<2,baseline)
            note=dict(group_id=g['group_id'],preflight_hash=prehash,baseline=baseline,candidate=candidate)
            write(path,note)
        fitted[g['group_id']]=note
        if i%100==0:print(f'Reference distributions saved: {i+1}/{len(groups)}',flush=True)
    evaluation=read(PUBLIC/'evaluation.json.gz');predictions=[]
    for i,r in enumerate(evaluation):
        r=dict(r);note=fitted[r['group_id']]
        for arm in ('baseline','candidate'):
            post=posterior(r['current_count'],r['current_exposure'],note[arm],r['channel']<2)
            r.update({arm+'_'+k:v for k,v in post.items()})
            if r['target_status']=='observed_positive_exposure':
                out=predictive(r['target_count'],r['target_exposure'],post,r['channel']<2)
                r.update({arm+'_'+k:v for k,v in out.items()})
        predictions.append(r)
        if i%10000==0:print(f'Count predictions scored: {i+1}/{len(evaluation)}',flush=True)
    OUT.mkdir(parents=True,exist_ok=True)
    path=OUT/'predictions.parquet';assert not path.exists();pl.DataFrame(predictions,infer_schema_length=None).write_parquet(path)
    results={str(y):score([r for r in predictions if r['origin_year']==y]) for y in YEARS}
    buckets=[]
    for y in YEARS:
        rs=[r for r in predictions if r['origin_year']==y]
        for column in ('channel','level','age_band','current_band'):
            for value in sorted({r[column] for r in rs},key=str):
                buckets.append(dict(origin_year=y,column=column,value=value,score=score([r for r in rs if r[column]==value])))
    primary=results['2022'];failed=[]
    if primary['arms']['candidate']['impossible_rows']>primary['arms']['baseline']['impossible_rows']:failed.append('additional_impossible_observations')
    if primary['paired'] is None or primary['paired']['interval95'][1]>=0:failed.append('no_supported_primary_finite_loss_gain')
    for g in buckets:
        s=g['score']
        if g['origin_year']!=2022 or g['column'] not in ('channel','level') or s.get('observed_people',0)<100:continue
        a=s['arms']
        if s['paired'] and s['paired']['candidate_nll']>s['paired']['baseline_nll']*1.05:failed.append(f"loss_deterioration_{g['column']}_{g['value']}")
        if a['candidate']['coverage90']<.85:failed.append(f"undercoverage_{g['column']}_{g['value']}")
    write(PUBLIC/'summary.json.gz',dict(origins=results,groups=buckets,source_screen_failed_checks=failed,
        source_screen_pass=not failed,independent_review_pending=True,player_walkthrough_status='pending',deployment_approved=False,
        not_future_MLB_talent_validation=True,no_2026_outcomes=True,forecast_unchanged=True,
        fitted_reference_groups=len(groups),candidate_status=dict(Counter(n['candidate']['status'] for n in fitted.values())),
        candidate_boundary_groups=sum(n['candidate']['boundary'] for n in fitted.values()),
        hashes={str(p):sha256_file(p) for p in [path,PUBLIC/'preflight.json.gz',Path(__file__)]}))
    print(json.dumps(dict(origins=results,screen_failed_checks=failed),indent=2),flush=True)
    protections()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');parser.add_argument('--fit',action='store_true')
    args=parser.parse_args();assert args.prepare != args.fit,'Choose prepare OR fit'
    prepare() if args.prepare else fit_and_score()
