"""Fixed prior-coordinate repair; talent and delivery remain separate gates."""
from collections import defaultdict
from pathlib import Path
import argparse
import gzip
import json
import math
import numpy as np
import polars as pl
from universal_baseball.defense_reference_history import annual_references,history,origin_reference
from universal_baseball.defense_value import score_rows,paired_interval
from universal_baseball.storage import sha256_file
from verify_double_play_support_v22 import write
from run_hitter_finite_return_baseline import protections

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/generated/defense-reference-history-v26'
PUBLIC=ROOT/'reports/model-evidence/defense-reference-history-v26'
NATIVE=ROOT/'reports/generated/defense-native-range-v3'
V12=ROOT/'reports/generated/defense-value-v12'
V25=ROOT/'reports/model-evidence/defense-reference-v25/fold-repair'
OFFICIAL=ROOT/'reports/generated/defense-position-opportunity-v7/source.parquet'
BRIDGE=ROOT/'reports/generated/defense-transition-v10/predictions.parquet'
ARMS=('legacy','centered','neutral')
SEED=726026


def read(p):
    with (gzip.open(p,'rt',encoding='utf8') if p.suffix=='.gz' else p.open(encoding='utf8')) as f:return json.load(f)


def verify(note):
    for p,h in {**note.get('hashes',{}),**note.get('output_hashes',{})}.items():assert sha256_file(Path(p))==h,p


def close(a,b):
    assert (a is None and b is None) or (a is not None and b is not None and math.isclose(a,b,abs_tol=1e-8,rel_tol=0)),(a,b)


def sources():
    native=pl.read_parquet(NATIVE/'component-ledger.parquet').to_dicts();people=defaultdict(list)
    for r in native:people[r['player_id']].append(r)
    refs=annual_references(native);measured={}
    for y in range(2016,2026):
        for p in (7,8,9):
            rows=[r for r in native if r['season']==y and r['position']==p and r['range_valid']]
            measured[y,p]=1500*sum(r['range_runs'] for r in rows)/sum(r['native_outs'] for r in rows)
    official=defaultdict(int)
    for r in pl.read_parquet(OFFICIAL).iter_rows(named=True):
        if r['is_mlb'] and r['position_code'].isdigit():official[r['season'],r['player_id'],int(r['position_code'])]+=r['fielding_outs']
    return native,people,refs,measured,official


def prepare():
    protections();assert not (PUBLIC/'preflight.json.gz').exists()
    assert (OUT.parent).exists();OUT.mkdir(exist_ok=True);PUBLIC.mkdir(exist_ok=True)
    for path in [V25/'final-review.json.gz',V12/'final-review.json',NATIVE/'final-review.json']:
        receipt=read(path);assert receipt['player_walkthrough_status']=='complete';verify(receipt)
    native,people,refs,measured,official=sources()
    old=pl.read_parquet(NATIVE/'predictions.parquet').to_dicts();predictions=[]
    for r in old:
        y,pid,p=r['origin_year'],r['player_id'],r['position'];rows=people[pid];fold=pid%5
        h=history(rows,y,p,fold,refs);ref=origin_reference(y,p,fold,refs)
        close(h['history_outs'],r['history_outs']);close(h['weighted_raw_runs'],r['history_runs']);close(h['legacy_raw'],r['history_rate'])
        assert sum(s['native_outs'] for s in rows if y-2<=s['season']<=y and s['position']==p and s['range_valid'])>=25
        future=[s for s in rows if y<s['season']<=min(y+3,2025) and s['position']==p and s['range_valid']]
        n=sum(s['native_outs'] for s in future);raw=sum(s['range_runs'] for s in future)
        missing=sum(official[year,pid,p] for year in range(y+1,min(y+3,2025)+1) if not any(s['season']==year for s in future))
        valid=y+3<=2025 and n>=1500 and len(future)>=2 and missing==0
        assert valid==(r['quality_rate'] is not None)
        close(n,r['future_outs']);close(raw,r['future_runs']);close(missing,r['unmeasured_official_outs'])
        other=sum(official[year,pid,pos] for year in range(y+1,min(y+3,2025)+1) for pos in range(2,10) if pos!=p)
        close(other,r['future_other_position_outs'])
        target_runs=sum(s['range_runs']-(measured[s['season'],p]*s['native_outs']/1500 if p in (7,8,9) else 0) for s in future)
        target=1500*target_runs/n if valid else None
        predictions.append(dict(origin_year=y,player_id=pid,player_name=r['player_name'],position=p,age=r['age'],fold=fold,
            history_outs=h['history_outs'],history_raw_runs=h['weighted_raw_runs'],history_relative_runs=h['weighted_relative_runs'],
            reliability=h['reliability'],talent_known=h['talent_known'],origin_reference=ref,
            legacy_intrinsic=r['history'],legacy=r['history']-ref,centered=h['centered'],neutral=0.,
            centered_intrinsic=h['centered']+ref,quality_rate=target,quality_status=r['quality_status'],
            original_quality_rate=r['quality_rate'],future_outs=n,future_raw_runs=raw,future_relative_runs=target_runs,
            future_seasons=len(future),future_missing_outs=missing,future_other_position_outs=other,
            window_end=y+3,window_mature=y+3<=2025,
            age_band='unknown' if r['age'] is None else 'young' if r['age']<=24 else 'prime' if r['age']<=30 else 'older',
            sample_band='tiny' if h['history_outs']<1500 else 'medium' if h['history_outs']<4500 else 'large'))
    assert len(predictions)==13402
    q=pl.DataFrame(predictions);q.write_parquet(OUT/'quality-predictions.parquet')
    f=pl.read_parquet(V12/'predictions.parquet');bridge={r['row_id']:r for r in pl.read_parquet(BRIDGE).to_dicts()}
    cells=defaultdict(list)
    for c in pl.read_parquet(V12/'channel-predictions.parquet').to_dicts():cells[c['row_id']].append(c)
    values=[];updated_channels=[]
    for r in f.to_dicts():
        y,pid=r['origin_year'],r['player_id'];b=bridge[r['row_id']];cs=cells[r['row_id']]
        old_OF=sum(c['repair_history'] for c in cs if c['channel'] in ('range_7','range_8','range_9'))
        new_OF=offset=0.;observed_offset=0.;unknown=False
        for c in cs:
            if c['channel'] not in ('range_7','range_8','range_9'):continue
            p=int(c['channel'][-1]);h=history(people[pid],y,p,pid%5,refs);ref=origin_reference(y,p,pid%5,refs)
            close(h['legacy_raw'],c['history_rate'])
            n=b[f'repair_{p}'];assert n>=0
            legacy_runs=c['repair_history']-n*ref/1500;new_runs=n*h['centered']/1500
            offset+=n*ref/1500;new_OF+=new_runs
            source=next((s for s in people[pid] if s['season']==y+1 and s['position']==p),None)
            if c['actual_official_exposure']==0:aoff=0.
            elif c['actual_runs'] is None:aoff=None;unknown=True
            else:
                assert source is not None and source['range_valid'];close(c['actual_runs'],source['range_runs'])
                aoff=measured[y+1,p]*source['native_outs']/1500
            if aoff is not None:observed_offset+=aoff
            updated_channels.append(dict(row_id=r['row_id'],origin_year=y,player_id=pid,position=p,
                projected_outs=n,actual_official_outs=c['actual_official_exposure'],
                actual_native_outs=source['native_outs'] if source is not None and c['actual_runs'] is not None else None,
                history_outs=h['history_outs'],history_raw_runs=h['weighted_raw_runs'],history_relative_runs=h['weighted_relative_runs'],
                reliability=h['reliability'],talent_known=h['talent_known'],origin_reference=ref,
                legacy_rate=c['history_rate']-ref,centered_rate=h['centered'],neutral_rate=0.,
                legacy_intrinsic_rate=c['history_rate'],centered_intrinsic_rate=h['centered']+ref,
                legacy_runs=legacy_runs,centered_runs=new_runs,neutral_runs=0.,
                actual_raw_runs=c['actual_runs'],actual_reference_offset=aoff,
                actual_relative_runs=None if aoff is None else c['actual_runs']-aoff))
        outside=r['repair_history_defense']-old_OF
        complete=r['actual_defense'] is not None;assert not complete or not unknown
        actual=None if not complete else r['actual_defense']-observed_offset
        rec=dict(row_id=r['row_id'],player_id=pid,player_name=r['player_name'],origin_year=y,stage=r['stage'],age=r['age'],
            expected_PA=r['expected_PA'],actual_PA=r['actual_PA'],actual_fielding_outs=r['actual_fielding_outs'],
            position_runs=r['repair_position_runs'],actual_position_runs=r['actual_position_runs'],
            batting_forecast=r['batting_forecast'],actual_batting=r['actual_batting'],non_OF_history_runs=outside,
            legacy_defense=r['repair_history_defense']-offset,centered_defense=outside+new_OF,neutral_defense=outside,
            actual_defense=actual,actual_expanded=None if actual is None else r['actual_batting']+(actual+r['actual_position_runs'])/10,
            original_defense=r['repair_history_defense'],original_expanded=r['repair_history_expanded'],
            projected_reference_offset=offset,observed_reference_offset=None if unknown else observed_offset,
            unknown_target_channels=r['unknown_target_channels'])
        for a in ARMS:rec[a+'_expanded']=r['batting_forecast']+(r['repair_position_runs']+rec[a+'_defense'])/10
        values.append(rec)
    assert len(values)==12432 and len(updated_channels)==37296
    pl.DataFrame(values).write_parquet(OUT/'value-predictions.parquet')
    pl.DataFrame(updated_channels).write_parquet(OUT/'OF-predictions.parquet')
    supports=[]
    for y in (2021,2022):
        for fold in range(5):
            tr=[r for r in predictions if r['quality_rate'] is not None and r['window_end']<=y and r['player_id']%5!=fold]
            te=[r for r in predictions if r['origin_year']==y and r['fold']==fold]
            assert {r['player_id'] for r in tr}.isdisjoint(r['player_id'] for r in te)
            for p in range(3,10):
                for age in ('unknown','young','prime','older'):
                    for size in ('tiny','medium','large'):
                        ts=[r for r in tr if (r['position'],r['age_band'],r['sample_band'])==(p,age,size)]
                        es=[r for r in te if (r['position'],r['age_band'],r['sample_band'])==(p,age,size)]
                        if ts or es:supports.append(dict(origin=y,fold=fold,position=p,age=age,sample=size,
                            mature_training_people=len({r['player_id'] for r in ts}),eligible_test_people=len({r['player_id'] for r in es}),
                            qualification='Support for a possible future learner, not a fit or empirical justification of the fixed prior.'))
    coverage=q.group_by(['origin_year','position','age_band','sample_band','quality_status']).agg(pl.len().alias('rows'),pl.col('player_id').n_unique().alias('people')).sort(['origin_year','position','age_band','sample_band','quality_status']).to_dicts()
    paths=[Path(__file__),ROOT/'src/universal_baseball/defense_reference_history.py',ROOT/'docs/defense-reference-history-v26-contract.md',
        NATIVE/'component-ledger.parquet',NATIVE/'predictions.parquet',NATIVE/'final-review.json',OFFICIAL,BRIDGE,
        V12/'predictions.parquet',V12/'channel-predictions.parquet',V12/'final-review.json',V25/'final-review.json.gz',V25/'player-walks.json.gz']
    write(PUBLIC/'preflight.json.gz',dict(model_fits=0,before_scoring=True,quality_rows=13402,value_rows=12432,
        annual_held_references=[dict(season=k[0],position=k[1],fold=k[2],**v) for k,v in sorted(refs.items())],
        realized_target_references=[dict(season=k[0],position=k[1],rate=v) for k,v in sorted(measured.items())],
        mature_profile_support=supports,coverage=coverage,all_fixed_identities_retained=True,player_walkthrough_status='pending',
        frozen_and_explorer_unchanged=True,no_2026_selection=True,
        hashes={str(p):sha256_file(p) for p in paths},output_hashes={str(OUT/n):sha256_file(OUT/n) for n in ['quality-predictions.parquet','value-predictions.parquet','OF-predictions.parquet']}))
    protections();print('Fixed centered-before-shrinkage predictions and source/support preflight saved; no score yet.',flush=True)


def quality_scores(rows):
    selected=[r for r in rows if r['quality_rate'] is not None]
    if not selected:return None
    groups=defaultdict(list)
    for r in selected:groups[r['player_id']].append(r)
    result=[]
    for a in ARMS:
        mse=[np.mean([(r[a]-r['quality_rate'])**2 for r in g]) for g in groups.values()]
        mae=[np.mean([abs(r[a]-r['quality_rate']) for r in g]) for g in groups.values()]
        bias=[np.mean([r[a]-r['quality_rate'] for r in g]) for g in groups.values()]
        result.append(dict(arm=a,rows=len(selected),people=len(groups),rmse=float(np.sqrt(np.mean(mse))),mae=float(np.mean(mae)),bias=float(np.mean(bias))))
    intervals=[]
    for right in ('legacy','neutral'):
        loss=np.array([[np.mean([(r[a]-r['quality_rate'])**2 for r in g]) for a in ('centered',right)] for g in groups.values()])
        rng=np.random.default_rng(SEED);ds=[]
        for _ in range(2000):
            sample=loss[rng.integers(len(loss),size=len(loss))]
            roots=np.sqrt(sample.mean(axis=0));ds.append(float(roots[0]-roots[1]))
        intervals.append(dict(left='centered',right=right,people=len(groups),draws=2000,seed=SEED,
            difference=float(np.sqrt(loss.mean(axis=0))[0]-np.sqrt(loss.mean(axis=0))[1]),interval_95=np.quantile(ds,[.025,.975]).tolist()))
    return dict(scores=result,intervals=intervals)


def score():
    protections();assert not (PUBLIC/'report.json.gz').exists();pre=read(PUBLIC/'preflight.json.gz');verify(pre)
    q=pl.read_parquet(OUT/'quality-predictions.parquet').to_dicts();f=pl.read_parquet(OUT/'value-predictions.parquet').to_dicts()
    quality=[]
    for y in (2021,2022):
        rows=[r for r in q if r['origin_year']==y]
        for family,pool in [('OF',[r for r in rows if r['position'] in (7,8,9)]),('all_positions',rows)]:
            quality.append(dict(origin=y,family=family,result=quality_scores(pool)))
        for key in ('position','age_band','sample_band'):
            for val in sorted({r[key] for r in rows},key=str):
                pool=[r for r in rows if r[key]==val and r['position'] in (7,8,9)]
                quality.append(dict(origin=y,family=key,group=val,result=quality_scores(pool)))
    value={}
    for target in ('defense','expanded'):
        value[target]=score_rows(f,[a+'_'+target for a in ARMS],'actual_'+target)
        value[target]['intervals']=[paired_interval(f,'centered_'+target,a+'_'+target,'actual_'+target,draws=2000,seed=SEED) for a in ('legacy','neutral')]
    groups=[]
    for stage in sorted({r['stage'] for r in f}):
        rows=[r for r in f if r['stage']==stage]
        groups.append(dict(stage=stage,eligible=len(rows),measured_rows=sum(r['actual_defense'] is not None for r in rows),
            defense=score_rows(rows,[a+'_defense' for a in ARMS],'actual_defense'),expanded=score_rows(rows,[a+'_expanded' for a in ARMS],'actual_expanded')))
    defenders=[r for r in f if r['actual_fielding_outs']>0]
    write(PUBLIC/'report.json.gz',dict(model_fits=0,quality=quality,value=value,stage_groups=groups,
        actual_defenders=dict(eligible=len(defenders),complete=sum(r['actual_defense'] is not None for r in defenders),
            defense=score_rows(defenders,[a+'_defense' for a in ARMS],'actual_defense')),
        value_unknown_rows=sum(r['actual_defense'] is None for r in f),
        unknown_target_defensive_outs=sum(r['actual_fielding_outs'] for r in f if r['actual_defense'] is None),
        player_walkthrough_status='pending',deployment_approved=False,no_2026_selection=True,
        hashes={str(p):sha256_file(p) for p in [Path(__file__),PUBLIC/'preflight.json.gz']},
        uncertainty_limit='Development person intervals, conditional on measurement selection and fixed reference; not reference-estimation/season-shock uncertainty.'))
    protections();print('Fixed talent and value comparisons scored; player review pending.',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['prepare','score']);args=p.parse_args()
    (prepare if args.phase=='prepare' else score)()
