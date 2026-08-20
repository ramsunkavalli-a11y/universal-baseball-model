#!/usr/bin/env python
"""First diagnostic MiLB league -> RE24 -> FaBIO-bin value POC.

This is deliberately *not* a player model and does not freeze production
weights. It asks whether modest samples from actual affiliated leagues can:

1. support their own 24-state run-expectancy matrices;
2. achieve strong transition-level RE24 coverage;
3. join cleanly to the already-certified universal Performance event bins; and
4. produce directionally sensible league-typical bin values.

Official Stats API state transitions supply contextual RE24. The reused armstjc
history supplies physical contact / trajectory / direction. Player occurrences
are never scored by their own contextual RE24 here; contextual RE24 is averaged
within league-season-bin to estimate a diagnostic *bin* value, following the
FaBIO/tRA philosophy.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any, Mapping

import polars as pl

from universal_baseball.canonical_adapters import (
    normalize_armstjc_pitch_observations,
    normalize_official_play_sequence_observations,
)
from universal_baseball.canonical_schema import CANONICAL_SCHEMA_VERSION
from universal_baseball.certification import download_file, read_quarantined_csv
from universal_baseball.official_capture import (
    capture_official_json,
    new_official_session,
)
from universal_baseball.performance_events import build_performance_events
from universal_baseball.provenance import NormalizationDefinition, make_source_snapshot_id
from universal_baseball.resolution import resolve_pitch_observations_within_snapshot
from universal_baseball.run_expectancy import (
    attach_re24,
    estimate_run_expectancy,
    run_expectancy_coverage,
)
from universal_baseball.state_transitions import transition_quality_flags
from universal_baseball.state_transitions_v2 import build_official_state_transitions_v2


BASE_URL = "https://github.com/armstjc/milb-data-repository/releases/download/pbp"
DEFAULT_ASSETS = ("2025_4_aaa_pbp.csv", "2024_6_rk_pbp.csv")
ENVIRONMENT_COLUMNS = ["season", "league_id"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games-per-league", type=int, default=15)
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("data/quarantine/milb-bin-run-value-poc"),
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("reports/generated/milb-bin-run-value-poc"),
    )
    return parser.parse_args()


def _int(value: Any) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _asset_source_identity(asset: str, sha256: str) -> tuple[str, NormalizationDefinition]:
    snapshot_id = make_source_snapshot_id(
        source_name="armstjc_milb_pbp",
        content_sha256=sha256,
        upstream_version=asset,
    )
    normalization = NormalizationDefinition.build(
        source_snapshot_id=snapshot_id,
        normalizer_name="normalize_armstjc_pitch_observations",
        normalizer_version="1",
        canonical_schema_version=CANONICAL_SCHEMA_VERSION,
    )
    return snapshot_id, normalization


def _official_source_identity(
    *,
    endpoint: str,
    sha256: str,
) -> tuple[str, NormalizationDefinition, NormalizationDefinition]:
    snapshot_id = make_source_snapshot_id(
        source_name="mlb_stats_api",
        content_sha256=sha256,
        upstream_version=endpoint,
    )
    sequence_normalization = NormalizationDefinition.build(
        source_snapshot_id=snapshot_id,
        normalizer_name="normalize_official_play_sequence_observations",
        normalizer_version="1",
        canonical_schema_version=CANONICAL_SCHEMA_VERSION,
    )
    transition_normalization = NormalizationDefinition.build(
        source_snapshot_id=snapshot_id,
        normalizer_name="build_official_state_transitions",
        normalizer_version="poc-v2",
        canonical_schema_version=CANONICAL_SCHEMA_VERSION,
    )
    return snapshot_id, sequence_normalization, transition_normalization


def _game_inventory(frame: pl.DataFrame, asset: str) -> pl.DataFrame:
    required = {"game_pk", "game_date", "game_year", "league_id", "league_name"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{asset} missing game inventory fields: {missing}")

    columns = ["game_pk", "game_date", "game_year", "league_id", "league_name"]
    if "game_type" in frame.columns:
        columns.append("game_type")
    inventory = (
        frame.select(columns)
        .with_columns(
            pl.col("game_pk").cast(pl.Int64, strict=False),
            pl.col("game_year").cast(pl.Int64, strict=False).alias("season"),
            pl.col("league_id").cast(pl.Int64, strict=False),
            pl.col("league_name").cast(pl.String, strict=False),
            pl.col("game_date").cast(pl.String, strict=False),
        )
        .drop_nulls(["game_pk", "season", "league_id", "league_name", "game_date"])
        .unique()
    )
    if "game_type" in inventory.columns:
        # Regular-season code is R in the tested Stats API/source surfaces. If
        # no R games survive for an environment, fail rather than silently using
        # spring/exhibition games in a league-run-environment POC.
        regular = inventory.filter(pl.col("game_type") == "R")
        if regular.height:
            inventory = regular
    return inventory.sort(["league_id", "game_date", "game_pk"])


def _spread_sample(values: list[int], limit: int) -> list[int]:
    if limit <= 0 or not values:
        return []
    if len(values) <= limit:
        return values
    if limit == 1:
        return [values[len(values) // 2]]
    indices = {
        round(index * (len(values) - 1) / (limit - 1))
        for index in range(limit)
    }
    return [values[index] for index in sorted(indices)]


def _select_games(
    inventory: pl.DataFrame,
    *,
    games_per_league: int,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for key, group in inventory.group_by(
        ["season", "league_id", "league_name"], maintain_order=True
    ):
        season, league_id, league_name = key
        ordered = group.sort(["game_date", "game_pk"])
        game_ids = [int(value) for value in ordered.get_column("game_pk").to_list()]
        sampled = set(_spread_sample(game_ids, games_per_league))
        for row in ordered.filter(pl.col("game_pk").is_in(sorted(sampled))).to_dicts():
            selected.append(
                {
                    "season": int(season),
                    "league_id": int(league_id),
                    "league_name": str(league_name),
                    "game_pk": int(row["game_pk"]),
                    "game_date": str(row["game_date"]),
                }
            )
    return sorted(
        selected,
        key=lambda row: (row["season"], row["league_id"], row["game_date"], row["game_pk"]),
    )


def _filter_game(frame: pl.DataFrame, game_pk: int) -> pl.DataFrame:
    return frame.filter(pl.col("game_pk").cast(pl.Int64, strict=False) == game_pk)


def _augment_environment(
    frame: pl.DataFrame,
    metadata: Mapping[str, Any],
) -> pl.DataFrame:
    return frame.with_columns(
        pl.lit(int(metadata["season"]), dtype=pl.Int64).alias("season"),
        pl.lit(int(metadata["league_id"]), dtype=pl.Int64).alias("league_id"),
        pl.lit(str(metadata["league_name"])).alias("league_name"),
    )


def _quality_flag_counts(frame: pl.DataFrame) -> dict[str, int]:
    if frame.is_empty():
        return {}
    counts: Counter[str] = Counter()
    for raw in frame.get_column("quality_flags_json").to_list():
        for flag in json.loads(raw):
            counts[str(flag)] += 1
    return dict(sorted(counts.items()))


def _environment_reports(
    transitions: pl.DataFrame,
    matrix: pl.DataFrame,
    re24: pl.DataFrame,
    performance: pl.DataFrame,
    joined: pl.DataFrame,
) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    environments = (
        transitions.select(["season", "league_id", "league_name"])
        .unique()
        .sort(["season", "league_id"])
        .to_dicts()
    )
    for env in environments:
        condition = (
            (pl.col("season") == env["season"])
            & (pl.col("league_id") == env["league_id"])
        )
        env_transitions = transitions.filter(condition)
        env_matrix = matrix.filter(condition)
        env_re24 = re24.filter(condition)
        env_performance = performance.filter(condition)
        env_joined = joined.filter(condition)
        coverage = run_expectancy_coverage(env_re24)
        state_samples = env_matrix.get_column("state_sample_size").to_list()
        reports.append(
            {
                **env,
                "game_count": env_transitions.get_column("game_pk").n_unique(),
                "transition_count": env_transitions.height,
                "observed_state_count": env_matrix.height,
                "minimum_state_sample_size": int(min(state_samples)) if state_samples else 0,
                "median_state_sample_size": float(env_matrix.get_column("state_sample_size").median()) if state_samples else 0.0,
                "re24_coverage": coverage,
                "performance_pa_count": env_performance.height,
                "core_eligible_pre_foul_screen_count": int(
                    env_performance.get_column("core_profile_eligible_pre_foul_screen").sum()
                ),
                "core_joined_re24_count": env_joined.height,
            }
        )
    return reports


def _bin_weights(joined: pl.DataFrame) -> list[dict[str, Any]]:
    if joined.is_empty():
        return []
    weights = (
        joined.group_by(
            [
                "season",
                "league_id",
                "league_name",
                "fabio_core_bin_pre_foul_screen",
            ]
        )
        .agg(
            pl.len().alias("occurrence_count"),
            pl.col("re24").mean().alias("mean_contextual_re24"),
            pl.col("re24").std(ddof=1).alias("re24_std_dev"),
        )
        .with_columns(
            pl.when(pl.col("occurrence_count") > 1)
            .then(
                pl.col("re24_std_dev")
                / pl.col("occurrence_count").cast(pl.Float64).sqrt()
            )
            .otherwise(pl.lit(None, dtype=pl.Float64))
            .alias("standard_error")
        )
        .sort(
            ["season", "league_id", "fabio_core_bin_pre_foul_screen"]
        )
    )
    return weights.to_dicts()


def _directional_sanity(weights: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Report broad ordering checks without making them pass/fail gates."""

    by_environment: dict[tuple[int, int, str], dict[str, float]] = {}
    for row in weights:
        key = (int(row["season"]), int(row["league_id"]), str(row["league_name"]))
        value = row.get("mean_contextual_re24")
        if value is not None:
            by_environment.setdefault(key, {})[
                str(row["fabio_core_bin_pre_foul_screen"])
            ] = float(value)

    reports: list[dict[str, Any]] = []
    for (season, league_id, league_name), values in sorted(by_environment.items()):
        reports.append(
            {
                "season": season,
                "league_id": league_id,
                "league_name": league_name,
                "bb_hbp_gt_k": (
                    values.get("BB_HBP") > values.get("K")
                    if "BB_HBP" in values and "K" in values
                    else None
                ),
                "pull_offb_gt_iffb": (
                    values.get("PULL_OFFB") > values.get("IFFB")
                    if "PULL_OFFB" in values and "IFFB" in values
                    else None
                ),
                "bin_count": len(values),
            }
        )
    return reports


def main() -> int:
    args = parse_args()
    if args.games_per_league < 3:
        raise ValueError("games-per-league must be at least 3 for this POC")
    args.work_dir.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)

    asset_frames: dict[str, pl.DataFrame] = {}
    asset_snapshots: dict[str, str] = {}
    asset_normalizations: dict[str, NormalizationDefinition] = {}
    selected_games: list[dict[str, Any]] = []

    for asset in DEFAULT_ASSETS:
        path = args.work_dir / asset
        metadata = download_file(f"{BASE_URL}/{asset}", path, timeout_seconds=240)
        frame = read_quarantined_csv(path)
        snapshot_id, normalization = _asset_source_identity(asset, str(metadata["sha256"]))
        asset_frames[asset] = frame
        asset_snapshots[asset] = snapshot_id
        asset_normalizations[asset] = normalization
        for row in _select_games(
            _game_inventory(frame, asset), games_per_league=args.games_per_league
        ):
            selected_games.append({**row, "asset": asset})

    # Detect accidental game duplication across source assets before official
    # traffic. If the same game appears twice, source snapshot resolution belongs
    # upstream of this POC rather than silently double-counting its PA values.
    game_ids = [row["game_pk"] for row in selected_games]
    if len(game_ids) != len(set(game_ids)):
        duplicates = [
            game_pk
            for game_pk, count in Counter(game_ids).items()
            if count > 1
        ]
        raise RuntimeError(f"selected games overlap source assets: {duplicates[:20]}")

    performance_frames: list[pl.DataFrame] = []
    transition_frames: list[pl.DataFrame] = []
    per_game: list[dict[str, Any]] = []

    session = new_official_session()
    try:
        for ordinal, game in enumerate(selected_games, start=1):
            asset = str(game["asset"])
            source_game = _filter_game(asset_frames[asset], int(game["game_pk"]))
            pitch_observations = normalize_armstjc_pitch_observations(
                source_game,
                source_snapshot_id=asset_snapshots[asset],
                normalization_id=asset_normalizations[asset].normalization_id,
            )
            pitch_consensus = resolve_pitch_observations_within_snapshot(
                pitch_observations
            )

            capture = capture_official_json(
                f"game/{game['game_pk']}/playByPlay",
                session=session,
            )
            if not isinstance(capture.data, Mapping):
                raise RuntimeError(
                    f"official game {game['game_pk']} playByPlay is not an object"
                )
            (
                official_snapshot,
                sequence_normalization,
                transition_normalization,
            ) = _official_source_identity(
                endpoint=capture.endpoint,
                sha256=capture.content_sha256,
            )
            sequences = normalize_official_play_sequence_observations(
                int(game["game_pk"]),
                capture.data,
                source_snapshot_id=official_snapshot,
                normalization_id=sequence_normalization.normalization_id,
            )
            performance = build_performance_events(sequences, pitch_consensus)
            transitions = build_official_state_transitions_v2(
                int(game["game_pk"]),
                capture.data,
                source_snapshot_id=official_snapshot,
                normalization_id=transition_normalization.normalization_id,
            )

            transition_quality = transition_quality_flags(transitions)
            if not transition_quality.is_empty():
                raise RuntimeError(
                    f"state replay quality flags in game {game['game_pk']}: "
                    f"{_quality_flag_counts(transition_quality)}"
                )

            performance = _augment_environment(performance, game)
            transitions = _augment_environment(transitions, game)
            performance_frames.append(performance)
            transition_frames.append(transitions)
            per_game.append(
                {
                    **game,
                    "source_pitch_consensus_count": pitch_consensus.height,
                    "performance_pa_count": performance.height,
                    "core_eligible_count": int(
                        performance.get_column(
                            "core_profile_eligible_pre_foul_screen"
                        ).sum()
                    ),
                    "state_transition_count": transitions.height,
                    "official_snapshot_sha256": capture.content_sha256,
                    "ordinal": ordinal,
                }
            )
    finally:
        session.close()

    performance = pl.concat(performance_frames, how="vertical_relaxed")
    transitions = pl.concat(transition_frames, how="vertical_relaxed")

    matrix = estimate_run_expectancy(
        transitions,
        group_columns=ENVIRONMENT_COLUMNS,
    )
    re24 = attach_re24(
        transitions,
        matrix,
        group_columns=ENVIRONMENT_COLUMNS,
    )

    terminal_re24 = re24.filter(
        pl.col("is_plate_appearance_result") & pl.col("re24_available")
    ).select(
        [
            "game_pk",
            "at_bat_index",
            "season",
            "league_id",
            "re24",
            "run_expectancy_before",
            "run_expectancy_after",
        ]
    )
    duplicate_pa_value = (
        terminal_re24.group_by(["game_pk", "at_bat_index"])
        .len()
        .filter(pl.col("len") > 1)
    )
    if not duplicate_pa_value.is_empty():
        raise RuntimeError("terminal RE24 has duplicate PA keys")

    core = performance.filter(
        pl.col("fabio_core_bin_pre_foul_screen").is_not_null()
    )
    joined = core.join(
        terminal_re24,
        on=["game_pk", "at_bat_index", "season", "league_id"],
        how="inner",
    )
    missing_core_re24 = core.join(
        terminal_re24.select(
            ["game_pk", "at_bat_index", "season", "league_id"]
        ),
        on=["game_pk", "at_bat_index", "season", "league_id"],
        how="anti",
    )

    environment_reports = _environment_reports(
        transitions, matrix, re24, performance, joined
    )
    weights = _bin_weights(joined)
    sanity = _directional_sanity(weights)

    payload = {
        "report_schema_version": 1,
        "status": "diagnostic_pre_foul_screen_not_production_weights",
        "games_per_league_target": args.games_per_league,
        "selected_game_count": len(selected_games),
        "environment_count": len(environment_reports),
        "selected_games": per_game,
        "environments": environment_reports,
        "run_expectancy_matrix": matrix.to_dicts(),
        "core_bin_weights": weights,
        "directional_sanity_checks": sanity,
        "core_performance_pa_count": core.height,
        "core_pa_with_re24_count": joined.height,
        "core_pa_without_re24_count": missing_core_re24.height,
        "core_pa_re24_join_rate": joined.height / core.height if core.height else None,
        "method": (
            "League-season RE matrices use only three-out completed half-innings. "
            "Each terminal PA's contextual RE24 is then joined to its pre-foul-screen "
            "FaBIO candidate bin; the diagnostic bin value is the league-season mean "
            "contextual RE24 of occurrences in that bin. No player receives his own "
            "contextual RE24 as a Performance score."
        ),
        "limitations": [
            "small diagnostic game sample, not a full league-season estimate",
            "foul-air screen not yet applied",
            "no hierarchical pooling/shrinkage for sparse state or bin samples",
            "no player scores or rankings",
        ],
    }
    (args.report_dir / "milb_bin_run_value_poc.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        "# MiLB league-to-FaBIO-bin run-value POC",
        "",
        "**Diagnostic only. These are not production bin weights and are not player scores.**",
        "",
        f"- Selected games: {len(selected_games):,}",
        f"- Environments: {len(environment_reports)}",
        f"- Core pre-foul-screen PAs: {core.height:,}",
        f"- Core PAs with RE24: {joined.height:,}/{core.height:,} "
        f"({joined.height / core.height:.2%})" if core.height else "- Core PAs with RE24: n/a",
        "",
        "## Environment coverage",
        "",
    ]
    for report in environment_reports:
        coverage = report["re24_coverage"]
        lines.append(
            f"- {report['season']} {report['league_name']} (league `{report['league_id']}`): "
            f"{report['game_count']} games; states {report['observed_state_count']}/24; "
            f"min state n={report['minimum_state_sample_size']}; "
            f"RE24 {coverage['re24_available_count']}/{coverage['transition_count']} "
            f"({coverage['re24_coverage_rate']:.2%}); "
            f"core joined {report['core_joined_re24_count']}/{report['core_eligible_pre_foul_screen_count']}"
        )

    lines.extend(["", "## Diagnostic bin values", ""])
    for row in weights:
        lines.append(
            f"- {row['season']} {row['league_name']} — `{row['fabio_core_bin_pre_foul_screen']}`: "
            f"n={row['occurrence_count']}, mean RE24={row['mean_contextual_re24']:.4f}, "
            f"SE={row['standard_error']:.4f}" if row["standard_error"] is not None else
            f"- {row['season']} {row['league_name']} — `{row['fabio_core_bin_pre_foul_screen']}`: "
            f"n={row['occurrence_count']}, mean RE24={row['mean_contextual_re24']:.4f}, SE=n/a"
        )

    lines.extend(
        [
            "",
            "A successful POC shows the state/value architecture works. It does **not** justify freezing sampled weights. The next decision is how much league-season history is needed and how to pool sparse state/bin estimates before production values are generated.",
            "",
        ]
    )
    summary = "\n".join(lines)
    (args.report_dir / "milb_bin_run_value_poc.md").write_text(summary, encoding="utf-8")
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
