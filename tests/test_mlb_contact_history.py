import polars as pl
import pytest
from universal_baseball.mlb_contact_history import (
    RAW_COLUMNS, require_history, outcome_counts, contact_ledger, annual_cells,
    schedule_venues, CELLS,
)


def pitch(number=1, player=10, event='single', contact=True, year=2024):
    return dict(game_year=year, game_date=f'{year}-06-01', game_type='R',
                game_pk=1, at_bat_index=0, pitch_number=number,
                league_id=103, batter_mlbam_id=player, pitcher_mlbam_id=99,
                batter_side='R', pitcher_hand='L', bb_type='line_drive' if contact else None,
                hc_x=125., hc_y=80., result_description='Hitter singles.' if contact else 'Hitter strikes out.',
                events=event, is_contact=contact, is_plate_appearance_terminal=event is not None,
                pitch_result_code='X' if contact else 'S')


def venue(venue_id=20):
    return pl.DataFrame([dict(game_pk=1, schedule_season=2024,
                             official_date='2024-06-01', venue_id=venue_id,
                             venue_name='Ground')], schema_overrides={'venue_id': pl.Int64})


def test_only_ordinary_source_columns():
    assert len(RAW_COLUMNS) == len(set(RAW_COLUMNS)) == 21
    assert not set(RAW_COLUMNS) & {'launch_speed', 'launch_angle', 'release_speed',
                                   'estimated_woba_using_speedangle', 'batter_days_until_next_game'}


def test_protected_and_duplicate_sources_rejected():
    with pytest.raises(ValueError, match='fixed cached'):
        require_history(pl.DataFrame([pitch(year=2026)]))
    with pytest.raises(ValueError, match='Duplicate'):
        require_history(pl.DataFrame([pitch(), pitch()]))


def test_contact_cells_and_unknown_venue():
    events = contact_ledger(pl.DataFrame([pitch()]), venue(None))
    assert events['venue_missing'][0] and events['canonical_outcome'][0] == '1B'
    cells = annual_cells(events)
    assert cells['classified_contacts'][0] == 1
    assert sum(cells.select(CELLS).row(0)) == 1
    assert cells['count_CENTER_LD___1B'][0] == 1


def test_missing_geometry_is_not_a_measured_average_cell():
    row = pitch(); row['hc_x'] = None; row['hc_y'] = None
    q = contact_ledger(pl.DataFrame([row], schema_overrides={'hc_x': pl.Float64, 'hc_y': pl.Float64}), venue())
    assert q['contact_profile_status'][0] == 'unknown_missing_direction'
    counts = annual_cells(q)
    assert counts['physical_contacts'][0] == 1 and counts['classified_contacts'][0] == 0
    assert sum(counts.select(CELLS).row(0)) == 0


def test_strikeout_substitution_uses_official_outcome_not_physical_hitter():
    a = pitch(1, event=None, contact=False); b = pitch(2, event=None, contact=False)
    c = pitch(3, player=11, event='strikeout', contact=False)
    counts, substitutions = outcome_counts(pl.DataFrame([a, b, c]))
    assert counts['player_id'].to_list() == [10]
    assert counts['plate_appearances'][0] == counts['strike_outs'][0] == 1
    assert substitutions['batter_mlbam_id'][0] == 11
    assert substitutions['_outcome_player_id'][0] == 10


def test_special_physical_contact_not_an_ordinary_hit_result():
    row = pitch(event='field_error'); row['result_description'] = 'Hitter reaches on interference error.'
    q = contact_ledger(pl.DataFrame([row]), venue())
    assert len(q) == 1 and not q['cell_eligible'][0]
    assert q['canonical_outcome'][0] is None


def test_schedule_conflicts_and_unmatched_contacts_fail():
    payload = {'dates': [{'games': [dict(gamePk=1, gameType='R', season='2024',
                                        officialDate='2024-06-01', venue={'id': 20, 'name': 'Ground'}),
                                   dict(gamePk=1, gameType='R', season='2024',
                                        officialDate='2024-06-01', venue={'id': 21, 'name': 'Other'})]}]}
    with pytest.raises(ValueError, match='Conflicting'):
        schedule_venues(payload, 2024)
    with pytest.raises(ValueError, match='schedule'):
        contact_ledger(pl.DataFrame([pitch()]), venue().with_columns(pl.lit(2).alias('game_pk')))
