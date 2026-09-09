from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from universal_baseball.performance_season import ALL_CORE_BINS
from universal_baseball.playing_time_model import (
    PT_FORM_A,
    PT_FORM_B,
    PT_FORM_B0,
    PT_FORM_C,
    PT_FORM_U,
    PT_FORM_U0,
    PT_FORM_UA,
    build_playing_time_design,
    fit_playing_time_hurdle,
    playing_time_feature_names,
    playing_time_level_tier,
    predict_playing_time_hurdle,
    score_playing_time_hurdle,
)
from universal_baseball.projection_composition import projection_profile_to_ilr


def _predictors(n: int = 500) -> pl.DataFrame:
    rng = np.random.default_rng(17)
    levels = np.array(["MLB", "AAA", "AA", "HIGH_A", "SINGLE_A", "ROOKIE_COMPLEX"])
    probabilities = np.full(len(ALL_CORE_BINS), 1.0 / len(ALL_CORE_BINS))
    ilr = projection_profile_to_ilr(dict(zip(ALL_CORE_BINS, probabilities, strict=True)))
    rows: list[dict[str, object]] = []
    for player_id in range(1, n + 1):
        level = str(levels[(player_id - 1) % len(levels)])
        mlb = int(rng.integers(0, 650)) if level == "MLB" else int(rng.integers(0, 80))
        milb = int(rng.integers(0, 550)) if level != "MLB" else int(rng.integers(0, 40))
        row: dict[str, object] = {
            "player_id": player_id,
            "age_years": float(rng.uniform(19.0, 36.0)),
            "as_of_level_group": level,
            "current_season_mlb_pa": mlb,
            "current_season_milb_pa": milb,
            "on_40man": bool(level in {"MLB", "AAA"} or player_id % 7 == 0),
        }
        row.update({f"b2_ilr_{index:02d}": value for index, value in enumerate(ilr)})
        rows.append(row)
    return pl.DataFrame(rows)


def _targets(predictors: pl.DataFrame) -> pl.DataFrame:
    rng = np.random.default_rng(23)
    rows: list[dict[str, object]] = []
    for row in predictors.iter_rows(named=True):
        tier = playing_time_level_tier(row["as_of_level_group"])
        base = {"MLB": 0.82, "AAA": 0.32, "AA": 0.11, "A_OR_BELOW": 0.025}[tier]
        p = min(0.96, base + (0.10 if row["on_40man"] else 0.0))
        if rng.random() < p:
            mean = 390.0 if tier == "MLB" else 230.0
            alpha = 0.7
            size = 1.0 / alpha
            probability = size / (size + mean)
            count = 0
            while count <= 0:
                count = int(rng.negative_binomial(size, probability))
            count = min(count, 750)
        else:
            count = 0
        rows.append({"player_id": int(row["player_id"]), "next_year_mlb_pa": count})
    return pl.DataFrame(rows)


def test_level_tier_contract() -> None:
    assert playing_time_level_tier("MLB") == "MLB"
    assert playing_time_level_tier("AAA") == "AAA"
    assert playing_time_level_tier("AA") == "AA"
    assert playing_time_level_tier("HIGH_A") == "A_OR_BELOW"
    assert playing_time_level_tier("SINGLE_A") == "A_OR_BELOW"
    assert playing_time_level_tier("ROOKIE_COMPLEX") == "A_OR_BELOW"
    with pytest.raises(ValueError, match="unsupported"):
        playing_time_level_tier("DSL")


def test_nested_feature_forms_are_frozen_and_monotone() -> None:
    b0 = playing_time_feature_names(PT_FORM_B0)
    a = playing_time_feature_names(PT_FORM_A)
    b = playing_time_feature_names(PT_FORM_B)
    c = playing_time_feature_names(PT_FORM_C)
    assert set(b0) < set(a) < set(b) < set(c)
    assert "on_40man" not in a
    assert "on_40man" in b
    assert "b2_k_probability" in c


def test_universal_v2_keeps_inactive_unknown_and_missing_age_players() -> None:
    predictors = pl.DataFrame(
        [
            {
                "player_id": 1,
                "age_years": None,
                "as_of_level_group": "INACTIVE",
                "current_season_mlb_pa": 0,
                "current_season_milb_pa": 0,
                "on_40man": False,
            },
            {
                "player_id": 2,
                "age_years": 22.0,
                "as_of_level_group": "UNCLASSIFIED",
                "current_season_mlb_pa": 0,
                "current_season_milb_pa": 100,
                "on_40man": True,
            },
        ]
    )

    design = build_playing_time_design(predictors, form=PT_FORM_U)

    assert design.height == 2
    assert design.filter(pl.col("player_id") == 1).item(0, "level_inactive") == 1.0
    assert design.filter(pl.col("player_id") == 1).item(0, "age_missing") == 1.0
    assert design.filter(pl.col("player_id") == 2).item(0, "level_unknown") == 1.0


def test_universal_v2_forms_are_nested_without_changing_frozen_v1_forms() -> None:
    u0 = playing_time_feature_names(PT_FORM_U0)
    ua = playing_time_feature_names(PT_FORM_UA)
    u = playing_time_feature_names(PT_FORM_U)

    assert set(u0) < set(ua) < set(u)
    assert "age_missing" in ua
    assert "on_40man" not in ua
    assert "on_40man" in u


def test_hurdle_fit_and_score_produce_valid_full_distribution_metrics() -> None:
    predictors = _predictors()
    targets = _targets(predictors)
    design = build_playing_time_design(predictors, form=PT_FORM_B)
    fit = fit_playing_time_hurdle(design, targets, form=PT_FORM_B)
    scored, metrics = score_playing_time_hurdle(fit, design, targets)

    assert scored.height == predictors.height
    assert scored.filter(
        (pl.col("predicted_any_mlb_pa_probability") <= 0)
        | (pl.col("predicted_any_mlb_pa_probability") >= 1)
    ).is_empty()
    assert scored.filter(pl.col("predicted_expected_mlb_pa") <= 0).is_empty()
    assert scored.filter(
        (pl.col("observed_mlb_pa") == 0)
        & pl.col("positive_count_negative_log_likelihood").is_not_null()
    ).is_empty()
    assert metrics["mean_full_negative_log_likelihood"] > 0
    assert metrics["participation_log_loss"] > 0
    assert metrics["positive_count_negative_log_likelihood"] > 0
    assert metrics["unconditional_mlb_pa_mae"] >= 0
    assert fit.nb_alpha > 0

    predicted_only = predict_playing_time_hurdle(fit, design)
    assert predicted_only.get_column("predicted_expected_mlb_pa").to_list() == pytest.approx(
        scored.get_column("predicted_expected_mlb_pa").to_list()
    )


def test_compact_b2_form_reconstructs_valid_talent_summaries_from_ilr() -> None:
    predictors = _predictors(12)
    design = build_playing_time_design(predictors, form=PT_FORM_C)
    assert design.get_column("b2_bb_hbp_probability").min() > 0
    assert design.get_column("b2_k_probability").min() > 0
    assert design.get_column("b2_non_iffb_offb_probability").min() > 0
    assert design.get_column("b2_ld_probability").min() > 0


def test_hurdle_fit_handles_unidentified_positive_count_category() -> None:
    predictors = _predictors(500).with_columns(
        pl.when(pl.col("player_id") <= 20)
        .then(pl.lit("INACTIVE"))
        .otherwise(pl.col("as_of_level_group"))
        .alias("as_of_level_group")
    )
    targets = _targets(_predictors(500)).with_columns(
        pl.when(pl.col("player_id") <= 20)
        .then(pl.lit(0))
        .otherwise(pl.col("next_year_mlb_pa"))
        .alias("next_year_mlb_pa")
    )
    design = build_playing_time_design(predictors, form=PT_FORM_U)

    fit = fit_playing_time_hurdle(design, targets, form=PT_FORM_U)
    scored, _ = score_playing_time_hurdle(fit, design, targets)

    assert "level_inactive" in fit.metrics["positive_count_unidentified_features"]
    inactive_index = fit.feature_names.index("level_inactive") + 1
    assert fit.nb_coefficients[inactive_index] == 0.0
    assert scored.height == 500
