#!/usr/bin/env python3
"""Build current baserunning rates from official and public league-wide sources."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import date
import gzip
from hashlib import sha256
import json
from pathlib import Path

import polars as pl
import requests

from universal_baseball.current_baserunning import (
    advancement_history_frame,
    build_advancement_history,
    build_current_baserunning_rates,
    build_steal_history,
    steal_history_frame,
)
from universal_baseball.player_value_baserunning_runs import build_baserunning_reference
from universal_baseball.player_value_baserunning_sources import (
    SAVANT_BASERUNNING_RUN_VALUE_URL,
    audit_savant_baserunning_rows,
    parse_savant_baserunning_csv,
    savant_baserunning_query_params,
)
from universal_baseball.storage import write_canonical_parquet


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument("--history-seasons", default="2023,2024,2025,2026")
    parser.add_argument("--forecast-seasons", default="2027,2028,2029,2030,2031,2032")
    parser.add_argument("--reference-season", type=int, default=2025)
    parser.add_argument(
        "--affiliated-source", type=Path,
        default=Path(
            "reports/generated/affiliated-skill-source/tables/"
            "affiliated_hitting_components.parquet"
        ),
    )
    parser.add_argument(
        "--current-source-root", type=Path,
        default=Path("reports/generated/opportunity-current-source-2026-09-08/tables/2026"),
    )
    parser.add_argument(
        "--mlb-source-root", type=Path,
        default=Path("reports/generated/current-mlb-skill-source"),
    )
    parser.add_argument(
        "--output-root", type=Path,
        default=Path("reports/generated/current-baserunning-rates"),
    )
    return parser.parse_args()


def _seasons(raw: str) -> tuple[int, ...]:
    result = tuple(sorted({int(value.strip()) for value in raw.split(",") if value.strip()}))
    if not result:
        raise ValueError("season list must not be empty")
    return result


def _fetch_advancement(
    seasons: tuple[int, ...], output_root: Path
) -> tuple[dict[int, list[dict[str, str]]], list[dict[str, object]]]:
    rows_by_season: dict[int, list[dict[str, str]]] = {}
    captures: list[dict[str, object]] = []
    raw_root = output_root / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    with requests.Session() as session:
        session.headers["User-Agent"] = "universal-baseball-model-current-baserunning/0.1"
        for season in seasons:
            response = session.get(
                SAVANT_BASERUNNING_RUN_VALUE_URL,
                params=savant_baserunning_query_params(season),
                timeout=120,
            )
            response.raise_for_status()
            rows = parse_savant_baserunning_csv(response.content.decode("utf-8-sig"))
            audit = audit_savant_baserunning_rows(rows)
            if not audit["advancement_source_usable"]:
                raise RuntimeError(f"Savant advancement source failed {season}: {audit}")
            path = raw_root / f"savant-baserunning-{season}.csv.gz"
            with gzip.open(path, "wb") as handle:
                handle.write(response.content)
            rows_by_season[season] = rows
            captures.append(
                {
                    "season": season,
                    "requested_url": response.url,
                    "response_bytes": len(response.content),
                    "response_sha256": sha256(response.content).hexdigest(),
                    "row_count": len(rows),
                    "audit": audit,
                    "raw_path": path.as_posix(),
                }
            )
    return rows_by_season, captures


def _reference(
    components: pl.DataFrame,
    advancement: pl.DataFrame,
    environment: dict[str, object],
    *,
    season: int,
):
    mlb = components.filter(
        (pl.col("season") == season) & (pl.col("level_group") == "MLB")
    )
    opportunity = mlb.select(
        (
            pl.col("hits") - pl.col("doubles") - pl.col("triples")
            - pl.col("home_runs") + pl.col("base_on_balls")
            + pl.col("hit_by_pitch") - pl.col("intentional_walks")
        ).sum()
    ).item()
    attempts = mlb.select((pl.col("stolen_bases") + pl.col("caught_stealing")).sum()).item()
    return build_baserunning_reference(
        season=season,
        plate_appearances=float(environment["batting_plate_appearances"]),
        runs=float(environment["batting_runs_scored"]),
        outs=float(environment["pitching_outs"]),
        steal_opportunity_proxy=float(opportunity),
        steal_attempts=float(attempts),
        stolen_bases=float(mlb.get_column("stolen_bases").sum()),
        advancement_opportunities=float(
            advancement.filter(pl.col("season") == season)
            .get_column("opportunities_xb").sum()
        ),
    )


def main() -> int:
    args = _args()
    history_seasons = _seasons(args.history_seasons)
    forecast_seasons = _seasons(args.forecast_seasons)
    if args.reference_season not in history_seasons:
        raise ValueError("reference season must be included in history seasons")
    output_root = args.output_root / args.as_of_date.isoformat()
    tables = output_root / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    components = pl.read_parquet(args.affiliated_source).filter(
        pl.col("season").is_in(history_seasons)
    )
    steal_rows, environment_audit = build_steal_history(components)
    rows_by_season, captures = _fetch_advancement(history_seasons, output_root)
    advancement_rows = build_advancement_history(rows_by_season)
    advancement = advancement_history_frame(advancement_rows)
    environment_report = json.loads(
        (args.mlb_source_root / args.as_of_date.isoformat() / "report.json").read_text()
    )["reference_environment"]
    if int(environment_report["season"]) != args.reference_season:
        raise ValueError("MLB reference environment season differs from requested season")
    reference = _reference(
        components, advancement, environment_report, season=args.reference_season
    )
    players = pl.read_parquet(args.current_source_root / "hitter_snapshot.parquet").select(
        "player_id"
    )
    rates = build_current_baserunning_rates(
        players,
        steal_rows,
        advancement_rows,
        forecast_seasons=forecast_seasons,
        reference=reference,
    )
    storage = {
        "steal_history": write_canonical_parquet(
            steal_history_frame(steal_rows), tables / "steal_history.parquet",
            table_name="current_baserunning_steal_history",
        ).as_record(),
        "advancement_history": write_canonical_parquet(
            advancement, tables / "advancement_history.parquet",
            table_name="current_baserunning_advancement_history",
        ).as_record(),
        "rates": write_canonical_parquet(
            rates, tables / "hitter_baserunning_rates.parquet",
            table_name="current_hitter_baserunning_rates",
        ).as_record(),
    }
    report = {
        "report_schema_version": "0.1",
        "gate": "current_hitter_baserunning_rate_baseline",
        "as_of_date": args.as_of_date.isoformat(),
        "history_seasons": list(history_seasons),
        "forecast_seasons": list(forecast_seasons),
        "reference": asdict(reference),
        "steal_environment_audit": asdict(environment_audit),
        "advancement_captures": captures,
        "coverage": rates.group_by("baserunning_evidence_tier").len().sort(
            "baserunning_evidence_tier"
        ).to_dicts(),
        "environment_boundary": (
            "StatsAPI sport-level MiLB environment; exact league IDs are absent from "
            "the affiliated bulk component table"
        ),
        "current_season_used_as_evaluation_target": False,
        "storage": storage,
    }
    (output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"gate": report["gate"], "coverage": report["coverage"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
