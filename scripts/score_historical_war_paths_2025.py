#!/usr/bin/env python3
"""Score frozen 2025 expected WAR against a neutral like-for-like proxy."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from universal_baseball.historical_war_scoring import (
    score_hitter_neutral_war,
    score_pitcher_neutral_war,
    whole_player_war_metrics,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


def main() -> int:
    projection_root = Path("reports/generated/historical-projection-paths/2025-03-27")
    skill_root = Path("reports/generated/free-agent-historical-skill-source/2025-12-31")
    hitter_path = projection_root / "tables/hitter-expected-war-paths.parquet"
    pitcher_path = projection_root / "tables/pitcher-expected-war-paths.parquet"
    hitting_path = skill_root / "tables/mlb_hitting_components.parquet"
    pitching_path = skill_root / "tables/mlb_pitching_components.parquet"
    output = Path("reports/generated/historical-war-score/2025-03-27")

    projection_report_path = projection_root / "report.json"
    projection_report = json.loads(
        projection_report_path.read_text(encoding="utf-8")
    )
    if projection_report["boundaries"]["2025_outcomes_used"]:
        raise ValueError("historical projection artifact claims 2025 outcome use")
    skill_report_path = skill_root / "report.json"
    skill_report = json.loads(skill_report_path.read_text(encoding="utf-8"))
    runs_per_win = float(skill_report["reference_environment"]["runs_per_win"])

    hitter = pl.read_parquet(hitter_path).filter(pl.col("season") == 2025)
    pitcher = pl.read_parquet(pitcher_path).filter(pl.col("season") == 2025)
    hitting = pl.read_parquet(hitting_path)
    pitching = pl.read_parquet(pitching_path)
    hitter_scores, hitter_metrics = score_hitter_neutral_war(
        hitter,
        hitting.filter(pl.col("season") == 2025),
        hitting.filter(pl.col("season") == 2024),
        runs_per_win=runs_per_win,
    )
    pitcher_scores, pitcher_metrics = score_pitcher_neutral_war(
        pitcher,
        pitching.filter(pl.col("season") == 2025),
        pitching.filter(pl.col("season") == 2024),
        runs_per_win=runs_per_win,
    )
    whole_player, whole_player_metrics = whole_player_war_metrics(
        hitter_scores, pitcher_scores
    )

    output.mkdir(parents=True, exist_ok=True)
    storage = {
        "hitter_scores": write_canonical_parquet(
            hitter_scores,
            output / "hitter-neutral-war-scores.parquet",
            table_name="historical_2025_hitter_neutral_war_scores",
        ).as_record(),
        "pitcher_scores": write_canonical_parquet(
            pitcher_scores,
            output / "pitcher-neutral-war-scores.parquet",
            table_name="historical_2025_pitcher_neutral_war_scores",
        ).as_record(),
        "whole_player_scores": write_canonical_parquet(
            whole_player,
            output / "whole-player-neutral-war-scores.parquet",
            table_name="historical_2025_whole_player_neutral_war_scores",
        ).as_record(),
    }
    report = {
        "report_schema_version": "0.1",
        "gate": "historical_2025_frozen_neutral_war_score",
        "checkpoint_date": "2025-03-27",
        "target_season": 2025,
        "hitter": hitter_metrics,
        "pitcher": pitcher_metrics,
        "whole_player": whole_player_metrics,
        "boundaries": {
            "projection_refit_after_outcome_access": False,
            "model_form_changed": False,
            "rate_clipping_added": False,
            "realized_war_definition": (
                "same neutral event weights, 2024 run environment, projected position, "
                "average-zero baserunning and defense"
            ),
            "published_war_comparison": False,
            "ranking_status": "diagnostic_replay_not_publishable_ranking",
        },
        "source_files": {
            path.as_posix(): sha256_file(path)
            for path in (
                hitter_path,
                pitcher_path,
                hitting_path,
                pitching_path,
                projection_report_path,
                skill_report_path,
            )
        },
        "storage": storage,
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {key: value for key, value in report.items() if key != "storage"},
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
