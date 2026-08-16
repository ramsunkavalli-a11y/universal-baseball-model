#!/usr/bin/env python
"""Fetch full eight-field official vectors for five localized 2022 corrections."""

from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from universal_baseball.official_capture import capture_official_json, new_official_session


CASES = (
    {"player_id": 702112, "sport_id": 14, "league_id": 110, "game_pk": 670939},
    {"player_id": 700998, "sport_id": 14, "league_id": 122, "game_pk": 669885},
    {"player_id": 686577, "sport_id": 14, "league_id": 123, "game_pk": 670544},
    {"player_id": 695467, "sport_id": 16, "league_id": 124, "game_pk": 712445},
    {"player_id": 800313, "sport_id": 16, "league_id": 130, "game_pk": 712082},
)
FIELDS = (
    "plateAppearances",
    "atBats",
    "baseOnBalls",
    "hitByPitch",
    "strikeOuts",
    "sacFlies",
    "sacBunts",
    "catchersInterference",
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


def main() -> int:
    root = Path("reports/generated/current-talent-2022-corrected-game-vectors")
    root.mkdir(parents=True, exist_ok=True)
    session = new_official_session()
    reports: list[dict[str, Any]] = []
    try:
        for case in CASES:
            endpoint = "people/{}/stats?{}".format(
                case["player_id"],
                urlencode({
                    "stats": "gameLog",
                    "group": "hitting",
                    "season": 2022,
                    "sportId": case["sport_id"],
                }),
            )
            capture = capture_official_json(endpoint, session=session)
            if not isinstance(capture.data, Mapping):
                raise RuntimeError("official gameLog payload is not an object")
            matches: list[dict[str, Any]] = []
            for group in capture.data.get("stats") or []:
                for raw in _mapping(group).get("splits") or []:
                    split = _mapping(raw)
                    game = _mapping(split.get("game"))
                    league = _mapping(split.get("league"))
                    game_pk = _int(game.get("gamePk") or game.get("pk") or game.get("id"))
                    if game_pk != case["game_pk"]:
                        continue
                    stat = _mapping(split.get("stat"))
                    matches.append({
                        "game_pk": game_pk,
                        "date": split.get("date"),
                        "game_type": split.get("gameType"),
                        "league_id": _int(league.get("id")),
                        **{field: _int(stat.get(field)) for field in FIELDS},
                    })
            reports.append({**case, "match_count": len(matches), "matches": matches})
    finally:
        session.close()
    payload = {"season": 2022, "cases": reports}
    (root / "report.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    text = "\n".join(
        ["# 2022 corrected official game vectors", ""]
        + [f"- player={row['player_id']} game={row['game_pk']}: {row['matches']}" for row in reports]
    )
    (root / "report.md").write_text(text, encoding="utf-8")
    print(text)
    if any(row["match_count"] != 1 for row in reports):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
