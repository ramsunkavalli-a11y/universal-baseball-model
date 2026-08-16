#!/usr/bin/env python
"""Certify reusable season-player aggregate stats against official season splits.

The architectural goal is to avoid replaying every historical official game if
public season boxscore aggregates can reliably supply PA/BF and non-contact
outcome counts. This audit therefore tests:

1. deterministic player-team-league grain;
2. baseball accounting identities inside the source rows; and
3. representative player/team/league season splits against the current official
   MLB Stats API person-season endpoint.

This remains certification: no source row is silently corrected from the
current official feed.
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


BASE_URL = "https://github.com/armstjc/milb-data-repository/releases/download"
SPECS = (
    {
        "kind": "batting",
        "tag": "season_player_batting",
        "asset": "2026_aaa_season_batting_stats.csv",
        "sport_label": "Triple-A",
        "player_ids": [807916, 814028],
    },
    {
        "kind": "batting",
        "tag": "season_player_batting",
        "asset": "2026_rk_season_batting_stats.csv",
        "sport_label": "Rookie",
        "player_ids": [710367, 829570],
    },
    {
        "kind": "pitching",
        "tag": "season_player_pitching",
        "asset": "2026_aaa_season_pitching_stats.csv",
        "sport_label": "Triple-A",
        "player_ids": [808580, 682000],
    },
    {
        "kind": "pitching",
        "tag": "season_player_pitching",
        "asset": "2026_rk_season_pitching_stats.csv",
        "sport_label": "Rookie",
        "player_ids": [],
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


def _source_numeric(frame: pl.DataFrame, column: str) -> pl.Expr:
    return pl.col(column).cast(pl.Int64, strict=False).fill_null(0)


def _grain_profile(frame: pl.DataFrame, kind: str) -> dict[str, Any]:
    prefix = f"{kind}_"
    required = {
        f"{prefix}player_id",
        f"{prefix}team_id",
        f"{prefix}league_id",
        f"{prefix}year",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{kind} source missing grain columns: {missing}")
    key = [
        f"{prefix}year",
        f"{prefix}league_id",
        f"{prefix}team_id",
        f"{prefix}player_id",
    ]
    duplicates = frame.group_by(key).len().filter(pl.col("len") > 1)
    return {
        "key": key,
        "row_count": frame.height,
        "duplicate_group_count": duplicates.height,
        "duplicate_extra_row_count": int(
            duplicates.select((pl.col("len") - 1).sum()).item() or 0
        ),
        "distinct_player_count": frame.get_column(f"{prefix}player_id").n_unique(),
        "distinct_team_count": frame.get_column(f"{prefix}team_id").n_unique(),
        "distinct_league_count": frame.get_column(f"{prefix}league_id").n_unique(),
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
        return {"available": False, "missing_columns": missing}

    working = frame.with_columns(
        _source_numeric(frame, total).alias("__total"),
        sum(
            (_source_numeric(frame, column) for column in components),
            start=pl.lit(0, dtype=pl.Int64),
        ).alias("__components"),
    )
    mismatches = working.filter(pl.col("__total") != pl.col("__components"))
    difference_counts = Counter(
        int(value)
        for value in mismatches.select(
            (pl.col("__total") - pl.col("__components")).alias("difference")
        ).get_column("difference").to_list()
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
            [column for column in frame.columns if column in {total, *components, f"{kind}_player_id", f"{kind}_team_id", f"{kind}_league_id"}]
        ).head(15).to_dicts(),
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


def _stats_endpoint(person_id: int, kind: str, sport_id: int) -> str:
    params = {
        "stats": "season",
        "group": "hitting" if kind == "batting" else "pitching",
        "season": 2026,
        "sportId": sport_id,
    }
    return f"people/{person_id}/stats?{urlencode(params)}"


def _official_splits(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for stats_group in payload.get("stats") or []:
        group = _mapping(stats_group)
        for raw_split in group.get("splits") or []:
            split = _mapping(raw_split)
            team = _mapping(split.get("team"))
            league = _mapping(split.get("league"))
            sport = _mapping(split.get("sport"))
            stat = _mapping(split.get("stat"))
            result.append(
                {
                    "team_id": _int(team.get("id")),
                    "team_name": _text(team.get("name")),
                    "league_id": _int(league.get("id")),
                    "league_name": _text(league.get("name")),
                    "sport_id": _int(sport.get("id")),
                    "sport_name": _text(sport.get("name")),
                    "stat": dict(stat),
                }
            )
    return result


def _source_rows_for_player(frame: pl.DataFrame, kind: str, person_id: int) -> list[dict[str, Any]]:
    player_col = f"{kind}_player_id"
    return frame.filter(
        pl.col(player_col).cast(pl.Int64, strict=False) == person_id
    ).to_dicts()


def _compare_player(
    *,
    frame: pl.DataFrame,
    kind: str,
    person_id: int,
    sport_id: int,
    session: Any,
) -> dict[str, Any]:
    endpoint = _stats_endpoint(person_id, kind, sport_id)
    capture = capture_official_json(endpoint, session=session)
    if not isinstance(capture.data, Mapping):
        raise RuntimeError(f"official stats payload for {person_id} is not an object")
    official = _official_splits(capture.data)
    source = _source_rows_for_player(frame, kind, person_id)
    compare_fields = BATTING_COMPARE if kind == "batting" else PITCHING_COMPARE

    matches: list[dict[str, Any]] = []
    unmatched_source: list[dict[str, Any]] = []
    official_used: set[int] = set()
    for source_row in source:
        team_id = _int(source_row.get(f"{kind}_team_id"))
        league_id = _int(source_row.get(f"{kind}_league_id"))
        candidates = [
            (index, row)
            for index, row in enumerate(official)
            if row["team_id"] == team_id
            and (row["league_id"] in {None, league_id})
        ]
        if not candidates:
            unmatched_source.append(
                {
                    "team_id": team_id,
                    "league_id": league_id,
                    "team_name": source_row.get(f"{kind}_team_name"),
                }
            )
            continue
        index, official_row = candidates[0]
        official_used.add(index)
        differences: dict[str, Any] = {}
        compared = 0
        for official_field, source_field in compare_fields.items():
            if source_field not in source_row:
                continue
            official_value = _int(official_row["stat"].get(official_field))
            source_value = _int(source_row.get(source_field))
            if official_value is None and source_value is None:
                continue
            compared += 1
            if official_value != source_value:
                differences[source_field] = {
                    "source": source_value,
                    "official": official_value,
                    "official_field": official_field,
                }
        matches.append(
            {
                "team_id": team_id,
                "league_id": league_id,
                "official_sport_id": official_row["sport_id"],
                "official_sport_name": official_row["sport_name"],
                "compared_field_count": compared,
                "difference_count": len(differences),
                "differences": differences,
            }
        )

    return {
        "person_id": person_id,
        "kind": kind,
        "sport_id_requested": sport_id,
        "endpoint": endpoint,
        "official_snapshot_sha256": capture.content_sha256,
        "source_row_count": len(source),
        "official_split_count": len(official),
        "matched_source_row_count": len(matches),
        "unmatched_source_rows": unmatched_source,
        "unmatched_official_splits": [
            row for index, row in enumerate(official) if index not in official_used
        ],
        "matched_rows": matches,
        "all_compared_fields_exact": bool(matches)
        and not unmatched_source
        and all(row["difference_count"] == 0 for row in matches),
        "official_split_preview": official[:8],
    }


def main() -> int:
    work_dir = Path("data/quarantine/season-stat-official-reconciliation")
    report_dir = Path("reports/generated/season-stat-official-reconciliation")
    work_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    loaded: list[tuple[dict[str, Any], pl.DataFrame, dict[str, Any]]] = []
    for spec in SPECS:
        path = work_dir / spec["asset"]
        metadata = download_file(
            f"{BASE_URL}/{spec['tag']}/{spec['asset']}", path, timeout_seconds=180
        )
        frame = read_quarantined_csv(path)
        loaded.append((spec, frame, metadata))

    session = new_official_session()
    try:
        sports = _sports_map(session)
        source_reports: list[dict[str, Any]] = []
        player_reports: list[dict[str, Any]] = []
        for spec, frame, metadata in loaded:
            source_reports.append(
                {
                    "asset": spec["asset"],
                    "kind": spec["kind"],
                    "source_sha256": metadata["sha256"],
                    "grain": _grain_profile(frame, spec["kind"]),
                    "accounting": _accounting_profile(frame, spec["kind"]),
                }
            )
            sport_id = sports.get(spec["sport_label"])
            if spec["player_ids"] and sport_id is None:
                raise RuntimeError(
                    f"official sports endpoint lacks expected {spec['sport_label']!r}; "
                    f"available examples={list(sorted(sports))[:30]}"
                )
            for person_id in spec["player_ids"]:
                player_reports.append(
                    _compare_player(
                        frame=frame,
                        kind=spec["kind"],
                        person_id=int(person_id),
                        sport_id=int(sport_id),
                        session=session,
                    )
                )
    finally:
        session.close()

    payload = {
        "report_schema_version": 1,
        "official_sports": sports,
        "source_reports": source_reports,
        "player_reconciliation": player_reports,
        "source_grain_all_unique": all(
            report["grain"]["duplicate_group_count"] == 0
            for report in source_reports
        ),
        "source_accounting_all_exact": all(
            report["accounting"].get("mismatch_row_count") == 0
            for report in source_reports
            if report["accounting"].get("available")
        ),
        "official_player_rows_all_exact": all(
            report["all_compared_fields_exact"] for report in player_reports
        ) if player_reports else None,
        "interpretation": (
            "Current official season splits are a certification oracle, not a historical-vintage rewrite. "
            "The reusable season rows remain immutable source snapshots with their own checksums."
        ),
    }
    (report_dir / "season_stat_official_reconciliation.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )

    lines = [
        "# Season-player aggregate certification",
        "",
        f"- Source player-team-league grains all unique: {payload['source_grain_all_unique']}",
        f"- PA/BF accounting identities all exact: {payload['source_accounting_all_exact']}",
        f"- Sampled official player/team splits all exact: {payload['official_player_rows_all_exact']}",
        "",
        "## Source rows",
        "",
    ]
    for report in source_reports:
        accounting = report["accounting"]
        lines.append(
            f"- `{report['asset']}`: rows {report['grain']['row_count']:,}; "
            f"duplicate player-team-league-season groups {report['grain']['duplicate_group_count']}; "
            f"accounting mismatches {accounting.get('mismatch_row_count', 'n/a')}/{accounting.get('compared_row_count', 'n/a')}"
        )
    lines.extend(["", "## Official player split checks", ""])
    for report in player_reports:
        lines.append(
            f"- {report['kind']} player `{report['person_id']}`: "
            f"source rows {report['source_row_count']}; official splits {report['official_split_count']}; "
            f"matched {report['matched_source_row_count']}; exact={report['all_compared_fields_exact']}"
        )
        if report["unmatched_source_rows"] or not report["all_compared_fields_exact"]:
            lines.append(
                f"  - diagnostic: unmatched source `{report['unmatched_source_rows']}`; "
                f"matched rows `{report['matched_rows']}`"
            )
    lines.extend(
        [
            "",
            "A clean result would justify using season-player aggregates as the outcome-count backbone while retaining PBP for contact profile and sampled official PBP for league run-value calibration. It would not replace PBP where sequence/contact evidence is required.",
            "",
        ]
    )
    summary = "\n".join(lines)
    (report_dir / "season_stat_official_reconciliation.md").write_text(summary, encoding="utf-8")
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
