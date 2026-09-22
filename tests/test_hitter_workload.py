from __future__ import annotations

import numpy as np
import polars as pl

from universal_baseball.hitter_target_architecture import Fold
from universal_baseball.hitter_workload import run_workload_fold


def test_run_workload_fold_composes_probability_and_conditional_pa(monkeypatch) -> None:
    class Model:
        def fit(self, *_args, **_kwargs):
            return self

        def predict_proba(self, matrix):
            return np.column_stack([np.full(len(matrix), 0.75), np.full(len(matrix), 0.25)])

        def predict(self, matrix):
            return np.full(len(matrix), 400.0)

    class Models:
        classifier = Model()
        regressor = Model()

    monkeypatch.setattr(
        "universal_baseball.hitter_workload.make_engine_models",
        lambda *_args, **_kwargs: Models(),
    )
    panel = pl.DataFrame(
        {
            "origin_year": [2015, 2016, 2017],
            "target_season": [2016, 2017, 2018],
            "player_id": [1, 2, 3],
            "feature": [1.0, 2.0, 3.0],
            "target_mlb_active": [0, 1, 1],
            "target_mlb_pa": [0.0, 500.0, 300.0],
            "target_conditional_component_war_per_600": [None, 1.0, 1.0],
            "target_component_war": [0.0, 1.0, 1.0],
        }
    )
    result, metrics = run_workload_fold(
        panel, Fold(2017, (2015, 2016)), "lightgbm", include_direct=True
    )
    assert result["predicted_hurdle_pa"].to_list() == [100.0]
    assert result["predicted_direct_pa"].to_list() == [400.0]
    assert metrics["hurdle_pa"]["rmse"] == 200.0
