#!/usr/bin/env python
"""Independent-season confirmation of the pre-specified MLB bin-value policy.

The 2024 primary audit nominated lambda=5 prior-equivalent occurrences as the
smallest positive AL<->NL same-bin shrinkage strength that matched or improved
direct estimates on every primary split-half and five-fold metric.  This script
freezes that choice and tests it unchanged on 2023.

This is deliberately an audit-only wrapper around the exact primary-audit
implementation so the confirmation cannot drift to a subtly different RE24,
contact classification, schedule sampling, or scoring definition.
"""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

import audit_mlb_bin_value_policy as primary
from universal_baseball.official_capture import new_official_session


SEASON = 2023
CONFIRMATION_STRENGTH = 5
REPORT_DIR = Path("reports/generated/mlb-bin-value-independent-validation")
WORK_DIR = Path("data/quarantine/mlb-bin-value-independent-validation")
METRICS = (*primary.PRIMARY_METRICS, "occurrence_weighted_cell_mae")


def _configure_primary_for_confirmation() -> None:
    # The primary audit predates parameterized season helpers.  Keep this
    # mutation local to this one-off audit wrapper rather than duplicating the
    # state/re24/contact implementation and risking methodological drift.
    primary.SEASON = SEASON
    primary.RETROSHEET_URL = f"https://www.retrosheet.org/downloads/plays/{SEASON}plays.zip"
    primary.WORK_DIR = WORK_DIR
    primary.REPORT_DIR = REPORT_DIR


def _metric_comparison(
    direct: dict[str, float | int],
    candidate: dict[str, float | int],
) -> dict[str, dict[str, float | bool]]:
    return {
        metric: {
            "direct": float(direct[metric]),
            "lambda_5": float(candidate[metric]),
            "delta_lambda_5_minus_direct": float(candidate[metric]) - float(direct[metric]),
            "passes": float(candidate[metric]) <= float(direct[metric]),
        }
        for metric in METRICS
    }


def main() -> int:
    _configure_primary_for_confirmation()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    matrix, retrosheet_meta = primary._load_retrosheet_matrix()
    candidates, schedule_meta = primary._schedule_candidates()
    selected = {
        league_id: primary._spread_sample(rows, primary.GAMES_PER_LEAGUE)
        for league_id, rows in candidates.items()
    }

    frames: dict[int, list[pl.DataFrame]] = {
        league_id: [] for league_id in primary.LEAGUES
    }
    session = new_official_session()
    try:
        for league_id in sorted(selected):
            for game in selected[league_id]:
                frames[league_id].append(primary._process_game(game, matrix, session=session))
    finally:
        session.close()

    strengths = [0, CONFIRMATION_STRENGTH]
    split_rows, cv_rows = primary._evaluate(frames, strengths)
    split_eval = primary._evaluation_table(split_rows, strengths)
    cv_eval = primary._evaluation_table(cv_rows, strengths)

    split_direct = next(row for row in split_eval if int(row["prior_strength"]) == 0)
    split_candidate = next(
        row for row in split_eval if int(row["prior_strength"]) == CONFIRMATION_STRENGTH
    )
    cv_direct = next(row for row in cv_eval if int(row["prior_strength"]) == 0)
    cv_candidate = next(
        row for row in cv_eval if int(row["prior_strength"]) == CONFIRMATION_STRENGTH
    )

    split_comparison = _metric_comparison(split_direct, split_candidate)
    cv_comparison = _metric_comparison(cv_direct, cv_candidate)
    confirmation_pass = all(
        row["passes"]
        for comparison in (split_comparison, cv_comparison)
        for row in comparison.values()
    )

    payload = {
        "report_schema_version": 1,
        "status": (
            "independent_confirmation_pass"
            if confirmation_pass
            else "independent_confirmation_fail"
        ),
        "season": SEASON,
        "pre_specified_strength": CONFIRMATION_STRENGTH,
        "games_per_league": primary.GAMES_PER_LEAGUE,
        "fold_count": primary.FOLD_COUNT,
        "retrosheet": retrosheet_meta,
        "schedule": schedule_meta,
        "selected_games": {
            primary.LEAGUES[league_id]: selected[league_id]
            for league_id in sorted(selected)
        },
        "event_counts": {
            primary.LEAGUES[league_id]: sum(frame.height for frame in frames[league_id])
            for league_id in sorted(frames)
        },
        "split_half": {
            "direct": split_direct,
            "lambda_5": split_candidate,
            "comparison": split_comparison,
        },
        "five_fold": {
            "direct": cv_direct,
            "lambda_5": cv_candidate,
            "comparison": cv_comparison,
        },
        "confirmation_pass": confirmation_pass,
        "decision_rule": (
            "The pre-specified 2024 nominee lambda=5 is accepted only if it matches "
            "or improves the direct baseline on cell MAE, cell RMSE, event MAE, "
            "event RMSE, and occurrence-weighted cell MAE in both the 2023 "
            "bidirectional split-half and five-fold tests. No alternative strength "
            "may be selected after observing this confirmation season."
        ),
    }
    (REPORT_DIR / "mlb_bin_value_independent_validation.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    pl.DataFrame(split_rows).write_csv(REPORT_DIR / "split_half_prediction_cells.csv")
    pl.DataFrame(cv_rows).write_csv(REPORT_DIR / "cross_validation_prediction_cells.csv")

    lines = [
        "# Independent MLB Performance-bin value confirmation — 2023",
        "",
        f"- Pre-specified AL/NL peer prior strength: **{CONFIRMATION_STRENGTH}**",
        f"- Games per AL/NL environment: {primary.GAMES_PER_LEAGUE}",
        f"- Core events — AL / NL: {payload['event_counts']['AL']:,} / {payload['event_counts']['NL']:,}",
        f"- Confirmation pass: **{confirmation_pass}**",
        "",
        "## Split-half",
        "",
    ]
    for metric in METRICS:
        row = split_comparison[metric]
        lines.append(
            f"- {metric}: direct={row['direct']:.6f}, lambda=5={row['lambda_5']:.6f}, "
            f"delta={row['delta_lambda_5_minus_direct']:+.6f}, pass={row['passes']}"
        )
    lines.extend(["", "## Five-fold", ""])
    for metric in METRICS:
        row = cv_comparison[metric]
        lines.append(
            f"- {metric}: direct={row['direct']:.6f}, lambda=5={row['lambda_5']:.6f}, "
            f"delta={row['delta_lambda_5_minus_direct']:+.6f}, pass={row['passes']}"
        )
    lines.extend(
        [
            "",
            "No alternative shrinkage strength is considered in this confirmation gate.",
        ]
    )
    (REPORT_DIR / "mlb_bin_value_independent_validation.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    if not confirmation_pass:
        raise RuntimeError(
            "pre-specified MLB lambda=5 failed independent 2023 confirmation; "
            "production MLB bin values must remain direct"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
