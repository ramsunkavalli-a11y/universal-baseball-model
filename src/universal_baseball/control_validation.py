"""Identity-safe matching used only to validate external control references."""

from __future__ import annotations

import re
import unicodedata

import polars as pl


CONTROL_VALIDATION_MATCH_SCHEMA: dict[str, pl.DataType] = {
    "fangraphs_id": pl.String,
    "reference_player_name": pl.String,
    "player_id": pl.Int64,
    "statsapi_player_name": pl.String,
    "match_method": pl.String,
    "match_status": pl.String,
}


def _normalized_name(value: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", ascii_name.lower())


def match_control_reference_players(
    references: pl.DataFrame,
    statsapi_candidates: pl.DataFrame,
    fangraphs_crosswalk: pl.DataFrame,
) -> pl.DataFrame:
    """Use stable IDs first and unique exact normalized names only for validation."""

    for label, frame, required in (
        ("references", references, {"fangraphs_id", "player_name"}),
        ("statsapi_candidates", statsapi_candidates, {"player_id", "player_name"}),
        (
            "fangraphs_crosswalk",
            fangraphs_crosswalk,
            {"fangraphs_id", "player_id", "crosswalk_status"},
        ),
    ):
        missing = sorted(required - set(frame.columns))
        if missing:
            raise ValueError(f"{label} missing columns: {missing}")
    candidates = {
        int(row["player_id"]): str(row["player_name"])
        for row in statsapi_candidates.select("player_id", "player_name").iter_rows(named=True)
    }
    by_name: dict[str, list[tuple[int, str]]] = {}
    for player_id, name in candidates.items():
        by_name.setdefault(_normalized_name(name), []).append((player_id, name))
    crosswalk = {
        str(row["fangraphs_id"]): row
        for row in fangraphs_crosswalk.iter_rows(named=True)
    }
    rows: list[dict[str, object]] = []
    for reference in references.select("fangraphs_id", "player_name").iter_rows(named=True):
        fangraphs_id = str(reference["fangraphs_id"])
        reference_name = str(reference["player_name"])
        link = crosswalk.get(fangraphs_id)
        linked_id = (
            int(link["player_id"])
            if link and link["crosswalk_status"] == "matched_unique" and link["player_id"] is not None
            else None
        )
        if linked_id is not None and linked_id in candidates:
            player_id = linked_id
            candidate_name = candidates[linked_id]
            method = "chadwick_fangraphs_to_mlbam"
            status = "matched_stable_id"
        elif linked_id is not None:
            player_id = linked_id
            candidate_name = ""
            method = "chadwick_fangraphs_to_mlbam"
            status = "stable_id_outside_statsapi_candidates"
        else:
            name_matches = by_name.get(_normalized_name(reference_name), [])
            if len(name_matches) == 1:
                player_id, candidate_name = name_matches[0]
                method = "unique_normalized_name_validation_only"
                status = "matched_validation_only"
            elif len(name_matches) > 1:
                player_id = None
                candidate_name = ""
                method = "unique_normalized_name_validation_only"
                status = "ambiguous_name"
            else:
                player_id = None
                candidate_name = ""
                method = "none"
                status = "unmatched"
        rows.append(
            {
                "fangraphs_id": fangraphs_id,
                "reference_player_name": reference_name,
                "player_id": player_id,
                "statsapi_player_name": candidate_name,
                "match_method": method,
                "match_status": status,
            }
        )
    return pl.DataFrame(rows, schema=CONTROL_VALIDATION_MATCH_SCHEMA).sort(
        ["match_status", "reference_player_name"]
    )
