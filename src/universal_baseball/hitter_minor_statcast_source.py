"""Contact-only historical minor request and capture checks; no learned model."""
from datetime import date, timedelta
from urllib.parse import urlencode
import polars as pl
from universal_baseball.mlb_contact_history import RAW_COLUMNS

COLUMNS = RAW_COLUMNS + ['launch_speed', 'launch_angle']
KEY = ['game_pk', 'batter', 'at_bat_number', 'pitch_number']
LIMIT = 25_000


def contact_url(start, end, *, tracked=False):
    if not isinstance(start, date) or not isinstance(end, date):
        raise ValueError('Explicit dates required')
    if end < start or start.year != end.year or start.year not in range(2021, 2025):
        raise ValueError('Only historical 2021–24 disjoint season windows')
    params = dict(all='true', player_type='batter', hfGT='R|',
                  game_date_gt=start.isoformat(), game_date_lt=end.isoformat(),
                  type='details', minors='true', hfPR=r'hit\.\.into\.\.play|')
    if tracked:
        params.update(hfFlag='is..tracked|', chk_is__tracked='on')
        params['chk_is..tracked'] = params.pop('chk_is__tracked')
    return 'https://baseballsavant.mlb.com/statcast-search-minors/csv?' + urlencode(params)


def split_window(start, end):
    if start == end:
        raise ValueError('Capped one-day response cannot be accepted')
    middle = start + timedelta(days=(end-start).days // 2)
    return [(start, middle), (middle+timedelta(days=1), end)]


def validate_contact_response(frame, start, end):
    if set(COLUMNS)-set(frame.columns):
        raise ValueError('Missing required detail columns')
    if frame.height >= LIMIT:
        raise ValueError('Capped or potentially capped response')
    if not frame.is_empty():
        if set(frame['game_type'].unique()) != {'R'}:
            raise ValueError('Non-regular game included')
        if set(frame['game_year'].cast(pl.Int64).unique()) != {start.year}:
            raise ValueError('Wrong source season')
        if not frame['game_date'].str.to_date().is_between(start, end).all():
            raise ValueError('Outside requested interval')
        if frame.unique(KEY).height != frame.height:
            raise ValueError('Duplicate pitch keys')
        if frame.unique(['game_pk', 'batter', 'at_bat_number']).height != frame.height:
            raise ValueError('Multiple returned pitches for a PA')
        if frame['events'].fill_null('').str.strip_chars().eq('').any():
            raise ValueError('Nonterminal pitch returned by contact request')
        # MLB provider contact requests also return non-contact interference.
        unusual = frame.filter(pl.col('type').fill_null('') != 'X')
        if unusual.filter(pl.col('events') != 'catcher_interf').height:
            raise ValueError('Unexplained non-X result in contact response')
    return True
