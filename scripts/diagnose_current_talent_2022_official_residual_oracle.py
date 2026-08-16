#!/usr/bin/env python
"""Confirm sparse 2022 residual classification with official season + gameLog stats.

Certification-only oracle for six previously localized player × league cases.
No reusable source is mutated and no production correction is performed here.
"""

from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from universal_baseball.official_capture import capture_official_json, new_official_session


SEASON = 2022
CASES = (
    {"level": "aaa", "sport_id": 11, "league_id": 117, "player_id": 592261,
     "source": {"plateAppearances": 426, "baseOnBalls": 77, "hitByPitch": 4, "strikeOuts": 116},
     "season_asset": {"plateAppearances": 426, "baseOnBalls": 76, "hitByPitch": 5, "strikeOuts": 116}},
    {"level": "a", "sport_id": 14, "league_id": 110, "player_id": 702112,
     "source": {"plateAppearances": 143, "baseOnBalls": 17, "hitByPitch": 6, "strikeOuts": 31},
     "season_asset": {"plateAppearances": 144, "baseOnBalls": 17, "hitByPitch": 6, "strikeOuts": 32}},
    {"level": "a", "sport_id": 14, "league_id": 122, "player_id": 700998,
     "source": {"plateAppearances": 171, "baseOnBalls": 21, "hitByPitch": 1, "strikeOuts": 58},
     "season_asset": {"plateAppearances": 172, "baseOnBalls": 21, "hitByPitch": 1, "strikeOuts": 59}},
    {"level": "a", "sport_id": 14, "league_id": 123, "player_id": 686577,
     "source": {"plateAppearances": 395, "baseOnBalls": 22, "hitByPitch": 2, "strikeOuts": 138},
     "season_asset": {"plateAppearances": 396, "baseOnBalls": 22, "hitByPitch": 2, "strikeOuts": 138}},
    {"level": "rk", "sport_id": 16, "league_id": 124, "player_id": 695467,
     "source": {"plateAppearances": 39, "baseOnBalls": 3, "hitByPitch": 4, "strikeOuts": 11},
     "season_asset": {"plateAppearances": 39, "baseOnBalls": 3, "hitByPitch": 4, "strikeOuts": 12}},
    {"level": "rk", "sport_id": 16, "league_id": 130, "player_id": 800313,
     "source": {"plateAppearances": 68, "baseOnBalls": 5, "hitByPitch": 2, "strikeOuts": 17},
     "season_asset": {"plateAppearances": 69, "baseOnBalls": 5, "hitByPitch": 2, "strikeOuts": 17}},
)
FIELDS = ("plateAppearances", "baseOnBalls", "hitByPitch", "strikeOuts")


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


def _endpoint(player_id: int, sport_id: int, stats: str) -> str:
    return f"people/{player_id}/stats?{urlencode({'stats': stats, 'group': 'hitting', 'season': SEASON, 'sportId': sport_id})}"


def _splits(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for group in payload.get("stats") or []:
        for raw in _mapping(group).get("splits") or []:
            split = _mapping(raw)
            stat = _mapping(split.get("stat"))
            game = _mapping(split.get("game"))
            league = _mapping(split.get("league"))
            rows.append({
                "game_pk": _int(game.get("gamePk") or game.get("pk") or game.get("id")),
                "date": split.get("date"),
                "league_id": _int(league.get("id")),
                **{field: _int(stat.get(field)) for field in FIELDS},
            })
    return rows


def _totals(rows: list[dict[str, Any]], league_id: int) -> dict[str, int]:
    target = [row for row in rows if row.get("league_id") in (None, league_id)]
    return {field: sum(int(row.get(field) or 0) for row in target) for field in FIELDS}


def _classify(case: dict[str, Any], official: dict[str, int]) -> str:
    source = case["source"]
    season_asset = case["season_asset"]
    if official == source and official != season_asset:
        return "official_matches_player_game_source_season_asset_stale"
    if official == season_asset and official != source:
        return "official_matches_season_asset_player_game_stale"
    if official == source == season_asset:
        return "all_agree"
    return "official_disagrees_with_both_or_mixed"


def main() -> int:
    report_root = Path("reports/generated/current-talent-2022-official-residual-oracle")
    report_root.mkdir(parents=True, exist_ok=True)
    session = new_official_session()
    reports: list[dict[str, Any]] = []
    try:
        for raw_case in CASES:
            case = dict(raw_case)
            season_capture = capture_official_json(
                _endpoint(case["player_id"], case["sport_id"], "season"), session=session
            )
            game_capture = capture_official_json(
                _endpoint(case["player_id"], case["sport_id"], "gameLog"), session=session
            )
            if not isinstance(season_capture.data, Mapping) or not isinstance(game_capture.data, Mapping):
                raise RuntimeError("official residual oracle payload is not an object")
            season_rows = _splits(season_capture.data)
            game_rows = _splits(game_capture.data)
            season_totals = _totals(season_rows, int(case["league_id"]))
            game_totals = _totals(game_rows, int(case["league_id"]))
            nonzero_game_splits = [
                row for row in game_rows
                if row.get("league_id") == case["league_id"]
                and any(int(row.get(field) or 0) for field in FIELDS)
            ]
            reports.append({
                **case,
                "official_season_split_count": len(season_rows),
                "official_season_totals": season_totals,
                "official_game_log_totals": game_totals,
                "official_season_vs_game_log_exact": season_totals == game_totals,
                "classification": _classify(case, season_totals),
                "official_season_snapshot_sha256": season_capture.content_sha256,
                "official_game_log_snapshot_sha256": game_capture.content_sha256,
                "nonzero_official_game_splits": nonzero_game_splits,
            })
    finally:
        session.close()

    payload = {
        "report_schema_version": 1,
        "season": SEASON,
        "cases": reports,
        "all_official_season_vs_game_log_exact": all(
            row["official_season_vs_game_log_exact"] for row in reports
        ),
        "interpretation": "Certification-only current official oracle; no historical evidence mutated.",
    }
    (report_root / "report.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )
    lines = ["# 2022 official residual oracle", ""]
    for row in reports:
        lines.append(
            f"- {row['level']} league={row['league_id']} player={row['player_id']}: "
            f"{row['classification']}; season_vs_gameLog={row['official_season_vs_game_log_exact']}"
        )
    text = "\n".join(lines)
    (report_root / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
