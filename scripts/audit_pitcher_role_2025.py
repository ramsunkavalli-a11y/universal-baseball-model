#!/usr/bin/env python3
"""Audit saved pitcher role probabilities against completed 2025 MLB usage."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.pitcher_opportunity_paths import pitcher_role


ROLES = ("starter", "swingman", "reliever")


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--forecast-path", type=Path,
        default=Path(
            "reports/generated/historical-projection-paths/2025-03-27/tables/"
            "pitcher-expected-war-paths.parquet"
        ),
    )
    parser.add_argument(
        "--history-root", type=Path,
        default=Path("reports/generated/opportunity-history-sources-v2/tables"),
    )
    parser.add_argument(
        "--output-json", type=Path,
        default=Path("docs/pitcher-role-2025-audit-result.json"),
    )
    return parser.parse_args()


def _scores(frame: pl.DataFrame) -> dict[str, object]:
    probabilities = frame.select(
        "starter_probability_if_active",
        "swingman_probability_if_active",
        "reliever_probability_if_active",
    ).to_numpy()
    observed = np.asarray([ROLES.index(value) for value in frame["observed_role"]])
    one_hot = np.eye(3)[observed]
    chosen = np.clip(probabilities[np.arange(len(observed)), observed], 1e-12, 1)
    role_shares = {
        role: {
            "predicted": float(probabilities[:, index].mean()),
            "observed": float((observed == index).mean()),
        }
        for index, role in enumerate(ROLES)
    }
    starter_probability = probabilities[:, 0]
    starter_observed = (observed == 0).astype(float)
    ordered = np.argsort(starter_probability, kind="stable")
    bins = []
    for number, indices in enumerate(np.array_split(ordered, 5), start=1):
        bins.append(
            {
                "bin": number,
                "players": int(len(indices)),
                "predicted_starter_rate": float(starter_probability[indices].mean()),
                "observed_starter_rate": float(starter_observed[indices].mean()),
            }
        )
    return {
        "players": frame.height,
        "log_loss": float(-np.log(chosen).mean()),
        "brier": float(np.square(probabilities - one_hot).sum(axis=1).mean()),
        "accuracy": float((probabilities.argmax(axis=1) == observed).mean()),
        "role_shares": role_shares,
        "starter_reliability": bins,
        "coverage_tiers": frame.group_by("coverage_tier").len().sort("coverage_tier").to_dicts(),
    }


def main() -> int:
    args = _args()
    forecast = (
        pl.read_parquet(args.forecast_path)
        .filter(pl.col("season") == 2025)
        .select(
            "player_id", "starter_probability_if_active",
            "swingman_probability_if_active", "reliever_probability_if_active",
            "coverage_tier", "role_model_id",
        )
    )
    history_paths = sorted(
        args.history_root.glob("*/affiliated_season_stats.parquet")
    )
    history = pl.concat(
        [pl.read_parquet(path) for path in history_paths], how="vertical_relaxed"
    ).filter(pl.col("stat_group") == "pitching")
    actual = (
        history.filter((pl.col("season") == 2025) & (pl.col("sport_id") == 1))
        .group_by("player_id")
        .agg(
            pl.col("batters_faced").sum().alias("observed_bf"),
            pl.col("games").sum().alias("observed_games"),
            pl.col("starts").sum().alias("observed_starts"),
        )
        .filter(pl.col("observed_bf") > 0)
        .with_columns(
            pl.struct("observed_games", "observed_starts").map_elements(
                lambda row: pitcher_role(
                    games=int(row["observed_games"]),
                    starts=int(row["observed_starts"]),
                ),
                return_dtype=pl.String,
            ).alias("observed_role")
        )
    )
    prior_mlb = set(
        history.filter((pl.col("season") < 2025) & (pl.col("sport_id") == 1))
        .group_by("player_id")
        .agg(pl.col("batters_faced").sum())
        .filter(pl.col("batters_faced") > 0)
        .get_column("player_id")
        .to_list()
    )
    scored = forecast.join(actual, on="player_id", how="inner", validate="1:1").sort(
        "player_id"
    )
    no_prior_mlb = scored.filter(~pl.col("player_id").is_in(prior_mlb))
    report = {
        "report_schema_version": "0.1",
        "as_of_date": args.as_of_date.isoformat(),
        "status": "pitcher_role_2025_audit_complete",
        "contract": "docs/pitcher-role-2025-audit-plan.md",
        "all_active_pitchers": _scores(scored),
        "no_prior_mlb_pitchers": _scores(no_prior_mlb),
        "boundaries": {
            "role_is_conditional_on_positive_mlb_bf": True,
            "outside_fv_used": False,
            "current_2026_outcomes_used": False,
            "model_changed": False,
        },
    }
    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
