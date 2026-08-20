#!/usr/bin/env python3
"""Test the pre-registered Defense v1 age challenger against frozen U1."""

from __future__ import annotations

import argparse
from datetime import date
import json
import math
from pathlib import Path
import time
from typing import Any

import numpy as np
import requests

from develop_defense_v1_universal import (
    INPUT_BY_TARGET,
    TARGET_YEARS,
    _fit_general_normalizer,
    _general_matrix,
    _general_targets,
    _load_profiles,
    _metrics,
    _predict,
    _ridge_fit,
)


REPORT_ROOT = Path("reports/generated/defense-v1-age-challenger")
INCUMBENT_RESULT = Path("docs/defense-v1-universal-development-result.json")
PERSON_URL = "https://statsapi.mlb.com/api/v1/people/{player_id}"


def _fetch_birth_dates(player_ids: set[int]) -> tuple[dict[int, date], list[dict[str, Any]]]:
    session = requests.Session()
    session.headers["User-Agent"] = "universal-baseball-model-defense-age/0.1"
    birth_dates: dict[int, date] = {}
    records: list[dict[str, Any]] = []
    try:
        for index, player_id in enumerate(sorted(player_ids), start=1):
            url = PERSON_URL.format(player_id=player_id)
            last_error: str | None = None
            status_code: int | None = None
            payload: dict[str, Any] | None = None
            for attempt in range(1, 4):
                try:
                    response = session.get(url, timeout=30)
                    status_code = int(response.status_code)
                    response.raise_for_status()
                    payload = response.json()
                    last_error = None
                    break
                except Exception as exc:
                    last_error = f"{type(exc).__name__}: {exc}"
                    if attempt < 3:
                        time.sleep(float(attempt))
            birth_text: str | None = None
            if payload is not None:
                people = payload.get("people") or []
                if len(people) == 1 and isinstance(people[0], dict):
                    value = people[0].get("birthDate")
                    if value:
                        birth_text = str(value)
                        try:
                            birth_dates[player_id] = date.fromisoformat(birth_text)
                        except ValueError:
                            last_error = f"invalid birthDate: {birth_text!r}"
            records.append(
                {
                    "player_id": player_id,
                    "url": url,
                    "status_code": status_code,
                    "birth_date": birth_text,
                    "resolved": player_id in birth_dates,
                    "error": last_error,
                }
            )
            if index % 100 == 0:
                print(f"Resolved birth dates: {index}/{len(player_ids)}")
    finally:
        session.close()
    return birth_dates, records


def _age_terms(birth: date, input_year: int) -> tuple[float, float] | None:
    anchor = date(input_year, 7, 1)
    age_years = (anchor - birth).days / 365.2425
    if not math.isfinite(age_years) or not (15.0 <= age_years <= 45.0):
        return None
    age_c = (age_years - 27.0) / 5.0
    return age_c, age_c * age_c


def _filter_age(
    x: np.ndarray,
    y: np.ndarray,
    meta: list[dict[str, Any]],
    birth_dates: dict[int, date],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[dict[str, Any]]]:
    keep_x: list[np.ndarray] = []
    keep_y: list[float] = []
    ages: list[list[float]] = []
    keep_meta: list[dict[str, Any]] = []
    for row_x, row_y, row_meta in zip(x, y, meta, strict=True):
        player_id = int(row_meta["player_id"])
        target_year = int(row_meta["target_year"])
        birth = birth_dates.get(player_id)
        if birth is None:
            continue
        terms = _age_terms(birth, INPUT_BY_TARGET[target_year])
        if terms is None:
            continue
        keep_x.append(row_x)
        keep_y.append(float(row_y))
        ages.append([terms[0], terms[1]])
        keep_meta.append(row_meta)
    width = x.shape[1] if x.ndim == 2 else 0
    return (
        np.asarray(keep_x, dtype=float).reshape((-1, width)),
        np.asarray(keep_y, dtype=float),
        np.asarray(ages, dtype=float).reshape((-1, 2)),
        keep_meta,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    args = parser.parse_args()

    if not INCUMBENT_RESULT.exists():
        raise RuntimeError("frozen universal development result is missing")
    incumbent = json.loads(INCUMBENT_RESULT.read_text())
    selected = incumbent.get("decision", {}).get("selected_general_range_family")
    if selected != {"family": "U1", "lambda": 0.0}:
        raise RuntimeError(f"unexpected frozen general incumbent: {selected!r}")
    if incumbent.get("boundary", {}).get("2025_defensive_targets_accessed") is not False:
        raise RuntimeError("incumbent boundary does not preserve 2025 defensive target quarantine")

    profiles, meta = _load_profiles(args.source_root)
    meta.pop("catcher")
    targets = _general_targets()

    fold_cache: dict[int, dict[str, Any]] = {}
    needed_ids: set[int] = set()
    for held_year in TARGET_YEARS:
        train_years = set(TARGET_YEARS) - {held_year}
        normalizer = _fit_general_normalizer(profiles, {INPUT_BY_TARGET[y] for y in train_years})
        x_train, y_train, meta_train = _general_matrix(profiles, targets, train_years, normalizer, "U1")
        x_hold, y_hold, meta_hold = _general_matrix(profiles, targets, {held_year}, normalizer, "U1")
        fold_cache[held_year] = {
            "x_train": x_train,
            "y_train": y_train,
            "meta_train": meta_train,
            "x_hold": x_hold,
            "y_hold": y_hold,
            "meta_hold": meta_hold,
        }
        needed_ids.update(int(row["player_id"]) for row in meta_train)
        needed_ids.update(int(row["player_id"]) for row in meta_hold)

    print(f"Fetching immutable birth dates for {len(needed_ids)} development players")
    birth_dates, birth_records = _fetch_birth_dates(needed_ids)

    folds: list[dict[str, Any]] = []
    u1_oof_y: list[np.ndarray] = []
    u1_oof_pred: list[np.ndarray] = []
    a1_oof_y: list[np.ndarray] = []
    a1_oof_pred: list[np.ndarray] = []
    all_finite = True

    for held_year in TARGET_YEARS:
        cache = fold_cache[held_year]
        x_train, y_train, age_train, _ = _filter_age(
            cache["x_train"], cache["y_train"], cache["meta_train"], birth_dates
        )
        x_hold, y_hold, age_hold, _ = _filter_age(
            cache["x_hold"], cache["y_hold"], cache["meta_hold"], birth_dates
        )
        if len(y_train) == 0 or len(y_hold) == 0:
            raise RuntimeError(f"empty age-resolved fold target_year={held_year}")

        beta_u1 = _ridge_fit(x_train, y_train, 0.0)
        pred_u1 = _predict(beta_u1, x_hold)

        x_train_a1 = np.column_stack([x_train, age_train])
        x_hold_a1 = np.column_stack([x_hold, age_hold])
        beta_a1 = _ridge_fit(x_train_a1, y_train, 0.0)
        pred_a1 = _predict(beta_a1, x_hold_a1)

        all_finite = all_finite and bool(
            np.isfinite(beta_u1).all()
            and np.isfinite(beta_a1).all()
            and np.isfinite(pred_u1).all()
            and np.isfinite(pred_a1).all()
        )
        u1_metrics = _metrics(y_hold, pred_u1)
        a1_metrics = _metrics(y_hold, pred_a1)
        relative = (
            (float(a1_metrics["mse"]) - float(u1_metrics["mse"])) / float(u1_metrics["mse"])
            if u1_metrics["mse"] not in {None, 0.0}
            else None
        )
        folds.append(
            {
                "target_year": held_year,
                "train_player_count": int(len(y_train)),
                "player_count": int(len(y_hold)),
                "u1": u1_metrics,
                "a1": a1_metrics,
                "a1_mse_relative_vs_u1": relative,
                "u1_coefficients": beta_u1.tolist(),
                "a1_coefficients": beta_a1.tolist(),
            }
        )
        u1_oof_y.append(y_hold)
        u1_oof_pred.append(pred_u1)
        a1_oof_y.append(y_hold)
        a1_oof_pred.append(pred_a1)

    y_all = np.concatenate(u1_oof_y)
    u1_pred_all = np.concatenate(u1_oof_pred)
    a1_pred_all = np.concatenate(a1_oof_pred)
    u1_pooled = _metrics(y_all, u1_pred_all)
    a1_pooled = _metrics(y_all, a1_pred_all)
    pooled_improvement = (
        (float(u1_pooled["mse"]) - float(a1_pooled["mse"])) / float(u1_pooled["mse"])
    )
    folds_better = sum(
        1 for fold in folds if float(fold["a1"]["mse"]) < float(fold["u1"]["mse"])
    )
    worst_relative = max(float(fold["a1_mse_relative_vs_u1"]) for fold in folds)
    spearman_delta = (
        float(a1_pooled["spearman"]) - float(u1_pooled["spearman"])
        if a1_pooled["spearman"] is not None and u1_pooled["spearman"] is not None
        else None
    )
    counts_ok = all(int(fold["player_count"]) >= 100 for fold in folds)
    passed = bool(
        all_finite
        and counts_ok
        and folds_better >= 2
        and pooled_improvement >= 0.005
        and worst_relative <= 0.025
        and spearman_delta is not None
        and spearman_delta >= -0.005
    )

    report = {
        "report_schema_version": "0.1",
        "gate": "defense_v1_age_incremental_challenger",
        "contract": "docs/defense-v1-age-challenger-contract.md",
        "incumbent": {"family": "U1", "lambda": 0.0},
        "challenger": {
            "name": "U1_plus_quadratic_age_v1",
            "age_anchor_date": "July 1 of input season",
            "age_c_formula": "(age_years - 27.0) / 5.0",
            "terms": ["age_c", "age_c2"],
            "lambda": 0.0,
        },
        "source": {
            "historical_source_run_id": 32148467330,
            **meta,
            "requested_birth_date_player_count": len(needed_ids),
            "resolved_birth_date_player_count": len(birth_dates),
            "birth_date_records": birth_records,
        },
        "folds": folds,
        "pooled": {
            "u1": u1_pooled,
            "a1": a1_pooled,
            "a1_mse_improvement_vs_u1": pooled_improvement,
            "a1_spearman_delta_vs_u1": spearman_delta,
            "folds_mse_better_than_u1": folds_better,
            "worst_fold_mse_relative_vs_u1": worst_relative,
        },
        "decision": {
            "age_challenger_passed": passed,
            "selected_general_range_form": "U1_plus_quadratic_age_v1" if passed else "U1",
            "additional_age_tuning_authorized": False,
            "tracked_incremental_challenger_authorized_next": True,
            "2025_confirmation_authorized": False,
            "defense_v1_frozen": False,
            "war_value_authorized": False,
        },
        "boundary": {
            "2025_defensive_targets_accessed": False,
            "tracked_evidence_used": False,
            "catcher_models_modified": False,
            "playing_time_v1_modified": False,
            "position_role_v1_modified": False,
            "run_value_conversion_performed": False,
        },
    }
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    (REPORT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# Defense v1 age challenger",
        "",
        f"- requested/resolved birth dates: {len(needed_ids)}/{len(birth_dates)}",
        f"- folds A1 MSE better than U1: {folds_better}/3",
        f"- pooled MSE improvement: {pooled_improvement:.6f}",
        f"- pooled Spearman delta: {spearman_delta}",
        f"- age challenger passed: {passed}",
        f"- selected general form: {report['decision']['selected_general_range_form']}",
        "- 2025 defensive targets accessed: False",
        "- WAR/value authorized: False",
        "",
    ]
    (REPORT_ROOT / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
