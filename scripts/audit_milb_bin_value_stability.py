#!/usr/bin/env python
"""Measure league-season FaBIO-bin value stability as game sample grows.

This audit answers an infrastructure question, not a player-ranking question:
how many official games must be fetched per league-season to estimate useful
league-typical Performance-bin values?

It reuses the already-certified source/state/RE24 pipeline from
``audit_milb_bin_run_values.py``. Games are placed in a deterministic nested
spread order so each larger sample contains the smaller sample while continuing
to cover the observed date range. The largest sample is a diagnostic reference,
not assumed truth; an alternating-game split-half comparison provides a second
sampling-noise check.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from math import sqrt
import json
from pathlib import Path
from typing import Any, Mapping

import polars as pl

import audit_milb_bin_run_values as base
from universal_baseball.canonical_adapters import (
    normalize_armstjc_pitch_observations,
    normalize_official_play_sequence_observations,
)
from universal_baseball.certification import download_file, read_quarantined_csv
from universal_baseball.official_capture import capture_official_json, new_official_session
from universal_baseball.performance_events import build_performance_events
from universal_baseball.resolution import resolve_pitch_observations_within_snapshot
from universal_baseball.run_expectancy import attach_re24, estimate_run_expectancy, run_expectancy_coverage
from universal_baseball.state_transitions import transition_quality_flags
from universal_baseball.state_transitions_v2 import build_official_state_transitions_v2


DEFAULT_SAMPLE_SIZES = (5, 10, 15, 25, 35, 45)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-games-per-league", type=int, default=45)
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("data/quarantine/milb-bin-value-stability"),
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("reports/generated/milb-bin-value-stability"),
    )
    return parser.parse_args()


def _nested_spread_order(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return a deterministic max-min order over date-sorted games."""

    if not rows:
        return []
    ordered = sorted(rows, key=lambda row: (row["game_date"], row["game_pk"]))
    n = len(ordered)
    if n == 1:
        return ordered

    selected: list[int] = []
    for seed in (n // 2, 0, n - 1):
        if seed not in selected:
            selected.append(seed)

    while len(selected) < n:
        candidates = [index for index in range(n) if index not in selected]
        next_index = max(
            candidates,
            key=lambda index: (
                min(abs(index - chosen) for chosen in selected),
                -abs(index - (n - 1) / 2),
                -index,
            ),
        )
        selected.append(next_index)
    return [ordered[index] for index in selected]


def _inventory_orders(
    frame: pl.DataFrame,
    asset: str,
    *,
    max_games: int,
) -> dict[tuple[int, int, str], list[dict[str, Any]]]:
    inventory = base._game_inventory(frame, asset)
    result: dict[tuple[int, int, str], list[dict[str, Any]]] = {}
    for key, group in inventory.group_by(
        ["season", "league_id", "league_name"], maintain_order=True
    ):
        season, league_id, league_name = key
        raw_rows = [
            {
                "season": int(season),
                "league_id": int(league_id),
                "league_name": str(league_name),
                "game_pk": int(row["game_pk"]),
                "game_date": str(row["game_date"]),
                "asset": asset,
            }
            for row in group.select(["game_pk", "game_date"]).to_dicts()
        ]
        spread = _nested_spread_order(raw_rows)
        result[(int(season), int(league_id), str(league_name))] = spread[:max_games]
    return result


def _process_game(
    game: Mapping[str, Any],
    *,
    source_frame: pl.DataFrame,
    source_snapshot_id: str,
    source_normalization: Any,
    session: Any,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    source_game = base._filter_game(source_frame, int(game["game_pk"]))
    observations = normalize_armstjc_pitch_observations(
        source_game,
        source_snapshot_id=source_snapshot_id,
        normalization_id=source_normalization.normalization_id,
    )
    pitch_consensus = resolve_pitch_observations_within_snapshot(observations)

    capture = capture_official_json(
        f"game/{game['game_pk']}/playByPlay",
        session=session,
    )
    if not isinstance(capture.data, Mapping):
        raise RuntimeError(f"official game {game['game_pk']} PBP is not an object")
    official_snapshot, sequence_norm, transition_norm = base._official_source_identity(
        endpoint=capture.endpoint,
        sha256=capture.content_sha256,
    )
    sequences = normalize_official_play_sequence_observations(
        int(game["game_pk"]),
        capture.data,
        source_snapshot_id=official_snapshot,
        normalization_id=sequence_norm.normalization_id,
    )
    performance = build_performance_events(sequences, pitch_consensus)
    transitions = build_official_state_transitions_v2(
        int(game["game_pk"]),
        capture.data,
        source_snapshot_id=official_snapshot,
        normalization_id=transition_norm.normalization_id,
    )
    quality = transition_quality_flags(transitions)
    if not quality.is_empty():
        raise RuntimeError(
            f"state replay quality flags in game {game['game_pk']}: "
            f"{base._quality_flag_counts(quality)}"
        )
    return (
        base._augment_environment(performance, game),
        base._augment_environment(transitions, game),
    )


def _sample_value_result(
    performance_frames: list[pl.DataFrame],
    transition_frames: list[pl.DataFrame],
) -> dict[str, Any]:
    performance = pl.concat(performance_frames, how="vertical_relaxed")
    transitions = pl.concat(transition_frames, how="vertical_relaxed")
    matrix = estimate_run_expectancy(transitions)
    valued = attach_re24(transitions, matrix)
    coverage = run_expectancy_coverage(valued)

    terminal = valued.filter(
        pl.col("is_plate_appearance_result") & pl.col("re24_available")
    ).select(["game_pk", "at_bat_index", "re24"])
    core = performance.filter(
        pl.col("fabio_core_bin_pre_foul_screen").is_not_null()
    )
    joined = core.join(terminal, on=["game_pk", "at_bat_index"], how="inner")
    weights = (
        joined.group_by("fabio_core_bin_pre_foul_screen")
        .agg(
            pl.len().alias("occurrence_count"),
            pl.col("re24").mean().alias("mean_re24"),
            pl.col("re24").std(ddof=1).alias("std_dev"),
        )
        .with_columns(
            pl.when(pl.col("occurrence_count") > 1)
            .then(
                pl.col("std_dev")
                / pl.col("occurrence_count").cast(pl.Float64).sqrt()
            )
            .otherwise(pl.lit(None, dtype=pl.Float64))
            .alias("standard_error")
        )
        .sort("fabio_core_bin_pre_foul_screen")
    )
    state_samples = matrix.get_column("state_sample_size").to_list()
    return {
        "game_count": transitions.get_column("game_pk").n_unique(),
        "transition_count": transitions.height,
        "performance_pa_count": performance.height,
        "core_pa_count": core.height,
        "core_joined_count": joined.height,
        "core_join_rate": joined.height / core.height if core.height else None,
        "observed_state_count": matrix.height,
        "minimum_state_sample_size": int(min(state_samples)) if state_samples else 0,
        "median_state_sample_size": float(matrix.get_column("state_sample_size").median()) if state_samples else 0.0,
        "re24_coverage": coverage,
        "weights": weights.to_dicts(),
    }


def _weight_map(result: Mapping[str, Any]) -> dict[str, dict[str, float | int | None]]:
    return {
        str(row["fabio_core_bin_pre_foul_screen"]): {
            "mean": float(row["mean_re24"]),
            "n": int(row["occurrence_count"]),
            "se": None if row["standard_error"] is None else float(row["standard_error"]),
        }
        for row in result["weights"]
    }


def _pearson(left: list[float], right: list[float]) -> float | None:
    if len(left) < 2 or len(left) != len(right):
        return None
    mean_left = sum(left) / len(left)
    mean_right = sum(right) / len(right)
    numerator = sum(
        (x - mean_left) * (y - mean_right) for x, y in zip(left, right)
    )
    left_ss = sum((x - mean_left) ** 2 for x in left)
    right_ss = sum((y - mean_right) ** 2 for y in right)
    denominator = sqrt(left_ss * right_ss)
    return numerator / denominator if denominator else None


def _compare_weights(
    candidate: Mapping[str, Any],
    reference: Mapping[str, Any],
) -> dict[str, Any]:
    left = _weight_map(candidate)
    right = _weight_map(reference)
    bins = sorted(set(left) & set(right))
    deltas = [left[bin_name]["mean"] - right[bin_name]["mean"] for bin_name in bins]
    absolute = [abs(value) for value in deltas]
    candidate_values = [float(left[bin_name]["mean"]) for bin_name in bins]
    reference_values = [float(right[bin_name]["mean"]) for bin_name in bins]
    total_reference_n = sum(int(right[bin_name]["n"]) for bin_name in bins)
    weighted_mae = (
        sum(
            abs(float(left[bin_name]["mean"]) - float(right[bin_name]["mean"]))
            * int(right[bin_name]["n"])
            for bin_name in bins
        )
        / total_reference_n
        if total_reference_n
        else None
    )
    return {
        "common_bin_count": len(bins),
        "pearson_correlation": _pearson(candidate_values, reference_values),
        "mae": sum(absolute) / len(absolute) if absolute else None,
        "rmse": sqrt(sum(value * value for value in deltas) / len(deltas)) if deltas else None,
        "max_absolute_delta": max(absolute) if absolute else None,
        "median_absolute_delta": (
            float(pl.Series("delta", absolute).median()) if absolute else None
        ),
        "occurrence_weighted_mae": weighted_mae,
        "bin_within_0_05_count": sum(value <= 0.05 for value in absolute),
        "bin_within_0_10_count": sum(value <= 0.10 for value in absolute),
        "deltas": {
            bin_name: {
                "candidate": left[bin_name],
                "reference": right[bin_name],
                "delta": float(left[bin_name]["mean"]) - float(right[bin_name]["mean"]),
            }
            for bin_name in bins
        },
    }


def _sample_sizes(max_games: int) -> list[int]:
    values = [size for size in DEFAULT_SAMPLE_SIZES if size <= max_games]
    if max_games not in values:
        values.append(max_games)
    return sorted(set(values))


def main() -> int:
    args = parse_args()
    if args.max_games_per_league < 15:
        raise ValueError("max-games-per-league must be at least 15")
    args.work_dir.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)

    asset_frames: dict[str, pl.DataFrame] = {}
    asset_snapshots: dict[str, str] = {}
    asset_normalizations: dict[str, Any] = {}
    environment_orders: dict[tuple[int, int, str], list[dict[str, Any]]] = {}

    for asset in base.DEFAULT_ASSETS:
        path = args.work_dir / asset
        metadata = download_file(f"{base.BASE_URL}/{asset}", path, timeout_seconds=240)
        frame = read_quarantined_csv(path)
        snapshot_id, normalization = base._asset_source_identity(
            asset, str(metadata["sha256"])
        )
        asset_frames[asset] = frame
        asset_snapshots[asset] = snapshot_id
        asset_normalizations[asset] = normalization
        for key, order in _inventory_orders(
            frame, asset, max_games=args.max_games_per_league
        ).items():
            if key in environment_orders:
                raise RuntimeError(f"environment spans multiple selected assets: {key}")
            environment_orders[key] = order

    insufficient = {
        key: len(order)
        for key, order in environment_orders.items()
        if len(order) < args.max_games_per_league
    }
    if insufficient:
        raise RuntimeError(
            f"selected source asset lacks max game target for environments: {insufficient}"
        )

    per_environment_frames: dict[
        tuple[int, int, str], list[tuple[dict[str, Any], pl.DataFrame, pl.DataFrame]]
    ] = defaultdict(list)

    session = new_official_session()
    try:
        for key in sorted(environment_orders):
            for game in environment_orders[key]:
                performance, transitions = _process_game(
                    game,
                    source_frame=asset_frames[str(game["asset"])],
                    source_snapshot_id=asset_snapshots[str(game["asset"])],
                    source_normalization=asset_normalizations[str(game["asset"])],
                    session=session,
                )
                per_environment_frames[key].append((game, performance, transitions))
    finally:
        session.close()

    sample_sizes = _sample_sizes(args.max_games_per_league)
    environment_reports: list[dict[str, Any]] = []

    for key in sorted(per_environment_frames):
        season, league_id, league_name = key
        game_frames = per_environment_frames[key]
        sample_results: dict[int, dict[str, Any]] = {}
        for size in sample_sizes:
            subset = game_frames[:size]
            sample_results[size] = _sample_value_result(
                [item[1] for item in subset],
                [item[2] for item in subset],
            )

        reference = sample_results[max(sample_sizes)]
        convergence = [
            {
                "sample_games": size,
                **{
                    key_name: value
                    for key_name, value in sample_results[size].items()
                    if key_name != "weights"
                },
                "vs_max_sample": _compare_weights(sample_results[size], reference),
            }
            for size in sample_sizes
        ]

        split_a = game_frames[0::2]
        split_b = game_frames[1::2]
        split_a_result = _sample_value_result(
            [item[1] for item in split_a], [item[2] for item in split_a]
        )
        split_b_result = _sample_value_result(
            [item[1] for item in split_b], [item[2] for item in split_b]
        )
        split_comparison = _compare_weights(split_a_result, split_b_result)

        environment_reports.append(
            {
                "season": season,
                "league_id": league_id,
                "league_name": league_name,
                "max_sample_games": len(game_frames),
                "date_spread_order": [
                    {
                        "ordinal": index + 1,
                        "game_pk": item[0]["game_pk"],
                        "game_date": item[0]["game_date"],
                    }
                    for index, item in enumerate(game_frames)
                ],
                "convergence": convergence,
                "max_sample_weights": reference["weights"],
                "split_half": {
                    "a_games": len(split_a),
                    "b_games": len(split_b),
                    "a": {
                        key_name: value
                        for key_name, value in split_a_result.items()
                        if key_name != "weights"
                    },
                    "b": {
                        key_name: value
                        for key_name, value in split_b_result.items()
                        if key_name != "weights"
                    },
                    "comparison": split_comparison,
                },
            }
        )

    payload = {
        "report_schema_version": 1,
        "status": "diagnostic_sampling_stability_not_production_weights",
        "sample_sizes": sample_sizes,
        "environment_count": len(environment_reports),
        "environment_reports": environment_reports,
        "interpretation": (
            "The maximum sample is a convergence reference, not truth. Split-half comparisons "
            "measure independent sampling instability. This study is intended to choose an "
            "efficient historical official-PBP sampling strategy before production backfill."
        ),
    }
    (args.report_dir / "milb_bin_value_stability.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        "# MiLB bin-value sampling stability",
        "",
        "**Diagnostic only. No sampled weight is promoted to production.**",
        "",
        f"- Environments: {len(environment_reports)}",
        f"- Maximum official games per environment: {args.max_games_per_league}",
        f"- Nested sample sizes: {sample_sizes}",
        "",
    ]
    for report in environment_reports:
        lines.extend(
            [
                f"## {report['season']} {report['league_name']}",
                "",
            ]
        )
        for row in report["convergence"]:
            comparison = row["vs_max_sample"]
            lines.append(
                f"- {row['sample_games']} games: states {row['observed_state_count']}/24; "
                f"min state n={row['minimum_state_sample_size']}; "
                f"core n={row['core_joined_count']}; "
                f"vs max MAE={comparison['mae']:.4f}, RMSE={comparison['rmse']:.4f}, "
                f"max |Δ|={comparison['max_absolute_delta']:.4f}, "
                f"r={comparison['pearson_correlation']:.4f}"
            )
        split = report["split_half"]
        comparison = split["comparison"]
        lines.append(
            f"- Alternating split-half ({split['a_games']} vs {split['b_games']} games): "
            f"MAE={comparison['mae']:.4f}, RMSE={comparison['rmse']:.4f}, "
            f"max |Δ|={comparison['max_absolute_delta']:.4f}, "
            f"r={comparison['pearson_correlation']:.4f}"
        )
        lines.append("")

    lines.extend(
        [
            "The next production decision should be based on convergence and split-half noise, not on whether a small sample happened to observe all 24 states. If direct league-season bin means remain unstable, the correct response is partial pooling/shrinkage or a larger certified sample—not silent acceptance of noisy weights.",
            "",
        ]
    )
    summary = "\n".join(lines)
    (args.report_dir / "milb_bin_value_stability.md").write_text(summary, encoding="utf-8")
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
