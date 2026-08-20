#!/usr/bin/env python
"""Run the predeclared Player Value v1 park-neutrality audit."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import date
import json
import math
import os
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.performance_season import ALL_CORE_BINS
from universal_baseball.player_value_batting_runs import build_v1_mlb_batting_reference
from universal_baseball.player_value_park_neutrality import (
    harmonic_exposure,
    one_sided_permutation_p_value,
    weighted_mean,
    weighted_slope,
)
from universal_baseball.savant import (
    project_savant_performance_rows,
    read_savant_csv_bytes,
)


REFERENCE_SEASON = 2024
CUTOFF = date(2024, 7, 15)
PERMUTATIONS = 10_000
PERMUTATION_SEED = 20_240_820


def _one(root: Path, pattern: str) -> Path:
    matches = sorted(root.rglob(pattern))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {pattern} below {root}, found {len(matches)}")
    return matches[0]


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _rounded_metrics(value: Any) -> Any:
    """Stabilize reported diagnostics below any decision-relevant precision."""

    if isinstance(value, float):
        return round(value, 12)
    if isinstance(value, dict):
        return {key: _rounded_metrics(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_rounded_metrics(item) for item in value]
    return value


def _projection_rates(profile_path: Path, reference: Any) -> pl.DataFrame:
    profile = pl.read_parquet(profile_path).select(
        "player_id", "core_bin", "baseline2_latent_probability"
    )
    keys = profile.select("player_id", "core_bin").unique()
    if keys.height != profile.height:
        raise ValueError("B2 profile contains duplicate player-bin keys")
    complete = profile.group_by("player_id").agg(
        pl.col("core_bin").n_unique().alias("bin_count"),
        pl.col("baseline2_latent_probability").sum().alias("probability_sum"),
    )
    if complete.filter(
        (pl.col("bin_count") != len(ALL_CORE_BINS))
        | ((pl.col("probability_sum") - 1.0).abs() > 1e-9)
    ).height:
        raise ValueError("B2 profiles are incomplete or do not sum to one")
    values = pl.DataFrame(
        {
            "core_bin": list(ALL_CORE_BINS),
            "pooled_bin_run_value": [
                float(reference.bin_run_values[core_bin]) for core_bin in ALL_CORE_BINS
            ],
        }
    )
    return (
        profile.join(values, on="core_bin", how="left")
        .with_columns(
            (
                pl.col("baseline2_latent_probability")
                * pl.col("pooled_bin_run_value")
            ).alias("weighted_value")
        )
        .group_by("player_id")
        .agg(pl.col("weighted_value").sum().alias("projected_value_per_core_event"))
        .with_columns(
            (
                pl.col("projected_value_per_core_event")
                * float(reference.core_event_rate_per_pa)
            ).alias("projected_raw_runs_per_pa")
        )
    )


def _game_context(root: Path) -> pl.DataFrame:
    frames: list[pl.DataFrame] = []
    for path in sorted(root.rglob("savant_*.csv")):
        projected = project_savant_performance_rows(
            read_savant_csv_bytes(path.read_bytes()), regular_season_only=True
        )
        frames.append(
            projected.select(
                "game_pk",
                pl.col("batter_mlbam_id").alias("player_id"),
                "home_team",
                "away_team",
                "batting_team",
            ).unique()
        )
    if not frames:
        raise ValueError(f"no frozen Savant captures found below {root}")
    context = pl.concat(frames, how="vertical_relaxed").unique()
    unique_keys = (
        context.group_by("game_pk", "player_id")
        .len()
        .filter(pl.col("len") == 1)
        .select("game_pk", "player_id")
    )
    context = context.join(unique_keys, on=["game_pk", "player_id"], how="inner")
    if context.select("home_team", "away_team", "batting_team").null_count().row(0) != (0, 0, 0):
        raise ValueError("player-game batting context contains null teams")
    return context


def _venue_context(root: Path) -> pl.DataFrame:
    schedule = _load_json(_one(root, "schedule_*_regular.json"))
    rows: list[dict[str, Any]] = []
    for day in schedule.get("dates") or []:
        for game in day.get("games") or []:
            venue = game.get("venue") or {}
            rows.append(
                {
                    "game_pk": int(game["gamePk"]),
                    "venue_id": int(venue["id"]),
                    "venue_name": str(venue["name"]),
                }
            )
    frame = pl.DataFrame(rows).unique()
    if frame.group_by("game_pk").len().filter(pl.col("len") != 1).height:
        raise ValueError("schedule contains duplicate game venue mappings")
    return frame


def _season_game_values(
    root: Path,
    *,
    season: int,
    projection_rates: pl.DataFrame,
    reference: Any,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    summary = pl.read_parquet(_one(root, f"current_talent_game_summary_{season}_mlb.parquet"))
    profile = pl.read_parquet(_one(root, f"current_talent_game_profile_{season}_mlb.parquet"))
    values = pl.DataFrame(
        {
            "core_bin": list(ALL_CORE_BINS),
            "pooled_bin_run_value": [
                float(reference.bin_run_values[core_bin]) for core_bin in ALL_CORE_BINS
            ],
        }
    )
    observed = (
        profile.join(values, on="core_bin", how="left")
        .with_columns(
            (pl.col("occurrence_count") * pl.col("pooled_bin_run_value")).alias(
                "observed_raw_runs"
            )
        )
        .group_by("game_pk", "player_id")
        .agg(
            pl.col("occurrence_count").sum().alias("profile_core_events"),
            pl.col("observed_raw_runs").sum(),
        )
    )
    games = (
        summary.filter(pl.col("batting_plate_appearances") > 0)
        .select(
            "game_date",
            "game_pk",
            "player_id",
            "batting_plate_appearances",
            "core_profile_event_count",
        )
        .join(observed, on=["game_pk", "player_id"], how="left")
        .with_columns(
            pl.col("profile_core_events").fill_null(0),
            pl.col("observed_raw_runs").fill_null(0.0),
        )
    )
    if games.filter(
        pl.col("profile_core_events") != pl.col("core_profile_event_count")
    ).height:
        raise ValueError(f"{season} player-game profile does not reconcile to summary")
    modeled_before_context = games.join(projection_rates, on="player_id", how="inner")
    context = _game_context(root)
    excluded_context = modeled_before_context.join(
        context.select("game_pk", "player_id"),
        on=["game_pk", "player_id"],
        how="anti",
    )
    games = (
        modeled_before_context.join(context, on=["game_pk", "player_id"], how="inner")
        .join(_venue_context(root), on="game_pk", how="left")
        .with_columns(
            pl.col("game_date").cast(pl.Date),
            (
                pl.col("projected_raw_runs_per_pa")
                * pl.col("batting_plate_appearances")
            ).alias("projected_raw_runs"),
        )
        .with_columns(
            (pl.col("observed_raw_runs") - pl.col("projected_raw_runs")).alias(
                "observed_minus_projected_runs"
            ),
            (pl.col("batting_team") == pl.col("home_team")).alias("is_home"),
        )
    )
    required_context = ("home_team", "away_team", "batting_team", "venue_id", "venue_name")
    if any(games.get_column(column).null_count() for column in required_context):
        raise ValueError(f"{season} modeled player-games lack team or venue context")
    audit = {
        "positive_pa_player_game_count": summary.filter(
            pl.col("batting_plate_appearances") > 0
        ).height,
        "b2_modeled_before_context_player_game_count": modeled_before_context.height,
        "b2_modeled_before_context_player_count": modeled_before_context.get_column(
            "player_id"
        ).n_unique(),
        "b2_modeled_before_context_pa": int(
            modeled_before_context.get_column("batting_plate_appearances").sum()
        ),
        "ambiguous_or_missing_context_player_game_count": excluded_context.height,
        "ambiguous_or_missing_context_pa": int(
            excluded_context.get_column("batting_plate_appearances").sum() or 0
        ),
        "ambiguous_or_missing_context_core_events": int(
            excluded_context.get_column("core_profile_event_count").sum() or 0
        ),
        "included_player_game_count": games.height,
        "included_player_count": games.get_column("player_id").n_unique(),
        "included_game_count": games.get_column("game_pk").n_unique(),
        "included_pa": int(games.get_column("batting_plate_appearances").sum()),
        "included_core_events": int(games.get_column("core_profile_event_count").sum()),
    }
    return games.sort("game_date", "game_pk", "player_id"), audit


def _single_team(frame: pl.DataFrame, season: int) -> pl.DataFrame:
    return (
        frame.group_by("player_id")
        .agg(
            pl.col("batting_team").n_unique().alias("team_count"),
            pl.col("batting_team").first().alias("batting_team"),
        )
        .filter(pl.col("team_count") == 1)
        .drop("team_count")
        .rename({"batting_team": f"batting_team_{season}"})
    )


def _player_split(frame: pl.DataFrame, *, home: bool, prefix: str) -> pl.DataFrame:
    return (
        frame.filter(pl.col("is_home") == home)
        .group_by("player_id", "batting_team")
        .agg(
            pl.col("batting_plate_appearances").sum().alias(f"{prefix}_pa"),
            pl.col("observed_raw_runs").sum().alias(f"{prefix}_observed_runs"),
            pl.col("projected_raw_runs").sum().alias(f"{prefix}_projected_runs"),
        )
    )


def _team_retention(
    target: pl.DataFrame,
    eligible: pl.DataFrame,
    *,
    suffix: str,
) -> pl.DataFrame:
    players = (
        target.filter(~pl.col("is_home"))
        .join(eligible.select("player_id", "batting_team"), on=["player_id", "batting_team"], how="inner")
        .group_by("player_id", "batting_team")
        .agg(
            pl.col("batting_plate_appearances").sum().alias("away_pa"),
            (pl.col("projected_raw_runs") - pl.col("observed_raw_runs"))
            .sum()
            .alias("retention_runs"),
        )
    )
    pooled = float(players.get_column("retention_runs").sum()) / float(
        players.get_column("away_pa").sum()
    )
    return (
        players.group_by("batting_team")
        .agg(
            pl.col("away_pa").sum().alias(f"away_pa_{suffix}"),
            pl.col("retention_runs").sum().alias("retention_runs"),
        )
        .with_columns(
            (
                600.0
                * (pl.col("retention_runs") / pl.col(f"away_pa_{suffix}") - pooled)
            ).alias(f"retention_residual_{suffix}")
        )
        .drop("retention_runs")
    )


def _primary_audit(source: pl.DataFrame, target: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame, dict[str, Any]]:
    source_teams = _single_team(source, 2023)
    target_teams = _single_team(target, 2024)
    home = _player_split(source, home=True, prefix="source_home")
    away = _player_split(source, home=False, prefix="source_away")
    target_away = _player_split(target, home=False, prefix="target_away")
    eligible = (
        source_teams.join(target_teams, on="player_id", how="inner")
        .filter(pl.col("batting_team_2023") == pl.col("batting_team_2024"))
        .select("player_id", pl.col("batting_team_2024").alias("batting_team"))
        .join(home, on=["player_id", "batting_team"], how="inner")
        .join(away, on=["player_id", "batting_team"], how="inner")
        .join(target_away, on=["player_id", "batting_team"], how="inner")
        .filter(
            (pl.col("source_home_pa") >= 30)
            & (pl.col("source_away_pa") >= 30)
            & (pl.col("target_away_pa") >= 60)
        )
        .with_columns(
            (
                600.0
                * (
                    pl.col("source_home_observed_runs") / pl.col("source_home_pa")
                    - pl.col("source_away_observed_runs") / pl.col("source_away_pa")
                )
            ).alias("prior_home_signal"),
            pl.struct("source_home_pa", "source_away_pa")
            .map_elements(
                lambda row: harmonic_exposure(row["source_home_pa"], row["source_away_pa"]),
                return_dtype=pl.Float64,
            )
            .alias("prior_signal_weight"),
            (
                600.0
                * (
                    pl.col("target_away_projected_runs")
                    - pl.col("target_away_observed_runs")
                )
                / pl.col("target_away_pa")
            ).alias("retention_residual_uncentered"),
        )
    )
    pre_team_eligible_player_count = eligible.height
    pre_team_eligible_away_pa = int(eligible.get_column("target_away_pa").sum())
    global_retention = weighted_mean(
        eligible.get_column("retention_residual_uncentered").to_list(),
        eligible.get_column("target_away_pa").to_list(),
    )
    eligible = eligible.with_columns(
        (pl.col("retention_residual_uncentered") - global_retention).alias(
            "retention_residual"
        )
    )
    teams = (
        eligible.group_by("batting_team")
        .agg(
            pl.len().alias("eligible_player_count"),
            pl.col("target_away_pa").sum().alias("target_away_pa"),
            (
                (pl.col("prior_home_signal") * pl.col("prior_signal_weight")).sum()
                / pl.col("prior_signal_weight").sum()
            ).alias("prior_home_signal"),
            (
                (pl.col("retention_residual") * pl.col("target_away_pa")).sum()
                / pl.col("target_away_pa").sum()
            ).alias("retention_residual_full"),
        )
        .filter(
            (pl.col("eligible_player_count") >= 5)
            & (pl.col("target_away_pa") >= 300)
        )
    )
    eligible = eligible.join(teams.select("batting_team"), on="batting_team", how="inner")
    first = _team_retention(
        target.filter(pl.col("game_date") < CUTOFF), eligible, suffix="first_half"
    )
    second = _team_retention(
        target.filter(pl.col("game_date") >= CUTOFF), eligible, suffix="second_half"
    )
    teams = teams.join(first, on="batting_team", how="inner").join(
        second, on="batting_team", how="inner"
    ).sort("batting_team")
    x = teams.get_column("prior_home_signal").to_list()
    weights = teams.get_column("target_away_pa").to_list()
    full = weighted_slope(x, teams.get_column("retention_residual_full").to_list(), weights)
    first_slope = weighted_slope(
        x, teams.get_column("retention_residual_first_half").to_list(), weights
    )
    second_slope = weighted_slope(
        x, teams.get_column("retention_residual_second_half").to_list(), weights
    )
    p_value = one_sided_permutation_p_value(
        x,
        teams.get_column("retention_residual_full").to_list(),
        weights,
        iterations=PERMUTATIONS,
        seed=PERMUTATION_SEED,
    )
    gates = {
        "at_least_20_teams": teams.height >= 20,
        "retention_slope_at_least_0_25": full.slope >= 0.25,
        "one_sided_permutation_p_at_most_0_05": p_value <= 0.05,
        "fitted_weighted_sd_at_least_1_run_per_600_pa": full.fitted_weighted_sd >= 1.0,
        "both_split_half_slopes_positive": first_slope.slope > 0 and second_slope.slope > 0,
    }
    result = {
        "eligible_player_count_before_team_minimums": pre_team_eligible_player_count,
        "eligible_2024_away_pa_before_team_minimums": pre_team_eligible_away_pa,
        "eligible_player_count": eligible.height,
        "eligible_team_count": teams.height,
        "eligible_2024_away_pa": int(eligible.get_column("target_away_pa").sum()),
        "global_projection_minus_away_observed_runs_per_600_pa_removed": global_retention,
        "full_season_weighted_line": asdict(full),
        "first_half_weighted_line": asdict(first_slope),
        "second_half_weighted_line": asdict(second_slope),
        "permutation": {
            "iterations": PERMUTATIONS,
            "seed": PERMUTATION_SEED,
            "one_sided_p_value": p_value,
        },
        "gates": gates,
        "all_gates_pass": all(gates.values()),
    }
    return eligible.sort("batting_team", "player_id"), teams, result


def _weighted_dispersion(frame: pl.DataFrame, rate_column: str, weight_column: str) -> float:
    return math.sqrt(
        float(
            frame.select(
                (
                    (pl.col(rate_column) ** 2 * pl.col(weight_column)).sum()
                    / pl.col(weight_column).sum()
                ).alias("variance")
            ).item()
        )
    )


def _secondary_audit(target: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame, dict[str, Any]]:
    pooled = float(target.get_column("observed_minus_projected_runs").sum()) / float(
        target.get_column("batting_plate_appearances").sum()
    )
    venues = (
        target.group_by("venue_id", "venue_name")
        .agg(
            pl.col("batting_plate_appearances").sum().alias("eligible_pa"),
            pl.col("observed_minus_projected_runs").sum().alias("residual_runs"),
            pl.col("game_pk").n_unique().alias("game_count"),
            pl.col("player_id").n_unique().alias("player_count"),
        )
        .with_columns(
            (600.0 * (pl.col("residual_runs") / pl.col("eligible_pa") - pooled)).alias(
                "centered_residual_runs_per_600_pa"
            )
        )
        .sort("eligible_pa", descending=True)
    )
    primary_venues = venues.filter(pl.col("eligible_pa") >= 2500)
    team_sides = (
        target.group_by("batting_team", "is_home")
        .agg(
            pl.col("batting_plate_appearances").sum().alias("eligible_pa"),
            pl.col("observed_minus_projected_runs").sum().alias("residual_runs"),
        )
        .with_columns(
            (600.0 * pl.col("residual_runs") / pl.col("eligible_pa")).alias(
                "residual_runs_per_600_pa"
            )
        )
    )
    home = team_sides.filter(pl.col("is_home")).select(
        "batting_team",
        pl.col("eligible_pa").alias("home_pa"),
        pl.col("residual_runs_per_600_pa").alias("home_residual_runs_per_600_pa"),
    )
    away = team_sides.filter(~pl.col("is_home")).select(
        "batting_team",
        pl.col("eligible_pa").alias("away_pa"),
        pl.col("residual_runs_per_600_pa").alias("away_residual_runs_per_600_pa"),
    )
    teams = home.join(away, on="batting_team", how="inner").with_columns(
        (
            pl.col("home_residual_runs_per_600_pa")
            - pl.col("away_residual_runs_per_600_pa")
        ).alias("home_minus_away_residual_runs_per_600_pa")
    ).sort("batting_team")
    largest = (
        primary_venues.with_columns(
            pl.col("centered_residual_runs_per_600_pa").abs().alias("absolute_rate")
        )
        .sort("absolute_rate", descending=True)
        .head(5)
        .drop("absolute_rate")
        .to_dicts()
    )
    result = {
        "modeled_player_count": target.get_column("player_id").n_unique(),
        "modeled_game_count": target.get_column("game_pk").n_unique(),
        "modeled_player_game_count": target.height,
        "modeled_pa": int(target.get_column("batting_plate_appearances").sum()),
        "modeled_core_events": int(target.get_column("core_profile_event_count").sum()),
        "venue_count": venues.height,
        "primary_venue_count_at_least_2500_pa": primary_venues.height,
        "primary_venue_weighted_residual_sd_runs_per_600_pa": _weighted_dispersion(
            primary_venues, "centered_residual_runs_per_600_pa", "eligible_pa"
        ),
        "largest_absolute_primary_venue_residuals": largest,
        "batting_team_count": teams.height,
        "median_absolute_team_home_away_residual_runs_per_600_pa": float(
            teams.get_column("home_minus_away_residual_runs_per_600_pa").abs().median()
        ),
        "interpretation": (
            "Realized venue and home/away effects are descriptive only; the primary "
            "prior-home retention test controls the park-correction decision."
        ),
    }
    return venues, teams, result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--b2-root", type=Path, required=True)
    parser.add_argument("--mlb-2023-root", type=Path, required=True)
    parser.add_argument("--mlb-2024-root", type=Path, required=True)
    parser.add_argument("--performance-root", type=Path, required=True)
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("docs/player-value-v1-park-neutrality-audit-result.json"),
    )
    parser.add_argument("--output-root", type=Path, default=Path("reports/generated/player-value-v1-park-neutrality-audit"))
    args = parser.parse_args()

    centering = _load_json(Path("docs/player-value-v1-mlb-centering-2024.json"))
    if centering.get("status") != "player_value_v1_mlb_centering_2024_frozen_verified":
        raise ValueError("park audit requires frozen verified numerical centering")
    reference = build_v1_mlb_batting_reference(
        pl.read_parquet(_one(args.performance_root, "batting_performance_summary_2024_mlb.parquet")),
        pl.read_parquet(_one(args.performance_root, "batting_performance_bins_2024_mlb.parquet")),
        pl.read_parquet(_one(args.performance_root, "league_bin_values_2024_mlb.parquet")),
        season=REFERENCE_SEASON,
    )
    rates = _projection_rates(_one(args.b2_root, "frozen_b2_profile.parquet"), reference)
    source, source_input_audit = _season_game_values(
        args.mlb_2023_root, season=2023, projection_rates=rates, reference=reference
    )
    target, target_input_audit = _season_game_values(
        args.mlb_2024_root, season=2024, projection_rates=rates, reference=reference
    )
    players, primary_teams, primary = _primary_audit(source, target)
    venues, secondary_teams, secondary = _secondary_audit(target)
    correction_authorized = bool(primary["all_gates_pass"])
    payload = {
        "schema_version": "0.1",
        "status": "player_value_v1_park_neutrality_audit_frozen_verified",
        "contract": "docs/player-value-v1-park-neutrality-audit-contract.md",
        "source_commit": str(os.environ.get("GITHUB_SHA") or "").strip() or None,
        "actions_run_id": int(os.environ["GITHUB_RUN_ID"]) if os.environ.get("GITHUB_RUN_ID") else None,
        "inputs": {
            "b2": {"run_id": 32099733186, "artifact_id": 9311172007},
            "mlb_2023": {"run_id": 31989561396, "artifact_id": 9274868338, "digest": "sha256:4fde9a0a8774135bcea775bb369a3c4d484d53938a818c4c2bce803878e03d54"},
            "mlb_2024": {"run_id": 32096473700, "artifact_id": 9310382371, "digest": "sha256:bdca35299b7a82130eae197987aa1d1bb0448c8ef9dc9ee6c6ba3d39e79f2efe"},
            "performance": {"run_id": 31955392482, "artifact_id": 9265954750},
            "centering_run_id": centering["materialization_run_id"],
        },
        "common_value_reference": {
            "season": reference.season,
            "core_event_rate_per_pa": reference.core_event_rate_per_pa,
            "reference_run_value_per_core_event": reference.reference_run_value_per_core_event,
            "bin_run_values": dict(reference.bin_run_values),
        },
        "season_input_audits": {
            "2023": source_input_audit,
            "2024": target_input_audit,
        },
        "primary_retained_prior_home_context": _rounded_metrics(primary),
        "secondary_realized_context_diagnostics": _rounded_metrics(secondary),
        "decision": {
            "park_correction_design_authorized": correction_authorized,
            "Rpark_frozen_zero": not correction_authorized,
            "reason": (
                "all predeclared retained-context gates passed"
                if correction_authorized
                else "at least one predeclared retained-context gate failed"
            ),
        },
        "boundary": {
            "live_savant_fetched": False,
            "realized_2024_used_as_projection_input": False,
            "b2_refit_or_reselected": False,
            "centering_changed": False,
            "park_correction_applied": False,
            "2025_data_accessed": False,
            "war_calculated": False,
        },
    }
    args.output_root.mkdir(parents=True, exist_ok=True)
    players.write_parquet(args.output_root / "eligible_player_diagnostics.parquet")
    primary_teams.write_parquet(args.output_root / "primary_team_diagnostics.parquet")
    venues.write_parquet(args.output_root / "venue_diagnostics.parquet")
    secondary_teams.write_parquet(args.output_root / "home_away_team_diagnostics.parquet")
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "primary": payload["primary_retained_prior_home_context"],
                "decision": payload["decision"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
