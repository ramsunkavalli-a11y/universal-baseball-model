"""Apply frozen adjacent-year general defense to current hitter paths."""

from __future__ import annotations

from collections.abc import Mapping
import math

import polars as pl

from universal_baseball.player_value_defense_projection import (
    GENERAL_POSITIONS,
    predict_general_range_skill,
)


CURRENT_DEFENSE_MODEL_ID = "frozen_defense_v1_u1_adjacent_year"


def build_current_general_defense_rates(
    players: pl.DataFrame,
    profiles: pl.DataFrame,
    opportunity: pl.DataFrame,
    *,
    current_season: int,
    forecast_seasons: tuple[int, ...],
    general_parameters: Mapping[str, object],
    conversion_parameters: Mapping[str, object],
) -> pl.DataFrame:
    """Produce conditional defense rates without current-team depth.

    Frozen prior-year MLB position outs are treated as defensive exposure when
    MLB-active. The hitter participation model supplies the separate probability
    of being active. Only the adjacent season is covered by the frozen defense
    validation; later horizons use the explicit neutral fallback.
    """

    if set(players.columns) != {"player_id"}:
        raise ValueError("defense players require only player_id")
    required_profile = {
        "season",
        "player_id",
        "position",
        "mlb_fielding_outs",
    }
    if missing := sorted(required_profile - set(profiles.columns)):
        raise ValueError(f"defense profiles missing fields: {missing}")
    required_opportunity = {
        "player_id",
        "season",
        "mlb_active_probability",
        "conditional_mlb_pa",
    }
    if missing := sorted(required_opportunity - set(opportunity.columns)):
        raise ValueError(f"defense opportunity missing fields: {missing}")
    years = tuple(sorted(set(int(value) for value in forecast_seasons)))
    expected_keys = {
        (int(player_id), season)
        for player_id in players.get_column("player_id")
        for season in years
    }
    opportunity_rows = opportunity.filter(pl.col("season").is_in(years))
    if set(opportunity_rows.select("player_id", "season").iter_rows()) != expected_keys:
        raise ValueError("defense opportunity does not cover every player-year")
    profile_lookup = {
        (int(row["player_id"]), str(row["position"])): row
        for row in profiles.filter(pl.col("season") == current_season).iter_rows(
            named=True
        )
    }
    opportunity_lookup = {
        (int(row["player_id"]), int(row["season"])): row
        for row in opportunity_rows.iter_rows(named=True)
    }
    conversion_by_position = conversion_parameters["parameters_by_position"]
    adjacent_season = current_season + 1
    skill_by_key: dict[tuple[int, str], tuple[float, str]] = {}
    center_by_position: dict[str, float] = {}
    for position in sorted(GENERAL_POSITIONS):
        weighted_sum = 0.0
        weight_sum = 0.0
        for player_id in players.get_column("player_id"):
            pid = int(player_id)
            profile = profile_lookup.get((pid, position))
            skill, family = predict_general_range_skill(
                profile,
                tracked_z=None,
                parameters=general_parameters,
            )
            skill_by_key[(pid, position)] = (skill, family)
            if family == "U1" and profile is not None:
                weight = (
                    float(profile["mlb_fielding_outs"])
                    * float(
                        opportunity_lookup[(pid, adjacent_season)][
                            "mlb_active_probability"
                        ]
                    )
                )
                weighted_sum += skill * weight
                weight_sum += weight
        center_by_position[position] = (
            weighted_sum / weight_sum if weight_sum > 0 else 0.0
        )
    rows: list[dict[str, object]] = []
    for player_id in players.get_column("player_id"):
        pid = int(player_id)
        adjacent_runs = 0.0
        eligible_positions = 0
        for position in sorted(GENERAL_POSITIONS):
            profile = profile_lookup.get((pid, position))
            skill, family = skill_by_key[(pid, position)]
            if family == "U1" and profile is not None:
                eligible_positions += 1
                run_rate = float(
                    conversion_by_position[position][
                        "run_rate_per_z_opportunity"
                    ]
                )
                adjacent_runs += (
                    (skill - center_by_position[position])
                    * float(profile["mlb_fielding_outs"])
                    * run_rate
                )
        if not math.isfinite(adjacent_runs):
            raise ValueError("current defense produced non-finite runs")
        for season in years:
            conditional_pa = float(
                opportunity_lookup[(pid, season)]["conditional_mlb_pa"]
            )
            covered = season == current_season + 1 and conditional_pa > 0
            runs = adjacent_runs if covered else 0.0
            rows.append(
                {
                    "player_id": pid,
                    "season": season,
                    "defense_runs_per_600": (
                        runs * 600.0 / conditional_pa if covered else 0.0
                    ),
                    "conditional_defense_runs": runs,
                    "defense_evidence_tier": (
                        "frozen_u1_adjacent_year"
                        if covered and eligible_positions
                        else (
                            "adjacent_year_neutral_no_eligible_mlb_exposure"
                            if covered
                            else "neutral_beyond_validated_adjacent_year"
                        )
                    ),
                    "defense_model_id": CURRENT_DEFENSE_MODEL_ID,
                    "defense_centering_method": (
                        "position_expected_exposure_weighted_zero"
                    ),
                    "eligible_general_positions": eligible_positions,
                    "catcher_defense_policy": "neutral_missing_native_pitch_inputs",
                }
            )
    return pl.DataFrame(rows).sort(["player_id", "season"])
