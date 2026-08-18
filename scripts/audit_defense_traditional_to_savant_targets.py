#!/usr/bin/env python3
"""Test prior all-level traditional fielding rates against next-year Savant targets."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import polars as pl

from sportsdataverse.mlb.mlb_statcast import (
    mlb_statcast_leaderboard_catcher_blocking,
    mlb_statcast_leaderboard_catcher_throwing,
    mlb_statcast_leaderboard_outs_above_average,
)


SEASONS = {2021, 2022, 2023, 2024}
TARGET_YEARS = (2022, 2023, 2024)
TRANSITIONS = ((2021, 2022), (2022, 2023), (2023, 2024))
LEVEL_BY_LEAGUE = {
    103: "MLB", 104: "MLB", 112: "AAA", 117: "AAA",
    109: "AA", 111: "AA", 113: "AA",
    116: "HIGH_A", 118: "HIGH_A", 126: "HIGH_A",
    110: "SINGLE_A", 122: "SINGLE_A", 123: "SINGLE_A",
    121: "ROOKIE_COMPLEX", 124: "ROOKIE_COMPLEX", 130: "ROOKIE_COMPLEX",
}
POS_ORDER = {"C": 2, "1B": 3, "2B": 4, "3B": 5, "SS": 6, "LF": 7, "CF": 8, "RF": 9}
GENERAL_POSITIONS = {"1B", "2B", "3B", "SS", "LF", "CF", "RF"}
GENERAL_FEATURE_SIGNS = {
    "fielding_pct": 1.0,
    "range_factor_per_9": 1.0,
    "errors_per_9": -1.0,
    "throwing_errors_per_9": -1.0,
    "double_plays_per_9": 1.0,
}
REPORT_ROOT = Path("reports/generated/defense-traditional-to-savant-targets")


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _infer_context(path: Path) -> tuple[int, int]:
    parts = list(path.parts)
    for index, part in enumerate(parts[:-1]):
        try:
            season = int(part)
        except ValueError:
            continue
        if season not in SEASONS or index + 1 >= len(parts):
            continue
        try:
            league_id = int(parts[index + 1])
        except ValueError:
            continue
        if league_id in LEVEL_BY_LEAGUE:
            return season, league_id
    raise RuntimeError(f"cannot infer season/league from {path}")


def _integer(value: Any, *, field: str) -> int:
    if value is None or str(value).strip() == "":
        raise ValueError(f"missing {field}")
    numeric = float(str(value).strip())
    if not numeric.is_integer() or numeric < 0:
        raise ValueError(f"invalid nonnegative integer {field}: {value!r}")
    return int(numeric)


def _innings_to_outs(value: Any) -> int:
    text = str(value if value is not None else "").strip()
    if not text:
        raise ValueError("missing innings")
    if "." in text:
        whole, frac = text.split(".", 1)
    else:
        whole, frac = text, "0"
    if not whole.isdigit() or frac not in {"0", "1", "2"}:
        raise ValueError(f"invalid baseball innings: {text!r}")
    return int(whole) * 3 + int(frac)


def _float_text(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if not text or text.lower() in {"nan", "none", "null", "--"}:
        return None
    if text.endswith("%"):
        text = text[:-1].strip()
    try:
        numeric = float(text)
    except ValueError:
        return None
    return numeric if math.isfinite(numeric) else None


def _rankdata(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(len(values), dtype=float)
    i = 0
    while i < len(values):
        j = i + 1
        while j < len(values) and values[order[j]] == values[order[i]]:
            j += 1
        ranks[order[i:j]] = (i + 1 + j) / 2.0
        i = j
    return ranks


def _corr(x: np.ndarray, y: np.ndarray) -> float | None:
    if len(x) < 2 or np.std(x) == 0 or np.std(y) == 0:
        return None
    result = float(np.corrcoef(x, y)[0, 1])
    return result if math.isfinite(result) else None


def _corr_metrics(x: np.ndarray, y: np.ndarray) -> dict[str, Any]:
    return {
        "pair_count": int(len(x)),
        "pearson": _corr(x, y),
        "spearman": _corr(_rankdata(x), _rankdata(y)) if len(x) else None,
    }


def _position_standardized(frame: pl.DataFrame, feature: str, target: str) -> pl.DataFrame:
    return (
        frame.with_columns(
            (
                (pl.col(feature) - pl.col(feature).mean().over("position"))
                / pl.col(feature).std(ddof=0).over("position")
            ).alias("x_z"),
            (
                (pl.col(target) - pl.col(target).mean().over("position"))
                / pl.col(target).std(ddof=0).over("position")
            ).alias("y_z"),
        )
        .filter(pl.col("x_z").is_finite() & pl.col("y_z").is_finite())
    )


def _build_prior_profiles(source_root: Path) -> tuple[pl.DataFrame, dict[str, Any]]:
    captures = sorted(source_root.rglob("fielding_offset_*.json"))
    if not captures:
        raise RuntimeError("no certified fielding captures found")
    rows: list[dict[str, Any]] = []
    observed_pairs: set[tuple[int, int]] = set()
    for path in captures:
        season, league_id = _infer_context(path)
        observed_pairs.add((season, league_id))
        payload = json.loads(path.read_text(encoding="utf-8"))
        groups = payload.get("stats") or []
        if len(groups) != 1:
            raise RuntimeError(f"expected one stats group in {path}")
        for split in groups[0].get("splits") or []:
            split = _mapping(split)
            player = _mapping(split.get("player") or split.get("person"))
            position = str(_mapping(split.get("position")).get("abbreviation") or "").strip()
            if position not in POS_ORDER:
                continue
            stat = _mapping(split.get("stat"))
            is_catcher = position == "C"
            rows.append(
                {
                    "season": season,
                    "player_id": _integer(player.get("id"), field="player.id"),
                    "position": position,
                    "position_order": POS_ORDER[position],
                    "fielding_outs": _innings_to_outs(stat.get("innings")),
                    "put_outs": _integer(stat.get("putOuts"), field="putOuts"),
                    "assists": _integer(stat.get("assists"), field="assists"),
                    "chances": _integer(stat.get("chances"), field="chances"),
                    "errors": _integer(stat.get("errors"), field="errors"),
                    "throwing_errors": _integer(stat.get("throwingErrors"), field="throwingErrors"),
                    "double_plays": _integer(stat.get("doublePlays"), field="doublePlays"),
                    "caught_stealing": _integer(stat.get("caughtStealing"), field="caughtStealing") if is_catcher else 0,
                    "stolen_bases": _integer(stat.get("stolenBases"), field="stolenBases") if is_catcher else 0,
                    "passed_balls": _integer(stat.get("passedBall"), field="passedBall") if is_catcher else 0,
                    "catcher_interference": _integer(stat.get("catchersInterference"), field="catchersInterference") if is_catcher else 0,
                }
            )
    expected = {(season, league) for season in SEASONS for league in LEVEL_BY_LEAGUE}
    if observed_pairs != expected:
        raise RuntimeError("certified season/league source surface is incomplete")

    position = (
        pl.DataFrame(rows)
        .group_by(["season", "player_id", "position", "position_order"])
        .agg(
            pl.col("fielding_outs").sum(),
            pl.col("put_outs").sum(),
            pl.col("assists").sum(),
            pl.col("chances").sum(),
            pl.col("errors").sum(),
            pl.col("throwing_errors").sum(),
            pl.col("double_plays").sum(),
            pl.col("caught_stealing").sum(),
            pl.col("stolen_bases").sum(),
            pl.col("passed_balls").sum(),
            pl.col("catcher_interference").sum(),
        )
        .with_columns(
            pl.when(pl.col("chances") > 0)
            .then((pl.col("put_outs") + pl.col("assists")) / pl.col("chances"))
            .otherwise(None)
            .alias("fielding_pct"),
            pl.when(pl.col("fielding_outs") > 0)
            .then(27.0 * (pl.col("put_outs") + pl.col("assists")) / pl.col("fielding_outs"))
            .otherwise(None)
            .alias("range_factor_per_9"),
            pl.when(pl.col("fielding_outs") > 0)
            .then(27.0 * pl.col("errors") / pl.col("fielding_outs"))
            .otherwise(None)
            .alias("errors_per_9"),
            pl.when(pl.col("fielding_outs") > 0)
            .then(27.0 * pl.col("throwing_errors") / pl.col("fielding_outs"))
            .otherwise(None)
            .alias("throwing_errors_per_9"),
            pl.when(pl.col("fielding_outs") > 0)
            .then(27.0 * pl.col("double_plays") / pl.col("fielding_outs"))
            .otherwise(None)
            .alias("double_plays_per_9"),
            (pl.col("caught_stealing") + pl.col("stolen_bases")).alias("steal_attempts"),
            pl.when((pl.col("caught_stealing") + pl.col("stolen_bases")) > 0)
            .then(pl.col("caught_stealing") / (pl.col("caught_stealing") + pl.col("stolen_bases")))
            .otherwise(None)
            .alias("caught_stealing_pct"),
            pl.when(pl.col("fielding_outs") > 0)
            .then(27.0 * pl.col("passed_balls") / pl.col("fielding_outs"))
            .otherwise(None)
            .alias("passed_balls_per_9"),
            pl.when(pl.col("fielding_outs") > 0)
            .then(27.0 * pl.col("catcher_interference") / pl.col("fielding_outs"))
            .otherwise(None)
            .alias("catcher_interference_per_9"),
        )
    )
    primary = (
        position.sort(
            ["season", "player_id", "fielding_outs", "position_order"],
            descending=[False, False, True, False],
        )
        .unique(subset=["season", "player_id"], keep="first", maintain_order=True)
        .sort(["season", "player_id"])
    )
    return position, {
        "capture_page_count": len(captures),
        "player_season_position_count": int(position.height),
        "primary_player_season_count": int(primary.height),
    } | {"primary": primary}


def _oaa_target(year: int) -> pl.DataFrame:
    raw = mlb_statcast_leaderboard_outs_above_average(year=year)
    needed = {"player_id", "primary_pos_formatted", "diff_success_rate_formatted"}
    missing = sorted(needed - set(raw.columns))
    if missing:
        raise RuntimeError(f"OAA leaderboard {year} missing columns {missing}")
    rows = []
    for row in raw.select(*sorted(needed)).iter_rows(named=True):
        value = _float_text(row["diff_success_rate_formatted"])
        player = _float_text(row["player_id"])
        position = str(row["primary_pos_formatted"] or "").strip()
        if value is None or player is None or not float(player).is_integer():
            continue
        rows.append(
            {
                "player_id": int(player),
                "target_position": position,
                "target_success_diff": value,
            }
        )
    return pl.DataFrame(rows) if rows else pl.DataFrame(schema={"player_id": pl.Int64, "target_position": pl.Utf8, "target_success_diff": pl.Float64})


def _throwing_target(year: int) -> pl.DataFrame:
    raw = mlb_statcast_leaderboard_catcher_throwing(year=year)
    needed = {"player_id", "sb_attempts", "cs_aa_per_throw"}
    missing = sorted(needed - set(raw.columns))
    if missing:
        raise RuntimeError(f"throwing leaderboard {year} missing columns {missing}")
    rows = []
    for row in raw.select(*sorted(needed)).iter_rows(named=True):
        player = _float_text(row["player_id"])
        attempts = _float_text(row["sb_attempts"])
        value = _float_text(row["cs_aa_per_throw"])
        if player is None or attempts is None or value is None or not float(player).is_integer():
            continue
        rows.append({"player_id": int(player), "target_attempts": attempts, "target_throwing_rate": value})
    return pl.DataFrame(rows) if rows else pl.DataFrame(schema={"player_id": pl.Int64, "target_attempts": pl.Float64, "target_throwing_rate": pl.Float64})


def _blocking_target(year: int) -> pl.DataFrame:
    raw = mlb_statcast_leaderboard_catcher_blocking(year=year)
    needed = {"player_id", "pitches", "blocks_above_average_per_game"}
    missing = sorted(needed - set(raw.columns))
    if missing:
        raise RuntimeError(f"blocking leaderboard {year} missing columns {missing}")
    rows = []
    for row in raw.select(*sorted(needed)).iter_rows(named=True):
        player = _float_text(row["player_id"])
        pitches = _float_text(row["pitches"])
        value = _float_text(row["blocks_above_average_per_game"])
        if player is None or pitches is None or value is None or not float(player).is_integer():
            continue
        rows.append({"player_id": int(player), "target_pitches": pitches, "target_blocking_rate": value})
    return pl.DataFrame(rows) if rows else pl.DataFrame(schema={"player_id": pl.Int64, "target_pitches": pl.Float64, "target_blocking_rate": pl.Float64})


def _general_fold(
    prior_primary: pl.DataFrame,
    target: pl.DataFrame,
    *,
    input_year: int,
    target_year: int,
    feature: str,
) -> tuple[dict[str, Any], np.ndarray, np.ndarray]:
    current = prior_primary.filter(
        (pl.col("season") == input_year)
        & pl.col("position").is_in(sorted(GENERAL_POSITIONS))
        & (pl.col("fielding_outs") >= 300)
        & pl.col(feature).is_not_null()
    )
    if feature == "fielding_pct":
        current = current.filter(pl.col("chances") >= 100)
    joined = (
        current.select("player_id", "position", feature)
        .join(target, on="player_id", how="inner")
        .filter(pl.col("position") == pl.col("target_position"))
        .drop_nulls([feature, "target_success_diff"])
    )
    standardized = _position_standardized(joined, feature, "target_success_diff")
    x = standardized.get_column("x_z").to_numpy().astype(float)
    y = standardized.get_column("y_z").to_numpy().astype(float)
    metrics = _corr_metrics(x, y)
    metrics.update(
        {
            "input_year": input_year,
            "target_year": target_year,
            "pre_standardization_pair_count": int(joined.height),
            "position_counts": joined.group_by("position").len().sort("position").to_dicts(),
        }
    )
    return metrics, x, y


def _catcher_fold(
    catcher: pl.DataFrame,
    target: pl.DataFrame,
    *,
    input_year: int,
    target_year: int,
    feature: str,
    target_col: str,
    extra_filter: pl.Expr,
) -> tuple[dict[str, Any], np.ndarray, np.ndarray]:
    current = catcher.filter(
        (pl.col("season") == input_year)
        & (pl.col("fielding_outs") >= 300)
        & pl.col(feature).is_not_null()
    )
    if feature == "caught_stealing_pct":
        current = current.filter(pl.col("steal_attempts") >= 10)
    joined = (
        current.select("player_id", feature)
        .join(target, on="player_id", how="inner")
        .filter(extra_filter)
        .drop_nulls([feature, target_col])
    )
    x = joined.get_column(feature).to_numpy().astype(float)
    y = joined.get_column(target_col).to_numpy().astype(float)
    metrics = _corr_metrics(x, y)
    metrics.update({"input_year": input_year, "target_year": target_year})
    return metrics, x, y


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    args = parser.parse_args()

    position, meta = _build_prior_profiles(args.source_root)
    primary = meta.pop("primary")
    catcher = position.filter(pl.col("position") == "C")

    targets = {
        year: {
            "oaa": _oaa_target(year),
            "throwing": _throwing_target(year),
            "blocking": _blocking_target(year),
        }
        for year in TARGET_YEARS
    }

    general_results = []
    supported: list[str] = []
    for feature, sign in GENERAL_FEATURE_SIGNS.items():
        folds = []
        pooled_x: list[np.ndarray] = []
        pooled_y: list[np.ndarray] = []
        for input_year, target_year in TRANSITIONS:
            metrics, x, y = _general_fold(
                primary,
                targets[target_year]["oaa"],
                input_year=input_year,
                target_year=target_year,
                feature=feature,
            )
            spearman = metrics["spearman"]
            metrics["expected_direction"] = "positive" if sign > 0 else "negative"
            metrics["signed_spearman"] = spearman * sign if spearman is not None else None
            folds.append(metrics)
            pooled_x.append(x)
            pooled_y.append(y)
        x_all = np.concatenate(pooled_x) if pooled_x else np.array([])
        y_all = np.concatenate(pooled_y) if pooled_y else np.array([])
        pooled = _corr_metrics(x_all, y_all)
        pooled_signed = pooled["spearman"] * sign if pooled["spearman"] is not None else None
        enough = all(fold["pair_count"] >= 100 for fold in folds)
        good_folds = sum(1 for fold in folds if fold["signed_spearman"] is not None and fold["signed_spearman"] >= 0.05)
        passes = bool(enough and good_folds >= 2 and pooled_signed is not None and pooled_signed >= 0.08)
        if passes:
            supported.append(feature)
        general_results.append(
            {
                "feature": feature,
                "expected_direction": "positive" if sign > 0 else "negative",
                "folds": folds,
                "pooled": pooled | {"signed_spearman": pooled_signed},
                "folds_meeting_signed_spearman_0_05": good_folds,
                "savant_target_support": passes,
            }
        )

    catcher_results = []
    for feature, target_name, target_col, sign, extra_filter in (
        (
            "caught_stealing_pct",
            "catcher_throwing_cs_aa_per_throw",
            "target_throwing_rate",
            1.0,
            pl.col("target_attempts") >= 10,
        ),
        (
            "passed_balls_per_9",
            "catcher_blocking_blocks_above_average_per_game",
            "target_blocking_rate",
            -1.0,
            pl.col("target_pitches") >= 500,
        ),
    ):
        folds = []
        pooled_x: list[np.ndarray] = []
        pooled_y: list[np.ndarray] = []
        target_kind = "throwing" if "throwing" in target_name else "blocking"
        for input_year, target_year in TRANSITIONS:
            metrics, x, y = _catcher_fold(
                catcher,
                targets[target_year][target_kind],
                input_year=input_year,
                target_year=target_year,
                feature=feature,
                target_col=target_col,
                extra_filter=extra_filter,
            )
            spearman = metrics["spearman"]
            metrics["signed_spearman"] = spearman * sign if spearman is not None else None
            folds.append(metrics)
            pooled_x.append(x)
            pooled_y.append(y)
        x_all = np.concatenate(pooled_x) if pooled_x else np.array([])
        y_all = np.concatenate(pooled_y) if pooled_y else np.array([])
        pooled = _corr_metrics(x_all, y_all)
        pooled_signed = pooled["spearman"] * sign if pooled["spearman"] is not None else None
        enough = all(fold["pair_count"] >= 30 for fold in folds)
        good_folds = sum(1 for fold in folds if fold["signed_spearman"] is not None and fold["signed_spearman"] >= 0.05)
        passes = bool(enough and good_folds >= 2 and pooled_signed is not None and pooled_signed >= 0.10)
        if passes:
            supported.append(feature)
        catcher_results.append(
            {
                "feature": feature,
                "target": target_name,
                "expected_direction": "positive" if sign > 0 else "negative",
                "folds": folds,
                "pooled": pooled | {"signed_spearman": pooled_signed},
                "folds_meeting_signed_spearman_0_05": good_folds,
                "savant_target_support": passes,
            }
        )

    catcher_results.append(
        {
            "feature": "catcher_interference_per_9",
            "direct_target_available": False,
            "savant_target_support": False,
            "reason": "no direct Savant catcher-interference defensive target in the frozen source set",
        }
    )

    target_summary = {
        str(year): {
            kind: {"row_count": int(frame.height), "columns": frame.columns}
            for kind, frame in year_targets.items()
        }
        for year, year_targets in targets.items()
    }

    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    report = {
        "report_schema_version": "0.1",
        "gate": "defense_traditional_to_next_year_savant_targets",
        "contract": "docs/defense-traditional-to-savant-target-contract.md",
        "source": {
            "historical_source_run_id": 32148467330,
            "target_years": list(TARGET_YEARS),
            **meta,
            "savant_target_summary": target_summary,
        },
        "general_range_features": general_results,
        "catcher_features": catcher_results,
        "decision": {
            "defense_v1_traditional_challenger_supported_features": sorted(set(supported)),
            "traditional_feature_target_signal_established": bool(supported),
            "tier_c_fallback_frozen": False,
            "defense_projection_authorized": False,
            "war_value_authorized": False,
        },
        "boundary": {
            "2025_accessed": False,
            "regression_model_fit": False,
            "feature_weights_selected": False,
            "tracked_range_or_framing_model_modified": False,
            "untracked_player_defense_imputed": False,
        },
    }
    (REPORT_ROOT / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    lines = [
        "# Traditional fielding -> Savant target test",
        "",
        f"- supported features: {sorted(set(supported))}",
    ]
    for row in general_results:
        lines.append(
            f"- {row['feature']}: pooled signed Spearman={row['pooled']['signed_spearman']}, "
            f"support={row['savant_target_support']}"
        )
    for row in catcher_results:
        if row.get("direct_target_available") is False:
            lines.append(f"- {row['feature']}: no direct target; support=False")
        else:
            lines.append(
                f"- {row['feature']}: pooled signed Spearman={row['pooled']['signed_spearman']}, "
                f"support={row['savant_target_support']}"
            )
    lines.extend(["- Defense v1 projection authorized: False", "- WAR/value authorized: False", ""])
    (REPORT_ROOT / "report.md").write_text("\n".join(lines))
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
