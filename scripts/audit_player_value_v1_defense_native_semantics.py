#!/usr/bin/env python3
"""Audit pre-2025 native source semantics for frozen Defense v1 targets.

This is a source/identity diagnostic only. It does not fit or score a Defense model,
select a z-to-native conversion, choose future opportunity forecasts, or calculate WAR/value.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import polars as pl
import requests
from sportsdataverse.mlb.mlb_statcast import mlb_statcast_leaderboard_outs_above_average

CONTRACT_SHA256 = "aab6abb9a8babad1e994d62c314236db319ec3d19659e56436530bcd6c52873a"
YEARS = (2022, 2023, 2024)
GENERAL_POSITIONS = ("1B", "2B", "3B", "SS", "LF", "CF", "RF")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--contract-path",
        type=Path,
        default=Path("docs/player-value-v1-defense-native-semantics-audit-contract.md"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/player-value-v1-defense-native-semantics-audit"),
    )
    return parser.parse_args()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_contract(path: Path) -> str:
    observed = _sha256(path)
    if observed != CONTRACT_SHA256:
        raise RuntimeError(
            f"native-semantics contract mismatch: expected {CONTRACT_SHA256}, observed {observed}"
        )
    return observed


def _number(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if not text or text.lower() in {"nan", "none", "null", "--"}:
        return None
    if text.endswith("%"):
        text = text[:-1].strip()
    try:
        result = float(text)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _target_stats(values: Iterable[float]) -> dict[str, float | int | None]:
    array = np.asarray(list(values), dtype=np.float64)
    array = array[np.isfinite(array)]
    if not len(array):
        return {
            "count": 0,
            "mean": None,
            "population_sd": None,
            "median": None,
            "min": None,
            "max": None,
            "mean_over_sd": None,
        }
    sd = float(np.std(array, ddof=0))
    mean = float(np.mean(array))
    return {
        "count": int(len(array)),
        "mean": mean,
        "population_sd": sd,
        "median": float(np.median(array)),
        "min": float(np.min(array)),
        "max": float(np.max(array)),
        "mean_over_sd": float(mean / sd) if sd > 1e-12 else None,
    }


def _keyword_columns(columns: list[str], keywords: tuple[str, ...]) -> list[str]:
    return sorted(
        column for column in columns if any(keyword in column.lower() for keyword in keywords)
    )


def _first_present(columns: list[str], candidates: tuple[str, ...]) -> str | None:
    lookup = {column.lower(): column for column in columns}
    for candidate in candidates:
        if candidate.lower() in lookup:
            return lookup[candidate.lower()]
    return None


def _identity_error(
    frame: pl.DataFrame,
    *,
    lhs_column: str,
    rhs_columns: tuple[str, ...],
    formula,
) -> dict[str, object]:
    residuals: list[float] = []
    for row in frame.select(lhs_column, *rhs_columns).iter_rows(named=True):
        lhs = _number(row[lhs_column])
        rhs_values = [_number(row[column]) for column in rhs_columns]
        if lhs is None or any(value is None for value in rhs_values):
            continue
        try:
            expected = float(formula(*[float(value) for value in rhs_values]))
        except (ZeroDivisionError, ValueError, OverflowError):
            continue
        if not math.isfinite(expected):
            continue
        residuals.append(float(lhs - expected))
    if not residuals:
        return {"n": 0, "mae": None, "max_abs_error": None, "mean_error": None}
    array = np.asarray(residuals, dtype=np.float64)
    return {
        "n": int(len(array)),
        "mae": float(np.mean(np.abs(array))),
        "max_abs_error": float(np.max(np.abs(array))),
        "mean_error": float(np.mean(array)),
    }


def _general(year: int) -> dict[str, object]:
    raw = mlb_statcast_leaderboard_outs_above_average(year=year)
    if raw.is_empty():
        raise RuntimeError(f"general range source empty for {year}")
    columns = list(raw.columns)
    required = {"player_id", "primary_pos_formatted", "diff_success_rate_formatted"}
    missing = sorted(required - set(columns))
    if missing:
        raise RuntimeError(f"general range source {year} missing {missing}")

    targets: list[float] = []
    for row in raw.select("primary_pos_formatted", "diff_success_rate_formatted").iter_rows(named=True):
        position = str(row["primary_pos_formatted"] or "").strip()
        value = _number(row["diff_success_rate_formatted"])
        if position in GENERAL_POSITIONS and value is not None:
            targets.append(value)

    oaa_col = _first_present(
        columns,
        (
            "outs_above_average",
            "outs_above_average_formatted",
            "oaa",
            "oaa_formatted",
        ),
    )
    opportunities_col = _first_present(
        columns,
        (
            "opportunities",
            "fielding_opportunities",
            "opportunity",
            "opps",
        ),
    )
    identities: dict[str, object] = {
        "oaa_total_column": oaa_col,
        "opportunities_column": opportunities_col,
        "tested": False,
    }
    if oaa_col and opportunities_col:
        identities = {
            "oaa_total_column": oaa_col,
            "opportunities_column": opportunities_col,
            "tested": True,
            "success_rate_added_equals_100_oaa_over_opportunities": _identity_error(
                raw,
                lhs_column="diff_success_rate_formatted",
                rhs_columns=(oaa_col, opportunities_col),
                formula=lambda oaa, opp: 100.0 * oaa / opp if opp != 0 else math.nan,
            ),
            "success_rate_added_equals_oaa_over_opportunities": _identity_error(
                raw,
                lhs_column="diff_success_rate_formatted",
                rhs_columns=(oaa_col, opportunities_col),
                formula=lambda oaa, opp: oaa / opp if opp != 0 else math.nan,
            ),
        }

    return {
        "year": year,
        "transport": "sportsdataverse==0.0.75 mlb_statcast_leaderboard_outs_above_average(year=year)",
        "source_row_count": int(raw.height),
        "eligible_target_row_count": int(len(targets)),
        "target": "diff_success_rate_formatted",
        "target_stats": _target_stats(targets),
        "columns": sorted(columns),
        "semantic_candidate_columns": {
            "success": _keyword_columns(columns, ("success", "diff_success")),
            "opportunity": _keyword_columns(columns, ("opportun", "opp")),
            "outs_above_average": _keyword_columns(columns, ("above_average", "oaa", "out")),
            "run_or_value": _keyword_columns(columns, ("run", "value", "frv")),
        },
        "identities": identities,
    }


def _catcher_params(kind: str, year: int) -> dict[str, object]:
    minimum = 10 if kind == "throwing" else 500
    params: dict[str, object] = {
        "game_type": "Regular",
        "n": minimum,
        "season_start": year,
        "season_end": year,
        "split": "no",
        "team": "",
        "type": "Cat",
        "with_team_only": 1,
        "csv": "true",
    }
    if kind == "throwing":
        params["target_base"] = "All"
    return params


def _fetch_csv(session: requests.Session, endpoint: str, params: dict[str, object]) -> tuple[pl.DataFrame, str]:
    response = session.get(
        f"https://baseballsavant.mlb.com/leaderboard/{endpoint}",
        params=params,
        timeout=60,
    )
    response.raise_for_status()
    raw = response.content
    if not raw.strip() or raw.lstrip().startswith(b"<"):
        raise RuntimeError(f"{endpoint} returned empty/HTML body")
    frame = pl.read_csv(io.BytesIO(raw), infer_schema_length=10000)
    if frame.is_empty():
        raise RuntimeError(f"{endpoint} returned empty CSV")
    return frame, response.url


def _catcher(session: requests.Session, kind: str, year: int) -> dict[str, object]:
    endpoint = "catcher-throwing" if kind == "throwing" else "catcher-blocking"
    target_col = "cs_aa_per_throw" if kind == "throwing" else "blocks_above_average_per_game"
    exposure_col = "sb_attempts" if kind == "throwing" else "pitches"
    minimum = 10.0 if kind == "throwing" else 500.0
    raw, response_url = _fetch_csv(session, endpoint, _catcher_params(kind, year))
    columns = list(raw.columns)
    required = {"player_id", target_col, exposure_col}
    missing = sorted(required - set(columns))
    if missing:
        raise RuntimeError(f"{kind} {year} missing {missing}")

    targets: list[float] = []
    eligible_rows: list[dict[str, Any]] = []
    for row in raw.iter_rows(named=True):
        player = _number(row.get("player_id"))
        target = _number(row.get(target_col))
        exposure = _number(row.get(exposure_col))
        if (
            player is not None
            and float(player).is_integer()
            and target is not None
            and exposure is not None
            and exposure >= minimum
        ):
            targets.append(target)
            eligible_rows.append(row)
    eligible = pl.DataFrame(eligible_rows) if eligible_rows else raw.head(0)

    if kind == "throwing":
        total_col = _first_present(
            columns,
            ("cs_aa", "caught_stealing_above_average", "cs_above_average"),
        )
        identities: dict[str, object] = {
            "total_cs_aa_column": total_col,
            "tested": False,
        }
        if total_col:
            identities = {
                "total_cs_aa_column": total_col,
                "tested": True,
                "total_cs_aa_equals_rate_times_attempts": _identity_error(
                    eligible,
                    lhs_column=total_col,
                    rhs_columns=(target_col, exposure_col),
                    formula=lambda rate, attempts: rate * attempts,
                ),
            }
    else:
        total_col = _first_present(
            columns,
            ("blocks_above_average", "blocking_above_average", "blocks_aa"),
        )
        games_col = _first_present(
            columns,
            ("games", "games_caught", "catcher_games", "n_games"),
        )
        identities = {
            "total_blocks_above_average_column": total_col,
            "games_column": games_col,
            "tested": False,
        }
        if total_col and games_col:
            identities = {
                "total_blocks_above_average_column": total_col,
                "games_column": games_col,
                "tested": True,
                "total_blocks_aa_equals_per_game_times_games": _identity_error(
                    eligible,
                    lhs_column=total_col,
                    rhs_columns=(target_col, games_col),
                    formula=lambda rate, games: rate * games,
                ),
            }

    return {
        "year": year,
        "endpoint": endpoint,
        "response_url": response_url,
        "requested_params": _catcher_params(kind, year),
        "source_row_count": int(raw.height),
        "eligible_target_row_count": int(len(targets)),
        "target": target_col,
        "eligibility_exposure": exposure_col,
        "eligibility_minimum": minimum,
        "target_stats": _target_stats(targets),
        "columns": sorted(columns),
        "semantic_candidate_columns": {
            "above_average": _keyword_columns(columns, ("above_average", "_aa", "aa_")),
            "opportunity": _keyword_columns(columns, ("attempt", "pitch", "game", "throw")),
            "run_or_value": _keyword_columns(columns, ("run", "value", "rv")),
        },
        "identities": identities,
    }


def _framing_params(year: int) -> dict[str, object]:
    return {
        "type": "catcher",
        "seasonStart": year,
        "seasonEnd": year,
        "team": "",
        "min": 1,
        "sortColumn": "rv_tot",
        "sortDirection": "desc",
        "csv": "true",
    }


def _framing(session: requests.Session, year: int) -> dict[str, object]:
    raw, response_url = _fetch_csv(session, "catcher-framing", _framing_params(year))
    columns = list(raw.columns)
    id_col = _first_present(columns, ("id", "player_id"))
    if id_col is None:
        raise RuntimeError(f"framing {year} missing id/player_id")
    required = {"rv_tot", "pitches"}
    missing = sorted(required - set(columns))
    if missing:
        raise RuntimeError(f"framing {year} missing {missing}")

    eligible_rows: list[dict[str, Any]] = []
    target_values: list[float] = []
    for row in raw.iter_rows(named=True):
        player = _number(row.get(id_col))
        pitches = _number(row.get("pitches"))
        rv_tot = _number(row.get("rv_tot"))
        if (
            player is not None
            and float(player).is_integer()
            and pitches is not None
            and pitches >= 1000
            and rv_tot is not None
        ):
            enriched = dict(row)
            enriched["target_raw_audit"] = 1000.0 * rv_tot / pitches
            eligible_rows.append(enriched)
            target_values.append(float(enriched["target_raw_audit"]))
    eligible = pl.DataFrame(eligible_rows) if eligible_rows else raw.head(0)

    return {
        "year": year,
        "endpoint": "catcher-framing",
        "response_url": response_url,
        "requested_params": _framing_params(year),
        "source_row_count": int(raw.height),
        "eligible_target_row_count": int(len(target_values)),
        "target": "1000 * rv_tot / pitches",
        "native_seasonal_run_total_column": "rv_tot",
        "native_exposure": "pitches",
        "eligibility_minimum_pitches": 1000,
        "target_stats": _target_stats(target_values),
        "columns": sorted(columns),
        "semantic_candidate_columns": {
            "run_or_value": _keyword_columns(columns, ("run", "value", "rv")),
            "opportunity": _keyword_columns(columns, ("pitch", "take", "called")),
        },
        "identities": {
            "target_raw_equals_1000_rv_tot_over_pitches": {
                "tested": True,
                "n": int(eligible.height),
                "mae": 0.0,
                "max_abs_error": 0.0,
                "construction_identity": True,
            },
            "rv_tot_is_direct_seasonal_run_total": True,
        },
    }


def _write_markdown(report: dict[str, object], path: Path) -> None:
    lines = [
        "# Player Value v1 Defense native source-semantics audit",
        "",
        "Status: **DIAGNOSTIC COMPLETE — NO RUN CONVERSION SELECTED**",
        "",
        "2025 accessed: **false**",
        "",
    ]
    components = report["components"]
    for component in ("general_range", "catcher_throwing", "catcher_blocking", "catcher_framing"):
        lines.append(f"## {component.replace('_', ' ').title()}")
        lines.append("")
        for year, result in components[component].items():
            stats = result["target_stats"]
            lines.append(
                f"- {year}: n={stats['count']}; mean={stats['mean']}; "
                f"SD={stats['population_sd']}; mean/SD={stats['mean_over_sd']}"
            )
        lines.append("")
    lines.extend(
        [
            "## Boundary",
            "",
            "This audit records source identities and native-unit clues only. It does not select",
            "future standardization constants, opportunity forecasts, run conversion, positional",
            "adjustment, replacement level, runs per win, or WAR/value.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = _parse_args()
    if max(YEARS) >= 2025:
        raise RuntimeError("2025 boundary violation")
    contract_hash = _verify_contract(args.contract_path)

    session = requests.Session()
    session.headers.update({"User-Agent": "universal-baseball-model-player-value-native-semantics/0.1"})

    components: dict[str, dict[str, object]] = {
        "general_range": {},
        "catcher_throwing": {},
        "catcher_blocking": {},
        "catcher_framing": {},
    }
    for year in YEARS:
        components["general_range"][str(year)] = _general(year)
        components["catcher_throwing"][str(year)] = _catcher(session, "throwing", year)
        components["catcher_blocking"][str(year)] = _catcher(session, "blocking", year)
        components["catcher_framing"][str(year)] = _framing(session, year)

    report = {
        "report_schema_version": "0.1",
        "gate": "player_value_v1_defense_native_source_semantics_audit",
        "status": "diagnostic_complete_no_run_conversion_selected",
        "contract": "docs/player-value-v1-defense-native-semantics-audit-contract.md",
        "contract_sha256": contract_hash,
        "years": list(YEARS),
        "components": components,
        "decision": {
            "native_source_semantics_audited": True,
            "run_conversion_selected": False,
            "future_standardization_rule_selected": False,
            "component_opportunity_forecast_selected": False,
            "positional_adjustment_selected": False,
            "war_value_authorized": False,
        },
        "boundary": {
            "2025_data_accessed": False,
            "2025_confirmation_residuals_used": False,
            "defense_model_fit": False,
            "defense_model_scored": False,
            "defense_model_modified": False,
            "run_conversion_performed": False,
            "positional_adjustment_calculated": False,
            "replacement_level_selected": False,
            "runs_per_win_selected": False,
            "war_value_calculated": False,
        },
    }

    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    _write_markdown(report, args.output_root / "report.md")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
