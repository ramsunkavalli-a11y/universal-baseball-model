import numpy as np
import polars as pl
import pytest

from universal_baseball.nonmedical_opportunity import FIELDS, OBS, numeric, frame


def test_game_and_calendar_units_are_not_remaining_time():
    r = numeric([True, False], 80, None, '2023-04-20', '2023-01-26')
    assert r['restriction_games'] == .8 and r['restriction_games_known'] == 1
    assert r['restriction_end_days'] == 0 and r['restriction_end_known'] == 0
    assert r['return_report_days'] == 84 / 365
    assert numeric([False, False], None, None, None, '2023-01-26') == dict.fromkeys(FIELDS, 0.)


def test_legacy_values_and_cutoff_must_reconstruct_without_mutating_original():
    old = numeric([1, 0], 80, None, '2023-04-20', '2023-01-26')
    original = pl.DataFrame([dict(row_id=1, origin_year=2022, player_id=1,
        ctx_information_date='2023-01-26', unchanged_talent=1.4, **old)])
    s = pl.DataFrame([dict(origin_year=2022, player_id=1, information_date='2023-01-26',
        captured_legal_class='finite_game_suspension', observation_has_return=False,
        **{'legacy_' + n: v for n, v in old.items()}, **{OBS[n]: v for n, v in old.items()})])
    new = frame(original, s)
    assert new.select(original.columns).equals(original)
    assert np.array_equal(new.select(OBS.values()).to_numpy(), original.select(FIELDS).to_numpy())
    with pytest.raises(ValueError, match='reconstruct'):
        frame(original, s.with_columns(pl.lit(0.).alias('legacy_restriction_games')))
    with pytest.raises(ValueError, match='cutoff'):
        frame(original, s.with_columns(pl.lit('2023-01-27').alias('information_date')))
    with pytest.raises(ValueError, match='Missing'):
        frame(original, s.with_columns(pl.lit(2).alias('player_id')))


def test_old_timing_clips_are_preserved_and_invalid_sentences_rejected():
    old = numeric([1, 0], 2000, '2025-01-01', '2020-01-01', '2023-01-26')
    assert old['restriction_games'] == 10 and old['restriction_end_days'] == 1
    assert old['return_report_days'] == -1
    for games in [0, -1, 1.5]:
        with pytest.raises(ValueError):
            numeric([1, 0], games, None, None, '2023-01-26')
