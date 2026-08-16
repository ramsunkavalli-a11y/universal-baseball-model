"""Certified exception-only identity corrections for historical player-game evidence.

Reusable historical player-game rows remain the default Current Talent outcome
and contact-control source. A row may be remapped only when a separately audited
official game boxscore establishes a unique participant replacement and the
source row still matches the exact evidence vector that was certified.

This module deliberately contains a tiny explicit registry rather than a generic
fuzzy matcher. If a source release changes, the pinned game date/outcome vector
must still match or materialization fails closed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import polars as pl

from universal_baseball.current_talent_milb_evidence import OUTCOME_FIELDS


IDENTITY_CORRECTION_POLICY = "certified_official_boxscore_identity_remap_v1"


@dataclass(frozen=True)
class HistoricalPlayerGameIdentityCorrection:
    season: int
    league_id: int
    game_id: int
    source_player_id: int
    corrected_player_id: int
    game_date: str
    expected_outcome_vector: tuple[int, ...]
    evidence: str

    def expected_outcomes(self) -> dict[str, int]:
        if len(self.expected_outcome_vector) != len(OUTCOME_FIELDS):
            raise ValueError("historical identity correction outcome vector has wrong length")
        return dict(zip(OUTCOME_FIELDS, self.expected_outcome_vector, strict=True))


HISTORICAL_PLAYER_GAME_IDENTITY_CORRECTIONS: tuple[
    HistoricalPlayerGameIdentityCorrection, ...
] = (
    HistoricalPlayerGameIdentityCorrection(
        season=2021,
        league_id=130,
        game_id=660171,
        source_player_id=703595,
        corrected_player_id=682770,
        game_date="2021-09-23",
        expected_outcome_vector=(4, 3, 0, 0, 2, 0, 1, 0),
        evidence=(
            "2021 DSL LAD Bautista official boxscore audit: source participant 703595 is absent; "
            "Victor Diaz 682770 is the unique same-game batter matching team 611, batting order "
            "500, DH, and the complete PA/AB/BB/HBP/SO/SF/SH/CI vector. Team-611 outcome totals "
            "match official boxscores in all 57 audited games. The reusable source also contains "
            "an empty 682770 roster placeholder in game 660171; that placeholder may be absorbed "
            "only while it remains null-outcome and zero-contact evidence."
        ),
    ),
)


def _empty_evidence() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "season": pl.Int64,
            "league_id": pl.Int64,
            "game_id": pl.Int64,
            "source_player_id": pl.Int64,
            "corrected_player_id": pl.Int64,
            "game_date": pl.Date,
            **{field: pl.Int64 for field in OUTCOME_FIELDS},
            "policy": pl.String,
            "evidence": pl.String,
        }
    )


def _validate_unique_player_game(frame: pl.DataFrame, label: str) -> None:
    required = {"game_id", "player_id"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{label} missing player-game identity fields: {missing}")
    duplicates = frame.group_by(["game_id", "player_id"]).len().filter(pl.col("len") > 1)
    if not duplicates.is_empty():
        raise ValueError(f"{label} contains duplicate game/player keys after identity correction")


def _date_iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip()
    return text[:10] if text else None


def _empty_target_placeholder_is_safe(
    target_outcome: pl.DataFrame,
    target_control: pl.DataFrame,
    *,
    correction: HistoricalPlayerGameIdentityCorrection,
) -> bool:
    """Return true only for the audited null-outcome/zero-contact target placeholder."""

    if target_outcome.height != 1 or target_control.height != 1:
        return False
    outcome_row = target_outcome.row(0, named=True)
    control_row = target_control.row(0, named=True)
    if int(outcome_row.get("league_id") or -1) != correction.league_id:
        return False
    if _date_iso(outcome_row.get("game_date")) != correction.game_date:
        return False
    if any(outcome_row.get(field) is not None for field in OUTCOME_FIELDS):
        return False
    if "expected_contact_count" not in control_row:
        return False
    if int(control_row.get("expected_contact_count") or 0) != 0:
        return False
    for field in ("batting_PA", "batting_AB", "batting_SO", "batting_SF", "batting_SH"):
        if field in control_row and control_row.get(field) is not None:
            return False
    if "league_id" in control_row and control_row.get("league_id") is not None:
        if int(control_row["league_id"]) != correction.league_id:
            return False
    if "game_date" in control_row and control_row.get("game_date") is not None:
        if _date_iso(control_row["game_date"]) != correction.game_date:
            return False
    return True


def apply_historical_player_game_identity_corrections(
    outcomes: pl.DataFrame,
    controls: pl.DataFrame,
    *,
    season: int,
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, dict[str, Any]]:
    """Apply only pinned, fully validated player-game identity remaps.

    The outcome row is the semantic guard because it carries the complete
    certified batting vector. The matching resolved contact-control row is then
    remapped with the same game/player key so downstream contact residual logic
    either agrees with the source PBP participant or triggers existing official
    sequence authority.

    A target-key collision still fails closed unless the existing target is the
    separately audited empty roster placeholder: all outcome fields null and
    expected contacts exactly zero. In that one case the empty target row is
    removed before the substantive source evidence is remapped to the corrected
    player ID.

    Corrections are applicable only when their actual league is present in the
    supplied outcome slice. A 2021 DSL exception therefore cannot make a 2021
    AAA/AA/High-A/Single-A materialization expect DSL evidence that is outside
    that level's input.
    """

    outcome_required = {
        "game_id",
        "player_id",
        "league_id",
        "game_date",
        *OUTCOME_FIELDS,
    }
    control_required = {"game_id", "player_id", "expected_contact_count"}
    missing_outcomes = sorted(outcome_required - set(outcomes.columns))
    missing_controls = sorted(control_required - set(controls.columns))
    if missing_outcomes:
        raise ValueError(f"outcomes missing identity-correction fields: {missing_outcomes}")
    if missing_controls:
        raise ValueError(f"controls missing identity-correction fields: {missing_controls}")

    corrected_outcomes = outcomes
    corrected_controls = controls
    evidence_rows: list[dict[str, Any]] = []
    absorbed_empty_target_placeholder_count = 0
    season_registered = [
        correction
        for correction in HISTORICAL_PLAYER_GAME_IDENTITY_CORRECTIONS
        if correction.season == int(season)
    ]
    observed_league_ids = {
        int(value)
        for value in corrected_outcomes.get_column("league_id").drop_nulls().unique().to_list()
    }
    applicable = [
        correction
        for correction in season_registered
        if correction.league_id in observed_league_ids
    ]

    for correction in applicable:
        source_outcome = corrected_outcomes.filter(
            (pl.col("game_id") == correction.game_id)
            & (pl.col("league_id") == correction.league_id)
            & (pl.col("player_id") == correction.source_player_id)
        )
        if source_outcome.height != 1:
            raise ValueError(
                "certified identity correction expected exactly one source outcome row: "
                f"season={season} game={correction.game_id} league={correction.league_id} "
                f"player={correction.source_player_id}, rows={source_outcome.height}"
            )
        source_row = source_outcome.row(0, named=True)
        if _date_iso(source_row["game_date"]) != correction.game_date:
            raise ValueError(
                "certified identity correction source game date drifted: "
                f"game={correction.game_id} observed={source_row['game_date']} "
                f"expected={correction.game_date}"
            )
        expected = correction.expected_outcomes()
        observed = {field: int(source_row[field] or 0) for field in OUTCOME_FIELDS}
        if observed != expected:
            raise ValueError(
                "certified identity correction source outcome vector drifted: "
                f"game={correction.game_id} player={correction.source_player_id} "
                f"observed={observed} expected={expected}"
            )

        source_control = corrected_controls.filter(
            (pl.col("game_id") == correction.game_id)
            & (pl.col("player_id") == correction.source_player_id)
        )
        if source_control.height != 1:
            raise ValueError(
                "certified identity correction expected exactly one source contact-control row: "
                f"game={correction.game_id} player={correction.source_player_id}, "
                f"rows={source_control.height}"
            )

        target_outcome = corrected_outcomes.filter(
            (pl.col("game_id") == correction.game_id)
            & (pl.col("player_id") == correction.corrected_player_id)
        )
        target_control = corrected_controls.filter(
            (pl.col("game_id") == correction.game_id)
            & (pl.col("player_id") == correction.corrected_player_id)
        )
        if not target_outcome.is_empty() or not target_control.is_empty():
            if not _empty_target_placeholder_is_safe(
                target_outcome,
                target_control,
                correction=correction,
            ):
                raise ValueError(
                    "certified identity correction would collide with non-empty or ambiguous target evidence: "
                    f"game={correction.game_id} player={correction.corrected_player_id}"
                )
            target_predicate = (
                (pl.col("game_id") == correction.game_id)
                & (pl.col("player_id") == correction.corrected_player_id)
            )
            corrected_outcomes = corrected_outcomes.filter(~target_predicate)
            corrected_controls = corrected_controls.filter(~target_predicate)
            absorbed_empty_target_placeholder_count += 1

        outcome_predicate = (
            (pl.col("game_id") == correction.game_id)
            & (pl.col("league_id") == correction.league_id)
            & (pl.col("player_id") == correction.source_player_id)
        )
        control_predicate = (
            (pl.col("game_id") == correction.game_id)
            & (pl.col("player_id") == correction.source_player_id)
        )
        corrected_outcomes = corrected_outcomes.with_columns(
            pl.when(outcome_predicate)
            .then(pl.lit(correction.corrected_player_id))
            .otherwise(pl.col("player_id"))
            .cast(pl.Int64)
            .alias("player_id")
        )
        corrected_controls = corrected_controls.with_columns(
            pl.when(control_predicate)
            .then(pl.lit(correction.corrected_player_id))
            .otherwise(pl.col("player_id"))
            .cast(pl.Int64)
            .alias("player_id")
        )
        evidence_rows.append(
            {
                "season": correction.season,
                "league_id": correction.league_id,
                "game_id": correction.game_id,
                "source_player_id": correction.source_player_id,
                "corrected_player_id": correction.corrected_player_id,
                "game_date": date.fromisoformat(correction.game_date),
                **expected,
                "policy": IDENTITY_CORRECTION_POLICY,
                "evidence": correction.evidence,
            }
        )

    _validate_unique_player_game(corrected_outcomes, "corrected outcomes")
    _validate_unique_player_game(corrected_controls, "corrected contact controls")
    evidence = (
        pl.DataFrame(evidence_rows, schema=_empty_evidence().schema, strict=False)
        if evidence_rows
        else _empty_evidence()
    )
    return corrected_outcomes, corrected_controls, evidence, {
        "policy": IDENTITY_CORRECTION_POLICY,
        "registered_correction_count_for_season": len(season_registered),
        "applicable_correction_count": len(applicable),
        "observed_league_ids": sorted(observed_league_ids),
        "applied_correction_count": int(evidence.height),
        "absorbed_empty_target_placeholder_count": absorbed_empty_target_placeholder_count,
        "corrected_game_count": int(evidence.get_column("game_id").n_unique()) if not evidence.is_empty() else 0,
        "corrected_source_player_count": int(evidence.get_column("source_player_id").n_unique()) if not evidence.is_empty() else 0,
        "fail_closed_on_source_drift": True,
    }
