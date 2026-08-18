#!/usr/bin/env python3
"""Score the final selective position-role development challenger."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl


THRESHOLD = 0.65
SOURCE_RUN_ID = 32152125644
SOURCE_ARTIFACT = "position-role-transition-challenger-development"
SOURCE_ARTIFACT_DIGEST = "sha256:4e98081cb1800d45f3668595e4e61a169dbce68a8b565aa1e8f60d7dcd1417e5"


def _find_one(root: Path, filename: str) -> Path:
    matches = sorted(root.rglob(filename))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {filename!r} below {root}, found {len(matches)}")
    return matches[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/position-role-selective-transition"),
    )
    args = parser.parse_args()

    frame = pl.read_parquet(_find_one(args.source_root, "predictions.parquet")).with_columns(
        (pl.col("current_primary_share") >= THRESHOLD).alias("smoothing_active")
    ).with_columns(
        pl.when(pl.col("smoothing_active"))
        .then(pl.col("candidate_tv"))
        .otherwise(pl.col("baseline_tv"))
        .alias("selective_tv"),
        pl.when(pl.col("smoothing_active"))
        .then(pl.col("candidate_sse"))
        .otherwise(pl.col("baseline_sse"))
        .alias("selective_sse"),
        pl.when(pl.col("smoothing_active"))
        .then(pl.col("candidate_primary_position"))
        .otherwise(pl.col("baseline_primary_position"))
        .alias("selective_primary_position"),
    ).with_columns(
        (pl.col("baseline_primary_position") == pl.col("observed_primary_position")).alias(
            "baseline_primary_correct"
        ),
        (pl.col("selective_primary_position") == pl.col("observed_primary_position")).alias(
            "selective_primary_correct"
        ),
    )

    folds = []
    for (current_season, next_season), fold in frame.group_by(
        ["current_season", "next_season"], maintain_order=True
    ):
        row = fold.select(
            pl.len().alias("scored_player_count"),
            pl.col("smoothing_active").sum().alias("smoothing_active_player_count"),
            pl.col("smoothing_active").mean().alias("smoothing_active_rate"),
            pl.col("baseline_tv").mean().alias("baseline_mean_tv"),
            pl.col("selective_tv").mean().alias("candidate_mean_tv"),
            pl.col("baseline_sse").mean().alias("baseline_mean_sse"),
            pl.col("selective_sse").mean().alias("candidate_mean_sse"),
            pl.col("baseline_primary_correct").mean().alias("baseline_primary_match_rate"),
            pl.col("selective_primary_correct").mean().alias("candidate_primary_match_rate"),
        ).row(0, named=True)
        baseline_tv = float(row["baseline_mean_tv"])
        candidate_tv = float(row["candidate_mean_tv"])
        baseline_sse = float(row["baseline_mean_sse"])
        candidate_sse = float(row["candidate_mean_sse"])
        passed = candidate_tv < baseline_tv and candidate_sse < baseline_sse
        folds.append(
            {
                "current_season": int(current_season),
                "next_season": int(next_season),
                "scored_player_count": int(row["scored_player_count"]),
                "smoothing_active_player_count": int(row["smoothing_active_player_count"]),
                "smoothing_active_rate": float(row["smoothing_active_rate"]),
                "baseline_mean_tv": baseline_tv,
                "candidate_mean_tv": candidate_tv,
                "tv_absolute_improvement": baseline_tv - candidate_tv,
                "tv_relative_improvement": (baseline_tv - candidate_tv) / baseline_tv,
                "baseline_mean_sse": baseline_sse,
                "candidate_mean_sse": candidate_sse,
                "sse_absolute_improvement": baseline_sse - candidate_sse,
                "sse_relative_improvement": (baseline_sse - candidate_sse) / baseline_sse,
                "baseline_primary_match_rate": float(row["baseline_primary_match_rate"]),
                "candidate_primary_match_rate": float(row["candidate_primary_match_rate"]),
                "passed": passed,
            }
        )

    folds = sorted(folds, key=lambda row: (row["current_season"], row["next_season"]))
    expected = [(2022, 2023), (2023, 2024)]
    observed = [(row["current_season"], row["next_season"]) for row in folds]
    if observed != expected:
        raise ValueError(f"unexpected development fold inventory: {observed}")

    candidate_passed = all(bool(row["passed"]) for row in folds)
    report = {
        "report_schema_version": "0.1",
        "gate": "position_role_selective_transition_final_development",
        "contract": "docs/position-role-selective-transition-contract.md",
        "source": {
            "run_id": SOURCE_RUN_ID,
            "artifact_name": SOURCE_ARTIFACT,
            "artifact_digest": SOURCE_ARTIFACT_DIGEST,
        },
        "candidate": {
            "name": "primary_share_thresholded_transition_mean_v1",
            "primary_share_threshold": THRESHOLD,
            "formula": "carry_forward if s < 0.65 else s * current_profile + (1 - s) * prior_history_mean_next_profile_by_current_primary_position",
            "new_hyperparameter_search": False,
        },
        "boundary": {
            "2025_position_source_accessed": False,
            "2025_position_outcomes_scored": False,
            "first_challenger_transition_means_refit": False,
            "threshold_changed_after_contract": False,
            "team_allocator_fit": False,
            "defense_model_fit": False,
        },
        "folds": folds,
        "decision": {
            "candidate_passed_development": candidate_passed,
            "2025_position_role_confirmation_authorized": candidate_passed,
            "additional_position_role_development_challenger_authorized": False,
            "team_allocator_authorized": False,
            "defense_model_authorized": False,
        },
    }

    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    frame.select(
        "current_season",
        "next_season",
        "player_id",
        "current_primary_position",
        "current_primary_share",
        "smoothing_active",
        "baseline_tv",
        "selective_tv",
        "baseline_sse",
        "selective_sse",
        "observed_primary_position",
        "baseline_primary_position",
        "selective_primary_position",
    ).write_parquet(args.output_root / "selective_predictions.parquet")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
