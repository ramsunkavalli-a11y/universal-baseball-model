#!/usr/bin/env python3
"""Materialize the validated post-arrival progression equations for simulation."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from audit_prospect_post_arrival_workload import _rows
from universal_baseball.prospect_mlb_progression import fit_progression
from universal_baseball.storage import sha256_file, write_canonical_parquet


OUTPUT = Path("model_artifacts/prospect-post-arrival-progression-2025")
RESULT = Path("docs/prospect-post-arrival-workload-result.json")
RUNNER = Path("scripts/materialize_prospect_post_arrival_progression_model.py")
FEATURE_NAMES = {
    "age_elapsed": (
        "transition_age_centered_scaled",
        "elapsed_year_centered_scaled",
        "elapsed_year_at_least_three",
    ),
    "age_elapsed_prior_workload": (
        "transition_age_centered_scaled",
        "elapsed_year_centered_scaled",
        "elapsed_year_at_least_three",
        "prior_mlb_active",
        "log1p_prior_workload_vs_active_mean",
    ),
}
SELECTED_FEATURE = {
    "FRINGE_MLB": "age_elapsed_prior_workload",
    "MEANINGFUL_MLB": "age_elapsed",
}


def _source_paths() -> list[Path]:
    root = Path("reports/generated")
    history = root / "opportunity-history-sources-v2/tables"
    paths = [
        RESULT,
        Path("scripts/audit_prospect_post_arrival_workload.py"),
        Path("scripts/audit_prospect_ordered_transition_path.py"),
        Path("src/universal_baseball/prospect_mlb_progression.py"),
        history / "hitter_snapshots.parquet",
        history / "pitcher_snapshots.parquet",
        root / "opportunity-40man-history/tables/historical_40man_membership.parquet",
        root / "player-demographics/tables/player-demographics.parquet",
        root / "phase2-arrival-skill-source/tables/affiliated_hitting_components.parquet",
        root / "phase2-arrival-skill-source/tables/affiliated_pitching_components.parquet",
        root / "career-mlb-outcome-inventory-2009-2025/tables/people-debut-dates.parquet",
        root / "career-mlb-outcome-inventory-2009-2025/tables/mlb_batting_2009_2025.parquet",
        root / "career-mlb-outcome-inventory-2009-2025/tables/mlb_pitching_2009_2025.parquet",
        *sorted(history.glob("*/affiliated_season_stats.parquet")),
    ]
    if missing := [path for path in paths if not path.exists()]:
        raise FileNotFoundError(f"progression model sources missing: {missing}")
    return paths


def main() -> int:
    selected = json.loads(RESULT.read_text(encoding="utf-8"))
    coefficient_rows: list[dict[str, object]] = []
    support_rows: list[dict[str, object]] = []
    for player_type in ("hitter", "pitcher"):
        rows = _rows(player_type).filter(pl.col("outcome_year") <= 2025)
        for origin_state, feature_set in SELECTED_FEATURE.items():
            regularization = float(
                selected[player_type]["selected_regularization"][origin_state][feature_set]
            )
            fit = fit_progression(
                rows,
                origin_state=origin_state,
                feature_set=feature_set,
                regularization_c=regularization,
            )
            cell = rows.filter(pl.col("from_state") == origin_state)
            coefficient_rows.append(
                {
                    "player_type": player_type,
                    "origin_state": origin_state,
                    "feature_set": feature_set,
                    "term": "intercept",
                    "coefficient": float(fit.model.intercept_[0]),
                    "regularization_c": regularization,
                }
            )
            coefficient_rows.extend(
                {
                    "player_type": player_type,
                    "origin_state": origin_state,
                    "feature_set": feature_set,
                    "term": term,
                    "coefficient": float(value),
                    "regularization_c": regularization,
                }
                for term, value in zip(
                    FEATURE_NAMES[feature_set], fit.model.coef_[0], strict=True
                )
            )
            support_rows.append(
                {
                    "player_type": player_type,
                    "origin_state": origin_state,
                    "feature_set": feature_set,
                    "players": cell.height,
                    "advances": int(cell["advanced"].sum()),
                    "minimum_outcome_year": int(cell["outcome_year"].min()),
                    "maximum_outcome_year": int(cell["outcome_year"].max()),
                }
            )
    coefficients = pl.DataFrame(coefficient_rows).sort(
        "player_type", "origin_state", "term"
    )
    support = pl.DataFrame(support_rows).sort("player_type", "origin_state")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    storage = {
        "coefficients": write_canonical_parquet(
            coefficients,
            OUTPUT / "coefficients.parquet",
            table_name="prospect_post_arrival_progression_coefficients_2025",
        ).as_record(),
        "support": write_canonical_parquet(
            support,
            OUTPUT / "support.parquet",
            table_name="prospect_post_arrival_progression_support_2025",
        ).as_record(),
    }
    report = {
        "report_schema_version": "0.1",
        "status": "validated_equations_materialized_not_integrated",
        "training_outcomes_through": 2025,
        "shortened_2020_outcomes_excluded": True,
        "fringe_uses_prior_sampled_workload": True,
        "meaningful_uses_pooled_age_elapsed_fallback": True,
        "pitcher_role_used": False,
        "outside_fv_used": False,
        "production_changed": False,
        "runner_path": RUNNER.as_posix(),
        "runner_sha256": sha256_file(RUNNER),
        "sources": {path.as_posix(): sha256_file(path) for path in _source_paths()},
        "storage": storage,
    }
    (OUTPUT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({**report, "sources": f"{len(report['sources'])} files"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
