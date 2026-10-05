"""Origin-only audit labels, never learned routing or forecast replacements."""
import polars as pl

STRATA = ['audit_route', 'audit_age_group', 'on_40man', 'audit_major_link',
          'audit_demonstrated_regular', 'audit_top20', 'audit_fresh_top10_college']
DISTANCE = ['age', 'MLB_0_pa', 'AAA_0_pa', 'AA_0_pa', 'last_MLB_work',
            'last_first_team_work', 'scout_rank_score_0', 'draft_rank', 'on_40man']


def tag(f):
    foreign = (pl.col('evidence_foreign_source_present') > 0) & (
        pl.col('last_first_team_known') > 0) & (pl.col('last_MLB_known') == 0)
    return f.with_columns(
        pl.when((pl.col('status_hard_unavailable') > 0) | (pl.col('status_retired') > 0))
          .then(pl.lit('known_unavailable'))
          .when(pl.col('pa_0') > 0).then(pl.lit('current_MLB'))
          .when(pl.col('prior_debut') > 0).then(pl.lit('absent_previous_MLB'))
          .when(foreign).then(pl.lit('foreign_no_MLB'))
          .when(pl.col('AA_0_pa') + pl.col('AAA_0_pa') > 0).then(pl.lit('never_upper'))
          .otherwise(pl.lit('never_other')).alias('audit_route'),
        (pl.col('age') // 5).cast(pl.Int64).alias('audit_age_group'),
        (pl.col('status_major_link') > 0).alias('audit_major_link'),
        (pl.max_horizontal('work_0', 'work_1', 'work_2') >= 400).alias('audit_demonstrated_regular'),
        ((pl.col('scout_listed_0') > 0) & (pl.col('scout_rank_score_0') >= .8)).alias('audit_top20'),
        ((pl.col('draft_known') > 0) & (pl.col('draft_college') > 0)
         & (pl.col('draft_year') == pl.col('origin_year'))
         & pl.col('pick_number').is_between(1, 10)).fill_null(False).alias('audit_fresh_top10_college'))


def counts(train, test):
    broad = train.group_by('audit_route').agg(pl.col('player_id').n_unique().alias('route_people'))
    exact = train.group_by(STRATA).agg(pl.col('player_id').n_unique().alias('stratum_people'))
    return test.select('row_id', *STRATA).join(broad, on='audit_route', how='left', validate='m:1').join(
        exact, on=STRATA, how='left', validate='m:1').with_columns(
            pl.col('route_people', 'stratum_people').fill_null(0))
