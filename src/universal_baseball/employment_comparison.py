"""One matched source correction; original nonemployment evidence is immutable."""
import numpy as np
import polars as pl

FLAGS = ['status_major_link', 'status_minor_agreement', 'status_agreement_unspecified',
    'status_acquisition_only', 'status_released', 'status_employment_unknown',
    'status_employment_conflict', 'status_negative_listing_conflict', 'status_positive_listing_conflict']


def corrected_frame(frame, indicators):
    columns = frame.columns
    j = frame.join(indicators.select('origin_year', 'player_id', 'information_date', *FLAGS),
        on=['origin_year', 'player_id'], how='left', suffix='_corrected', validate='1:1')
    if j['information_date'].null_count() or not (j['information_date'] == j['ctx_information_date']).all():
        raise ValueError('Missing or mismatched dated employment source')
    before = np.where((frame['status_major_link'] > 0) | (frame['on_40man'] > 0) |
                      (frame['status_agreement_unspecified'] > 0), frame['last_first_team_work'], 0.)
    if not np.allclose(before, frame['signed_first_team_work'], atol=1e-12, rtol=0):
        raise ValueError('Original derived employment input does not reconstruct')
    j = j.with_columns([pl.col(n+'_corrected').cast(frame.schema[n]).alias(n) for n in FLAGS])
    j = j.with_columns(pl.when((pl.col('status_major_link') > 0) | (pl.col('on_40man') > 0) |
        (pl.col('status_agreement_unspecified') > 0)).then(pl.col('last_first_team_work')).otherwise(0.).alias('signed_first_team_work'))
    j = j.select(columns)
    unchanged = [n for n in columns if n not in {*FLAGS, 'signed_first_team_work'}]
    if not frame.select(unchanged).equals(j.select(unchanged)):
        raise ValueError('Nonemployment evidence changed')
    return j


def profiles(f):
    return f.with_columns((pl.col('age')//5).cast(pl.Int64).alias('age_group'),
        pl.when(pl.col('pa_0')==0).then(0).when(pl.col('pa_0')<200).then(1).otherwise(2).alias('mlb_exposure'),
        (pl.col('evidence_foreign_source_present')>0).alias('foreign_source'),
        (pl.col('last_first_team_known')>0).alias('first_team_history'),
        pl.when(pl.col('status_major_link')>0).then(pl.lit('major_link'))
          .when(pl.col('status_minor_agreement')>0).then(pl.lit('minor_agreement'))
          .when(pl.col('status_agreement_unspecified')>0).then(pl.lit('unspecified_agreement'))
          .when(pl.col('status_released')>0).then(pl.lit('released'))
          .when(pl.col('status_acquisition_only')>0).then(pl.lit('acquisition'))
          .when(pl.col('status_employment_unknown')>0).then(pl.lit('unknown'))
          .otherwise(pl.lit('other')).alias('employment_category'),
        pl.when(pl.col('status_hard_unavailable')>0).then(3)
          .when(pl.col('status_unresolved_nonmedical')>0).then(2)
          .when(pl.col('status_finite_nonmedical')>0).then(1).otherwise(0).alias('restriction_profile'))


def support(train, test):
    keys = ['prior_debut', 'stage', 'age_group', 'mlb_exposure', 'foreign_source',
            'first_team_history', 'restriction_profile', 'employment_category']
    tr, te = profiles(train), profiles(test)
    counts = tr.group_by(keys).agg(pl.col('player_id').n_unique().alias('profile_people'))
    return te.select('row_id', *keys).join(counts, on=keys, how='left', validate='m:1').with_columns(
        pl.col('profile_people').fill_null(0))
