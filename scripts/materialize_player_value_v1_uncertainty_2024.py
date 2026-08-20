#!/usr/bin/env python
"""Materialize deterministic Player Value v1 forecast intervals."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.performance_season import ALL_CORE_BINS
from universal_baseball.player_value_batting_runs import build_v1_mlb_batting_reference
from universal_baseball.player_value_defense_projection import (
    CATCHER_OPPORTUNITY_COMPONENT_KEYS,
)
from universal_baseball.player_value_uncertainty import (
    CATCHER_MSE,
    GENERAL_RANGE_MSE,
    MASTER_SEED,
    NB2_ALPHA,
    SIMULATION_DRAWS,
    UNCERTAINTY_ID,
    defense_run_variance_at_expected_pa,
    simulate_player_uncertainty,
    structural_zero_uncertainty,
)


EXPECTED_PLAYER_COUNT = 3051
EXPECTED_STRUCTURAL_ZERO_COUNT = 6
TOLERANCE = 1e-10


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _one_row_by_player(frame: pl.DataFrame, *, label: str) -> dict[int, dict[str, Any]]:
    if frame.is_empty() or frame.group_by("player_id").len().filter(pl.col("len") != 1).height:
        raise ValueError(f"{label} must have exactly one row per player")
    return {int(row["player_id"]): row for row in frame.iter_rows(named=True)}


def _b2_profiles(path: Path) -> tuple[dict[int, dict[str, Any]], dict[str, Any]]:
    frame = pl.read_parquet(path)
    required = {
        "player_id",
        "core_bin",
        "baseline2_latent_probability",
        "baseline2_effective_core_events",
        "prior_strength_core_events",
    }
    if not required.issubset(frame.columns):
        raise ValueError("B2 profile columns changed")
    profiles: dict[int, dict[str, Any]] = {}
    for player_id, group in frame.group_by("player_id", maintain_order=False):
        pid = int(player_id[0])
        if group.height != len(ALL_CORE_BINS):
            raise ValueError(f"B2 profile row count changed for {pid}")
        by_bin = {
            str(row["core_bin"]): float(row["baseline2_latent_probability"])
            for row in group.iter_rows(named=True)
        }
        if set(by_bin) != set(ALL_CORE_BINS) or abs(sum(by_bin.values()) - 1.0) > 1e-9:
            raise ValueError(f"B2 profile simplex changed for {pid}")
        effective = group.get_column("baseline2_effective_core_events").unique()
        prior = group.get_column("prior_strength_core_events").unique()
        if len(effective) != 1 or len(prior) != 1:
            raise ValueError(f"B2 evidence fields vary within player {pid}")
        profiles[pid] = {
            "probabilities": [by_bin[core_bin] for core_bin in ALL_CORE_BINS],
            "effective_core_events": float(effective.item()),
            "prior_strength_core_events": float(prior.item()),
        }
    return profiles, {
        "player_count": len(profiles),
        "profile_row_count": frame.height,
        "sha256": _sha256(path),
    }


def _playing_time(
    scored_path: Path, coefficients_path: Path
) -> tuple[dict[int, dict[str, Any]], dict[str, Any]]:
    scored = pl.read_parquet(scored_path)
    by_id = _one_row_by_player(scored, label="Playing Time scored surface")
    coefficients = pl.read_parquet(coefficients_path)
    alpha_rows = coefficients.filter(
        (pl.col("component") == "positive_truncated_nb2") & (pl.col("feature") == "alpha")
    )
    if alpha_rows.height != 1:
        raise ValueError("Playing Time NB2 alpha row changed")
    alpha = float(alpha_rows.item(0, "coefficient"))
    if abs(alpha - NB2_ALPHA) > 1e-12:
        raise ValueError(f"Playing Time NB2 alpha changed: {alpha}")
    return by_id, {
        "player_count": len(by_id),
        "nb2_alpha": alpha,
        "scored_sha256": _sha256(scored_path),
        "coefficients_sha256": _sha256(coefficients_path),
    }


def _batting_reference(root: Path):
    return build_v1_mlb_batting_reference(
        pl.read_parquet(root / "tables/batting_performance_summary_2024_mlb.parquet"),
        pl.read_parquet(root / "tables/batting_performance_bins_2024_mlb.parquet"),
        pl.read_parquet(root / "tables/league_bin_values_2024_mlb.parquet"),
        season=2024,
    )


def _catcher_opportunities(path: Path) -> tuple[dict[int, dict[str, Any]], dict[str, Any]]:
    frame = pl.read_parquet(path).filter(
        (pl.col("source_year") == 2023) & (pl.col("target_year") == 2024)
    )
    rows: dict[int, dict[str, Any]] = {}
    reverse_keys = {value: key for key, value in CATCHER_OPPORTUNITY_COMPONENT_KEYS.items()}
    for row in frame.iter_rows(named=True):
        source_component = str(row["component"])
        if source_component not in reverse_keys:
            raise ValueError(f"unexpected catcher opportunity component: {source_component}")
        pid = int(row["player_id"])
        component = reverse_keys[source_component]
        if component in rows.setdefault(pid, {}):
            raise ValueError("duplicate catcher opportunity row")
        rows[pid][component] = row
    return rows, {
        "player_count": len(rows),
        "row_count": frame.height,
        "sha256": _sha256(path),
    }


def _distribution(series: pl.Series) -> dict[str, float]:
    return {
        "minimum": float(series.min()),
        "p05": float(series.quantile(0.05, interpolation="linear")),
        "median": float(series.median()),
        "mean": float(series.mean()),
        "p95": float(series.quantile(0.95, interpolation="linear")),
        "maximum": float(series.max()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--final-table", type=Path, required=True)
    parser.add_argument("--final-json", type=Path, required=True)
    parser.add_argument("--b2-profile", type=Path, required=True)
    parser.add_argument("--playing-time-scored", type=Path, required=True)
    parser.add_argument("--playing-time-coefficients", type=Path, required=True)
    parser.add_argument("--mlb-performance-root", type=Path, required=True)
    parser.add_argument("--catcher-opportunities", type=Path, required=True)
    parser.add_argument(
        "--defense-conversion",
        type=Path,
        default=Path("docs/player-value-v1-defense-native-run-conversion-parameters.json"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("docs/player-value-v1-uncertainty-2024.json"),
    )
    parser.add_argument(
        "--output-table",
        type=Path,
        default=Path("reports/generated/player-value-v1-uncertainty-2024.parquet"),
    )
    args = parser.parse_args()

    final = pl.read_parquet(args.final_table).sort("rank")
    final_record = _load_json(args.final_json)
    if (
        final.height != EXPECTED_PLAYER_COUNT
        or final.get_column("player_id").n_unique() != EXPECTED_PLAYER_COUNT
        or final.get_column("rank").to_list() != list(range(1, EXPECTED_PLAYER_COUNT + 1))
    ):
        raise ValueError("final Player Value population/rank changed")
    if final_record.get("status") != "player_value_v1_final_2024_frozen_verified":
        raise ValueError("final Player Value record is not frozen and verified")
    if abs(float(final.get_column("war").sum()) - float(final_record["aggregate"]["war"])) > TOLERANCE:
        raise ValueError("final table aggregate WAR differs from frozen JSON")

    b2, b2_audit = _b2_profiles(args.b2_profile)
    playing_time, pt_audit = _playing_time(
        args.playing_time_scored, args.playing_time_coefficients
    )
    reference = _batting_reference(args.mlb_performance_root)
    catcher, catcher_audit = _catcher_opportunities(args.catcher_opportunities)
    conversion = _load_json(args.defense_conversion)
    general_run_rates = {
        position: float(values["run_rate_per_z_opportunity"])
        for position, values in conversion["general_range"]["parameters_by_position"].items()
    }
    catcher_run_rates = {
        component: float(conversion[f"catcher_{component}"]["run_rate_per_z_opportunity"])
        for component in ("throwing", "blocking", "framing")
    }
    centered_values = [
        float(reference.bin_run_values[core_bin])
        - float(reference.reference_run_value_per_core_event)
        for core_bin in ALL_CORE_BINS
    ]

    rows: list[dict[str, Any]] = []
    max_pt_delta = 0.0
    max_point_identity_delta = 0.0
    max_batting_delta = 0.0
    max_share_residual = 0.0
    for final_row in final.iter_rows(named=True):
        pid = int(final_row["player_id"])
        expected_pa = float(final_row["projected_expected_mlb_pa"])
        point_war = float(final_row["war"])
        point_rar = float(final_row["runs_above_replacement"])
        rpw = float(final_row["runs_per_win"])
        max_point_identity_delta = max(max_point_identity_delta, abs(point_rar / rpw - point_war))
        structural_zero = bool(final_row["outside_snapshot_zero_exposure"])
        if structural_zero:
            if expected_pa != 0.0 or point_rar != 0.0 or point_war != 0.0:
                raise ValueError(f"structural-zero row changed: {pid}")
            uncertainty = structural_zero_uncertainty()
            evidence = {
                "participation_probability": 0.0,
                "positive_truncated_mean_pa": 0.0,
                "b2_effective_core_events": 0.0,
                "b2_prior_strength_core_events": 0.0,
                "b2_posterior_concentration": 0.0,
                "defense_variance_at_expected_pa_runs2": 0.0,
            }
        else:
            if expected_pa <= 0.0 or pid not in playing_time or pid not in b2:
                raise ValueError(f"positive final row missing uncertainty input: {pid}")
            pt = playing_time[pid]
            predicted_expected = float(pt["predicted_expected_mlb_pa"])
            identity_expected = float(pt["predicted_any_mlb_pa_probability"]) * float(
                pt["predicted_positive_mlb_pa_mean"]
            )
            pt_delta = max(abs(predicted_expected - expected_pa), abs(identity_expected - expected_pa))
            max_pt_delta = max(max_pt_delta, pt_delta)
            if pt_delta > TOLERANCE:
                raise ValueError(f"Playing Time identity changed for {pid}: {pt_delta}")
            profile = b2[pid]
            probabilities = profile["probabilities"]
            batting_reproduction = (
                expected_pa
                * float(reference.core_event_rate_per_pa)
                * sum(p * value for p, value in zip(probabilities, centered_values, strict=True))
            )
            batting_delta = abs(batting_reproduction - float(final_row["batting_runs"]))
            max_batting_delta = max(max_batting_delta, batting_delta)
            if batting_delta > TOLERANCE:
                raise ValueError(f"batting point reproduction changed for {pid}: {batting_delta}")
            defense_variance = defense_run_variance_at_expected_pa(
                final_row=final_row,
                catcher_opportunities=catcher.get(pid, {}),
                general_run_rates=general_run_rates,
                catcher_run_rates=catcher_run_rates,
            )
            concentration = float(profile["effective_core_events"]) + float(
                profile["prior_strength_core_events"]
            )
            uncertainty = simulate_player_uncertainty(
                player_id=pid,
                point_war=point_war,
                point_runs_above_replacement=point_rar,
                expected_pa=expected_pa,
                participation_probability=pt["predicted_any_mlb_pa_probability"],
                positive_truncated_mean=pt["predicted_positive_mlb_pa_mean"],
                runs_per_win=rpw,
                batting_probabilities=probabilities,
                centered_bin_run_values=centered_values,
                core_event_rate_per_pa=reference.core_event_rate_per_pa,
                batting_posterior_concentration=concentration,
                defense_variance_at_expected_pa=defense_variance,
            )
            share_sum = (
                uncertainty.playing_time_variance_share
                + uncertainty.batting_variance_share
                + uncertainty.defense_variance_share
            )
            if uncertainty.total_variance_war2 > 0.0:
                max_share_residual = max(max_share_residual, abs(share_sum - 1.0))
            evidence = {
                "participation_probability": float(pt["predicted_any_mlb_pa_probability"]),
                "positive_truncated_mean_pa": float(pt["predicted_positive_mlb_pa_mean"]),
                "b2_effective_core_events": float(profile["effective_core_events"]),
                "b2_prior_strength_core_events": float(profile["prior_strength_core_events"]),
                "b2_posterior_concentration": concentration,
                "defense_variance_at_expected_pa_runs2": defense_variance,
            }
        values = asdict(uncertainty)
        if not (
            values["war_p025"]
            <= values["war_p10"]
            <= values["median_war"]
            <= values["war_p90"]
            <= values["war_p975"]
        ):
            raise ValueError(f"interval nesting failed for {pid}")
        rows.append(
            {
                "player_id": pid,
                "rank": int(final_row["rank"]),
                "point_war": point_war,
                "projected_expected_mlb_pa": expected_pa,
                "outside_snapshot_zero_exposure": structural_zero,
                **evidence,
                **values,
                "defense_families_json": str(final_row["defense_families_json"]),
                "independent_baserunning_skill_variance_modeled": False,
                "future_position_mix_variance_modeled": False,
                "cross_component_covariance_modeled": False,
            }
        )

    table = pl.DataFrame(rows).sort("rank")
    if table.height != EXPECTED_PLAYER_COUNT or table.get_column("player_id").n_unique() != EXPECTED_PLAYER_COUNT:
        raise ValueError("uncertainty output population changed")
    structural = table.filter(pl.col("outside_snapshot_zero_exposure"))
    if structural.height != EXPECTED_STRUCTURAL_ZERO_COUNT or structural.get_column(
        "interval_95_width"
    ).abs().max() != 0.0:
        raise ValueError("structural-zero interval rows changed")
    if max_share_residual > TOLERANCE:
        raise ValueError("component variance shares do not sum to one")
    numeric = table.select(pl.selectors.numeric())
    if any(not math.isfinite(float(value)) for value in numeric.to_numpy().ravel()):
        raise ValueError("uncertainty table contains non-finite values")

    top_25 = table.head(25).select(
        "rank",
        "player_id",
        "point_war",
        "war_p025",
        "war_p10",
        "median_war",
        "war_p90",
        "war_p975",
    ).to_dicts()
    result = {
        "schema_version": "0.1",
        "status": "player_value_v1_forecast_uncertainty_2024_frozen_verified",
        "contract": "docs/player-value-v1-uncertainty-contract.md",
        "uncertainty_id": UNCERTAINTY_ID,
        "reference_season": 2024,
        "source_commit": str(os.environ.get("GITHUB_SHA") or "").strip() or None,
        "actions_run_id": int(os.environ["GITHUB_RUN_ID"]) if os.environ.get("GITHUB_RUN_ID") else None,
        "population": {
            "player_count": table.height,
            "structural_zero_count": structural.height,
            "nonstructural_count": table.height - structural.height,
        },
        "simulation": {
            "draws_per_player": SIMULATION_DRAWS,
            "master_seed": MASTER_SEED,
            "bit_generator": "PCG64",
            "player_seed": "SeedSequence([20240820, player_id])",
            "playing_time_distribution": "Bernoulli hurdle + zero-truncated NB2",
            "nb2_alpha": NB2_ALPHA,
            "batting_distribution": "moment-matched normal Dirichlet-multinomial",
            "defense_distribution": "independent normal native-z residuals",
        },
        "aggregate": {
            "point_war": float(table.get_column("point_war").sum()),
            "simulated_mean_war": float(table.get_column("simulated_mean_war").sum()),
            "median_war": float(table.get_column("median_war").sum()),
            "median_absolute_simulated_mean_minus_point_war": float(
                (table.get_column("simulated_mean_war") - table.get_column("point_war")).abs().median()
            ),
            "zero_width_80_player_count": int(table.filter(pl.col("interval_80_width") == 0.0).height),
            "zero_width_95_player_count": int(table.filter(pl.col("interval_95_width") == 0.0).height),
        },
        "distributions": {
            "interval_80_width_war": _distribution(table.get_column("interval_80_width")),
            "interval_95_width_war": _distribution(table.get_column("interval_95_width")),
            "playing_time_variance_share": _distribution(table.get_column("playing_time_variance_share")),
            "batting_variance_share": _distribution(table.get_column("batting_variance_share")),
            "defense_variance_share": _distribution(table.get_column("defense_variance_share")),
        },
        "top_25": top_25,
        "qa": {
            "maximum_playing_time_identity_delta_pa": max_pt_delta,
            "maximum_point_war_identity_delta": max_point_identity_delta,
            "maximum_batting_point_reproduction_delta_runs": max_batting_delta,
            "maximum_variance_share_sum_residual": max_share_residual,
            "all_3051_rows_preserved": True,
            "point_rank_and_war_unchanged": True,
            "six_structural_zero_intervals_preserved": True,
            "intervals_nested_and_finite": True,
            "tolerance": TOLERANCE,
        },
        "variance_sources": {
            "general_range_mse": GENERAL_RANGE_MSE,
            "catcher_mse": CATCHER_MSE,
            "modeled": [
                "playing_time_hurdle_and_positive_count",
                "batting_finite_season_core_event_outcomes",
                "batting_b2_posterior_profile",
                "defense_native_skill_residuals",
            ],
            "not_modeled": [
                "independent_baserunning_skill_error",
                "future_position_and_dh_mix_error",
                "park_centering_replacement_and_rpw_parameter_error",
                "source_revision_error",
                "cross_component_covariance",
            ],
        },
        "inputs": {
            "final_table": {"run_id": 32385002209, "artifact_id": 9412571491, "sha256": _sha256(args.final_table)},
            "final_json": {"sha256": _sha256(args.final_json)},
            "b2": {"run_id": 32099733186, "artifact_id": 9311172007, **b2_audit},
            "playing_time": {"run_id": 32142089669, "artifact_id": 9326300207, **pt_audit},
            "mlb_performance": {"run_id": 31955392482, "artifact_id": 9265954750},
            "catcher_opportunities": {"run_id": 32269076231, "artifact_id": 9371426672, **catcher_audit},
            "defense_conversion_sha256": _sha256(args.defense_conversion),
        },
        "boundary": {
            "point_model_changed": False,
            "ranking_changed": False,
            "upstream_refit_or_reselection": False,
            "2025_outcomes_accessed": False,
            "interval_driven_cap_or_floor": False,
        },
    }
    args.output_table.parent.mkdir(parents=True, exist_ok=True)
    table.write_parquet(args.output_table, compression="zstd")
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"aggregate": result["aggregate"], "qa": result["qa"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
