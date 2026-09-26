"""Complete archived GB accounting, deliberately not a certified range metric."""
import polars as pl
from universal_baseball.pbp_opportunity_events import (
    resolve_overlapping_terminal_plays, build_fielding_opportunities,
)

KEY = ['game_pk', 'at_bat_index']
FIELDS = ['season', 'level', 'league_id', 'game_date', 'game_type', 'batter',
    'pitcher', 'inning', 'inning_top_bot', 'outs_when_up', 'stand', 'p_throws',
    'park_key', 'defense_team', 'bb_type', 'hit_location', 'hc_x', 'hc_y',
    'pa_description', 'terminal_outcome_group', 'terminal_outcome_status',
    *[f'fielder_{p}' for p in range(2, 10)]]


def reconcile_ground_balls(frames):
    """Retain the UNION of GB keys; never pre-filter their conflicting versions."""
    raw = pl.concat(frames, how='diagonal_relaxed')
    if not raw['season'].is_in([2016,2017,2018,2019,2021,2022,2023,2024]).all():
        raise ValueError('Outside locked historical seasons')
    if raw.filter(pl.col('game_type') != 'R').height:
        raise ValueError('Outside regular season')
    keys = raw.filter(pl.col('bb_type') == 'ground_ball').select(KEY).unique()
    versions = raw.join(keys, on=KEY, how='semi')
    # Exact legacy reconstruction is diagnostic only; its unresolved choices stay
    # confined to the legacy columns, not the new consensual measurement.
    legacy = resolve_overlapping_terminal_plays([versions])
    selected = build_fielding_opportunities(legacy).filter(
        (pl.col('bb_type') == 'ground_ball') & pl.col('responsible_position').is_in([4,5,6])
    ).select(KEY).with_columns(pl.lit(True).alias('legacy_456_selected'))
    result = versions.group_by(KEY).agg(
        pl.len().alias('source_row_count'),
        pl.col('source_asset').unique().sort().alias('source_assets'),
        *[pl.when(pl.col(c).drop_nulls().n_unique() <= 1)
            .then(pl.col(c).drop_nulls().first()).otherwise(None).alias(c) for c in FIELDS],
        *[(pl.col(c).drop_nulls().n_unique() > 1).alias(c+'__conflict') for c in FIELDS],
        (pl.col('terminal_outcome_status') == 'unsupported_bunt').any().alias('any_bunt'),
    ).with_columns(pl.concat_list([
        pl.when(pl.col(c+'__conflict')).then(pl.lit(c)).otherwise(None) for c in FIELDS
    ]).list.drop_nulls().alias('conflicting_fields'))
    result = result.drop([c+'__conflict' for c in FIELDS]).with_columns(
        (pl.col('conflicting_fields').list.len() > 0).alias('has_source_conflict'),
        pl.lit(True).alias('ground_ball_in_any_source'),
        pl.col('pitcher').alias('fielder_1'),
        pl.lit(False).alias('individual_range_certified'),
        pl.lit('archived_terminal_not_full_event_certified').alias('lineup_source'),
    ).join(selected,on=KEY,how='left').with_columns(pl.col('legacy_456_selected').fill_null(False))
    assert result.height == keys.height
    return result.sort(KEY)


def add_benchmark(df):
    """Literature-inspired POST-outcome allocation plus unassigned sensitivity."""
    loc=pl.col('hit_location').cast(pl.Int64); out=pl.col('terminal_outcome_group').cast(pl.String)
    clean=(~pl.col('has_source_conflict')) & (~pl.col('any_bunt'))
    touch=clean & loc.is_between(1,6) & out.is_in(['OUT','MULTI_OUT','1B','2B','3B','ROE'])
    single=clean & loc.is_in([7,8,9]) & (out=='1B')
    corner=clean & loc.is_in([7,9]) & out.is_in(['2B','3B'])
    return df.with_columns(
        pl.when(touch).then(loc).when(single).then(loc.replace_strict({7:5,8:6,9:4},default=None))
            .when(corner).then(loc.replace_strict({7:5,9:3},default=None)).otherwise(None).alias('candidate_position_a'),
        pl.when(single).then(loc.replace_strict({7:6,8:4,9:3},default=None)).otherwise(None).alias('candidate_position_b'),
        pl.when(touch).then(pl.lit('observed_IF_touch_not_ex_ante'))
            .when(single).then(pl.lit('assumed_adjacent_single_equal_share'))
            .when(corner).then(pl.lit('assumed_corner_XBH'))
            .when(pl.col('has_source_conflict')).then(pl.lit('unassigned_source_conflict'))
            .when(pl.col('any_bunt')).then(pl.lit('unassigned_bunt'))
            .when(out=='FC_REACH').then(pl.lit('unassigned_FC'))
            .otherwise(pl.lit('unassigned_other')).alias('allocation_basis'),
    ).with_columns(
        pl.when(pl.col('candidate_position_b').is_not_null()).then(.5)
            .when(pl.col('candidate_position_a').is_not_null()).then(1.).otherwise(0.).alias('share_a'),
        pl.when(pl.col('candidate_position_b').is_not_null()).then(.5).otherwise(0.).alias('share_b'),
        pl.when(pl.col('candidate_position_a').is_null()).then(1.).otherwise(0.).alias('unassigned_share'),
        # Inferring a responsibility is not inferring who physically occupied it.
        *[pl.coalesce([pl.when(pl.col('candidate_position_'+slot)==p).then(pl.col(f'fielder_{p}'))
            for p in range(1,10)]).alias('candidate_fielder_'+slot) for slot in ('a','b')],
        pl.when(pl.col('allocation_basis').str.starts_with('assumed_')).then(1.)
            .when(pl.col('candidate_position_a').is_null()).then(1.).otherwise(0.).alias('unassigned_sensitivity_share'),
    ).with_columns(
        ((pl.col('candidate_position_a').is_not_null() & pl.col('candidate_fielder_a').is_null()) |
         (pl.col('candidate_position_b').is_not_null() & pl.col('candidate_fielder_b').is_null())).alias('unknown_candidate_identity'),
    )
