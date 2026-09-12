"""Explainable present-hitter talent output from the frozen Current Talent profile."""

from __future__ import annotations

from math import isfinite
from typing import Mapping

import polars as pl

from universal_baseball.performance_season import ALL_CORE_BINS
from universal_baseball.player_value_batting_runs import MlbBattingReference


TALENT_RATE_BASIS_PA = 600.0
RANKING_MINIMUM_EFFECTIVE_EVENTS = 100.0


def evidence_band(effective_events: object) -> str:
    """Return the fixed Current Talent evidence band used by model diagnostics."""

    value = float(effective_events)
    if not isfinite(value) or value < 0:
        raise ValueError("effective events must be finite and nonnegative")
    if value < 25:
        return "unresolved_lt_25"
    if value < 50:
        return "thin_25_49"
    if value < 100:
        return "limited_50_99"
    if value < 200:
        return "moderate_100_199"
    return "strong_200_plus"


def _component_description(core_bin: str, probability_delta: float) -> str:
    if core_bin == "K":
        return "fewer strikeouts" if probability_delta < 0 else "more strikeouts"
    if core_bin == "BB_HBP":
        return "more walks/HBP" if probability_delta > 0 else "fewer walks/HBP"
    if core_bin == "IFFB":
        return "more infield flies" if probability_delta > 0 else "fewer infield flies"
    direction, contact = core_bin.split("_", maxsplit=1)
    labels = {
        "PULL": "pull",
        "CENTER": "center",
        "OPPO": "opposite-field",
        "GB": "ground-ball",
        "LD": "line-drive",
        "OFFB": "outfield-fly",
        "IFFB": "infield-fly",
    }
    return f"{labels[direction]} {labels[contact]} mix"


def build_present_hitter_talent(
    profile: pl.DataFrame,
    context: pl.DataFrame,
    reference: MlbBattingReference,
    *,
    names: Mapping[int, str] | None = None,
) -> pl.DataFrame:
    """Build a rate-only leaderboard with evidence and component explanations.

    The score contains no playing time, position, defense, age projection, arrival,
    public rank/FV, contract, or replacement runs.
    """

    required_profile = {
        "player_id",
        "core_bin",
        "baseline2_latent_probability",
        "baseline2_effective_core_events",
    }
    missing = sorted(required_profile - set(profile.columns))
    if missing:
        raise ValueError(f"Current Talent profile missing required columns: {missing}")
    if set(profile.get_column("core_bin").unique().to_list()) != set(ALL_CORE_BINS):
        raise ValueError("Current Talent profile does not contain the full core-bin set")

    context_columns = [
        column
        for column in (
            "player_id",
            "as_of_level_group",
            "age_years",
            "prior_mlb_evidence",
            "current_season_effective_core_events",
            "prior_season_effective_core_events",
        )
        if column in context.columns
    ]
    if "player_id" not in context_columns:
        raise ValueError("Current Talent context missing player_id")

    rows: list[dict[str, object]] = []
    for key, group in profile.group_by("player_id"):
        player_id = int(key[0])
        probabilities = {
            str(row["core_bin"]): float(row["baseline2_latent_probability"])
            for row in group.iter_rows(named=True)
        }
        if set(probabilities) != set(ALL_CORE_BINS):
            raise ValueError(f"player {player_id} has an incomplete core profile")
        effective_values = group.get_column("baseline2_effective_core_events").unique()
        if effective_values.len() != 1:
            raise ValueError(f"player {player_id} has inconsistent effective evidence")
        effective = float(effective_values.item())

        contributions: list[tuple[str, float, float]] = []
        for core_bin in ALL_CORE_BINS:
            delta = probabilities[core_bin] - float(reference.reference_probabilities[core_bin])
            contribution = (
                TALENT_RATE_BASIS_PA
                * float(reference.core_event_rate_per_pa)
                * delta
                * float(reference.bin_run_values[core_bin])
            )
            contributions.append((core_bin, delta, contribution))
        batting_runs = sum(value for _, _, value in contributions)
        helpful = max(contributions, key=lambda item: item[2])
        harmful = min(contributions, key=lambda item: item[2])
        rows.append(
            {
                "player_id": player_id,
                "player_name": (names or {}).get(player_id),
                "present_batting_runs_per_600_pa": batting_runs,
                "effective_core_events": effective,
                "reliability": effective / (effective + 100.0),
                "evidence_band": evidence_band(effective),
                "ranking_status": (
                    "ranked" if effective >= RANKING_MINIMUM_EFFECTIVE_EVENTS else "unresolved"
                ),
                "strongest_positive_component": _component_description(helpful[0], helpful[1]),
                "strongest_positive_runs_per_600": helpful[2],
                "largest_negative_component": _component_description(harmful[0], harmful[1]),
                "largest_negative_runs_per_600": harmful[2],
            }
        )

    result = pl.DataFrame(rows).join(
        context.select(context_columns).unique(subset=["player_id"]),
        on="player_id",
        how="left",
    )
    ranked = (
        result.filter(pl.col("ranking_status") == "ranked")
        .sort(
            ["present_batting_runs_per_600_pa", "effective_core_events", "player_id"],
            descending=[True, True, False],
        )
        .with_row_index("present_batting_talent_rank", offset=1)
    )
    unresolved = result.filter(pl.col("ranking_status") == "unresolved").with_columns(
        pl.lit(None, dtype=pl.UInt32).alias("present_batting_talent_rank")
    )
    return pl.concat([ranked, unresolved], how="diagonal_relaxed").sort(
        ["ranking_status", "present_batting_talent_rank", "player_id"],
        descending=[False, False, False],
        nulls_last=True,
    )
