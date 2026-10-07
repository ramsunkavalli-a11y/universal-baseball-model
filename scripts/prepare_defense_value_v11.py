"""Matched native labels and existing quality histories; no fit or forecast score."""

from collections import defaultdict
from pathlib import Path
import json
import math

import polars as pl

from universal_baseball.defense_native_range import history as range_history
from universal_baseball.catcher_framing_baseline import history as framing_history
from universal_baseball.catcher_throw_block_baseline import history as catcher_history
from universal_baseball.arm_receiving_baseline import history as arm_history
from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections,save

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/generated/defense-value-v11'
PUBLIC=ROOT/'reports/model-evidence/defense-value-v11'
RANGE=ROOT/'reports/generated/defense-native-range-v3'
BRIDGE=ROOT/'reports/generated/defense-transition-v10'
PATHS={
    'range':RANGE/'component-ledger.parquet',
    'framing':ROOT/'reports/generated/catcher-native-opportunity-v3/modern/framing-annual.parquet',
    'catcher':ROOT/'reports/generated/catcher-throw-block-v5/extension-annual.parquet',
    'other':ROOT/'reports/generated/arm-receiving-v6/official-scope/annual.parquet',
    'range_predictions':RANGE/'predictions.parquet',
    'batting':ROOT/'reports/generated/hitter-season-value-ledger/ledger.parquet',
}
CHANNELS=[*(f'range_{p}' for p in range(3,10)),'framing','throwing','blocking','arm','receiving']


def read(p):return json.loads(p.read_text(encoding='utf8'))


def main():
    protections();assert not (OUT/'source-review.json').exists()
    final=read(BRIDGE/'final-review.json');assert final['player_walkthrough_status']=='complete'
    for p,h in final['hashes'].items():assert sha256_file(Path(p))==h,p
    OUT.mkdir(parents=True,exist_ok=True);PUBLIC.mkdir(parents=True,exist_ok=True)
    frames={k:pl.read_parquet(p) for k,p in PATHS.items()}
    q=pl.read_parquet(BRIDGE/'predictions.parquet')
    bat=frames['batting'].filter(pl.col('row_id').is_in(q['row_id']))
    paired=q.select('row_id','player_id','origin_year','target_year','preseason_pa','next_pa').sort('row_id')
    assert paired.equals(bat.select(paired.columns).sort('row_id')) and q.height==12432
    origin_value=bat.select('row_id','origin_replacement_rate','audit_relative_value','combined_value','preseason_value')
    origin_value.write_parquet(OUT/'batting-ledger.parquet')
    hist={k:defaultdict(list) for k in ('range','framing','catcher','other')}
    for k in hist:
        for r in frames[k].to_dicts():hist[k][r['player_id']].append(r)
    native={(r['season'],r['player_id'],r['position']):r for r in frames['range'].to_dicts()}
    framing={(r['season'],r['player_id']):r for r in frames['framing'].to_dicts()}
    catcher={(r['season'],r['player_id'],r['component']):r for r in frames['catcher'].to_dicts()}
    other={(r['season'],r['player_id'],r['kind']):r for r in frames['other'].to_dicts()}
    cal={(r['origin_year'],r['player_id'],r['position']):r for r in frames['range_predictions'].to_dicts()}
    for r in frames['range'].to_dicts():
        total=sum(r[c] or 0 for c in ('range_runs','arm_runs','dp_runs','fielding_runs_prevented_on_rec1b','framing_runs','throwing_runs','blocking_runs'))
        assert math.isclose(total,r['total_runs'],abs_tol=1e-9)
    labels=[];groups=defaultdict(list)
    for r in q.to_dicts():
        y,t,pid=r['origin_year'],r['target_year'],r['player_id']
        for channel in CHANNELS:
            record=None;source_keys=[];known=False;runs=None;den=None;calibration=None;cal_allowed=None;cal_support=None
            if channel.startswith('range_'):
                pos=int(channel.split('_')[1]);exposure=r[f'actual_{pos}'];record=native.get((t,pid,pos))
                known=bool(record and record['range_valid'])
                if known:runs=record['range_runs'];den=record['native_outs']
                h,_=range_history(hist['range'][pid],y,pos)
                rate=h['history_rate'];reliability=h['reliability'];observed=h['history_outs']>0;history_den=h['history_outs'];unit=1500.
                calibration_record=cal.get((y,pid,pos))
                if calibration_record:
                    calibration=calibration_record['calibrated'];cal_allowed=calibration_record['fit_allowed'];cal_support=calibration_record['profile_people']
                source_keys=[dict(season=t,player_id=pid,position=pos)]
            elif channel=='framing':
                exposure=r['actual_2'];record=framing.get((t,pid));known=bool(record and record['exposure_valid'] and record['framing_measurement_valid'])
                if known:runs=record['framing_runs'];den=record['pitches']
                h=framing_history(hist['framing'][pid],y);rate=h['history_rate'];reliability=h['reliability'];observed=h['quality_evidence_observed'];history_den=h['history_pitches'];unit=1000.
                source_keys=[dict(season=t,player_id=pid)]
            elif channel in ('throwing','blocking'):
                exposure=r['actual_2'];record=catcher.get((t,pid,channel));known=bool(record and record['exposure_valid'] and record['measurement_valid'])
                if known:runs=record['runs'];den=record['opportunities']
                h=catcher_history(channel,hist['catcher'][pid],y);rate=h['history'];reliability=h['reliability'];observed=h['quality_evidence_observed'];history_den=h['history_opportunities'];unit=100. if channel=='throwing' else 1000.
                source_keys=[dict(season=t,player_id=pid,component=channel)]
            else:
                record=other.get((t,pid,channel));unit=100.
                h=arm_history(channel,hist['other'][pid],y);rate=h['history'];reliability=h['reliability'];observed=h['quality_evidence_observed'];history_den=h['history_opportunities']
                if channel=='receiving':
                    exposure=r['actual_3'];known=bool(record and record['quality_valid'])
                    if known:runs=record['runs'];den=record['opportunities']
                    source_keys=[dict(season=t,player_id=pid,kind=channel)]
                else:
                    positions=[p for p in (7,8,9) if r[f'actual_{p}']>0];exposure=sum(r[f'actual_{p}'] for p in (7,8,9))
                    posrecords=[native.get((t,pid,p)) for p in positions]
                    known=bool(positions) and all(n and n['exposure_valid'] and n['arm_runs'] is not None for n in posrecords)
                    if known:runs=sum(n['arm_runs'] for n in posrecords)
                    if record and record['isolated_outfield_quality_valid']:den=record['opportunities']
                    source_keys=[dict(season=t,player_id=pid,position=p) for p in positions]
            if exposure==0:
                runs=0.;known=True;status='certified_no_position_exposure_not_skill'
            else:status='measured_delivered_runs' if known else 'unmeasured_applicable_channel'
            if not known:runs=None
            result=dict(row_id=r['row_id'],player_id=pid,player_name=r['player_name'],origin_year=y,target_year=t,outer_fold=r['outer_fold'],stage=r['stage'],age=r['age'],
                channel=channel,actual_official_exposure=exposure,actual_runs=runs,target_status=status,actual_native_opportunities=den,
                source_keys=json.dumps(source_keys),history_rate=rate,rate_unit=unit,history_opportunities=history_den,reliability=reliability,
                quality_evidence_observed=observed,quality_status='measured_history' if observed else 'unknown_quality_zero_prior_mean',
                saved_range_calibration=calibration,range_calibration_fit_allowed=cal_allowed,range_calibration_profile_people=cal_support,
                isolated_arm_opportunities_known=(den is not None) if channel=='arm' else None)
            labels.append(result);groups[y,channel].append(result)
    long=pl.DataFrame(labels,infer_schema_length=None);assert long.height==12432*12
    long.write_parquet(OUT/'component-ledger.parquet')
    coverage=[]
    for (y,c),rows in sorted(groups.items()):
        applicable=[r for r in rows if r['actual_official_exposure']>0];measured=[r for r in applicable if r['actual_runs'] is not None]
        coverage.append(dict(origin=y,channel=c,rows=len(rows),applicable_people=len(applicable),measured_people=len(measured),
            unknown_people=len(applicable)-len(measured),official_outs=sum(r['actual_official_exposure'] for r in applicable),
            unmeasured_official_outs=sum(r['actual_official_exposure'] for r in applicable if r['actual_runs'] is None),
            historical_quality_people=sum(r['quality_evidence_observed'] for r in rows),
            measured_delivered_runs=sum(r['actual_runs'] for r in measured),
            isolated_native_count_people=sum(r['actual_native_opportunities'] is not None for r in applicable)))
    complete=long.group_by('row_id','origin_year').agg(pl.col('actual_runs').null_count().alias('unknown_channels'),
        pl.col('actual_runs').sum().alias('observed_partial_native_runs')).with_columns(
        pl.when(pl.col('unknown_channels')==0).then(pl.col('observed_partial_native_runs')).otherwise(None).alias('complete_defined_native_runs'))
    complete.write_parquet(OUT/'player-ledger.parquet')
    nonOF=frames['range'].filter(pl.col('season').is_between(2023,2025)&pl.col('position').is_between(3,6)).group_by('season').agg(
        pl.col('arm_runs').sum().alias('unmodeled_non_OF_arm_runs'),pl.col('dp_runs').sum().alias('excluded_DP_runs'))
    fixed=[(545361,2022),(592206,2022),(677951,2022),(694192,2023),(682626,2022),(662139,2022),(621566,2022),(805811,2024)]
    caseids=[]
    for pid,y in fixed:
        focal=q.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y))
        assert focal.height==1,(pid,y)
        r=focal.to_dicts()[0]
        pool=q.filter((pl.col('origin_year')==y)&(pl.col('stage')==r['stage'])&(pl.col('player_id')!=pid)&
            (pl.col('repertoire_primary_role')==r['repertoire_primary_role'])).to_dicts()
        peers=sorted(pool,key=lambda p:(abs((p['age'] or 27)-(r['age'] or 27)),abs(p['role_defensive_sample']-r['role_defensive_sample']),p['row_id']))[:3]
        for member in [r,*peers]:
            caseids.append(dict(focal_player_id=pid,origin=y,player_id=member['player_id'],player_name=member['player_name'],row_id=member['row_id'],is_focal=member['player_id']==pid))
    save(OUT/'source-player-cases.json',dict(selection='Eight fixed different-defense/coverage cases; three same-origin/stage/dominant-role peers nearest age and exposure, no outcome selection.',
        records=[dict(**c,channels=long.filter(pl.col('row_id')==c['row_id']).to_dicts()) for c in caseids]))
    inputpaths=[Path(__file__),ROOT/'docs/defense-value-v11-source-contract.md',BRIDGE/'predictions.parquet',BRIDGE/'final-review.json',*PATHS.values(),
        ROOT/'src/universal_baseball/defense_native_range.py',ROOT/'src/universal_baseball/catcher_framing_baseline.py',
        ROOT/'src/universal_baseball/catcher_throw_block_baseline.py',ROOT/'src/universal_baseball/arm_receiving_baseline.py']
    result=dict(status='prepared_needs_independent_arithmetic_and_player_review',fits=0,model_accuracy_claim=False,forecast_rows=q.height,channel_rows=long.height,
        coverage=coverage,complete_target_counts=complete.group_by('origin_year').agg(pl.len(),(pl.col('unknown_channels')==0).sum().alias('complete_people'),
            (pl.col('unknown_channels')>0).sum().alias('partial_people')).sort('origin_year').to_dicts(),
        unmodeled_or_excluded_native_channels=nonOF.sort('season').to_dicts(),
        defined_target='Seven range positions plus OF arms, 1B receiving and framing/throwing/blocking; excludes DP and non-OF arms, not exact full WAR.',
        matched_batting_units='Existing season-relative batting plus replacement common wins; no second replacement addition.',
        actual_outcome_units='Native component runs; ten runs per existing common win, not season-specific published FG WAR.',
        positional_schedule_denominator_outs=4374,unknown_quality_is_not_measured_neutral=True,
        player_walkthrough_status='pending',protected_outcomes_used=False,forecast_or_explorer_changed=False,
        hashes={str(p):sha256_file(p) for p in inputpaths},output_hashes={str(OUT/n):sha256_file(OUT/n) for n in
            ['component-ledger.parquet','player-ledger.parquet','batting-ledger.parquet','source-player-cases.json']})
    save(OUT/'source-review.json',result);save(PUBLIC/'source-review.json',result)
    save(PUBLIC/'source-player-cases.json',read(OUT/'source-player-cases.json'))
    protections();print(json.dumps(dict(rows=q.height,channels=long.height,complete=result['complete_target_counts'],status=result['status'])))


if __name__=='__main__':main()
