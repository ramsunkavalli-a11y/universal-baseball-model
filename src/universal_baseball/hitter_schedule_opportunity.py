"""Dated schedule exposure, never an individual medical/roster-availability label."""
import polars as pl

FEATURES = ['minor_schedule_coverage', 'minor_pa_per_team_game', 'minor_effective_team_games']


def completed_teams(payload, season, sport):
    if not 2007 <= season <= 2024:
        raise ValueError('Historical development schedules only')
    games = {}
    for day in payload.get('dates', []):
        for g in day.get('games', []):
            if g.get('gameType') != 'R' or g.get('status', {}).get('codedGameState') != 'F':
                continue
            # Some same-sport foreign leagues use split-season labels (2018.1).
            # Keep the calendar-year key; downstream joins retain only our teams.
            if int(str(g.get('season', season)).split('.')[0]) != season:
                raise ValueError('Wrong season')
            if g.get('officialDate') and not g['officialDate'].startswith(str(season)+'-'):
                raise ValueError('Game outside calendar year')
            # A resumed/suspended listing may duplicate a game: count its ID once.
            pair = tuple(sorted(int(g['teams'][s]['team']['id']) for s in ('home', 'away')))
            if pair[0] == pair[1]:
                raise ValueError('Same team on both sides')
            pk = int(g['gamePk'])
            if pk in games and games[pk] != pair:
                raise ValueError('Conflicting game teams')
            games[pk] = pair
    counts = {}
    for pair in games.values():
        for team in pair:
            counts[team] = counts.get(team, 0) + 1
    return [{'season':season, 'sport_id':sport, 'team_id':team, 'team_games':n}
            for team,n in sorted(counts.items())]


def schedule_features(stats, teams):
    keys = ['season','sport_id','team_id']
    if teams.unique(keys).height != teams.height or teams.filter(pl.col('team_games') <= 0).height:
        raise ValueError('Invalid team schedules')
    if stats.unique(keys+['player_id']).height != stats.height:
        raise ValueError('Duplicate batting stint')
    s = stats.filter((pl.col('sport_id') != 1) & (pl.col('plate_appearances') > 0))
    s = s.join(teams, on=keys, how='left', validate='m:1')
    result = s.group_by('season','player_id').agg(
        pl.col('plate_appearances').sum().alias('minor_pa'),
        pl.when(pl.col('team_games').is_not_null()).then(pl.col('plate_appearances')).otherwise(0).sum().alias('covered_pa'),
        (pl.col('plate_appearances') / pl.col('team_games')).sum().alias('fraction'),
    ).with_columns((pl.col('covered_pa')/pl.col('minor_pa')).alias(FEATURES[0]))
    complete = (pl.col('covered_pa') == pl.col('minor_pa')) & (pl.col('fraction') > 0)
    return result.with_columns(
        pl.when(complete).then(pl.col('fraction')).alias(FEATURES[1]),
        pl.when(complete).then(pl.col('minor_pa')/pl.col('fraction')).alias(FEATURES[2]),
    ).select('season','player_id',*FEATURES)


def attach_schedule(panel, features):
    if features.unique(['season','player_id']).height != features.height:
        raise ValueError('Duplicate player schedule feature')
    return panel.join(features.rename({'season':'origin_year'}),
                      on=['origin_year','player_id'], how='left', validate='1:1')


def restrict_training(train):
    return train.filter(pl.col('origin_year') >= 2015).with_columns(
        (1.0/pl.len().over('player_id')).alias('identity_weight'))
