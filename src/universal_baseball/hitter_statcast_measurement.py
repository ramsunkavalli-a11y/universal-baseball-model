"""Reviewed historical launch projection, separate from sealed two-year pilot."""
import polars as pl
from universal_baseball.hitter_statcast_history import KEY, annual_launch_features


def interference_award():
    return ((pl.col('events')=='field_error') & pl.col('des').fill_null('')
            .str.to_lowercase().str.contains('reaches on an interference error'))


def project_measurements(raw, season):
    if season not in range(2015,2025):
        raise ValueError('Only declared historical MLB 2015–24 measurements permitted')
    required={'game_date','game_year','game_type','game_pk','batter','pitcher','stand','p_throws',
              'at_bat_number','pitch_number','type','events','des','launch_speed','launch_angle'}
    if required-set(raw.columns): raise ValueError('Missing measurement columns')
    if not raw.is_empty() and (set(raw['game_year'].cast(pl.Int64).unique())!={season}
            or set(raw['game_type'].unique())!={'R'}):
        raise ValueError('Source outside declared season or regular play')
    if raw.unique(['game_pk','batter','at_bat_number']).height!=len(raw):
        raise ValueError('Duplicate terminal PA')
    reason=pl.when((pl.col('type')!='X')|pl.col('events').fill_null('').str.strip_chars().eq(''))
    reason=reason.then(pl.lit('not_terminal_inplay')).when(interference_award()).then(pl.lit('interference_award'))
    reason=reason.when(pl.col('des').fill_null('').str.to_lowercase().str.contains(r'\bbunt\b')).then(pl.lit('bunt'))
    marked=raw.with_columns(reason.otherwise(None).alias('measurement_exclusion'))
    excluded=marked.filter(pl.col('measurement_exclusion').is_not_null())
    q=marked.filter(pl.col('measurement_exclusion').is_null()).select(
        pl.col('game_date').str.to_date(strict=True),pl.lit(season).alias('season'),
        *[pl.col(c).cast(pl.Int64) for c in ['game_pk','at_bat_number','pitch_number']],
        pl.col('batter').cast(pl.Int64).alias('player_id'),pl.col('pitcher').cast(pl.Int64).alias('pitcher_id'),
        pl.col('stand').alias('batter_side'),pl.col('p_throws').alias('pitcher_hand'),'events',
        pl.col('launch_speed').cast(pl.Float64,strict=True),pl.col('launch_angle').cast(pl.Float64,strict=True))
    if q.select(pl.any_horizontal(pl.col(*KEY).is_null()).any()).item(): raise ValueError('Missing identity')
    if len(q) and set(q['game_date'].dt.year().unique())!={season}: raise ValueError('Cross-season date')
    q=q.with_columns(
        (pl.col('launch_speed').is_not_null() & (~pl.col('launch_speed').is_finite()|
            ~pl.col('launch_speed').is_between(0,130))).fill_null(False).alias('invalid_ev'),
        (pl.col('launch_angle').is_not_null() & (~pl.col('launch_angle').is_finite()|
            ~pl.col('launch_angle').is_between(-90,90))).fill_null(False).alias('invalid_la'))
    q=q.with_columns((pl.col('launch_speed').is_not_null()&~pl.col('invalid_ev')).alias('valid_ev'),
        (pl.col('launch_angle').is_not_null()&~pl.col('invalid_la')).alias('valid_la'))
    return q.with_columns((pl.col('valid_ev')&pl.col('valid_la')).alias('complete_pair')).sort(KEY),excluded
