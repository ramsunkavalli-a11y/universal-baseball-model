#!/usr/bin/env python
"""Audit bounded historical MiLB source pairs without fitting a model."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.armstjc_assets import ArmstjcAsset, fetch_pbp_asset_inventory
from universal_baseball.armstjc_schema import normalize_known_schema_aliases
from universal_baseball.certification import (
    download_file,
    read_quarantined_csv,
    sha256_file,
)
from universal_baseball.current_talent_contact_value_source import (
    attach_narrative_terminal_groups,
    project_terminal_pa_descriptions,
)
from universal_baseball.current_talent_milb_source import derive_player_game_league_map
from universal_baseball.hitter_v2_outcomes import (
    project_official_player_game_outcomes,
    resolve_official_player_game_outcomes,
)
from universal_baseball.player_game_stats import (
    ArmstjcPlayerGameAsset,
    fetch_player_game_asset_inventory,
)


SELECTION_MATRIX: dict[int, tuple[str, ...]] = {
    2017: ("aaa", "rk"),
    2018: ("aaa", "aa"),
    2019: ("aaa", "aa", "a+", "a", "rk"),
}
PILOT_EXCLUDED_PERIODS: dict[tuple[int, str], tuple[int, ...]] = {
    (2019, "aaa"): (3, 10),
    (2019, "rk"): (9,),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("data/quarantine/hitter-v2-historical-expansion-sample"),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-historical-expansion-audit"),
    )
    return parser.parse_args()


def _select_pairs(
    pbp_assets: list[ArmstjcAsset],
    player_game_assets: list[ArmstjcPlayerGameAsset],
) -> list[tuple[ArmstjcAsset, ArmstjcPlayerGameAsset]]:
    pbp = {(row.year, row.filename_level, row.filename_period): row for row in pbp_assets}
    player_game = {
        (row.year, row.filename_level, row.filename_period): row
        for row in player_game_assets
    }
    selected: list[tuple[ArmstjcAsset, ArmstjcPlayerGameAsset]] = []
    for year, levels in SELECTION_MATRIX.items():
        for level in levels:
            keys = sorted(
                key
                for key in set(pbp) & set(player_game)
                if key[0] == year and key[1] == level
                and key[2] not in PILOT_EXCLUDED_PERIODS.get((year, level), ())
            )
            if not keys:
                raise RuntimeError(f"no paired historical asset for {year} {level}")
            key = min(
                keys,
                key=lambda item: (
                    pbp[item].size_bytes + player_game[item].size_bytes,
                    item[2],
                ),
            )
            selected.append((pbp[key], player_game[key]))
    return selected


def _download(asset: Any, root: Path, family: str) -> tuple[Path, dict[str, Any]]:
    path = root / family / asset.name
    retrieval: dict[str, Any] | None = None
    if not path.exists() or path.stat().st_size <= 0:
        retrieval = download_file(
            asset.browser_download_url,
            path,
            timeout_seconds=600,
        )
    if path.stat().st_size != asset.size_bytes:
        raise RuntimeError(
            f"downloaded size differs from inventory for {asset.name}: "
            f"{path.stat().st_size} != {asset.size_bytes}"
        )
    return path, {
        "asset_id": asset.asset_id,
        "name": asset.name,
        "filename_period": asset.filename_period,
        "inventory_size_bytes": asset.size_bytes,
        "created_at_utc": asset.created_at_utc.isoformat(),
        "updated_at_utc": asset.updated_at_utc.isoformat(),
        "downloaded_size_bytes": path.stat().st_size,
        "downloaded_sha256": sha256_file(path),
        "retrieval": retrieval or "reused_checksum_verified_local_quarantine",
    }


def _counts(frame: pl.DataFrame, column: str) -> dict[str, int]:
    return {
        str(row[column]): int(row["len"])
        for row in frame.group_by(column).len().sort(column).to_dicts()
    }


def _audit_pair(
    pbp_asset: ArmstjcAsset,
    player_game_asset: ArmstjcPlayerGameAsset,
    work_root: Path,
) -> dict[str, Any]:
    pbp_path, pbp_source = _download(pbp_asset, work_root, "pbp")
    pg_path, pg_source = _download(player_game_asset, work_root, "player-game")
    raw_pbp = read_quarantined_csv(pbp_path)
    raw_pg = read_quarantined_csv(pg_path)
    pbp, pbp_aliases = normalize_known_schema_aliases(raw_pbp)
    player_game, pg_aliases = normalize_known_schema_aliases(raw_pg)

    result: dict[str, Any] = {
        "season": pbp_asset.year,
        "filename_level": pbp_asset.filename_level,
        "filename_period": pbp_asset.filename_period,
        "pbp_source": pbp_source,
        "player_game_source": pg_source,
        "pbp_schema": {
            "row_count": pbp.height,
            "column_count": len(pbp.columns),
            "columns": pbp.columns,
            "alias_report": pbp_aliases,
        },
        "player_game_schema": {
            "row_count": player_game.height,
            "column_count": len(player_game.columns),
            "columns": player_game.columns,
            "alias_report": pg_aliases,
        },
        "stages": {},
    }

    try:
        key = ["game_pk", "at_bat_number", "pitch_number"]
        missing_key = sorted(set(key) - set(pbp.columns))
        if missing_key:
            raise ValueError(f"missing PBP key fields: {missing_key}")
        valid_key = pbp.select(key).drop_nulls(key)
        duplicate_rows = valid_key.height - valid_key.unique().height
        terminal = attach_narrative_terminal_groups(
            project_terminal_pa_descriptions(pbp, game_type="R")
        )
        result["stages"]["terminal_pa"] = {
            "status": "passed",
            "valid_raw_key_row_count": valid_key.height,
            "duplicate_raw_key_row_count": duplicate_rows,
            "terminal_pa_count": terminal.height,
            "terminal_raw_repeat_row_count": int(
                terminal.select((pl.col("raw_terminal_row_count") - 1).sum()).item() or 0
            ),
            "description_missing_count": terminal.filter(
                pl.col("pa_description").is_null()
            ).height,
            "outcome_status_counts": _counts(terminal, "terminal_outcome_status"),
            "outcome_group_counts": _counts(
                terminal.with_columns(
                    pl.col("terminal_outcome_group").fill_null("<null>")
                ),
                "terminal_outcome_group",
            ),
        }
    except Exception as exc:
        result["stages"]["terminal_pa"] = {
            "status": "failed_closed",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

    try:
        league_map, league_metrics = derive_player_game_league_map(player_game)
        regular_games = (
            pbp.filter(pl.col("game_type").cast(pl.String) == "R")
            .select(pl.col("game_pk").cast(pl.Int64, strict=False))
            .drop_nulls()
            .unique()
        )
        missing = regular_games.join(league_map, on="game_pk", how="anti")
        result["stages"]["same_game_league_authority"] = {
            "status": "passed" if missing.is_empty() else "bounded_gap",
            **league_metrics,
            "regular_pbp_game_count": regular_games.height,
            "regular_pbp_game_without_authority_count": missing.height,
        }
    except Exception as exc:
        result["stages"]["same_game_league_authority"] = {
            "status": "failed_closed",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

    try:
        observations = project_official_player_game_outcomes(
            player_game,
            source_asset=player_game_asset.name,
            season=player_game_asset.year,
            game_type="R",
        )
        resolved, resolution = resolve_official_player_game_outcomes(observations)
        positive_pa = resolved.filter(
            pl.col("batting_PA").is_not_null() & (pl.col("batting_PA") > 0)
        )
        result["stages"]["official_outcomes"] = {
            "status": "passed",
            **resolution,
            "positive_pa_player_game_count": positive_pa.height,
            "official_pa": int(positive_pa.get_column("batting_PA").sum() or 0),
            "resolution_counts": _counts(resolved, "outcome_resolution"),
        }
    except Exception as exc:
        result["stages"]["official_outcomes"] = {
            "status": "failed_closed",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

    statuses = [stage["status"] for stage in result["stages"].values()]
    result["pair_status"] = (
        "compatible_sample"
        if statuses and all(value == "passed" for value in statuses)
        else "compatible_with_bounded_gap"
        if statuses and all(value in {"passed", "bounded_gap"} for value in statuses)
        else "failed_closed"
    )
    return result


def main() -> int:
    args = parse_args()
    args.work_root.mkdir(parents=True, exist_ok=True)
    args.report_root.mkdir(parents=True, exist_ok=True)

    pbp_assets = fetch_pbp_asset_inventory()
    player_game_assets = fetch_player_game_asset_inventory()
    pairs = _select_pairs(pbp_assets, player_game_assets)
    results = [_audit_pair(pbp, player_game, args.work_root) for pbp, player_game in pairs]
    status_counts = dict(sorted(Counter(row["pair_status"] for row in results).items()))
    payload = {
        "report_schema_version": "0.1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "purpose": "bounded_historical_source_compatibility_audit_no_model_fit_or_score",
        "analyzed_seasons": [2017, 2018, 2019],
        "protected_season_outcome_payload_accessed": False,
        "inventory_endpoint_note": (
            "The public release API returned filename-level metadata outside the analyzed "
            "window. Selection was filtered to 2017-2019 before any asset download."
        ),
        "selection_policy": {
            "matrix": {str(year): list(levels) for year, levels in SELECTION_MATRIX.items()},
            "rule": "smallest combined PBP/player-game asset among exact common periods after pilot exclusion of non-regular-only player-game files",
            "pilot_excluded_periods": [
                {
                    "season": year,
                    "filename_level": level,
                    "filename_period": period,
                    "reason": "player-game game_type contained no regular-season R rows (pilot observed exhibition E or postseason W only)",
                }
                for (year, level), periods in sorted(PILOT_EXCLUDED_PERIODS.items())
                for period in periods
            ],
            "reason": "bounded compatibility sample spanning nearest history, early history, full-season and rookie schemas",
        },
        "pair_status_counts": status_counts,
        "pairs": results,
    }
    report_path = args.report_root / "report.json"
    report_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# Hitter v2 historical expansion sample audit",
        "",
        "No model was fit or scored. No protected-season outcome payload was opened.",
        "",
        f"- Sample pairs: {len(results)}",
        f"- Statuses: {status_counts}",
        "",
    ]
    for row in results:
        lines.append(
            f"- {row['season']} {row['filename_level']} period {row['filename_period']}: "
            f"{row['pair_status']}"
        )
    (args.report_root / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
