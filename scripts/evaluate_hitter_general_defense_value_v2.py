#!/usr/bin/env python3
"""Test frozen general defense inside the new hitter value stack."""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import polars as pl
import requests

from universal_baseball.current_defense import build_current_general_defense_rates
from universal_baseball.hitter_target_architecture import (
    paired_cluster_rmse_delta,
    regression_metrics,
)
from universal_baseball.mlb_season_stats import MLB_STATS_URL, _statsapi_get_with_retry
from universal_baseball.player_value_defense_projection import (
    GENERAL_POSITIONS,
    LEVEL_BY_LEAGUE,
    load_frozen_fielding_profiles,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


OLD_REPORTS = Path(
    "C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/"
    "universal-baseball-model/reports/generated"
)
BASE_PATH = Path("reports/generated/hitter-baserunning-value-v2/predictions.parquet")
WORKLOAD_PATH = Path(
    "reports/generated/hitter-workload-model-v2/chronological-predictions.parquet"
)
GENERAL_PARAMETER_PATH = Path("docs/defense-v1-confirmation-parameters.json")
CONVERSION_PARAMETER_PATH = Path(
    "docs/player-value-v1-defense-native-run-conversion-parameters.json"
)
TARGET_PATH = Path(
    "reports/generated/defense-v1-2025-target-source/tables/"
    "general_range_targets_2025.parquet"
)
MLB_FIELDING_PATH = (
    OLD_REPORTS
    / "mlb-fielding-outcome-inventory-2004-2025/tables/"
    "mlb_fielding_usage_2004_2025.parquet"
)
OUTPUT_ROOT = Path("reports/generated/hitter-general-defense-value-v2")
CAPTURE_ROOT = OUTPUT_ROOT / "captures"
ORIGIN_SEASON = 2024
TARGET_SEASON = 2025
RUNS_PER_WIN = 10.0
PAGE_LIMIT = 500


def _fetch_league(
    session: requests.Session,
    *,
    season: int,
    league_id: int,
) -> list[dict[str, object]]:
    captures: list[dict[str, object]] = []
    seen_signatures: set[tuple[tuple[int, str, int], ...]] = set()
    offset = 0
    while True:
        path = (
            CAPTURE_ROOT
            / str(season)
            / str(league_id)
            / f"fielding_offset_{offset}.json"
        )
        if path.exists():
            content = path.read_bytes()
            payload = json.loads(content)
            requested_url = "cached_official_statsapi_capture"
        else:
            response = _statsapi_get_with_retry(
                session,
                MLB_STATS_URL,
                params={
                    "stats": "season",
                    "group": "fielding",
                    "season": season,
                    "leagueId": league_id,
                    "playerPool": "ALL",
                    "gameType": "R",
                    "limit": PAGE_LIMIT,
                    "offset": offset,
                },
                timeout_seconds=120,
            )
            content = response.content
            payload = response.json()
            requested_url = response.url
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        blocks = payload.get("stats") or []
        if len(blocks) != 1 or not isinstance(blocks[0].get("splits"), list):
            raise RuntimeError("fielding response has invalid stats block")
        splits = blocks[0]["splits"]
        signature = tuple(
            (
                int((row.get("player") or row.get("person") or {})["id"]),
                str((row.get("position") or {}).get("abbreviation") or ""),
                int((row.get("team") or {})["id"]),
            )
            for row in splits
        )
        if signature and signature in seen_signatures:
            raise RuntimeError("fielding pagination repeated a page")
        seen_signatures.add(signature)
        captures.append(
            {
                "season": season,
                "league_id": league_id,
                "offset": offset,
                "returned_rows": len(splits),
                "requested_url": requested_url,
                "response_bytes": len(content),
                "response_sha256": sha256(content).hexdigest(),
                "path": str(path),
            }
        )
        if len(splits) < PAGE_LIMIT:
            break
        offset += len(splits)
        if offset > 10_000:
            raise RuntimeError("fielding pagination exceeded safety limit")
    return captures


def _profiles() -> tuple[pl.DataFrame, dict[str, int], list[dict[str, object]]]:
    captures = []
    with requests.Session() as session:
        session.headers["User-Agent"] = "universal-baseball-model-defense-v2/0.1"
        for league_id in sorted(LEVEL_BY_LEAGUE):
            captures.extend(
                _fetch_league(
                    session,
                    season=ORIGIN_SEASON,
                    league_id=league_id,
                )
            )
    profiles, audit = load_frozen_fielding_profiles(
        CAPTURE_ROOT, expected_seasons={ORIGIN_SEASON}
    )
    return profiles, audit, captures


def _actual_defense_war(
    targets: pl.DataFrame,
    fielding: pl.DataFrame,
    conversion: dict[str, Any],
) -> tuple[pl.DataFrame, pl.DataFrame]:
    actual = (
        fielding.filter(
            (pl.col("season") == TARGET_SEASON)
            & pl.col("position_abbreviation").is_in(sorted(GENERAL_POSITIONS))
        )
        .group_by("player_id", "position_abbreviation")
        .agg(pl.col("fielding_outs").sum())
        .rename({"position_abbreviation": "position"})
        .join(
            targets.select("player_id", "position", "range_target_z"),
            on=["player_id", "position"],
            how="inner",
            validate="1:1",
        )
    )
    moments = actual.group_by("position").agg(
        (
            (pl.col("range_target_z") * pl.col("fielding_outs")).sum()
            / pl.col("fielding_outs").sum()
        ).alias("exposure_weighted_target_center")
    )
    by_position = (
        actual.join(moments, on="position", how="left", validate="m:1")
        .with_columns(
            pl.col("position")
            .replace_strict(
                {
                    position: float(
                        conversion["parameters_by_position"][position][
                            "run_rate_per_z_opportunity"
                        ]
                    )
                    for position in sorted(GENERAL_POSITIONS)
                },
                return_dtype=pl.Float64,
            )
            .alias("run_rate_per_z_out")
        )
        .with_columns(
            (
                (
                    pl.col("range_target_z")
                    - pl.col("exposure_weighted_target_center")
                )
                * pl.col("fielding_outs")
                * pl.col("run_rate_per_z_out")
            ).alias("actual_general_defense_runs")
        )
        .sort(["player_id", "position"])
    )
    by_player = (
        by_position.group_by("player_id")
        .agg(pl.col("actual_general_defense_runs").sum())
        .with_columns(
            (pl.col("actual_general_defense_runs") / RUNS_PER_WIN).alias(
                "actual_general_defense_war"
            )
        )
        .sort("player_id")
    )
    return by_player, by_position


def main() -> None:
    base = pl.read_parquet(BASE_PATH)
    workload = pl.read_parquet(WORKLOAD_PATH).filter(
        pl.col("origin_year") == ORIGIN_SEASON
    )
    profiles, profile_audit, captures = _profiles()
    general_parameters = json.loads(
        GENERAL_PARAMETER_PATH.read_text(encoding="utf-8")
    )["parameters"]["general"]
    conversion = json.loads(
        CONVERSION_PARAMETER_PATH.read_text(encoding="utf-8")
    )["general_range"]

    opportunity = workload.select(
        "player_id",
        pl.lit(TARGET_SEASON).alias("season"),
        pl.col("prediction_candidate_active_probability").alias(
            "mlb_active_probability"
        ),
        pl.when(pl.col("prediction_candidate_active_probability") > 0)
        .then(
            pl.col("prediction_candidate_expected_pa")
            / pl.col("prediction_candidate_active_probability")
        )
        .otherwise(0.0)
        .alias("conditional_mlb_pa"),
    )
    rates = build_current_general_defense_rates(
        base.select("player_id"),
        profiles,
        opportunity,
        current_season=ORIGIN_SEASON,
        forecast_seasons=(TARGET_SEASON,),
        general_parameters=general_parameters,
        conversion_parameters=conversion,
    )
    actual_by_player, actual_by_position = _actual_defense_war(
        pl.read_parquet(TARGET_PATH),
        pl.read_parquet(MLB_FIELDING_PATH),
        conversion,
    )

    frame = (
        base.join(
            opportunity.select("player_id", "mlb_active_probability"),
            on="player_id",
            how="left",
            validate="1:1",
        )
        .join(
            rates.select(
                "player_id",
                "conditional_defense_runs",
                "defense_runs_per_600",
                "defense_evidence_tier",
                "eligible_general_positions",
            ),
            on="player_id",
            how="left",
            validate="1:1",
        )
        .join(actual_by_player, on="player_id", how="left", validate="1:1")
        .with_columns(
            pl.col("actual_general_defense_runs").fill_null(0.0),
            pl.col("actual_general_defense_war").fill_null(0.0),
        )
        .with_columns(
            (
                pl.col("conditional_defense_runs")
                * pl.col("mlb_active_probability")
                / RUNS_PER_WIN
            ).alias("prediction_general_defense_war"),
            (
                pl.col("actual_batting_position_baserunning_war")
                + pl.col("actual_general_defense_war")
            ).alias("actual_partial_war_with_general_defense"),
            pl.col("prediction_position_plus_baserunning_war").alias(
                "prediction_without_general_defense_war"
            ),
        )
        .with_columns(
            (
                pl.col("prediction_without_general_defense_war")
                + pl.col("prediction_general_defense_war")
            ).alias("prediction_with_general_defense_war")
        )
        .sort("player_id")
    )

    target = frame["actual_partial_war_with_general_defense"].to_numpy()
    player_ids = frame["player_id"].to_numpy()
    without = frame["prediction_without_general_defense_war"].to_numpy()
    with_defense = frame["prediction_with_general_defense_war"].to_numpy()
    actual_component = frame["actual_general_defense_war"].to_numpy()
    predicted_component = frame["prediction_general_defense_war"].to_numpy()
    zero_component = predicted_component * 0.0

    by_stage = {}
    for stage in ("current_mlb", "upper_minors", "lower_minors"):
        segment = frame.filter(pl.col("player_stage") == stage)
        segment_target = segment["actual_partial_war_with_general_defense"].to_numpy()
        by_stage[stage] = {
            "without_general_defense": regression_metrics(
                segment_target,
                segment["prediction_without_general_defense_war"].to_numpy(),
            ),
            "with_general_defense": regression_metrics(
                segment_target,
                segment["prediction_with_general_defense_war"].to_numpy(),
            ),
        }

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    prediction_artifact = write_canonical_parquet(
        frame,
        OUTPUT_ROOT / "predictions.parquet",
        table_name="hitter_general_defense_value_v2_predictions",
    )
    position_artifact = write_canonical_parquet(
        actual_by_position,
        OUTPUT_ROOT / "actual-defense-by-position.parquet",
        table_name="hitter_general_defense_v2_actual_by_position",
    )
    profile_artifact = write_canonical_parquet(
        profiles,
        OUTPUT_ROOT / "origin-fielding-profiles.parquet",
        table_name="hitter_general_defense_v2_origin_profiles",
    )
    report = {
        "schema_version": "0.1",
        "status": "hitter_general_defense_value_test_complete",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "target": (
            "2025 batting plus replacement plus position plus baserunning plus "
            "general defense WAR"
        ),
        "population_rows": frame.height,
        "model": {
            "skill": "frozen Defense v1 U1 general range",
            "exposure": "frozen prior-season MLB defensive-outs persistence",
            "position_allocation": "frozen prior-season defensive-out shares",
            "centering": "position exposure-weighted zero",
            "catcher_components": "neutral and excluded from this test",
        },
        "metrics": {
            "without_general_defense": regression_metrics(target, without),
            "with_general_defense": regression_metrics(target, with_defense),
        },
        "paired_comparison": paired_cluster_rmse_delta(
            target, with_defense, without, player_ids
        ),
        "component_metrics": {
            "neutral_zero": regression_metrics(actual_component, zero_component),
            "player_specific": regression_metrics(
                actual_component, predicted_component
            ),
        },
        "component_paired_comparison": paired_cluster_rmse_delta(
            actual_component,
            predicted_component,
            zero_component,
            player_ids,
        ),
        "by_player_stage": by_stage,
        "coverage": frame.group_by("defense_evidence_tier")
        .len()
        .sort("defense_evidence_tier")
        .to_dicts(),
        "profile_audit": profile_audit,
        "capture_pages": len(captures),
        "capture_manifest": captures,
        "sources": {
            "base_predictions": {
                "path": str(BASE_PATH),
                "sha256": sha256_file(BASE_PATH),
            },
            "workload_predictions": {
                "path": str(WORKLOAD_PATH),
                "sha256": sha256_file(WORKLOAD_PATH),
            },
            "general_parameters": {
                "path": str(GENERAL_PARAMETER_PATH),
                "sha256": sha256_file(GENERAL_PARAMETER_PATH),
            },
            "conversion_parameters": {
                "path": str(CONVERSION_PARAMETER_PATH),
                "sha256": sha256_file(CONVERSION_PARAMETER_PATH),
            },
            "target": {"path": str(TARGET_PATH), "sha256": sha256_file(TARGET_PATH)},
            "mlb_fielding": {
                "path": str(MLB_FIELDING_PATH),
                "sha256": sha256_file(MLB_FIELDING_PATH),
            },
        },
        "artifacts": {
            "predictions": prediction_artifact.as_record(),
            "actual_by_position": position_artifact.as_record(),
            "origin_profiles": profile_artifact.as_record(),
        },
        "limitations": [
            "This is an already-exposed 2025 development test, not final confirmation.",
            "The conservative exposure rule gives no defense value to players without prior MLB defensive outs.",
            "Only general range is included; catcher throwing, blocking, and framing remain neutral.",
            "Players absent from the qualified 2025 public OAA target are assigned zero realized general-defense value.",
            "The live 2025 public target was recaptured after the original one-shot confirmation and is disclosed by hash.",
        ],
    }
    (OUTPUT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "metrics": report["metrics"],
                "paired_comparison": report["paired_comparison"],
                "component_metrics": report["component_metrics"],
                "component_paired_comparison": report[
                    "component_paired_comparison"
                ],
                "coverage": report["coverage"],
                "profile_audit": profile_audit,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
