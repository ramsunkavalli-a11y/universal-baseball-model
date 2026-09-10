#!/usr/bin/env python3
"""Test a pooled non-HR XBH component in affiliated pitcher translation."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

from audit_pitcher_contact_components import FIVE, _load_source, _population
from universal_baseball.hitter_v2_evaluation import (
    NEUTRAL_WOBA_SCALE,
    NEUTRAL_WOBA_WEIGHTS,
)
from universal_baseball.level_component_translation import (
    build_translated_affiliated_profiles,
    fit_same_season_component_translation,
    score_component_profiles,
)


SEVEN = ("so", "ubb", "hbp", "single", "xbh", "hr", "other")
CANDIDATES = (800.0, 1600.0, 2400.0, 4000.0)
OUTPUT = Path("docs/pitcher-pooled-xbh-result.json")


def _seven_source(source: pl.DataFrame) -> pl.DataFrame:
    result = source.with_columns((pl.col("double") + pl.col("triple")).alias("xbh"))
    if result.filter(pl.sum_horizontal(*SEVEN) != pl.col("batters_faced")).height:
        raise ValueError("seven pitching outcomes do not reconcile to BF")
    return result


def _profiles(
    source: pl.DataFrame,
    *,
    target_season: int,
    components: tuple[str, ...],
    regression_bf: float,
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    model_source = source
    if components == FIVE:
        model_source = source.with_columns(
            (pl.col("batters_faced") - pl.sum_horizontal("so", "ubb", "hbp", "hr"))
            .alias("other")
        )
    cutoff = target_season - 1
    players, evidence = _population(model_source, cutoff)
    fit = fit_same_season_component_translation(
        model_source,
        exposure_column="batters_faced",
        component_columns=components,
        completed_seasons=tuple(
            int(value)
            for value in evidence.get_column("season").unique().sort().to_list()
        ),
        minimum_level_exposure=30,
    )
    predictions = build_translated_affiliated_profiles(
        players,
        evidence,
        fit.offsets,
        exposure_column="batters_faced",
        component_columns=components,
        current_season=cutoff,
        reference_season=cutoff,
        regression_exposure=regression_bf,
    )
    target = source.filter(
        (pl.col("season") == target_season) & (pl.col("level_group") == "MLB")
    )
    reference = source.filter(
        (pl.col("season") == cutoff) & (pl.col("level_group") == "MLB")
    )
    return predictions, target, reference


def _expand_incumbent(five: pl.DataFrame, reference: pl.DataFrame) -> pl.DataFrame:
    totals = {component: float(reference.get_column(component).sum()) for component in SEVEN}
    broad_other = sum(totals[value] for value in ("single", "xbh", "other"))
    shares = {
        value: totals[value] / broad_other for value in ("single", "xbh", "other")
    }
    return five.with_columns(
        *((pl.col("p_other") * shares[value]).alias(f"p_{value}") for value in shares)
    ).select("player_id", *(f"p_{value}" for value in SEVEN))


def _score_rows(predictions: pl.DataFrame, target: pl.DataFrame) -> pl.DataFrame:
    actual = target.group_by("player_id").agg(
        pl.col("batters_faced").sum(),
        *(pl.col(component).sum() for component in SEVEN),
    ).filter(pl.col("batters_faced") > 0)
    return actual.join(predictions, on="player_id", how="inner", validate="1:1").sort(
        "player_id"
    ).with_columns(
        pl.sum_horizontal(
            *(-pl.col(component) * pl.col(f"p_{component}").log() for component in SEVEN)
        ).alias("log_loss_total"),
        (
            pl.col("batters_faced")
            * (1.0 + pl.sum_horizontal(*(pl.col(f"p_{c}") ** 2 for c in SEVEN)))
            - 2.0
            * pl.sum_horizontal(*(pl.col(c) * pl.col(f"p_{c}") for c in SEVEN))
        ).alias("brier_total"),
    )


def _bootstrap(candidate: pl.DataFrame, incumbent: pl.DataFrame) -> dict[str, object]:
    joined = candidate.select(
        "player_id", "batters_faced", "log_loss_total", "brier_total"
    ).join(
        incumbent.select(
            "player_id",
            pl.col("log_loss_total").alias("incumbent_ll"),
            pl.col("brier_total").alias("incumbent_brier"),
        ),
        on="player_id",
        validate="1:1",
    ).select(
        "batters_faced",
        (pl.col("log_loss_total") - pl.col("incumbent_ll")).alias("ll_delta"),
        (pl.col("brier_total") - pl.col("incumbent_brier")).alias("brier_delta"),
    ).to_numpy()
    rng = np.random.default_rng(20250913)
    draws = np.empty((2000, 2))
    for index in range(len(draws)):
        sample = joined[rng.integers(0, len(joined), len(joined))]
        draws[index] = sample[:, 1:].sum(axis=0) / sample[:, 0].sum()
    return {
        name: {
            "lower_95": float(np.quantile(draws[:, column], 0.025)),
            "median": float(np.quantile(draws[:, column], 0.5)),
            "upper_95": float(np.quantile(draws[:, column], 0.975)),
        }
        for column, name in enumerate(("component_log_loss", "component_brier"))
    }


def _run_rate_spread(predictions: pl.DataFrame, reference: pl.DataFrame) -> float:
    weights = {
        "so": 0.0,
        "ubb": NEUTRAL_WOBA_WEIGHTS["UBB"],
        "hbp": NEUTRAL_WOBA_WEIGHTS["HBP"],
        "single": NEUTRAL_WOBA_WEIGHTS["1B"],
        "xbh": (
            NEUTRAL_WOBA_WEIGHTS["2B"]
            * float(reference.get_column("double").sum())
            + NEUTRAL_WOBA_WEIGHTS["3B"]
            * float(reference.get_column("triple").sum())
        ) / float(reference.get_column("xbh").sum()),
        "hr": NEUTRAL_WOBA_WEIGHTS["HR"],
        "other": 0.0,
    }
    predicted_woba = predictions.select(
        pl.sum_horizontal(*(pl.col(f"p_{key}") * value for key, value in weights.items()))
        .alias("woba")
    ).get_column("woba")
    return float((predicted_woba * 800.0 / NEUTRAL_WOBA_SCALE).std())


def _fold(
    source: pl.DataFrame, target_season: int, regressions: tuple[float, ...]
) -> dict[str, object]:
    five, target, reference = _profiles(
        source, target_season=target_season, components=FIVE, regression_bf=800.0
    )
    incumbent = _expand_incumbent(five, reference)
    candidates = {
        int(regression): _profiles(
            source,
            target_season=target_season,
            components=SEVEN,
            regression_bf=regression,
        )[0]
        for regression in regressions
    }
    return {
        "target": target,
        "reference": reference,
        "incumbent": incumbent,
        "candidates": candidates,
        "incumbent_score": score_component_profiles(
            incumbent,
            target,
            exposure_column="batters_faced",
            component_columns=SEVEN,
        ),
        "candidate_scores": {
            str(key): score_component_profiles(
                value,
                target,
                exposure_column="batters_faced",
                component_columns=SEVEN,
            )
            for key, value in candidates.items()
        },
    }


def main() -> int:
    source = _seven_source(_load_source())
    development = _fold(source, 2024, CANDIDATES)
    incumbent_dev = development["incumbent_score"]
    eligible = [
        regression
        for regression in CANDIDATES
        if float(development["candidate_scores"][str(int(regression))]["component_brier_score"])
        < float(incumbent_dev["component_brier_score"])
    ]
    selected = (
        min(
            eligible,
            key=lambda value: float(
                development["candidate_scores"][str(int(value))]["component_log_loss"]
            ),
        )
        if eligible
        else None
    )
    outer_report = None
    if selected is not None:
        outer = _fold(source, 2025, (selected,))
        candidate = outer["candidates"][int(selected)]
        candidate_score = outer["candidate_scores"][str(int(selected))]
        incumbent_score = outer["incumbent_score"]
        outer_report = {
            "incumbent_score": incumbent_score,
            "candidate_score": candidate_score,
            "candidate_minus_incumbent_log_loss": float(candidate_score["component_log_loss"])
            - float(incumbent_score["component_log_loss"]),
            "candidate_minus_incumbent_brier": float(candidate_score["component_brier_score"])
            - float(incumbent_score["component_brier_score"]),
            "bootstrap_candidate_minus_incumbent": _bootstrap(
                _score_rows(candidate, outer["target"]),
                _score_rows(outer["incumbent"], outer["target"]),
            ),
            "incumbent_predicted_run_rate_sd": _run_rate_spread(
                outer["incumbent"], outer["reference"]
            ),
            "candidate_predicted_run_rate_sd": _run_rate_spread(
                candidate, outer["reference"]
            ),
        }
    outer_passed = bool(
        outer_report is not None
        and outer_report["candidate_minus_incumbent_log_loss"] < 0
        and outer_report["candidate_minus_incumbent_brier"] < 0
    )
    report = {
        "report_schema_version": "0.1",
        "status": "pitcher_pooled_xbh_retrospective_audit_complete",
        "contract": "docs/pitcher-pooled-xbh-plan.md",
        "source_rows": source.height,
        "development_2024": {
            "incumbent_score": incumbent_dev,
            "candidate_scores": development["candidate_scores"],
            "selected_regression_bf": None if selected is None else int(selected),
        },
        "retrospective_outer_2025": outer_report,
        "decision": {
            "outer_point_gate_passed": outer_passed,
            "promoted": False,
            "reason": (
                "no_development_candidate_improved_both_scores"
                if selected is None
                else "retrospective_outer_only_fresh_2026_confirmation_required"
            ),
        },
        "boundaries": {
            "current_2026_outcomes_used": False,
            "outside_fv_used": False,
            "uncertified_pitch_process_used": False,
            "fully_stacked_demographic_comparison": False,
        },
    }
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "selected_regression_bf": None if selected is None else int(selected),
        "outer_scored": outer_report is not None,
        "outer_point_gate_passed": outer_passed,
        "promoted": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
