"""One declared employment-recency interaction, without changing source facts."""
import numpy as np
import polars as pl

OLD = 'employment_evidence_age_years'
NEW = 'unlinked_employment_age_years'


def transform(frame):
    age = frame[OLD].to_numpy()
    link = frame['status_major_link'].to_numpy()
    if not np.isfinite(age).all() or (age < 0).any() or not np.isin(link, [0, 1]).all():
        raise ValueError('Finite nonnegative record age and binary source linkage required')
    return frame.with_columns(pl.Series(NEW, age * (1 - link)))


def feature_names(names):
    if names.count(OLD) != 1 or NEW in names or len(set(names)) != len(names):
        raise ValueError('Exactly one ordered age replacement required')
    return [NEW if n == OLD else n for n in names]


def profiles(frame):
    return frame.with_columns((pl.col('age') // 5).cast(pl.Int64).alias('continuity_age_band'),
        (pl.max_horizontal('work_1', 'work_2') >= 400).alias('prior_regular_evidence'),
        (pl.col('pa_0') > 0).alias('current_MLB_present'),
        (pl.col('obs_status_unresolved_nonmedical') > 0).alias('unresolved_observation'))


PROFILE_KEYS = ['continuity_age_band', 'prior_regular_evidence', 'current_MLB_present',
                'status_major_link', 'unresolved_observation']


def support(train, test):
    a, b = profiles(train), profiles(test)
    counts = a.group_by(PROFILE_KEYS).agg(pl.col('player_id').n_unique().alias('continuity_people'))
    return b.select('row_id', *PROFILE_KEYS).join(counts, on=PROFILE_KEYS, how='left', validate='m:1').with_columns(
        pl.col('continuity_people').fill_null(0))
