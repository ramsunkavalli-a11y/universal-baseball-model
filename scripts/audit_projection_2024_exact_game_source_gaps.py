#!/usr/bin/env python3
"""Audit exact official game surfaces for the remaining 2024 Projection source gaps.

This is diagnostic only. It does not modify source evidence, fit a model, score a
Projection candidate, or access 2025.

Cases frozen from the preceding 2024 historical materialization failures:
- High-A player 669233, game 755829: positive-PA reusable source row absent from official gameLog;
- Single-A player 686541, game 754395: same class;
- Rookie game 774353: PBP game absent from reusable same-game league map.

For the two outcome cases the audit captures the reusable resolved source row and
three exact official game surfaces: playByPlay, boxscore, and feed/live.  It
reports whether the target player appears in each boxscore surface and, when
available, the complete PA/AB/BB/HBP/SO/SF/SH/CI batting vector.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import polars as pl

import materialize_current_talent_historical_milb_game_evidence as historical
from universal_baseball.current_talent_era import current_talent_level_spec
from universal_baseball.current_talent_official_game_identity import (
    project_official_game_league_identity,
)
from universal_baseball.official import capture_official_json, project_official_play_by_play


OUTCOME_CASES = (
    {"label": "high_a", "level": "a+", "player_id": 669233, "game_id": 755829},
    {"label": "single_a", "level": "a", "player_id": 686541, "game_id": 754395},
)
ROOKIE_GAME_ID = 774353
SEASON = 2024
OUTCOME_FIELDS = (
    "batting_PA",
    "batting_AB",
    "batting_BB",
    "batting_HBP",
    "batting_SO",
    "batting_SF",
    "batting_SH",
    "batting_CI",
)


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _int(value: Any) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return int(numeric) if numeric.is_integer() else None


def _boxscore_root(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    live = _mapping(payload.get("liveData"))
    if live:
        return _mapping(live.get("boxscore"))
    return payload


def _player_boxscore_records(payload: Mapping[str, Any], player_id: int) -> list[dict[str, Any]]:
    root = _boxscore_root(payload)
    teams = _mapping(root.get("teams"))
    output: list[dict[str, Any]] = []
    for side in ("away", "home"):
        team = _mapping(teams.get(side))
        players = _mapping(team.get("players"))
        for key, raw in players.items():
            player = _mapping(raw)
            person = _mapping(player.get("person"))
            pid = _int(person.get("id"))
            if pid != int(player_id):
                continue
            batting = _mapping(_mapping(player.get("stats")).get("batting"))
            output.append(
                {
                    "side": side,
                    "player_key": str(key),
                    "person_id": pid,
                    "full_name": person.get("fullName"),
                    "position": _mapping(player.get("position")),
                    "batting_order": player.get("battingOrder"),
                    "batting_stats_raw": dict(batting),
                    "outcome_vector": {
                        "batting_PA": _int(batting.get("plateAppearances")),
                        "batting_AB": _int(batting.get("atBats")),
                        "batting_BB": _int(batting.get("baseOnBalls")),
                        "batting_HBP": _int(batting.get("hitByPitch")),
                        "batting_SO": _int(batting.get("strikeOuts")),
                        "batting_SF": _int(batting.get("sacFlies")),
                        "batting_SH": _int(batting.get("sacBunts")),
                        "batting_CI": _int(batting.get("catchersInterference")),
                    },
                }
            )
    return output


def _all_boxscore_batters(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    root = _boxscore_root(payload)
    teams = _mapping(root.get("teams"))
    output: list[dict[str, Any]] = []
    for side in ("away", "home"):
        team = _mapping(teams.get(side))
        players = _mapping(team.get("players"))
        for key, raw in players.items():
            player = _mapping(raw)
            batting = _mapping(_mapping(player.get("stats")).get("batting"))
            pa = _int(batting.get("plateAppearances"))
            if pa is None or pa <= 0:
                continue
            person = _mapping(player.get("person"))
            output.append(
                {
                    "side": side,
                    "player_key": str(key),
                    "person_id": _int(person.get("id")),
                    "full_name": person.get("fullName"),
                    "plate_appearances": pa,
                    "at_bats": _int(batting.get("atBats")),
                    "walks": _int(batting.get("baseOnBalls")),
                    "strikeouts": _int(batting.get("strikeOuts")),
                }
            )
    return sorted(output, key=lambda row: (str(row["side"]), int(row["person_id"] or -1)))


def _capture(endpoint: str, raw_path: Path, *, session) -> tuple[dict[str, Any], dict[str, Any]]:
    capture = capture_official_json(endpoint, session=session)
    capture.write_raw(raw_path)
    if not isinstance(capture.data, dict):
        raise RuntimeError(f"official endpoint {endpoint} did not return an object")
    meta = {
        "endpoint": capture.endpoint,
        "url": capture.url,
        "retrieved_at_utc": capture.retrieved_at_utc.isoformat(),
        "content_sha256": capture.content_sha256,
        "raw_path": str(raw_path),
    }
    return capture.data, meta


def main() -> int:
    output_root = Path("reports/generated/projection-2024-exact-game-source-gap-audit")
    raw_root = output_root / "raw"
    work_root = Path("data/quarantine/projection-2024-exact-game-source-gap-audit")
    output_root.mkdir(parents=True, exist_ok=True)
    raw_root.mkdir(parents=True, exist_ok=True)
    work_root.mkdir(parents=True, exist_ok=True)

    github_session = historical._github_session()
    source_by_level: dict[str, pl.DataFrame] = {}
    source_metrics: dict[str, Any] = {}
    try:
        for level in sorted({str(case["level"]) for case in OUTCOME_CASES}):
            spec = current_talent_level_spec(SEASON, level)
            _, _, outcomes, metrics = historical._load_player_game_sources(
                season=SEASON,
                level=level,
                league_ids=spec.league_ids,
                work_dir=work_root / ("aplus" if level == "a+" else level),
                session=github_session,
            )
            source_by_level[level] = outcomes
            source_metrics[level] = metrics
    finally:
        github_session.close()

    official_session = historical.new_official_session()
    case_reports: list[dict[str, Any]] = []
    try:
        for case in OUTCOME_CASES:
            level = str(case["level"])
            player_id = int(case["player_id"])
            game_id = int(case["game_id"])
            source = source_by_level[level].filter(
                (pl.col("player_id") == player_id) & (pl.col("game_id") == game_id)
            )
            source_rows = source.to_dicts()
            if len(source_rows) != 1:
                raise RuntimeError(
                    f"expected one resolved reusable source row for {player_id}/{game_id}, "
                    f"found {len(source_rows)}"
                )
            source_row = source_rows[0]
            source_vector = {field: _int(source_row.get(field)) for field in OUTCOME_FIELDS}

            prefix = raw_root / str(case["label"])
            prefix.mkdir(parents=True, exist_ok=True)
            pbp, pbp_meta = _capture(
                f"game/{game_id}/playByPlay",
                prefix / "playbyplay.json",
                session=official_session,
            )
            box, box_meta = _capture(
                f"game/{game_id}/boxscore",
                prefix / "boxscore.json",
                session=official_session,
            )
            live, live_meta = _capture(
                f"game/{game_id}/feed/live",
                prefix / "feed_live.json",
                session=official_session,
            )

            pbp_pa, _ = project_official_play_by_play(game_id, pbp)
            live_plays = _mapping(_mapping(live.get("liveData")).get("plays"))
            live_pbp_payload = {
                "allPlays": live_plays.get("allPlays", []),
                "scoringPlays": live_plays.get("scoringPlays", []),
                "playsByInning": live_plays.get("playsByInning", []),
            }
            live_pa, _ = project_official_play_by_play(game_id, live_pbp_payload)

            exact_identity = project_official_game_league_identity(game_id, live)
            case_reports.append(
                {
                    **case,
                    "source_row": source_row,
                    "source_outcome_vector": source_vector,
                    "official_game_identity": {
                        "game_date": exact_identity.game_date.isoformat(),
                        "game_type": exact_identity.game_type,
                        "league_id": exact_identity.league_id,
                        "sport_id": exact_identity.sport_id,
                        "away_team_id": exact_identity.away_team_id,
                        "home_team_id": exact_identity.home_team_id,
                    },
                    "play_by_play_endpoint": {
                        **pbp_meta,
                        "all_play_count": len(pbp.get("allPlays", [])),
                        "true_pa_count": int(pbp_pa.height),
                        "target_player_true_pa_count": int(
                            pbp_pa.filter(pl.col("batter_id") == player_id).height
                        ),
                    },
                    "feed_live_play_by_play": {
                        **live_meta,
                        "all_play_count": len(live_pbp_payload["allPlays"]),
                        "true_pa_count": int(live_pa.height),
                        "target_player_true_pa_count": int(
                            live_pa.filter(pl.col("batter_id") == player_id).height
                        ),
                    },
                    "boxscore_endpoint": {
                        **box_meta,
                        "target_player_records": _player_boxscore_records(box, player_id),
                        "positive_pa_batters": _all_boxscore_batters(box),
                    },
                    "feed_live_boxscore": {
                        "target_player_records": _player_boxscore_records(live, player_id),
                        "positive_pa_batters": _all_boxscore_batters(live),
                    },
                }
            )

        rookie_prefix = raw_root / "rookie"
        rookie_prefix.mkdir(parents=True, exist_ok=True)
        rookie_live, rookie_meta = _capture(
            f"game/{ROOKIE_GAME_ID}/feed/live",
            rookie_prefix / "feed_live.json",
            session=official_session,
        )
        rookie_identity = project_official_game_league_identity(ROOKIE_GAME_ID, rookie_live)
        rookie_report = {
            "game_id": ROOKIE_GAME_ID,
            **rookie_meta,
            "game_date": rookie_identity.game_date.isoformat(),
            "game_type": rookie_identity.game_type,
            "league_id": rookie_identity.league_id,
            "sport_id": rookie_identity.sport_id,
            "away_team_id": rookie_identity.away_team_id,
            "home_team_id": rookie_identity.home_team_id,
        }
    finally:
        official_session.close()

    report = {
        "report_schema_version": "0.1",
        "gate": "projection_2024_exact_game_source_gap_audit",
        "season": SEASON,
        "outcome_cases": case_reports,
        "rookie_missing_game_league_identity": rookie_report,
        "source_load_metrics": source_metrics,
        "boundary": {
            "source_mutated": False,
            "projection_model_fit": False,
            "projection_scoring": False,
            "accessed_2025": False,
        },
    }
    (output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Projection 2024 exact-game source-gap audit",
        "",
        "Diagnostic only; no source mutation, Projection model fit, scoring, or 2025 access.",
        "",
    ]
    for row in case_reports:
        lines.extend(
            [
                f"## {row['label']} player {row['player_id']} / game {row['game_id']}",
                f"- source vector: `{row['source_outcome_vector']}`",
                f"- /playByPlay target true PAs: {row['play_by_play_endpoint']['target_player_true_pa_count']}",
                f"- feed/live target true PAs: {row['feed_live_play_by_play']['target_player_true_pa_count']}",
                f"- /boxscore target records: {len(row['boxscore_endpoint']['target_player_records'])}",
                f"- feed/live boxscore target records: {len(row['feed_live_boxscore']['target_player_records'])}",
                "",
            ]
        )
    lines.extend(
        [
            "## Rookie missing same-game league identity",
            f"- game: {rookie_report['game_id']}",
            f"- league: {rookie_report['league_id']}",
            f"- sport: {rookie_report['sport_id']}",
            "",
        ]
    )
    (output_root / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
