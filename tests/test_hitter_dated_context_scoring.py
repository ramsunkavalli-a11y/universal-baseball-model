import importlib
from pathlib import Path

import numpy as np
import polars as pl
import pytest

from universal_baseball.hitter_compatible_value import UNIT
from universal_baseball.mlb_event_logit import EVENTS, VALUES


@pytest.fixture
def reviewed_labels(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'scripts'))
    review = importlib.import_module('review_hitter_dated_context_v2')
    columns = ['strike_outs', 'unintentional_walks', 'hit_by_pitch',
               'singles', 'doubles', 'triples', 'home_runs']
    raw = np.array([5., 2., 1., 0., 1., 0., 0., 1.])
    rows = [dict(player_id=1, season=2024, sport_id=1, plate_appearances=20,
                 **{c: 0 for c in columns}),
            dict(player_id=1, season=2025, sport_id=1, plate_appearances=10,
                 **dict(zip(columns, raw[1:], strict=True))),
            dict(player_id=9, season=2025, sport_id=1, plate_appearances=10,
                 **{c: 0 for c in columns})]
    monkeypatch.setattr(review.pl, 'read_parquet', lambda _: pl.DataFrame(rows))
    origin = np.array([1., 0., 0., 0., 0., 0., 0., 0.])
    target = (raw + 10 * origin) / 20
    relative = float((raw / 10 - target) @ VALUES * UNIT)
    common = float((raw / 10 - origin) @ VALUES * UNIT)
    forecasts = []
    for rid, pid, events, rate, legacy in [(1, 1, raw, relative, common),
                                         (2, 2, np.zeros(8), None, None)]:
        n = int(events.sum())
        r = dict(row_id=rid, player_id=pid, origin_year=2024, target_year=2025,
                 next_pa=n, origin_replacement_rate=.003,
                 actual_future_relative_rate=rate, next_batting_rate=legacy,
                 relative_value_label=n * ((rate or 0) / 600 + .003),
                 next_value=n * ((legacy or 0) / 600 + .003))
        for prefix, vector in [('count_', events), ('origin_env_', origin),
                               ('target_env_', target)]:
            r.update({prefix + e: float(v) for e, v in zip(EVENTS, vector, strict=True)})
        forecasts.append(r)
    return review, pl.DataFrame(forecasts)


def test_legacy_origin_reference_does_not_become_the_relative_label(reviewed_labels):
    review, q = reviewed_labels
    rate, value = review.actual_from_dated_counts(q)
    assert rate[0] != q['next_batting_rate'][0]
    assert np.isclose(rate[0], q['actual_future_relative_rate'][0])
    assert rate[1] == value[1] == 0  # Accounting placeholder, not observed talent.
    mutated = q.with_columns(pl.lit(999.).alias('next_batting_rate'))
    new_rate, new_value = review.actual_from_dated_counts(mutated)
    assert np.array_equal(rate, new_rate) and np.array_equal(value, new_value)


def test_wrong_relative_label_fails_reconstruction(reviewed_labels):
    review, q = reviewed_labels
    wrong = q.with_columns(pl.col('next_value').alias('relative_value_label'))
    with pytest.raises(AssertionError):
        review.actual_from_dated_counts(wrong)


def test_missing_positive_pa_source_cannot_be_scored_as_zero(reviewed_labels):
    review, q = reviewed_labels
    wrong = q.with_columns(pl.when(pl.col('player_id') == 1).then(100)
                           .otherwise(pl.col('player_id')).alias('player_id'))
    with pytest.raises(AssertionError):
        review.actual_from_dated_counts(wrong)
