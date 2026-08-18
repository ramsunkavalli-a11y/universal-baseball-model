#!/usr/bin/env python3
"""Audit whether two 2024 source-only player-game rows are exact removable residuals.

Diagnostic only.  For each already-frozen case, compare resolved reusable
player-game outcomes to the independent season aggregate before and after
removing only the disputed game.  Also compare the after-removal outcome vector
to the official player gameLog aggregate.  No source mutation, Projection fit,
scoring, or 2025 access occurs here.
"""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

import materialize_current_talent_historical_milb_game_evidence as historical
from universal_baseball.current_talent_era import current_talent_level_spec
from universal_baseball.current_talent_official_outcomes import (
    official_game_log_endpoint,
    project_official_hitting_game_log,
)
from universal_baseball.current_talent_season_reconciliation import (
    reconcile_resolved_outcomes_to_season_aggregates,
)
from universal_baseball.official_capture import capture_official_json, new_official_session

SEASON = 2024
CASES = (
    {"label": "high_a", "level": "a+", "player_id": 669233, "game_id": 755829},
    {"label": "single_a", "level": "a", "player_id": 686541, "game_id": 754395},
)
OUTCOME_FIELDS = (
    "batting_PA", "batting_AB", "batting_BB", "batting_HBP",
    "batting_SO", "batting_SF", "batting_SH", "batting_CI",
)


def _sum(frame: pl.DataFrame) -> dict[str, int]:
    if frame.is_empty():
        return {field: 0 for field in OUTCOME_FIELDS}
    row = frame.select([pl.col(field).fill_null(0).sum().alias(field) for field in OUTCOME_FIELDS]).row(0, named=True)
    return {field: int(row[field] or 0) for field in OUTCOME_FIELDS}


def _comparison_row(comparison: pl.DataFrame, player_id: int) -> dict:
    rows = comparison.filter(pl.col("player_id") == int(player_id)).to_dicts()
    if len(rows) != 1:
        raise RuntimeError(f"expected one season comparison row for player={player_id}; found {len(rows)}")
    return rows[0]


def main() -> int:
    out = Path("reports/generated/projection-2024-source-only-outcome-row-audit")
    raw = out / "raw"
    work = Path("data/quarantine/projection-2024-source-only-outcome-row-audit")
    out.mkdir(parents=True, exist_ok=True)
    raw.mkdir(parents=True, exist_ok=True)
    work.mkdir(parents=True, exist_ok=True)

    github = historical._github_session()
    official_session = new_official_session()
    reports = []
    try:
        for case in CASES:
            level = str(case["level"])
            player_id = int(case["player_id"])
            game_id = int(case["game_id"])
            spec = current_talent_level_spec(SEASON, level)
            level_dir = work / ("aplus" if level == "a+" else level)
            _, _, outcomes, _ = historical._load_player_game_sources(
                season=SEASON,
                level=level,
                league_ids=spec.league_ids,
                work_dir=level_dir,
                session=github,
            )
            season_stats, _ = historical._load_season_batting(
                season=SEASON,
                level=level,
                work_dir=level_dir,
                session=github,
            )
            suspect = outcomes.filter(
                (pl.col("player_id") == player_id) & (pl.col("game_id") == game_id)
            )
            if suspect.height != 1:
                raise RuntimeError(f"expected one suspect row for {player_id}/{game_id}; found {suspect.height}")

            before, before_metrics = reconcile_resolved_outcomes_to_season_aggregates(
                outcomes, season_stats, season=SEASON,
                expected_league_ids=spec.league_ids, require_exact=False,
            )
            trimmed = outcomes.filter(
                ~((pl.col("player_id") == player_id) & (pl.col("game_id") == game_id))
            )
            after, after_metrics = reconcile_resolved_outcomes_to_season_aggregates(
                trimmed, season_stats, season=SEASON,
                expected_league_ids=spec.league_ids, require_exact=False,
            )

            endpoint = official_game_log_endpoint(
                player_id=player_id, sport_id=spec.official_sport_id, season=SEASON
            )
            capture = capture_official_json(endpoint, session=official_session)
            capture.write_raw(raw / f"{case['label']}_player_{player_id}_gamelog.json")
            official = project_official_hitting_game_log(
                capture.data, player_id=player_id, sport_id=spec.official_sport_id
            ).filter(pl.col("league_id").is_in(sorted(spec.league_ids)))

            player_before = outcomes.filter(
                (pl.col("player_id") == player_id) & pl.col("league_id").is_in(sorted(spec.league_ids))
            )
            player_after = trimmed.filter(
                (pl.col("player_id") == player_id) & pl.col("league_id").is_in(sorted(spec.league_ids))
            )
            official_positive = official.filter(pl.col("batting_PA").fill_null(0) > 0)
            before_row = _comparison_row(before, player_id)
            after_row = _comparison_row(after, player_id)
            after_totals = _sum(player_after)
            official_totals = _sum(official_positive)
            reports.append({
                **case,
                "suspect_source_row": suspect.to_dicts()[0],
                "source_totals_before": _sum(player_before),
                "source_totals_after_removal": after_totals,
                "official_game_log_totals": official_totals,
                "season_comparison_before": before_row,
                "season_comparison_after_removal": after_row,
                "before_has_any_mismatch": bool(before_row["has_any_mismatch"]),
                "after_has_any_mismatch": bool(after_row["has_any_mismatch"]),
                "after_matches_official_game_log": after_totals == official_totals,
                "exact_removable_residual": (
                    bool(before_row["has_any_mismatch"])
                    and not bool(after_row["has_any_mismatch"])
                    and after_totals == official_totals
                ),
                "before_metrics": before_metrics,
                "after_metrics": after_metrics,
                "official_game_ids": sorted(int(v) for v in official_positive.get_column("game_id").unique().to_list()),
            })
    finally:
        official_session.close()
        github.close()

    report = {
        "gate": "projection_2024_source_only_outcome_row_audit",
        "season": SEASON,
        "cases": reports,
        "boundary": {
            "source_mutated": False,
            "projection_model_fit": False,
            "projection_scoring": False,
            "accessed_2025": False,
        },
    }
    (out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")
    lines = ["# Projection 2024 source-only outcome-row audit", ""]
    for row in reports:
        lines += [
            f"## {row['label']} player {row['player_id']} / game {row['game_id']}",
            f"- suspect vector: `{ {k: row['suspect_source_row'].get(k) for k in OUTCOME_FIELDS} }`",
            f"- pre-removal season mismatch: {row['before_has_any_mismatch']}",
            f"- post-removal season mismatch: {row['after_has_any_mismatch']}",
            f"- post-removal totals match official gameLog: {row['after_matches_official_game_log']}",
            f"- exact removable residual: **{row['exact_removable_residual']}**",
            "",
        ]
    (out / "report.md").write_text("\n".join(lines))
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
