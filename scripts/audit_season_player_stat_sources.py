#!/usr/bin/env python
"""Audit reusable season-player batting/pitching releases before adoption.

This gate asks whether public season aggregates can supply the non-contact
outcome backbone (PA/BF, K, BB, HBP, etc.) while reusable PBP supplies contact
shape and sampled official PBP supplies league run-value calibration.

No aggregate field is promoted by name alone. The report inventories schemas,
key uniqueness, levels/leagues, identity fields, and arithmetic relationships
for old AAA plus current AAA/Rookie samples.
"""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.certification import download_file, read_quarantined_csv


BASE_URL = "https://github.com/armstjc/milb-data-repository/releases/download"
SPECS = (
    ("batting", "season_player_batting", "2005_aaa_season_batting_stats.csv"),
    ("batting", "season_player_batting", "2026_aaa_season_batting_stats.csv"),
    ("batting", "season_player_batting", "2026_rk_season_batting_stats.csv"),
    ("pitching", "season_player_pitching", "2005_aaa_season_pitching_stats.csv"),
    ("pitching", "season_player_pitching", "2026_aaa_season_pitching_stats.csv"),
    ("pitching", "season_player_pitching", "2026_rk_season_pitching_stats.csv"),
)

IDENTITY_CANDIDATES = (
    "player_id",
    "person_id",
    "id",
    "mlbam_id",
    "player_name",
    "full_name",
    "name",
)
ENVIRONMENT_CANDIDATES = (
    "season",
    "year",
    "level",
    "level_name",
    "league_id",
    "league_name",
    "team_id",
    "team_name",
    "parent_org_id",
    "parent_org_name",
)
OUTCOME_CANDIDATES = (
    "games_played",
    "games",
    "plate_appearances",
    "plateappearances",
    "at_bats",
    "atbats",
    "hits",
    "doubles",
    "triples",
    "home_runs",
    "homeruns",
    "base_on_balls",
    "baseonballs",
    "intentional_walks",
    "intentionalwalks",
    "hit_by_pitch",
    "hitbypitch",
    "strike_outs",
    "strikeouts",
    "sac_bunts",
    "sacbunts",
    "sac_flies",
    "sacflies",
    "catchers_interference",
    "catchersinterference",
    "batters_faced",
    "battersfaced",
    "innings_pitched",
    "inningspitched",
    "earned_runs",
    "earnedruns",
    "runs",
)


def _normalized(column: str) -> str:
    return "".join(character.lower() for character in column if character.isalnum() or character == "_")


def _candidate_matches(columns: list[str], candidates: tuple[str, ...]) -> dict[str, str]:
    normalized = {_normalized(column): column for column in columns}
    result: dict[str, str] = {}
    for candidate in candidates:
        key = _normalized(candidate)
        if key in normalized:
            result[candidate] = normalized[key]
    return result


def _nonblank_count(frame: pl.DataFrame, column: str) -> int:
    return int(
        frame.select(
            (
                pl.col(column).is_not_null()
                & (pl.col(column).cast(pl.String).str.strip_chars() != "")
            ).sum()
        ).item()
    )


def _numeric_summary(frame: pl.DataFrame, column: str) -> dict[str, Any]:
    values = frame.select(
        pl.col(column).cast(pl.Float64, strict=False).alias("value")
    ).get_column("value")
    valid = values.drop_nulls()
    return {
        "nonblank_count": _nonblank_count(frame, column),
        "numeric_count": len(valid),
        "min": float(valid.min()) if len(valid) else None,
        "max": float(valid.max()) if len(valid) else None,
        "sum": float(valid.sum()) if len(valid) else None,
    }


def _distinct_examples(frame: pl.DataFrame, column: str, limit: int = 12) -> list[str]:
    values = (
        frame.select(pl.col(column).cast(pl.String, strict=False).alias("value"))
        .filter(pl.col("value").is_not_null() & (pl.col("value").str.strip_chars() != ""))
        .get_column("value")
        .unique()
        .sort()
        .head(limit)
        .to_list()
    )
    return [str(value) for value in values]


def _identity_profile(frame: pl.DataFrame, matches: dict[str, str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for canonical, column in matches.items():
        nonblank = _nonblank_count(frame, column)
        unique = int(
            frame.select(pl.col(column).cast(pl.String, strict=False).alias("value"))
            .filter(pl.col("value").is_not_null() & (pl.col("value").str.strip_chars() != ""))
            .get_column("value")
            .n_unique()
        )
        result[canonical] = {
            "column": column,
            "nonblank_count": nonblank,
            "unique_count": unique,
            "examples": _distinct_examples(frame, column, limit=8),
        }
    return result


def _duplicate_profile(frame: pl.DataFrame, identity_matches: dict[str, str]) -> dict[str, Any]:
    id_column = None
    for candidate in ("player_id", "person_id", "mlbam_id", "id"):
        if candidate in identity_matches:
            id_column = identity_matches[candidate]
            break
    if id_column is None:
        return {"available": False}

    candidate_keys = [id_column]
    for column in frame.columns:
        normalized = _normalized(column)
        if normalized in {
            "league_id",
            "leagueid",
            "team_id",
            "teamid",
            "level",
            "level_name",
            "levelname",
            "year",
            "season",
        }:
            candidate_keys.append(column)
    candidate_keys = list(dict.fromkeys(candidate_keys))

    profiles: list[dict[str, Any]] = []
    for key_count in range(1, min(len(candidate_keys), 5) + 1):
        key = candidate_keys[:key_count]
        duplicate_groups = (
            frame.group_by(key)
            .len()
            .filter(pl.col("len") > 1)
        )
        profiles.append(
            {
                "key": key,
                "duplicate_group_count": duplicate_groups.height,
                "duplicate_extra_rows": int(
                    duplicate_groups.select((pl.col("len") - 1).sum()).item() or 0
                ),
            }
        )
    return {
        "available": True,
        "candidate_key_order": candidate_keys,
        "profiles": profiles,
    }


def _arithmetic_checks(frame: pl.DataFrame, columns: list[str]) -> dict[str, Any]:
    by_norm = {_normalized(column): column for column in columns}

    def find(*names: str) -> str | None:
        for name in names:
            key = _normalized(name)
            if key in by_norm:
                return by_norm[key]
        return None

    pa = find("plate_appearances", "plateAppearances")
    ab = find("at_bats", "atBats")
    bb = find("base_on_balls", "baseOnBalls")
    hbp = find("hit_by_pitch", "hitByPitch")
    sh = find("sac_bunts", "sacBunts")
    sf = find("sac_flies", "sacFlies")
    ci = find("catchers_interference", "catchersInterference")
    checks: dict[str, Any] = {}

    if pa and ab and bb and hbp:
        components = [ab, bb, hbp]
        if sh:
            components.append(sh)
        if sf:
            components.append(sf)
        if ci:
            components.append(ci)
        working = frame.select(
            [pl.col(column).cast(pl.Int64, strict=False).alias(column) for column in [pa, *components]]
        ).drop_nulls([pa, *components])
        if working.height:
            expression = sum((pl.col(column) for column in components), start=pl.lit(0))
            mismatches = working.filter(pl.col(pa) != expression)
            checks["pa_accounting"] = {
                "available": True,
                "formula": f"{pa} == " + " + ".join(components),
                "compared_rows": working.height,
                "mismatch_rows": mismatches.height,
            }
        else:
            checks["pa_accounting"] = {"available": False, "reason": "components have no complete rows"}
    else:
        checks["pa_accounting"] = {
            "available": False,
            "missing": [
                label
                for label, value in (("PA", pa), ("AB", ab), ("BB", bb), ("HBP", hbp))
                if value is None
            ],
        }
    return checks


def _profile(kind: str, asset: str, metadata: dict[str, Any], frame: pl.DataFrame) -> dict[str, Any]:
    columns = frame.columns
    identity = _candidate_matches(columns, IDENTITY_CANDIDATES)
    environment = _candidate_matches(columns, ENVIRONMENT_CANDIDATES)
    outcomes = _candidate_matches(columns, OUTCOME_CANDIDATES)
    outcome_summary = {
        canonical: {
            "column": column,
            **_numeric_summary(frame, column),
        }
        for canonical, column in outcomes.items()
    }
    return {
        "kind": kind,
        "asset": asset,
        "source_sha256": metadata["sha256"],
        "file_size_bytes": metadata["file_size_bytes"],
        "row_count": frame.height,
        "column_count": len(columns),
        "columns": columns,
        "identity_matches": identity,
        "identity_profile": _identity_profile(frame, identity),
        "environment_matches": environment,
        "environment_examples": {
            canonical: {
                "column": column,
                "nonblank_count": _nonblank_count(frame, column),
                "unique_count": frame.get_column(column).drop_nulls().n_unique(),
                "examples": _distinct_examples(frame, column),
            }
            for canonical, column in environment.items()
        },
        "outcome_matches": outcomes,
        "outcome_summary": outcome_summary,
        "duplicate_profile": _duplicate_profile(frame, identity),
        "arithmetic_checks": _arithmetic_checks(frame, columns),
        "first_rows": frame.head(3).to_dicts(),
    }


def main() -> int:
    work_dir = Path("data/quarantine/season-player-stat-source-audit")
    report_dir = Path("reports/generated/season-player-stat-source-audit")
    work_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    reports: list[dict[str, Any]] = []
    for kind, tag, asset in SPECS:
        path = work_dir / asset
        metadata = download_file(
            f"{BASE_URL}/{tag}/{asset}", path, timeout_seconds=180
        )
        frame = read_quarantined_csv(path)
        reports.append(_profile(kind, asset, metadata, frame))

    payload = {
        "report_schema_version": 1,
        "sources": reports,
        "interpretation": (
            "Schema presence is not certification. A field is only a production candidate after "
            "reconciliation to independent official totals and cross-level/era coverage checks."
        ),
    }
    (report_dir / "season_player_stat_source_audit.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )

    lines = [
        "# Season player-stat source audit",
        "",
        "Schema/coverage inspection only — no aggregate field is promoted yet.",
        "",
    ]
    for report in reports:
        lines.extend(
            [
                f"## `{report['asset']}`",
                "",
                f"- Rows: {report['row_count']:,}; columns: {report['column_count']}",
                f"- Identity candidates: `{report['identity_matches']}`",
                f"- Environment candidates: `{report['environment_matches']}`",
                f"- Outcome candidates: `{report['outcome_matches']}`",
                f"- Candidate duplicate profiles: `{report['duplicate_profile']}`",
                f"- Arithmetic checks: `{report['arithmetic_checks']}`",
                "",
                f"Columns: `{report['columns']}`",
                "",
            ]
        )
    summary = "\n".join(lines)
    (report_dir / "season_player_stat_source_audit.md").write_text(summary, encoding="utf-8")
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
