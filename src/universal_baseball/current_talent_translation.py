"""Leakage-safe matched-environment evidence for Current Talent translation.

This module is a *candidate baseline foundation*, not a promoted translation model.
It turns certified player-game evidence into chronological environment stints and
adjacent within-player environment pairs, then provides a transparent weighted
least-squares estimator for level effects on a centered-log-ratio (CLR) profile
scale.

Important boundaries:

- only games strictly before ``training_end`` may contribute;
- same-day multi-environment player dates are ambiguous and break continuity;
- pairs are made only from adjacent observed stints, so a sparse/ambiguous stop is
  never silently skipped to create a cleaner transition;
- actual season/league/level context is preserved in the evidence even though the
  first candidate fitter estimates level-group effects only;
- the fitter requires the requested reporting anchor (normally MLB) to be present
  and connected to every fitted level;
- no Current Talent estimate, age prior, projection, or playing-time inference is
  produced here.

The CLR representation keeps the full core profile compositional: environment
shifts are estimated jointly on a scale whose components sum to zero, and later
translation can map back through a softmax without independently distorted
component probabilities.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import date
from math import log, sqrt
from typing import Any

import polars as pl

from universal_baseball.current_talent_evidence import (
    LEVEL_ORDINAL,
    validate_player_game_evidence,
)
from universal_baseball.performance_season import ALL_CORE_BINS


STINT_KEY = ("player_id", "continuity_segment", "stint_index")
STINT_ENVIRONMENT_KEY = (*STINT_KEY, "season", "league_id", "level_group")
PAIR_PROFILE_KEY = ("pair_id", "core_bin")
TRANSLATION_METHOD = "matched_adjacent_stint_clr_wls_v1"
DEFAULT_CLR_PSEUDOCOUNT = 0.5


@dataclass(frozen=True, slots=True)
class EnvironmentTranslationEvidence:
    """Training-only stints and matched environment pairs."""

    stint_summary: pl.DataFrame
    stint_profile: pl.DataFrame
    pair_summary: pl.DataFrame
    pair_profile: pl.DataFrame
    metrics: dict[str, Any]


@dataclass(frozen=True, slots=True)
class LevelTranslationFit:
    """Candidate level-group CLR effects relative to one reporting anchor."""

    offsets: pl.DataFrame
    metrics: dict[str, Any]


def _parsed_date(column: str = "game_date") -> pl.Expr:
    return pl.col(column).cast(pl.String).str.to_date(strict=False)


def _empty_mapping() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "player_id": pl.Int64,
            "training_date": pl.Date,
            "season": pl.Int64,
            "league_id": pl.Int64,
            "level_group": pl.String,
            "continuity_segment": pl.Int64,
            "stint_index": pl.Int64,
        }
    )


def _build_stint_mapping(date_summary: pl.DataFrame) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    current_player: int | None = None
    segment = 0
    stint_index = 0
    previous_environment: tuple[int, int, str] | None = None

    for row in date_summary.sort(["player_id", "training_date"]).iter_rows(named=True):
        player_id = int(row["player_id"])
        if player_id != current_player:
            current_player = player_id
            segment = 0
            stint_index = 0
            previous_environment = None

        if bool(row["ambiguous_environment"]):
            segment += 1
            previous_environment = None
            continue

        environment = (
            int(row["season"]),
            int(row["league_id"]),
            str(row["level_group"]),
        )
        if previous_environment is None or environment != previous_environment:
            stint_index += 1
        previous_environment = environment
        rows.append(
            {
                "player_id": player_id,
                "training_date": row["training_date"],
                "season": environment[0],
                "league_id": environment[1],
                "level_group": environment[2],
                "continuity_segment": segment,
                "stint_index": stint_index,
            }
        )

    if not rows:
        return _empty_mapping()
    return pl.DataFrame(rows).cast(_empty_mapping().schema, strict=True)


def _profile_counts_by_stint(stint_profile: pl.DataFrame) -> dict[tuple[int, int, int], dict[str, int]]:
    counts: dict[tuple[int, int, int], dict[str, int]] = defaultdict(dict)
    for row in stint_profile.iter_rows(named=True):
        key = (
            int(row["player_id"]),
            int(row["continuity_segment"]),
            int(row["stint_index"]),
        )
        core_bin = str(row["core_bin"])
        if core_bin in counts[key]:
            raise ValueError(f"duplicate stint profile bin at {key}: {core_bin}")
        counts[key][core_bin] = int(row["occurrence_count"])
    return counts


def _clr_from_counts(
    counts: dict[str, int],
    *,
    total: int,
    pseudocount: float,
) -> dict[str, float]:
    if total <= 0:
        raise ValueError("CLR profile requires positive core-event evidence")
    if pseudocount <= 0:
        raise ValueError("CLR pseudocount must be positive")
    denominator = float(total) + pseudocount * len(ALL_CORE_BINS)
    logs = {
        core_bin: log((float(counts.get(core_bin, 0)) + pseudocount) / denominator)
        for core_bin in ALL_CORE_BINS
    }
    mean_log = sum(logs.values()) / len(logs)
    return {core_bin: value - mean_log for core_bin, value in logs.items()}


def build_training_environment_transition_evidence(
    summary: pl.DataFrame,
    profile: pl.DataFrame,
    *,
    training_end: date,
    min_core_events_per_stint: int = 20,
    max_gap_days: int = 365,
    clr_pseudocount: float = DEFAULT_CLR_PSEUDOCOUNT,
) -> EnvironmentTranslationEvidence:
    """Build adjacent within-player environment evidence from training history only.

    ``training_end`` is exclusive. A player-date containing more than one actual
    season/league/level environment is excluded and deliberately breaks the stint
    chain so rows on either side can never be paired across that ambiguous date.

    All observed stints are retained. Pair eligibility is evaluated *after* the
    adjacent pairs are formed, which prevents a low-evidence intermediate stint
    from being dropped and accidentally creating a non-adjacent transition.
    """

    if min_core_events_per_stint <= 0:
        raise ValueError("min_core_events_per_stint must be positive")
    if max_gap_days <= 0:
        raise ValueError("max_gap_days must be positive")
    if clr_pseudocount <= 0:
        raise ValueError("clr_pseudocount must be positive")

    evidence_metrics = validate_player_game_evidence(summary, profile)
    training_summary = summary.with_columns(_parsed_date().alias("training_date")).filter(
        pl.col("training_date") < pl.lit(training_end)
    )
    if training_summary.is_empty():
        raise ValueError("no player-game evidence exists before training_end")

    date_summary = (
        training_summary.group_by(["player_id", "training_date"])
        .agg(
            pl.col("season").n_unique().alias("_season_count"),
            pl.col("season").first().cast(pl.Int64).alias("season"),
            pl.col("league_id").n_unique().alias("_league_count"),
            pl.col("league_id").first().cast(pl.Int64).alias("league_id"),
            pl.col("level_group").n_unique().alias("_level_count"),
            pl.col("level_group").first().cast(pl.String).alias("level_group"),
            pl.col("game_pk").n_unique().cast(pl.Int64).alias("game_count"),
            pl.col("batting_plate_appearances").sum().cast(pl.Int64).alias("plate_appearances"),
            pl.col("core_profile_event_count").sum().cast(pl.Int64).alias("core_events"),
        )
        .with_columns(
            (
                (pl.col("_season_count") != 1)
                | (pl.col("_league_count") != 1)
                | (pl.col("_level_count") != 1)
            ).alias("ambiguous_environment")
        )
        .sort(["player_id", "training_date"])
    )

    mapping = _build_stint_mapping(date_summary)
    if mapping.is_empty():
        raise ValueError("all training player-dates are environment-ambiguous")

    mapped_dates = (
        date_summary.filter(~pl.col("ambiguous_environment"))
        .join(
            mapping,
            on=["player_id", "training_date", "season", "league_id", "level_group"],
            how="inner",
        )
    )
    stint_summary = (
        mapped_dates.group_by(list(STINT_ENVIRONMENT_KEY))
        .agg(
            pl.col("training_date").min().alias("first_game_date"),
            pl.col("training_date").max().alias("last_game_date"),
            pl.col("game_count").sum().cast(pl.Int64).alias("game_count"),
            pl.col("plate_appearances").sum().cast(pl.Int64).alias("plate_appearances"),
            pl.col("core_events").sum().cast(pl.Int64).alias("core_events"),
        )
        .sort(["player_id", "continuity_segment", "stint_index"])
    )

    training_profile = profile.with_columns(_parsed_date().alias("training_date")).filter(
        pl.col("training_date") < pl.lit(training_end)
    )
    stint_profile = (
        training_profile.join(
            mapping,
            on=["player_id", "training_date", "season", "league_id", "level_group"],
            how="inner",
        )
        .group_by([*STINT_ENVIRONMENT_KEY, "core_bin"])
        .agg(pl.col("occurrence_count").sum().cast(pl.Int64).alias("occurrence_count"))
        .sort(["player_id", "continuity_segment", "stint_index", "core_bin"])
    )

    reconciliation = (
        stint_summary.select(*STINT_KEY, "core_events")
        .join(
            stint_profile.group_by(list(STINT_KEY)).agg(
                pl.col("occurrence_count").sum().cast(pl.Int64).alias("profile_core_events")
            ),
            on=list(STINT_KEY),
            how="left",
        )
        .with_columns(pl.col("profile_core_events").fill_null(0).cast(pl.Int64))
    )
    if reconciliation.filter(pl.col("profile_core_events") != pl.col("core_events")).height:
        raise ValueError("stint profile counts do not reconcile to stint core-event totals")

    pair_rows: list[dict[str, object]] = []
    previous_by_group: dict[tuple[int, int], dict[str, object]] = {}
    for row in stint_summary.iter_rows(named=True):
        group = (int(row["player_id"]), int(row["continuity_segment"]))
        previous = previous_by_group.get(group)
        if previous is not None:
            from_last = previous["last_game_date"]
            to_first = row["first_game_date"]
            if not isinstance(from_last, date) or not isinstance(to_first, date):
                raise ValueError("stint dates must be parsed dates")
            if from_last >= to_first:
                raise ValueError("adjacent stints do not have strict date-only chronology")

            gap_days = (to_first - from_last).days
            from_core = int(previous["core_events"])
            to_core = int(row["core_events"])
            reasons: list[str] = []
            if from_core < min_core_events_per_stint:
                reasons.append("LOW_FROM_CORE_EVENTS")
            if to_core < min_core_events_per_stint:
                reasons.append("LOW_TO_CORE_EVENTS")
            if gap_days > max_gap_days:
                reasons.append("GAP_EXCEEDS_MAX")
            eligible = not reasons

            from_level = str(previous["level_group"])
            to_level = str(row["level_group"])
            from_ordinal = LEVEL_ORDINAL[from_level]
            to_ordinal = LEVEL_ORDINAL[to_level]
            if to_ordinal > from_ordinal:
                transition = "PROMOTION"
            elif to_ordinal < from_ordinal:
                transition = "DEMOTION"
            else:
                transition = "SAME_LEVEL_ENVIRONMENT_CHANGE"

            denominator = from_core + to_core
            pair_weight = (
                float(from_core * to_core) / float(denominator) if denominator > 0 else 0.0
            )
            pair_id = (
                f"p{int(row['player_id'])}:seg{int(row['continuity_segment'])}:"
                f"{int(previous['stint_index'])}>{int(row['stint_index'])}"
            )
            pair_rows.append(
                {
                    "pair_id": pair_id,
                    "player_id": int(row["player_id"]),
                    "continuity_segment": int(row["continuity_segment"]),
                    "from_stint_index": int(previous["stint_index"]),
                    "to_stint_index": int(row["stint_index"]),
                    "from_season": int(previous["season"]),
                    "from_league_id": int(previous["league_id"]),
                    "from_level_group": from_level,
                    "from_first_game_date": previous["first_game_date"],
                    "from_last_game_date": from_last,
                    "from_core_events": from_core,
                    "to_season": int(row["season"]),
                    "to_league_id": int(row["league_id"]),
                    "to_level_group": to_level,
                    "to_first_game_date": to_first,
                    "to_last_game_date": row["last_game_date"],
                    "to_core_events": to_core,
                    "gap_days": gap_days,
                    "transition": transition,
                    "pair_precision_weight": pair_weight,
                    "translation_pair_eligible": eligible,
                    "pair_exclusion_reason": ";".join(reasons),
                    "clr_pseudocount": float(clr_pseudocount),
                }
            )
        previous_by_group[group] = row

    pair_schema = {
        "pair_id": pl.String,
        "player_id": pl.Int64,
        "continuity_segment": pl.Int64,
        "from_stint_index": pl.Int64,
        "to_stint_index": pl.Int64,
        "from_season": pl.Int64,
        "from_league_id": pl.Int64,
        "from_level_group": pl.String,
        "from_first_game_date": pl.Date,
        "from_last_game_date": pl.Date,
        "from_core_events": pl.Int64,
        "to_season": pl.Int64,
        "to_league_id": pl.Int64,
        "to_level_group": pl.String,
        "to_first_game_date": pl.Date,
        "to_last_game_date": pl.Date,
        "to_core_events": pl.Int64,
        "gap_days": pl.Int64,
        "transition": pl.String,
        "pair_precision_weight": pl.Float64,
        "translation_pair_eligible": pl.Boolean,
        "pair_exclusion_reason": pl.String,
        "clr_pseudocount": pl.Float64,
    }
    pair_summary = (
        pl.DataFrame(pair_rows).cast(pair_schema, strict=True)
        if pair_rows
        else pl.DataFrame(schema=pair_schema)
    )

    counts_by_stint = _profile_counts_by_stint(stint_profile)
    pair_profile_rows: list[dict[str, object]] = []
    for pair in pair_rows:
        if not bool(pair["translation_pair_eligible"]):
            continue
        from_key = (
            int(pair["player_id"]),
            int(pair["continuity_segment"]),
            int(pair["from_stint_index"]),
        )
        to_key = (
            int(pair["player_id"]),
            int(pair["continuity_segment"]),
            int(pair["to_stint_index"]),
        )
        from_counts = counts_by_stint.get(from_key, {})
        to_counts = counts_by_stint.get(to_key, {})
        if sum(from_counts.values()) != int(pair["from_core_events"]):
            raise ValueError(f"from-stint profile mismatch for {pair['pair_id']}")
        if sum(to_counts.values()) != int(pair["to_core_events"]):
            raise ValueError(f"to-stint profile mismatch for {pair['pair_id']}")
        from_clr = _clr_from_counts(
            from_counts,
            total=int(pair["from_core_events"]),
            pseudocount=clr_pseudocount,
        )
        to_clr = _clr_from_counts(
            to_counts,
            total=int(pair["to_core_events"]),
            pseudocount=clr_pseudocount,
        )
        for core_bin in ALL_CORE_BINS:
            pair_profile_rows.append(
                {
                    "pair_id": str(pair["pair_id"]),
                    "core_bin": core_bin,
                    "from_occurrence_count": int(from_counts.get(core_bin, 0)),
                    "to_occurrence_count": int(to_counts.get(core_bin, 0)),
                    "from_clr": float(from_clr[core_bin]),
                    "to_clr": float(to_clr[core_bin]),
                    "clr_delta": float(to_clr[core_bin] - from_clr[core_bin]),
                }
            )
    pair_profile_schema = {
        "pair_id": pl.String,
        "core_bin": pl.String,
        "from_occurrence_count": pl.Int64,
        "to_occurrence_count": pl.Int64,
        "from_clr": pl.Float64,
        "to_clr": pl.Float64,
        "clr_delta": pl.Float64,
    }
    pair_profile = (
        pl.DataFrame(pair_profile_rows).cast(pair_profile_schema, strict=True)
        if pair_profile_rows
        else pl.DataFrame(schema=pair_profile_schema)
    )

    eligible_pairs = pair_summary.filter(pl.col("translation_pair_eligible"))
    metrics = {
        "training_end_exclusive": training_end.isoformat(),
        "temporal_semantics": "retrospective_event_cutoff_corrected_history_not_vintage_information_set",
        "source_player_game_count": int(evidence_metrics["player_game_count"]),
        "training_player_game_count": int(training_summary.height),
        "training_player_count": int(training_summary.get_column("player_id").n_unique()),
        "training_player_date_count": int(date_summary.height),
        "ambiguous_player_date_count": int(
            date_summary.filter(pl.col("ambiguous_environment")).height
        ),
        "stint_count": int(stint_summary.height),
        "pair_count": int(pair_summary.height),
        "eligible_pair_count": int(eligible_pairs.height),
        "eligible_pair_player_count": (
            int(eligible_pairs.get_column("player_id").n_unique()) if not eligible_pairs.is_empty() else 0
        ),
        "eligible_promotion_pair_count": int(
            eligible_pairs.filter(pl.col("transition") == "PROMOTION").height
        ),
        "eligible_demotion_pair_count": int(
            eligible_pairs.filter(pl.col("transition") == "DEMOTION").height
        ),
        "eligible_same_level_environment_pair_count": int(
            eligible_pairs.filter(pl.col("transition") == "SAME_LEVEL_ENVIRONMENT_CHANGE").height
        ),
        "min_core_events_per_stint": int(min_core_events_per_stint),
        "max_gap_days": int(max_gap_days),
        "clr_pseudocount": float(clr_pseudocount),
        "pair_weight_method": "inverse_difference_variance_proxy_n1_n2_over_n1_plus_n2",
        "pairing_policy": "adjacent_observed_stints_only_no_sparse_or_ambiguous_bridge",
    }
    return EnvironmentTranslationEvidence(
        stint_summary=stint_summary,
        stint_profile=stint_profile,
        pair_summary=pair_summary,
        pair_profile=pair_profile,
        metrics=metrics,
    )


def _solve_linear_system(matrix: list[list[float]], rhs: list[float]) -> list[float]:
    size = len(rhs)
    if size == 0:
        return []
    augmented = [list(matrix[row]) + [float(rhs[row])] for row in range(size)]
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) < 1e-12:
            raise ValueError("translation normal equations are singular")
        if pivot != column:
            augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        scale = augmented[column][column]
        augmented[column] = [value / scale for value in augmented[column]]
        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column]
            if abs(factor) < 1e-18:
                continue
            augmented[row] = [
                value - factor * pivot_value
                for value, pivot_value in zip(augmented[row], augmented[column], strict=True)
            ]
    return [augmented[row][-1] for row in range(size)]


def _graph_distances(
    pairs: list[dict[str, object]],
    *,
    anchor_level: str,
) -> dict[str, int]:
    adjacency: dict[str, set[str]] = defaultdict(set)
    for pair in pairs:
        from_level = str(pair["from_level_group"])
        to_level = str(pair["to_level_group"])
        if from_level == to_level:
            continue
        adjacency[from_level].add(to_level)
        adjacency[to_level].add(from_level)

    if anchor_level not in adjacency:
        raise ValueError(f"translation anchor level {anchor_level!r} has no matched cross-level support")
    distance = {anchor_level: 0}
    queue: deque[str] = deque([anchor_level])
    while queue:
        level = queue.popleft()
        for neighbor in sorted(adjacency[level]):
            if neighbor not in distance:
                distance[neighbor] = distance[level] + 1
                queue.append(neighbor)
    return distance


def fit_level_clr_translation(
    pair_summary: pl.DataFrame,
    pair_profile: pl.DataFrame,
    *,
    anchor_level: str = "MLB",
) -> LevelTranslationFit:
    """Fit candidate level CLR effects from eligible matched transition pairs.

    For each core component ``k`` the fitted relation is:

    ``CLR(observed at level L, k) = CLR(anchor-scale latent profile, k) + beta[L, k]``

    with ``beta[anchor_level, k] = 0``. Within-player pair differences remove the
    player intercept; weighted graph least squares estimates the remaining level
    effects. Every fitted level must be connected to the anchor through observed
    cross-level pairs or the function fails closed.
    """

    if anchor_level not in LEVEL_ORDINAL:
        raise ValueError(f"unsupported anchor level: {anchor_level}")
    summary_required = {
        "pair_id",
        "from_level_group",
        "to_level_group",
        "pair_precision_weight",
        "translation_pair_eligible",
    }
    profile_required = {"pair_id", "core_bin", "clr_delta"}
    if missing := sorted(summary_required - set(pair_summary.columns)):
        raise ValueError(f"pair summary missing translation fields: {missing}")
    if missing := sorted(profile_required - set(pair_profile.columns)):
        raise ValueError(f"pair profile missing translation fields: {missing}")

    eligible = pair_summary.filter(
        pl.col("translation_pair_eligible")
        & (pl.col("pair_precision_weight") > 0)
        & (pl.col("from_level_group") != pl.col("to_level_group"))
    )
    if eligible.is_empty():
        raise ValueError("no eligible cross-level transition pairs for translation")

    invalid_levels = set(eligible.get_column("from_level_group").to_list()) | set(
        eligible.get_column("to_level_group").to_list()
    )
    invalid_levels -= set(LEVEL_ORDINAL)
    if invalid_levels:
        raise ValueError(f"unsupported level groups in translation pairs: {sorted(invalid_levels)}")

    pair_rows = [dict(row) for row in eligible.iter_rows(named=True)]
    distances = _graph_distances(pair_rows, anchor_level=anchor_level)
    observed_levels = sorted(
        set(eligible.get_column("from_level_group").to_list())
        | set(eligible.get_column("to_level_group").to_list()),
        key=lambda level: LEVEL_ORDINAL[str(level)],
    )
    disconnected = [str(level) for level in observed_levels if str(level) not in distances]
    if disconnected:
        raise ValueError(
            f"translation levels are not connected to anchor {anchor_level}: {disconnected}"
        )

    pair_ids = [str(row["pair_id"]) for row in pair_rows]
    relevant_profile = pair_profile.filter(pl.col("pair_id").is_in(pair_ids))
    duplicate = relevant_profile.group_by(["pair_id", "core_bin"]).len().filter(pl.col("len") != 1)
    if not duplicate.is_empty():
        raise ValueError("translation pair profile violates pair_id + core_bin grain")

    profile_by_pair: dict[str, dict[str, float]] = defaultdict(dict)
    for row in relevant_profile.iter_rows(named=True):
        pair_id = str(row["pair_id"])
        core_bin = str(row["core_bin"])
        if core_bin not in ALL_CORE_BINS:
            raise ValueError(f"unsupported core bin in translation pair profile: {core_bin}")
        profile_by_pair[pair_id][core_bin] = float(row["clr_delta"])
    for pair_id in pair_ids:
        if set(profile_by_pair[pair_id]) != set(ALL_CORE_BINS):
            raise ValueError(f"translation pair {pair_id} does not contain all core bins")

    unknown_levels = [str(level) for level in observed_levels if str(level) != anchor_level]
    level_index = {level: index for index, level in enumerate(unknown_levels)}
    size = len(unknown_levels)
    normal = [[0.0 for _ in range(size)] for _ in range(size)]
    design_rows: list[tuple[dict[str, object], list[float]]] = []
    for pair in pair_rows:
        design = [0.0 for _ in range(size)]
        from_level = str(pair["from_level_group"])
        to_level = str(pair["to_level_group"])
        if from_level != anchor_level:
            design[level_index[from_level]] -= 1.0
        if to_level != anchor_level:
            design[level_index[to_level]] += 1.0
        weight = float(pair["pair_precision_weight"])
        for row_index in range(size):
            for column_index in range(size):
                normal[row_index][column_index] += (
                    weight * design[row_index] * design[column_index]
                )
        design_rows.append((pair, design))

    effects_by_bin: dict[str, dict[str, float]] = {}
    residual_rmse_by_bin: dict[str, float] = {}
    for core_bin in ALL_CORE_BINS:
        rhs = [0.0 for _ in range(size)]
        for pair, design in design_rows:
            weight = float(pair["pair_precision_weight"])
            delta = profile_by_pair[str(pair["pair_id"])][core_bin]
            for index in range(size):
                rhs[index] += weight * design[index] * delta
        solution = _solve_linear_system(normal, rhs)
        effects = {anchor_level: 0.0}
        effects.update({level: solution[index] for level, index in level_index.items()})
        effects_by_bin[core_bin] = effects

        residual_weight = 0.0
        residual_ss = 0.0
        for pair in pair_rows:
            from_level = str(pair["from_level_group"])
            to_level = str(pair["to_level_group"])
            predicted = effects[to_level] - effects[from_level]
            observed = profile_by_pair[str(pair["pair_id"])][core_bin]
            weight = float(pair["pair_precision_weight"])
            residual_ss += weight * (observed - predicted) ** 2
            residual_weight += weight
        residual_rmse_by_bin[core_bin] = sqrt(residual_ss / residual_weight)

    # Numerical noise aside, CLR effects should sum to zero across components for
    # every level. Enforce that compositional constraint explicitly.
    for level in observed_levels:
        level_name = str(level)
        mean_effect = sum(effects_by_bin[core_bin][level_name] for core_bin in ALL_CORE_BINS) / len(
            ALL_CORE_BINS
        )
        for core_bin in ALL_CORE_BINS:
            effects_by_bin[core_bin][level_name] -= mean_effect

    incident_count: dict[str, int] = defaultdict(int)
    incident_weight: dict[str, float] = defaultdict(float)
    for pair in pair_rows:
        weight = float(pair["pair_precision_weight"])
        for level in {str(pair["from_level_group"]), str(pair["to_level_group"])}:
            incident_count[level] += 1
            incident_weight[level] += weight

    output_rows: list[dict[str, object]] = []
    for level in observed_levels:
        level_name = str(level)
        for core_bin in ALL_CORE_BINS:
            output_rows.append(
                {
                    "level_group": level_name,
                    "core_bin": core_bin,
                    "clr_environment_effect": float(effects_by_bin[core_bin][level_name]),
                    "anchor_level_group": anchor_level,
                    "matched_pair_count": int(incident_count[level_name]),
                    "matched_pair_weight": float(incident_weight[level_name]),
                    "graph_distance_to_anchor": int(distances[level_name]),
                    "weighted_fit_residual_rmse": float(residual_rmse_by_bin[core_bin]),
                    "estimator_method": TRANSLATION_METHOD,
                }
            )
    offsets = pl.DataFrame(output_rows).sort(
        [
            pl.col("level_group").replace_strict(LEVEL_ORDINAL, return_dtype=pl.Int64),
            "core_bin",
        ]
    )

    metrics = {
        "anchor_level_group": anchor_level,
        "fitted_level_count": len(observed_levels),
        "eligible_cross_level_pair_count": len(pair_rows),
        "eligible_cross_level_player_count": int(eligible.get_column("player_id").n_unique())
        if "player_id" in eligible.columns
        else None,
        "estimator_method": TRANSLATION_METHOD,
        "profile_transform": "symmetric_pseudocount_centered_log_ratio",
        "all_levels_connected_to_anchor": True,
        "max_graph_distance_to_anchor": max(distances.values()),
        "interpretation": (
            "Candidate training-only observation-layer level effects. Not a Current Talent model "
            "and not promoted until chronological out-of-time validation passes."
        ),
    }
    return LevelTranslationFit(offsets=offsets, metrics=metrics)
