"""Locked accounting comparison of saved quality/opportunity; zero model fits."""

from collections import defaultdict
from pathlib import Path
import argparse
import json
import math

import polars as pl

from universal_baseball.defense_value import (
    OPPORTUNITY_ARMS, QUALITY_ARMS, position_value, quality, opportunity,
    predicted_runs, score_rows, paired_interval)
from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections, save

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'reports/generated/defense-value-v12'
PUBLIC = ROOT/'reports/model-evidence/defense-value-v12'
SOURCE = ROOT/'reports/generated/defense-value-v11'
BRIDGE = ROOT/'reports/generated/defense-transition-v10/predictions.parquet'
CONTRACT = ROOT/'docs/defense-value-v12-integration-contract.md'
ARMS = tuple(f'{o}_{q}' for o in OPPORTUNITY_ARMS for q in QUALITY_ARMS)


def read(p): return json.loads(p.read_text(encoding='utf8'))


def write(name, value):
    for d in (OUT, PUBLIC): save(d/name, value)


def verify(hashes):
    for p,h in hashes.items(): assert sha256_file(Path(p)) == h,p


def prepare():
    protections(); OUT.mkdir(parents=True,exist_ok=True); PUBLIC.mkdir(parents=True,exist_ok=True)
    assert not (OUT/'preflight.json').exists()
    receipt=read(SOURCE/'source-final-review.json'); assert receipt['player_walkthrough_status']=='complete'
    verify(receipt['hashes'])
    q=pl.read_parquet(BRIDGE); native=pl.read_parquet(SOURCE/'reviewed-component-ledger.parquet')
    target=pl.read_parquet(SOURCE/'reviewed-player-ledger.parquet')
    bat=pl.read_parquet(SOURCE/'batting-ledger.parquet')
    assert q.height==12432 and q['row_id'].n_unique()==12432
    assert q['target_year'].max()==2025 and (q['target_year']==q['origin_year']+1).all()
    assert native.height==12432*12 and native.unique(['row_id','channel']).height==native.height
    assert set(q['row_id'])==set(target['row_id'])==set(bat['row_id'])
    ranges=pl.read_parquet(ROOT/'reports/generated/defense-native-range-v3/predictions.parquet')
    cal={(r['origin_year'],r['player_id'],r['position']):r for r in ranges.iter_rows(named=True)}
    cal_checks=read(ROOT/'reports/generated/defense-native-range-v3/fit-preflight.json')['checks']
    for check in cal_checks:
        if check['origin'] not in (2022,2023,2024): continue
        assert all(y+3<=check['origin'] and pid%5!=check['fold'] for y,pid,pos in check['train_keys'])
        assert all(y==check['origin'] and pid%5==check['fold'] for y,pid,pos in check['test_keys'])
        assert {r[1] for r in check['train_keys']}.isdisjoint(r[1] for r in check['test_keys'])
    cells=[]
    for r in native.iter_rows(named=True):
        saved=cal.get((r['origin_year'],r['player_id'],int(r['channel'][-1]))) if r['channel'].startswith('range_') else None
        cells.append(dict(**r, calibration_outside_training_range=saved['features_outside_training_range'] if saved else None))
    channels=defaultdict(list)
    for r in cells: channels[r['row_id']].append(r)
    bl={r['row_id']:r for r in bat.iter_rows(named=True)}
    tl={r['row_id']:r for r in target.iter_rows(named=True)}
    predictions=[]; channel_predictions=[]
    for r in q.iter_rows(named=True):
        entries=channels[r['row_id']]; b=bl[r['row_id']]; label=tl[r['row_id']]
        actual_position=position_value(r,'actual'); actual_total=label['complete_defined_native_runs']
        out=dict(row_id=r['row_id'],player_id=r['player_id'],player_name=r['player_name'],origin_year=r['origin_year'],target_year=r['target_year'],
            stage=r['stage'],age=r['age'],prior_debut=r['prior_debut'],current_MLB_PA=r['pa_0'],expected_PA=r['preseason_pa'],actual_PA=r['next_pa'],
            actual_fielding_outs=sum(r[f'actual_{p}'] for p in range(2,10)),
            known_quality_channels=sum(c['quality_evidence_observed'] for c in entries),
            calibrated_range_channels=sum(c['quality_evidence_observed'] and bool(c['range_calibration_fit_allowed']) and c['saved_range_calibration'] is not None for c in entries if c['channel'].startswith('range_')),
            sparse_calibrated_range_channels=sum(c['quality_evidence_observed'] and bool(c['range_calibration_fit_allowed']) and (c['range_calibration_profile_people'] or 0)<20 for c in entries if c['channel'].startswith('range_')),
            extrapolated_range_channels=sum(bool(c['calibration_outside_training_range']) for c in entries),
            unknown_target_channels=label['unknown_channels'],actual_defense=actual_total,
            batting_forecast=b['combined_value'],batting_reference=b['preseason_value'],actual_batting=b['audit_relative_value'],actual_position_runs=actual_position,
            actual_expanded=None if actual_total is None else b['audit_relative_value']+(actual_total+actual_position)/10.,
            actual_no_framing=None if actual_total is None else b['audit_relative_value']+(actual_total+actual_position-next(c['actual_runs'] for c in entries if c['channel']=='framing'))/10.)
        for o in OPPORTUNITY_ARMS:
            out[f'{o}_position_runs']=position_value(r,o)
            out[f'{o}_unallocated_outs']=r.get(f'{o}_unallocated_outs',0.) or 0.
            for skill in QUALITY_ARMS:
                arm=f'{o}_{skill}';values={c['channel']:predicted_runs(r,c,o,skill) for c in entries}
                total=sum(values.values())
                out[arm+'_defense']=total
                out[arm+'_expanded']=b['combined_value']+(out[f'{o}_position_runs']+total)/10.
                out[arm+'_no_framing']=out[arm+'_expanded']-values['framing']/10.
        for c in entries:
            detail=dict(**c)
            for skill in QUALITY_ARMS:
                detail[skill+'_quality']=quality(c,skill)
                den=c['actual_native_opportunities']
                if c['actual_official_exposure']==0: den=0.
                detail[skill+'_oracle_runs']=None if den is None else quality(c,skill)*den/c['rate_unit']
                for o in OPPORTUNITY_ARMS: detail[f'{o}_{skill}']=predicted_runs(r,c,o,skill)
            for o in OPPORTUNITY_ARMS: detail[o+'_predicted_opportunities']=opportunity(r,c['channel'],o)
            channel_predictions.append(detail)
        predictions.append(out)
    f=pl.DataFrame(predictions,infer_schema_length=None);f.write_parquet(OUT/'predictions.parquet')
    pl.DataFrame(channel_predictions,infer_schema_length=None).write_parquet(OUT/'channel-predictions.parquet')
    assert all(math.isfinite(r[a+'_expanded']) for r in predictions for a in ARMS)
    paths=[Path(__file__),CONTRACT,ROOT/'src/universal_baseball/defense_value.py',BRIDGE,
        SOURCE/'source-final-review.json',SOURCE/'reviewed-component-ledger.parquet',SOURCE/'reviewed-player-ledger.parquet',SOURCE/'batting-ledger.parquet',
        ROOT/'reports/generated/defense-native-range-v3/fit-preflight.json',ROOT/'reports/generated/defense-native-range-v3/models.json',
        ROOT/'reports/generated/defense-native-range-v3/predictions.parquet']
    write('preflight.json',dict(before_scoring=True,new_fits=0,forecasts=12432,origin_years=[2022,2023,2024],
        primary_contrast=['repair_history','repair_neutral'],opportunity_arms=list(OPPORTUNITY_ARMS),quality_arms=list(QUALITY_ARMS),
        range_fit_chronology_and_own_player_exclusion_pass=True,support_claim='Saved qualification and sparse/extrapolation warnings retained; no universal minor transfer claim.',
        observed_complete_rows=f.filter(pl.col('actual_defense').is_not_null()).height,
        unknown_outcomes_kept=f.filter(pl.col('actual_defense').is_null()).height,
        batting_branch='Reviewed combined_value with fixed V68 preseason_PA, not a new production replay.',
        fits=0,protected_outcomes_used=False,forecast_or_explorer_changed=False,
        hashes={str(p):sha256_file(p) for p in paths},output_hashes={str(OUT/n):sha256_file(OUT/n) for n in ['predictions.parquet','channel-predictions.parquet']}))
    protections();print('Prepared fixed nine combinations, no fit or score.')


def score():
    protections();assert not (OUT/'report.json').exists();pre=read(OUT/'preflight.json')
    verify({**pre['hashes'],**pre['output_hashes']})
    f=pl.read_parquet(OUT/'predictions.parquet');rows=f.to_dicts();channel=pl.read_parquet(OUT/'channel-predictions.parquet')
    metrics={}
    for name,target in [('defense','actual_defense'),('expanded','actual_expanded'),('no_framing','actual_no_framing')]:
        fields=[a+'_'+name for a in ARMS]
        metrics[name]=dict(all_complete=score_rows(rows,fields,target),
            actual_defenders=score_rows([r for r in rows if r['actual_fielding_outs']>0],fields,target),
            known_history=score_rows([r for r in rows if r['known_quality_channels']>0],fields,target))
    intervals=[]
    for name,target in [('defense','actual_defense'),('expanded','actual_expanded'),('no_framing','actual_no_framing')]:
        for left,right in [('repair_history','repair_neutral'),('repair_calibrated','repair_history')]:
            intervals.append(paired_interval(rows,left+'_'+name,right+'_'+name,target))
    channel_scores=[]
    for (c,),g in channel.group_by('channel'):
        rs=g.to_dicts(); observed=[r for r in rs if r['actual_runs'] is not None]
        for scope,data in [('all_observed',observed),('actual_exposure',[r for r in observed if r['actual_official_exposure']>0]),
                           ('measured_history',[r for r in observed if r['quality_evidence_observed']])]:
            channel_scores.append(dict(channel=c,scope=scope,delivered=score_rows(data,list(ARMS),'actual_runs'),
                actual_count_diagnostic=score_rows([r for r in data if r['history_oracle_runs'] is not None],
                    ['neutral_oracle_runs','history_oracle_runs','calibrated_oracle_runs'],'actual_runs')))
    groups=[]
    for y in (2022,2023,2024):
        for stage in sorted(f['stage'].unique()):
            for ageband in ['<=24','25-29','30+','unknown']:
                rs=[r for r in rows if r['origin_year']==y and r['stage']==stage and
                    ('unknown' if r['age'] is None else '<=24' if r['age']<=24 else '25-29' if r['age']<=29 else '30+')==ageband]
                if not rs:continue
                groups.append(dict(origin=y,stage=stage,age_band=ageband,rows=len(rs),
                    actual_defenders=sum(r['actual_fielding_outs']>0 for r in rs),
                    partial_measurements=sum(r['actual_defense'] is None for r in rs),
                    defense=score_rows(rs,['repair_neutral_defense','repair_history_defense','repair_calibrated_defense'],'actual_defense'),
                    expanded=score_rows(rs,['repair_neutral_expanded','repair_history_expanded','repair_calibrated_expanded'],'actual_expanded')))
    position=score_rows(rows,[o+'_position_runs' for o in OPPORTUNITY_ARMS],'actual_position_runs')
    report=dict(status='scored_pending_independent_replay_and_player_review',metrics=metrics,paired_intervals=intervals,
        position=position,channel_scores=channel_scores,groups=groups,forecasts=12432,
        partial_rows=f.filter(pl.col('actual_defense').is_null()).height,
        partial_actual_outs=int(f.filter(pl.col('actual_defense').is_null())['actual_fielding_outs'].sum()),
        support_counts=f.group_by('origin_year').agg(pl.col('calibrated_range_channels').sum(),
            pl.col('sparse_calibrated_range_channels').sum(),pl.col('extrapolated_range_channels').sum()).sort('origin_year').to_dicts(),
        fits=0,full_WAR_claim=False,lower_minor_skill_transfer_validated=False,player_walkthrough_status='pending',
        protected_outcomes_used=False,forecast_or_explorer_changed=False,
        hashes={str(OUT/'preflight.json'):sha256_file(OUT/'preflight.json')})
    write('report.json',report)
    print(json.dumps({k:v['all_complete']['equal_origin'] for k,v in metrics.items()},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','score']);args=parser.parse_args()
    prepare() if args.mode=='prepare' else score()
