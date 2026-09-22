#!/usr/bin/env python3
"""Build pitcher contact value after removing park, defense, and batter context."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path

import polars as pl

from materialize_hitter_contact_neutralization import TERMINAL_COLUMNS, _load_terminal
from universal_baseball.hitter_contact_neutralization import (
    crossfit_shrunk_context_probabilities,
    prepare_pitcher_terminal_contacts,
)
from universal_baseball.pitcher_contact_neutralization import (
    aggregate_pitcher_contact_value,
)
from universal_baseball.storage import write_canonical_parquet


DEFAULT_SEASONS = (2016, 2017, 2018, 2019, 2021, 2022, 2023, 2024)
STAGES = ("physical", "park", "park_defense", "park_defense_batter")


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
        "--output-root",
        type=Path,
        default=Path("reports/generated/pitcher-contact-neutralization-v1"),
    )
    parser.add_argument("--seasons", nargs="+", type=int, default=list(DEFAULT_SEASONS))
    parser.add_argument("--folds", type=int, default=2)
    parser.add_argument("--reuse-existing", action="store_true")
    return parser.parse_args()


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
    annual: dict[str, list[pl.DataFrame]] = {stage: [] for stage in STAGES}
    reports: list[dict[str, object]] = []
    for index, season in enumerate(args.seasons, start=1):
        report_path = season_root / f"season={season}" / "report.json"
        feature_paths = {
            stage: season_root / f"season={season}" / f"{stage}-features.parquet"
            for stage in STAGES
        }
        if (
            args.reuse_existing
            and report_path.exists()
            and all(path.exists() for path in feature_paths.values())
        ):
            print(f"[{index}/{len(args.seasons)}] {season}: reusing", flush=True)
            for stage, path in feature_paths.items():
                annual[stage].append(pl.read_parquet(path))
            reports.append(json.loads(report_path.read_text(encoding="utf-8")))
            continue
        print(f"[{index}/{len(args.seasons)}] {season}: loading events", flush=True)
        terminal = _load_terminal(args.terminal_root, season).select(*TERMINAL_COLUMNS)
        events = prepare_pitcher_terminal_contacts(
            terminal, game_context.filter(pl.col("season") == season)
        )
        print(
            f"  eligible contacts={events.height:,}; pitchers={events['player_id'].n_unique():,}",
            flush=True,
        )
        probabilities, report = crossfit_shrunk_context_probabilities(
            events,
            folds=args.folds,
            random_state=917 + season,
            opponent_column="batter",
            opponent_stage_name="batter",
        )
        artifacts = {}
        for stage in STAGES:
            features = aggregate_pitcher_contact_value(events, probabilities[stage])
            feature_paths[stage].parent.mkdir(parents=True, exist_ok=True)
            artifacts[stage] = write_canonical_parquet(
                features,
                feature_paths[stage],
                table_name=f"pitcher_contact_neutralization_{stage}_{season}_v1",
            ).as_record()
            annual[stage].append(features)
        report.update(
            {
                "generated_at_utc": datetime.now(UTC).isoformat(),
                "protected_2026_outcomes_used": False,
                "2020_missing_milb_season_expected": True,
                "feature_artifacts": artifacts,
            }
        )
        report_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        reports.append(report)

    annual_artifacts = {}
    for stage, frames in annual.items():
        combined = pl.concat(frames, how="vertical_relaxed").sort("season", "player_id")
        annual_artifacts[stage] = write_canonical_parquet(
            combined,
            table_root / f"{stage}-player-season.parquet",
            table_name=f"pitcher_contact_neutralization_{stage}_player_season_v1",
        ).as_record()
    report = {
        "schema_version": "0.1",
        "status": "pitcher_contact_neutralization_materialized",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "seasons": list(args.seasons),
        "event_crossfit_folds": args.folds,
        "events": sum(int(row["events"]) for row in reports),
        "pitcher_seasons": sum(int(row["players"]) for row in reports),
        "stages": list(STAGES),
        "protected_2026_outcomes_used": False,
        "2020_missing_milb_season_expected": True,
        "annual_artifacts": annual_artifacts,
        "season_reports": reports,
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"events": report["events"], "stages": list(STAGES)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
