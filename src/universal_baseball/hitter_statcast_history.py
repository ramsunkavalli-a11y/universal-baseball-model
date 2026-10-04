"""Raw historical launch measurements, not adjusted talent or forecasts."""
import polars as pl
from universal_baseball.current_talent_batted_ball_quality import project_complete_tracked_bbe

KEY = ['game_pk', 'player_id', 'at_bat_number', 'pitch_number']


def project_launch_history(raw: pl.DataFrame, season: int) -> pl.DataFrame:
    """Keep terminal non-bunt contacts, including missing launch measurements."""
    if season not in (2023, 2024):
        raise ValueError('This cached-source receipt permits 2023 and 2024 only')
    required = ['game_date', 'game_year', 'game_type', 'game_pk', 'batter',
                'at_bat_number', 'pitch_number', 'type', 'events', 'des',
                'launch_speed', 'launch_angle']
    missing = set(required)-set(raw.columns)
    if missing:
        raise ValueError(f'Missing launch source columns: {sorted(missing)}')
    regular = raw.filter(pl.col('game_type') == 'R')
    if not regular.is_empty() and set(regular['game_year'].cast(pl.Int64).unique()) != {season}:
        raise ValueError('Source crosses declared season')
    q = regular.filter(
        (pl.col('type').str.strip_chars().str.to_uppercase() == 'X') &
        pl.col('events').fill_null('').str.strip_chars().ne('') &
        ~pl.col('des').fill_null('').str.to_lowercase().str.contains(r'\bbunt\b')
    ).select(
        pl.col('game_date').str.to_date(strict=True), pl.lit(season).alias('season'),
        *[pl.col(c).cast(pl.Int64) for c in ['game_pk', 'at_bat_number', 'pitch_number']],
        pl.col('batter').cast(pl.Int64).alias('player_id'), 'events',
        pl.col('launch_speed').cast(pl.Float64, strict=True),
        pl.col('launch_angle').cast(pl.Float64, strict=True))
    if q.select(pl.any_horizontal(pl.col(*KEY).is_null()).any()).item():
        raise ValueError('Missing terminal contact identity')
    if q.unique(KEY).height != len(q) or q.unique(KEY[:-1]).height != len(q):
        raise ValueError('Duplicate or multiple terminal contacts in one PA')
    if len(q) and set(q['game_date'].dt.year().unique()) != {season}:
        raise ValueError('Terminal contact date crosses season')
    # Values are preserved, not clipped or silently converted to missing.
    q = q.with_columns(
        (pl.col('launch_speed').is_not_null() &
         (~pl.col('launch_speed').is_finite() | ~pl.col('launch_speed').is_between(0, 130))).fill_null(False).alias('invalid_ev'),
        (pl.col('launch_angle').is_not_null() &
         (~pl.col('launch_angle').is_finite() | ~pl.col('launch_angle').is_between(-90, 90))).fill_null(False).alias('invalid_la'))
    q = q.with_columns(
        (pl.col('launch_speed').is_not_null() & ~pl.col('invalid_ev')).alias('valid_ev'),
        (pl.col('launch_angle').is_not_null() & ~pl.col('invalid_la')).alias('valid_la'))
    q = q.with_columns((pl.col('valid_ev') & pl.col('valid_la')).alias('complete_pair'))
    # The old canonical projector must agree on the accepted complete subset.
    complete = project_complete_tracked_bbe(regular)
    valid = complete.filter(pl.col('launch_speed').is_finite() & pl.col('launch_speed').is_between(0, 130) &
                            pl.col('launch_angle').is_finite() & pl.col('launch_angle').is_between(-90, 90))
    expected = q.filter(pl.col('complete_pair')).select(*KEY, 'launch_speed', 'launch_angle').sort(KEY)
    if not expected.equals(valid.select(expected.columns).sort(KEY)):
        raise ValueError('Canonical launch projection mismatch')
    return q.sort(KEY)


def annual_launch_features(q: pl.DataFrame) -> pl.DataFrame:
    """Unshrunk source summaries; null statistics mean no measurement."""
    ev = pl.col('launch_speed').filter(pl.col('valid_ev'))
    la = pl.col('launch_angle').filter(pl.col('valid_la'))
    out = q.group_by('season', 'player_id').agg(
        pl.len().alias('terminal_nonbunt_contacts'),
        pl.col('valid_ev').sum().alias('measured_ev_contacts'),
        pl.col('valid_la').sum().alias('measured_la_contacts'),
        pl.col('complete_pair').sum().alias('measured_pair_contacts'),
        pl.col('invalid_ev').sum().alias('invalid_ev_contacts'),
        pl.col('invalid_la').sum().alias('invalid_la_contacts'),
        ev.mean().alias('mean_ev'), ev.quantile(.95, interpolation='linear').alias('ev95'),
        (ev >= 95).mean().alias('hard_hit_fraction'),
        la.mean().alias('mean_la'), la.std(ddof=1).alias('la_sd'),
        la.is_between(8, 32).mean().alias('sweet_spot_fraction'),
        (pl.col('complete_pair') & (pl.col('launch_speed') >= 95) &
         pl.col('launch_angle').is_between(8, 32)).fill_null(False).sum().alias('hard_sweet_spot_contacts'),
        (pl.col('complete_pair') & (pl.col('launch_speed') >= 95) &
         pl.col('launch_angle').is_between(8, 50)).fill_null(False).sum().alias('hard_air_contacts'),
        pl.col('game_date').min().alias('first_date'), pl.col('game_date').max().alias('last_date'))
    return out.with_columns(
        (pl.col('measured_pair_contacts')/pl.col('terminal_nonbunt_contacts')).alias('pair_coverage'),
        pl.when(pl.col('measured_pair_contacts') > 0)
        .then(pl.col('hard_air_contacts')/pl.col('measured_pair_contacts'))
        .otherwise(None).alias('hard_air_fraction')).sort('season', 'player_id')
