"""Deterministic terminal-PA labels for the Hitter v2 contextual source gate.

This module is source-only. It contains no estimator, forecast target, run value,
candidate score, or protected-season access.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

import polars as pl

from universal_baseball.current_talent_contact_value_source import (
    classify_terminal_result_description,
)
from universal_baseball.hitter_v2_outcomes import MLB_EVENT_OUTCOME, TERMINAL_OUTCOMES


_INTENTIONAL_WALK = re.compile(
    r"\b(intentional(?:ly)? walk(?:s|ed)?|walk(?:s|ed)? intentionally)\b", re.I
)
_WALK = re.compile(r"\bwalks?\b", re.I)
_HBP = re.compile(r"\b(hit by pitch|hits? .* with (?:a )?pitch)\b", re.I)
_STRIKEOUT = re.compile(
    r"\b(strikes? out|strikeout|called out on strikes)\b", re.I
)
_BUNT_OR_INTERFERENCE = re.compile(
    r"\b(bunt|catcher interference|batter interference|fan interference|runner interference)\b",
    re.I,
)


@dataclass(frozen=True, slots=True)
class TerminalOutcomeLabel:
    outcome: str | None
    status: str
    authority: str


def classify_terminal_pa(
    *, event_type: str | None, description: str | None
) -> TerminalOutcomeLabel:
    """Classify one PA from structured authority, then conservative narrative.

    A nonblank but unsupported structured value does not override a usable narrative;
    this accommodates the affiliated PBP files whose ``events`` field is sparsely
    populated. Conflicting narrative groups remain unresolved through the existing
    certified contact classifier.
    """

    event = "" if event_type is None else str(event_type).strip()
    text = "" if description is None else str(description).strip()
    if event == "field_error" and re.search(r"\binterference error\b", text, re.I):
        return TerminalOutcomeLabel(
            "SH_OR_SPECIAL", "supported_structured_interference_error", "structured_event"
        )
    if event:
        structured = MLB_EVENT_OUTCOME.get(event)
        if structured is not None:
            return TerminalOutcomeLabel(
                structured, "supported_structured_event", "structured_event"
            )

    if not text:
        return TerminalOutcomeLabel(None, "unsupported_blank_description", "none")
    if _BUNT_OR_INTERFERENCE.search(text):
        return TerminalOutcomeLabel(
            "SH_OR_SPECIAL", "supported_narrative_special", "narrative"
        )
    if _INTENTIONAL_WALK.search(text):
        return TerminalOutcomeLabel("IBB", "supported_narrative_ibb", "narrative")
    if _WALK.search(text):
        return TerminalOutcomeLabel("UBB", "supported_narrative_ubb", "narrative")
    if _HBP.search(text):
        return TerminalOutcomeLabel("HBP", "supported_narrative_hbp", "narrative")
    if _STRIKEOUT.search(text):
        return TerminalOutcomeLabel("K", "supported_narrative_k", "narrative")

    contact = classify_terminal_result_description(text)
    if contact.terminal_outcome_group is None:
        return TerminalOutcomeLabel(None, contact.status, "narrative")
    outcome = "OTHER_OUT" if contact.terminal_outcome_group == "OUT" else (
        contact.terminal_outcome_group
    )
    return TerminalOutcomeLabel(outcome, contact.status, "narrative")


def attach_terminal_pa_labels(
    terminal_pas: pl.DataFrame,
    *,
    event_column: str | None = None,
    description_column: str = "pa_description",
) -> pl.DataFrame:
    """Attach exactly one deterministic label record to every input terminal PA."""

    required = {"game_pk", "at_bat_index", description_column}
    if event_column is not None:
        required.add(event_column)
    missing = sorted(required - set(terminal_pas.columns))
    if missing:
        raise ValueError(f"terminal label source missing fields: {missing}")
    duplicate = (
        terminal_pas.group_by(["game_pk", "at_bat_index"])
        .len()
        .filter(pl.col("len") != 1)
    )
    if not duplicate.is_empty():
        raise ValueError("terminal label source is not unique at game/at-bat grain")

    rows: list[dict[str, Any]] = []
    for row in terminal_pas.iter_rows(named=True):
        label = classify_terminal_pa(
            event_type=row.get(event_column) if event_column is not None else None,
            description=row.get(description_column),
        )
        rows.append(
            {
                **row,
                "canonical_outcome": label.outcome,
                "label_status": label.status,
                "label_authority": label.authority,
            }
        )
    if not rows:
        return terminal_pas.with_columns(
            pl.lit(None, dtype=pl.String).alias("canonical_outcome"),
            pl.lit(None, dtype=pl.String).alias("label_status"),
            pl.lit(None, dtype=pl.String).alias("label_authority"),
        )
    result = pl.DataFrame(rows).with_columns(
        pl.col("canonical_outcome").cast(pl.String),
        pl.col("label_status").cast(pl.String),
        pl.col("label_authority").cast(pl.String),
    )
    unsupported = sorted(
        set(result["canonical_outcome"].drop_nulls().unique().to_list())
        - set(TERMINAL_OUTCOMES)
    )
    if unsupported:
        raise ValueError(f"terminal label source produced unsupported outcomes: {unsupported}")
    return result


def attach_structured_terminal_event(
    raw_pbp: pl.DataFrame,
    terminal_pas: pl.DataFrame,
    *,
    game_type: str = "R",
) -> pl.DataFrame:
    """Attach a conflict-screened structured event from the exact terminal pitch."""

    raw_required = {
        "game_pk",
        "at_bat_number",
        "pitch_number",
        "game_type",
        "events",
    }
    terminal_required = {"game_pk", "at_bat_index", "terminal_pitch_number"}
    missing_raw = sorted(raw_required - set(raw_pbp.columns))
    missing_terminal = sorted(terminal_required - set(terminal_pas.columns))
    if missing_raw:
        raise ValueError(f"raw structured-event source missing fields: {missing_raw}")
    if missing_terminal:
        raise ValueError(f"terminal PA source missing fields: {missing_terminal}")

    numeric_game = pl.col("game_pk").cast(pl.Float64, strict=False)
    numeric_ab = pl.col("at_bat_number").cast(pl.Float64, strict=False)
    numeric_pitch = pl.col("pitch_number").cast(pl.Float64, strict=False)
    raw = raw_pbp.select(
        numeric_game.cast(pl.Int64, strict=False).alias("game_pk"),
        numeric_ab.cast(pl.Int64, strict=False).alias("at_bat_index"),
        numeric_pitch.cast(pl.Int64, strict=False).alias("pitch_number"),
        pl.col("game_type").cast(pl.String),
        pl.col("events").cast(pl.String).str.strip_chars().alias("structured_event"),
    ).filter(pl.col("game_type") == game_type)
    exact_terminal = raw.join(
        terminal_pas.select(
            "game_pk", "at_bat_index", "terminal_pitch_number"
        ).unique(),
        left_on=["game_pk", "at_bat_index", "pitch_number"],
        right_on=["game_pk", "at_bat_index", "terminal_pitch_number"],
        how="inner",
        validate="m:1",
    ).with_columns(
        pl.when(pl.col("structured_event") == "")
        .then(pl.lit(None, dtype=pl.String))
        .otherwise(pl.col("structured_event"))
        .alias("structured_event")
    )
    authority = exact_terminal.group_by(["game_pk", "at_bat_index"]).agg(
        pl.col("structured_event").drop_nulls().n_unique().alias("event_variant_count"),
        pl.col("structured_event").drop_nulls().first().alias("structured_event"),
    ).with_columns(
        pl.when(pl.col("event_variant_count") <= 1)
        .then(pl.col("structured_event"))
        .otherwise(pl.lit(None, dtype=pl.String))
        .alias("structured_event"),
        (pl.col("event_variant_count") > 1).alias("structured_event_conflict"),
    )
    return terminal_pas.join(
        authority, on=["game_pk", "at_bat_index"], how="left", validate="1:1"
    ).with_columns(
        pl.col("event_variant_count").fill_null(0),
        pl.col("structured_event_conflict").fill_null(False),
    )


def reconcile_terminal_pa_labels(
    labeled_sidecar: pl.DataFrame,
    player_games: pl.DataFrame,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Fail closed unless direct PA labels equal all certified player-game totals."""

    label_required = {
        "season",
        "game_pk",
        "at_bat_index",
        "player_id",
        "canonical_outcome",
        "matchup_ready",
        "modeling_join_ready",
    }
    game_required = {
        "season",
        "game_id",
        "player_id",
        "modeling_eligible",
        "accepted_terminal_pa",
        *TERMINAL_OUTCOMES,
    }
    missing_labels = sorted(label_required - set(labeled_sidecar.columns))
    missing_games = sorted(game_required - set(player_games.columns))
    if missing_labels:
        raise ValueError(f"labeled sidecar missing fields: {missing_labels}")
    if missing_games:
        raise ValueError(f"player-game authority missing fields: {missing_games}")
    duplicate = (
        labeled_sidecar.group_by(["season", "game_pk", "at_bat_index"])
        .len()
        .filter(pl.col("len") != 1)
    )
    if not duplicate.is_empty():
        raise ValueError("labeled sidecar is not unique at canonical PA grain")

    keys = ["season", "game_pk", "player_id"]
    direct = labeled_sidecar.group_by(keys).agg(
        pl.len().alias("sidecar_pa"),
        pl.col("canonical_outcome").is_not_null().sum().alias("direct_labeled_pa"),
        pl.col("matchup_ready").sum().alias("matchup_ready_pa"),
        pl.col("modeling_join_ready").sum().alias("prior_modeling_join_ready_pa"),
        *[
            (pl.col("canonical_outcome") == outcome)
            .sum()
            .alias(f"direct_{outcome}")
            for outcome in TERMINAL_OUTCOMES
        ],
    )
    authority = player_games.select(
        "season",
        pl.col("game_id").alias("game_pk"),
        "player_id",
        "modeling_eligible",
        "accepted_terminal_pa",
        *TERMINAL_OUTCOMES,
    )
    reconciliation = direct.join(
        authority, on=keys, how="full", coalesce=True, validate="1:1"
    ).with_columns(
        pl.all_horizontal(
            [
                pl.col(f"direct_{outcome}").fill_null(-1)
                == pl.col(outcome).fill_null(-2)
                for outcome in TERMINAL_OUTCOMES
            ]
        ).alias("all_outcome_counts_exact")
    )
    ready = (
        pl.col("modeling_eligible").fill_null(False)
        & (pl.col("sidecar_pa") == pl.col("accepted_terminal_pa"))
        & (pl.col("direct_labeled_pa") == pl.col("sidecar_pa"))
        & pl.col("all_outcome_counts_exact")
        & (pl.col("matchup_ready_pa") == pl.col("sidecar_pa"))
        & (pl.col("prior_modeling_join_ready_pa") == pl.col("sidecar_pa"))
    )
    reconciliation = reconciliation.with_columns(
        ready.alias("context_label_player_game_ready"),
        pl.when(ready)
        .then(pl.lit("exact_direct_labels"))
        .when(pl.col("sidecar_pa").is_null())
        .then(pl.lit("player_game_without_sidecar"))
        .when(pl.col("accepted_terminal_pa").is_null())
        .then(pl.lit("sidecar_without_player_game_authority"))
        .when(pl.col("direct_labeled_pa") != pl.col("sidecar_pa"))
        .then(pl.lit("unresolved_direct_label"))
        .when(~pl.col("all_outcome_counts_exact"))
        .then(pl.lit("direct_outcome_count_mismatch"))
        .otherwise(pl.lit("prior_source_or_matchup_not_ready"))
        .alias("context_label_reconciliation_status"),
    ).sort(keys)

    attached = labeled_sidecar.join(
        reconciliation.select(
            *keys,
            "context_label_player_game_ready",
            "context_label_reconciliation_status",
        ),
        on=keys,
        how="left",
        validate="m:1",
    ).with_columns(
        pl.col("context_label_player_game_ready").fill_null(False),
        (
            pl.col("context_label_player_game_ready").fill_null(False)
            & pl.col("canonical_outcome").is_not_null()
        ).alias("context_label_ready"),
    )
    return attached, reconciliation
