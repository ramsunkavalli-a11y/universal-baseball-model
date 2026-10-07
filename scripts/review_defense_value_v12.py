"""Preserved source cases plus predeclared score diagnostics and origin-only peers."""
from collections import defaultdict
from pathlib import Path
import json

import polars as pl

from universal_baseball.defense_value import score_rows
from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections,save
from verify_defense_value_v11 import weighted_history, PATHS

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/generated/defense-value-v12'
PUBLIC=ROOT/'reports/model-evidence/defense-value-v12'
SOURCE=ROOT/'reports/generated/defense-value-v11'


def read(p):return json.loads(p.read_text(encoding='utf8'))


def main():
    protections();assert not (OUT/'player-walkthrough.json').exists()
    pre=read(OUT/'preflight.json');verified=read(OUT/'independent-verification.json')
    for p,h in {**pre['hashes'],**pre['output_hashes'],**verified['hashes']}.items():assert sha256_file(Path(p))==h,p
    f=pl.read_parquet(OUT/'predictions.parquet');complete=f.filter(pl.col('actual_defense').is_not_null())
    q=pl.read_parquet(ROOT/'reports/generated/defense-transition-v10/predictions.parquet')
    bridge={r['row_id']:r for r in q.to_dicts()};forecasts={r['row_id']:r for r in f.to_dicts()}
    channel=pl.read_parquet(OUT/'channel-predictions.parquet');channels=defaultdict(list)
    for r in channel.to_dicts():channels[r['row_id']].append(r)
    hist={k:defaultdict(list) for k in ('range','framing','catcher','other')}
    for k in hist:
        for r in pl.read_parquet(PATHS[k]).to_dicts():hist[k][r['player_id']].append(r)
    selected=defaultdict(list)
    original=read(SOURCE/'reviewed-source-player-cases.json')['records']
    for r in original:
        if r['is_focal']:selected[r['row_id']].append('fixed_source_focal')
    for metric,target in [('defense','actual_defense'),('expanded','actual_expanded')]:
        ranked=complete.with_columns(
            ((pl.col('repair_history_'+metric)-pl.col(target))**2-(pl.col('repair_neutral_'+metric)-pl.col(target))**2).alias('change'),
            (pl.col('repair_history_'+metric)-pl.col(target)).alias('residual'))
        for category,key,descending in [('largest_gain','change',False),('largest_loss','change',True),
            ('largest_false_high','residual',True),('largest_false_low','residual',False)]:
            row=ranked.sort([key,'row_id'],descending=[descending,False]).row(0,named=True)
            selected[row['row_id']].append(metric+'_'+category)
    calrank=complete.with_columns(((pl.col('repair_calibrated_defense')-pl.col('actual_defense'))**2-
        (pl.col('repair_history_defense')-pl.col('actual_defense'))**2).alias('change'))
    for category,descending in [('calibration_gain',False),('calibration_loss',True)]:
        selected[calrank.sort(['change','row_id'],descending=[descending,False])['row_id'][0]].append(category)
    ordinary=complete.filter((pl.col('actual_fielding_outs')>=300)&(pl.col('actual_PA')>=100)).with_columns(
        (pl.col('repair_history_expanded')-pl.col('actual_expanded')).abs().alias('absolute_error'))
    median=ordinary['absolute_error'].median()
    rid=ordinary.with_columns((pl.col('absolute_error')-median).abs().alias('distance')).sort(['distance','row_id'])['row_id'][0]
    selected[rid].append('ordinary_participant_nearest_median_absolute_error')
    cases=[]
    original_by_focal=defaultdict(list)
    for r in original:original_by_focal[r['focal_player_id'],r['origin']].append(r['row_id'])
    for rid,categories in sorted(selected.items()):
        r=bridge[rid];pid,y=r['player_id'],r['origin_year']
        if (pid,y) in original_by_focal:
            ids=original_by_focal[pid,y]
        else:
            peers=q.filter((pl.col('origin_year')==y)&(pl.col('stage')==r['stage'])&
                (pl.col('repertoire_primary_role')==r['repertoire_primary_role'])&(pl.col('player_id')!=pid)).to_dicts()
            peers=sorted(peers,key=lambda p:(abs((p['age'] or 27)-(r['age'] or 27)),
                abs(p['role_defensive_sample']-r['role_defensive_sample']),p['row_id']))[:3]
            ids=[rid,*[p['row_id'] for p in peers]]
        records=[]
        for recordid in ids:
            b=bridge[recordid];rec=forecasts[recordid];year=b['origin_year'];player=b['player_id'];ch=channels[recordid]
            calculations={}
            for c in ch:
                group='range' if c['channel'].startswith('range_') else 'framing' if c['channel']=='framing' else 'catcher' if c['channel'] in ('throwing','blocking') else 'other'
                calculations[c['channel']]=weighted_history(c['channel'],hist[group][player],year)
            records.append(dict(is_focal=recordid==rid,forecast=rec,channels=ch,history_calculations=calculations,
                past_native_records={k:[a for a in hist[k][player] if year-2<=a['season']<=year] for k in hist},
                future_native_records={k:[a for a in hist[k][player] if a['season']==year+1] for k in hist},
                role_inputs={k:v for k,v in b.items() if k.startswith(('mlb_weighted_','minor_weighted_','repertoire_','transition_','repair_'))
                    and not k.endswith('cell_squared_error')},
                official_actual_exposure={p:b[f'actual_{p}'] for p in range(2,11)},
                forecast_exposure={arm:{p:b[f'{arm}_{p}'] for p in range(2,11)} for arm in ('ratio','repair','transition')}))
        cases.append(dict(row_id=rid,player_id=pid,origin=y,player_name=r['player_name'],categories=categories,records=records))
    # Additional slices named in the original contract; no new forecast or selection.
    slices=[];rows=f.to_dicts()
    for feature in ['current_MLB_exposure','quality_history']:
        for label in (['zero','1-99','100+'] if feature=='current_MLB_exposure' else ['unknown_all_channels','some_measured_history']):
            selected_rows=[r for r in rows if ('zero' if r['current_MLB_PA']==0 else '1-99' if r['current_MLB_PA']<100 else '100+')==label] if feature=='current_MLB_exposure' else [r for r in rows if ('unknown_all_channels' if r['known_quality_channels']==0 else 'some_measured_history')==label]
            slices.append(dict(feature=feature,label=label,rows=len(selected_rows),actual_defenders=sum(r['actual_fielding_outs']>0 for r in selected_rows),
                defense=score_rows(selected_rows,['repair_neutral_defense','repair_history_defense','repair_calibrated_defense'],'actual_defense'),
                expanded=score_rows(selected_rows,['repair_neutral_expanded','repair_history_expanded','repair_calibrated_expanded'],'actual_expanded')))
    write=dict(status='machine_traces_complete_readable_review_pending',selection='Nine fixed cases/peers preserved; contracted primary extrema, calibration extrema and ordinary case with origin-only peers.',
        cases=cases,focal_cases=len(cases),records=sum(len(c['records']) for c in cases),slices=slices,
        preserved_source_records=36,player_walkthrough_status='pending',fits=0,protected_outcomes_used=False,
        hashes={str(p):sha256_file(p) for p in [Path(__file__),OUT/'preflight.json',OUT/'report.json',OUT/'independent-verification.json',
            SOURCE/'reviewed-source-player-cases.json',*PATHS.values()]})
    for d in (OUT,PUBLIC):save(d/'player-walkthrough.json',write)
    protections();print(json.dumps([(c['player_name'],c['origin'],c['categories']) for c in cases]));print('Records',write['records'])


if __name__=='__main__':main()
