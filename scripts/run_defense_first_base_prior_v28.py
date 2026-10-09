"""Locked talent prior, fixed value consequences and source-to-outcome walks."""
from collections import defaultdict
from pathlib import Path
import gzip
import json
import math
import numpy as np
import polars as pl
from universal_baseball.defense_first_base_prior import reference, estimate
from universal_baseball.defense_value import score_rows, paired_interval
from universal_baseball.storage import sha256_file
from reconstruct_defense_value_v26 import reconstruct
from audit_defense_component_bias_v27 import protected

ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/'reports/model-evidence/defense-first-base-prior-v28'
NATIVE=ROOT/'reports/generated/defense-native-range-v3'
V12=ROOT/'reports/generated/defense-value-v12'
OFFICIAL=ROOT/'reports/generated/defense-position-opportunity-v7/source.parquet'
BRIDGE=ROOT/'reports/generated/defense-transition-v10/predictions.parquet'
SEED=728028
ARMS=('zero','history','calibrated','candidate')


def read(p):
    with gzip.open(p,'rt',encoding='utf8') as f:return json.load(f)


def write(name,note):
    p=PUBLIC/(name+'.json.gz');assert not p.exists(),p
    with gzip.open(p,'wt',encoding='utf8') as f:json.dump(note,f,allow_nan=False,separators=(',',':'))


def close(a,b):
    assert (a is None and b is None) or (a is not None and b is not None and math.isclose(a,b,abs_tol=1e-8,rel_tol=1e-10)),(a,b)


def quality_scores(rows):
    measured=[r for r in rows if r['quality_rate'] is not None]
    if not measured:return None
    groups=defaultdict(list)
    for r in measured:groups[r['player_id']].append(r)
    loss=np.array([[np.mean([(r[a]-r['quality_rate'])**2 for r in rs]) for a in ARMS] for rs in groups.values()])
    scores=[]
    for i,a in enumerate(ARMS):
        scores.append(dict(arm=a,people=len(groups),rows=len(measured),rmse=float(np.sqrt(loss[:,i].mean())),
            mae=float(np.mean([np.mean([abs(r[a]-r['quality_rate']) for r in rs]) for rs in groups.values()])),
            bias=float(np.mean([np.mean([r[a]-r['quality_rate'] for r in rs]) for rs in groups.values()]))))
    rng=np.random.default_rng(SEED);diffs=[]
    for _ in range(2000):
        roots=np.sqrt(loss[rng.integers(len(groups),size=len(groups))].mean(axis=0))
        diffs.append([float(roots[3]-roots[i]) for i in range(3)])
    base=np.sqrt(loss.mean(axis=0));intervals=[]
    for i,a in enumerate(ARMS[:3]):
        intervals.append(dict(left='candidate',right=a,difference=float(base[3]-base[i]),
            interval_95=np.quantile(np.array(diffs)[:,i],[.025,.975]).tolist(),draws=2000,seed=SEED))
    return dict(scores=scores,intervals=intervals)


def main():
    assert not (PUBLIC/'preflight.json.gz').exists()
    locks=protected();PUBLIC.mkdir(parents=True,exist_ok=True)
    # Previous diagnostic has completed its source and all 56 player reviews.
    prev=ROOT/'reports/model-evidence/defense-component-bias-v27'
    check=read(prev/'independent-review.json.gz');assert check['execution_integrity_pass'] and check['player_records_replayed']==56
    assert read(prev/'player-value-context.json.gz')['records']==56
    values,recovery=reconstruct()
    native=pl.read_parquet(NATIVE/'component-ledger.parquet').filter(pl.col('position')==3).to_dicts()
    people=defaultdict(list)
    for r in native:people[r['player_id']].append(r)
    old=pl.read_parquet(NATIVE/'predictions.parquet').filter(pl.col('position')==3).to_dicts()
    refs={(y,f):reference(native,y,f) for y in sorted({r['origin_year'] for r in old}|{2022,2023,2024}) for f in range(5)}
    official=defaultdict(int)
    for r in pl.read_parquet(OFFICIAL,columns=['is_mlb','position_code','season','player_id','fielding_outs']).filter(
            pl.col('is_mlb') & (pl.col('position_code')=='3')).iter_rows(named=True):official[r['season'],r['player_id']]+=r['fielding_outs']
    q=[]
    for r in old:
        y,pid=r['origin_year'],r['player_id']
        past=[s for s in people[pid] if y-2<=s['season']<=y and s['range_valid']]
        n=sum(s['native_outs']*2.**(s['season']-y) for s in past)
        v=sum(s['range_runs']*2.**(s['season']-y) for s in past)
        close(n,r['history_outs']);close(v,r['history_runs']);close(1500*v/(n+3000),r['history'])
        future=[s for s in people[pid] if y<s['season']<=min(y+3,2025) and s['range_valid']]
        fn=sum(s['native_outs'] for s in future);fr=sum(s['range_runs'] for s in future)
        missing=sum(official[year,pid] for year in range(y+1,min(y+3,2025)+1) if not any(s['season']==year for s in future))
        valid=y+3<=2025 and fn>=1500 and len(future)>=2 and missing==0
        assert valid==(r['quality_rate'] is not None)
        close(fn,r['future_outs']);close(fr,r['future_runs']);close(missing,r['unmeasured_official_outs'])
        if valid:close(1500*fr/fn,r['quality_rate'])
        q.append(dict(**r,zero=0.,candidate=estimate(v,n,refs[y,pid%5]['rate']),
            prior_rate=refs[y,pid%5]['rate'],prior_supported=refs[y,pid%5]['supported'],
            age_band='unknown' if r['age'] is None else 'young' if r['age']<=24 else 'prime' if r['age']<=30 else 'older',
            exposure_band='tiny' if n<1500 else 'medium' if n<4500 else 'large'))
    columns=['row_id','player_id','player_name','origin_year','target_year','stage','age','history_rate','history_opportunities',
             'rate_unit','repair_predicted_opportunities','repair_history','actual_native_opportunities','actual_official_exposure',
             'actual_runs','target_status','quality_evidence_observed']
    cs=pl.read_parquet(V12/'channel-predictions.parquet',columns=['channel',*columns]).filter(pl.col('channel')=='range_3').to_dicts()
    cb={};vb={r['row_id']:r for r in values}
    for c in cs:
        y,pid=c['origin_year'],c['player_id'];past=[s for s in people[pid] if y-2<=s['season']<=y and s['range_valid']]
        n=sum(s['native_outs']*2.**(s['season']-y) for s in past);v=sum(s['range_runs']*2.**(s['season']-y) for s in past)
        close(n,c['history_opportunities']);close(1500*v/(n+3000),c['history_rate']);assert c['quality_evidence_observed']==(n>0)
        prior=refs[y,pid%5]['rate'];rate=estimate(v,n,prior)
        runs=c['repair_predicted_opportunities']*rate/1500;delta=runs-c['repair_history']
        actual_n=0 if c['actual_official_exposure']==0 else c['actual_native_opportunities']
        oracle=None if actual_n is None else actual_n*rate/1500
        oldoracle=None if actual_n is None else actual_n*c['history_rate']/1500
        cb[c['row_id']]=dict(**c,weighted_runs=v,prior_rate=prior,candidate_rate=rate,candidate_runs=runs,
            history_oracle=oldoracle,candidate_oracle=oracle,talent_known=n>0,delta=delta)
        r=vb[c['row_id']]
        r.update(history_1b=c['repair_history'],candidate_1b=runs,actual_1b=c['actual_runs'],
            history_1b_oracle=oldoracle,candidate_1b_oracle=oracle,actual_1b_official=c['actual_official_exposure'],
            candidate_defense=r['centered_defense']+delta,candidate_expanded=r['centered_expanded']+delta/10)
    assert len(cb)==len(vb)==12432
    paths=[Path(__file__),ROOT/'scripts/reconstruct_defense_value_v26.py',ROOT/'src/universal_baseball/defense_first_base_prior.py',
           ROOT/'docs/defense-first-base-prior-v28-contract.md',ROOT/'docs/hitter-stopping-point-execution.md',
           NATIVE/'component-ledger.parquet',NATIVE/'predictions.parquet',V12/'predictions.parquet',V12/'channel-predictions.parquet',
           OFFICIAL,BRIDGE,prev/'independent-review.json.gz',prev/'player-value-context.json.gz']
    coverage=defaultdict(int)
    for r in q:coverage[r['origin_year'],r['quality_status']]+=1
    write('preflight',dict(before_scoring=True,model_fits=0,protected_hashes=locks,reconstruction=recovery,
        hashes={str(p):sha256_file(p) for p in paths},references=list(refs.values()),quality_rows=len(q),value_rows=len(values),
        coverage=[dict(origin=k[0],status=k[1],rows=v) for k,v in sorted(coverage.items())],
        missing_quality_is_unknown=True,unchanged_quality_membership=True,
        support_kind='Contemporaneous held-fold empirical position mean, not a future-label fitted learner; saved age-fit support flags retained.',
        quality_support=[dict(origin=y,rows=sum(r['origin_year']==y for r in q),measured=sum(r['origin_year']==y and r['quality_rate'] is not None for r in q),
            people=len({r['player_id'] for r in q if r['origin_year']==y and r['quality_rate'] is not None}),
            reference_fallbacks=sum(r['origin_year']==y and not r['prior_supported'] for r in q)) for y in sorted({r['origin_year'] for r in q})]))
    write('quality-predictions',dict(rows=q))
    primary=[r for r in q if r['origin_year']==2022];quality_groups=[]
    for y in sorted({r['origin_year'] for r in q if r['window_mature']}):
        quality_groups.append(dict(origin=y,scope='all',result=quality_scores([r for r in q if r['origin_year']==y])))
    for key in ('age_band','exposure_band'):
        for val in sorted({r[key] for r in primary}):
            quality_groups.append(dict(origin=2022,scope=key,group=val,result=quality_scores([r for r in primary if r[key]==val])))
    score={}
    for target,left,right,truth in [('first_base','candidate_1b','history_1b','actual_1b'),
                                  ('defense','candidate_defense','centered_defense','actual_defense'),
                                  ('expanded','candidate_expanded','centered_expanded','actual_expanded')]:
        score[target]=score_rows(values,[right,left],truth)
        score[target]['interval']=paired_interval(values,left,right,truth,draws=2000,seed=SEED)
    defenders=[r for r in values if r['actual_1b_official']>0]
    stage=[]
    for st in sorted({r['stage'] for r in values}):
        rs=[r for r in values if r['stage']==st]
        stage.append(dict(stage=st,rows=len(rs),defense=score_rows(rs,['centered_defense','candidate_defense'],'actual_defense'),
                          expanded=score_rows(rs,['centered_expanded','candidate_expanded'],'actual_expanded')))
    report=dict(model_fits=0,primary=quality_scores(primary),quality_groups=quality_groups,value=score,stage=stage,
        first_base_defenders=score_rows(defenders,['history_1b','candidate_1b','history_1b_oracle','candidate_1b_oracle'],'actual_1b'),
        unknown_value_rows=sum(r['actual_defense'] is None for r in values),unchanged_quality_membership=True,
        uncertainty_limit='Exposed development data; player intervals condition on reference estimation, outcome measurement selection and shared seasons.',
        player_walkthrough_status='pending',deployment_approved=False,no_2026_access=True)
    write('report',report)
    # Fixed cases plus primary error-based cases; peers use only origin role/age/exposure.
    fixed=[(518692,2022),(621566,2022),(502671,2022),(665489,2022),(467793,2023)]
    v27=read(prev/'player-walks.json.gz')
    wilson=next(g['focal_player_id'] for g in v27['groups'] if g['channel']=='range_3' and 'Wilson' in g['records'][0]['player_name'])
    fixed.append((wilson,2022))
    selections=[dict(kind='fixed',player_id=p,origin=y) for p,y in fixed]
    measured=[r for r in primary if r['quality_rate'] is not None]
    improvement=lambda r:(r['candidate']-r['quality_rate'])**2-(r['history']-r['quality_rate'])**2
    ranked=sorted(measured,key=lambda r:(abs(r['candidate']-r['quality_rate']),r['player_id']))
    chosen=[('largest_gain',min(measured,key=improvement)),('largest_deterioration',max(measured,key=improvement)),
            ('false_high',max(measured,key=lambda r:r['candidate']-r['quality_rate'])),
            ('false_low',min(measured,key=lambda r:r['candidate']-r['quality_rate'])),('median_error',ranked[len(ranked)//2])]
    selections.extend(dict(kind=k,player_id=r['player_id'],origin=2022) for k,r in chosen)
    bridges=pl.read_parquet(BRIDGE,columns=['row_id','player_id','origin_year','stage','age','repertoire_primary_role','role_defensive_sample']).to_dicts()
    bby={(r['origin_year'],r['player_id']):r for r in bridges};qby={(r['origin_year'],r['player_id']):r for r in q}
    def walk(b):
        y,p=b['origin_year'],b['player_id'];c=cb[b['row_id']];v=vb[b['row_id']]
        return dict(player_name=v['player_name'],player_id=p,origin=y,role=b['repertoire_primary_role'],role_exposure=b['role_defensive_sample'],
            age=b['age'],stage=b['stage'],history=[s for s in people[p] if y-2<=s['season']<=y],
            future_measurements=[s for s in people[p] if y<s['season']<=min(y+3,2025)],
            future_official=[dict(season=z,outs=official[z,p]) for z in range(y+1,min(y+3,2025)+1)],
            empirical_prior=refs[y,p%5],quality=qby.get((y,p)),first_base=c,value=v)
    walks=[]
    for s in selections:
        b=bby[s['origin'],s['player_id']]
        pool=[r for r in bridges if r['origin_year']==b['origin_year'] and r['stage']==b['stage']
              and r['repertoire_primary_role']==b['repertoire_primary_role'] and r['player_id']!=b['player_id']]
        peers=sorted(pool,key=lambda r:(abs((r['age'] if r['age'] is not None else 27)-(b['age'] if b['age'] is not None else 27)),
            abs(r['role_defensive_sample']-b['role_defensive_sample']),r['row_id']))[:3]
        walks.append(dict(selection=s,peer_rule='Same origin/stage/primary role; closest age then exposure then row ID; no outcomes.',records=[walk(r) for r in [b,*peers]]))
    write('player-walks',dict(groups=walks,player_walkthrough_status='pending_readable_review'))
    # Compact unchanged-baseline and delta ledger; sufficient for independent scores.
    write('value-predictions',dict(rows=values))
    assert protected()==locks
    print(json.dumps(dict(primary=report['primary'],value_equal_origin={k:v['equal_origin'] for k,v in score.items()},groups=len(walks))))


if __name__=='__main__':main()
