#!/usr/bin/env python3
"""Test the provisional two-year-to-longer-horizon prospect probability rule."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.prospect_arrival import (
    build_arrival_cohort,
    fit_arrival_model,
    predict_arrival,
)


def _history_stats(root: Path) -> pl.DataFrame:
    return pl.concat(
        [pl.read_parquet(path) for path in sorted(root.glob("*/affiliated_season_stats.parquet"))],
        how="vertical_relaxed",
    )


def _clean_metrics(frame: pl.DataFrame, probability: str, observed: str) -> dict[str, float]:
    clipped = frame.with_columns(pl.col(probability).clip(1e-12, 1 - 1e-12).alias("p"))
    return {
        "players": clipped.height,
        "positives": int(clipped.get_column(observed).sum()),
        "observed_rate": float(clipped.get_column(observed).mean()),
        "mean_probability": float(clipped.get_column("p").mean()),
        "brier": float(
            clipped.select(((pl.col("p") - pl.col(observed)) ** 2).mean()).item()
        ),
        "log_loss": float(
            clipped.select(
                (
                    -pl.col(observed) * pl.col("p").log()
                    - (1 - pl.col(observed)) * (1 - pl.col("p")).log()
                ).mean()
            ).item()
        ),
    }


def _subgroup_calibration(
    frame: pl.DataFrame,
    *,
    group: str,
    probability: str,
    observed: str,
    minimum_players: int = 100,
) -> list[dict[str, object]]:
    return (
        frame.group_by(group)
        .agg(
            pl.len().alias("players"),
            pl.col(observed).sum().alias("positives"),
            pl.col(observed).mean().alias("observed_rate"),
            pl.col(probability).mean().alias("mean_probability"),
        )
        .filter(pl.col("players") >= minimum_players)
        .with_columns(
            (pl.col("mean_probability") - pl.col("observed_rate")).alias(
                "calibration_gap"
            )
        )
        .sort(group)
        .to_dicts()
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--history-root", type=Path,
        default=Path("reports/generated/opportunity-history-sources-v2/tables"),
    )
    parser.add_argument(
        "--membership-path", type=Path,
        default=Path(
            "reports/generated/opportunity-40man-history/tables/"
            "historical_40man_membership.parquet"
        ),
    )
    parser.add_argument(
        "--skill-path", type=Path,
        default=Path(
            "reports/generated/phase2-arrival-skill-source/tables/"
            "affiliated_pitching_components.parquet"
        ),
    )
    parser.add_argument(
        "--demographics-path", type=Path,
        default=Path(
            "reports/generated/player-demographics/tables/player-demographics.parquet"
        ),
    )
    parser.add_argument(
        "--output-json", type=Path,
        default=Path("docs/prospect-horizon-extrapolation-result.json"),
    )
    parser.add_argument(
        "--output-md", type=Path,
        default=Path("docs/prospect-horizon-extrapolation-result.md"),
    )
    args = parser.parse_args()

    snapshots = pl.read_parquet(args.history_root / "pitcher_snapshots.parquet")
    stats = _history_stats(args.history_root)
    membership = pl.read_parquet(args.membership_path)
    skill = pl.read_parquet(args.skill_path)
    demographics = pl.read_parquet(args.demographics_path)
    debut_dates = pl.read_parquet(
        "reports/generated/career-mlb-outcome-inventory-2009-2025/tables/people-debut-dates.parquet"
    )
    training = build_arrival_cohort(
        snapshots, stats, membership, skill, debut_dates,
        snapshot_year=2018, horizon=2, player_type="pitcher",
        demographics=demographics,
    )
    outer_features = build_arrival_cohort(
        snapshots, stats, membership, skill, debut_dates,
        snapshot_year=2021, horizon=2, player_type="pitcher",
        demographics=demographics,
    )
    outer_outcomes = build_arrival_cohort(
        snapshots, stats, membership, skill, debut_dates,
        snapshot_year=2021, horizon=4, player_type="pitcher",
        demographics=demographics,
    ).select(
        "player_id", "arrived_within_horizon", "meaningful_role_within_horizon",
        "established_role_within_horizon",
    )

    arrival_fit = fit_arrival_model(training, player_type="pitcher")
    scored = predict_arrival(arrival_fit, outer_features)
    meaningful_direct_fit = fit_arrival_model(
        training,
        player_type="pitcher",
        target_column="meaningful_role_within_horizon",
        outcome_name="meaningful_role",
        feature_set="core",
    )
    scored = predict_arrival(meaningful_direct_fit, scored)
    established_direct_fit = fit_arrival_model(
        training,
        player_type="pitcher",
        target_column="established_role_within_horizon",
        outcome_name="established_role",
        feature_set="core",
    )
    scored = predict_arrival(established_direct_fit, scored)
    meaningful_fit = fit_arrival_model(
        training.filter(pl.col("arrived_within_horizon") == 1),
        player_type="pitcher",
        target_column="meaningful_role_within_horizon",
        outcome_name="meaningful_given_arrival",
        feature_set="core",
    )
    scored = predict_arrival(meaningful_fit, scored)
    established_fit = fit_arrival_model(
        training.filter(pl.col("meaningful_role_within_horizon") == 1),
        player_type="pitcher",
        target_column="established_role_within_horizon",
        outcome_name="established_given_meaningful",
        feature_set="core",
    )
    scored = predict_arrival(established_fit, scored).join(
        outer_outcomes, on="player_id", how="inner", validate="1:1",
        suffix="_four_year",
    )
    p_arrival = "predicted_two_year_arrival_probability"
    p_meaningful = "predicted_two_year_meaningful_given_arrival_probability"
    p_established = "predicted_two_year_established_given_meaningful_probability"
    p_meaningful_direct = "predicted_two_year_meaningful_role_probability"
    p_established_direct = "predicted_two_year_established_role_probability"
    scored = scored.with_columns(
        (1 - (1 - pl.col(p_arrival)) ** 2).alias("four_year_arrival_probability"),
        (1 - (1 - pl.col(p_meaningful)) ** 2).alias(
            "four_year_meaningful_given_arrival_probability"
        ),
        (1 - (1 - pl.col(p_established)) ** 2).alias(
            "four_year_established_given_meaningful_probability"
        ),
        (pl.col(p_arrival) * pl.col(p_meaningful)).alias(
            "two_year_nested_meaningful_probability"
        ),
        (1 - (1 - pl.col(p_meaningful_direct)) ** 2).alias(
            "four_year_direct_meaningful_probability"
        ),
        (1 - (1 - pl.col(p_established_direct)) ** 2).alias(
            "four_year_direct_established_probability"
        ),
    ).with_columns(
        (
            pl.col("four_year_arrival_probability")
            * pl.col("four_year_meaningful_given_arrival_probability")
        ).alias("four_year_nested_meaningful_probability")
        ,
        (
            pl.col("two_year_nested_meaningful_probability")
            * pl.col(p_established)
        ).alias("two_year_nested_established_probability"),
    ).with_columns(
        (
            pl.col("four_year_nested_meaningful_probability")
            * pl.col("four_year_established_given_meaningful_probability")
        ).alias("four_year_nested_established_probability")
        ,
        pl.when(pl.col("age_years") < 21)
        .then(pl.lit("under_21"))
        .when(pl.col("age_years") < 24)
        .then(pl.lit("21_to_23"))
        .otherwise(pl.lit("24_plus"))
        .alias("age_band"),
        pl.min_horizontal(
            "four_year_nested_meaningful_probability",
            "four_year_direct_meaningful_probability",
        ).alias("four_year_capped_meaningful_probability"),
    ).with_columns(
        pl.min_horizontal(
            "four_year_nested_established_probability",
            "four_year_direct_established_probability",
            "four_year_capped_meaningful_probability",
        ).alias("four_year_capped_established_probability"),
    )

    comparisons = {
        "arrival": {
            "unextrapolated_two_year_probability": _clean_metrics(
                scored, p_arrival, "arrived_within_horizon_four_year"
            ),
            "constant_hazard_four_year_probability": _clean_metrics(
                scored, "four_year_arrival_probability",
                "arrived_within_horizon_four_year",
            ),
        },
        "meaningful": {
            "unextrapolated_two_year_probability": _clean_metrics(
                scored, "two_year_nested_meaningful_probability",
                "meaningful_role_within_horizon_four_year",
            ),
            "constant_hazard_four_year_probability": _clean_metrics(
                scored, "four_year_nested_meaningful_probability",
                "meaningful_role_within_horizon_four_year",
            ),
            "direct_unconditional_four_year_probability": _clean_metrics(
                scored, "four_year_direct_meaningful_probability",
                "meaningful_role_within_horizon_four_year",
            ),
            "direct_capped_nested_four_year_probability": _clean_metrics(
                scored, "four_year_capped_meaningful_probability",
                "meaningful_role_within_horizon_four_year",
            ),
        },
        "established": {
            "unextrapolated_two_year_probability": _clean_metrics(
                scored, "two_year_nested_established_probability",
                "established_role_within_horizon_four_year",
            ),
            "constant_hazard_four_year_probability": _clean_metrics(
                scored, "four_year_nested_established_probability",
                "established_role_within_horizon_four_year",
            ),
            "direct_unconditional_four_year_probability": _clean_metrics(
                scored, "four_year_direct_established_probability",
                "established_role_within_horizon_four_year",
            ),
            "direct_capped_nested_four_year_probability": _clean_metrics(
                scored, "four_year_capped_established_probability",
                "established_role_within_horizon_four_year",
            ),
        },
    }
    subgroup_calibration = {
        outcome: {
            group: _subgroup_calibration(
                scored,
                group=group,
                probability=probability,
                observed=observed,
            )
            for group in ("level_tier", "age_band", "pitch_hand", "role_tier")
        }
        for outcome, probability, observed in (
            (
                "arrival", "four_year_arrival_probability",
                "arrived_within_horizon_four_year",
            ),
            (
                "meaningful", "four_year_nested_meaningful_probability",
                "meaningful_role_within_horizon_four_year",
            ),
            (
                "established", "four_year_nested_established_probability",
                "established_role_within_horizon_four_year",
            ),
        )
    }
    report = {
        "report_schema_version": "0.1",
        "as_of_date": args.as_of_date.isoformat(),
        "status": "development_horizon_extrapolation_audit_complete",
        "player_type": "pitcher",
        "training_snapshot": 2018,
        "training_outcome_years": [2019, 2020],
        "outer_snapshot": 2021,
        "outer_outcome_years": [2022, 2025],
        "training_players": training.height,
        "outer_players": scored.height,
        "comparisons": comparisons,
        "subgroup_calibration": subgroup_calibration,
        "decision": (
            "diagnostic only; the four-year outcomes test the deployed hazard shape "
            "but this period is not a fresh untouched confirmation set"
        ),
        "limitations": [
            "The 2018 two-year training outcome includes the shortened 2020 season.",
            "The 2021 cohort has already appeared in earlier two-year development work.",
            "This tests hurdle probabilities, not conditional WAR rate accuracy.",
        ],
    }
    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    arrival = comparisons["arrival"]["constant_hazard_four_year_probability"]
    meaningful = comparisons["meaningful"]["constant_hazard_four_year_probability"]
    established = comparisons["established"]["constant_hazard_four_year_probability"]
    capped_meaningful = comparisons["meaningful"][
        "direct_capped_nested_four_year_probability"
    ]
    capped_established = comparisons["established"][
        "direct_capped_nested_four_year_probability"
    ]
    raw_arrival = comparisons["arrival"]["unextrapolated_two_year_probability"]
    raw_meaningful = comparisons["meaningful"]["unextrapolated_two_year_probability"]
    largest_meaningful_gap = max(
        (
            row
            for rows in subgroup_calibration["meaningful"].values()
            for row in rows
        ),
        key=lambda row: float(row["calibration_gap"]),
    )
    markdown = f"""# Prospect pitcher horizon-extrapolation audit

**Status:** development diagnostic; not a promotion gate

The deployed prospect hurdle turns a two-year probability into a longer horizon by
repeating a constant hazard. This audit fits only the 2018 pitcher snapshot and its
2019-2020 outcomes, then evaluates the 2021 snapshot against four completed seasons
from 2022 through 2025. All {scored.height:,} eligible pitchers remain in the sample,
including non-arrivals.

| Four-year outcome | Observed | Predicted | Brier | Log loss |
|---|---:|---:|---:|---:|
| Any MLB arrival | {arrival['observed_rate']:.2%} | {arrival['mean_probability']:.2%} | {arrival['brier']:.5f} | {arrival['log_loss']:.5f} |
| Meaningful role | {meaningful['observed_rate']:.2%} | {meaningful['mean_probability']:.2%} | {meaningful['brier']:.5f} | {meaningful['log_loss']:.5f} |
| Established role | {established['observed_rate']:.2%} | {established['mean_probability']:.2%} | {established['brier']:.5f} | {established['log_loss']:.5f} |

The direct-evidence cap lowers meaningful-role Brier from
{meaningful['brier']:.5f} to {capped_meaningful['brier']:.5f} and log loss from
{meaningful['log_loss']:.5f} to {capped_meaningful['log_loss']:.5f}. For established
roles it changes Brier from {established['brier']:.5f} to
{capped_established['brier']:.5f} and log loss from {established['log_loss']:.5f} to
{capped_established['log_loss']:.5f}.

The repeated-hazard form is not causing low probabilities. It is more optimistic than
the outcomes and worsens both Brier and log-loss scores versus leaving the two-year
arrival probability unchanged ({raw_arrival['brier']:.5f} versus
{arrival['brier']:.5f}; {raw_arrival['log_loss']:.5f} versus
{arrival['log_loss']:.5f}). It also worsens the meaningful-role Brier score
({raw_meaningful['brier']:.5f} versus {meaningful['brier']:.5f}). The largest
supported meaningful-role calibration gap is
{largest_meaningful_gap['calibration_gap']:.1%}. The subgroup tables in the JSON
cover level, age band, throwing hand, and starter/reliever role.

This is a useful check of the probability chain, not an untouched confirmation set.
The 2018 training label includes shortened 2020, and the 2021 cohort has appeared in
earlier two-year work. It also does not test pitcher WAR conditional on reaching MLB.
No current value changes can be justified from this result alone.
"""
    args.output_md.write_text(markdown, encoding="utf-8")
    print(json.dumps({
        "players": scored.height,
        "arrival_observed": arrival["observed_rate"],
        "arrival_predicted": arrival["mean_probability"],
        "meaningful_observed": meaningful["observed_rate"],
        "meaningful_predicted": meaningful["mean_probability"],
        "established_observed": established["observed_rate"],
        "established_predicted": established["mean_probability"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
