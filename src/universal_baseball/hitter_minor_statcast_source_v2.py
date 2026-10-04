"""Additive source validation: in-play search descriptions need not be terminal."""
import polars as pl
from universal_baseball.hitter_minor_statcast_source import COLUMNS, KEY, LIMIT, contact_url, split_window


def validate_contact_response(frame, start, end):
    if set(COLUMNS)-set(frame.columns):
        raise ValueError('Missing detail columns')
    if frame.height >= LIMIT:
        raise ValueError('Capped response')
    if frame.is_empty():return True
    if set(frame['game_type'].unique())!={'R'} or set(frame['game_year'].cast(pl.Int64).unique())!={start.year}:
        raise ValueError('Outside regular historical season')
    if not frame['game_date'].str.to_date().is_between(start,end).all():
        raise ValueError('Outside request dates')
    if frame.unique(KEY).height!=frame.height or frame.select(pl.any_horizontal(pl.col(*KEY).is_null()).any()).item():
        raise ValueError('Duplicate or missing pitch identity')
    terminal=frame.filter(pl.col('events').fill_null('').str.strip_chars().ne(''))
    if terminal.unique(['game_pk','batter','at_bat_number']).height!=terminal.height:
        raise ValueError('Multiple terminal pitches for PA')
    if terminal.filter((pl.col('type').fill_null('')!='X')&(pl.col('events')!='catcher_interf')).height:
        raise ValueError('Unexplained non-X terminal result')
    return True
