"""Source contracts for Current Talent contact-value challenger 2.

This module is deliberately upstream of model evaluation. It defines only:

- the frozen MLB Stats API terminal-event taxonomy for the nine contact-value
  outcome groups;
- a conservative narrative fallback for historical reusable MiLB PBP; and
- deterministic terminal-PA projection from overlapping historical pitch rows.

Structured official ``event_type`` is authoritative whenever available. The
historical armstjc release does not export the PA-level structured result code,
so its repeated PA result description may be used only through the conservative
fallback below. The historically ambiguous English result labels were settled by
source-only official reconciliation across 2021-22 affiliated levels:

- ``force out`` -> official ``force_out`` -> ``OUT``;
- ``reaches on a fielder's choice out`` -> ``fielders_choice_out`` -> ``OUT``;
- plain ``reaches on a fielder's choice`` -> ``fielders_choice`` -> ``FC_REACH``.

No player scoring, future-outcome fitting, or 2023 evidence is accessed here.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any
import unicodedata

import polars as pl


STRUCTURED_TERMINAL_GROUP: dict[str, str] = {
    "single": "1B",
    "double": "2B",
    "triple": "3B",
    "home_run": "HR",
    "field_error": "ROE",
    "fielders_choice": "FC_REACH",
    "sac_fly": "SF",
    "double_play": "MULTI_OUT",
    "grounded_into_double_play": "MULTI_OUT",
    "sac_fly_double_play": "MULTI_OUT",
    "triple_play": "MULTI_OUT",
    "field_out": "OUT",
    "fielders_choice_out": "OUT",
    "force_out": "OUT",
}
SUPPORTED_TERMINAL_GROUPS = frozenset(STRUCTURED_TERMINAL_GROUP.values())

# These phrases are intentionally narrower than the exploratory audit. A
# description can be used only when it identifies exactly one frozen group.
# Source-only official reconciliation established the distinct FC/force-out
# semantics; regexes therefore keep ``fielder's choice out`` separate from plain
# ``fielder's choice`` rather than relying on pattern order.
_NARRATIVE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("HR", re.compile(r"\b(homers|home run|grand slam)\b", re.I)),
    ("3B", re.compile(r"\btriples\b", re.I)),
    ("2B", re.compile(r"\b(doubles|ground-rule double)\b", re.I)),
    ("1B", re.compile(r"\bsingles\b", re.I)),
    ("MULTI_OUT", re.compile(r"\b(double play|triple play)\b", re.I)),
    ("SF", re.compile(r"\bsacrifice fly\b", re.I)),
    (
        "ROE",
        re.compile(
            r"\breaches(?: first base)? on (?:a |an )?[^.]{0,80}\berror\b",
            re.I,
        ),
    ),
    (
        "FC_REACH",
        re.compile(
            r"\breaches(?: first base)? on (?:a )?fielder'?s choice(?! out)\b",
            re.I,
        ),
    ),
    (
        "OUT",
        re.compile(
            r"\b(grounds out|flies out|flyout|lines out|lineout|pops out|pop out|fouls out|foul out|force out|fielder'?s choice out)\b",
            re.I,
        ),
    ),
)
_BUNT = re.compile(r"\bbunt\b", re.I)
_SPECIAL_UNSUPPORTED = re.compile(
    r"\b(catcher interference|batter interference|fan interference|runner interference)\b",
    re.I,
)
_MOJIBAKE_MARKERS = ("Ã", "Â", "â", "ð", "�")


@dataclass(frozen=True, slots=True)
class NarrativeOutcomeClassification:
    terminal_outcome_group: str | None
    status: str
    matched_groups: tuple[str, ...]


def terminal_group_from_structured_event_type(event_type: str | None) -> str | None:
    """Return the frozen nine-group target for an official PA event type.

    Unsupported/special PA outcomes return ``None``. Callers that require a
    supported contact target must fail closed or exclude them symmetrically.
    """

    if event_type is None:
        return None
    key = str(event_type).strip()
    if not key:
        return None
    return STRUCTURED_TERMINAL_GROUP.get(key)


def classify_terminal_result_description(
    description: str | None,
) -> NarrativeOutcomeClassification:
    """Conservatively classify one historical PA result description.

    Only source-reconciled lexical distinctions are accepted. Multiple frozen-
    group matches remain unresolved rather than being resolved by pattern order.
    """

    text = "" if description is None else str(description).strip()
    if not text:
        return NarrativeOutcomeClassification(None, "unsupported_blank_description", ())
    if _BUNT.search(text):
        return NarrativeOutcomeClassification(None, "unsupported_bunt", ())
    if _SPECIAL_UNSUPPORTED.search(text):
        return NarrativeOutcomeClassification(None, "unsupported_special_result", ())

    matched = tuple(
        group for group, pattern in _NARRATIVE_PATTERNS if pattern.search(text)
    )
    distinct = tuple(dict.fromkeys(matched))
    if len(distinct) == 1:
        return NarrativeOutcomeClassification(
            distinct[0], "supported_narrative_fallback", distinct
        )
    if len(distinct) > 1:
        return NarrativeOutcomeClassification(None, "ambiguous_narrative_groups", distinct)
    return NarrativeOutcomeClassification(None, "unsupported_narrative_result", ())


def _integer_expr(column: str, alias: str) -> pl.Expr:
    numeric = pl.col(column).cast(pl.Float64, strict=False)
    return (
        pl.when(numeric.is_not_null() & (numeric == numeric.floor()))
        .then(numeric.cast(pl.Int64, strict=False))
        .otherwise(None)
        .alias(alias)
    )


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def _repair_utf8_mojibake(value: str) -> str:
    """Repair narrow UTF-8-as-Latin-1 mojibake only when evidence improves.

    Historical release overlap occasionally contains the same PA narrative once
    as proper Unicode and once with UTF-8 bytes decoded as Latin-1 (for example
    ``GonzÃ¡lez`` vs ``González``). This helper is used only for duplicate-source
    identity comparison; substantive narrative differences still fail closed.
    """

    repaired = value
    for _ in range(2):
        current_score = sum(repaired.count(marker) for marker in _MOJIBAKE_MARKERS)
        if current_score == 0:
            break
        try:
            candidate = repaired.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            break
        candidate_score = sum(candidate.count(marker) for marker in _MOJIBAKE_MARKERS)
        if candidate_score >= current_score:
            break
        repaired = candidate
    return unicodedata.normalize("NFC", repaired)


def _description_identity(value: str) -> str:
    """Normalize whitespace/encoding artifacts for duplicate-source comparison."""

    return _repair_utf8_mojibake(" ".join(value.split()))


def project_terminal_pa_descriptions(
    raw_pbp_rows: pl.DataFrame,
    *,
    game_type: str = "R",
) -> pl.DataFrame:
    """Project overlapping reusable PBP to one terminal description per PA.

    The terminal pitch is the maximum structured ``pitch_number`` within
    ``game_pk + at_bat_number``. Exact duplicated release rows therefore do not
    become extra events. Formatting-only whitespace differences and a narrow
    UTF-8-as-Latin-1 mojibake duplicate are treated as the same repeated
    description. If terminal rows disagree on their nonblank PA result
    description after that normalization, projection fails instead of choosing
    by filename, retrieval time, or row order.
    """

    required = {"game_pk", "at_bat_number", "pitch_number", "game_type"}
    missing = sorted(required - set(raw_pbp_rows.columns))
    if missing:
        raise ValueError(f"historical terminal-PA source missing fields: {missing}")
    description_columns = [
        column for column in ("des", "description") if column in raw_pbp_rows.columns
    ]
    if not description_columns:
        raise ValueError("historical terminal-PA source lacks des/description")

    projected = raw_pbp_rows.select(
        _integer_expr("game_pk", "game_pk"),
        _integer_expr("at_bat_number", "at_bat_index"),
        _integer_expr("pitch_number", "pitch_number"),
        pl.col("game_type").cast(pl.String),
        *[pl.col(column).cast(pl.String) for column in description_columns],
    ).drop_nulls(["game_pk", "at_bat_index", "pitch_number"])
    projected = projected.filter(pl.col("game_type") == str(game_type))
    if projected.is_empty():
        return pl.DataFrame(
            schema={
                "game_pk": pl.Int64,
                "at_bat_index": pl.Int64,
                "terminal_pitch_number": pl.Int64,
                "pa_description": pl.String,
                "raw_terminal_row_count": pl.Int64,
                "terminal_description_variant_count": pl.Int64,
            }
        )

    terminal = (
        projected.with_columns(
            pl.col("pitch_number")
            .max()
            .over(["game_pk", "at_bat_index"])
            .alias("terminal_pitch_number")
        )
        .filter(pl.col("pitch_number") == pl.col("terminal_pitch_number"))
    )

    rows: list[dict[str, Any]] = []
    for group in terminal.partition_by(["game_pk", "at_bat_index"], maintain_order=False):
        first = group.row(0, named=True)
        descriptions_by_identity: dict[str, str] = {}
        for row in group.iter_rows(named=True):
            selected = None
            for column in description_columns:
                selected = _text(row.get(column))
                if selected is not None:
                    break
            if selected is not None:
                identity = _description_identity(selected)
                descriptions_by_identity.setdefault(identity, selected)
        descriptions = list(descriptions_by_identity.values())
        if len(descriptions) > 1:
            raise ValueError(
                "historical terminal PA has conflicting result descriptions: "
                f"game_pk={int(first['game_pk'])}, at_bat_index={int(first['at_bat_index'])}, "
                f"descriptions={descriptions[:5]}"
            )
        rows.append(
            {
                "game_pk": int(first["game_pk"]),
                "at_bat_index": int(first["at_bat_index"]),
                "terminal_pitch_number": int(first["terminal_pitch_number"]),
                "pa_description": descriptions[0] if descriptions else None,
                "raw_terminal_row_count": int(group.height),
                "terminal_description_variant_count": len(descriptions),
            }
        )

    return pl.DataFrame(rows).with_columns(
        pl.col("game_pk").cast(pl.Int64),
        pl.col("at_bat_index").cast(pl.Int64),
        pl.col("terminal_pitch_number").cast(pl.Int64),
        pl.col("pa_description").cast(pl.String),
        pl.col("raw_terminal_row_count").cast(pl.Int64),
        pl.col("terminal_description_variant_count").cast(pl.Int64),
    ).sort(["game_pk", "at_bat_index"])


def attach_narrative_terminal_groups(
    terminal_pas: pl.DataFrame,
) -> pl.DataFrame:
    """Attach conservative narrative-group/status fields to terminal PAs."""

    required = {"game_pk", "at_bat_index", "terminal_pitch_number", "pa_description"}
    missing = sorted(required - set(terminal_pas.columns))
    if missing:
        raise ValueError(f"terminal PA projection missing fields: {missing}")

    rows: list[dict[str, Any]] = []
    for row in terminal_pas.iter_rows(named=True):
        classification = classify_terminal_result_description(row.get("pa_description"))
        rows.append(
            {
                **row,
                "terminal_outcome_group": classification.terminal_outcome_group,
                "terminal_outcome_status": classification.status,
                "terminal_outcome_matches": ",".join(classification.matched_groups),
            }
        )
    if not rows:
        return terminal_pas.with_columns(
            pl.lit(None, dtype=pl.String).alias("terminal_outcome_group"),
            pl.lit(None, dtype=pl.String).alias("terminal_outcome_status"),
            pl.lit(None, dtype=pl.String).alias("terminal_outcome_matches"),
        )
    return pl.DataFrame(rows).with_columns(
        pl.col("terminal_outcome_group").cast(pl.String),
        pl.col("terminal_outcome_status").cast(pl.String),
        pl.col("terminal_outcome_matches").cast(pl.String),
    )
