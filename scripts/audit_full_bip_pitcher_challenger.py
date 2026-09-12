#!/usr/bin/env python3
"""Evaluate the frozen full-profile pitcher BIP contact-value challenger."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.bip_contact_talent import (
    apply_bip_residual_blend,
    estimate_neutral_bip_values,
    fit_bip_residual_blend,
)
from universal_baseball.hitter_v2_evaluation import NEUTRAL_WOBA_WEIGHTS
PRIOR_CONTACTS = 100.0
MIN_TARGET_CONTACTS = 50
CONTACT_VALUE_WEIGHTS = dict(NEUTRAL_WOBA_WEIGHTS)


def _load(root: Path, player_type: str) -> tuple[pl.DataFrame, pl.DataFrame]:
    tables = root / "tables"
    return (
        pl.read_parquet(tables / f"{player_type}_full_bip_profile.parquet"),
        pl.read_parquet(tables / f"{player_type}_full_bip_outcomes.parquet"),
    )


def _player_estimates(profile: pl.DataFrame, outcomes: pl.DataFrame) -> pl.DataFrame:
    """Build equally regressed results-only and full-BIP estimates for one origin."""

    bin_values = estimate_neutral_bip_values(
        outcomes, outcome_weights=CONTACT_VALUE_WEIGHTS
    )
    population_profile = (
        profile.group_by("source_level", "core_bin")
        .agg(pl.col("occurrence_count").sum())
        .with_columns(
            (
                pl.col("occurrence_count")
                / pl.col("occurrence_count").sum().over("source_level")
            ).alias("population_bin_probability")
        )
    )
    valued_outcomes = outcomes.with_columns(
        pl.col("canonical_outcome")
        .replace_strict(CONTACT_VALUE_WEIGHTS, return_dtype=pl.Float64)
        .alias("outcome_value")
    )
    population_value = (
        valued_outcomes.group_by("source_level")
        .agg(
            (pl.col("occurrence_count") * pl.col("outcome_value")).sum()
            .alias("population_value_total"),
            pl.col("occurrence_count").sum().alias("population_value_events"),
        )
        .with_columns(
            (pl.col("population_value_total") / pl.col("population_value_events"))
            .alias("population_contact_value")
        )
    )
    player_level_contacts = profile.group_by("player_id", "source_level").agg(
        pl.col("occurrence_count").sum().alias("level_contacts")
    )
    player_contacts = player_level_contacts.group_by("player_id").agg(
        pl.col("level_contacts").sum().alias("origin_contacts")
    )
    primary_level = (
        player_level_contacts.sort(
            ["player_id", "level_contacts", "source_level"],
            descending=[False, True, False],
        )
        .unique("player_id", keep="first")
        .select("player_id", pl.col("source_level").alias("origin_level"))
    )
    player_prior_profile = (
        player_level_contacts.join(population_profile, on="source_level", how="inner")
        .group_by("player_id", "core_bin")
        .agg(
            (
                pl.col("level_contacts") * pl.col("population_bin_probability")
            ).sum().alias("_weighted_prior")
        )
        .join(player_contacts, on="player_id", how="left")
        .with_columns(
            (pl.col("_weighted_prior") / pl.col("origin_contacts"))
            .alias("player_prior_bin_probability")
        )
    )
    complete = (
        player_prior_profile.join(
            profile.group_by("player_id", "core_bin").agg(
                pl.col("occurrence_count").sum().alias("player_bin_count")
            ),
            on=["player_id", "core_bin"],
            how="left",
        )
        .with_columns(pl.col("player_bin_count").fill_null(0))
        .join(bin_values.select("core_bin", "neutral_run_value"), on="core_bin")
        .with_columns(
            (
                (
                    pl.col("player_bin_count")
                    + PRIOR_CONTACTS * pl.col("player_prior_bin_probability")
                )
                / (pl.col("origin_contacts") + PRIOR_CONTACTS)
            ).alias("projected_bin_probability")
        )
    )
    bip = complete.group_by("player_id").agg(
        (pl.col("projected_bin_probability") * pl.col("neutral_run_value"))
        .sum()
        .alias("bip_contact_value")
    )
    player_prior_value = (
        player_level_contacts.join(population_value, on="source_level", how="inner")
        .group_by("player_id")
        .agg(
            (pl.col("level_contacts") * pl.col("population_contact_value"))
            .sum()
            .alias("_weighted_prior_value"),
            pl.col("level_contacts").sum().alias("origin_contacts"),
        )
        .with_columns(
            (pl.col("_weighted_prior_value") / pl.col("origin_contacts"))
            .alias("player_prior_contact_value")
        )
    )
    player_results = valued_outcomes.group_by("player_id").agg(
        (pl.col("occurrence_count") * pl.col("outcome_value")).sum()
        .alias("player_value_total"),
        pl.col("occurrence_count").sum().alias("player_value_events"),
    )
    return (
        player_prior_value.join(player_results, on="player_id", how="left")
        .with_columns(
            pl.col("player_value_total").fill_null(0.0),
            pl.col("player_value_events").fill_null(0),
        )
        .with_columns(
            (
                (
                    pl.col("player_value_total")
                    + PRIOR_CONTACTS * pl.col("player_prior_contact_value")
                )
                / (pl.col("player_value_events") + PRIOR_CONTACTS)
            ).alias("baseline_contact_value")
        )
        .join(bip, on="player_id", how="inner", validate="1:1")
        .join(primary_level, on="player_id", how="left", validate="1:1")
        .select(
            "player_id", "origin_level", "origin_contacts", "baseline_contact_value",
            "bip_contact_value",
        )
    )


def _targets(outcomes: pl.DataFrame) -> pl.DataFrame:
    valued = outcomes.with_columns(
            pl.col("canonical_outcome")
            .replace_strict(CONTACT_VALUE_WEIGHTS, return_dtype=pl.Float64)
            .alias("outcome_value")
        )
    target_level = (
        valued.group_by("player_id", "source_level")
        .agg(pl.col("occurrence_count").sum().alias("level_contacts"))
        .sort(
            ["player_id", "level_contacts", "source_level"],
            descending=[False, True, False],
        )
        .unique("player_id", keep="first")
        .select("player_id", pl.col("source_level").alias("target_level"))
    )
    return (
        valued
        .group_by("player_id")
        .agg(
            (pl.col("occurrence_count") * pl.col("outcome_value")).sum()
            .alias("_target_value_total"),
            pl.col("occurrence_count").sum().cast(pl.Float64).alias("target_contacts"),
        )
        .filter(pl.col("target_contacts") >= MIN_TARGET_CONTACTS)
        .with_columns(
            (pl.col("_target_value_total") / pl.col("target_contacts"))
            .alias("target_contact_value")
        )
        .join(target_level, on="player_id", how="left", validate="1:1")
        .select("player_id", "target_level", "target_contact_value", "target_contacts")
    )


def _metrics(frame: pl.DataFrame, prediction: str) -> dict[str, float | int]:
    error = frame.get_column(prediction).to_numpy() - frame.get_column(
        "target_contact_value"
    ).to_numpy()
    weights = frame.get_column("target_contacts").to_numpy()
    return {
        "players": frame.height,
        "target_contacts": int(weights.sum()),
        "player_mae": float(np.mean(np.abs(error))),
        "player_rmse": float(np.sqrt(np.mean(error**2))),
        "contact_mae": float(np.average(np.abs(error), weights=weights)),
        "contact_rmse": float(np.sqrt(np.average(error**2, weights=weights))),
    }


def _by_origin_level(frame: pl.DataFrame) -> list[dict[str, object]]:
    output = []
    for level in sorted(frame.get_column("origin_level").unique().to_list()):
        group = frame.filter(pl.col("origin_level") == level)
        if group.height < 100:
            continue
        baseline = _metrics(group, "baseline_contact_value")
        blend = _metrics(group, "blended_contact_value")
        output.append(
            {
                "origin_level": level,
                "players": group.height,
                "player_mae_delta": blend["player_mae"] - baseline["player_mae"],
                "player_rmse_delta": blend["player_rmse"] - baseline["player_rmse"],
                "contact_mae_delta": blend["contact_mae"] - baseline["contact_mae"],
                "contact_rmse_delta": blend["contact_rmse"] - baseline["contact_rmse"],
            }
        )
    return output


def _transition(
    origin_root: Path, target_root: Path, player_type: str
) -> pl.DataFrame:
    origin_profile, origin_outcomes = _load(origin_root, player_type)
    _, target_outcomes = _load(target_root, player_type)
    return _player_estimates(origin_profile, origin_outcomes).join(
        _targets(target_outcomes), on="player_id", how="inner", validate="1:1"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--origin-2021", type=Path, required=True)
    parser.add_argument("--target-2022", type=Path, required=True)
    parser.add_argument("--target-2023", type=Path)
    parser.add_argument("--player-type", choices=("hitter", "pitcher"), default="pitcher")
    parser.add_argument(
        "--exclude-hr-value",
        action="store_true",
        help="set HR outcome value to zero so the active HR component remains separate",
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("reports/generated/full-bip-pitcher-challenger/report.json"),
    )
    args = parser.parse_args()
    if args.exclude_hr_value:
        CONTACT_VALUE_WEIGHTS["HR"] = 0.0
    development = _transition(args.origin_2021, args.target_2022, args.player_type)
    blend = fit_bip_residual_blend(development)
    developed = apply_bip_residual_blend(development, blend)
    development_levels = _by_origin_level(developed)
    report: dict[str, object] = {
        "status": "development_only" if args.target_2023 is None else "confirmation_scored",
        "prior_contacts": PRIOR_CONTACTS,
        "minimum_target_contacts": MIN_TARGET_CONTACTS,
        "hr_value_in_contact_target": not args.exclude_hr_value,
        "player_type": args.player_type,
        "development": {
            "baseline": _metrics(developed, "baseline_contact_value"),
            "bip_only": _metrics(developed, "bip_contact_value"),
            "blend": _metrics(developed, "blended_contact_value"),
            "fitted_weight": blend.weight,
            "unconstrained_weight": blend.unconstrained_weight,
            "by_origin_level": development_levels,
        },
    }
    if args.target_2023 is not None:
        confirmation = _transition(
            args.target_2022, args.target_2023, args.player_type
        )
        confirmed = apply_bip_residual_blend(confirmation, blend)
        confirmation_levels = _by_origin_level(confirmed)
        supported_reversals = [
            row["origin_level"]
            for row in confirmation_levels
            if row["player_mae_delta"] > 0.0 and row["player_rmse_delta"] > 0.0
        ]
        report["confirmation"] = {
            "baseline": _metrics(confirmed, "baseline_contact_value"),
            "bip_only": _metrics(confirmed, "bip_contact_value"),
            "blend": _metrics(confirmed, "blended_contact_value"),
            "frozen_weight": blend.weight,
            "by_origin_level": confirmation_levels,
            "supported_level_reversals": supported_reversals,
            "supported_level_reversal_pass": not supported_reversals,
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
