#!/usr/bin/env python3
"""Test whether recent official MLB usage improves a late-season workload baseline."""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from hashlib import sha256
import json
from pathlib import Path

import polars as pl
import requests

from universal_baseball.playing_time_roster_source import STATS_API_BASE
from universal_baseball.mlb_usage_window import (
    project_mlb_usage_date_range_payload,
)
from universal_baseball.rest_of_season import project_team_schedule_calendar
from universal_baseball.storage import write_canonical_parquet


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seasons", default="2022,2023,2024,2025")
    parser.add_argument("--confirmation-season", type=int, default=2025)
    parser.add_argument("--cutoff-month", type=int, default=9)
    parser.add_argument("--cutoff-day", type=int, default=8)
    parser.add_argument("--recent-days", type=int, default=30)
    parser.add_argument(
        "--recent-regression-exposures", default="25,50,100,200"
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/historical-ros-usage-recency"),
    )
    return parser.parse_args()


def _capture(
    session: requests.Session,
    url: str,
    params: dict[str, object],
    path: Path,
) -> dict:
    response = session.get(url, params=params, timeout=120)
    response.raise_for_status()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(response.content)
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("official MLB response must be an object")
    return payload


def _stats(
    session: requests.Session,
    *,
    group: str,
    start: date,
    end: date,
    path: Path,
) -> tuple[pl.DataFrame, dict[str, object]]:
    payload = _capture(
        session,
        f"{STATS_API_BASE}/stats",
        {
            "stats": "byDateRange",
            "group": group,
            "sportIds": 1,
            "startDate": start.strftime("%m/%d/%Y"),
            "endDate": end.strftime("%m/%d/%Y"),
            "playerPool": "ALL",
            "gameType": "R",
            "limit": 5000,
        },
        path,
    )
    frame = project_mlb_usage_date_range_payload(payload, group=group)
    return frame, {
        "path": path.as_posix(),
        "sha256": sha256(path.read_bytes()).hexdigest(),
        "group": group,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "source_splits": int(payload["stats"][0]["totalSplits"]),
        "players": frame.height,
    }


def _role(games: pl.Expr, starts: pl.Expr) -> pl.Expr:
    return (
        pl.when(games <= 0)
        .then(pl.lit("none"))
        .when(starts == 0)
        .then(pl.lit("reliever"))
        .when(starts * 2 >= games)
        .then(pl.lit("starter"))
        .otherwise(pl.lit("swingman"))
    )


def _score_season(
    *,
    season: int,
    group: str,
    prior: pl.DataFrame,
    year_to_date: pl.DataFrame,
    recent: pl.DataFrame,
    target: pl.DataFrame,
    elapsed_team_games: float,
    recent_team_games: float,
    remaining_fraction: float,
    recent_exposures: tuple[float, ...],
) -> pl.DataFrame:
    prefix = lambda frame, name: frame.rename(  # noqa: E731
        {column: f"{name}_{column}" for column in frame.columns if column != "player_id"}
    )
    joined = prefix(year_to_date, "ytd").join(
        prefix(prior, "prior"), on="player_id", how="left"
    ).join(
        prefix(recent, "recent"), on="player_id", how="left"
    ).join(
        prefix(target, "target"), on="player_id", how="left"
    ).with_columns(
        pl.exclude("player_id").fill_null(0),
        pl.lit(season).alias("season"),
        pl.lit(group).alias("component"),
    )
    observed = pl.col("ytd_workload")
    base_reliability = observed / (observed + 200.0)
    base_full_pace = (
        base_reliability * observed * 162.0 / elapsed_team_games
        + (1.0 - base_reliability) * pl.col("prior_workload")
    )
    joined = joined.with_columns(
        base_full_pace.alias("base_full_season_pace"),
        (base_full_pace * remaining_fraction).alias("base_prediction"),
        _role(pl.col("ytd_games"), pl.col("ytd_starts")).alias("ytd_role"),
        _role(pl.col("recent_games"), pl.col("recent_starts")).alias("recent_role"),
    )
    for exposure in recent_exposures:
        label = str(int(exposure))
        reliability = pl.col("recent_workload") / (
            pl.col("recent_workload") + exposure
        )
        recent_full_pace = pl.col("recent_workload") * 162.0 / recent_team_games
        joined = joined.with_columns(
            (
                (
                    reliability * recent_full_pace
                    + (1.0 - reliability) * pl.col("base_full_season_pace")
                )
                * remaining_fraction
            ).alias(f"recent_{label}_prediction")
        )
    return joined


def _metrics(frame: pl.DataFrame, prediction: str) -> dict[str, object]:
    error = pl.col(prediction) - pl.col("target_workload")
    return {
        "rows": frame.height,
        "mae": float(frame.select(error.abs().mean()).item()),
        "rmse": float(frame.select((error * error).mean().sqrt()).item()),
        "predicted_total": float(frame.get_column(prediction).sum()),
        "actual_total": float(frame.get_column("target_workload").sum()),
    }


def main() -> int:
    args = _args()
    seasons = tuple(sorted({int(value) for value in args.seasons.split(",")}))
    exposures = tuple(
        sorted({float(value) for value in args.recent_regression_exposures.split(",")})
    )
    if args.confirmation_season not in seasons or args.recent_days <= 0:
        raise ValueError("confirmation season and recent window must be valid")
    captures = args.output_root / "captures"
    source_records: list[dict[str, object]] = []
    scored: list[pl.DataFrame] = []
    with requests.Session() as session:
        session.headers["User-Agent"] = "universal-baseball-model-ros-role-audit/0.1"
        for season in seasons:
            cutoff = date(season, args.cutoff_month, args.cutoff_day)
            schedule_path = captures / f"schedule-{season}.json"
            schedule_payload = _capture(
                session,
                f"{STATS_API_BASE}/schedule",
                {"sportId": 1, "season": season, "gameType": "R"},
                schedule_path,
            )
            calendar, completed, scheduled = project_team_schedule_calendar(
                schedule_payload, season=season, as_of_date=cutoff
            )
            season_start = calendar.get_column("championship_season_start").min()
            season_end = calendar.get_column("championship_season_end").max()
            assert isinstance(season_start, date) and isinstance(season_end, date)
            elapsed_team_games = 2.0 * completed / 30.0
            remaining_fraction = (scheduled - completed) / scheduled
            recent_start = cutoff - timedelta(days=args.recent_days - 1)
            recent_schedule, recent_completed, _ = project_team_schedule_calendar(
                schedule_payload, season=season, as_of_date=recent_start - timedelta(days=1)
            )
            del recent_schedule
            recent_team_games = 2.0 * (completed - recent_completed) / 30.0
            for group in ("hitting", "pitching"):
                windows = {
                    "prior": (date(season - 1, 1, 1), date(season - 1, 12, 31)),
                    "ytd": (season_start, cutoff),
                    "recent": (recent_start, cutoff),
                    "target": (cutoff + timedelta(days=1), season_end),
                }
                frames: dict[str, pl.DataFrame] = {}
                for name, (start, end) in windows.items():
                    frame, record = _stats(
                        session,
                        group=group,
                        start=start,
                        end=end,
                        path=captures / f"{group}-{season}-{name}.json",
                    )
                    frames[name] = frame
                    source_records.append({"season": season, "window": name, **record})
                scored.append(
                    _score_season(
                        season=season,
                        group=group,
                        prior=frames["prior"],
                        year_to_date=frames["ytd"],
                        recent=frames["recent"],
                        target=frames["target"],
                        elapsed_team_games=elapsed_team_games,
                        recent_team_games=recent_team_games,
                        remaining_fraction=remaining_fraction,
                        recent_exposures=exposures,
                    )
                )
            source_records.append(
                {
                    "season": season,
                    "window": "schedule",
                    "path": schedule_path.as_posix(),
                    "sha256": sha256(schedule_path.read_bytes()).hexdigest(),
                }
            )
    panel = pl.concat(scored, how="diagonal_relaxed").sort(
        ["season", "component", "player_id"]
    )
    raw_predictions = [
        f"recent_{int(exposure)}_prediction" for exposure in exposures
    ]
    for prediction in raw_predictions:
        panel = panel.with_columns(
            (
                pl.col(prediction)
                * pl.col("base_prediction").sum().over("season", "component")
                / pl.col(prediction).sum().over("season", "component")
            ).alias(f"{prediction}_baseline_total_scaled")
        )
    predictions = ["base_prediction"] + raw_predictions + [
        f"{prediction}_baseline_total_scaled" for prediction in raw_predictions
    ]
    development = panel.filter(pl.col("season") < args.confirmation_season)
    confirmation = panel.filter(pl.col("season") == args.confirmation_season)
    comparison: list[dict[str, object]] = []
    for component in ("hitting", "pitching"):
        for split_name, split in (
            ("development", development),
            ("confirmation", confirmation),
        ):
            part = split.filter(pl.col("component") == component)
            for prediction in predictions:
                comparison.append(
                    {
                        "component": component,
                        "split": split_name,
                        "candidate": prediction,
                        **_metrics(part, prediction),
                    }
                )
    development_rows = [row for row in comparison if row["split"] == "development"]
    selected = {
        component: min(
            (row for row in development_rows if row["component"] == component),
            key=lambda row: float(row["mae"]),
        )["candidate"]
        for component in ("hitting", "pitching")
    }
    role_changes = (
        panel.filter(
            (pl.col("component") == "pitching")
            & (pl.col("recent_role") != "none")
            & (pl.col("ytd_role") != pl.col("recent_role"))
        )
        .group_by("season", "ytd_role", "recent_role")
        .agg(pl.len().alias("players"), pl.col("target_workload").mean())
        .sort("season", "ytd_role", "recent_role")
        .to_dicts()
    )
    tables = args.output_root / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    storage = write_canonical_parquet(
        panel,
        tables / "historical-ros-usage-panel.parquet",
        table_name="historical_rest_of_season_usage_panel",
    ).as_record()
    report = {
        "report_schema_version": "0.1",
        "gate": "historical_ros_usage_recency_challenger",
        "status": "audit_not_production_model",
        "seasons": list(seasons),
        "confirmation_season": args.confirmation_season,
        "cutoff_month_day": f"{args.cutoff_month:02d}-{args.cutoff_day:02d}",
        "recent_days": args.recent_days,
        "base_method": (
            "season-to-date workload pace blended with prior-year workload using "
            "the existing 200-exposure reliability"
        ),
        "challenger_method": (
            "recent-window pace blended into the base using only recent workload "
            "and a prespecified regression exposure; scaled candidates only "
            "redistribute the baseline league total and use no team depth or cap"
        ),
        "selected_on_development_mae": selected,
        "comparison": comparison,
        "pitcher_role_change_diagnostics": role_changes,
        "source_records": source_records,
        "storage": storage,
    }
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "gate": report["gate"],
        "selected_on_development_mae": selected,
        "comparison": comparison,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
