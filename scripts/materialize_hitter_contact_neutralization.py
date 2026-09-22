#!/usr/bin/env python3
"""Cross-fit context-neutral hitter contact features over the full PBP history."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path

import polars as pl

from universal_baseball.hitter_contact_neutralization import (
    aggregate_neutralized_contact_features,
    attach_neutralized_lags,
    crossfit_contact_probabilities,
    crossfit_shrunk_context_probabilities,
    prepare_terminal_contacts,
)
from universal_baseball.storage import write_canonical_parquet


DEFAULT_SEASONS = (2016, 2017, 2018, 2019, 2021, 2022, 2023, 2024)
TERMINAL_COLUMNS = (
    "season",
    "level",
    "game_pk",
    "at_bat_index",
    "terminal_pitch_number",
    "league_id",
    "batter",
    "pitcher",
    "inning",
    "outs_when_up",
    "on_1b",
    "on_2b",
    "on_3b",
    "bat_score",
    "fld_score",
    "inning_top_bot",
    "stand",
    "p_throws",
    "bb_type",
    "hc_x",
    "hc_y",
    "terminal_outcome_group",
    "defense_team",
    "is_batted_ball",
)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--terminal-root",
        type=Path,
        default=Path("data/working/pbp-opportunity-foundation-v1"),
    )
    parser.add_argument(
        "--game-context",
        type=Path,
        default=Path(
            "reports/generated/defensive-venue-context-v1/"
            "affiliated-game-context.parquet"
        ),
    )
    parser.add_argument(
        "--base-panel",
        type=Path,
        default=Path(
            "reports/generated/hitter-value-panel-v2/tables/modeling-panel.parquet"
        ),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/hitter-contact-neutralization-v1"),
    )
    parser.add_argument("--seasons", nargs="+", type=int, default=list(DEFAULT_SEASONS))
    parser.add_argument("--folds", type=int, default=2)
    parser.add_argument("--exclude-opponent-ids", action="store_true")
    parser.add_argument(
        "--method", choices=("tree", "shrunk"), default="tree"
    )
    parser.add_argument(
        "--selected-stage",
        choices=(
            "park_w025",
            "park_w050",
            "park",
            "park_defense_w025",
            "park_defense_w050",
            "park_defense",
            "park_defense_pitcher_w025",
            "park_defense_pitcher_w050",
            "park_defense_pitcher",
        ),
        default="park_defense_pitcher_w025",
    )
    parser.add_argument("--reuse-existing", action="store_true")
    return parser.parse_args()


def _load_terminal(root: Path, season: int) -> pl.DataFrame:
    paths = sorted(root.glob(f"season={season}/level=*/terminal/*.parquet"))
    if not paths:
        raise FileNotFoundError(f"no terminal PBP partitions found for {season}")
    frames = [pl.read_parquet(path, columns=list(TERMINAL_COLUMNS)) for path in paths]
    return pl.concat(frames, how="diagonal_relaxed")


def _weighted_metrics(reports: list[dict[str, object]], model: str) -> dict[str, float]:
    events = sum(int(report["events"]) for report in reports)
    key = f"{model}_metrics"
    return {
        metric: sum(
            int(report["events"]) * float(report[key][metric]) for report in reports
        )
        / events
        for metric in ("log_loss", "brier")
    }


def main() -> int:
    args = _args()
    if any(season >= 2026 for season in args.seasons):
        raise ValueError("protected 2026 outcomes cannot be materialized")
    args.output_root.mkdir(parents=True, exist_ok=True)
    season_root = args.output_root / "seasons"
    table_root = args.output_root / "tables"
    season_root.mkdir(exist_ok=True)
    table_root.mkdir(exist_ok=True)
    game_context = pl.read_parquet(args.game_context)

    feature_frames: list[pl.DataFrame] = []
    season_reports: list[dict[str, object]] = []
    for index, season in enumerate(args.seasons, start=1):
        feature_path = season_root / f"season={season}" / "player-features.parquet"
        report_path = season_root / f"season={season}" / "report.json"
        if args.reuse_existing and feature_path.exists() and report_path.exists():
            print(f"[{index}/{len(args.seasons)}] {season}: reusing", flush=True)
            feature_frames.append(pl.read_parquet(feature_path))
            season_reports.append(json.loads(report_path.read_text(encoding="utf-8")))
            continue
        print(f"[{index}/{len(args.seasons)}] {season}: loading events", flush=True)
        terminal = _load_terminal(args.terminal_root, season)
        events = prepare_terminal_contacts(
            terminal,
            game_context.filter(pl.col("season") == season),
        )
        print(
            f"  eligible contacts={events.height:,}; players={events['player_id'].n_unique():,}",
            flush=True,
        )
        if args.method == "shrunk":
            stage_probabilities, season_report = (
                crossfit_shrunk_context_probabilities(
                    events,
                    folds=args.folds,
                    random_state=417 + season,
                )
            )
            context_probability = stage_probabilities[args.selected_stage]
            season_report["physical_metrics"] = season_report["stage_metrics"][
                "physical"
            ]
            season_report["context_metrics"] = season_report["stage_metrics"][
                args.selected_stage
            ]
            season_report["selected_stage"] = args.selected_stage
        else:
            _, context_probability, season_report = crossfit_contact_probabilities(
                events,
                folds=args.folds,
                random_state=417 + season,
                include_opponent_ids=not args.exclude_opponent_ids,
            )
        features = aggregate_neutralized_contact_features(events, context_probability)
        feature_path.parent.mkdir(parents=True, exist_ok=True)
        artifact = write_canonical_parquet(
            features,
            feature_path,
            table_name=f"hitter_contact_neutralization_{season}_v1",
        )
        season_report.update(
            {
                "generated_at_utc": datetime.now(UTC).isoformat(),
                "protected_2026_outcomes_used": False,
                "2020_missing_milb_season_expected": True,
                "feature_artifact": artifact.as_record(),
            }
        )
        report_path.write_text(
            json.dumps(season_report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        feature_frames.append(features)
        season_reports.append(season_report)
        physical = season_report["physical_metrics"]
        context = season_report["context_metrics"]
        print(
            "  context minus contact-only: "
            f"log loss {float(context['log_loss']) - float(physical['log_loss']):+.6f}; "
            f"Brier {float(context['brier']) - float(physical['brier']):+.6f}",
            flush=True,
        )

    annual = pl.concat(feature_frames, how="vertical_relaxed").sort(
        "season", "player_id"
    )
    annual_artifact = write_canonical_parquet(
        annual,
        table_root / "player-season-features.parquet",
        table_name="hitter_contact_neutralized_player_season_v1",
    )
    panel = attach_neutralized_lags(pl.read_parquet(args.base_panel), annual)
    panel_artifact = write_canonical_parquet(
        panel,
        table_root / "modeling-panel.parquet",
        table_name="hitter_contact_neutralized_modeling_panel_v1",
    )
    physical = _weighted_metrics(season_reports, "physical")
    context = _weighted_metrics(season_reports, "context")
    report = {
        "schema_version": "1.0",
        "status": "materialization_complete",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "seasons": list(args.seasons),
        "event_crossfit_folds": args.folds,
        "method": args.method,
        "selected_stage": args.selected_stage if args.method == "shrunk" else None,
        "context_scope": (
            "shrunk_park_defense_pitcher_residuals"
            if args.method == "shrunk"
            else (
                "park_weather_and_raw_opponent_ids"
                if not args.exclude_opponent_ids
                else "park_and_weather_only"
            )
        ),
        "events": sum(int(row["events"]) for row in season_reports),
        "players_by_season": sum(int(row["players"]) for row in season_reports),
        "physical_metrics": physical,
        "context_metrics": context,
        "context_minus_physical": {
            metric: context[metric] - physical[metric]
            for metric in ("log_loss", "brier")
        },
        "protected_2026_outcomes_used": False,
        "2020_missing_milb_season_expected": True,
        "annual_feature_artifact": annual_artifact.as_record(),
        "modeling_panel_artifact": panel_artifact.as_record(),
        "season_reports": season_reports,
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report["context_minus_physical"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
