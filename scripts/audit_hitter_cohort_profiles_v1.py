"""Audit existing predictions; no new fitting and no deployed model changes."""
import json
from pathlib import Path
import numpy as np
import polars as pl
from fit_hitter_arrival_coherence_v1 import save
from universal_baseball.hitter_cohort_profile_audit import cohort,decompose,profiles,describe,PATH
from universal_baseball.hitter_talent_workload import pedigree_features,PEDIGREE
from universal_baseball.storage import sha256_file

OUT=Path('reports/generated/hitter-cohort-profile-audit-v1')
PANEL=Path('reports/generated/hitter-arrival-source-repair-v1/repaired-panel.parquet')
PA=Path('model_artifacts/hitter-conditional-workload-v1-2026-09-23/predictions.parquet')
BASE=Path('model_artifacts/hitter-arrival-value-transfer-v1-2026-09-23/predictions.parquet')
ARRIVAL=Path('reports/generated/hitter-arrival-source-repair-v1/predictions.parquet')
TALENT=Path('model_artifacts/hitter-talent-workload-v1-2026-09-23/nested-talent.parquet')
DRAFT=Path('model_artifacts/hitter-talent-workload-v1-2026-09-23/draft-evidence.parquet')


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    paths=[PANEL,PA,BASE,ARRIVAL,TALENT,DRAFT,Path(__file__),
        Path('src/universal_baseball/hitter_cohort_profile_audit.py'),Path('docs/hitter-cohort-profile-audit-v1-plan.md')]
    hashes={str(p):sha256_file(p) for p in paths}
    panel=pl.read_parquet(PANEL);panel=pedigree_features(panel,pl.read_parquet(DRAFT))
    talent=pl.read_parquet(TALENT)
    panel=panel.join(talent,on=['origin_year','player_id'],how='left',validate='1:1',maintain_order='left')
    ranks=panel.filter(pl.col('prospect')&pl.col('talent_rate_h1').is_finite()).select('origin_year','player_id','talent_rate_h1')
    ranks=ranks.with_columns((((pl.col('talent_rate_h1').rank('ordinal').over('origin_year')-1)*5/pl.len().over('origin_year')).floor()+1)
        .cast(pl.Int8).alias('talent_quintile')).select('origin_year','player_id','talent_quintile')
    panel=cohort(panel.join(ranks,on=['origin_year','player_id'],how='left',validate='1:1'))
    # Draft extract stops at 2022: later-year matching would misclassify new draftees.
    # Do not diagnose later draft/talent bins where source support is absent.
    panel=panel.with_columns(*[pl.when(pl.col('origin_year')>2022).then(None).otherwise(pl.col(c)).alias(c) for c in PEDIGREE])
    pa=pl.read_parquet(PA);base=pl.read_parquet(BASE).select('origin_year','player_id','horizon','B_p')
    pa=pa.join(base,on=['origin_year','player_id','horizon'],validate='1:1',maintain_order='left')
    pa=pa.with_columns(pl.when(pl.col('prospect')).then(pl.col('fixed_p')).otherwise(pl.col('B_p')).alias('probability'),
        pl.when(pl.col('prospect')).then(pl.col('D_conditional')).otherwise(pl.col('I_conditional')).alias('conditional'))
    extra=[c for c in panel.columns if c not in pa.columns and not c.startswith(('pa_h','war_h','complete_h'))]
    pa=cohort(pa.join(panel.select('origin_year','player_id',*extra),on=['origin_year','player_id'],validate='m:1',maintain_order='left'))
    pa=decompose(pa)
    np.testing.assert_allclose(pa['expected_pa'],pa['D_pa'],rtol=1e-12,atol=1e-12)
    np.testing.assert_allclose(pa['pa_error'],pa['participation_pa_error']+pa['workload_pa_error'],rtol=1e-12,atol=1e-12)
    groups=profiles();report={'annual':{},'annual_participation':{},'hashes':hashes,
        'model':'research F/D for prospects, B for others','protected_outcomes_used':False,'forecasts_changed':False}
    for h in (1,2,3):
        q=pa.filter(pl.col('horizon')==h)
        report['annual'][str(h)]={n:describe(q.filter(e)) for n,e in groups.items()}
    first=pa.filter((pl.col('horizon')==1)&pl.col('prospect')).select('origin_year','player_id','probability','active')
    recent=pl.read_parquet(ARRIVAL).filter((pl.col('arm')=='F')&(pl.col('target')=='next_year')&pl.col('prospect')&
        pl.col('origin_year').is_in([2023,2024])).select('origin_year','player_id','probability',pl.col('actual').cast(pl.Int64).alias('active'))
    first=pl.concat([first,recent],how='vertical_relaxed').join(panel,on=['origin_year','player_id'],validate='1:1',maintain_order='left')
    np.testing.assert_array_equal(first['active'],(first['pa_h1']>0).cast(pl.Int64))
    report['annual_participation']={n:describe(first.filter(e),False) for n,e in groups.items()}
    keys=['player_name','age','stage','audit_cohort','prospect','prior_debut','minor_returner','recent_debut','mlb_pa_lag0',
          'level','pa_lag0','on_40man','raw0__available','league_mexican_pa_share_lag0',*PEDIGREE,'talent_quintile',
          'strikeout_rate_lag0','home_run_rate_lag0','ubb_rate_lag0',*[c for c in panel.columns if c.startswith(PATH)],'path0__available']
    c=pa.group_by('origin_year','player_id').agg(pl.len().alias('_n'),pl.col('horizon').n_unique().alias('_nh'),
        *[pl.col(k).first() for k in keys],*[pl.col(k).sum() for k in ('actual_pa','expected_pa','probability','active','pa_error','participation_pa_error','workload_pa_error')])\
        .filter((pl.col('_n')==3)&(pl.col('_nh')==3))
    # For cumulative summaries, active is participant-seasons, not ever-arrival.
    report['cumulative']={}
    for n,e in groups.items():
        g=c.filter(e)
        if not g.height:report['cumulative'][n]=None;continue
        totals=g.group_by('origin_year').agg(pl.len().alias('rows'),
            *[pl.col(k).sum() for k in ('actual_pa','expected_pa','pa_error','participation_pa_error','workload_pa_error')],
            (pl.col('pa_error')**2).mean().sqrt().alias('rmse'),pl.col('pa_error').mean().alias('bias')).sort('origin_year')
        report['cumulative'][n]=totals.to_dicts()
    selection=['origin_year','player_id','player_name','horizon','audit_cohort','level','age','on_40man',
        'probability','conditional','expected_pa','actual_pa','pa_error','participation_pa_error','workload_pa_error',
        'pa_lag0','strikeout_rate_lag0','home_run_rate_lag0','talent_rate_h1']
    examples={}
    for h in (1,2,3):
        q=pa.filter(pl.col('horizon')==h)
        for subset,condition in [('all',pl.lit(True)),('non2021',pl.col('origin_year')!=2021),('2021',pl.col('origin_year')==2021)]:
            z=q.filter(condition)
            examples[f'{h}/{subset}']={'under':z.sort('pa_error',descending=True).select(selection).head(20).to_dicts(),
                'over':z.sort('pa_error').select(selection).head(20).to_dicts()}
    save(OUT/'examples.json',examples)
    pa.select(*selection,'prospect','prior_debut','minor_returner','recent_debut','active','B_pa','D_pa').write_parquet(OUT/'audited-predictions.parquet')
    save(OUT/'report.json',report)
    assert hashes=={str(p):sha256_file(p) for p in paths}
    print(json.dumps({'rows':pa.height,'profiles':len(groups),'annual_origins':sorted(first['origin_year'].unique()),
        'prediction_changes':False,'h1_recurring':{n:g['non2021_equal_origin_bias'] for n,g in report['annual']['1'].items() if g and g['descriptive_flag']}}))


if __name__=='__main__':main()
