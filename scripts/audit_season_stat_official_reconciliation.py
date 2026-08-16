#!/usr/bin/env python
"""Certify reusable season-player aggregates against completed official seasons.

The goal is to determine whether public season-player files can supply the
historical PA/BF and non-contact outcome backbone without replaying every game
through the official API. The reusable source remains immutable; current
official data is only a certification oracle.
"""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlencode

import polars as pl

from universal_baseball.certification import download_file, read_quarantined_csv
from universal_baseball.official_capture import capture_official_json, new_official_session
from universal_baseball.season_stats import (
    select_reconciliation_players,
    standardize_armstjc_season_stats,
)


BASE_URL = "https://github.com/armstjc/milb-data-repository/releases/download"
CERTIFICATION_SEASON = 2024
SAMPLE_PER_ACTUAL_LEAGUE = 1
SPECS = (
    {
        "season": CERTIFICATION_SEASON,
        "kind": "batting",
        "tag": "season_player_batting",
        "asset": f"{CERTIFICATION_SEASON}_aaa_season_batting_stats.csv",
        "sport_label": "Triple-A",
    },
    {
        "season": CERTIFICATION_SEASON,
        "kind": "batting",
        "tag": "season_player_batting",
        "asset": f"{CERTIFICATION_SEASON}_rk_season_batting_stats.csv",
        "sport_label": "Rookie",
    },
    {
        "season": CERTIFICATION_SEASON,
        "kind": "pitching",
        "tag": "season_player_pitching",
        "asset": f"{CERTIFICATION_SEASON}_aaa_season_pitching_stats.csv",
        "sport_label": "Triple-A",
    },
    {
        "season": CERTIFICATION_SEASON,
        "kind": "pitching",
        "tag": "season_player_pitching",
        "asset": f"{CERTIFICATION_SEASON}_rk_season_pitching_stats.csv",
        "sport_label": "Rookie",
    },
)

BATTING_COMPARE = {
    "gamesPlayed": "batting_games_played",
    "plateAppearances": "batting_plate_appearances",
    "atBats": "batting_at_bats",
    "hits": "batting_hits",
    "doubles": "batting_doubles",
    "triples": "batting_triples",
    "homeRuns": "batting_home_runs",
    "baseOnBalls": "batting_base_on_balls",
    "intentionalWalks": "batting_intentional_walks",
    "hitByPitch": "batting_hit_by_pitch",
    "strikeOuts": "batting_strike_outs",
    "sacBunts": "batting_sac_bunts",
    "sacFlies": "batting_sac_flies",
    "catchersInterference": "batting_catchers_interference_reached",
}
PITCHING_COMPARE = {
    "gamesPlayed": "pitching_games_played",
    "gamesStarted": "pitching_games_started",
    "battersFaced": "pitching_batters_faced",
    "atBats": "pitching_at_bats",
    "hits": "pitching_hits",
    "doubles": "pitching_doubles",
    "triples": "pitching_triples",
    "homeRuns": "pitching_home_runs",
    "baseOnBalls": "pitching_base_on_balls",
    "intentionalWalks": "pitching_intentional_walks",
    "hitBatsmen": "pitching_hit_batsmen",
    "strikeOuts": "pitching_strike_outs",
    "sacBunts": "pitching_sac_bunts",
    "sacFlies": "pitching_sac_flies",
}


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _int(value: Any) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _source_numeric(column: str) -> pl.Expr:
    return pl.col(column).cast(pl.Int64, strict=False).fill_null(0)


def _grain_profile(frame: pl.DataFrame) -> dict[str, Any]:
    key = ["season", "league_id", "team_id", "player_id"]
    missing = sorted(set(key) - set(frame.columns))
    if missing:
        raise ValueError(f"standardized season-stat source missing grain columns: {missing}")
    duplicates = frame.group_by(key).len().filter(pl.col("len") > 1)
    return {
        "key": key,
        "row_count": frame.height,
        "duplicate_group_count": duplicates.height,
        "duplicate_extra_row_count": int(
            duplicates.select((pl.col("len") - 1).sum()).item() or 0
        ),
        "distinct_player_count": frame.get_column("player_id").n_unique(),
        "distinct_team_count": frame.get_column("team_id").n_unique(),
        "distinct_league_count": frame.get_column("league_id").n_unique(),
    }


def _accounting_profile(frame: pl.DataFrame, kind: str) -> dict[str, Any]:
    if kind == "batting":
        total = "batting_plate_appearances"
        components = [
            "batting_at_bats",
            "batting_base_on_balls",
            "batting_hit_by_pitch",
            "batting_sac_bunts",
            "batting_sac_flies",
            "batting_catchers_interference_reached",
        ]
        label = "PA = AB + BB + HBP + SH + SF + CI"
    else:
        total = "pitching_batters_faced"
        components = [
            "pitching_at_bats",
            "pitching_base_on_balls",
            "pitching_hit_batsmen",
            "pitching_sac_bunts",
            "pitching_sac_flies",
            "pitching_catchers_interference",
        ]
        label = "BF = AB + BB + HBP + SH + SF + CI"

    missing = sorted({total, *components} - set(frame.columns))
    if missing:
        return {
            "available": False,
            "identity": label,
            "missing_columns": missing,
            "reason": "source does not expose every component required for exact accounting",
        }

    working = frame.with_columns(
        _source_numeric(total).alias("__total"),
        sum(
            (_source_numeric(column) for column in components),
            start=pl.lit(0, dtype=pl.Int64),
        ).alias("__components"),
    )
    mismatches = working.filter(pl.col("__total") != pl.col("__components"))
    difference_counts = Counter(
        int(value)
        for value in mismatches.select(
            (pl.col("__total") - pl.col("__components")).alias("difference")
        )
        .get_column("difference")
        .to_list()
    )
    return {
        "available": True,
        "identity": label,
        "compared_row_count": working.height,
        "exact_match_row_count": working.height - mismatches.height,
        "mismatch_row_count": mismatches.height,
        "mismatch_rate": mismatches.height / working.height if working.height else None,
        "difference_counts": dict(sorted(difference_counts.items())),
        "mismatch_examples": mismatches.select(
            [
                column
                for column in [
                    "player_id",
                    "team_id",
                    "league_id",
                    total,
                    *components,
                ]
                if column in mismatches.columns
            ]
        )
        .head(15)
        .to_dicts(),
    }


def _sports_map(session: Any) -> dict[str, int]:
    capture = capture_official_json("sports", session=session)
    if not isinstance(capture.data, Mapping):
        raise RuntimeError("official sports endpoint is not an object")
    result: dict[str, int] = {}
    for raw in capture.data.get("sports") or []:
        sport = _mapping(raw)
        name = _text(sport.get("name"))
        sport_id = _int(sport.get("id"))
        if name is not None and sport_id is not None:
            result[name] = sport_id
    return result


def _stats_endpoint(person_id: int, kind: str, sport_id: int, season: int) -> str:
    params = {
        "stats": "season",
        "group": "hitting" if kind == "batting" else "pitching",
        "season": season,
        "sportId": sport_id,
    }
    return f"people/{person_id}/stats?{urlencode(params)}"


def _official_splits(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for stats_group in payload.get("stats") or []:
        for raw_split in _mapping(stats_group).get("splits") or []:
            split = _mapping(raw_split)
            team = _mapping(split.get("team"))
            league = _mapping(split.get("league"))
            sport = _mapping(split.get("sport"))
            result.append(
                {
                    "team_id": _int(team.get("id")),
                    "team_name": _text(team.get("name")),
                    "league_id": _int(league.get("id")),
                    "league_name": _text(league.get("name")),
                    "sport_id": _int(sport.get("id")),
                    "sport_name": _text(sport.get("name")),
                    "stat": dict(_mapping(split.get("stat"))),
                }
            )
    return result


def _aggregate_source_player_league(
    frame: pl.DataFrame,
    *,
    person_id: int,
    league_id: int,
    fields: list[str],
) -> tuple[dict[str, int], int]:
    subset = frame.filter(
        (pl.col("player_id").cast(pl.Int64, strict=False) == person_id)
        & (pl.col("league_id").cast(pl.Int64, strict=False) == league_id)
    )
    available = [field for field in fields if field in subset.columns]
    if subset.is_empty() or not available:
        return {}, subset.height
    values = subset.select(
        [_source_numeric(field).sum().alias(field) for field in available]
    ).row(0, named=True)
    return {field: int(value or 0) for field, value in values.items()}, subset.height


def _compare_player(
    *,
    frame: pl.DataFrame,
    kind: str,
    sample: Mapping[str, int],
    sport_id: int,
    season: int,
    session: Any,
) -> dict[str, Any]:
    person_id = int(sample["player_id"])
    league_id = int(sample["league_id"])
    endpoint = _stats_endpoint(person_id, kind, sport_id, season)
    capture = capture_official_json(endpoint, session=session)
    if not isinstance(capture.data, Mapping):
        raise RuntimeError(f"official stats payload for {person_id} is not an object")

    official = _official_splits(capture.data)
    compare_fields = BATTING_COMPARE if kind == "batting" else PITCHING_COMPARE
    source, source_row_count = _aggregate_source_player_league(
        frame,
        person_id=person_id,
        league_id=league_id,
        fields=list(compare_fields.values()),
    )

    differences: dict[str, Any] = {}
    compared_fields: list[str] = []
    if len(official) == 1:
        official_stat = official[0]["stat"]
        for official_field, source_field in compare_fields.items():
            if source_field not in source or official_field not in official_stat:
                continue
            official_value = _int(official_stat.get(official_field))
            if official_value is None:
                continue
            source_value = source[source_field]
            compared_fields.append(source_field)
            if source_value != official_value:
                differences[source_field] = {
                    "source": source_value,
                    "official": official_value,
                    "official_field": official_field,
                }

    return {
        "person_id": person_id,
        "league_id": league_id,
        "sample_volume": int(sample["sample_volume"]),
        "kind": kind,
        "season": season,
        "sport_id_requested": sport_id,
        "endpoint": endpoint,
        "official_snapshot_sha256": capture.content_sha256,
        "source_team_row_count": source_row_count,
        "official_split_count": len(official),
        "compared_field_count": len(compared_fields),
        "compared_fields": compared_fields,
        "difference_count": len(differences),
        "differences": differences,
        "exact": len(official) == 1 and bool(compared_fields) and not differences,
        "official_split_metadata": [
            {key: value for key, value in row.items() if key != "stat"}
            for row in official
        ],
    }


def main() -> int:
    work_dir = Path("data/quarantine/season-stat-official-reconciliation")
    report_dir = Path("reports/generated/season-stat-official-reconciliation")
    work_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    loaded: list[
        tuple[dict[str, Any], pl.DataFrame, dict[str, Any], dict[str, Any]]
    ] = []
    for spec in SPECS:
        path = work_dir / spec["asset"]
        metadata = download_file(
            f"{BASE_URL}/{spec['tag']}/{spec['asset']}",
            path,
            timeout_seconds=180,
        )
        raw_frame = read_quarantined_csv(path)
        if raw_frame.is_empty():
            raise RuntimeError(f"season-stat source asset is empty: {spec['asset']}")
        frame, normalization = standardize_armstjc_season_stats(
            raw_frame, spec["kind"]
        )
        loaded.append((spec, frame, metadata, normalization))

    session = new_official_session()
    try:
        sports = _sports_map(session)
        source_reports: list[dict[str, Any]] = []
        player_reports: list[dict[str, Any]] = []
        for spec, frame, metadata, normalization in loaded:
            selected = select_reconciliation_players(
                frame,
                spec["kind"],
                per_league=SAMPLE_PER_ACTUAL_LEAGUE,
            )
            source_reports.append(
                {
                    "asset": spec["asset"],
                    "season": spec["season"],
                    "kind": spec["kind"],
                    "sport_label": spec["sport_label"],
                    "source_sha256": metadata["sha256"],
                    "schema_normalization": normalization,
                    "grain": _grain_profile(frame),
                    "accounting": _accounting_profile(frame, spec["kind"]),
                    "selected_reconciliation_players": selected,
                }
            )
            sport_id = sports.get(spec["sport_label"])
            if selected and sport_id is None:
                raise RuntimeError(
                    f"official sports endpoint lacks expected {spec['sport_label']!r}"
                )
            for sample in selected:
                player_reports.append(
                    _compare_player(
                        frame=frame,
                        kind=spec["kind"],
                        sample=sample,
                        sport_id=int(sport_id),
                        season=int(spec["season"]),
                        session=session,
                    )
                )
    finally:
        session.close()

    available_accounting = [
        report["accounting"]
        for report in source_reports
        if report["accounting"].get("available")
    ]
    payload = {
        "report_schema_version": 3,
        "certification_season": CERTIFICATION_SEASON,
        "sample_per_actual_league": SAMPLE_PER_ACTUAL_LEAGUE,
        "official_sports": sports,
        "source_reports": source_reports,
        "player_reconciliation": player_reports,
        "source_grain_all_unique": all(
            report["grain"]["duplicate_group_count"] == 0
            for report in source_reports
        ),
        "available_accounting_check_count": len(available_accounting),
        "source_available_accounting_all_exact": bool(available_accounting)
        and all(
            report.get("mismatch_row_count") == 0
            for report in available_accounting
        ),
        "official_sample_count": len(player_reports),
        "official_player_samples_all_exact": bool(player_reports)
        and all(report["exact"] for report in player_reports),
        "interpretation": (
            f"Completed {CERTIFICATION_SEASON} source rows are compared to current "
            "official completed-season totals. Samples are chosen deterministically "
            "from each actual source league and exclude players who appeared in "
            "multiple source leagues, so the broader official sport total is "
            "comparable. Current official data is a certification oracle, not a "
            "historical-vintage rewrite."
        ),
    }
    (report_dir / "season_stat_official_reconciliation.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )

    lines = [
        "# Season-player aggregate certification",
        "",
        f"Completed season under test: **{CERTIFICATION_SEASON}**",
        f"- Source player-team-league grains all unique: {payload['source_grain_all_unique']}",
        f"- Available exact PA/BF accounting checks: {payload['available_accounting_check_count']}; all exact={payload['source_available_accounting_all_exact']}",
        f"- Deterministic official samples: {payload['official_sample_count']}; all exact={payload['official_player_samples_all_exact']}",
        "",
        "## Source files",
        "",
    ]
    for report in source_reports:
        accounting = report["accounting"]
        if accounting.get("available"):
            accounting_text = (
                f"accounting mismatches {accounting.get('mismatch_row_count')}/"
                f"{accounting.get('compared_row_count')}"
            )
        else:
            accounting_text = (
                f"accounting unavailable; missing "
                f"{accounting.get('missing_columns', [])}"
            )
        samples = ", ".join(
            f"league {sample['league_id']}→{sample['player_id']} ({sample['sample_volume']})"
            for sample in report["selected_reconciliation_players"]
        )
        lines.append(
            f"- `{report['asset']}`: rows {report['grain']['row_count']:,}; "
            f"duplicate grain groups {report['grain']['duplicate_group_count']}; "
            f"{accounting_text}; samples [{samples}]"
        )

    lines.extend(["", "## Official completed-season checks", ""])
    for report in player_reports:
        lines.append(
            f"- {report['kind']} player `{report['person_id']}`, source league "
            f"`{report['league_id']}`: source team rows "
            f"{report['source_team_row_count']}; official splits "
            f"{report['official_split_count']}; compared fields "
            f"{report['compared_field_count']}; differences "
            f"{report['difference_count']}; exact={report['exact']}"
        )
        if not report["exact"]:
            lines.append(
                f"  - diagnostic: differences `{report['differences']}`; "
                f"official metadata `{report['official_split_metadata']}`"
            )

    lines.extend(
        [
            "",
            "A clean result would support using season-player aggregates as the historical outcome-count backbone, with PBP retained for contact profile and sampled official PBP retained for league run-value calibration.",
            "",
        ]
    )
    summary = "\n".join(lines)
    (report_dir / "season_stat_official_reconciliation.md").write_text(
        summary, encoding="utf-8"
    )
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
