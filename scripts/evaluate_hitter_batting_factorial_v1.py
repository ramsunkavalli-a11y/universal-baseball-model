"""Execute the already declared eight-cell diagnostic; no refitting/selection."""
import argparse
import json
from pathlib import Path
import numpy as np
import polars as pl
from universal_baseball.hitter_batting_factorial import CELLS, assemble_cells, residual_loss_identity
from universal_baseball.hitter_common_weight import paired_mse
from universal_baseball.hitter_integrated_opportunity_value import META, KEY, profiles
from universal_baseball.methodology_review import component_loss_decomposition
from universal_baseball.storage import sha256_file

OUT=Path('model_artifacts/hitter-batting-factorial-v1-2026-09-25')
ROOT=Path('model_artifacts/hitter-integrated-opportunity-value-v1-2026-09-25')
ANCHORS=Path('model_artifacts/hitter-anchored-development-v1-2026-09-22')
NATIVE=Path('model_artifacts/multiyear-hitter-components-v1-2026-09-22/component-predictions.parquet')
OF=Path('reports/generated/milb-outfield-range-hitter-value-v1/predictions.parquet')


def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')


def hashes():
    paths=[Path('docs/hitter-value-factorial-v1-plan.md'),Path(__file__),
        Path('src/universal_baseball/hitter_batting_factorial.py'),Path('src/universal_baseball/hitter_common_weight.py'),
        Path('src/universal_baseball/methodology_review.py'),Path('src/universal_baseball/hitter_integrated_opportunity_value.py'),
        Path('tests/test_hitter_batting_factorial.py'),NATIVE,OF,
        ROOT/'predictions.parquet',ROOT/'cumulative-predictions.parquet',ROOT/'score-report.json',ROOT/'component-predictions.parquet',
        ANCHORS/'historical-anchors.parquet']
    return {str(p):sha256_file(p) for p in paths}


def freeze():
    if (OUT/'prefit.json').exists():raise ValueError('Already sealed')
    for root in (ROOT,ANCHORS):
        m=json.loads((root/'manifest.json').read_text())
        for n,h in m['files'].items():assert sha256_file(root/n)==h
    # Validate original rate/head training cutoffs, not only current data hash.
    m=json.loads(Path('model_artifacts/hitter-arrival-value-transfer-v1-2026-09-23/fit-manifest.json').read_text())
    for note in m['fits']:
        if 'latest_label' in note:assert note['latest_label']<=note.get('year',note.get('origin'))
    save(OUT/'prefit.json',{'hashes':hashes(),'cells':CELLS,'new_fits':0,
        'primary':'H_anchor_product minus E_anchor_product, equal-origin cumulative batting MSE',
        'protected_outcomes_used':False,'production_changed':False})


def summarize(f,target='actual_value',suffix=''):
    if not f.height:return None
    records=[]
    for (year,),g in f.group_by('origin_year'):
        y=g[target].to_numpy();arms={}
        for cell in CELLS:
            pred=g[cell+suffix].to_numpy();err=pred-y
            arms[cell]={'mse':float(np.mean(err**2)),'mae':float(np.mean(abs(err))),
                'bias':float(err.mean()),'predicted_total':float(pred.sum()),'actual_total':float(y.sum())}
        records.append({'origin':year,'rows':g.height,'participants':int((g['actual_pa']>0).sum()),'arms':arms})
    result={'rows':f.height,'unique_players':f['player_id'].n_unique(),'participants':int((f['actual_pa']>0).sum()),
        'by_origin':sorted(records,key=lambda r:r['origin']),
        'arms':{cell:{k:float(np.mean([r['arms'][cell][k] for r in records])) for k in ('mse','mae','bias')}
            for cell in CELLS}}
    for arm in result['arms'].values():arm['rmse']=arm['mse']**.5
    return result


def contrast(f,left,right):
    return {'equal_origin_mse_delta':float(f.group_by('origin_year').agg(
        (((pl.col(left)-pl.col('actual_value'))**2)-((pl.col(right)-pl.col('actual_value'))**2)).mean().alias('d'))['d'].mean())}


def run():
    pre=json.loads((OUT/'prefit.json').read_text());assert pre['hashes']==hashes()
    f=pl.read_parquet(ROOT/'predictions.parquet');assert f.height==52181
    a=pl.read_parquet(ANCHORS/'historical-anchors.parquet')
    assert a.filter((pl.col('anchor_cutoff')!=pl.col('origin_year'))|(pl.col('latest_anchor_target')>pl.col('origin_year'))).is_empty()
    f=f.join(a,on=['origin_year','player_id'],how='left',validate='m:1')
    assert not f.select(KEY).is_duplicated().any() and (f['origin_year']+f['horizon']).max()<=2025
    f=assemble_cells(f)
    for cell,old in [('E_anchor_product','N'),('H_horizon_marginal','H'),('E_horizon_marginal','E')]:
        np.testing.assert_allclose(f[cell],f[old+'_value'],atol=1e-12,rtol=0)
        np.testing.assert_allclose(f[cell+'_expanded'],f[old+'_expanded'],atol=1e-12,rtol=0)
    forecast_cols=[n+s for n in CELLS for s in ('','_expanded')]
    changed=assemble_cells(f.with_columns(pl.lit(999.).alias('actual_value')))
    assert f.select(forecast_cols).equals(changed.select(forecast_cols))
    c=f.group_by('origin_year','player_id').agg(pl.len().alias('_n'),pl.col('horizon').n_unique().alias('_nh'),
        pl.col('complete_components').all(),*[pl.col(k).first() for k in [*META,'player_name']],
        *[pl.col(k).sum() for k in ['actual_pa','actual_value','actual_expanded',*forecast_cols,'E_other_runs','H_other_runs']]
        ).filter((pl.col('_n')==3)&(pl.col('_nh')==3)).with_columns(
            pl.when(pl.col('complete_components')).then(pl.col('actual_expanded')).otherwise(None).alias('actual_expanded')
        ).sort('origin_year','player_id')
    assert c.height==12891 and c.filter(pl.col('complete_components')).height==8308
    f.write_parquet(OUT/'predictions.parquet');c.write_parquet(OUT/'cumulative.parquet')
    groups={**profiles(),'remaining':~pl.col('prospect')&~pl.col('prior_debut')}
    report={'primary':paired_mse(c,'H_anchor_product','E_anchor_product','actual_value'),
        'primary_without2021_sensitivity':paired_mse(c.filter(pl.col('origin_year')!=2021),'H_anchor_product','E_anchor_product','actual_value'),
        'annual':{},'cumulative':{},'expanded_cumulative':{},'secondary_contrasts':{},'residual_decomposition':[],
        'new_fits':0,'protected_outcomes_used':False,'production_changed':False,'candidate_selected':False}
    for h in (1,2,3):
        q=f.filter(pl.col('horizon')==h)
        report['annual'][str(h)]={n:summarize(q.filter(e)) for n,e in groups.items()}
    report['cumulative']={n:summarize(c.filter(e)) for n,e in groups.items()}
    report['expanded_cumulative']={n:summarize(c.filter(e&pl.col('complete_components')),'actual_expanded','_expanded') for n,e in groups.items()}
    for r in ('anchor','horizon'):
        for assembly in ('product','marginal'):
            report['secondary_contrasts'][f'workload_{r}_{assembly}']=contrast(c,f'H_{r}_{assembly}',f'E_{r}_{assembly}')
    for w in ('E','H'):
        for r in ('anchor','horizon'):
            report['secondary_contrasts'][f'assembly_{w}_{r}']=contrast(c,f'{w}_{r}_marginal',f'{w}_{r}_product')
            for (year,),g in c.group_by('origin_year'):
                report['residual_decomposition'].append({'workload':w,'rate':r,'origin':year,
                    **residual_loss_identity(g[f'{w}_{r}_product'],g[f'{w}_{r}_marginal'],g['actual_value'])})
        for assembly in ('product','marginal'):
            report['secondary_contrasts'][f'rate_{w}_{assembly}']=contrast(c,f'{w}_horizon_{assembly}',f'{w}_anchor_{assembly}')
    contrasts=report['secondary_contrasts']
    report['loss_interactions']={r:contrasts[f'workload_{r}_marginal']['equal_origin_mse_delta']-
        contrasts[f'workload_{r}_product']['equal_origin_mse_delta'] for r in ('anchor','horizon')}
    ex=c.with_columns((((pl.col('H_anchor_product')-pl.col('actual_value'))**2)-
        ((pl.col('E_anchor_product')-pl.col('actual_value'))**2)).alias('error_change'))
    report['largest_absolute_error_changes']={str(y):g.with_columns(pl.col('error_change').abs().alias('_abs')).sort('_abs',descending=True).head(10).select(
        'origin_year','player_id','player_name','stage','age','prospect','prior_debut','mlb_pa_lag0','pa_lag0',
        'actual_pa','actual_value','H_anchor_product','E_anchor_product','error_change').to_dicts() for (y,),g in ex.group_by('origin_year')}
    report['induced_nonbatting_rate_head_change']=c.group_by('origin_year').agg(
        (pl.col('H_other_runs')-pl.col('E_other_runs')).sum().alias('total_runs_change'),
        (pl.col('H_other_runs')-pl.col('E_other_runs')).abs().mean().alias('mean_absolute_runs_change')).sort('origin_year').to_dicts()
    # Current component additions versus omission, holding all other predictions fixed.
    components=pl.read_parquet(ROOT/'component-predictions.parquet')
    native=pl.read_parquet(NATIVE).select(*KEY,'component','actual')
    comp=components.join(native,on=[*KEY,'component'],validate='1:1').join(
        f.select(*KEY,'actual_expanded','H_expanded','complete_components'),on=KEY,validate='m:1').filter(pl.col('complete_components'))
    rows=[]
    for (name,year,h),g in comp.group_by('component','origin_year','horizon'):
        pred=g['H_runs'].to_numpy()/10;actual=g['actual'].to_numpy()/10
        for scope,mask in [('all',np.ones(g.height,bool)),('changed',pred!=0),('unchanged',pred==0)]:
            if not mask.any():continue
            rows.append({'component':name,'origin':year,'horizon':h,'scope':scope,'rows':int(mask.sum()),
                **component_loss_decomposition(g['H_expanded'].to_numpy()[mask]-pred[mask],
                    g['actual_expanded'].to_numpy()[mask]-actual[mask],pred[mask],actual[mask])})
    report['component_addition_decomposition']=rows
    # Earlier OF bridge: isolate replacement-specific gain, not the retained arm.
    of=pl.read_parquet(OF);new=of['prediction_outfield_rebuilt_war'].to_numpy();old=of['prediction_general_defense_war'].to_numpy()
    report['outfield_replacement_decomposition']=[]
    for scope,mask in [('all',np.ones(of.height,bool)),('changed',abs(new-old)>1e-12),('unchanged',abs(new-old)<=1e-12)]:
        if not mask.any():continue
        # Treat new-minus-old as the addition and actual-minus-old as its target.
        report['outfield_replacement_decomposition'].append({'scope':scope,'rows':int(mask.sum()),
            **component_loss_decomposition(of['prediction_without_general_defense_war'].to_numpy()[mask],
                (of['actual_partial_war_with_general_defense']-of['actual_general_defense_war']).to_numpy()[mask],
                (new-old)[mask],(of['actual_general_defense_war'].to_numpy()-old)[mask])})
    report['hashes']={n:sha256_file(OUT/n) for n in ('predictions.parquet','cumulative.parquet','prefit.json')}
    assert pre['hashes']==hashes()
    save(OUT/'report.json',report)
    print(json.dumps({'primary':report['primary'],'cells':report['cumulative']['all']['arms'],
        'outfield_replacement':report['outfield_replacement_decomposition']},indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['freeze','run']);args=ap.parse_args()
    {'freeze':freeze,'run':run}[args.mode]()
