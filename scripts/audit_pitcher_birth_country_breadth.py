#!/usr/bin/env python3
"""Test stable birth-country features for pitcher component forecasts."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from audit_pitcher_age_level_handedness import (
    DEMOGRAPHICS,
    _apply_adjustment,
    _fit_adjustment,
    _fold_base,
)
from audit_pitcher_affiliated_regression import (
    COMPONENTS,
    SOURCE,
    _components,
    _score_rows,
)
from universal_baseball.level_component_translation import score_component_profiles
from universal_baseball.pitcher_demographic_breadth import (
    add_pitcher_country_features,
)


OUTPUT = Path("docs/pitcher-birth-country-breadth-result.json")
FAMILIES = {
    "age_hand": ("age_relative", "left_handed", "age_x_left"),
    "country": ("country_usa", "country_dominican", "country_venezuela"),
    "age_hand_country": (
        "age_relative", "left_handed", "age_x_left",
        "country_usa", "country_dominican", "country_venezuela",
    ),
    "age_country_interactions": (
        "age_relative", "left_handed", "age_x_left",
        "country_usa", "country_dominican", "country_venezuela",
        "age_x_usa", "age_x_dominican", "age_x_venezuela",
    ),
}


def _score(
    predictions: pl.DataFrame, target: pl.DataFrame
) -> dict[str, object]:
    return score_component_profiles(
        predictions,
        target,
        exposure_column="batters_faced",
        component_columns=COMPONENTS,
    )


def _cross_validated_predictions(
    base: pl.DataFrame,
    target: pl.DataFrame,
    features: pl.DataFrame,
    columns: tuple[str, ...],
) -> pl.DataFrame:
    pieces = []
    for fold in range(5):
        validation_ids = base.filter(pl.col("player_id") % 5 == fold).get_column(
            "player_id"
        ).to_list()
        training = base.filter(~pl.col("player_id").is_in(validation_ids))
        validation = base.filter(pl.col("player_id").is_in(validation_ids))
        beta = _fit_adjustment(training, target, features, columns)
        pieces.append(_apply_adjustment(validation, features, columns, beta))
    result = pl.concat(pieces).sort("player_id")
    if result.height != base.height or result.get_column("player_id").n_unique() != base.height:
        raise RuntimeError("cross-validated predictions do not preserve player grain")
    return result


def _subgroup_scores(
    candidate: pl.DataFrame,
    incumbent: pl.DataFrame,
    target: pl.DataFrame,
    features: pl.DataFrame,
) -> list[dict[str, object]]:
    candidate_rows = _score_rows(candidate, target).join(
        features.select("player_id", "country"), on="player_id", validate="1:1"
    )
    incumbent_rows = _score_rows(incumbent, target).select(
        "player_id",
        pl.col("log_loss_total").alias("incumbent_log_loss_total"),
        pl.col("brier_total").alias("incumbent_brier_total"),
    )
    rows = candidate_rows.join(incumbent_rows, on="player_id", validate="1:1").with_columns(
        pl.when(pl.col("country").is_in(["USA", "Dominican Republic", "Venezuela"]))
        .then(pl.col("country"))
        .otherwise(pl.lit("Other/unknown"))
        .alias("country_group")
    )
    return (
        rows.group_by("country_group")
        .agg(
            pl.len().alias("players"),
            pl.col("batters_faced").sum().alias("target_bf"),
            (
                (pl.col("log_loss_total") - pl.col("incumbent_log_loss_total")).sum()
                / pl.col("batters_faced").sum()
            ).alias("log_loss_delta"),
            (
                (pl.col("brier_total") - pl.col("incumbent_brier_total")).sum()
                / pl.col("batters_faced").sum()
            ).alias("brier_delta"),
        )
        .sort("country_group")
        .to_dicts()
    )


def main() -> int:
    source = _components(pl.read_parquet(SOURCE))
    demographics = pl.read_parquet(DEMOGRAPHICS)
    dev_base, dev_target, dev_features, _ = _fold_base(source, demographics, 2024)
    dev_features = add_pitcher_country_features(dev_features, demographics)
    development_scores = {"incumbent": _score(dev_base, dev_target)}
    candidates = {}
    for name, columns in FAMILIES.items():
        candidate = _cross_validated_predictions(
            dev_base, dev_target, dev_features, columns
        )
        candidates[name] = candidate
        development_scores[name] = _score(candidate, dev_target)
    eligible = [
        name
        for name in FAMILIES
        if development_scores[name]["component_log_loss"]
        < development_scores["incumbent"]["component_log_loss"]
        and development_scores[name]["component_brier_score"]
        < development_scores["incumbent"]["component_brier_score"]
    ]
    selected = (
        min(eligible, key=lambda name: development_scores[name]["component_log_loss"])
        if eligible
        else "incumbent"
    )

    outer_base, outer_target, outer_features, _ = _fold_base(
        source, demographics, 2025
    )
    outer_features = add_pitcher_country_features(outer_features, demographics)
    if selected == "incumbent":
        outer_candidate = outer_base
    else:
        beta = _fit_adjustment(
            dev_base, dev_target, dev_features, FAMILIES[selected]
        )
        outer_candidate = _apply_adjustment(
            outer_base, outer_features, FAMILIES[selected], beta
        )
    report = {
        "report_schema_version": "0.1",
        "status": "development_diagnostic_not_promoted",
        "contract": "docs/pitcher-birth-country-breadth-plan.md",
        "development_2024_out_of_fold": {
            "scores": development_scores,
            "eligible_families": eligible,
            "selected_family": selected,
        },
        "development_2025_already_inspected": {
            "incumbent_score": _score(outer_base, outer_target),
            "selected_score": _score(outer_candidate, outer_target),
            "country_subgroups": _subgroup_scores(
                outer_candidate, outer_base, outer_target, outer_features
            ),
        },
        "decision": {
            "promoted": False,
            "reason": "2025 is development evidence; later untouched origin required",
        },
        "boundaries": {
            "five_fold_player_cross_validation_2024": True,
            "current_height_or_weight_used": False,
            "height_weight_excluded_as_historical_leakage": True,
            "current_2026_outcomes_used": False,
            "outside_fv_or_rank_used": False,
            "country_effect_is_association_not_causal": True,
        },
    }
    OUTPUT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "selected_family": selected,
        "eligible_families": eligible,
        "development_2024_scores": development_scores,
        "development_2025_subgroups": report[
            "development_2025_already_inspected"
        ]["country_subgroups"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
