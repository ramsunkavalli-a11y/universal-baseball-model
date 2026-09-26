"""Read archived evidence and write audit facts, never new candidate predictions."""
import json
from pathlib import Path
import numpy as np
import polars as pl
from universal_baseball.multiyear_hitter_followup import compare_losses
from universal_baseball.model_decision_audit import batting_identity
from universal_baseball.storage import sha256_file

ART=Path('model_artifacts')
ROOT=ART/'hitter-integrated-opportunity-value-v1-2026-09-25'
ANCHOR=ART/'hitter-anchored-development-v1-2026-09-22/historical-anchors.parquet'
DISPLAY=ART/'hitter-arrival-coherence-v1-2026-09-23/forecast-2026-2031.parquet'
COMP=ART/'multiyear-hitter-components-v1-2026-09-22/component-predictions.parquet'
OUT=ART/'model-decision-audit-v1-2026-09-25'


def comparison(f,target,reference='N'):
    f=f.with_columns(((pl.col('H_'+target)-pl.col('actual_'+target))**2).alias('_h'),
                    ((pl.col(reference+'_'+target)-pl.col('actual_'+target))**2).alias('_r'))
    return compare_losses(f,'_h','_r',draws=4000)


def main():
    files=[ROOT/'predictions.parquet',ROOT/'cumulative-predictions.parquet',ROOT/'score-report.json',ANCHOR,DISPLAY,COMP,
        ART/'historical-projection-state-v1-2026-09-23/states.parquet',
        ART/'hitter-three-year-opportunity-v1-2026-09-22/predictions.parquet',
        ART/'hitter-arrival-value-transfer-v1-2026-09-23/fit-manifest.json',
        ART/'hitter-conditional-workload-v1-2026-09-23/fit-manifest.json',
        Path('scripts/report_hitter_arrival_coherence_v1.py'),Path('scripts/evaluate_hitter_anchored_development_v1.py'),
        Path('src/universal_baseball/hitter_anchored_development.py'),Path('scripts/fit_hitter_arrival_coherence_v1.py'),
        Path('scripts/audit_model_decisions_v1.py'),Path('src/universal_baseball/model_decision_audit.py'),
        Path('src/universal_baseball/hitter_value_panel.py'),Path('src/universal_baseball/multiyear_hitter_value.py'),
        Path('src/universal_baseball/multiyear_hitter_followup.py')]
    hashes={str(p):sha256_file(p) for p in files}
    f=pl.read_parquet(ROOT/'predictions.parquet');c=pl.read_parquet(ROOT/'cumulative-predictions.parquet')
    report=json.loads((ROOT/'score-report.json').read_text())
    a=pl.read_parquet(ANCHOR)
    assert a.filter((pl.col('anchor_cutoff')!=pl.col('origin_year'))|(pl.col('latest_anchor_target')>pl.col('origin_year'))).is_empty()
    joined=f.join(a,on=['origin_year','player_id'],how='left',validate='m:1')
    assert joined['performance_anchor'].null_count()==0
    native=joined['E_pa']*joined['performance_anchor']/600
    np.testing.assert_allclose(native,joined['N_value'],atol=1e-12)
    identities=batting_identity(f['B_value'],f['B_pa'],f['H_pa'],f['rate'])
    np.testing.assert_allclose(identities['marginal'],f['H_value'],atol=1e-12)
    lower=f.filter((pl.col('horizon')==1)&pl.col('prospect')&(pl.col('stage')=='Lower minors'))
    result={'audit_only':True,'new_candidate_scores':False,'new_fits':0,'protected_outcomes_used':False,
        'production_forecasts_changed':False,'source_hashes':hashes,'lower_minor_H1':{
        'rows':lower.height,'players':lower['player_id'].n_unique(),'participants':lower.filter(pl.col('actual_pa')>0).height,
        'participant_players':lower.filter(pl.col('actual_pa')>0)['player_id'].n_unique(),
        'all_origins':comparison(lower,'pa','E'),
        'without2021_diagnostic':comparison(lower.filter(pl.col('origin_year')!=2021),'pa','E')},
        'lower_minor_horizons':{h:g['lower_prospects']['pa']['arms'] for h,g in report['annual'].items()},
        'lower_minor_cumulative':report['cumulative']['lower_prospects']['pa'],
        'comparability':{'N_replays_independent_rate_product':True,'rate_anchor_rows_matched':joined.height,
            'E_N_PA_max_difference':float((f['E_pa']-f['N_pa']).abs().max()),
            'E_N_other_runs_max_difference':float((f['E_other_runs']-f['N_other_runs']).abs().max()),
            'marginal_identity_verified':True},'value_groups':{},'cohort_errors':{}}
    for target in ('value','expanded'):
        z=c.filter(pl.col('complete_components')) if target=='expanded' else c
        result['value_groups'][target]={n:comparison(z.filter(e),target) for n,e in
            [('prospects',pl.col('prospect')),('prior_MLB',pl.col('prior_debut')),('without2021',pl.col('origin_year')!=2021)]}
    for name,ex in [('all',pl.lit(True)),('prospects',pl.col('prospect')),('prior_MLB',pl.col('prior_debut')),
                    ('remaining',~pl.col('prospect')&~pl.col('prior_debut'))]:
        result['cohort_errors'][name]=c.filter(ex).group_by('origin_year').agg(pl.col('actual_pa').sum(),
            *[(pl.col(k+'_pa')-pl.col('actual_pa')).sum().alias(k+'_error') for k in ('D','E','H')]).sort('origin_year').to_dicts()
    result['examples']=c.filter((pl.col('origin_year')==2021)&pl.col('player_name').is_in(
        ['Ezequiel Tovar','Maikel Garcia','Jorbit Vivas','Eddys Leonard'])).select(
        'player_name','actual_pa','H_pa','E_pa','actual_value','H_value','N_value').to_dicts()
    current=pl.read_parquet(DISPLAY);comp=pl.read_parquet(COMP).filter(pl.col('origin_year')==2025)
    result['display']={'package':str(DISPLAY),'players':current.height,
        'full_control_value_missing':current['full_control_value'].null_count(),'horizons':{}}
    for h in range(1,7):
        affected=current.filter(pl.col(f'arrival_repaired_h{h}'))
        ratio=affected[f'expected_pa_h{h}']/affected[f'baseline_pa_h{h}']
        cc=comp.filter((pl.col('horizon')==h)&(pl.col('selected_model')=='direct')).join(
            affected.select('player_id'),on='player_id',how='inner')
        if cc.height:
            scaled=cc.join(affected.select('player_id',
                (pl.col(f'expected_pa_h{h}')/pl.col(f'baseline_pa_h{h}')).alias('_ratio')),on='player_id')
            direct_change=(scaled['selected']*(scaled['_ratio']-1)).abs()
            for component in cc['component'].unique():
                check=scaled.filter(pl.col('component')==component).join(
                    affected.select('player_id',f'{component}_runs_h{h}'),on='player_id',validate='1:1')
                np.testing.assert_allclose(check[f'{component}_runs_h{h}'],
                    check['selected']*check['_ratio'],atol=1e-12)
        else:
            direct_change=pl.Series([],dtype=pl.Float64)
        result['display']['horizons'][str(h)]={'repaired_players':affected.height,
            'ratio_min':float(ratio.min()) if len(ratio) else None,'ratio_max':float(ratio.max()) if len(ratio) else None,
            'selected_direct_component_records_rescaled':cc.height,
            'direct_components':sorted(cc['component'].unique().to_list()),
            'direct_rescaling_sum_absolute_runs':float(direct_change.sum()),
            'direct_rescaling_max_absolute_runs':float(direct_change.max()) if len(direct_change) else None,
            'PA_total':float(current[f'expected_pa_h{h}'].sum()),'batting_total':float(current[f'value_{2025+h}'].sum())}
    # Existing support, not an assumption that older recipes equal newer F/D/E.
    states=pl.read_parquet(files[6]);ensemble=pl.read_parquet(files[7])
    result['nested_support']={'historical_state_rows':states.height,'state_columns':states.columns,
        'state_origins':sorted(states['origin_year'].unique().to_list()),
        'ensemble_origins':sorted(ensemble['origin_year'].unique().to_list()),
        'common_integration_folds':f.select('origin_year','horizon').unique().sort('horizon','origin_year').to_dicts(),
        'rate_anchor_origins':a.group_by('origin_year').agg(pl.len().alias('rows'),pl.col('latest_anchor_target').max()).sort('origin_year').to_dicts()}
    assert hashes=={str(p):sha256_file(p) for p in files}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'audit-evidence.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'matched_rows':joined.height,'display':result['display'],
        'lower_minor':result['lower_minor_H1'],'nested_origins':result['nested_support']['ensemble_origins']},indent=2))


if __name__=='__main__':main()
