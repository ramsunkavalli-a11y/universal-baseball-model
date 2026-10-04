"""Ordinary MLB contact/result history, with no tracking predictors or fitting."""
import polars as pl

from universal_baseball.contact_profile import classify_contact_profile_events
from universal_baseball.current_talent_contact_value_source import STRUCTURED_TERMINAL_GROUP
from universal_baseball.hitter_value_panel import CONTACT_BINS, CONTACT_OUTCOMES
from universal_baseball.current_talent_mlb_evidence import _with_official_outcome_batter

# Selecting columns at CSV read time avoids importing tracking/future-game fields.
RAW_COLUMNS = ['game_date', 'game_year', 'game_pk', 'at_bat_number', 'pitch_number',
               'game_type', 'batter', 'pitcher', 'stand', 'p_throws', 'events',
               'description', 'des', 'type', 'bb_type', 'hit_location', 'hc_x',
               'hc_y', 'home_team', 'away_team', 'inning_topbot']
KEY = ['game_pk', 'at_bat_index', 'pitch_number']
CELLS = [f'count_{b}___{o}' for b in CONTACT_BINS for o in CONTACT_OUTCOMES]


def require_history(frame):
    if frame.is_empty() or not frame['game_year'].is_in([2023, 2024]).all():
        raise ValueError('Only the fixed cached 2023/2024 pilot is permitted')
    if frame.unique(KEY).height != len(frame):
        raise ValueError('Duplicate canonical pitch identity')
    if not frame['game_type'].eq('R').all():
        raise ValueError('Regular-season source required')


def outcome_counts(frame):
    require_history(frame)
    attributed = _with_official_outcome_batter(frame)
    terminal = attributed.filter(pl.col('is_plate_appearance_terminal'))
    if terminal.unique(['game_pk', 'at_bat_index']).height != len(terminal):
        raise ValueError('Duplicate true PA terminal')
    if terminal['_outcome_player_id'].null_count():
        raise ValueError('Unknown official outcome participant')
    cols = {'strike_outs': ['strikeout', 'strikeout_double_play'],
            'unintentional_walks': ['walk'], 'hit_by_pitch': ['hit_by_pitch'],
            'singles': ['single'], 'doubles': ['double'], 'triples': ['triple'],
            'home_runs': ['home_run']}
    result = terminal.group_by('game_year', '_outcome_player_id').agg(
        pl.len().cast(pl.Int64).alias('plate_appearances'),
        *[pl.col('events').is_in(events).sum().cast(pl.Int64).alias(name)
          for name, events in cols.items()]).rename(
              {'game_year': 'season', '_outcome_player_id': 'player_id'})
    substitutions = terminal.filter(pl.col('_outcome_player_id') != pl.col('batter_mlbam_id'))
    return result.sort('season', 'player_id'), substitutions.select(
        *KEY, 'batter_mlbam_id', '_outcome_player_id', 'events')


def schedule_venues(payload, season):
    rows = []
    for date in payload.get('dates', []):
        for game in date.get('games', []):
            if game['gameType'] == 'R' and int(game['season']) == season:
                rows.append(dict(game_pk=int(game['gamePk']),
                                 schedule_season=season,
                                 official_date=game['officialDate'],
                                 venue_id=game.get('venue', {}).get('id'),
                                 venue_name=game.get('venue', {}).get('name')))
    q = pl.DataFrame(rows).unique()
    if q.unique('game_pk').height != len(q):
        raise ValueError('Conflicting game schedule venues')
    return q.sort('game_pk')


def contact_ledger(frame, venues):
    require_history(frame)
    raw = frame.filter(pl.col('is_contact'))
    projection = raw.select(
        pl.col('game_year').alias('season'), 'league_id', *KEY, 'batter_mlbam_id',
        'batter_side', 'bb_type', 'hc_x', 'hc_y', 'result_description',
        pl.lit('savant_official').alias('participant_authority'),
        pl.lit('savant_official').alias('result_description_authority'))
    profile = classify_contact_profile_events(projection)
    if len(profile) != len(raw):
        raise ValueError('Classifier lost physical contacts')
    q = raw.select(
        pl.col('game_year').alias('season'), 'game_date', 'league_id', *KEY,
        pl.col('batter_mlbam_id').alias('player_id'), 'pitcher_mlbam_id',
        'batter_side', 'pitcher_hand', 'bb_type', 'hc_x', 'hc_y',
        'events', 'is_plate_appearance_terminal', 'result_description').join(
            profile.select(*KEY, 'core_bin', 'contact_profile_status'),
            on=KEY, how='left', validate='1:1').join(
                venues, on='game_pk', how='left', validate='m:1')
    if q['schedule_season'].null_count() or not q['season'].equals(q['schedule_season']):
        raise ValueError('Physical contacts missing or crossing schedule seasons')
    # Structured special results remain outside cells even when geometry exists.
    special = (pl.col('events') == 'field_error') & pl.col('result_description').str.to_lowercase().str.contains('interference error').fill_null(False)
    q = q.with_columns(
        pl.when(pl.col('is_plate_appearance_terminal') & ~special)
        .then(pl.col('events').replace_strict(STRUCTURED_TERMINAL_GROUP, default=None))
        .otherwise(None).alias('terminal_outcome_group'))
    q = q.with_columns(
        pl.col('terminal_outcome_group').replace_strict(
            {'OUT': 'OTHER_OUT', **{o: o for o in CONTACT_OUTCOMES}}, default=None).alias('canonical_outcome'),
        pl.col('venue_id').is_null().alias('venue_missing'),
        pl.lit('MLB').alias('bucket'))
    q = q.with_columns((pl.col('core_bin').is_not_null() & pl.col('canonical_outcome').is_not_null()).alias('cell_eligible'))
    if q.unique(KEY).height != len(q):
        raise ValueError('Context join duplicated physical contacts')
    return q.sort(KEY)


def annual_cells(events):
    grain = ['season', 'player_id']
    exposure = events.group_by(grain).agg(
        pl.len().cast(pl.Int64).alias('physical_contacts'),
        pl.col('cell_eligible').sum().cast(pl.Int64).alias('classified_contacts'),
        pl.col('core_bin').is_not_null().sum().cast(pl.Int64).alias('geometry_core_contacts'),
        pl.col('venue_missing').sum().cast(pl.Int64).alias('venue_missing_contacts'))
    eligible = events.filter(pl.col('cell_eligible'))
    for b in CONTACT_BINS:
        part = eligible.filter(pl.col('core_bin') == b).group_by(grain).agg(
            *[(pl.col('canonical_outcome') == o).sum().cast(pl.Int64).alias(f'count_{b}___{o}')
              for o in CONTACT_OUTCOMES])
        exposure = exposure.join(part, on=grain, how='left', validate='1:1')
    q = exposure.with_columns(pl.col(CELLS).fill_null(0).cast(pl.Int64))
    if not q.select((pl.sum_horizontal(CELLS) == pl.col('classified_contacts')).all()).item():
        raise ValueError('Contact cells do not exhaust classified exposure')
    return q.sort(grain)
