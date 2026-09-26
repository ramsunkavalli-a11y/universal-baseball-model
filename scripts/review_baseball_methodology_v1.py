"""Deep-review diagnostics on archived data only; no fitting or forecast changes."""
import json
from pathlib import Path
import numpy as np
import polars as pl
from universal_baseball.hitter_arrival_value_transfer import training
from universal_baseball.hitter_conditional_workload import active_training
from universal_baseball.methodology_review import component_loss_decomposition, workload_error_decomposition
from universal_baseball.storage import sha256_file

OUT=Path('model_artifacts/baseball-methodology-review-v1-2026-09-25')
PANEL=Path('reports/generated/hitter-arrival-source-repair-v1/repaired-panel.parquet')
FORECAST=Path('model_artifacts/hitter-integrated-opportunity-value-v1-2026-09-25/predictions.parquet')
DEFENSE=Path('reports/generated/milb-outfield-range-hitter-value-v1/predictions.parquet')
FITS=Path('model_artifacts/hitter-conditional-workload-v1-2026-09-23/fit-manifest.json')
ROOT=Path('data/working/pbp-opportunity-foundation-v1')
YEARS=(2016,2017,2018,2019,2021,2022,2023,2024)


def main():
    paths=[PANEL,FORECAST,DEFENSE,FITS,Path('scripts/review_baseball_methodology_v1.py'),
        Path('src/universal_baseball/methodology_review.py'),
        Path('src/universal_baseball/pbp_opportunity_events.py'),
        Path('src/universal_baseball/historical_fielding_range.py'),
        Path('src/universal_baseball/historical_catcher_pbp.py'),
        Path('src/universal_baseball/hitter_arrival_value_transfer.py'),
        Path('src/universal_baseball/hitter_conditional_workload.py')]
    hashes={str(p):sha256_file(p) for p in paths}
    result={'purpose':'diagnose archived measurement and inference, not select a model',
        'new_fits':0,'forecast_changes':False,'protected_outcomes_used':False,
        'source_hashes':hashes,'opportunity':[],'weighting':[],'fielding':[], 'catcher_narratives':[],
        'partition_hashes':{},'partition_deduplication':[]}
    panel=pl.read_parquet(PANEL)
    assert panel['origin_year'].max()<=2025
    f=pl.read_parquet(FORECAST)
    assert (f['origin_year']+f['horizon']).max()<=2025
    for (year,h),g in f.filter(pl.col('prospect')).group_by('origin_year','horizon',maintain_order=True):
        p=g['H_p'].to_numpy();q=g['H_pa'].to_numpy()/p;w=g['actual_pa'].to_numpy()
        result['opportunity'].append({'origin':year,'horizon':h,'players':g.height,
            'actual_participants':int((w>0).sum()),'predicted_participants':float(p.sum()),
            'actual_pa':float(w.sum()),'predicted_pa':float(g['H_pa'].sum()),
            **workload_error_decomposition(p,q,w)})
    result['opportunity'].sort(key=lambda x:(x['origin'],x['horizon']))
    fits=json.loads(FITS.read_text())['fits']
    for record in fits:
        if record['head']!='D':continue
        year,h=record['year'],record['horizon']
        all_rows=training(panel,year,h)
        active=all_rows.filter(pl.col(f'pa_h{h}')>0)
        recalculated=active_training(panel,year,h)
        assert active.select('origin_year','player_id').equals(recalculated.select('origin_year','player_id'))
        y=active[f'pa_h{h}'].to_numpy();wa=active['identity_weight'].to_numpy();wr=recalculated['identity_weight'].to_numpy()
        result['weighting'].append({'origin':year,'horizon':h,'used_features':len(record['used_features']),
            'training_origins':record['training_origins'],'latest_label':record['latest_label'],
            'active_training_rows':active.height,'active_players':active['player_id'].n_unique(),
            'active_rows_with_current_contact':int(active['raw0__available'].sum()),
            'row_mean_conditional_pa':float(y.mean()),
            'same_measure_conditional_pa':float(np.average(y,weights=wa)),
            'reweighted_conditional_pa':float(np.average(y,weights=wr)),
            'row_share_regular':float((y>=450).mean()),
            'same_measure_share_regular':float(np.average(y>=450,weights=wa)),
            'reweighted_share_regular':float(np.average(y>=450,weights=wr))})
    d=pl.read_parquet(DEFENSE)
    other_actual=d['actual_partial_war_with_general_defense']-d['actual_general_defense_war']
    result['defense_error_interaction']={'rows':d.height,'target_season':2025,
        **component_loss_decomposition(d['prediction_without_general_defense_war'],other_actual,
             d['prediction_outfield_rebuilt_war'],d['actual_general_defense_war'])}
    cols=['season','level','game_pk','at_bat_index','bb_type','terminal_outcome_group',
          'responsible_position','pa_description','fielder_2','pitcher','hc_x','hc_y']
    for year in YEARS:
        parts=sorted(ROOT.glob(f'season={year}/level=*/terminal/*.parquet'))
        assert parts
        print(f'Reviewing PBP attribution {year}: {len(parts)} partitions',flush=True)
        frames=[]
        for part in parts:
            result['partition_hashes'][str(part)]=sha256_file(part)
            frames.append(pl.read_parquet(part,columns=cols))
        t=pl.concat(frames,how='diagonal_relaxed')
        raw_rows=t.height;t=t.unique()
        conflicts=t.group_by('game_pk','at_bat_index').len().filter(pl.col('len')>1)
        t=t.join(conflicts.select('game_pk','at_bat_index'),on=['game_pk','at_bat_index'],how='anti')
        result['partition_deduplication'].append(dict(season=year,raw_rows=raw_rows,
            excluded_conflicting_keys=conflicts.height,unique_usable_plays=t.height))
        gb=t.filter((pl.col('bb_type')=='ground_ball')&pl.col('terminal_outcome_group').is_in(
            ['OUT','SF','MULTI_OUT','1B','2B','3B','ROE']))
        gb=gb.with_columns(pl.col('terminal_outcome_group').is_in(['OUT','SF','MULTI_OUT']).alias('is_out'),
            pl.when(pl.col('responsible_position').is_in([4,5,6])).then(pl.lit('2B_3B_SS'))
              .when(pl.col('responsible_position').is_in([7,8,9])).then(pl.lit('outfield'))
              .otherwise(pl.lit('other_or_missing')).alias('first_touch_group'))
        result['fielding'].extend(gb.group_by('season','level','is_out','first_touch_group').agg(
            pl.len().alias('balls'),(pl.col('hc_x').is_not_null()&pl.col('hc_y').is_not_null()).sum().alias('coordinates_present')
            ).sort('season','level','is_out','first_touch_group').to_dicts())
        desc=pl.col('pa_description').fill_null('').str.to_lowercase()
        z=t.filter(~desc.str.contains(r'\b(?:pickoff|picked off)\b')&pl.col('fielder_2').is_not_null()&pl.col('pitcher').is_not_null())
        result['catcher_narratives'].extend(z.group_by('season','level').agg(pl.len().alias('plays'),
            desc.str.contains(r'\bcaught stealing\b').sum().alias('caught_mentions'),
            (desc.str.contains(r'\b(?:steals|stolen base)\b')&~desc.str.contains(r'\bcaught stealing\b')).sum().alias('successful_mentions')
            ).sort('season','level').to_dicts())
    inventory=[]
    for p in sorted(Path('docs').glob('*result*.md')):
        # File inventory only: do not read unsealed 2026 outcome reports.
        inventory.append({'path':str(p),'bytes':p.stat().st_size})
    result['result_document_inventory']=inventory
    result['result_document_inventory_note']='Index only; not a claim of line-by-line audit of every document or archived experiment.'
    assert hashes=={str(p):sha256_file(p) for p in paths}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'diagnostics.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'defense':result['defense_error_interaction'],'opportunity_2021':[x for x in result['opportunity'] if x['origin']==2021],
        'weighting_2021':[x for x in result['weighting'] if x['origin']==2021]},indent=2))


if __name__=='__main__':main()
