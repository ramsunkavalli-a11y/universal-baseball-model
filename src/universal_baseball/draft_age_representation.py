"""Cutoff-known approximate draft age; never impute schooling from default age."""
import polars as pl

REMOVED = ['draft_hs', 'draft_jc', 'draft_college', 'draft_class_unknown']
ADDED = ['draft_age_known', 'draft_age_centered', 'draft_age_low_exposure']


def materialize(frame):
    age = pl.col('age') - (pl.col('origin_year') - pl.col('draft_year'))
    known = (pl.col('draft_known') == 1) & (pl.col('age_unknown') == 0)
    known = known & pl.col('draft_year').is_not_null()
    f = frame.with_columns(
        known.cast(pl.Int64).alias('draft_age_known'),
        pl.when(known).then(age).otherwise(None).alias('draft_age_proxy'),
        pl.sum_horizontal([pl.col(f'{b}_{lag}_pa') for b in
            ['MLB','AAA','AA','Aplus','A','Aminus','DSL','RK120','RK121',
             'RK124','RK128','RK134','RKother','MEX'] for lag in range(3)]).alias('recent_all_pa'))
    return f.with_columns(
        pl.when(pl.col('draft_age_known') == 1).then((pl.col('draft_age_proxy')-21)/5)
        .otherwise(0.).alias('draft_age_centered')).with_columns(
        (pl.col('draft_age_centered')*pl.col('draft_rank_low_exposure')).alias('draft_age_low_exposure'))
