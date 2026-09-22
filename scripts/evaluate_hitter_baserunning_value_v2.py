#!/usr/bin/env python3
"""Test the frozen baserunning model inside the new hitter value stack."""

from __future__ import annotations

from dataclasses import asdict, fields
from datetime import UTC, datetime
import gzip
from hashlib import sha256
import json
from pathlib import Path

import polars as pl
import requests

from universal_baseball.current_baserunning import (
    build_advancement_history,
    build_current_baserunning_rates,
    build_steal_history,
)
from universal_baseball.historical_hitter_advancement import (
    advancement_war_by_player_origin,
)
from universal_baseball.historical_hitter_baserunning import steal_war_by_player_origin
from universal_baseball.hitter_target_architecture import (
    paired_cluster_rmse_delta,
    regression_metrics,
)
from universal_baseball.player_value_baserunning_runs import BaserunningReference
from universal_baseball.player_value_baserunning_sources import (
    SAVANT_BASERUNNING_RUN_VALUE_URL,
    audit_savant_baserunning_rows,
    parse_savant_baserunning_csv,
    savant_baserunning_query_params,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


OLD_ROOT = Path(
    "C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/"
    "universal-baseball-model"
)
HISTORICAL_COMPONENTS_PATH = (
    OLD_ROOT
    / "reports/generated/affiliated-skill-source-2018-2022/tables/"
    "affiliated_hitting_components.parquet"
)
CURRENT_COMPONENTS_PATH = (
    OLD_ROOT
    / "reports/generated/affiliated-skill-source/tables/"
    "affiliated_hitting_components.parquet"
)
CURRENT_SAVANT_RAW_ROOT = (
    OLD_ROOT / "reports/generated/current-baserunning-rates/2026-09-08/raw"
)
POSITION_PATH = Path("reports/generated/hitter-positional-value-v2/predictions.parquet")
REFERENCE_PATH = Path("docs/player-value-v1-baserunning-run-conversion-2024.json")
OUTPUT_ROOT = Path("reports/generated/hitter-baserunning-value-v2")
HISTORY_SEASONS = (2022, 2023, 2024)
TARGET_SEASON = 2025
RUNS_PER_WIN = 10.0


def _reference() -> BaserunningReference:
    payload = json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))
    values = payload["reference"]
    return BaserunningReference(
        **{field.name: values[field.name] for field in fields(BaserunningReference)}
    )


def _load_or_fetch_savant(
    season: int,
) -> tuple[list[dict[str, str]], dict[str, object]]:
    old_path = CURRENT_SAVANT_RAW_ROOT / f"savant-baserunning-{season}.csv.gz"
    output_path = OUTPUT_ROOT / "raw" / f"savant-baserunning-{season}.csv.gz"
    if old_path.exists():
        source_path = old_path
        content = gzip.decompress(old_path.read_bytes())
        source = "existing_certified_capture"
    elif output_path.exists():
        source_path = output_path
        content = gzip.decompress(output_path.read_bytes())
        source = "output_cache"
    else:
        response = requests.get(
            SAVANT_BASERUNNING_RUN_VALUE_URL,
            params=savant_baserunning_query_params(season),
            timeout=120,
            headers={"User-Agent": "universal-baseball-model-hitter-baserunning-v2/0.1"},
        )
        response.raise_for_status()
        content = response.content
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(output_path, "wb") as handle:
            handle.write(content)
        source_path = output_path
        source = "official_savant_download"
    rows = parse_savant_baserunning_csv(content.decode("utf-8-sig"))
    audit = audit_savant_baserunning_rows(rows)
    if not audit["advancement_source_usable"]:
        raise RuntimeError(f"Savant advancement source failed {season}: {audit}")
    return rows, {
        "season": season,
        "source": source,
        "path": str(source_path),
        "response_bytes": len(content),
        "response_sha256": sha256(content).hexdigest(),
        "row_count": len(rows),
        "audit": audit,
    }


def _components() -> pl.DataFrame:
    columns = list(pl.read_parquet_schema(CURRENT_COMPONENTS_PATH))
    return (
        pl.concat(
            [
                pl.read_parquet(HISTORICAL_COMPONENTS_PATH, columns=columns),
                pl.read_parquet(CURRENT_COMPONENTS_PATH, columns=columns),
            ]
        )
        .filter(pl.col("season").is_between(min(HISTORY_SEASONS), TARGET_SEASON))
        .unique(["season", "player_id", "sport_id", "team_id"], keep="last")
        .sort(["season", "player_id", "sport_id", "team_id"])
    )


def _actual_steal_war(components: pl.DataFrame, reference: BaserunningReference) -> pl.DataFrame:
    names = {
        "hits": "batting_hits",
        "doubles": "batting_doubles",
        "triples": "batting_triples",
        "home_runs": "batting_home_runs",
        "base_on_balls": "batting_base_on_balls",
        "intentional_walks": "batting_intentional_walks",
        "hit_by_pitch": "batting_hit_by_pitch",
        "stolen_bases": "batting_stolen_bases",
        "caught_stealing": "batting_caught_stealing",
    }
    mlb = components.filter(pl.col("level_group") == "MLB").rename(names)
    return steal_war_by_player_origin(
        mlb,
        origin=TARGET_SEASON - 1,
        horizon=1,
        runs_per_win=RUNS_PER_WIN,
        reference=reference,
    )


def main() -> None:
    base = pl.read_parquet(POSITION_PATH)
    reference = _reference()
    components = _components()

    rows_by_season: dict[int, list[dict[str, str]]] = {}
    captures = []
    for season in (*HISTORY_SEASONS, TARGET_SEASON):
        rows, capture = _load_or_fetch_savant(season)
        rows_by_season[season] = rows
        captures.append(capture)

    steal_history, environment_audit = build_steal_history(
        components.filter(pl.col("season").is_in(HISTORY_SEASONS))
    )
    advancement_history = build_advancement_history(
        {season: rows_by_season[season] for season in HISTORY_SEASONS}
    )
    rates = build_current_baserunning_rates(
        base.select("player_id"),
        steal_history,
        advancement_history,
        forecast_seasons=(TARGET_SEASON,),
        reference=reference,
    )

    actual_steals = _actual_steal_war(components, reference)
    actual_advancement = advancement_war_by_player_origin(
        pl.DataFrame(
            [
                {
                    "season": TARGET_SEASON,
                    "player_id": int(row["player_id"]),
                    "runner_runs_xb": float(row["runner_runs_xb"]),
                }
                for row in rows_by_season[TARGET_SEASON]
            ]
        ),
        origin=TARGET_SEASON - 1,
        horizon=1,
        runs_per_win=RUNS_PER_WIN,
    )

    frame = (
        base.join(
            rates.select(
                "player_id",
                "baserunning_runs_per_600",
                "steal_runs_per_600",
                "advancement_runs_per_600",
                "baserunning_evidence_tier",
            ),
            on="player_id",
            how="left",
            validate="1:1",
        )
        .join(actual_steals, on="player_id", how="left", validate="1:1")
        .join(actual_advancement, on="player_id", how="left", validate="1:1")
        .with_columns(
            pl.col("later_steal_war").fill_null(0.0),
            pl.col("later_steal_runs").fill_null(0.0),
            pl.col("later_advancement_war").fill_null(0.0),
            pl.col("later_advancement_runs").fill_null(0.0),
        )
        .with_columns(
            (
                pl.col("prediction_candidate_expected_pa")
                / 600.0
                * pl.col("steal_runs_per_600")
                / RUNS_PER_WIN
            ).alias("prediction_steal_war"),
            (
                pl.col("prediction_candidate_expected_pa")
                / 600.0
                * pl.col("advancement_runs_per_600")
                / RUNS_PER_WIN
            ).alias("prediction_advancement_war"),
            (pl.col("later_steal_war") + pl.col("later_advancement_war")).alias(
                "actual_baserunning_war"
            ),
        )
        .with_columns(
            (pl.col("prediction_steal_war") + pl.col("prediction_advancement_war")).alias(
                "prediction_baserunning_war"
            ),
            (pl.col("actual_partial_war") + pl.col("actual_baserunning_war")).alias(
                "actual_batting_position_baserunning_war"
            ),
            pl.col("prediction_transition_position_partial_war").alias(
                "prediction_position_only_war"
            ),
            (
                pl.col("prediction_transition_position_partial_war")
                + pl.col("prediction_steal_war")
            ).alias("prediction_position_plus_steal_war"),
            (
                pl.col("prediction_transition_position_partial_war")
                + pl.col("prediction_advancement_war")
            ).alias("prediction_position_plus_advancement_war"),
        )
        .with_columns(
            (
                pl.col("prediction_transition_position_partial_war")
                + pl.col("prediction_baserunning_war")
            ).alias("prediction_position_plus_baserunning_war"),
        )
        .sort("player_id")
    )

    target = frame["actual_batting_position_baserunning_war"].to_numpy()
    player_ids = frame["player_id"].to_numpy()
    methods = {
        "position_only": "prediction_position_only_war",
        "position_plus_steal": "prediction_position_plus_steal_war",
        "position_plus_advancement": "prediction_position_plus_advancement_war",
        "position_plus_baserunning": "prediction_position_plus_baserunning_war",
    }
    metrics = {
        name: regression_metrics(target, frame[column].to_numpy())
        for name, column in methods.items()
    }
    comparisons = {
        f"{name}_minus_position_only": paired_cluster_rmse_delta(
            target,
            frame[column].to_numpy(),
            frame[methods["position_only"]].to_numpy(),
            player_ids,
        )
        for name, column in methods.items()
        if name != "position_only"
    }
    component_columns = {
        "steal": ("later_steal_war", "prediction_steal_war"),
        "advancement": ("later_advancement_war", "prediction_advancement_war"),
        "combined": ("actual_baserunning_war", "prediction_baserunning_war"),
    }
    component_metrics = {}
    component_comparisons = {}
    for name, (actual_column, prediction_column) in component_columns.items():
        actual_component = frame[actual_column].to_numpy()
        predicted_component = frame[prediction_column].to_numpy()
        neutral_component = predicted_component * 0.0
        component_metrics[name] = {
            "neutral_zero": regression_metrics(actual_component, neutral_component),
            "player_specific": regression_metrics(
                actual_component, predicted_component
            ),
        }
        component_comparisons[f"{name}_model_minus_neutral_zero"] = (
            paired_cluster_rmse_delta(
                actual_component,
                predicted_component,
                neutral_component,
                player_ids,
            )
        )
    by_stage = {}
    for stage in ("current_mlb", "upper_minors", "lower_minors"):
        segment = frame.filter(pl.col("player_stage") == stage)
        segment_target = segment["actual_batting_position_baserunning_war"].to_numpy()
        by_stage[stage] = {
            name: regression_metrics(segment_target, segment[column].to_numpy())
            for name, column in methods.items()
        }

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    artifact = write_canonical_parquet(
        frame,
        OUTPUT_ROOT / "predictions.parquet",
        table_name="hitter_baserunning_value_v2_predictions",
    )
    report = {
        "schema_version": "0.1",
        "status": "hitter_baserunning_value_test_complete",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "target": "2025 batting plus replacement plus position plus baserunning WAR",
        "population_rows": frame.height,
        "runs_per_win": RUNS_PER_WIN,
        "model": {
            "steal_attempt": "B2_k5",
            "steal_success": "B2_k45",
            "nonsteal_advancement": "A2_k25",
            "gidp_residual": "omitted_as_nonadditive_with_batting",
            "history_seasons": list(HISTORY_SEASONS),
            "forecast_season": TARGET_SEASON,
            "expected_pa_source": "new hitter workload candidate",
        },
        "metrics": metrics,
        "paired_comparisons": comparisons,
        "component_metrics": component_metrics,
        "component_paired_comparisons": component_comparisons,
        "by_player_stage": by_stage,
        "evidence_tier_counts": frame.group_by("baserunning_evidence_tier")
        .len()
        .sort("baserunning_evidence_tier")
        .to_dicts(),
        "steal_environment_audit": asdict(environment_audit),
        "source_captures": captures,
        "sources": {
            "historical_components": {
                "path": str(HISTORICAL_COMPONENTS_PATH),
                "sha256": sha256_file(HISTORICAL_COMPONENTS_PATH),
            },
            "current_components": {
                "path": str(CURRENT_COMPONENTS_PATH),
                "sha256": sha256_file(CURRENT_COMPONENTS_PATH),
            },
            "position_predictions": {
                "path": str(POSITION_PATH),
                "sha256": sha256_file(POSITION_PATH),
            },
            "reference": {
                "path": str(REFERENCE_PATH),
                "sha256": sha256_file(REFERENCE_PATH),
            },
        },
        "artifact": artifact.as_record(),
        "limitations": [
            "This is an already-exposed 2025 development test, not final confirmation.",
            "Savant non-steal advancement exists only for MLB runners; MiLB-only players are neutral in that channel.",
            "GIDP is omitted because raw double-play value is not additive with the batting target.",
            "A missing 2025 Savant player row is treated as zero realized non-steal advancement value.",
        ],
    }
    (OUTPUT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
