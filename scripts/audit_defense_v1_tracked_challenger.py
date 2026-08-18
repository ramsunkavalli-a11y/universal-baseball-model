#!/usr/bin/env python3
"""Score the final pre-2025 Defense v1 tracked-evidence challenger."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

from sportsdataverse.mlb.mlb_statcast import mlb_statcast_leaderboard_catcher_framing

from develop_defense_v1_universal import (
    INPUT_BY_TARGET,
    TARGET_YEARS,
    _fit_general_normalizer,
    _float_text,
    _general_matrix,
    _general_targets,
    _load_profiles,
    _metrics,
    _predict,
    _ridge_fit,
)


REPORT_ROOT = Path("reports/generated/defense-v1-tracked-challenger")
SOURCE_RESULT = Path("docs/defense-v1-tracked-source-result.json")
UNIVERSAL_RESULT = Path("docs/defense-v1-universal-development-result.json")
AGE_RESULT = Path("docs/defense-v1-age-challenger-result.json")
GENERAL_POSITIONS = {"1B", "2B", "3B", "SS", "LF", "CF", "RF"}


def _find_one(root: Path, name: str) -> Path:
    matches = list(root.rglob(name))
    if len(matches) != 1:
        raise RuntimeError(f"expected one {name} under {root}, observed={matches}")
    return matches[0]


def _z_range(frame: pl.DataFrame) -> dict[tuple[int, str, int, str], float]:
    eligible = frame.filter(
        pl.col("position_abbreviation").is_in(sorted(GENERAL_POSITIONS))
        & (pl.col("opportunities") >= 100)
        & pl.col("tracked_oaa_per_100").is_not_null()
    )
    moments = eligible.group_by(["season", "level_group", "position_abbreviation"]).agg(
        pl.col("tracked_oaa_per_100").mean().alias("mean"),
        pl.col("tracked_oaa_per_100").std(ddof=0).alias("sd"),
        pl.len().alias("n"),
    )
    scored = (
        eligible.join(moments, on=["season", "level_group", "position_abbreviation"], how="left")
        .filter((pl.col("n") >= 20) & pl.col("sd").is_not_null() & (pl.col("sd") > 1e-12))
        .with_columns(((pl.col("tracked_oaa_per_100") - pl.col("mean")) / pl.col("sd")).alias("tracked_z"))
    )
    return {
        (int(row["season"]), str(row["level_group"]), int(row["player_id"]), str(row["position_abbreviation"])): float(row["tracked_z"])
        for row in scored.select("season", "level_group", "player_id", "position_abbreviation", "tracked_z").iter_rows(named=True)
    }


def _z_framing(frame: pl.DataFrame) -> dict[tuple[int, str, int], float]:
    eligible = frame.filter(
        (pl.col("takes") >= 500)
        & pl.col("tracked_framing_per_1000_takes").is_not_null()
    )
    moments = eligible.group_by(["season", "level_group"]).agg(
        pl.col("tracked_framing_per_1000_takes").mean().alias("mean"),
        pl.col("tracked_framing_per_1000_takes").std(ddof=0).alias("sd"),
        pl.len().alias("n"),
    )
    scored = (
        eligible.join(moments, on=["season", "level_group"], how="left")
        .filter((pl.col("n") >= 15) & pl.col("sd").is_not_null() & (pl.col("sd") > 1e-12))
        .with_columns(((pl.col("tracked_framing_per_1000_takes") - pl.col("mean")) / pl.col("sd")).alias("tracked_z"))
    )
    return {
        (int(row["season"]), str(row["level_group"]), int(row["player_id"])): float(row["tracked_z"])
        for row in scored.select("season", "level_group", "player_id", "tracked_z").iter_rows(named=True)
    }


def _profile_index(profiles: pl.DataFrame) -> dict[tuple[int, int], dict[str, Any]]:
    return {
        (int(row["season"]), int(row["player_id"])): row
        for row in profiles.iter_rows(named=True)
    }


def _range_subset(
    x: np.ndarray,
    y: np.ndarray,
    meta: list[dict[str, Any]],
    profiles_index: dict[tuple[int, int], dict[str, Any]],
    tracked: dict[tuple[int, str, int, str], float],
    *,
    mode: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[dict[str, Any]]]:
    keep_x: list[np.ndarray] = []
    keep_y: list[float] = []
    keep_z: list[float] = []
    keep_meta: list[dict[str, Any]] = []
    for row_x, row_y, row_meta in zip(x, y, meta, strict=True):
        target_year = int(row_meta["target_year"])
        input_year = INPUT_BY_TARGET[target_year]
        player_id = int(row_meta["player_id"])
        profile = profiles_index.get((input_year, player_id))
        if profile is None:
            continue
        position = str(profile["position"])
        if mode == "MLB":
            key = (input_year, "MLB", player_id, position)
            value = tracked.get(key)
        elif mode == "MILB_TRANSFER":
            if str(profile["current_level_group"]) == "MLB":
                continue
            # Deterministic highest tracked level if a player appears in both tiers.
            value = tracked.get((input_year, "AAA", player_id, position))
            if value is None:
                value = tracked.get((input_year, "TRACKED_NON_AAA", player_id, position))
        else:
            raise ValueError(mode)
        if value is None or not math.isfinite(value):
            continue
        keep_x.append(row_x)
        keep_y.append(float(row_y))
        keep_z.append(float(value))
        keep_meta.append(row_meta)
    width = x.shape[1] if x.ndim == 2 else 0
    return (
        np.asarray(keep_x, dtype=float).reshape((-1, width)),
        np.asarray(keep_y, dtype=float),
        np.asarray(keep_z, dtype=float),
        keep_meta,
    )


def _evaluate_range(
    profiles: pl.DataFrame,
    targets: dict[int, pl.DataFrame],
    tracked: dict[tuple[int, str, int, str], float],
) -> dict[str, Any]:
    index = _profile_index(profiles)
    folds: list[dict[str, Any]] = []
    u1_oof_y: list[np.ndarray] = []
    u1_oof_p: list[np.ndarray] = []
    t1_oof_p: list[np.ndarray] = []
    held_2024: dict[str, Any] | None = None
    finite = True

    for held_year in TARGET_YEARS:
        train_years = set(TARGET_YEARS) - {held_year}
        normalizer = _fit_general_normalizer(profiles, {INPUT_BY_TARGET[y] for y in train_years})
        x_train_all, y_train_all, meta_train_all = _general_matrix(profiles, targets, train_years, normalizer, "U1")
        x_hold_all, y_hold_all, meta_hold_all = _general_matrix(profiles, targets, {held_year}, normalizer, "U1")
        x_train, y_train, z_train, _ = _range_subset(
            x_train_all, y_train_all, meta_train_all, index, tracked, mode="MLB"
        )
        x_hold, y_hold, z_hold, _ = _range_subset(
            x_hold_all, y_hold_all, meta_hold_all, index, tracked, mode="MLB"
        )
        if not len(y_train) or not len(y_hold):
            raise RuntimeError(f"empty tracked range fold target_year={held_year}")
        beta_u1 = _ridge_fit(x_train, y_train, 0.0)
        beta_t1 = _ridge_fit(np.column_stack([x_train, z_train]), y_train, 0.0)
        pred_u1 = _predict(beta_u1, x_hold)
        pred_t1 = _predict(beta_t1, np.column_stack([x_hold, z_hold]))
        finite = finite and bool(
            np.isfinite(beta_u1).all()
            and np.isfinite(beta_t1).all()
            and np.isfinite(pred_u1).all()
            and np.isfinite(pred_t1).all()
        )
        u1m = _metrics(y_hold, pred_u1)
        t1m = _metrics(y_hold, pred_t1)
        relative = (float(t1m["mse"]) - float(u1m["mse"])) / float(u1m["mse"])
        fold = {
            "target_year": held_year,
            "train_player_count": int(len(y_train)),
            "player_count": int(len(y_hold)),
            "u1": u1m,
            "t1": t1m,
            "t1_mse_relative_vs_u1": relative,
            "u1_coefficients": beta_u1.tolist(),
            "t1_coefficients": beta_t1.tolist(),
        }
        folds.append(fold)
        u1_oof_y.append(y_hold)
        u1_oof_p.append(pred_u1)
        t1_oof_p.append(pred_t1)
        if held_year == 2024:
            held_2024 = {
                "normalizer": normalizer,
                "beta_u1": beta_u1,
                "beta_t1": beta_t1,
                "x_hold_all": x_hold_all,
                "y_hold_all": y_hold_all,
                "meta_hold_all": meta_hold_all,
            }

    y_all = np.concatenate(u1_oof_y)
    u1_pooled = _metrics(y_all, np.concatenate(u1_oof_p))
    t1_pooled = _metrics(y_all, np.concatenate(t1_oof_p))
    improvement = (float(u1_pooled["mse"]) - float(t1_pooled["mse"])) / float(u1_pooled["mse"])
    folds_better = sum(1 for fold in folds if float(fold["t1"]["mse"]) < float(fold["u1"]["mse"]))
    worst_relative = max(float(fold["t1_mse_relative_vs_u1"]) for fold in folds)
    spearman_delta = (
        float(t1_pooled["spearman"]) - float(u1_pooled["spearman"])
        if t1_pooled["spearman"] is not None and u1_pooled["spearman"] is not None
        else None
    )
    counts_ok = all(int(fold["player_count"]) >= 75 for fold in folds)
    tier_a_passed = bool(
        finite
        and counts_ok
        and folds_better >= 2
        and improvement >= 0.01
        and worst_relative <= 0.03
        and spearman_delta is not None
        and spearman_delta >= -0.005
    )

    transfer: dict[str, Any] = {
        "attempted": False,
        "player_count": 0,
        "status": "not_attempted_tier_a_failed" if not tier_a_passed else "pending",
        "passed": False,
    }
    if tier_a_passed:
        assert held_2024 is not None
        x_transfer, y_transfer, z_transfer, _ = _range_subset(
            held_2024["x_hold_all"],
            held_2024["y_hold_all"],
            held_2024["meta_hold_all"],
            index,
            tracked,
            mode="MILB_TRANSFER",
        )
        transfer["attempted"] = True
        transfer["player_count"] = int(len(y_transfer))
        if len(y_transfer) >= 30:
            pred_u1 = _predict(held_2024["beta_u1"], x_transfer)
            pred_t1 = _predict(held_2024["beta_t1"], np.column_stack([x_transfer, z_transfer]))
            u1m = _metrics(y_transfer, pred_u1)
            t1m = _metrics(y_transfer, pred_t1)
            relative = (float(t1m["mse"]) - float(u1m["mse"])) / float(u1m["mse"])
            spearman_delta_transfer = (
                float(t1m["spearman"]) - float(u1m["spearman"])
                if t1m["spearman"] is not None and u1m["spearman"] is not None
                else None
            )
            passed = bool(
                np.isfinite(pred_u1).all()
                and np.isfinite(pred_t1).all()
                and relative <= 0.05
                and spearman_delta_transfer is not None
                and spearman_delta_transfer >= -0.02
            )
            transfer.update(
                {
                    "status": "scored",
                    "u1": u1m,
                    "t1": t1m,
                    "t1_mse_relative_vs_u1": relative,
                    "t1_spearman_delta_vs_u1": spearman_delta_transfer,
                    "passed": passed,
                }
            )
        else:
            transfer["status"] = "insufficient_transfer_evidence"

    return {
        "folds": folds,
        "pooled": {
            "u1": u1_pooled,
            "t1": t1_pooled,
            "t1_mse_improvement_vs_u1": improvement,
            "t1_spearman_delta_vs_u1": spearman_delta,
            "folds_mse_better_than_u1": folds_better,
            "worst_fold_mse_relative_vs_u1": worst_relative,
        },
        "tier_a_gate": {
            "all_fold_counts_ge_75": counts_ok,
            "finite": finite,
            "passed": tier_a_passed,
        },
        "tier_b_transfer": transfer,
    }


def _framing_targets() -> dict[int, pl.DataFrame]:
    targets: dict[int, pl.DataFrame] = {}
    for year in TARGET_YEARS:
        raw = mlb_statcast_leaderboard_catcher_framing(year=year)
        needed = {"id", "rv_tot", "pitches"}
        missing = sorted(needed - set(raw.columns))
        if missing:
            raise RuntimeError(f"framing target {year} missing {missing}")
        rows: list[dict[str, Any]] = []
        for row in raw.select(*sorted(needed)).iter_rows(named=True):
            player = _float_text(row["id"])
            rv = _float_text(row["rv_tot"])
            pitches = _float_text(row["pitches"])
            if (
                player is None
                or not float(player).is_integer()
                or rv is None
                or pitches is None
                or pitches < 1000
            ):
                continue
            rows.append({"player_id": int(player), "target_raw": 1000.0 * rv / pitches})
        frame = pl.DataFrame(rows)
        if frame.is_empty():
            raise RuntimeError(f"empty framing target {year}")
        mean = float(frame.get_column("target_raw").mean())
        sd = float(frame.get_column("target_raw").std(ddof=0))
        if not math.isfinite(sd) or sd <= 1e-12:
            raise RuntimeError(f"degenerate framing target SD {year}")
        targets[year] = frame.with_columns(((pl.col("target_raw") - mean) / sd).alias("target_z"))
    return targets


def _framing_rows_for_year(
    target_year: int,
    targets: dict[int, pl.DataFrame],
    tracked: dict[tuple[int, str, int], float],
    catcher_index: dict[tuple[int, int], dict[str, Any]],
    *,
    mode: str,
) -> tuple[np.ndarray, np.ndarray, list[int]]:
    input_year = INPUT_BY_TARGET[target_year]
    z_values: list[float] = []
    y_values: list[float] = []
    player_ids: list[int] = []
    for row in targets[target_year].select("player_id", "target_z").iter_rows(named=True):
        player_id = int(row["player_id"])
        profile = catcher_index.get((input_year, player_id))
        if profile is None or int(profile["fielding_outs"]) < 300:
            continue
        if mode == "MLB":
            value = tracked.get((input_year, "MLB", player_id))
        elif mode == "MILB_TRANSFER":
            if str(profile["current_level_group"]) == "MLB":
                continue
            value = tracked.get((input_year, "AAA", player_id))
            if value is None:
                value = tracked.get((input_year, "TRACKED_NON_AAA", player_id))
        else:
            raise ValueError(mode)
        if value is None or not math.isfinite(value):
            continue
        z_values.append(float(value))
        y_values.append(float(row["target_z"]))
        player_ids.append(player_id)
    return np.asarray(z_values, dtype=float), np.asarray(y_values, dtype=float), player_ids


def _evaluate_framing(
    catcher: pl.DataFrame,
    targets: dict[int, pl.DataFrame],
    tracked: dict[tuple[int, str, int], float],
) -> dict[str, Any]:
    catcher_index = {
        (int(row["season"]), int(row["player_id"])): row
        for row in catcher.iter_rows(named=True)
    }
    folds: list[dict[str, Any]] = []
    f0_y: list[np.ndarray] = []
    f1_p: list[np.ndarray] = []
    held_2024: dict[str, Any] | None = None
    finite = True
    for held_year in TARGET_YEARS:
        train_years = set(TARGET_YEARS) - {held_year}
        train_z: list[np.ndarray] = []
        train_y: list[np.ndarray] = []
        for year in sorted(train_years):
            z, y, _ = _framing_rows_for_year(year, targets, tracked, catcher_index, mode="MLB")
            train_z.append(z)
            train_y.append(y)
        z_train = np.concatenate(train_z)
        y_train = np.concatenate(train_y)
        z_hold, y_hold, _ = _framing_rows_for_year(held_year, targets, tracked, catcher_index, mode="MLB")
        if not len(y_train) or not len(y_hold):
            raise RuntimeError(f"empty framing tracked fold target_year={held_year}")
        beta = _ridge_fit(z_train.reshape(-1, 1), y_train, 0.0)
        pred = _predict(beta, z_hold.reshape(-1, 1))
        finite = finite and bool(np.isfinite(beta).all() and np.isfinite(pred).all())
        f0m = _metrics(y_hold, np.zeros(len(y_hold)))
        f1m = _metrics(y_hold, pred)
        relative = (float(f1m["mse"]) - float(f0m["mse"])) / float(f0m["mse"])
        folds.append(
            {
                "target_year": held_year,
                "train_catcher_count": int(len(y_train)),
                "player_count": int(len(y_hold)),
                "f0": f0m,
                "f1": f1m,
                "f1_mse_relative_vs_f0": relative,
                "f1_coefficients": beta.tolist(),
            }
        )
        f0_y.append(y_hold)
        f1_p.append(pred)
        if held_year == 2024:
            held_2024 = {"beta": beta}
    y_all = np.concatenate(f0_y)
    f0_pooled = _metrics(y_all, np.zeros(len(y_all)))
    f1_pooled = _metrics(y_all, np.concatenate(f1_p))
    improvement = (float(f0_pooled["mse"]) - float(f1_pooled["mse"])) / float(f0_pooled["mse"])
    folds_better = sum(1 for fold in folds if float(fold["f1"]["mse"]) < float(fold["f0"]["mse"]))
    worst_relative = max(float(fold["f1_mse_relative_vs_f0"]) for fold in folds)
    counts_ok = all(int(fold["player_count"]) >= 20 for fold in folds)
    tier_a_passed = bool(
        finite
        and counts_ok
        and folds_better >= 2
        and improvement >= 0.02
        and worst_relative <= 0.05
        and f1_pooled["spearman"] is not None
        and f1_pooled["spearman"] >= 0.10
    )
    transfer: dict[str, Any] = {
        "attempted": False,
        "player_count": 0,
        "status": "not_attempted_tier_a_failed" if not tier_a_passed else "pending",
        "passed": False,
    }
    if tier_a_passed:
        assert held_2024 is not None
        z_transfer, y_transfer, _ = _framing_rows_for_year(2024, targets, tracked, catcher_index, mode="MILB_TRANSFER")
        transfer["attempted"] = True
        transfer["player_count"] = int(len(y_transfer))
        if len(y_transfer) >= 10:
            pred = _predict(held_2024["beta"], z_transfer.reshape(-1, 1))
            f0m = _metrics(y_transfer, np.zeros(len(y_transfer)))
            f1m = _metrics(y_transfer, pred)
            relative = (float(f1m["mse"]) - float(f0m["mse"])) / float(f0m["mse"])
            passed = bool(
                np.isfinite(pred).all()
                and relative <= 0.10
                and f1m["spearman"] is not None
                and f1m["spearman"] >= 0.0
            )
            transfer.update(
                {
                    "status": "scored",
                    "f0": f0m,
                    "f1": f1m,
                    "f1_mse_relative_vs_f0": relative,
                    "passed": passed,
                }
            )
        else:
            transfer["status"] = "insufficient_transfer_evidence"
    return {
        "folds": folds,
        "pooled": {
            "f0": f0_pooled,
            "f1": f1_pooled,
            "f1_mse_improvement_vs_f0": improvement,
            "folds_mse_better_than_f0": folds_better,
            "worst_fold_mse_relative_vs_f0": worst_relative,
        },
        "tier_a_gate": {"all_fold_counts_ge_20": counts_ok, "finite": finite, "passed": tier_a_passed},
        "tier_b_transfer": transfer,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--tracked-root", type=Path, required=True)
    args = parser.parse_args()

    source_result = json.loads(SOURCE_RESULT.read_text())
    if source_result.get("decision", {}).get("tracked_source_materialized") is not True:
        raise RuntimeError("tracked source result is not materialized/accepted")
    if source_result.get("boundary", {}).get("2025_source_accessed") is not False:
        raise RuntimeError("tracked source crossed 2025 boundary")
    universal = json.loads(UNIVERSAL_RESULT.read_text())
    if universal.get("decision", {}).get("selected_general_range_family") != {"family": "U1", "lambda": 0.0}:
        raise RuntimeError("unexpected universal general incumbent")
    age = json.loads(AGE_RESULT.read_text())
    if age.get("decision", {}).get("age_challenger_passed") is not False:
        raise RuntimeError("age challenger boundary changed; tracked contract expects closed age")

    range_path = _find_one(args.tracked_root, "tracked_range_proxy_2021_2023.parquet")
    framing_path = _find_one(args.tracked_root, "tracked_framing_proxy_2021_2023.parquet")
    range_frame = pl.read_parquet(range_path)
    framing_frame = pl.read_parquet(framing_path)
    range_z = _z_range(range_frame)
    framing_z = _z_framing(framing_frame)

    profiles, meta = _load_profiles(args.source_root)
    catcher = meta.pop("catcher")
    general_targets = _general_targets()
    framing_targets = _framing_targets()

    range_result = _evaluate_range(profiles, general_targets, range_z)
    framing_result = _evaluate_framing(catcher, framing_targets, framing_z)

    report = {
        "report_schema_version": "0.1",
        "gate": "defense_v1_final_tracked_incremental_challenger",
        "contract": "docs/defense-v1-tracked-challenger-contract.md",
        "source": {
            "tracked_source_run_id": source_result.get("source_run_id"),
            "tracked_source_sha": source_result.get("source_sha"),
            "tracked_range_file_sha256": source_result.get("storage", {}).get("range", {}).get("sha256"),
            "tracked_framing_file_sha256": source_result.get("storage", {}).get("framing", {}).get("sha256"),
            "historical_fielding_source_run_id": 32148467330,
            **meta,
            "eligible_range_z_count": len(range_z),
            "eligible_framing_z_count": len(framing_z),
        },
        "general_tracked_range": range_result,
        "catcher_tracked_framing": framing_result,
        "decision": {
            "tier_a_tracked_range_passed": bool(range_result["tier_a_gate"]["passed"]),
            "tier_b_tracked_range_transfer_passed": bool(range_result["tier_b_transfer"]["passed"]),
            "tier_a_tracked_framing_passed": bool(framing_result["tier_a_gate"]["passed"]),
            "tier_b_tracked_framing_transfer_passed": bool(framing_result["tier_b_transfer"]["passed"]),
            "pre_2025_defense_development_closed": True,
            "additional_development_challenger_authorized": False,
            "final_refit_and_parameter_freeze_authorized_next": True,
            "2025_confirmation_authorized": False,
            "defense_v1_frozen": False,
            "war_value_authorized": False,
        },
        "boundary": {
            "2025_defensive_targets_accessed": False,
            "age_reopened": False,
            "traditional_feature_search_reopened": False,
            "playing_time_v1_modified": False,
            "position_role_v1_modified": False,
            "run_value_conversion_performed": False,
        },
    }
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    (REPORT_ROOT / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Defense v1 tracked challenger",
        "",
        f"- Tier A tracked range passed: {report['decision']['tier_a_tracked_range_passed']}",
        f"- Tier B range transfer passed: {report['decision']['tier_b_tracked_range_transfer_passed']}",
        f"- Tier A tracked framing passed: {report['decision']['tier_a_tracked_framing_passed']}",
        f"- Tier B framing transfer passed: {report['decision']['tier_b_tracked_framing_transfer_passed']}",
        "- pre-2025 Defense development closed: True",
        "- 2025 defensive targets accessed: False",
        "- WAR/value authorized: False",
        "",
    ]
    (REPORT_ROOT / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
