#!/usr/bin/env python
"""Reconcile reusable airborne PA narratives to MLB Stats API result descriptions.

The foul-air vocabulary audit found a candidate explicit narrative rule. This
script checks that the reusable ``description`` field is preserving the same PA
narrative concept as official Stats API ``allPlay.result.description`` rather
than a source-specific rewrite.

For each audited asset it deterministically samples airborne PAs from both sides
of the candidate rule (explicit ``foul territory`` and ordinary airborne),
spreading samples across games when possible. It then compares:

- source natural PA key to official ``atBatIndex``;
- official PA semantics;
- normalized narrative text;
- candidate foul-air classification.

Classification agreement is a hard gate. Exact narrative equality is reported
separately because current official text may contain later corrections to old
historical descriptions.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

import polars as pl

from audit_foul_air_descriptions import classify_description
from universal_baseball.certification import download_file, read_quarantined_csv
from universal_baseball.event_types import PLATE_APPEARANCE_EVENT_TYPES
from universal_baseball.official_capture import capture_official_json, new_official_session
from universal_baseball.trajectory_audit import AIRBORNE_TYPES, collapse_trajectory_evidence


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--asset-name", required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--sample-per-class", type=int, default=6)
    return parser.parse_args()


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _int(value: Any) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not numeric.is_integer():
        return None
    return int(numeric)


def _clean_text(value: Any) -> str:
    return "" if value is None else " ".join(str(value).split())


def _source_airborne_rows(frame: pl.DataFrame) -> list[dict[str, Any]]:
    collapsed = collapse_trajectory_evidence(frame.unique())
    required = {"game_pk", "at_bat_number", "pitch_number", "bb_type", "description"}
    missing = sorted(required - set(collapsed.columns))
    if missing:
        raise ValueError(f"source missing official-reconciliation fields: {missing}")
    rows = (
        collapsed.filter(
            pl.col("bb_type").is_in(list(AIRBORNE_TYPES))
            & pl.col("description").is_not_null()
        )
        .sort(["game_pk", "at_bat_number", "pitch_number"])
        .to_dicts()
    )
    result: list[dict[str, Any]] = []
    for row in rows:
        game_pk = _int(row.get("game_pk"))
        at_bat_index = _int(row.get("at_bat_number"))
        pitch_number = _int(row.get("pitch_number"))
        if game_pk is None or at_bat_index is None or pitch_number is None:
            continue
        text = _clean_text(row.get("description"))
        classification = classify_description(text)
        result.append(
            {
                "game_pk": game_pk,
                "at_bat_index": at_bat_index,
                "pitch_number": pitch_number,
                "bb_type": str(row.get("bb_type")),
                "source_description": text,
                "source_explicit_foul_territory": bool(
                    classification["explicit_foul_territory"]
                ),
            }
        )
    return result


def _sample_class(
    rows: list[dict[str, Any]],
    *,
    flag: bool,
    limit: int,
) -> list[dict[str, Any]]:
    candidates = [
        row for row in rows if bool(row["source_explicit_foul_territory"]) is flag
    ]
    if not candidates:
        return []

    # Prefer game diversity so the official check does not certify one feed row
    # repeated across many PAs from the same game. Supplement deterministically
    # only if the class has fewer unique games than requested samples.
    selected: list[dict[str, Any]] = []
    seen_games: set[int] = set()
    selected_keys: set[tuple[int, int]] = set()
    for row in candidates:
        game_pk = int(row["game_pk"])
        key = (game_pk, int(row["at_bat_index"]))
        if game_pk in seen_games:
            continue
        selected.append(row)
        seen_games.add(game_pk)
        selected_keys.add(key)
        if len(selected) >= limit:
            return selected
    for row in candidates:
        key = (int(row["game_pk"]), int(row["at_bat_index"]))
        if key in selected_keys:
            continue
        selected.append(row)
        selected_keys.add(key)
        if len(selected) >= limit:
            break
    return selected


def _official_sequence_map(payload: Mapping[str, Any]) -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    for raw_play in payload.get("allPlays") or []:
        play = _mapping(raw_play)
        at_bat_index = _int(play.get("atBatIndex"))
        if at_bat_index is None:
            continue
        structured = _mapping(play.get("result"))
        event_type = str(structured.get("eventType") or "").strip()
        result[at_bat_index] = {
            "event_type": event_type or None,
            "is_plate_appearance": event_type in PLATE_APPEARANCE_EVENT_TYPES,
            "description": _clean_text(structured.get("description")),
        }
    return result


def main() -> int:
    args = parse_args()
    if args.sample_per_class < 1:
        raise ValueError("sample-per-class must be at least 1")
    args.work_dir.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)

    source_path = args.work_dir / args.asset_name
    metadata = download_file(args.url, source_path, timeout_seconds=240)
    frame = read_quarantined_csv(source_path)
    if frame.is_empty():
        raise RuntimeError(f"foul-air reconciliation source is empty: {args.asset_name}")

    airborne = _source_airborne_rows(frame)
    flagged = _sample_class(
        airborne, flag=True, limit=args.sample_per_class
    )
    ordinary = _sample_class(
        airborne, flag=False, limit=args.sample_per_class
    )
    if not flagged:
        raise RuntimeError("source has no explicit foul-territory airborne candidates")
    if not ordinary:
        raise RuntimeError("source has no ordinary airborne candidates")
    samples = sorted(
        [*flagged, *ordinary],
        key=lambda row: (int(row["game_pk"]), int(row["at_bat_index"])),
    )

    game_maps: dict[int, dict[int, dict[str, Any]]] = {}
    game_sha256: dict[int, str] = {}
    session = new_official_session()
    try:
        for game_pk in sorted({int(row["game_pk"]) for row in samples}):
            capture = capture_official_json(
                f"game/{game_pk}/playByPlay", session=session
            )
            if not isinstance(capture.data, Mapping):
                raise RuntimeError(f"official game {game_pk} playByPlay is not an object")
            game_maps[game_pk] = _official_sequence_map(capture.data)
            game_sha256[game_pk] = capture.content_sha256
    finally:
        session.close()

    comparisons: list[dict[str, Any]] = []
    for source in samples:
        game_pk = int(source["game_pk"])
        at_bat_index = int(source["at_bat_index"])
        official = game_maps.get(game_pk, {}).get(at_bat_index)
        if official is None:
            comparisons.append(
                {
                    **source,
                    "official_found": False,
                    "official_snapshot_sha256": game_sha256.get(game_pk),
                    "official_event_type": None,
                    "official_is_plate_appearance": False,
                    "official_description": None,
                    "official_explicit_foul_territory": None,
                    "description_exact": False,
                    "classification_exact": False,
                }
            )
            continue
        official_description = _clean_text(official.get("description"))
        official_classification = classify_description(official_description)
        comparisons.append(
            {
                **source,
                "official_found": True,
                "official_snapshot_sha256": game_sha256.get(game_pk),
                "official_event_type": official.get("event_type"),
                "official_is_plate_appearance": bool(official.get("is_plate_appearance")),
                "official_description": official_description,
                "official_explicit_foul_territory": bool(
                    official_classification["explicit_foul_territory"]
                ),
                "description_exact": source["source_description"] == official_description,
                "classification_exact": bool(
                    source["source_explicit_foul_territory"]
                )
                == bool(official_classification["explicit_foul_territory"]),
            }
        )

    source_class_counts = {
        "explicit_foul_territory": sum(
            bool(row["source_explicit_foul_territory"]) for row in comparisons
        ),
        "ordinary_airborne": sum(
            not bool(row["source_explicit_foul_territory"]) for row in comparisons
        ),
    }
    official_found_count = sum(bool(row["official_found"]) for row in comparisons)
    official_pa_count = sum(bool(row["official_is_plate_appearance"]) for row in comparisons)
    classification_exact_count = sum(bool(row["classification_exact"]) for row in comparisons)
    description_exact_count = sum(bool(row["description_exact"]) for row in comparisons)
    pass_gate = (
        bool(comparisons)
        and official_found_count == len(comparisons)
        and official_pa_count == len(comparisons)
        and classification_exact_count == len(comparisons)
    )

    payload = {
        "report_schema_version": 1,
        "status": "official_foul_air_narrative_reconciliation",
        "source_asset": args.asset_name,
        "source_url": args.url,
        "source_metadata": metadata,
        "sample_per_class_requested": args.sample_per_class,
        "sample_class_counts": source_class_counts,
        "sample_count": len(comparisons),
        "sample_game_count": len({int(row["game_pk"]) for row in comparisons}),
        "official_found_count": official_found_count,
        "official_plate_appearance_count": official_pa_count,
        "classification_exact_count": classification_exact_count,
        "description_exact_count": description_exact_count,
        "description_exact_rate": description_exact_count / len(comparisons),
        "classification_exact_rate": classification_exact_count / len(comparisons),
        "pass": pass_gate,
        "comparisons": comparisons,
        "interpretation": (
            "The hard gate is candidate foul-air classification agreement on official "
            "true PAs. Normalized narrative text equality is diagnostic because current "
            "official records may include later textual corrections to historical PAs."
        ),
    }
    (args.report_dir / "foul_air_official_reconciliation.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        "# Foul-air narrative official reconciliation",
        "",
        f"- Asset: `{args.asset_name}`",
        f"- Source SHA-256: `{metadata['sha256']}`",
        f"- Samples: {len(comparisons)} across {payload['sample_game_count']} games",
        f"- Source class counts: `{source_class_counts}`",
        f"- Official sequence found: {official_found_count}/{len(comparisons)}",
        f"- Official true PA: {official_pa_count}/{len(comparisons)}",
        f"- Candidate foul-air classification exact: {classification_exact_count}/{len(comparisons)} ({payload['classification_exact_rate']:.2%})",
        f"- Normalized description text exact: {description_exact_count}/{len(comparisons)} ({payload['description_exact_rate']:.2%})",
        f"- Gate pass: **{pass_gate}**",
        "",
    ]
    differing = [row for row in comparisons if not row["description_exact"]]
    if differing:
        lines.extend(["## Narrative text differences", ""])
        for row in differing[:20]:
            lines.append(
                f"- game `{row['game_pk']}` PA `{row['at_bat_index']}`: source `{row['source_description']}`; official `{row['official_description']}`; class_exact={row['classification_exact']}"
            )
        lines.append("")
    summary = "\n".join(lines)
    (args.report_dir / "foul_air_official_reconciliation.md").write_text(
        summary, encoding="utf-8"
    )
    print(summary)
    return 0 if pass_gate else 1


if __name__ == "__main__":
    raise SystemExit(main())
