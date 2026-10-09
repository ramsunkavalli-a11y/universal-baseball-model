"""Explain saved component bias; no learner, replacement forecast or 2026 input."""
from collections import defaultdict
from pathlib import Path
import gzip
import json
import math

import numpy as np
import polars as pl

from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'reports/model-evidence/defense-component-bias-v27'
PATHS = dict(
    channels=ROOT/'reports/generated/defense-value-v12/channel-predictions.parquet',
    bridge=ROOT/'reports/generated/defense-transition-v10/predictions.parquet',
    values=ROOT/'reports/generated/defense-reference-history-v26/value-predictions.parquet',
    range=ROOT/'reports/generated/defense-native-range-v3/component-ledger.parquet',
    framing=ROOT/'reports/generated/catcher-native-opportunity-v3/modern/framing-annual.parquet',
)
FOCAL = ('range_3', 'framing')
FIXED = ((518692,'range_3'),(621566,'range_3'),(502671,'range_3'),
         (665489,'range_3'),(592663,'framing'),(575929,'framing'),
         (669221,'framing'),(595978,'framing'))


def read(path):
    with (gzip.open(path,'rt',encoding='utf8') if path.suffix=='.gz' else path.open(encoding='utf8')) as stream:
        return json.load(stream)


def write(path, value):
    assert not path.exists(), path
    with gzip.open(path,'wt',encoding='utf8') as stream:
        json.dump(value,stream,allow_nan=False,separators=(',',':'))


def equal(a,b):
    assert (a is None and b is None) or (a is not None and b is not None and math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-8)),(a,b)


def protected():
    protections()
    freeze=ROOT/'model_artifacts/hitter-selected-2026-frozen-2026-10-05'
    manifest=read(freeze/'freeze-manifest.json')
    entry=next(x for x in manifest['files'] if x['path']=='forecast.parquet')
    equal_hash=sha256_file(freeze/'forecast.parquet')
    assert equal_hash==entry['sha256']
    folder=ROOT/'reports/generated/hitter-final-2026-reviewed-explorer'
    ui=read(ROOT/'reports/model-evidence/hitter-final-2026/explorer-review.json')
    assert sha256_file(folder/'index.html')==ui['current_template_sha256']
    assert sha256_file(folder/'data.json')==ui['mobile_correction']['data_sha256']
    return {str(p):sha256_file(p) for p in [freeze/'forecast.parquet',folder/'index.html',folder/'data.json']}


def decompose(r):
    n=r['actual_native_opportunities']
    if r['actual_official_exposure']==0:n=0.
    oracle=None if n is None else r['history_rate']*n/r['rate_unit']
    equal(oracle,r['history_oracle_runs'])
    equal(r['repair_history'],r['repair_predicted_opportunities']*r['history_rate']/r['rate_unit'])
    measured=r['actual_runs'] is not None
    opportunity=None if oracle is None else r['repair_history']-oracle
    rate=None if oracle is None or not measured else oracle-r['actual_runs']
    if measured and oracle is not None:equal(r['repair_history']-r['actual_runs'],opportunity+rate)
    return dict(actual_opportunities=n,actual_opportunity_runs=oracle,
                opportunity_error=opportunity,rate_error=rate,
                total_error=None if not measured else r['repair_history']-r['actual_runs'])


def summary(rows):
    measured=[r for r in rows if r['actual_runs'] is not None]
    den=[r for r in measured if r['actual_opportunity_runs'] is not None]
    out=dict(rows=len(rows),measured=len(measured),unknown=len(rows)-len(measured),
        measured_actual_runs=sum(r['actual_runs'] for r in measured),
        measured_predicted_runs=sum(r['repair_history'] for r in measured),
        unknown_forecast_runs=sum(r['repair_history'] for r in rows if r['actual_runs'] is None),
        native_denominator_measured=len(den),native_denominator_missing=len(measured)-len(den),
        actual_official_exposure=sum(r['actual_official_exposure'] for r in rows),
        projected_native_opportunities=sum(r['repair_predicted_opportunities'] for r in rows),
        actual_native_opportunities=sum(r['actual_opportunities'] for r in den),
        decomposition_actual=sum(r['actual_runs'] for r in den),
        decomposition_forecast=sum(r['repair_history'] for r in den),
        decomposition_oracle=sum(r['actual_opportunity_runs'] for r in den),
        opportunity_error=sum(r['opportunity_error'] for r in den),
        rate_error=sum(r['rate_error'] for r in den))
    for name,field in [('forecast','repair_history'),('actual_opportunity','actual_opportunity_runs')]:
        e=np.array([r[field]-r['actual_runs'] for r in den])
        out[name+'_rmse']=None if not len(e) else float(np.sqrt(np.mean(e*e)))
        out[name+'_mae']=None if not len(e) else float(np.mean(abs(e)))
    equal(out['decomposition_forecast']-out['decomposition_actual'],out['opportunity_error']+out['rate_error'])
    return out


def native_rows(frames):
    sources=defaultdict(list)
    for channel in FOCAL:
        for r in frames['range' if channel=='range_3' else 'framing']:
            if channel=='range_3':
                if r['position']!=3 or not r['range_valid']:continue
                n=r['native_outs'];runs=r['range_runs']
            else:
                if not r['exposure_valid'] or not r['framing_measurement_valid']:continue
                n=r['pitches'];runs=r['framing_runs']
            assert n>0 and runs is not None and r['season']<=2025
            sources[channel].append(dict(**r,audit_opportunities=n,audit_runs=runs))
    return sources


def walk(r,bridge,sources,reference):
    y=r['origin_year'];pid=r['player_id'];ch=r['channel']
    past=[s for s in sources[ch] if s['player_id']==pid and y-2<=s['season']<=y]
    n=sum(s['audit_opportunities']*.5**(y-s['season']) for s in past)
    runs=sum(s['audit_runs']*.5**(y-s['season']) for s in past)
    prior=3000. if ch=='range_3' else 6000.
    unit=1500. if ch=='range_3' else 1000.
    equal(n,r['history_opportunities']);equal(n/(n+prior),r['reliability'])
    equal(unit*runs/(n+prior),r['history_rate'])
    assert r['quality_evidence_observed']==(n>0)
    target=[s for s in sources[ch] if s['player_id']==pid and s['season']==r['target_year']]
    if r['actual_official_exposure']>0 and r['actual_runs'] is not None:
        assert len(target)==1
        equal(target[0]['audit_runs'],r['actual_runs']);equal(target[0]['audit_opportunities'],r['actual_native_opportunities'])
    return dict(row_id=r['row_id'],player_id=pid,player_name=r['player_name'],origin_year=y,
        target_year=r['target_year'],channel=ch,age=r['age'],stage=r['stage'],outer_fold=r['outer_fold'],
        origin_role=bridge['repertoire_primary_role'],origin_exposure=bridge['role_defensive_sample'],
        source_history=sorted(past,key=lambda s:s['season']),target_source=target,
        weighted_runs=runs,weighted_opportunities=n,prior_opportunities=prior,unit=unit,
        reliability=r['reliability'],history_rate=r['history_rate'],quality_evidence_observed=n>0,
        origin_held_person_reference=reference[y,pid%5,ch],
        forecast_opportunities=r['repair_predicted_opportunities'],forecast_runs=r['repair_history'],
        actual_official_exposure=r['actual_official_exposure'],actual_runs=r['actual_runs'],
        target_status=r['target_status'],**decompose(r))


def main():
    assert not (PUBLIC/'preflight.json.gz').exists()
    locks=protected();PUBLIC.mkdir(parents=True,exist_ok=True)
    paths=[Path(__file__),ROOT/'docs/defense-component-bias-v27-contract.md',*PATHS.values(),
           ROOT/'src/universal_baseball/defense_native_range.py',ROOT/'src/universal_baseball/catcher_framing_baseline.py',
           ROOT/'src/universal_baseball/defense_opportunity_bridge.py']
    frames={k:pl.read_parquet(p).to_dicts() for k,p in PATHS.items()}
    assert len(frames['channels'])==149184 and len(frames['bridge'])==12432
    bridge={r['row_id']:r for r in frames['bridge']};assert len(bridge)==12432
    complete={r['row_id'] for r in frames['values'] if r['actual_defense'] is not None}
    assert set(bridge)=={r['row_id'] for r in frames['values']}
    assert all(r['target_year']<=2025 and r['target_year']==r['origin_year']+1 for r in frames['channels'])
    write(PUBLIC/'preflight.json.gz',dict(fits=0,inputs_locked_before_scoring=True,protected_hashes=locks,
        channel_rows=len(frames['channels']),forecast_rows=len(bridge),complete_rows=len(complete),
        source_hashes={str(p):sha256_file(p) for p in paths},fixed_cases=FIXED,
        previous_goal_turn='No defense progress: read-only Lovich explanation confirmed the separate batting defect.'))
    groups=defaultdict(list);by={}
    for raw in frames['channels']:
        r=dict(**raw,**decompose(raw));by[r['row_id'],r['channel']]=r
        groups[r['origin_year'],r['channel'],'all'].append(r)
        if r['row_id'] in complete:groups[r['origin_year'],r['channel'],'complete'].append(r)
        if r['actual_official_exposure']>0:groups[r['origin_year'],r['channel'],'actual_defenders'].append(r)
        if r['channel'] in FOCAL:
            groups[r['origin_year'],r['channel'],'measured_history' if r['quality_evidence_observed'] else 'unknown_history'].append(r)
    stats=[dict(origin=y,channel=c,scope=s,**summary(rs)) for (y,c,s),rs in sorted(groups.items())]
    sources=native_rows(frames);annual=[];references={}
    for ch,ss in sources.items():
        unit=1500. if ch=='range_3' else 1000.
        for y in sorted({s['season'] for s in ss}):
            parts=[s for s in ss if s['season']==y];n=sum(s['audit_opportunities'] for s in parts);runs=sum(s['audit_runs'] for s in parts)
            annual.append(dict(season=y,channel=ch,people=len(parts),opportunities=n,runs=runs,rate=unit*runs/n))
        for y in (2022,2023,2024):
            for fold in range(5):
                parts=[s for s in ss if y-2<=s['season']<=y and s['player_id']%5!=fold]
                n=sum(s['audit_opportunities']*.5**(y-s['season']) for s in parts)
                runs=sum(s['audit_runs']*.5**(y-s['season']) for s in parts)
                references[y,fold,ch]=dict(origin_year=y,excluded_fold=fold,fold_rule='player_id modulo five',
                    people=len({s['player_id'] for s in parts}),max_source_year=max(s['season'] for s in parts),
                    opportunities=n,runs=runs,rate=unit*runs/n,descriptive_not_replacement_prior=True)
    selections=[]
    for pid,ch in FIXED:
        rs=[r for r in by.values() if r['player_id']==pid and r['origin_year']==2022 and r['channel']==ch]
        assert len(rs)==1;selections.append(('fixed',rs[0]))
    for ch in FOCAL:
        rs=[r for r in by.values() if r['channel']==ch and r['actual_official_exposure']>0 and r['actual_runs'] is not None]
        selections.extend([('largest_positive_error',max(rs,key=lambda r:(r['total_error'],-r['row_id']))),
                           ('largest_negative_error',min(rs,key=lambda r:(r['total_error'],r['row_id'])))])
        ordered=sorted(rs,key=lambda r:(abs(r['total_error']),r['row_id']))
        selections.append(('ordinary_median_absolute_error',ordered[len(ordered)//2]))
    walks=[]
    for label,r in selections:
        focal=bridge[r['row_id']]
        pool=[p for p in bridge.values() if p['origin_year']==r['origin_year'] and p['stage']==focal['stage']
              and p['repertoire_primary_role']==focal['repertoire_primary_role'] and p['player_id']!=r['player_id']]
        peers=sorted(pool,key=lambda p:(abs((p['age'] if p['age'] is not None else 27)-(focal['age'] if focal['age'] is not None else 27)),
            abs(p['role_defensive_sample']-focal['role_defensive_sample']),p['row_id']))[:3]
        records=[walk(by[p['row_id'],r['channel']],p,sources,references) for p in [focal,*peers]]
        walks.append(dict(selection=label,focal_player_id=r['player_id'],channel=r['channel'],
            origin_year=r['origin_year'],comparison_rule='Same origin/stage/primary role; nearest age then exposure then row ID, no outcomes.',records=records))
    write(PUBLIC/'report.json.gz',dict(fits=0,predictions_changed=False,target_membership_unchanged=True,
        scopes=stats,qualified_native_annual=annual,held_player_references=list(references.values()),
        accounting_identity_verified_rows=sum(r['actual_runs'] is not None and r['actual_opportunity_runs'] is not None for r in by.values()),
        player_walkthrough_status='pending_readable_interpretation',
        claim_limit='Descriptive annual delivered-run decomposition; not future-MLB talent validation, a new prior, full WAR or a causal exposure effect.'))
    write(PUBLIC/'player-walks.json.gz',dict(groups=walks,source_rate_replays=len(walks)*4))
    assert locks==protected()
    for s in stats:
        if s['channel'] in FOCAL and s['scope']=='complete':
            print(json.dumps(s))
    print(json.dumps(dict(native_annual=annual,player_groups=len(walks))))


if __name__=='__main__':main()
