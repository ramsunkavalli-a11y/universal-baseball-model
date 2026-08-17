"""Simple Current Talent baselines on the MLB-anchored latent profile scale.

This module intentionally stops before Projection, playing time, WAR, or ranking.
It implements the first two results-only Current Talent baselines from the frozen
validation contract:

- Baseline 0: leave-one-out age + current-level population prior, with no player's
  own recent performance allowed to inform their prior.
- Baseline 1: recency-weighted player evidence translated to the MLB reporting
  scale and empirically shrunk toward Baseline 0.

Environment translation is applied before multi-level player evidence is
aggregated. That ordering matters: applying one level adjustment after a player's
AAA/AA/etc. evidence has already been pooled is not compositionally valid.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from math import exp, floor, log
from typing import Any

import polars as pl

from universal_baseball.current_talent_evidence import (
    EvidenceWindow,
    PLAYER_GAME_KEY,
    validate_player_game_evidence,
)
from universal_baseball.current_talent_translation import DEFAULT_CLR_PSEUDOCOUNT
from universal_baseball.performance_season import ALL_CORE_BINS


BASELINE0_METHOD = "loo_age_level_population_prior_v1"
BASELINE1_METHOD = "translated_recency_empirical_bayes_v1"
DEFAULT_AGE_BAND_WIDTH_YEARS = 2.0
DEFAULT_MIN_AGE_LEVEL_PEERS = 12
DEFAULT_PRIOR_STRENGTH_CORE_EVENTS = 100.0


@dataclass(frozen=True, slots=True)
class BaselineProfiles:
    """Latent MLB-scale component probabilities for Baseline 0 and Baseline 1."""

    profile: pl.DataFrame
    metrics: dict[str, Any]


def _require_columns(frame: pl.DataFrame, required: set[str], label: str) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{label} missing fields: {missing}")


def _softmax(values: list[float]) -> list[float]:
    maximum = max(values)
    exponentials = [exp(value - maximum) for value in values]
    denominator = sum(exponentials)
    if denominator <= 0:
        raise ValueError("softmax denominator must be positive")
    return [value / denominator for value in exponentials]


def _clr(probabilities: list[float]) -> list[float]:
    if any(value <= 0 for value in probabilities):
        raise ValueError("CLR probabilities must all be positive")
    logs = [log(value) for value in probabilities]
    mean_log = sum(logs) / len(logs)
    return [value - mean_log for value in logs]


def _translation_lookup(offsets: pl.DataFrame) -> dict[str, dict[str, float]]:
    required = {"level_group", "core_bin", "clr_environment_effect"}
    _require_columns(offsets, required, "translation offsets")
    duplicate = offsets.group_by(["level_group", "core_bin"]).len().filter(pl.col("len") != 1)
    if not duplicate.is_empty():
        raise ValueError("translation offsets violate level_group + core_bin grain")

    lookup: dict[str, dict[str, float]] = defaultdict(dict)
    for row in offsets.select(*required).iter_rows(named=True):
        level = str(row["level_group"])
        core_bin = str(row["core_bin"])
        if core_bin not in ALL_CORE_BINS:
            raise ValueError(f"unsupported core bin in translation offsets: {core_bin}")
        lookup[level][core_bin] = float(row["clr_environment_effect"])
    for level, values in lookup.items():
        if set(values) != set(ALL_CORE_BINS):
            raise ValueError(f"translation level {level} does not contain all core bins")
        component_sum = sum(values.values())
        if abs(component_sum) > 1e-7:
            raise ValueError(
                f"translation CLR effects must sum to zero within level {level}: {component_sum}"
            )
    if "MLB" not in lookup:
        raise ValueError("translation offsets must contain MLB anchor")
    return dict(lookup)


def build_recency_weighted_level_profile(
    summary: pl.DataFrame,
    profile: pl.DataFrame,
    *,
    cutoff: date,
    window: EvidenceWindow,
) -> pl.DataFrame:
    """Aggregate predictor evidence at player × level before translation."""

    validate_player_game_evidence(summary, profile)
    working = summary.with_columns(
        pl.col("game_date").cast(pl.String).str.to_date(strict=False).alias("_evidence_date")
    )
    predicate = pl.col("_evidence_date") < pl.lit(cutoff)
    if window.lookback_days is not None:
        start = cutoff - timedelta(days=int(window.lookback_days))
        predicate = predicate & (pl.col("_evidence_date") >= pl.lit(start))
    working = working.filter(predicate)
    if working.is_empty():
        return pl.DataFrame(
            schema={
                "player_id": pl.Int64,
                "level_group": pl.String,
                "core_bin": pl.String,
                "effective_occurrence_count": pl.Float64,
                "effective_core_events": pl.Float64,
            }
        )

    days_old = (pl.lit(cutoff) - pl.col("_evidence_date")).dt.total_days().cast(pl.Float64)
    if window.half_life_days is None:
        weight = pl.lit(1.0)
    else:
        weight = (-days_old * (log(2.0) / float(window.half_life_days))).exp()
    weighted_keys = working.with_columns(weight.alias("_recency_weight")).select(
        *PLAYER_GAME_KEY,
        "level_group",
        "_recency_weight",
    )
    weighted_profile = profile.join(
        weighted_keys,
        on=list(PLAYER_GAME_KEY),
        how="inner",
    )
    aggregated = (
        weighted_profile.group_by(["player_id", "level_group", "core_bin"])
        .agg(
            (pl.col("occurrence_count") * pl.col("_recency_weight"))
            .sum()
            .cast(pl.Float64)
            .alias("effective_occurrence_count")
        )
    )
    totals = aggregated.group_by(["player_id", "level_group"]).agg(
        pl.col("effective_occurrence_count").sum().alias("effective_core_events")
    )
    return (
        aggregated.join(totals, on=["player_id", "level_group"], how="left")
        .sort(["player_id", "level_group", "core_bin"])
    )


def translate_level_profile_to_mlb(
    level_profile: pl.DataFrame,
    offsets: pl.DataFrame,
    *,
    pseudocount: float = DEFAULT_CLR_PSEUDOCOUNT,
) -> pl.DataFrame:
    """Translate each player × level profile to the common latent MLB scale."""

    if pseudocount <= 0:
        raise ValueError("translation pseudocount must be positive")
    required = {
        "player_id",
        "level_group",
        "core_bin",
        "effective_occurrence_count",
        "effective_core_events",
    }
    _require_columns(level_profile, required, "level profile")
    lookup = _translation_lookup(offsets)
    if level_profile.is_empty():
        return pl.DataFrame(
            schema={
                "player_id": pl.Int64,
                "level_group": pl.String,
                "core_bin": pl.String,
                "effective_core_events": pl.Float64,
                "translated_effective_count": pl.Float64,
                "translated_mlb_rate": pl.Float64,
            }
        )

    rows: list[dict[str, object]] = []
    for key, group in level_profile.group_by(["player_id", "level_group"], maintain_order=True):
        player_id, level_group = int(key[0]), str(key[1])
        if level_group not in lookup:
            raise ValueError(f"no fitted translation offsets for level {level_group}")
        counts = {
            str(row["core_bin"]): float(row["effective_occurrence_count"])
            for row in group.iter_rows(named=True)
        }
        unknown = sorted(set(counts) - set(ALL_CORE_BINS))
        if unknown:
            raise ValueError(f"unsupported core bins in player level profile: {unknown}")
        total_values = set(float(value) for value in group.get_column("effective_core_events").to_list())
        if len(total_values) != 1:
            raise ValueError("effective_core_events must be constant within player + level")
        total = total_values.pop()
        if total <= 0:
            raise ValueError("translated player-level evidence requires positive effective core events")
        observed_counts = [counts.get(core_bin, 0.0) for core_bin in ALL_CORE_BINS]
        if abs(sum(observed_counts) - total) > 1e-7 * max(1.0, total):
            raise ValueError("player-level profile counts do not reconcile to effective core events")

        probabilities = [
            (count + pseudocount) / (total + pseudocount * len(ALL_CORE_BINS))
            for count in observed_counts
        ]
        observed_clr = _clr(probabilities)
        latent_clr = [
            observed_clr[index] - lookup[level_group][core_bin]
            for index, core_bin in enumerate(ALL_CORE_BINS)
        ]
        latent_probabilities = _softmax(latent_clr)
        for core_bin, probability in zip(ALL_CORE_BINS, latent_probabilities, strict=True):
            rows.append(
                {
                    "player_id": player_id,
                    "level_group": level_group,
                    "core_bin": core_bin,
                    "effective_core_events": total,
                    "translated_effective_count": probability * total,
                    "translated_mlb_rate": probability,
                }
            )
    return pl.DataFrame(rows).sort(["player_id", "level_group", "core_bin"])


def aggregate_translated_player_profile(translated_levels: pl.DataFrame) -> pl.DataFrame:
    """Combine already-translated level segments to one player latent profile."""

    required = {"player_id", "core_bin", "translated_effective_count"}
    _require_columns(translated_levels, required, "translated level profile")
    if translated_levels.is_empty():
        return pl.DataFrame(
            schema={
                "player_id": pl.Int64,
                "core_bin": pl.String,
                "translated_effective_count": pl.Float64,
                "effective_core_events": pl.Float64,
                "translated_mlb_rate": pl.Float64,
            }
        )
    aggregated = translated_levels.group_by(["player_id", "core_bin"]).agg(
        pl.col("translated_effective_count").sum().alias("translated_effective_count")
    )
    totals = aggregated.group_by("player_id").agg(
        pl.col("translated_effective_count").sum().alias("effective_core_events")
    )
    return (
        aggregated.join(totals, on="player_id", how="left")
        .with_columns(
            (pl.col("translated_effective_count") / pl.col("effective_core_events"))
            .alias("translated_mlb_rate")
        )
        .sort(["player_id", "core_bin"])
    )


def build_translated_player_evidence(
    summary: pl.DataFrame,
    profile: pl.DataFrame,
    offsets: pl.DataFrame,
    *,
    cutoff: date,
    window: EvidenceWindow,
    pseudocount: float = DEFAULT_CLR_PSEUDOCOUNT,
) -> pl.DataFrame:
    """Build one recency-weighted, MLB-scale player evidence profile."""

    level_profile = build_recency_weighted_level_profile(
        summary,
        profile,
        cutoff=cutoff,
        window=window,
    )
    translated = translate_level_profile_to_mlb(
        level_profile,
        offsets,
        pseudocount=pseudocount,
    )
    return aggregate_translated_player_profile(translated)


def _player_profiles(translated: pl.DataFrame) -> tuple[dict[int, dict[str, float]], dict[int, float]]:
    required = {
        "player_id",
        "core_bin",
        "translated_effective_count",
        "effective_core_events",
    }
    _require_columns(translated, required, "translated player profile")
    duplicate = translated.group_by(["player_id", "core_bin"]).len().filter(pl.col("len") != 1)
    if not duplicate.is_empty():
        raise ValueError("translated player profile violates player_id + core_bin grain")

    counts: dict[int, dict[str, float]] = defaultdict(dict)
    totals: dict[int, float] = {}
    for row in translated.iter_rows(named=True):
        player_id = int(row["player_id"])
        core_bin = str(row["core_bin"])
        if core_bin not in ALL_CORE_BINS:
            raise ValueError(f"unsupported translated core bin: {core_bin}")
        counts[player_id][core_bin] = float(row["translated_effective_count"])
        total = float(row["effective_core_events"])
        if player_id in totals and abs(totals[player_id] - total) > 1e-7:
            raise ValueError("effective_core_events must be constant within translated player profile")
        totals[player_id] = total
    for player_id, values in counts.items():
        if set(values) != set(ALL_CORE_BINS):
            raise ValueError(f"translated player {player_id} does not contain all core bins")
        if abs(sum(values.values()) - totals[player_id]) > 1e-7 * max(1.0, totals[player_id]):
            raise ValueError(f"translated player {player_id} counts do not reconcile")
    return dict(counts), totals


def fit_leave_one_out_age_level_prior(
    translated: pl.DataFrame,
    context: pl.DataFrame,
    *,
    age_band_width_years: float = DEFAULT_AGE_BAND_WIDTH_YEARS,
    min_age_level_peers: int = DEFAULT_MIN_AGE_LEVEL_PEERS,
    pseudocount: float = DEFAULT_CLR_PSEUDOCOUNT,
) -> pl.DataFrame:
    """Build Baseline-0 priors without using a player's own performance.

    Preferred peer pool = same current level and same age band. If fewer than the
    requested number of *other* players are available, fall back to same current
    level; if that is empty, fall back to all other players. Every pool explicitly
    excludes the player being predicted.
    """

    if age_band_width_years <= 0:
        raise ValueError("age band width must be positive")
    if min_age_level_peers < 1:
        raise ValueError("minimum age-level peers must be at least one")
    if pseudocount <= 0:
        raise ValueError("prior pseudocount must be positive")
    _require_columns(
        context,
        {"player_id", "age_years", "as_of_level_group", "as_of_environment_ambiguous"},
        "baseline context",
    )
    duplicate_context = context.group_by("player_id").len().filter(pl.col("len") != 1)
    if not duplicate_context.is_empty():
        raise ValueError("baseline context violates player_id grain")

    counts, totals = _player_profiles(translated)
    contexts: dict[int, dict[str, object]] = {}
    for row in context.iter_rows(named=True):
        player_id = int(row["player_id"])
        if player_id not in counts:
            continue
        if bool(row["as_of_environment_ambiguous"]):
            continue
        age = row["age_years"]
        level = row["as_of_level_group"]
        if age is None or level is None:
            continue
        age_value = float(age)
        band = floor(age_value / age_band_width_years) * age_band_width_years
        contexts[player_id] = {
            "age_years": age_value,
            "age_band_start": band,
            "level_group": str(level),
        }

    eligible_ids = sorted(contexts)
    if len(eligible_ids) < 2:
        raise ValueError("Baseline 0 requires at least two players with exact age and unambiguous level")

    age_level_groups: dict[tuple[str, float], set[int]] = defaultdict(set)
    level_groups: dict[str, set[int]] = defaultdict(set)
    for player_id, row in contexts.items():
        level = str(row["level_group"])
        band = float(row["age_band_start"])
        age_level_groups[(level, band)].add(player_id)
        level_groups[level].add(player_id)
    global_ids = set(eligible_ids)

    rows: list[dict[str, object]] = []
    for player_id in eligible_ids:
        row = contexts[player_id]
        level = str(row["level_group"])
        band = float(row["age_band_start"])
        preferred = age_level_groups[(level, band)] - {player_id}
        if len(preferred) >= min_age_level_peers:
            peers = preferred
            source = "age_level"
        else:
            level_peers = level_groups[level] - {player_id}
            if level_peers:
                peers = level_peers
                source = "level_fallback"
            else:
                peers = global_ids - {player_id}
                source = "global_fallback"
        if not peers:
            raise ValueError(f"no leave-one-out Baseline 0 peers for player {player_id}")

        pooled = {
            core_bin: sum(counts[peer][core_bin] for peer in peers)
            for core_bin in ALL_CORE_BINS
        }
        pooled_total = sum(totals[peer] for peer in peers)
        denominator = pooled_total + pseudocount * len(ALL_CORE_BINS)
        for core_bin in ALL_CORE_BINS:
            probability = (pooled[core_bin] + pseudocount) / denominator
            rows.append(
                {
                    "player_id": player_id,
                    "core_bin": core_bin,
                    "age_years": float(row["age_years"]),
                    "age_band_start": band,
                    "as_of_level_group": level,
                    "prior_probability": probability,
                    "prior_peer_source": source,
                    "prior_peer_player_count": len(peers),
                    "prior_peer_effective_core_events": pooled_total,
                    "baseline0_method": BASELINE0_METHOD,
                }
            )
    return pl.DataFrame(rows).sort(["player_id", "core_bin"])


def build_baseline_profiles(
    translated: pl.DataFrame,
    prior: pl.DataFrame,
    *,
    prior_strength_core_events: float = DEFAULT_PRIOR_STRENGTH_CORE_EVENTS,
) -> BaselineProfiles:
    """Return Baseline 0 and empirical-Bayes Baseline 1 latent probabilities."""

    if prior_strength_core_events <= 0:
        raise ValueError("Baseline 1 prior strength must be positive")
    _require_columns(
        prior,
        {
            "player_id",
            "core_bin",
            "prior_probability",
            "prior_peer_source",
            "baseline0_method",
        },
        "Baseline 0 prior",
    )
    counts, totals = _player_profiles(translated)
    prior_by_player: dict[int, dict[str, dict[str, object]]] = defaultdict(dict)
    for row in prior.iter_rows(named=True):
        player_id = int(row["player_id"])
        prior_by_player[player_id][str(row["core_bin"])] = dict(row)

    rows: list[dict[str, object]] = []
    for player_id in sorted(set(counts) & set(prior_by_player)):
        if set(prior_by_player[player_id]) != set(ALL_CORE_BINS):
            raise ValueError(f"Baseline 0 prior incomplete for player {player_id}")
        total = totals[player_id]
        baseline1_sum = 0.0
        player_rows: list[dict[str, object]] = []
        for core_bin in ALL_CORE_BINS:
            prior_probability = float(prior_by_player[player_id][core_bin]["prior_probability"])
            if not 0 < prior_probability < 1:
                raise ValueError("Baseline 0 component probabilities must lie strictly between zero and one")
            baseline1 = (
                counts[player_id][core_bin]
                + prior_strength_core_events * prior_probability
            ) / (total + prior_strength_core_events)
            baseline1_sum += baseline1
            player_rows.append(
                {
                    "player_id": player_id,
                    "core_bin": core_bin,
                    "baseline0_latent_probability": prior_probability,
                    "baseline1_latent_probability": baseline1,
                    "player_effective_core_events": total,
                    "prior_strength_core_events": prior_strength_core_events,
                    "prior_peer_source": str(
                        prior_by_player[player_id][core_bin]["prior_peer_source"]
                    ),
                    "baseline0_method": str(
                        prior_by_player[player_id][core_bin]["baseline0_method"]
                    ),
                    "baseline1_method": BASELINE1_METHOD,
                }
            )
        if abs(baseline1_sum - 1.0) > 1e-9:
            raise ValueError(f"Baseline 1 profile does not sum to one for player {player_id}")
        rows.extend(player_rows)

    result = pl.DataFrame(rows).sort(["player_id", "core_bin"])
    metrics = {
        "baseline0_method": BASELINE0_METHOD,
        "baseline1_method": BASELINE1_METHOD,
        "prediction_player_count": result.get_column("player_id").n_unique() if not result.is_empty() else 0,
        "profile_row_count": result.height,
        "prior_strength_core_events": float(prior_strength_core_events),
        "age_band_width_years": DEFAULT_AGE_BAND_WIDTH_YEARS,
        "player_specific_recent_performance_in_baseline0": False,
        "player_specific_translated_recent_performance_in_baseline1": True,
        "latent_reporting_scale": "MLB",
    }
    return BaselineProfiles(profile=result, metrics=metrics)
