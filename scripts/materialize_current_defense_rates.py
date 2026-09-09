#!/usr/bin/env python3
"""Materialize frozen adjacent-year general defense for current hitters."""

from __future__ import annotations

import argparse
from datetime import date
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import polars as pl
import requests

from universal_baseball.current_defense import build_current_general_defense_rates
from universal_baseball.mlb_season_stats import MLB_STATS_URL, _statsapi_get_with_retry
from universal_baseball.player_value_defense_projection import (
    LEVEL_BY_LEAGUE,
    load_frozen_fielding_profiles,
)
from universal_baseball.storage import write_canonical_parquet


PAGE_LIMIT = 500


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument("--forecast-seasons", default="2027,2028,2029,2030,2031,2032")
    parser.add_argument(
        "--opportunity-root", type=Path,
        default=Path("reports/generated/current-opportunity-paths"),
    )
    parser.add_argument(
        "--general-parameters", type=Path,
        default=Path("docs/defense-v1-confirmation-parameters.json"),
    )
    parser.add_argument(
        "--conversion-parameters", type=Path,
        default=Path(
            "docs/player-value-v1-defense-native-run-conversion-parameters.json"
        ),
    )
    parser.add_argument(
        "--output-root", type=Path,
        default=Path("reports/generated/current-defense-rates"),
    )
    return parser.parse_args()


def _fetch_league(
    session: requests.Session,
    *,
    season: int,
    league_id: int,
    capture_root: Path,
) -> list[dict[str, Any]]:
    captures: list[dict[str, Any]] = []
    seen_signatures: set[tuple[tuple[int, str, int], ...]] = set()
    offset = 0
    while True:
        response = _statsapi_get_with_retry(
            session,
            MLB_STATS_URL,
            params={
                "stats": "season",
                "group": "fielding",
                "season": season,
                "leagueId": league_id,
                "playerPool": "ALL",
                "gameType": "R",
                "limit": PAGE_LIMIT,
                "offset": offset,
            },
            timeout_seconds=120,
        )
        payload = response.json()
        blocks = payload.get("stats") or []
        if len(blocks) != 1 or not isinstance(blocks[0].get("splits"), list):
            raise RuntimeError("current fielding response has invalid stats block")
        splits = blocks[0]["splits"]
        signature = tuple(
            (
                int((row.get("player") or row.get("person") or {})["id"]),
                str((row.get("position") or {}).get("abbreviation") or ""),
                int((row.get("team") or {})["id"]),
            )
            for row in splits
        )
        if signature and signature in seen_signatures:
            raise RuntimeError("current fielding pagination repeated a page")
        seen_signatures.add(signature)
        path = (
            capture_root / str(season) / str(league_id)
            / f"fielding_offset_{offset}.json"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(response.content)
        captures.append(
            {
                "season": season,
                "league_id": league_id,
                "offset": offset,
                "returned_rows": len(splits),
                "requested_url": response.url,
                "response_sha256": sha256(response.content).hexdigest(),
                "path": path.as_posix(),
            }
        )
        if len(splits) < PAGE_LIMIT:
            break
        offset += len(splits)
        if offset > 10_000:
            raise RuntimeError("current fielding pagination exceeded safety limit")
    return captures


def main() -> int:
    args = _args()
    seasons = tuple(
        sorted({int(value.strip()) for value in args.forecast_seasons.split(",")})
    )
    output_root = args.output_root / args.as_of_date.isoformat()
    capture_root = output_root / "captures"
    tables = output_root / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    captures: list[dict[str, Any]] = []
    with requests.Session() as session:
        session.headers["User-Agent"] = "universal-baseball-model-current-defense/0.1"
        for league_id in sorted(LEVEL_BY_LEAGUE):
            captures.extend(
                _fetch_league(
                    session,
                    season=args.as_of_date.year,
                    league_id=league_id,
                    capture_root=capture_root,
                )
            )
    profiles, profile_audit = load_frozen_fielding_profiles(
        capture_root, expected_seasons={args.as_of_date.year}
    )
    opportunity = pl.read_parquet(
        args.opportunity_root / args.as_of_date.isoformat()
        / "tables/hitter_opportunity_paths.parquet"
    )
    general = json.loads(args.general_parameters.read_text(encoding="utf-8"))[
        "parameters"
    ]["general"]
    conversion = json.loads(
        args.conversion_parameters.read_text(encoding="utf-8")
    )["general_range"]
    rates = build_current_general_defense_rates(
        opportunity.select("player_id").unique().sort("player_id"),
        profiles,
        opportunity,
        current_season=args.as_of_date.year,
        forecast_seasons=seasons,
        general_parameters=general,
        conversion_parameters=conversion,
    )
    storage = {
        "profiles": write_canonical_parquet(
            profiles,
            tables / "current-fielding-profiles.parquet",
            table_name="current_fielding_profiles",
        ).as_record(),
        "rates": write_canonical_parquet(
            rates,
            tables / "hitter-defense-rates.parquet",
            table_name="hitter_defense_rates",
        ).as_record(),
    }
    adjacent = rates.filter(pl.col("season") == args.as_of_date.year + 1)
    adjacent_expected_runs = adjacent.join(
        opportunity.select("player_id", "season", "mlb_active_probability"),
        on=["player_id", "season"],
        how="inner",
        validate="1:1",
    ).select(
        (
            pl.col("conditional_defense_runs")
            * pl.col("mlb_active_probability")
        ).sum()
    ).item()
    report = {
        "report_schema_version": "0.1",
        "gate": "current_frozen_general_defense_adjacent_year",
        "as_of_date": args.as_of_date.isoformat(),
        "forecast_seasons": list(seasons),
        "source": "official_mlb_statsapi_fielding",
        "capture_pages": len(captures),
        "capture_manifest": captures,
        "profile_audit": profile_audit,
        "coverage": adjacent.group_by("defense_evidence_tier").len().to_dicts(),
        "adjacent_conditional_defense_runs": adjacent.get_column(
            "conditional_defense_runs"
        ).sum(),
        "adjacent_expected_defense_runs_after_centering": adjacent_expected_runs,
        "method": (
            "frozen U1 general-range skill times prior MLB position outs and the "
            "frozen position-specific native run conversion"
        ),
        "current_team_depth_used": False,
        "boundaries": [
            "T1 tracked range is not used because no current tracked input was built",
            "catcher throwing blocking and framing remain neutral",
            "years beyond the validated adjacent horizon remain neutral",
        ],
        "storage": storage,
    }
    (output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "gate": report["gate"],
                "profile_audit": profile_audit,
                "coverage": report["coverage"],
                "adjacent_conditional_defense_runs": report[
                    "adjacent_conditional_defense_runs"
                ],
                "adjacent_expected_defense_runs_after_centering": report[
                    "adjacent_expected_defense_runs_after_centering"
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
