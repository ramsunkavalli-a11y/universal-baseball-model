#!/usr/bin/env python
"""Classify the 48 first-pitch identity mismatches from certification run 31925278425.

The fixed mismatch set is deliberately diagnostic: it was frozen from the first
280-game batter-identity audit before this classifier was written. We fetch only
current official PBP for the affected games and ask whether each source batter:

1. is the official batter at a nearby atBatIndex (snapshot/reindex drift);
2. appears as an ``offensive_substitution`` player in the same/nearby sequence;
3. bats elsewhere in the game but not nearby; or
4. remains unresolved.

No production repair is made by this script.
"""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any, Mapping

from universal_baseball.official_capture import capture_official_json, new_official_session


# game_pk, source atBatIndex, source first-pitch batter, current official batter, league_id
MISMATCHES = [
    (781888, 87, 800683, 700032, 109), (781888, 86, 679938, 801126, 109),
    (782307, 62, 703715, 664332, 109), (788431, 77, 692591, 694543, 110),
    (788562, 65, 805117, 801592, 110), (788562, 82, 805319, 700815, 110),
    (788570, 74, 827264, 683588, 110), (788768, 71, 694732, 691435, 110),
    (782518, 81, 680846, 690992, 111), (782720, 85, 810053, 676509, 111),
    (782721, 49, 687272, 686755, 111), (782996, 80, 687248, 685298, 111),
    (779867, 73, 664670, 687231, 112), (779877, 61, 681909, 592696, 112),
    (783139, 77, 673901, 692348, 113), (783140, 76, 801076, 673901, 113),
    (783269, 65, 691370, 699144, 113), (784155, 65, 694182, 701616, 116),
    (784155, 34, 815089, 800957, 116), (784285, 75, 684712, 804645, 116),
    (784485, 75, 691797, 803745, 116), (784551, 71, 809338, 826164, 116),
    (780631, 100, 702750, 656449, 117), (772280, 72, 682728, 806730, 121),
    (772321, 31, 703179, 815304, 121), (772321, 76, 699113, 691401, 121),
    (772498, 91, 703639, 806959, 121), (785482, 8, 802219, 813620, 123),
    (785610, 64, 806368, 695000, 123), (785798, 50, 692489, 691605, 123),
    (785798, 54, 691770, 693418, 123), (785874, 67, 800510, 802219, 123),
    (771847, 67, 691450, 691452, 124), (771851, 98, 699098, 685337, 124),
    (771989, 57, 808488, 642451, 124), (771993, 68, 800369, 800348, 124),
    (772051, 60, 808516, 805104, 124), (772102, 56, 805103, 801256, 124),
    (772127, 58, 808237, 800384, 124), (772162, 63, 800139, 808037, 124),
    (772162, 56, 800405, 806962, 124), (788957, 74, 686683, 684109, 126),
    (788968, 62, 805931, 676038, 126), (789020, 58, 806534, 800194, 126),
    (789095, 67, 823703, 687982, 126), (789097, 58, 691285, 800198, 126),
    (773543, 64, 821625, 808060, 130), (773850, 67, 800143, 821235, 130),
]


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _int(value: Any) -> int | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return int(numeric) if numeric.is_integer() else None


def _game_index(payload: Mapping[str, Any]) -> tuple[dict[int, int], list[dict[str, Any]]]:
    batters: dict[int, int] = {}
    substitutions: list[dict[str, Any]] = []
    for raw_play in payload.get("allPlays") or []:
        play = _mapping(raw_play)
        index = _int(play.get("atBatIndex"))
        if index is None:
            continue
        batter = _int(_mapping(_mapping(play.get("matchup")).get("batter")).get("id"))
        if batter is not None:
            batters[index] = batter
        for raw_event in play.get("playEvents") or []:
            event = _mapping(raw_event)
            details = _mapping(event.get("details"))
            if str(details.get("eventType") or "") != "offensive_substitution":
                continue
            player_id = _int(_mapping(event.get("player")).get("id"))
            substitutions.append(
                {
                    "at_bat_index": index,
                    "player_id": player_id,
                    "description": details.get("description"),
                }
            )
    return batters, substitutions


def main() -> int:
    report_dir = Path("reports/generated/source-batter-identity-mismatch-diagnostic")
    report_dir.mkdir(parents=True, exist_ok=True)

    by_game: dict[int, tuple[dict[int, int], list[dict[str, Any]], str]] = {}
    session = new_official_session()
    try:
        for game_pk in sorted({row[0] for row in MISMATCHES}):
            capture = capture_official_json(f"game/{game_pk}/playByPlay", session=session)
            if not isinstance(capture.data, Mapping):
                raise RuntimeError(f"official PBP is not an object for game {game_pk}")
            batters, substitutions = _game_index(capture.data)
            by_game[game_pk] = (batters, substitutions, capture.content_sha256)
    finally:
        session.close()

    rows: list[dict[str, Any]] = []
    for game_pk, source_index, source_id, official_id, league_id in MISMATCHES:
        batters, substitutions, sha = by_game[game_pk]
        batter_indices = sorted(index for index, batter in batters.items() if batter == source_id)
        nearest_index = (
            min(batter_indices, key=lambda index: (abs(index - source_index), index))
            if batter_indices else None
        )
        nearest_delta = nearest_index - source_index if nearest_index is not None else None
        substitution_hits = [
            row for row in substitutions if row["player_id"] == source_id
        ]
        same_sequence_sub = [
            row for row in substitution_hits if row["at_bat_index"] == source_index
        ]
        nearby_sub = [
            row for row in substitution_hits
            if abs(int(row["at_bat_index"]) - source_index) <= 1
        ]

        if nearest_delta is not None and abs(nearest_delta) <= 2:
            classification = "nearby_official_batter_index_drift"
        elif same_sequence_sub:
            classification = "same_sequence_offensive_substitution_player"
        elif nearby_sub:
            classification = "nearby_offensive_substitution_player"
        elif batter_indices:
            classification = "source_id_bats_elsewhere_in_game"
        elif substitution_hits:
            classification = "source_id_is_offensive_substitution_elsewhere"
        else:
            classification = "unresolved"

        rows.append(
            {
                "game_pk": game_pk,
                "league_id": league_id,
                "source_at_bat_index": source_index,
                "source_batter_id": source_id,
                "current_official_batter_id": official_id,
                "current_official_batter_at_source_index": batters.get(source_index),
                "source_id_official_batter_indices": batter_indices,
                "nearest_official_batter_index": nearest_index,
                "nearest_index_delta": nearest_delta,
                "source_id_substitution_events": substitution_hits,
                "classification": classification,
                "official_snapshot_sha256": sha,
            }
        )

    counts = Counter(row["classification"] for row in rows)
    delta_counts = Counter(
        int(row["nearest_index_delta"])
        for row in rows
        if row["nearest_index_delta"] is not None
        and abs(int(row["nearest_index_delta"])) <= 5
    )
    payload = {
        "report_schema_version": 1,
        "source_audit_run_id": 31925278425,
        "mismatch_count": len(rows),
        "classification_counts": dict(sorted(counts.items())),
        "nearby_index_delta_counts": dict(sorted(delta_counts.items())),
        "rows": rows,
    }
    (report_dir / "source_batter_identity_mismatch_diagnostic.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )

    lines = [
        "# Source batter identity mismatch diagnostic",
        "",
        f"- Frozen first-pitch mismatch cases: {len(rows)}",
        f"- Affected games: {len(by_game)}",
        f"- Classifications: `{dict(sorted(counts.items()))}`",
        f"- Nearby official-batter index deltas (|delta| <= 5): `{dict(sorted(delta_counts.items()))}`",
        "",
    ]
    for classification, count in sorted(counts.items()):
        lines.append(f"- {classification}: {count}")
    lines.append("")
    summary = "\n".join(lines)
    (report_dir / "source_batter_identity_mismatch_diagnostic.md").write_text(
        summary, encoding="utf-8"
    )
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
