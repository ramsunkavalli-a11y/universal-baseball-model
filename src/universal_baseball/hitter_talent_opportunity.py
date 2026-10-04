"""Rolling, whole-player separated inputs for a talent-to-opportunity test."""
import polars as pl

MIN_ROWS = 200
MIN_PEOPLE = 100
MIN_ORIGINS = 2


def rate_membership(outer_training, origin, held_fold):
    train = outer_training.filter((pl.col('target_year') <= origin) &
        (pl.col('target_year') != 2020) & (pl.col('outer_fold') != held_fold) &
        (pl.col('next_pa') > 0)).sort('row_id')
    return train


def estimable(train):
    return (len(train) >= MIN_ROWS and train['player_id'].n_unique() >= MIN_PEOPLE
            and train['origin_year'].n_unique() >= MIN_ORIGINS)


def profile_counts(train, test, tagged):
    keys = ['prior_debut', 'stage', 'age_band', 'rank_band', 'new_draftee', 'thin_pro']
    counts = tagged(train).group_by(keys).agg(pl.col('player_id').n_unique().alias('profile_people'))
    return tagged(test).select('row_id', *keys).join(counts, on=keys, how='left',
        validate='m:1').with_columns(pl.col('profile_people').fill_null(0))
