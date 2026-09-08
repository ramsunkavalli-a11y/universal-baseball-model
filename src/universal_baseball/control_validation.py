"""Identity-safe matching used only to validate external control references."""

from __future__ import annotations

import re
import unicodedata
from datetime import date

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


def confirm_name_matches_with_current_roster_entries(
    identity_matches: pl.DataFrame,
    roster_entries: pl.DataFrame,
    *,
    expected_team_id: int,
    as_of_date: date,
) -> pl.DataFrame:
    """Promote a unique name match only with matching current official roster detail."""

    matches = identity_matches.select(list(CONTROL_VALIDATION_MATCH_SCHEMA)).cast(
        CONTROL_VALIDATION_MATCH_SCHEMA, strict=True
    )
    required = {
        "player_id",
        "team_id",
        "parent_org_id",
        "start_date",
        "end_date",
        "source_snapshot_id",
    }
    missing = sorted(required - set(roster_entries.columns))
    if missing:
        raise ValueError(f"roster entries missing identity confirmation fields: {missing}")
    rows: list[dict[str, object]] = []
    for row in matches.iter_rows(named=True):
        if row["match_status"] != "matched_validation_only" or row["player_id"] is None:
            rows.append(row)
            continue
        evidence = roster_entries.filter(
            (pl.col("player_id") == int(row["player_id"]))
            & (pl.col("start_date") <= pl.lit(as_of_date))
            & (pl.col("end_date").is_null() | (pl.col("end_date") >= pl.lit(as_of_date)))
            & (
                (pl.col("team_id") == int(expected_team_id))
                | (pl.col("parent_org_id") == int(expected_team_id))
            )
        )
        if evidence.height:
            row["match_method"] = "unique_name_plus_current_official_roster_entry"
            row["match_status"] = "matched_official_roster_confirmed_name"
        rows.append(row)
    return pl.DataFrame(rows, schema=CONTROL_VALIDATION_MATCH_SCHEMA).sort(
        ["match_status", "reference_player_name"]
    )
