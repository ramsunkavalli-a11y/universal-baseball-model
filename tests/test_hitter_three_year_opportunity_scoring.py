"""Scoring laws independent of the expensive model fits."""
from pathlib import Path
import sys

import numpy as np
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
from score_hitter_three_year_opportunity_v1 import (  # noqa: E402
    PA_FORMS, VALUE_FORMS, add_errors, errors, path_table, probability,
)


def test_equal_origin_scoring_not_row_weighted():
    f = pl.DataFrame({"origin_year": [2016, 2021, 2021, 2021], "prediction": [10., 0., 0., 0.], "truth": [0.]*4})
    score = errors(add_errors(f, ["prediction"], "truth"), ["prediction"], "truth")["prediction"]
    assert score["rmse"] == np.sqrt(50)
    assert score["bias"] == 5.


def test_path_growth_keeps_nonarrival_and_negative_value():
    rows = []
    for player in (1, 2):
        for h in (1, 2, 3):
            rows.append({"origin_year": 2021, "player_id": player, "horizon": h,
                "age": 21., "stage": "Upper minors", "reference_h1": .1, "prospect": True,
                "minor_returner": False, "recent_debut": False,
                "actual_pa": 100*h if player == 1 else 0, "actual_value": -.1*h if player == 1 else 0.,
                "arrival_by_h": .1*h, "actual_arrival_by_h": player == 1,
                **{k: 50.*h for k in PA_FORMS}, **{k: -.05*h for k in VALUE_FORMS}})
    f = path_table(pl.DataFrame(rows))
    assert f.height == 2
    assert f.filter(pl.col("player_id") == 2)["actual_pa"][0] == 0
    np.testing.assert_allclose(f.filter(pl.col("player_id") == 1)["actual_value"], [-.6])
    np.testing.assert_allclose(f["candidate"], [300., 300.])


def test_probability_score_uses_zero_outcomes():
    f = pl.DataFrame({"origin_year": [2021, 2021], "p": [.25, .75], "actual": [False, True]})
    metrics = probability(f, "p", "actual")
    assert metrics["brier"] == .0625
    assert metrics["actual_probability"] == .5
