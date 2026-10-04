"""Certified annual follow-up without imputing censored outcomes or batting talent."""
import polars as pl


def annual_followup(origins, targets, complete_seasons, max_horizon=6):
    if set(complete_seasons) != set(range(2009, 2026)):
        raise ValueError('Incomplete or protected outcome inventory')
    if origins.unique('row_id').height != origins.height or origins.unique(['player_id', 'origin_year']).height != origins.height:
        raise ValueError('Duplicate origin identities')
    if origins['origin_year'].max() > 2024 or targets['season'].max() > 2025:
        raise ValueError('Protected season')
    if targets.unique(['season', 'player_id']).height != targets.height:
        raise ValueError('Duplicate MLB outcomes')
    if max_horizon not in range(1, 7):
        raise ValueError('Invalid calendar horizon')
    env = targets.select('season', 'league_pa', 'schedule_fraction').unique()
    if env.unique('season').height != env.height or set(env['season']) != set(complete_seasons):
        raise ValueError('Conflicting or missing season environments')
    env = env.with_columns((570*pl.col('schedule_fraction')/pl.col('league_pa')).alias('replacement_per_pa'))
    # Do not join outcome-bearing columns into the origin feature table.
    annual = pl.concat([origins.select('row_id', 'player_id', 'origin_year', 'outer_fold').with_columns(
        pl.lit(h).alias('followup_year'), (pl.col('origin_year')+h).alias('season'))
        for h in range(1, max_horizon+1)])
    annual = annual.join(env, on='season', how='left', validate='m:1').join(
        targets.select('season', 'player_id', 'mlb_pa', 'component_war'),
        on=['season', 'player_id'], how='left', validate='m:1')
    annual = annual.with_columns(pl.col('season').is_in(complete_seasons).alias('observed'))
    annual = annual.with_columns(
        pl.when(pl.col('observed')).then(pl.col('mlb_pa').fill_null(0)).otherwise(None).alias('mlb_pa'),
        pl.when(pl.col('observed')).then(pl.col('component_war').fill_null(0)).otherwise(None).alias('component_value'))
    return annual.with_columns(
        pl.when(pl.col('mlb_pa')>0).then(600*(pl.col('component_value')-
            pl.col('replacement_per_pa')*pl.col('mlb_pa'))/pl.col('mlb_pa')).otherwise(None).alias('batting_rate'),
        (pl.col('observed') & (pl.col('season')!=2020)).alias('rate_training_eligible')).drop('component_war').sort('row_id', 'followup_year')


def support_membership(annual, cutoff, held_fold, max_horizon, cumulative=False):
    """Completed annual labels, or fully completed cumulative windows only."""
    cond = ((pl.col('followup_year')<=max_horizon) & (pl.col('season')<=cutoff) &
            (pl.col('outer_fold')!=held_fold) & pl.col('rate_training_eligible'))
    if cumulative:
        cond &= pl.col('origin_year')+max_horizon<=cutoff
    return annual.filter(cond)
