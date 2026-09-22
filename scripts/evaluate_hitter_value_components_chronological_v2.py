#!/usr/bin/env python3
"""Forward-test position and baserunning inside the clean-slate hitter stack."""

from __future__ import annotations

from dataclasses import fields
from datetime import UTC, datetime
import gzip
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
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
from universal_baseball.historical_hitter_position import position_war_by_player_origin
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
from universal_baseball.player_value_positional_adjustment import (
    POSITIONAL_RUNS_PER_162,
)
from universal_baseball.position_role_profile import (
    BATTING_ROLE_POSITIONS,
    build_batting_role_profiles,
)
from universal_baseball.position_role_transition import (
    transition_smoothed_prediction,
    validate_role_vector,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


OLD_ROOT = Path(
    "C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/"
    "universal-baseball-model"
)
BATTING_PATH = Path(
    "reports/generated/hitter-model-finalist-tuning-v2/tables/"
    "finalist-ensemble-predictions.parquet"
)
WORKLOAD_PATH = Path(
    "reports/generated/hitter-workload-model-v2/chronological-predictions.parquet"
)
FIELDING_HISTORY_PATH = (
    OLD_ROOT
    / "reports/generated/position-capacity-source/historical/reports/generated/"
    "position-role-historical-source/tables/historical_fielding_usage.parquet"
)
MLB_FIELDING_PATH = (
    OLD_ROOT
    / "reports/generated/mlb-fielding-outcome-inventory-2004-2025/tables/"
    "mlb_fielding_usage_2004_2025.parquet"
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
POSITION_PARAMETER_PATH = Path("docs/position-role-confirmation-parameters.json")
BASERUNNING_REFERENCE_PATH = Path(
    "docs/player-value-v1-baserunning-run-conversion-2024.json"
)
OUTPUT_ROOT = Path("reports/generated/hitter-value-components-chronological-v2")
ORIGINS = (2021, 2022, 2023, 2024)
SAVANT_SEASONS = tuple(range(2019, 2026))
RUNS_PER_WIN = 10.0


def _baserunning_reference() -> BaserunningReference:
    payload = json.loads(BASERUNNING_REFERENCE_PATH.read_text(encoding="utf-8"))
    values = payload["reference"]
    return BaserunningReference(
        **{field.name: values[field.name] for field in fields(BaserunningReference)}
    )


def _position_parameters() -> tuple[float, dict[str, np.ndarray]]:
    payload = json.loads(POSITION_PARAMETER_PATH.read_text(encoding="utf-8"))
    parameters = payload["parameters"]
    if parameters["position_order"] != list(BATTING_ROLE_POSITIONS):
        raise ValueError("frozen position ordering changed")
    destination_means = {
        source: validate_role_vector(
            np.array(
                [
                    float(details["probabilities"][destination])
                    for destination in BATTING_ROLE_POSITIONS
                ]
            )
        )
        for source, details in parameters["destination_means"].items()
    }
    return float(parameters["primary_share_threshold"]), destination_means


def _position_rate(profile: np.ndarray) -> float:
    return float(
        sum(
            profile[index] * POSITIONAL_RUNS_PER_162[position]
            for index, position in enumerate(BATTING_ROLE_POSITIONS)
        )
    )


def _position_rates(
    players: pl.DataFrame,
    fielding: pl.DataFrame,
    *,
    origin: int,
    threshold: float,
    destination_means: dict[str, np.ndarray],
) -> pl.DataFrame:
    built = build_batting_role_profiles(fielding.filter(pl.col("season") == origin))
    profiles: dict[int, np.ndarray] = {}
    for row in built.profile.select(
        "player_id", "position_abbreviation", "role_probability"
    ).iter_rows(named=True):
        vector = profiles.setdefault(
            int(row["player_id"]), np.zeros(len(BATTING_ROLE_POSITIONS))
        )
        vector[BATTING_ROLE_POSITIONS.index(str(row["position_abbreviation"]))] = float(
            row["role_probability"]
        )
    profiles = {
        player_id: validate_role_vector(vector)
        for player_id, vector in profiles.items()
    }
    summaries = {
        int(row["player_id"]): (
            str(row["primary_position"]),
            float(row["primary_role_share"]),
        )
        for row in built.player_season.select(
            "player_id", "primary_position", "primary_role_share"
        ).iter_rows(named=True)
    }
    rows: list[dict[str, object]] = []
    for player_id in players["player_id"]:
        pid = int(player_id)
        current = profiles.get(pid)
        summary = summaries.get(pid)
        if current is None or summary is None:
            rows.append(
                {
                    "player_id": pid,
                    "position_profile_available": 0,
                    "current_position_runs_per_600": 0.0,
                    "predicted_position_runs_per_600": 0.0,
                }
            )
            continue
        primary, share = summary
        predicted = (
            transition_smoothed_prediction(
                current,
                primary_share=share,
                destination_mean=destination_means[primary],
            )
            if share >= threshold
            else current
        )
        rows.append(
            {
                "player_id": pid,
                "position_profile_available": 1,
                "current_position_runs_per_600": _position_rate(current),
                "predicted_position_runs_per_600": _position_rate(predicted),
            }
        )
    return pl.DataFrame(rows)


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
            headers={"User-Agent": "universal-baseball-model-chronological-value/0.1"},
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
        .filter(pl.col("season").is_between(2018, 2025))
        .unique(["season", "player_id", "sport_id", "team_id"], keep="last")
        .sort(["season", "player_id", "sport_id", "team_id"])
    )


def _actual_steals(
    components: pl.DataFrame,
    *,
    origin: int,
    reference: BaserunningReference,
) -> pl.DataFrame:
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
        origin=origin,
        horizon=1,
        runs_per_win=RUNS_PER_WIN,
        reference=reference,
    )


def _fold(
    *,
    origin: int,
    batting: pl.DataFrame,
    workload: pl.DataFrame,
    fielding: pl.DataFrame,
    mlb_fielding: pl.DataFrame,
    components: pl.DataFrame,
    savant_rows: dict[int, list[dict[str, str]]],
    threshold: float,
    destination_means: dict[str, np.ndarray],
    reference: BaserunningReference,
) -> pl.DataFrame:
    target_season = origin + 1
    base = batting.filter(pl.col("origin_year") == origin).select(
        "origin_year",
        "player_id",
        "player_stage",
        "actual_component_war",
        pl.col("prediction_candidate_equal_mean").alias(
            "prediction_batting_replacement_war"
        ),
    )
    expected_pa = workload.filter(pl.col("origin_year") == origin).select(
        "player_id", "prediction_candidate_expected_pa"
    )
    positions = _position_rates(
        base.select("player_id"),
        fielding,
        origin=origin,
        threshold=threshold,
        destination_means=destination_means,
    )
    actual_position = position_war_by_player_origin(
        mlb_fielding,
        origin=origin,
        horizon=1,
        runs_per_win=RUNS_PER_WIN,
    )

    history_seasons = tuple(range(origin - 2, origin + 1))
    steal_history, _ = build_steal_history(
        components.filter(pl.col("season").is_in(history_seasons))
    )
    advancement_history = build_advancement_history(
        {season: savant_rows[season] for season in history_seasons}
    )
    baserunning_rates = build_current_baserunning_rates(
        base.select("player_id"),
        steal_history,
        advancement_history,
        forecast_seasons=(target_season,),
        reference=reference,
    )
    actual_steals = _actual_steals(components, origin=origin, reference=reference)
    actual_advancement = advancement_war_by_player_origin(
        pl.DataFrame(
            [
                {
                    "season": target_season,
                    "player_id": int(row["player_id"]),
                    "runner_runs_xb": float(row["runner_runs_xb"]),
                }
                for row in savant_rows[target_season]
            ]
        ),
        origin=origin,
        horizon=1,
        runs_per_win=RUNS_PER_WIN,
    )

    return (
        base.join(expected_pa, on="player_id", how="left", validate="1:1")
        .join(positions, on="player_id", how="left", validate="1:1")
        .join(actual_position, on="player_id", how="left", validate="1:1")
        .join(
            baserunning_rates.select(
                "player_id",
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
            pl.col("later_position_war").fill_null(0.0),
            pl.col("later_steal_war").fill_null(0.0),
            pl.col("later_advancement_war").fill_null(0.0),
        )
        .with_columns(
            (
                pl.col("prediction_candidate_expected_pa")
                / 600.0
                * pl.col("current_position_runs_per_600")
                / RUNS_PER_WIN
            ).alias("prediction_carry_position_war"),
            (
                pl.col("prediction_candidate_expected_pa")
                / 600.0
                * pl.col("predicted_position_runs_per_600")
                / RUNS_PER_WIN
            ).alias("prediction_transition_position_war"),
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
        )
        .with_columns(
            (pl.col("later_steal_war") + pl.col("later_advancement_war")).alias(
                "actual_baserunning_war"
            ),
            (pl.col("prediction_steal_war") + pl.col("prediction_advancement_war")).alias(
                "prediction_baserunning_war"
            ),
        )
        .with_columns(
            (
                pl.col("actual_component_war")
                + pl.col("later_position_war")
                + pl.col("actual_baserunning_war")
            ).alias("actual_partial_war"),
            pl.col("prediction_batting_replacement_war").alias(
                "prediction_batting_only_partial_war"
            ),
            (
                pl.col("prediction_batting_replacement_war")
                + pl.col("prediction_carry_position_war")
            ).alias("prediction_carry_position_partial_war"),
            (
                pl.col("prediction_batting_replacement_war")
                + pl.col("prediction_transition_position_war")
            ).alias("prediction_transition_position_partial_war"),
        )
        .with_columns(
            (
                pl.col("prediction_transition_position_partial_war")
                + pl.col("prediction_steal_war")
            ).alias("prediction_position_plus_steal_partial_war"),
            (
                pl.col("prediction_transition_position_partial_war")
                + pl.col("prediction_advancement_war")
            ).alias("prediction_position_plus_advancement_partial_war"),
            (
                pl.col("prediction_transition_position_partial_war")
                + pl.col("prediction_baserunning_war")
            ).alias("prediction_selected_partial_war"),
        )
        .sort("player_id")
    )


def _metrics(frame: pl.DataFrame) -> dict[str, dict[str, float]]:
    target = frame["actual_partial_war"].to_numpy()
    methods = {
        "batting_only": "prediction_batting_only_partial_war",
        "carry_position": "prediction_carry_position_partial_war",
        "transition_position": "prediction_transition_position_partial_war",
        "position_plus_steal": "prediction_position_plus_steal_partial_war",
        "position_plus_advancement": "prediction_position_plus_advancement_partial_war",
        "selected_position_plus_baserunning": "prediction_selected_partial_war",
    }
    return {
        name: regression_metrics(target, frame[column].to_numpy())
        for name, column in methods.items()
    }


def main() -> None:
    batting = pl.read_parquet(BATTING_PATH).filter(pl.col("origin_year").is_in(ORIGINS))
    workload = pl.read_parquet(WORKLOAD_PATH).filter(
        pl.col("origin_year").is_in(ORIGINS)
    )
    fielding = pl.read_parquet(FIELDING_HISTORY_PATH)
    mlb_fielding = pl.read_parquet(MLB_FIELDING_PATH)
    components = _components()
    threshold, destination_means = _position_parameters()
    reference = _baserunning_reference()

    savant_rows: dict[int, list[dict[str, str]]] = {}
    captures: list[dict[str, object]] = []
    for season in SAVANT_SEASONS:
        rows, capture = _load_or_fetch_savant(season)
        savant_rows[season] = rows
        captures.append(capture)

    folds = [
        _fold(
            origin=origin,
            batting=batting,
            workload=workload,
            fielding=fielding,
            mlb_fielding=mlb_fielding,
            components=components,
            savant_rows=savant_rows,
            threshold=threshold,
            destination_means=destination_means,
            reference=reference,
        )
        for origin in ORIGINS
    ]
    frame = pl.concat(folds).sort(["origin_year", "player_id"])
    target = frame["actual_partial_war"].to_numpy()
    player_ids = frame["player_id"].to_numpy()
    selected = frame["prediction_selected_partial_war"].to_numpy()
    batting_only = frame["prediction_batting_only_partial_war"].to_numpy()
    transition = frame["prediction_transition_position_partial_war"].to_numpy()
    carry = frame["prediction_carry_position_partial_war"].to_numpy()

    by_fold = {
        str(origin + 1): {
            "rows": frame.filter(pl.col("origin_year") == origin).height,
            "position_profile_coverage": float(
                frame.filter(pl.col("origin_year") == origin)[
                    "position_profile_available"
                ].mean()
            ),
            "metrics": _metrics(frame.filter(pl.col("origin_year") == origin)),
        }
        for origin in ORIGINS
    }
    by_stage = {
        stage: _metrics(frame.filter(pl.col("player_stage") == stage))
        for stage in ("current_mlb", "upper_minors", "lower_minors")
    }
    component_metrics = {}
    for name, actual_column, prediction_column in (
        ("position", "later_position_war", "prediction_transition_position_war"),
        ("steal", "later_steal_war", "prediction_steal_war"),
        (
            "advancement",
            "later_advancement_war",
            "prediction_advancement_war",
        ),
        (
            "baserunning",
            "actual_baserunning_war",
            "prediction_baserunning_war",
        ),
    ):
        actual = frame[actual_column].to_numpy()
        prediction = frame[prediction_column].to_numpy()
        component_metrics[name] = {
            "neutral_zero": regression_metrics(actual, np.zeros_like(actual)),
            "player_specific": regression_metrics(actual, prediction),
            "model_minus_neutral_zero": paired_cluster_rmse_delta(
                actual,
                prediction,
                np.zeros_like(actual),
                player_ids,
            ),
        }

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    artifact = write_canonical_parquet(
        frame,
        OUTPUT_ROOT / "chronological-predictions.parquet",
        table_name="hitter_value_components_chronological_v2_predictions",
    )
    report = {
        "schema_version": "0.1",
        "status": "hitter_value_components_chronological_test_complete",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "target_seasons": [origin + 1 for origin in ORIGINS],
        "population_rows": frame.height,
        "target": "next-season MLB batting plus replacement plus position plus baserunning WAR",
        "pooled_metrics": _metrics(frame),
        "paired_comparisons": {
            "transition_position_minus_batting_only": paired_cluster_rmse_delta(
                target, transition, batting_only, player_ids
            ),
            "transition_minus_carry_position": paired_cluster_rmse_delta(
                target, transition, carry, player_ids
            ),
            "selected_minus_transition_position": paired_cluster_rmse_delta(
                target, selected, transition, player_ids
            ),
            "selected_minus_batting_only": paired_cluster_rmse_delta(
                target, selected, batting_only, player_ids
            ),
        },
        "component_metrics": component_metrics,
        "by_target_season": by_fold,
        "by_player_stage": by_stage,
        "evidence_tier_counts": frame.group_by(
            "origin_year", "baserunning_evidence_tier"
        )
        .len()
        .sort("origin_year", "baserunning_evidence_tier")
        .to_dicts(),
        "source_captures": captures,
        "model": {
            "position": "frozen role-transition model scaled by new expected PA",
            "steal_attempt": "B2_k5",
            "steal_success": "B2_k45",
            "nonsteal_advancement": "A2_k25",
            "history_window": "three seasons through each forecast origin",
        },
        "sources": {
            "batting": {"path": str(BATTING_PATH), "sha256": sha256_file(BATTING_PATH)},
            "workload": {
                "path": str(WORKLOAD_PATH),
                "sha256": sha256_file(WORKLOAD_PATH),
            },
            "fielding_history": {
                "path": str(FIELDING_HISTORY_PATH),
                "sha256": sha256_file(FIELDING_HISTORY_PATH),
            },
            "mlb_fielding_outcomes": {
                "path": str(MLB_FIELDING_PATH),
                "sha256": sha256_file(MLB_FIELDING_PATH),
            },
            "historical_components": {
                "path": str(HISTORICAL_COMPONENTS_PATH),
                "sha256": sha256_file(HISTORICAL_COMPONENTS_PATH),
            },
            "current_components": {
                "path": str(CURRENT_COMPONENTS_PATH),
                "sha256": sha256_file(CURRENT_COMPONENTS_PATH),
            },
        },
        "artifact": artifact.as_record(),
        "limitations": [
            "This is development evidence and does not access 2026 outcomes.",
            "Affiliated fielding-role history begins in 2021, so the common chronological component test covers 2022-2025.",
            "Savant non-steal advancement exists only for MLB runners; MiLB-only players are neutral in that channel.",
            "General and catcher defense remain outside this partial-WAR target.",
        ],
    }
    (OUTPUT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
