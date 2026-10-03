"""Deterministic prospect features for smooth cross-profile partial pooling."""
import numpy as np
import polars as pl
from universal_baseball.hitter_numeric_history import BUCKETS
from universal_baseball.practical_hitter_v30 import EVENTS


def materialize(source):
    basic=['age_centered','age_squared','age_unknown','on_40man','reorganized','last_stat_gap',
        *[f'position_{p}' for p in [1,2,3,4,5,6,7,8,9,10,'Y','UNKNOWN']],
        *[f'milb_canceled_{k}' for k in range(3)],
        'draft_known','draft_rank','draft_elapsed','draft_hs','draft_jc','draft_college',
        'draft_class_unknown','draft_rank_low_exposure',
        *[f'{stem}_{k}' for k in range(3) for stem in ['scout_list_available','scout_listed','scout_rank_score','role_minor']]]
    names=basic.copy();expr=[]
    for b in BUCKETS:
        name=f'log_pool_{b}';expr.append((pl.col(f'pooled_{b}_pa')/100+1).log().alias(name));names.append(name)
        names.extend(f'pooled_{b}_{ev}' for ev in EVENTS)
    for k in range(3):
        for stem in ['minor_pa','games_minor']:
            name=f'log_{stem}_{k}';expr.append((pl.col(f'{stem}_{k}')/100+1).log().alias(name));names.append(name)
    # Small upper-level fill-in samples are not silently called terminal jobs.
    # Separate log exposure helps distinguish one PA from a substantial stint.
    categories={'AAA':['AAA'],'AA':['AA'],'Aplus':['Aplus'],'A':['A'],'short':['Aminus'],
        'complex':['RK120','RK121','RK124','RK128','RK134','RKother'],'DSL':['DSL'],'MEX':['MEX']}
    highest=pl.lit('none')
    # Highest known affiliated level, with MEX kept as its own uncertain category.
    for label in reversed(list(categories)):
        present=pl.sum_horizontal([pl.col(f'{b}_0_pa') for b in categories[label]])>0
        highest=pl.when(present).then(pl.lit(label)).otherwise(highest)
    source=source.with_columns(expr).with_columns(highest.alias('known_highest_current'))
    for label in [*categories,'none']:
        name='highest_'+label;names.append(name)
        source=source.with_columns((pl.col('known_highest_current')==label).cast(pl.Float64).alias(name))
    upper=pl.sum_horizontal('highest_AAA','highest_AA')
    source=source.with_columns((pl.col('draft_rank')*upper).alias('draft_upper_interaction'),
        (pl.col('age_centered')*upper).alias('age_upper_interaction'),
        (pl.col('draft_rank')/(1+10*pl.col('draft_elapsed'))).alias('recent_draft_rank'))
    names+=['draft_upper_interaction','age_upper_interaction','recent_draft_rank']
    assert len(names)==len(set(names)) and not any(c.startswith('next_') for c in names)
    assert np.isfinite(source.select(names).to_numpy()).all()
    return source,names
