"""Transparent Phase 1 conditional WAR-rate baselines.

Skill rates are intentionally separate from future participation and workload.
The hitter baseline is Marcel-class offense plus primary-position value. The frozen
Player Value v1 baserunning and defense models may be supplied; missing components
otherwise remain league-average zero fallbacks. The pitcher baseline converts the selected five-part BF forecast to
runs, with conservative component aging based on Tango's regressed adjacent-
season curves.
"""

from __future__ import annotations

import math
from types import MappingProxyType
from typing import Mapping

import polars as pl

from universal_baseball.hitter_v2_evaluation import (
    NEUTRAL_WOBA_SCALE,
    NEUTRAL_WOBA_WEIGHTS,
)
from universal_baseball.hitter_v2_model import marcel_age_factor
from universal_baseball.pitcher_baseline import build_pitcher_component_baseline
from universal_baseball.player_value_positional_adjustment import POSITIONAL_RUNS_PER_162


HITTER_RATE_MODEL_ID = "hitter_marcel_offense_position_phase1_v1"
PITCHER_RATE_MODEL_ID = "pitcher_321_components_tango_aging_phase1_v1"
MARCEL_REGRESSION_PA = 1200.0
PITCHER_REGRESSION_BF = 200.0
PITCHER_WAR_ALLOCATION = 430.0
HITTER_RECENCY_WEIGHTS = {1: 3.0, 2: 2.0, 3: 1.0}

# Cumulative component shapes from Tango's more-regressed adjacent-pitching
# sensitivity (30% regression for K; 75% for HR/hits). Values are relative
# indices, so only target-age/current-age ratios are applied to current talent.
_TANGO_AGES = tuple(range(20, 41))
_TANGO_COMPONENT_INDEX = MappingProxyType(
    {
        "hbp": (1.745, 1.360, 1.375, 1.368, 1.396, 1.389, 1.381, 1.351, 1.401, 1.473, 1.372, 1.377, 1.293, 1.235, 1.183, 1.234, 1.193, 1.045, 1.039, 1.000, 1.139),
        "ubb": (1.248, 1.286, 1.322, 1.299, 1.297, 1.287, 1.263, 1.265, 1.264, 1.229, 1.233, 1.224, 1.188, 1.168, 1.132, 1.119, 1.127, 1.093, 1.039, 1.000, 1.029),
        "so": (0.887, 0.956, 0.993, 0.997, 0.992, 1.000, 0.998, 0.978, 0.960, 0.941, 0.913, 0.870, 0.847, 0.797, 0.770, 0.751, 0.716, 0.698, 0.693, 0.661, 0.640),
        "hr": (0.893, 1.000, 1.019, 1.060, 1.078, 1.100, 1.100, 1.112, 1.086, 1.069, 1.050, 1.062, 1.066, 1.085, 1.094, 1.118, 1.165, 1.203, 1.199, 1.149, 1.113),
    }
)

_POSITION_BY_CODE = MappingProxyType(
    {"2": "C", "3": "1B", "4": "2B", "5": "3B", "6": "SS", "7": "LF", "8": "CF", "9": "RF", "10": "DH"}
)


def _finite_positive(value: object, label: str) -> float:
    numeric = float(value)
    if not math.isfinite(numeric) or numeric <= 0:
        raise ValueError(f"{label} must be finite and positive")
    return numeric


def _weighted_variance(
    probabilities: Mapping[str, float], values: Mapping[str, float]
) -> float:
    mean = sum(probabilities[key] * values[key] for key in probabilities)
    second = sum(probabilities[key] * values[key] ** 2 for key in probabilities)
    return max(0.0, second - mean * mean)


def _age_index(component: str, age: float) -> float:
    values = _TANGO_COMPONENT_INDEX[component]
    bounded = min(40.0, max(20.0, float(age)))
    lower = int(math.floor(bounded))
    upper = int(math.ceil(bounded))
    if lower == upper:
        return values[lower - 20]
    share = bounded - lower
    return values[lower - 20] * (1.0 - share) + values[upper - 20] * share


def apply_tango_pitcher_aging(
    probabilities: Mapping[str, float],
    *,
    current_age: float | None,
    target_age: float | None,
) -> dict[str, float]:
    """Age a coherent five-part BF profile without independent clipping."""

    required = {"so", "ubb", "hbp", "hr", "other"}
    if set(probabilities) != required:
        raise ValueError("pitcher probability keys differ from five-part profile")
    values = {key: float(value) for key, value in probabilities.items()}
    if any(not math.isfinite(value) or value < 0 for value in values.values()):
        raise ValueError("pitcher probabilities must be finite and nonnegative")
    if not math.isclose(sum(values.values()), 1.0, abs_tol=1e-9):
        raise ValueError("pitcher probabilities must sum to one")
    if current_age is None or target_age is None:
        return values
    adjusted = {"other": values["other"]}
    for component in ("so", "ubb", "hbp", "hr"):
        multiplier = _age_index(component, target_age) / _age_index(component, current_age)
        adjusted[component] = values[component] * multiplier
    total = sum(adjusted.values())
    return {key: value / total for key, value in adjusted.items()}


def _hitter_components(frame: pl.DataFrame) -> pl.DataFrame:
    required = {
        "season", "player_id", "batting_plate_appearances", "batting_hits",
        "batting_doubles", "batting_triples", "batting_home_runs",
        "batting_base_on_balls", "batting_intentional_walks", "batting_hit_by_pitch",
    }
    if missing := sorted(required - set(frame.columns)):
        raise ValueError(f"hitter component history missing columns: {missing}")
    result = frame.group_by("season", "player_id").agg(
        *(pl.col(column).sum().alias(column) for column in required - {"season", "player_id"})
    ).with_columns(
        (pl.col("batting_base_on_balls") - pl.col("batting_intentional_walks")).alias("ubb"),
        (pl.col("batting_hits") - pl.col("batting_doubles") - pl.col("batting_triples") - pl.col("batting_home_runs")).alias("single"),
        pl.col("batting_doubles").alias("double"),
        pl.col("batting_triples").alias("triple"),
        pl.col("batting_home_runs").alias("hr"),
        pl.col("batting_hit_by_pitch").alias("hbp"),
    ).with_columns(
        (pl.col("batting_plate_appearances") - pl.sum_horizontal("ubb", "hbp", "single", "double", "triple", "hr")).alias("other")
    )
    counts = ("ubb", "hbp", "single", "double", "triple", "hr", "other")
    if result.filter(pl.any_horizontal(*(pl.col(column) < 0 for column in counts))).height:
        raise ValueError("hitter component history has invalid event accounting")
    return result


def _position_runs_per_600(position_code: str | None) -> tuple[float, str]:
    code = str(position_code or "")
    if code == "O":
        return float(sum(POSITIONAL_RUNS_PER_162[p] for p in ("LF", "CF", "RF")) / 3.0), "OF"
    position = _POSITION_BY_CODE.get(code)
    if position is None:
        return 0.0, "unknown_average"
    return float(POSITIONAL_RUNS_PER_162[position]), position


def build_hitter_conditional_war_rates(
    players: pl.DataFrame,
    history: pl.DataFrame,
    *,
    current_season: int,
    forecast_seasons: tuple[int, ...],
    reference_plate_appearances: int,
    runs_per_win: float,
    affiliated_profiles: pl.DataFrame | None = None,
    baserunning_rates: pl.DataFrame | None = None,
    defense_rates: pl.DataFrame | None = None,
) -> pl.DataFrame:
    """Build universal conditional hitter WAR/600 rates."""

    if set(players.columns) != {"player_id", "age_years", "position_code"}:
        raise ValueError("hitter players require player_id, age_years, and position_code")
    rpw = _finite_positive(runs_per_win, "runs_per_win")
    reference_pa = _finite_positive(reference_plate_appearances, "reference_plate_appearances")
    components = _hitter_components(history).filter(
        pl.col("season").is_between(current_season - 2, current_season)
    ).with_columns(
        (current_season - pl.col("season")).replace_strict(
            {0: 3.0, 1: 2.0, 2: 1.0}, return_dtype=pl.Float64
        ).alias("weight")
    )
    event_columns = ("ubb", "hbp", "single", "double", "triple", "hr", "other")
    reference = components.filter(pl.col("season") == current_season - 1)
    reference_total = float(reference.get_column("batting_plate_appearances").sum())
    if reference_total <= 0:
        raise ValueError("hitter rates require a completed reference season")
    prior = {column: float(reference.get_column(column).sum()) / reference_total for column in event_columns}
    weighted = components.group_by("player_id").agg(
        (pl.col("batting_plate_appearances") * pl.col("weight")).sum().alias("weighted_pa"),
        *((pl.col(column) * pl.col("weight")).sum().alias(f"weighted_{column}") for column in event_columns),
    )
    joined = players.join(weighted, on="player_id", how="left")
    if affiliated_profiles is not None:
        joined = joined.join(affiliated_profiles, on="player_id", how="left", validate="1:1")
    woba_weight = {
        "ubb": NEUTRAL_WOBA_WEIGHTS["UBB"], "hbp": NEUTRAL_WOBA_WEIGHTS["HBP"],
        "single": NEUTRAL_WOBA_WEIGHTS["1B"], "double": NEUTRAL_WOBA_WEIGHTS["2B"],
        "triple": NEUTRAL_WOBA_WEIGHTS["3B"], "hr": NEUTRAL_WOBA_WEIGHTS["HR"], "other": 0.0,
    }
    reference_woba = sum(prior[key] * woba_weight[key] for key in event_columns)
    replacement_runs = 570.0 * rpw * 600.0 / reference_pa
    baserunning_lookup: dict[tuple[int, int], dict[str, object]] = {}
    if baserunning_rates is not None:
        required_baserunning = {
            "player_id", "season", "baserunning_runs_per_600",
            "baserunning_evidence_tier", "baserunning_model_id",
        }
        if missing := sorted(required_baserunning - set(baserunning_rates.columns)):
            raise ValueError(f"baserunning rates missing columns: {missing}")
        if baserunning_rates.group_by("player_id", "season").len().filter(
            pl.col("len") != 1
        ).height:
            raise ValueError("baserunning rates violate player-season grain")
        baserunning_lookup = {
            (int(row["player_id"]), int(row["season"])): row
            for row in baserunning_rates.iter_rows(named=True)
        }
        expected_keys = {
            (int(player_id), int(season))
            for player_id in players.get_column("player_id")
            for season in forecast_seasons
        }
        if set(baserunning_lookup) != expected_keys:
            raise ValueError("baserunning rates do not exactly cover hitter player-years")
    defense_lookup: dict[tuple[int, int], dict[str, object]] = {}
    if defense_rates is not None:
        required_defense = {
            "player_id", "season", "defense_runs_per_600",
            "defense_evidence_tier", "defense_model_id",
        }
        if missing := sorted(required_defense - set(defense_rates.columns)):
            raise ValueError(f"defense rates missing columns: {missing}")
        if defense_rates.group_by("player_id", "season").len().filter(
            pl.col("len") != 1
        ).height:
            raise ValueError("defense rates violate player-season grain")
        defense_lookup = {
            (int(row["player_id"]), int(row["season"])): row
            for row in defense_rates.iter_rows(named=True)
        }
        expected_keys = {
            (int(player_id), int(season))
            for player_id in players.get_column("player_id")
            for season in forecast_seasons
        }
        if set(defense_lookup) != expected_keys:
            raise ValueError("defense rates do not exactly cover hitter player-years")
    rows: list[dict[str, object]] = []
    for row in joined.iter_rows(named=True):
        mlb_evidence = float(row.get("weighted_pa") or 0.0)
        affiliated_evidence = float(row.get("weighted_affiliated_exposure") or 0.0)
        if mlb_evidence > 0:
            base = {
                key: (float(row.get(f"weighted_{key}") or 0.0) + MARCEL_REGRESSION_PA * prior[key])
                / (mlb_evidence + MARCEL_REGRESSION_PA)
                for key in event_columns
            }
            evidence = mlb_evidence
            reliability = mlb_evidence / (mlb_evidence + MARCEL_REGRESSION_PA)
            evidence_tier = "mlb_history"
        elif affiliated_evidence > 0:
            base = {key: float(row[f"p_{key}"]) for key in event_columns}
            evidence = affiliated_evidence
            reliability = float(row["affiliated_reliability"])
            evidence_tier = "affiliated_translated"
        else:
            base = dict(prior)
            evidence = 0.0
            reliability = 0.0
            evidence_tier = "population_prior"
        position_runs, position = _position_runs_per_600(row["position_code"])
        for season in forecast_seasons:
            age = None if row["age_years"] is None else float(row["age_years"]) + season - current_season
            factor = marcel_age_factor(age)
            aged_raw = {key: value * (factor if key != "other" else 1.0) for key, value in base.items()}
            denominator = sum(aged_raw.values())
            aged = {key: value / denominator for key, value in aged_raw.items()}
            woba = sum(aged[key] * woba_weight[key] for key in event_columns)
            batting_runs = (woba - reference_woba) * 600.0 / NEUTRAL_WOBA_SCALE
            event_run_variance = _weighted_variance(
                aged,
                {key: woba_weight[key] / NEUTRAL_WOBA_SCALE for key in event_columns},
            )
            posterior_concentration = (
                evidence / reliability if reliability > 0 else MARCEL_REGRESSION_PA
            )
            baserunning = baserunning_lookup.get((int(row["player_id"]), int(season)))
            baserunning_runs = (
                float(baserunning["baserunning_runs_per_600"])
                if baserunning is not None else 0.0
            )
            defense = defense_lookup.get((int(row["player_id"]), int(season)))
            defense_runs = (
                float(defense["defense_runs_per_600"])
                if defense is not None else 0.0
            )
            war = (
                batting_runs + baserunning_runs + defense_runs
                + position_runs + replacement_runs
            ) / rpw
            rows.append({
                "player_id": int(row["player_id"]), "season": int(season),
                "conditional_war_per_600_pa": war,
                "batting_runs_per_600": batting_runs,
                "baserunning_runs_per_600": baserunning_runs,
                "baserunning_evidence_tier": (
                    str(baserunning["baserunning_evidence_tier"])
                    if baserunning is not None else "population_neutral"
                ),
                "baserunning_model_id": (
                    str(baserunning["baserunning_model_id"])
                    if baserunning is not None else "league_average_zero_fallback"
                ),
                "defense_runs_per_600": defense_runs,
                "defense_evidence_tier": (
                    str(defense["defense_evidence_tier"])
                    if defense is not None else "population_neutral"
                ),
                "defense_model_id": (
                    str(defense["defense_model_id"])
                    if defense is not None else "league_average_zero_fallback"
                ),
                "positional_runs_per_600": position_runs,
                "replacement_runs_per_600": replacement_runs,
                "primary_position": position, "target_age": age,
                "weighted_history_pa": evidence,
                "reliability": reliability,
                "posterior_concentration": posterior_concentration,
                "event_run_variance": event_run_variance,
                "posterior_run_rate_variance": (
                    event_run_variance / (posterior_concentration + 1.0)
                ),
                "evidence_tier": evidence_tier,
                "talent_model_id": HITTER_RATE_MODEL_ID,
                **{f"predicted_{key}_rate": aged[key] for key in event_columns},
                "missing_component_policy": (
                    "none"
                    if baserunning_rates is not None and defense_rates is not None
                    else (
                        "league_average_defense"
                        if baserunning_rates is not None
                        else "league_average_defense_and_baserunning"
                    )
                ),
            })
    return pl.DataFrame(rows).sort(["player_id", "season"])


def build_pitcher_conditional_war_rates(
    players: pl.DataFrame,
    history: pl.DataFrame,
    *,
    current_season: int,
    forecast_seasons: tuple[int, ...],
    reference_batters_faced: int,
    runs_per_win: float,
    affiliated_profiles: pl.DataFrame | None = None,
) -> pl.DataFrame:
    """Build universal conditional pitcher WAR/800 BF rates."""

    if set(players.columns) != {"player_id", "age_years"}:
        raise ValueError("pitcher players require player_id and age_years")
    rpw = _finite_positive(runs_per_win, "runs_per_win")
    reference_bf = _finite_positive(reference_batters_faced, "reference_batters_faced")
    required = {
        "season", "player_id", "pitching_games_played", "pitching_games_started",
        "pitching_batters_faced", "pitching_strike_outs", "pitching_base_on_balls",
        "pitching_intentional_walks", "pitching_hit_batsmen", "pitching_home_runs",
    }
    if missing := sorted(required - set(history.columns)):
        raise ValueError(f"pitcher component history missing columns: {missing}")
    standardized = history.group_by("season", "player_id").agg(
        pl.col("pitching_games_played").sum().alias("pitching_games"),
        pl.col("pitching_games_started").sum().alias("pitching_starts"),
        pl.col("pitching_batters_faced").sum().alias("pitching_bf"),
        pl.col("pitching_strike_outs").sum().alias("pitching_so"),
        (pl.col("pitching_base_on_balls").sum() - pl.col("pitching_intentional_walks").sum()).alias("pitching_ubb"),
        pl.col("pitching_hit_batsmen").sum().alias("pitching_hbp"),
        pl.col("pitching_home_runs").sum().alias("pitching_hr"),
    )
    base = build_pitcher_component_baseline(
        players.select("player_id"), standardized,
        forecast_season=current_season + 1,
        regression_bf=PITCHER_REGRESSION_BF,
    )
    reference = standardized.filter(pl.col("season") == current_season - 1)
    total_bf = float(reference.get_column("pitching_bf").sum())
    reference_rates = {
        key: float(reference.get_column(column).sum()) / total_bf
        for key, column in {"so": "pitching_so", "ubb": "pitching_ubb", "hbp": "pitching_hbp", "hr": "pitching_hr"}.items()
    }
    reference_rates["other"] = 1.0 - sum(reference_rates.values())
    known_weight_sum = (
        reference_rates["ubb"] * NEUTRAL_WOBA_WEIGHTS["UBB"]
        + reference_rates["hbp"] * NEUTRAL_WOBA_WEIGHTS["HBP"]
        + reference_rates["hr"] * NEUTRAL_WOBA_WEIGHTS["HR"]
    )
    other_weight = (0.3188 - known_weight_sum) / reference_rates["other"]
    weights = {"so": 0.0, "ubb": NEUTRAL_WOBA_WEIGHTS["UBB"], "hbp": NEUTRAL_WOBA_WEIGHTS["HBP"], "hr": NEUTRAL_WOBA_WEIGHTS["HR"], "other": other_weight}
    replacement_runs = PITCHER_WAR_ALLOCATION * rpw * 800.0 / reference_bf
    joined = players.join(base, on="player_id", how="left", validate="1:1")
    if affiliated_profiles is not None:
        joined = joined.join(affiliated_profiles, on="player_id", how="left", validate="1:1")
    rows: list[dict[str, object]] = []
    for row in joined.iter_rows(named=True):
        mlb_evidence = float(row["weighted_history_bf"])
        affiliated_evidence = float(row.get("weighted_affiliated_exposure") or 0.0)
        if mlb_evidence > 0:
            probabilities = {key: float(row[f"predicted_{key}_rate"]) for key in ("so", "ubb", "hbp", "hr", "other")}
            evidence = mlb_evidence
            reliability = float(row["reliability"])
            evidence_tier = "mlb_history"
        elif affiliated_evidence > 0:
            probabilities = {key: float(row[f"p_{key}"]) for key in ("so", "ubb", "hbp", "hr", "other")}
            evidence = affiliated_evidence
            reliability = float(row["affiliated_reliability"])
            evidence_tier = "affiliated_translated"
        else:
            probabilities = {key: float(row[f"predicted_{key}_rate"]) for key in ("so", "ubb", "hbp", "hr", "other")}
            evidence = 0.0
            reliability = 0.0
            evidence_tier = "population_prior"
        current_age = None if row["age_years"] is None else float(row["age_years"])
        for season in forecast_seasons:
            target_age = None if current_age is None else current_age + season - current_season
            aged = apply_tango_pitcher_aging(probabilities, current_age=current_age, target_age=target_age)
            woba_allowed = sum(aged[key] * weights[key] for key in aged)
            runs_above_average = -(woba_allowed - 0.3188) * 800.0 / NEUTRAL_WOBA_SCALE
            event_run_variance = _weighted_variance(
                aged,
                {key: weights[key] / NEUTRAL_WOBA_SCALE for key in aged},
            )
            posterior_concentration = (
                evidence / reliability if reliability > 0 else PITCHER_REGRESSION_BF
            )
            war = (runs_above_average + replacement_runs) / rpw
            rows.append({
                "player_id": int(row["player_id"]), "season": int(season),
                "conditional_war_per_800_bf": war,
                "pitching_runs_above_average_per_800": runs_above_average,
                "replacement_runs_per_800": replacement_runs,
                "target_age": target_age,
                "weighted_history_bf": evidence,
                "reliability": reliability,
                "posterior_concentration": posterior_concentration,
                "event_run_variance": event_run_variance,
                "posterior_run_rate_variance": (
                    event_run_variance / (posterior_concentration + 1.0)
                ),
                "evidence_tier": evidence_tier,
                "talent_model_id": PITCHER_RATE_MODEL_ID,
                "aging_source": "tango_adjacent_pitching_regressed_part2",
                **{f"predicted_{key}_rate": aged[key] for key in aged},
            })
    return pl.DataFrame(rows).sort(["player_id", "season"])
