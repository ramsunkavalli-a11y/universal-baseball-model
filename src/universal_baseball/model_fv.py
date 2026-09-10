"""Independent production-based Model FV assembly."""

from __future__ import annotations

from math import erf, sqrt

import polars as pl

from universal_baseball.prospect_value import (
    benchmark_value_from_model_fv,
    display_fv,
    model_fv_from_expected_war,
)
from universal_baseball.prospect_outcome_quality import workload_prior


MODEL_FV_ID = "phase2_production_outcome_model_fv_v4_direct_role_cap"


def cap_nested_role_probabilities(
    arrival: float,
    direct_meaningful: float,
    direct_established: float,
    nested_meaningful: float,
    nested_established: float,
) -> tuple[float, float]:
    """Keep extrapolated nested role masses inside direct unconditional estimates."""

    values = (
        arrival, direct_meaningful, direct_established,
        nested_meaningful, nested_established,
    )
    if any(value < 0.0 or value > 1.0 for value in values):
        raise ValueError("career probabilities must lie in [0, 1]")
    meaningful = min(arrival, direct_meaningful, nested_meaningful)
    established = min(meaningful, direct_established, nested_established)
    return meaningful, established


def _normal_tail(threshold: float, mean: float, variance: float) -> float:
    if variance <= 0:
        return float(mean >= threshold)
    z = (threshold - mean) / sqrt(variance)
    return 0.5 * (1.0 - erf(z / sqrt(2.0)))


def diagnostic_role_bucket(player_type: str, role: str, fv: int) -> str:
    """Describe the projected population for diagnostics; never change a grade."""

    if player_type == "hitter":
        quality = "all_star" if fv >= 60 else "regular" if fv >= 50 else "depth"
        return f"{quality}_{role.lower()}"
    if role == "starter":
        quality = (
            "ace" if fv >= 70 else "number_2" if fv >= 65 else
            "number_3" if fv >= 60 else "number_4" if fv >= 55 else "number_5_or_depth"
        )
        return f"starter_{quality}"
    quality = "closer" if fv >= 60 else "setup" if fv >= 55 else "middle_or_depth"
    return f"reliever_{quality}"


def build_model_fv(
    hitter_paths: pl.DataFrame,
    pitcher_paths: pl.DataFrame,
    uncertainty: pl.DataFrame,
    *,
    pre_mlb_player_ids: set[int] | None = None,
    pre_mlb_arrival_probabilities: dict[tuple[str, int], float] | None = None,
    pre_mlb_meaningful_role_probabilities: dict[tuple[str, int], float] | None = None,
    pre_mlb_established_role_probabilities: dict[tuple[str, int], float] | None = None,
) -> pl.DataFrame:
    """Turn projected six-year production distributions into internal FV grades."""

    required = {"player_id", "season", "expected_war"}
    if required - set(hitter_paths.columns) or required - set(pitcher_paths.columns):
        raise ValueError("expected WAR paths have an unexpected schema")
    if {"player_id", "season", "annual_war_variance"} - set(uncertainty.columns):
        raise ValueError("WAR uncertainty has an unexpected schema")

    pre_mlb_player_ids = pre_mlb_player_ids or set()
    pre_mlb_arrival_probabilities = pre_mlb_arrival_probabilities or {}
    pre_mlb_meaningful_role_probabilities = (
        pre_mlb_meaningful_role_probabilities or {}
    )
    pre_mlb_established_role_probabilities = (
        pre_mlb_established_role_probabilities or {}
    )
    hitter = hitter_paths.group_by("player_id").agg(
        pl.len().alias("hitter_path_rows"),
        pl.col("expected_war").sum().alias("hitter_expected_six_year_war"),
        pl.col("mlb_active_probability").max().alias(
            "hitter_six_year_arrival_probability"
        ),
        (
            pl.col("conditional_war_per_600_pa")
            * pl.when(pl.col("primary_position") == "C")
            .then(450.0)
            .otherwise(550.0)
            / 600.0
        ).sum().alias(
            "hitter_six_control_year_war_if_arrived"
        ),
        pl.col("primary_position").drop_nulls().first().alias("primary_position"),
    )
    pitcher = pitcher_paths.group_by("player_id").agg(
        pl.len().alias("pitcher_path_rows"),
        pl.col("expected_war").sum().alias("pitcher_expected_six_year_war"),
        pl.col("mlb_active_probability").max().alias(
            "pitcher_six_year_arrival_probability"
        ),
        (
            pl.col("conditional_war_per_800_bf")
            * (
                800.0 * pl.col("starter_probability_if_active")
                + 450.0 * pl.col("swingman_probability_if_active")
                + 250.0 * pl.col("reliever_probability_if_active")
            )
            / 800.0
        ).sum().alias("pitcher_six_control_year_war_if_arrived"),
        pl.col("starter_probability_if_active").mean().alias("starter_probability"),
        pl.col("reliever_probability_if_active").mean().alias("reliever_probability"),
    )
    variance = uncertainty.group_by("player_id").agg(
        pl.col("annual_war_variance").sum().alias("six_year_war_variance")
    )
    joined = (
        hitter.join(pitcher, on="player_id", how="full", coalesce=True)
        .join(variance, on="player_id", how="left")
        .with_columns(
            pl.col("hitter_expected_six_year_war").fill_null(0.0),
            pl.col("pitcher_expected_six_year_war").fill_null(0.0),
            pl.col("hitter_path_rows").fill_null(0),
            pl.col("pitcher_path_rows").fill_null(0),
            pl.col("six_year_war_variance").fill_null(0.0),
        )
        .with_columns(
            (
                pl.col("hitter_expected_six_year_war")
                + pl.col("pitcher_expected_six_year_war")
            ).alias("expected_six_year_war"),
            pl.when(
                (pl.col("pitcher_path_rows") > 0)
                & (pl.col("hitter_path_rows") == 0)
            )
            .then(pl.lit("pitcher"))
            .when(
                (pl.col("hitter_path_rows") > 0)
                & (pl.col("pitcher_path_rows") == 0)
            )
            .then(pl.lit("hitter"))
            .when(
                pl.col("pitcher_expected_six_year_war")
                > pl.col("hitter_expected_six_year_war")
            )
            .then(pl.lit("pitcher"))
            .otherwise(pl.lit("hitter"))
            .alias("model_player_type"),
        )
    )

    rows = []
    for row in joined.iter_rows(named=True):
        player_type = str(row["model_player_type"])
        player_id = int(row["player_id"])
        expected_war = float(row["expected_six_year_war"])
        outcome_method = "next_six_calendar_years"
        model_arrival_probability = None
        model_meaningful_role_probability = None
        model_established_role_probability = None
        if player_id in pre_mlb_player_ids:
            if player_type == "hitter":
                arrival = float(row["hitter_six_year_arrival_probability"] or 0.0)
                if_arrived = float(row["hitter_six_control_year_war_if_arrived"] or 0.0)
            else:
                arrival = float(row["pitcher_six_year_arrival_probability"] or 0.0)
                if_arrived = float(row["pitcher_six_control_year_war_if_arrived"] or 0.0)
            modeled_arrival = pre_mlb_arrival_probabilities.get(
                (player_type, player_id)
            )
            model_meaningful_role_probability = (
                pre_mlb_meaningful_role_probabilities.get((player_type, player_id))
            )
            model_established_role_probability = (
                pre_mlb_established_role_probabilities.get((player_type, player_id))
            )
            if modeled_arrival is not None:
                arrival = float(modeled_arrival)
                arrival_source = "historical_two_year_arrival_survival"
            else:
                arrival_source = "maximum_annual_probability_fallback"
            expected_war = arrival * if_arrived
            model_arrival_probability = arrival
            outcome_method = "six_control_years_after_probabilistic_arrival"
        else:
            arrival_source = "not_pre_mlb"
        granular = model_fv_from_expected_war(expected_war, player_type)
        if player_type == "hitter":
            role = str(row["primary_position"] or "position_player")
        elif float(row["starter_probability"] or 0.0) >= 0.5:
            role = "starter"
        else:
            role = "reliever"
        shown_fv = display_fv(granular)
        rows.append(
            {
                **row,
                "expected_six_year_war": expected_war,
                "outcome_method": outcome_method,
                "model_arrival_probability": model_arrival_probability,
                "model_meaningful_role_probability": (
                    model_meaningful_role_probability
                ),
                "model_established_role_probability": (
                    model_established_role_probability
                ),
                "arrival_probability_source": arrival_source,
                "model_role": role,
                "model_fv_granular": granular,
                "model_fv_display": shown_fv,
                "diagnostic_role_bucket": diagnostic_role_bucket(
                    player_type, role, shown_fv
                ),
                "talent_benchmark_value_dollars": benchmark_value_from_model_fv(
                    granular, player_type
                ),
                "star_outcome_probability": _normal_tail(
                    18.0, expected_war, float(row["six_year_war_variance"])
                ),
                "model_fv_id": MODEL_FV_ID,
            }
        )
    return pl.DataFrame(rows, infer_schema_length=None).sort("player_id")


def apply_pre_mlb_outcome_quality_workload(
    values: pl.DataFrame,
    workload_priors: pl.DataFrame,
    *,
    pre_mlb_player_ids: set[int],
    minimum_role_players: int = 30,
) -> pl.DataFrame:
    """Replace the full-season-on-arrival shortcut in a research-only challenger."""

    required = {
        "player_id", "model_player_type", "model_arrival_probability",
        "model_meaningful_role_probability", "expected_six_year_war",
        "hitter_six_control_year_war_if_arrived",
        "pitcher_six_control_year_war_if_arrived", "primary_position",
        "starter_probability", "reliever_probability", "model_fv_granular",
        "model_fv_display",
    }
    if missing := sorted(required - set(values.columns)):
        raise ValueError(f"Model FV values missing columns: {missing}")
    rows = []
    for row in values.iter_rows(named=True):
        player_id = int(row["player_id"])
        applicable = (
            player_id in pre_mlb_player_ids
            and row["model_arrival_probability"] is not None
            and row["model_meaningful_role_probability"] is not None
        )
        incumbent_war = float(row["expected_six_year_war"])
        if not applicable:
            rows.append(
                {
                    **row,
                    "incumbent_expected_six_year_war": incumbent_war,
                    "outcome_quality_expected_workload": None,
                    "outcome_quality_expected_six_year_war": incumbent_war,
                    "outcome_quality_model_fv_granular": row["model_fv_granular"],
                    "outcome_quality_model_fv_display": row["model_fv_display"],
                    "outcome_quality_workload_source": "not_pre_mlb",
                }
            )
            continue
        player_type = str(row["model_player_type"])
        arrival = min(1.0, max(0.0, float(row["model_arrival_probability"])))
        meaningful = min(
            arrival,
            max(0.0, float(row["model_meaningful_role_probability"])),
        )
        fringe = arrival - meaningful
        if player_type == "hitter":
            fringe_workload, fringe_source = workload_prior(
                workload_priors,
                player_type="hitter",
                outcome_tier="fringe",
                career_role="hitter",
                minimum_role_players=minimum_role_players,
            )
            meaningful_workload, meaningful_source = workload_prior(
                workload_priors,
                player_type="hitter",
                outcome_tier="meaningful",
                career_role="hitter",
                minimum_role_players=minimum_role_players,
            )
            assumed_workload = 6.0 * (
                450.0 if str(row["primary_position"] or "") == "C" else 550.0
            )
            full_war = float(row["hitter_six_control_year_war_if_arrived"] or 0.0)
            source = f"fringe_{fringe_source}:meaningful_{meaningful_source}"
        else:
            starter = min(
                1.0, max(0.0, float(row["starter_probability"] or 0.0))
            )
            reliever = min(
                1.0, max(0.0, float(row["reliever_probability"] or 0.0))
            )
            swingman = max(0.0, 1.0 - starter - reliever)
            total_role = starter + reliever + swingman
            starter, reliever, swingman = (
                starter / total_role,
                reliever / total_role,
                swingman / total_role,
            )
            roles = {
                "starter": starter,
                "reliever": reliever,
                "swingman": swingman,
            }
            tier_workloads: dict[str, float] = {}
            tier_sources: dict[str, set[str]] = {}
            for tier in ("fringe", "meaningful"):
                tier_workloads[tier] = 0.0
                tier_sources[tier] = set()
                for role, probability in roles.items():
                    prior, prior_source = workload_prior(
                        workload_priors,
                        player_type="pitcher",
                        outcome_tier=tier,
                        career_role=role,
                        minimum_role_players=minimum_role_players,
                    )
                    tier_workloads[tier] += probability * prior
                    tier_sources[tier].add(prior_source)
            fringe_workload = tier_workloads["fringe"]
            meaningful_workload = tier_workloads["meaningful"]
            assumed_workload = 6.0 * (
                800.0 * starter + 250.0 * reliever + 450.0 * swingman
            )
            full_war = float(row["pitcher_six_control_year_war_if_arrived"] or 0.0)
            source = ":".join(
                f"{tier}_{'+'.join(sorted(sources))}"
                for tier, sources in tier_sources.items()
            )
        expected_workload = (
            fringe * fringe_workload + meaningful * meaningful_workload
        )
        rate = full_war / assumed_workload if assumed_workload > 0 else 0.0
        expected_war = rate * expected_workload
        granular = model_fv_from_expected_war(expected_war, player_type)
        rows.append(
            {
                **row,
                "incumbent_expected_six_year_war": incumbent_war,
                "outcome_quality_expected_workload": expected_workload,
                "outcome_quality_expected_six_year_war": expected_war,
                "outcome_quality_model_fv_granular": granular,
                "outcome_quality_model_fv_display": display_fv(granular),
                "outcome_quality_workload_source": source,
            }
        )
    return pl.DataFrame(rows, infer_schema_length=None).sort("player_id")


def apply_pre_mlb_three_tier_workload(
    values: pl.DataFrame,
    workload_priors: pl.DataFrame,
    *,
    pre_mlb_player_ids: set[int],
    minimum_role_players: int = 30,
) -> pl.DataFrame:
    """Apply ordered fringe/meaningful-only/established workload probabilities."""

    required = {
        "player_id", "model_player_type", "model_arrival_probability",
        "model_meaningful_role_probability", "model_established_role_probability",
        "expected_six_year_war", "hitter_six_control_year_war_if_arrived",
        "pitcher_six_control_year_war_if_arrived", "primary_position",
        "starter_probability", "reliever_probability", "model_fv_granular",
        "model_fv_display",
    }
    if missing := sorted(required - set(values.columns)):
        raise ValueError(f"Model FV values missing columns: {missing}")
    rows = []
    for row in values.iter_rows(named=True):
        player_id = int(row["player_id"])
        applicable = player_id in pre_mlb_player_ids and all(
            row[column] is not None
            for column in (
                "model_arrival_probability",
                "model_meaningful_role_probability",
                "model_established_role_probability",
            )
        )
        incumbent_war = float(row["expected_six_year_war"])
        if not applicable:
            rows.append(
                {
                    **row,
                    "incumbent_expected_six_year_war": incumbent_war,
                    "ordered_arrival_probability": None,
                    "ordered_meaningful_probability": None,
                    "ordered_established_probability": None,
                    "fringe_probability": None,
                    "meaningful_only_probability": None,
                    "established_probability": None,
                    "three_tier_expected_workload": None,
                    "three_tier_expected_six_year_war": incumbent_war,
                    "three_tier_model_fv_granular": row["model_fv_granular"],
                    "three_tier_model_fv_display": row["model_fv_display"],
                    "three_tier_workload_source": "not_pre_mlb",
                }
            )
            continue
        player_type = str(row["model_player_type"])
        arrival = min(1.0, max(0.0, float(row["model_arrival_probability"])))
        meaningful = min(
            arrival, max(0.0, float(row["model_meaningful_role_probability"]))
        )
        established = min(
            meaningful, max(0.0, float(row["model_established_role_probability"]))
        )
        tier_probability = {
            "fringe": arrival - meaningful,
            "meaningful_only": meaningful - established,
            "established": established,
        }
        if player_type == "hitter":
            tier_workload = {}
            tier_sources = {}
            for tier in tier_probability:
                tier_workload[tier], tier_sources[tier] = workload_prior(
                    workload_priors,
                    player_type="hitter",
                    outcome_tier=tier,
                    career_role="hitter",
                    minimum_role_players=minimum_role_players,
                )
            assumed_workload = 6.0 * (
                450.0 if str(row["primary_position"] or "") == "C" else 550.0
            )
            full_war = float(row["hitter_six_control_year_war_if_arrived"] or 0.0)
            source = ":".join(
                f"{tier}_{tier_sources[tier]}" for tier in tier_probability
            )
        else:
            starter = min(1.0, max(0.0, float(row["starter_probability"] or 0.0)))
            reliever = min(1.0, max(0.0, float(row["reliever_probability"] or 0.0)))
            swingman = max(0.0, 1.0 - starter - reliever)
            total_role = starter + reliever + swingman
            roles = {
                "starter": starter / total_role,
                "reliever": reliever / total_role,
                "swingman": swingman / total_role,
            }
            tier_workload = {}
            source_parts = []
            for tier in tier_probability:
                tier_workload[tier] = 0.0
                sources = set()
                for role, probability in roles.items():
                    prior, prior_source = workload_prior(
                        workload_priors,
                        player_type="pitcher",
                        outcome_tier=tier,
                        career_role=role,
                        minimum_role_players=minimum_role_players,
                    )
                    tier_workload[tier] += probability * prior
                    sources.add(prior_source)
                source_parts.append(f"{tier}_{'+'.join(sorted(sources))}")
            assumed_workload = 6.0 * (
                800.0 * roles["starter"]
                + 250.0 * roles["reliever"]
                + 450.0 * roles["swingman"]
            )
            full_war = float(row["pitcher_six_control_year_war_if_arrived"] or 0.0)
            source = ":".join(source_parts)
        expected_workload = sum(
            tier_probability[tier] * tier_workload[tier]
            for tier in tier_probability
        )
        rate = full_war / assumed_workload if assumed_workload > 0 else 0.0
        expected_war = rate * expected_workload
        granular = model_fv_from_expected_war(expected_war, player_type)
        rows.append(
            {
                **row,
                "incumbent_expected_six_year_war": incumbent_war,
                "ordered_arrival_probability": arrival,
                "ordered_meaningful_probability": meaningful,
                "ordered_established_probability": established,
                "fringe_probability": tier_probability["fringe"],
                "meaningful_only_probability": tier_probability["meaningful_only"],
                "established_probability": tier_probability["established"],
                "three_tier_expected_workload": expected_workload,
                "three_tier_expected_six_year_war": expected_war,
                "three_tier_model_fv_granular": granular,
                "three_tier_model_fv_display": display_fv(granular),
                "three_tier_workload_source": source,
            }
        )
    return pl.DataFrame(rows, infer_schema_length=None).sort("player_id")
