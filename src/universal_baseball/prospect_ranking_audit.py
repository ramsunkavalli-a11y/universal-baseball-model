"""Build an explanation-first audit of prospect ranking extremes."""

from __future__ import annotations

from typing import Any

import polars as pl


def _pct(value: Any) -> str:
    return "missing" if value is None else f"{100.0 * float(value):.0f}%"


def _number(value: Any, digits: int = 1) -> str:
    return "missing" if value is None else f"{float(value):.{digits}f}"


def explain_player(row: dict[str, Any]) -> str:
    """Explain a model result only with its own baseball inputs and outputs."""

    if row.get("model_rank") is None:
        if row.get("comparison_status") == "graduated_to_mlb":
            return (
                "Player debuted before the model checkpoint and is evaluated in the "
                "MLB pool, not the pre-MLB prospect ranking."
            )
        return "No current model match; resolve identity or eligibility before judging."
    age = _number(row.get("age_years"), 0)
    level = row.get("level_tier") or "unknown level"
    player_type = row.get("model_player_type") or "player"
    rate_unit = row.get("skill_rate_unit") or "full workload"
    parts = [
        f"Age {age} at {level}",
        f"{_pct(row.get('model_arrival_probability'))} six-year MLB chance",
        f"{_pct(row.get('model_meaningful_role_probability'))} meaningful-role chance",
        (
            f"{_number(row.get('conditional_skill_war_rate'), 2)} conditional WAR "
            f"per {rate_unit}"
        ),
        f"{_number(row.get('expected_workload'), 0)} expected six-year workload",
        f"{_number(row.get('expected_six_year_war'), 2)} expected WAR",
    ]
    if row.get("rule4_drafted"):
        parts.append(
            "Rule 4 draft evidence present"
            + (
                f" (pick-quality score {_number(row.get('draft_pick_quality'), 2)})"
                if row.get("draft_pick_quality") is not None
                else ""
            )
        )
    if player_type == "hitter":
        parts.append(
            "runs/600: "
            f"bat {_number(row.get('batting_runs_per_600'))}, "
            f"run {_number(row.get('baserunning_runs_per_600'))}, "
            f"field {_number(row.get('defense_runs_per_600'))}, "
            f"position {_number(row.get('positional_runs_per_600'))}"
        )
    else:
        parts.append(
            "pitching runs above average/800 BF: "
            f"{_number(row.get('pitching_runs_above_average_per_800'))}"
        )
        parts.append(
            "projected K/BB/HR rates: "
            f"{_pct(row.get('predicted_so_rate'))}/"
            f"{_pct(row.get('predicted_ubb_rate'))}/"
            f"{_pct(row.get('predicted_hr_rate'))}"
        )
    return "; ".join(parts) + "."


def review_flags(row: dict[str, Any]) -> list[str]:
    """Flag missing or extreme structure without treating public rank as truth."""

    flags: list[str] = []
    if row.get("source_rank") is not None and row.get("player_id") is None:
        flags.append("source_identity_unmatched")
    if row.get("model_rank") is None:
        if row.get("comparison_status") == "graduated_to_mlb":
            return flags
        flags.append("missing_from_model_prospect_pool")
        return flags
    required = (
        "age_years",
        "level_tier",
        "model_arrival_probability",
        "model_meaningful_role_probability",
        "conditional_skill_war_rate",
        "expected_workload",
        "expected_six_year_war",
    )
    if any(row.get(column) is None for column in required):
        flags.append("missing_basic_explanation_input")
    reliability = row.get("skill_reliability")
    if reliability is not None and float(reliability) < 0.20:
        flags.append("thin_skill_evidence")
    evidence = str(row.get("skill_evidence_tier") or "").lower()
    if any(word in evidence for word in ("fallback", "population", "missing")):
        flags.append("fallback_skill_evidence")
    if row.get("age_evidence_source") == "missing_fallback_24":
        flags.append("missing_age_fallback")
    rate = row.get("conditional_skill_war_rate")
    if rate is not None and (float(rate) > 5.0 or float(rate) < -1.5):
        flags.append("extreme_conditional_skill_rate")
    source_rank = row.get("source_rank")
    model_rank = row.get("model_rank")
    if source_rank is not None and model_rank is not None:
        if abs(int(source_rank) - int(model_rank)) > 50:
            flags.append("large_external_rank_difference")
    return flags


def add_explanations(frame: pl.DataFrame) -> pl.DataFrame:
    """Attach deterministic explanation text and review flags."""

    rows = frame.to_dicts()
    return frame.with_columns(
        pl.Series("baseball_explanation", [explain_player(row) for row in rows]),
        pl.Series("review_flags", [review_flags(row) for row in rows]),
    )
