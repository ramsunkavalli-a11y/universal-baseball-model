#!/usr/bin/env python3
"""Refit and freeze retained Defense v1 components before any 2025 target access."""

from __future__ import annotations

import argparse
from hashlib import sha256
from importlib.metadata import version
import json
import math
from pathlib import Path
import platform
from typing import Any, Mapping

import numpy as np
import polars as pl

from audit_defense_v1_tracked_challenger import _range_subset, _z_range
from develop_defense_v1_universal import (
    GENERAL_FEATURES,
    INPUT_BY_TARGET,
    TARGET_YEARS,
    _catcher_matrix,
    _catcher_targets,
    _fit_catcher_normalizer,
    _fit_general_normalizer,
    _general_matrix,
    _general_targets,
    _load_profiles,
    _ridge_fit,
)


REPORT_ROOT = Path("reports/generated/defense-v1-parameter-freeze")
TABLE_ROOT = REPORT_ROOT / "tables"
EXPECTED_HISTORICAL_RUN = 32148467330
EXPECTED_HISTORICAL_ARTIFACT = "position-role-historical-source-2021-2024"
EXPECTED_HISTORICAL_ARTIFACT_DIGEST = "sha256:908022d38b3652db1c2b68a7ba2768954c32f8973f0ace85c9557d30522adaf3"
EXPECTED_TRACKED_RUN = 32182019495
EXPECTED_TRACKED_ARTIFACT = "defense-v1-tracked-source-2021-2023"
EXPECTED_TRACKED_ARTIFACT_DIGEST = "sha256:a177f04655cc497534c85f47d94aa597b273358154eb76999b4a0bc9d5584de4"
EXPECTED_TRACKED_SHA = "5438e905d24e2167432a52253320ccbc978186b8"


def _sha_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + sha256(payload).hexdigest()


def _find_one(root: Path, name: str) -> Path:
    matches = list(root.rglob(name))
    if len(matches) != 1:
        raise RuntimeError(f"expected one {name} under {root}; observed={matches}")
    return matches[0]


def _tree_manifest(root: Path, pattern: str) -> dict[str, Any]:
    paths = sorted(root.rglob(pattern))
    if not paths:
        raise RuntimeError(f"no {pattern} files under {root}")
    rows = []
    total = 0
    for path in paths:
        size = path.stat().st_size
        total += size
        rows.append(
            {
                "path": str(path.relative_to(root)).replace("\\", "/"),
                "size_bytes": size,
                "sha256": _sha_file(path),
            }
        )
    return {
        "file_count": len(rows),
        "total_size_bytes": total,
        "manifest_sha256": _canonical_hash(rows),
    }


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_preconditions(
    universal: Mapping[str, Any],
    tracked: Mapping[str, Any],
    tracked_source: Mapping[str, Any],
) -> None:
    if universal["decision"]["selected_general_range_family"] != {"family": "U1", "lambda": 0.0}:
        raise RuntimeError("universal general selection is not frozen U1 lambda 0.0")
    if universal["decision"]["selected_catcher_throwing_family"] != "C1":
        raise RuntimeError("catcher throwing selection is not frozen C1")
    if universal["decision"]["selected_catcher_blocking_family"] != "C2":
        raise RuntimeError("catcher blocking selection is not frozen C2")
    decision = tracked["decision"]
    required = {
        "pre_2025_defense_development_closed": True,
        "final_refit_and_parameter_freeze_authorized_next": True,
        "tier_a_tracked_range_passed": True,
        "tier_b_tracked_range_transfer_passed": False,
        "tier_a_tracked_framing_passed": False,
        "2025_confirmation_authorized": False,
        "war_value_authorized": False,
    }
    for key, expected in required.items():
        if decision.get(key) is not expected:
            raise RuntimeError(f"tracked result precondition {key}={decision.get(key)!r}; expected {expected!r}")
    boundary = tracked.get("boundary", {})
    if boundary.get("2025_defensive_targets_accessed") is not False:
        raise RuntimeError("tracked result indicates 2025 defensive targets were accessed")
    if boundary.get("run_value_conversion_performed") is not False:
        raise RuntimeError("tracked result indicates run-value conversion")
    if tracked_source.get("source_run_id") != EXPECTED_TRACKED_RUN:
        raise RuntimeError("tracked source run changed")
    if tracked_source.get("source_sha") != EXPECTED_TRACKED_SHA:
        raise RuntimeError("tracked source SHA changed")
    if tracked_source.get("boundary", {}).get("2025_source_accessed") is not False:
        raise RuntimeError("tracked source crossed 2025 boundary")


def _general_normalizer_payload(normalizer: Any) -> dict[str, Any]:
    cell_rows = []
    position_rows = []
    global_rows = []
    for feature in GENERAL_FEATURES:
        for (position, level), moment in sorted(normalizer.cell[feature].items()):
            cell_rows.append(
                {
                    "feature": feature,
                    "position": position,
                    "level_group": level,
                    "mean": float(moment.mean),
                    "sd": float(moment.sd),
                    "count": int(moment.count),
                }
            )
        for position, moment in sorted(normalizer.position[feature].items()):
            position_rows.append(
                {
                    "feature": feature,
                    "position": position,
                    "mean": float(moment.mean),
                    "sd": float(moment.sd),
                    "count": int(moment.count),
                }
            )
        moment = normalizer.global_[feature]
        global_rows.append(
            {
                "feature": feature,
                "mean": float(moment.mean),
                "sd": float(moment.sd),
                "count": int(moment.count),
            }
        )
    return {"cell": cell_rows, "position": position_rows, "global": global_rows}


def _catcher_normalizer_payload(normalizer: Any) -> dict[str, Any]:
    return {
        "feature": str(normalizer.feature),
        "mean": float(normalizer.moment.mean),
        "sd": float(normalizer.moment.sd),
        "count": int(normalizer.moment.count),
    }


def _tracked_range_moments(frame: pl.DataFrame) -> pl.DataFrame:
    eligible = frame.filter(
        pl.col("position_abbreviation").is_in(["1B", "2B", "3B", "SS", "LF", "CF", "RF"])
        & (pl.col("opportunities") >= 100)
        & pl.col("tracked_oaa_per_100").is_not_null()
    )
    return (
        eligible.group_by(["season", "level_group", "position_abbreviation"])
        .agg(
            pl.col("tracked_oaa_per_100").mean().alias("mean"),
            pl.col("tracked_oaa_per_100").std(ddof=0).alias("sd"),
            pl.len().alias("count"),
        )
        .with_columns(
            (
                (pl.col("count") >= 20)
                & pl.col("sd").is_not_null()
                & (pl.col("sd") > 1e-12)
            ).alias("tracked_z_available")
        )
        .sort(["season", "level_group", "position_abbreviation"])
    )


def _coefficient_rows(component: str, terms: list[str], beta: np.ndarray) -> list[dict[str, Any]]:
    labels = ["intercept", *terms]
    if len(labels) != len(beta):
        raise RuntimeError(f"coefficient width mismatch for {component}")
    return [
        {"component": component, "term": term, "coefficient": float(value)}
        for term, value in zip(labels, beta, strict=True)
    ]


def _training_rows(
    component: str,
    meta: list[dict[str, Any]],
    profiles_index: dict[tuple[int, int], Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for item in meta:
        target_year = int(item["target_year"])
        input_year = int(INPUT_BY_TARGET[target_year])
        player_id = int(item["player_id"])
        profile = profiles_index.get((input_year, player_id))
        rows.append(
            {
                "component": component,
                "player_id": player_id,
                "input_year": input_year,
                "target_year": target_year,
                "input_position": None if profile is None else str(profile["position"]),
                "input_level_group": None if profile is None else str(profile["current_level_group"]),
            }
        )
    return rows


def _fit_once(
    primary: pl.DataFrame,
    catcher: pl.DataFrame,
    general_targets: dict[int, pl.DataFrame],
    throwing_targets: dict[int, pl.DataFrame],
    blocking_targets: dict[int, pl.DataFrame],
    tracked_range: pl.DataFrame,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    all_target_years = set(TARGET_YEARS)
    input_years = {INPUT_BY_TARGET[year] for year in TARGET_YEARS}
    profiles_index = {
        (int(row["season"]), int(row["player_id"])): row
        for row in primary.iter_rows(named=True)
    }

    general_normalizer = _fit_general_normalizer(primary, input_years)
    x_u1, y_u1, meta_u1 = _general_matrix(primary, general_targets, all_target_years, general_normalizer, "U1")
    if not len(y_u1):
        raise RuntimeError("empty final U1 training set")
    beta_u1 = _ridge_fit(x_u1, y_u1, 0.0)

    tracked_z = _z_range(tracked_range)
    x_t1, y_t1, z_t1, meta_t1 = _range_subset(
        x_u1,
        y_u1,
        meta_u1,
        profiles_index,
        tracked_z,
        mode="MLB",
    )
    if not len(y_t1):
        raise RuntimeError("empty final T1 tracked-MLB training set")
    beta_t1 = _ridge_fit(np.column_stack([x_t1, z_t1]), y_t1, 0.0)

    throwing_normalizer = _fit_catcher_normalizer(catcher, input_years, "caught_stealing_pct", "throwing")
    x_throw, y_throw, meta_throw = _catcher_matrix(
        catcher,
        throwing_targets,
        all_target_years,
        throwing_normalizer,
        "C1",
        "throwing",
    )
    if not len(y_throw):
        raise RuntimeError("empty final C1 throwing training set")
    beta_throw = _ridge_fit(x_throw, y_throw, 0.0)

    blocking_normalizer = _fit_catcher_normalizer(catcher, input_years, "passed_balls_per_9", "blocking")
    x_block, y_block, meta_block = _catcher_matrix(
        catcher,
        blocking_targets,
        all_target_years,
        blocking_normalizer,
        "C2",
        "blocking",
    )
    if not len(y_block):
        raise RuntimeError("empty final C2 blocking training set")
    beta_block = _ridge_fit(x_block, y_block, 0.0)

    if not all(
        np.isfinite(beta).all()
        for beta in (beta_u1, beta_t1, beta_throw, beta_block)
    ):
        raise RuntimeError("nonfinite final Defense v1 coefficient")

    general_norm = _general_normalizer_payload(general_normalizer)
    parameters = {
        "model_name": "defense_v1_pre_2025_parameter_package",
        "training_target_years": list(TARGET_YEARS),
        "training_input_years": sorted(input_years),
        "general": {
            "universal": {
                "family": "U1",
                "lambda": 0.0,
                "raw_features": list(GENERAL_FEATURES),
                "normalized_terms": [f"{feature}_z" for feature in GENERAL_FEATURES],
                "coefficients": [float(value) for value in beta_u1],
                "training_row_count": int(len(y_u1)),
            },
            "tracked_mlb": {
                "family": "T1",
                "lambda": 0.0,
                "definition": "exact U1 features plus tracked_range_z on MLB tracked-eligible rows",
                "normalized_terms": [f"{feature}_z" for feature in GENERAL_FEATURES] + ["tracked_range_z"],
                "coefficients": [float(value) for value in beta_t1],
                "training_row_count": int(len(y_t1)),
                "retained_levels": ["MLB"],
            },
            "normalization": {
                "rule": "fit on all authorized 2021-2023 input evidence; cell position x current_level_group when count>=30, then position fallback, then global fallback",
                **general_norm,
            },
            "eligibility": {
                "positions": ["1B", "2B", "3B", "SS", "LF", "CF", "RF"],
                "minimum_fielding_outs": 300,
                "minimum_chances": 100,
                "exact_next_year_target_position_match": True,
            },
            "coverage_fallback": {
                "eligible_mlb_with_eligible_tracking": "T1",
                "eligible_mlb_without_eligible_tracking": "U1",
                "eligible_affiliated_milb": "U1",
                "insufficient_u1_evidence": "B0_neutral_position_relative",
                "tracked_milb_t1": "closed_for_v1",
            },
        },
        "catcher_throwing": {
            "family": "C1",
            "feature": "caught_stealing_pct",
            "normalized_term": "caught_stealing_pct_z",
            "lambda": 0.0,
            "coefficients": [float(value) for value in beta_throw],
            "normalization": _catcher_normalizer_payload(throwing_normalizer),
            "training_row_count": int(len(y_throw)),
            "eligibility": {"minimum_fielding_outs": 300, "minimum_steal_attempts": 10},
            "insufficient_evidence_fallback": "B0_neutral",
        },
        "catcher_blocking": {
            "family": "C2",
            "feature": "passed_balls_per_9",
            "normalized_term": "passed_balls_per_9_z_two_season_recency_exposure",
            "lambda": 0.0,
            "prior_season_recency_weight": 0.5,
            "exposure": "fielding_outs",
            "coefficients": [float(value) for value in beta_block],
            "normalization": _catcher_normalizer_payload(blocking_normalizer),
            "training_row_count": int(len(y_block)),
            "eligibility": {"minimum_fielding_outs": 300},
            "insufficient_evidence_fallback": "B0_neutral",
        },
        "tracked_range_feature": {
            "raw_formula": "100 * oaa / opportunities",
            "minimum_opportunities": 100,
            "standardization": "within source season x tracked level x position",
            "minimum_eligible_players_per_cell": 20,
            "degenerate_cell_behavior": "feature unavailable; do not pool across position or level",
            "confirmation_2024_mlb_moments": "target-free source moments materialized only after this freeze under the confirmation contract",
        },
        "target_scale": {
            "general_range": "within target year x position z-score of Savant diff_success_rate_formatted",
            "catcher_throwing": "within target year z-score of Savant cs_aa_per_throw, target sb_attempts>=10",
            "catcher_blocking": "within target year z-score of Savant blocks_above_average_per_game, target pitches>=500",
        },
        "closed": {
            "age_A1": True,
            "traditional_feature_search": True,
            "tracked_framing_F1": True,
            "tracked_milb_T1": True,
            "additional_pre_2025_challenger_search": True,
        },
    }

    coeff_rows = []
    coeff_rows.extend(_coefficient_rows("general_U1", [f"{f}_z" for f in GENERAL_FEATURES], beta_u1))
    coeff_rows.extend(
        _coefficient_rows("general_T1_MLB", [f"{f}_z" for f in GENERAL_FEATURES] + ["tracked_range_z"], beta_t1)
    )
    coeff_rows.extend(_coefficient_rows("catcher_throwing_C1", ["caught_stealing_pct_z"], beta_throw))
    coeff_rows.extend(_coefficient_rows("catcher_blocking_C2", ["passed_balls_per_9_z_two_season"], beta_block))

    training_rows = []
    training_rows.extend(_training_rows("general_U1", meta_u1, profiles_index))
    training_rows.extend(_training_rows("general_T1_MLB", meta_t1, profiles_index))
    training_rows.extend(_training_rows("catcher_throwing_C1", meta_throw, profiles_index))
    training_rows.extend(_training_rows("catcher_blocking_C2", meta_block, profiles_index))
    return parameters, coeff_rows, training_rows


def _target_table(
    general_targets: dict[int, pl.DataFrame],
    throwing_targets: dict[int, pl.DataFrame],
    blocking_targets: dict[int, pl.DataFrame],
) -> pl.DataFrame:
    frames = []
    for year, frame in general_targets.items():
        frames.append(
            frame.select(
                pl.lit("general_range").alias("component"),
                pl.lit(int(year)).alias("target_year"),
                "player_id",
                pl.col("position").cast(pl.Utf8),
                "target_raw",
                "target_z",
            )
        )
    for component, targets in (("catcher_throwing", throwing_targets), ("catcher_blocking", blocking_targets)):
        for year, frame in targets.items():
            frames.append(
                frame.select(
                    pl.lit(component).alias("component"),
                    pl.lit(int(year)).alias("target_year"),
                    "player_id",
                    pl.lit(None, dtype=pl.Utf8).alias("position"),
                    "target_raw",
                    "target_z",
                )
            )
    return pl.concat(frames, how="vertical_relaxed").sort(["component", "target_year", "player_id"])


def _table_storage(path: Path, table_name: str, row_count: int) -> dict[str, Any]:
    return {
        "table_name": table_name,
        "path": str(path).replace("\\", "/"),
        "row_count": int(row_count),
        "file_size_bytes": path.stat().st_size,
        "sha256": _sha_file(path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--historical-root", type=Path, required=True)
    parser.add_argument("--tracked-root", type=Path, required=True)
    parser.add_argument("--universal-result", type=Path, required=True)
    parser.add_argument("--tracked-result", type=Path, required=True)
    parser.add_argument("--tracked-source-result", type=Path, required=True)
    parser.add_argument("--confirmation-contract", type=Path, required=True)
    args = parser.parse_args()

    universal = _load_json(args.universal_result)
    tracked_result = _load_json(args.tracked_result)
    tracked_source_result = _load_json(args.tracked_source_result)
    _assert_preconditions(universal, tracked_result, tracked_source_result)

    contract_sha256 = _sha_file(args.confirmation_contract)
    historical_manifest = _tree_manifest(args.historical_root, "fielding_offset_*.json")
    tracked_path = _find_one(args.tracked_root, "tracked_range_proxy_2021_2023.parquet")
    tracked_actual_sha = _sha_file(tracked_path)
    tracked_expected_sha = tracked_source_result["storage"]["range"]["sha256"]
    if tracked_actual_sha != tracked_expected_sha:
        raise RuntimeError(f"tracked range SHA mismatch {tracked_actual_sha} != {tracked_expected_sha}")

    primary, profile_meta = _load_profiles(args.historical_root)
    catcher = profile_meta["catcher"]
    profile_counts = {key: value for key, value in profile_meta.items() if key != "catcher"}
    general_targets = _general_targets()
    throwing_targets = _catcher_targets("throwing")
    blocking_targets = _catcher_targets("blocking")
    tracked_range = pl.read_parquet(tracked_path)

    parameters, coefficient_rows, training_rows = _fit_once(
        primary,
        catcher,
        general_targets,
        throwing_targets,
        blocking_targets,
        tracked_range,
    )
    reproduction, _, _ = _fit_once(
        primary,
        catcher,
        general_targets,
        throwing_targets,
        blocking_targets,
        tracked_range,
    )
    deterministic = parameters == reproduction
    if not deterministic:
        raise RuntimeError("Defense v1 final refit is not deterministically reproducible")

    TABLE_ROOT.mkdir(parents=True, exist_ok=True)
    coefficients = pl.DataFrame(coefficient_rows).sort(["component", "term"])
    training = pl.DataFrame(training_rows).sort(["component", "target_year", "player_id"])
    targets = _target_table(general_targets, throwing_targets, blocking_targets)
    tracked_moments = _tracked_range_moments(tracked_range)

    general_norm_rows = []
    for scope in ("cell", "position", "global"):
        for row in parameters["general"]["normalization"][scope]:
            general_norm_rows.append({"scope": scope, **row})
    general_norm = pl.DataFrame(general_norm_rows)
    catcher_norm = pl.DataFrame(
        [
            {"component": "catcher_throwing_C1", **parameters["catcher_throwing"]["normalization"]},
            {"component": "catcher_blocking_C2", **parameters["catcher_blocking"]["normalization"]},
        ]
    )

    paths = {
        "coefficients": TABLE_ROOT / "coefficients.parquet",
        "training_rows": TABLE_ROOT / "training_rows.parquet",
        "development_targets": TABLE_ROOT / "development_targets.parquet",
        "general_normalization": TABLE_ROOT / "general_normalization.parquet",
        "catcher_normalization": TABLE_ROOT / "catcher_normalization.parquet",
        "tracked_range_development_moments": TABLE_ROOT / "tracked_range_development_moments.parquet",
    }
    coefficients.write_parquet(paths["coefficients"], compression="zstd")
    training.write_parquet(paths["training_rows"], compression="zstd")
    targets.write_parquet(paths["development_targets"], compression="zstd")
    general_norm.write_parquet(paths["general_normalization"], compression="zstd")
    catcher_norm.write_parquet(paths["catcher_normalization"], compression="zstd")
    tracked_moments.write_parquet(paths["tracked_range_development_moments"], compression="zstd")

    parameter_hash = _canonical_hash(parameters)
    report = {
        "report_schema_version": "0.1",
        "gate": "defense_v1_pre_2025_parameter_freeze",
        "status": "frozen_ready_for_confirmation_source_materialization",
        "contract": str(args.confirmation_contract).replace("\\", "/"),
        "contract_sha256": contract_sha256,
        "parameter_hash": parameter_hash,
        "parameters": parameters,
        "deterministic_reproduction": {"passed": deterministic, "comparison": "exact canonical parameter object equality"},
        "package_versions": {
            "python": platform.python_version(),
            "numpy": version("numpy"),
            "polars": version("polars"),
            "sportsdataverse": version("sportsdataverse"),
        },
        "source": {
            "historical": {
                "run_id": EXPECTED_HISTORICAL_RUN,
                "artifact_name": EXPECTED_HISTORICAL_ARTIFACT,
                "artifact_digest": EXPECTED_HISTORICAL_ARTIFACT_DIGEST,
                **historical_manifest,
                **profile_counts,
            },
            "tracked": {
                "run_id": EXPECTED_TRACKED_RUN,
                "source_sha": EXPECTED_TRACKED_SHA,
                "artifact_name": EXPECTED_TRACKED_ARTIFACT,
                "artifact_digest": EXPECTED_TRACKED_ARTIFACT_DIGEST,
                "range_file_sha256": tracked_actual_sha,
                "range_row_count": int(tracked_range.height),
            },
            "development_target_years": list(TARGET_YEARS),
            "target_rows": {
                "general_range": {str(year): int(frame.height) for year, frame in general_targets.items()},
                "catcher_throwing": {str(year): int(frame.height) for year, frame in throwing_targets.items()},
                "catcher_blocking": {str(year): int(frame.height) for year, frame in blocking_targets.items()},
            },
        },
        "storage": {
            "coefficients": _table_storage(paths["coefficients"], "defense_v1_frozen_coefficients", coefficients.height),
            "training_rows": _table_storage(paths["training_rows"], "defense_v1_frozen_training_rows", training.height),
            "development_targets": _table_storage(paths["development_targets"], "defense_v1_frozen_development_targets", targets.height),
            "general_normalization": _table_storage(paths["general_normalization"], "defense_v1_frozen_general_normalization", general_norm.height),
            "catcher_normalization": _table_storage(paths["catcher_normalization"], "defense_v1_frozen_catcher_normalization", catcher_norm.height),
            "tracked_range_development_moments": _table_storage(
                paths["tracked_range_development_moments"],
                "defense_v1_tracked_range_development_moments",
                tracked_moments.height,
            ),
        },
        "decision": {
            "pre_2025_parameters_frozen": True,
            "defense_v1_final_confirmation_complete": False,
            "2024_mlb_tracking_confirmation_predictor_materialization_authorized": True,
            "2025_defensive_target_source_materialization_authorized": True,
            "2025_confirmation_scoring_authorized_after_source_certification": True,
            "additional_development_challenger_authorized": False,
            "war_value_authorized": False,
        },
        "boundary": {
            "2024_tracking_confirmation_predictor_accessed": False,
            "2025_defensive_targets_accessed": False,
            "2025_defensive_source_materialized": False,
            "model_form_reselected": False,
            "development_thresholds_changed": False,
            "run_value_conversion_performed": False,
            "playing_time_v1_modified": False,
            "position_role_v1_modified": False,
        },
    }

    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    (REPORT_ROOT / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = [
        "# Defense v1 pre-2025 parameter freeze",
        "",
        f"- parameter hash: `{parameter_hash}`",
        f"- U1 rows: {parameters['general']['universal']['training_row_count']}",
        f"- T1 MLB tracked rows: {parameters['general']['tracked_mlb']['training_row_count']}",
        f"- C1 throwing rows: {parameters['catcher_throwing']['training_row_count']}",
        f"- C2 blocking rows: {parameters['catcher_blocking']['training_row_count']}",
        "- deterministic reproduction: passed",
        "- 2024 confirmation tracking accessed: False",
        "- 2025 defensive targets accessed: False",
        "- WAR/value authorized: False",
        "",
    ]
    (REPORT_ROOT / "report.md").write_text("\n".join(summary), encoding="utf-8")
    print("\n".join(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
