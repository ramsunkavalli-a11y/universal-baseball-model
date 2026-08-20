#!/usr/bin/env python3
"""Develop the pre-registered universal Defense v1 candidates.

Uses only certified 2021-2024 official fielding inputs and public 2022-2024
Savant targets. Completed-2025 defensive targets are not accessed.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
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
INPUT_BY_TARGET = {2022: 2021, 2023: 2022, 2024: 2023}
LEVEL_BY_LEAGUE = {
    103: "MLB", 104: "MLB", 112: "AAA", 117: "AAA",
    109: "AA", 111: "AA", 113: "AA",
    116: "HIGH_A", 118: "HIGH_A", 126: "HIGH_A",
    110: "SINGLE_A", 122: "SINGLE_A", 123: "SINGLE_A",
    121: "ROOKIE_COMPLEX", 124: "ROOKIE_COMPLEX", 130: "ROOKIE_COMPLEX",
}
LEVEL_RANK = {
    "ROOKIE_COMPLEX": 1,
    "SINGLE_A": 2,
    "HIGH_A": 3,
    "AA": 4,
    "AAA": 5,
    "MLB": 6,
}
POS_ORDER = {"C": 2, "1B": 3, "2B": 4, "3B": 5, "SS": 6, "LF": 7, "CF": 8, "RF": 9}
GENERAL_POSITIONS = {"1B", "2B", "3B", "SS", "LF", "CF", "RF"}
GENERAL_FEATURES = (
    "fielding_pct",
    "range_factor_per_9",
    "errors_per_9",
    "throwing_errors_per_9",
)
LAMBDA_GRID = (0.0, 0.1, 1.0, 10.0)
REPORT_ROOT = Path("reports/generated/defense-v1-universal-development")


@dataclass(frozen=True)
class Moment:
    mean: float
    sd: float
    count: int


@dataclass
class GeneralNormalizer:
    cell: dict[str, dict[tuple[str, str], Moment]]
    position: dict[str, dict[str, Moment]]
    global_: dict[str, Moment]


@dataclass(frozen=True)
class CatcherNormalizer:
    feature: str
    moment: Moment


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
        result = float(text)
    except ValueError:
        return None
    return result if math.isfinite(result) else None


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
    if len(x) < 2 or np.std(x) <= 1e-12 or np.std(y) <= 1e-12:
        return None
    result = float(np.corrcoef(x, y)[0, 1])
    return result if math.isfinite(result) else None


def _metrics(y: np.ndarray, pred: np.ndarray) -> dict[str, Any]:
    if len(y) != len(pred):
        raise ValueError("target/prediction length mismatch")
    if not len(y):
        return {
            "player_count": 0,
            "mse": None,
            "mae": None,
            "pearson": None,
            "spearman": None,
            "calibration_intercept": None,
            "calibration_slope": None,
        }
    residual = y - pred
    pearson = _corr(pred, y)
    spearman = _corr(_rankdata(pred), _rankdata(y))
    if np.std(pred) > 1e-12:
        design = np.column_stack([np.ones(len(pred)), pred])
        beta, *_ = np.linalg.lstsq(design, y, rcond=None)
        cal_intercept, cal_slope = float(beta[0]), float(beta[1])
    else:
        cal_intercept = None
        cal_slope = None
    return {
        "player_count": int(len(y)),
        "mse": float(np.mean(residual**2)),
        "mae": float(np.mean(np.abs(residual))),
        "pearson": pearson,
        "spearman": spearman,
        "calibration_intercept": cal_intercept,
        "calibration_slope": cal_slope,
    }


def _ridge_fit(x: np.ndarray, y: np.ndarray, lam: float) -> np.ndarray:
    if x.ndim != 2 or len(x) != len(y):
        raise ValueError("invalid ridge dimensions")
    design = np.column_stack([np.ones(len(x)), x])
    penalty = np.eye(design.shape[1], dtype=float) * float(lam)
    penalty[0, 0] = 0.0
    lhs = design.T @ design + penalty
    rhs = design.T @ y
    try:
        return np.linalg.solve(lhs, rhs)
    except np.linalg.LinAlgError:
        return np.linalg.pinv(lhs) @ rhs


def _predict(beta: np.ndarray, x: np.ndarray) -> np.ndarray:
    return np.column_stack([np.ones(len(x)), x]) @ beta


def _moment(values: list[float]) -> Moment | None:
    if not values:
        return None
    array = np.asarray(values, dtype=float)
    array = array[np.isfinite(array)]
    if not len(array):
        return None
    sd = float(np.std(array, ddof=0))
    return Moment(mean=float(np.mean(array)), sd=sd, count=int(len(array)))


def _load_profiles(source_root: Path) -> tuple[pl.DataFrame, dict[str, Any]]:
    paths = sorted(source_root.rglob("fielding_offset_*.json"))
    if not paths:
        raise RuntimeError("no certified fielding capture pages found")
    rows: list[dict[str, Any]] = []
    observed_pairs: set[tuple[int, int]] = set()
    for path in paths:
        season, league_id = _infer_context(path)
        observed_pairs.add((season, league_id))
        level_group = LEVEL_BY_LEAGUE[league_id]
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
                    "league_id": league_id,
                    "level_group": level_group,
                    "level_rank": LEVEL_RANK[level_group],
                    "player_id": _integer(player.get("id"), field="player.id"),
                    "position": position,
                    "position_order": POS_ORDER[position],
                    "fielding_outs": _innings_to_outs(stat.get("innings")),
                    "put_outs": _integer(stat.get("putOuts"), field="putOuts"),
                    "assists": _integer(stat.get("assists"), field="assists"),
                    "chances": _integer(stat.get("chances"), field="chances"),
                    "errors": _integer(stat.get("errors"), field="errors"),
                    "throwing_errors": _integer(stat.get("throwingErrors"), field="throwingErrors"),
                    "caught_stealing": _integer(stat.get("caughtStealing"), field="caughtStealing") if is_catcher else 0,
                    "stolen_bases": _integer(stat.get("stolenBases"), field="stolenBases") if is_catcher else 0,
                    "passed_balls": _integer(stat.get("passedBall"), field="passedBall") if is_catcher else 0,
                }
            )
    expected_pairs = {(season, league) for season in SEASONS for league in LEVEL_BY_LEAGUE}
    if observed_pairs != expected_pairs:
        raise RuntimeError(
            f"certified source pair mismatch missing={sorted(expected_pairs-observed_pairs)} "
            f"unexpected={sorted(observed_pairs-expected_pairs)}"
        )

    raw = pl.DataFrame(rows)
    highest_level = (
        raw.filter(pl.col("fielding_outs") > 0)
        .group_by(["season", "player_id"])
        .agg(pl.col("level_rank").max().alias("current_level_rank"))
        .with_columns(
            pl.col("current_level_rank")
            .replace_strict({rank: level for level, rank in LEVEL_RANK.items()}, return_dtype=pl.Utf8)
            .alias("current_level_group")
        )
        .select("season", "player_id", "current_level_group")
    )
    position = (
        raw.group_by(["season", "player_id", "position", "position_order"])
        .agg(
            pl.col("fielding_outs").sum(),
            pl.col("put_outs").sum(),
            pl.col("assists").sum(),
            pl.col("chances").sum(),
            pl.col("errors").sum(),
            pl.col("throwing_errors").sum(),
            pl.col("caught_stealing").sum(),
            pl.col("stolen_bases").sum(),
            pl.col("passed_balls").sum(),
        )
        .join(highest_level, on=["season", "player_id"], how="left")
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
            (pl.col("caught_stealing") + pl.col("stolen_bases")).alias("steal_attempts"),
            pl.when((pl.col("caught_stealing") + pl.col("stolen_bases")) > 0)
            .then(pl.col("caught_stealing") / (pl.col("caught_stealing") + pl.col("stolen_bases")))
            .otherwise(None)
            .alias("caught_stealing_pct"),
            pl.when(pl.col("fielding_outs") > 0)
            .then(27.0 * pl.col("passed_balls") / pl.col("fielding_outs"))
            .otherwise(None)
            .alias("passed_balls_per_9"),
        )
        .sort(["season", "player_id", "position"])
    )
    primary = (
        position.sort(
            ["season", "player_id", "fielding_outs", "position_order"],
            descending=[False, False, True, False],
        )
        .unique(subset=["season", "player_id"], keep="first", maintain_order=True)
        .sort(["season", "player_id"])
    )
    catcher = position.filter(pl.col("position") == "C").sort(["season", "player_id"])
    return primary, {
        "catcher": catcher,
        "capture_page_count": len(paths),
        "raw_position_split_count": int(raw.height),
        "player_season_position_count": int(position.height),
        "primary_player_season_count": int(primary.height),
    }


def _general_targets() -> dict[int, pl.DataFrame]:
    targets: dict[int, pl.DataFrame] = {}
    for year in TARGET_YEARS:
        raw = mlb_statcast_leaderboard_outs_above_average(year=year)
        needed = {"player_id", "primary_pos_formatted", "diff_success_rate_formatted"}
        missing = sorted(needed - set(raw.columns))
        if missing:
            raise RuntimeError(f"OAA target {year} missing {missing}")
        rows: list[dict[str, Any]] = []
        for row in raw.select(*sorted(needed)).iter_rows(named=True):
            player = _float_text(row["player_id"])
            target = _float_text(row["diff_success_rate_formatted"])
            position = str(row["primary_pos_formatted"] or "").strip()
            if (
                player is None
                or not float(player).is_integer()
                or target is None
                or position not in GENERAL_POSITIONS
            ):
                continue
            rows.append({"player_id": int(player), "position": position, "target_raw": target})
        frame = pl.DataFrame(rows)
        if frame.is_empty():
            raise RuntimeError(f"empty OAA target for {year}")
        moments = frame.group_by("position").agg(
            pl.col("target_raw").mean().alias("target_mean"),
            pl.col("target_raw").std(ddof=0).alias("target_sd"),
            pl.len().alias("target_position_count"),
        )
        frame = (
            frame.join(moments, on="position", how="left")
            .filter(pl.col("target_sd").is_not_null() & (pl.col("target_sd") > 1e-12))
            .with_columns(((pl.col("target_raw") - pl.col("target_mean")) / pl.col("target_sd")).alias("target_z"))
        )
        targets[year] = frame
    return targets


def _catcher_targets(kind: str) -> dict[int, pl.DataFrame]:
    targets: dict[int, pl.DataFrame] = {}
    for year in TARGET_YEARS:
        if kind == "throwing":
            raw = mlb_statcast_leaderboard_catcher_throwing(year=year)
            needed = {"player_id", "sb_attempts", "cs_aa_per_throw"}
            missing = sorted(needed - set(raw.columns))
            if missing:
                raise RuntimeError(f"throwing target {year} missing {missing}")
            rows = []
            for row in raw.select(*sorted(needed)).iter_rows(named=True):
                player = _float_text(row["player_id"])
                attempts = _float_text(row["sb_attempts"])
                target = _float_text(row["cs_aa_per_throw"])
                if (
                    player is not None
                    and float(player).is_integer()
                    and attempts is not None
                    and attempts >= 10
                    and target is not None
                ):
                    rows.append({"player_id": int(player), "target_raw": target})
        elif kind == "blocking":
            raw = mlb_statcast_leaderboard_catcher_blocking(year=year)
            needed = {"player_id", "pitches", "blocks_above_average_per_game"}
            missing = sorted(needed - set(raw.columns))
            if missing:
                raise RuntimeError(f"blocking target {year} missing {missing}")
            rows = []
            for row in raw.select(*sorted(needed)).iter_rows(named=True):
                player = _float_text(row["player_id"])
                pitches = _float_text(row["pitches"])
                target = _float_text(row["blocks_above_average_per_game"])
                if (
                    player is not None
                    and float(player).is_integer()
                    and pitches is not None
                    and pitches >= 500
                    and target is not None
                ):
                    rows.append({"player_id": int(player), "target_raw": target})
        else:
            raise ValueError(kind)
        frame = pl.DataFrame(rows)
        if frame.is_empty():
            raise RuntimeError(f"empty catcher {kind} target for {year}")
        mean = float(frame.get_column("target_raw").mean())
        sd = float(frame.get_column("target_raw").std(ddof=0))
        if not math.isfinite(sd) or sd <= 1e-12:
            raise RuntimeError(f"degenerate catcher {kind} target SD {year}")
        targets[year] = frame.with_columns(((pl.col("target_raw") - mean) / sd).alias("target_z"))
    return targets


def _eligible_general(frame: pl.DataFrame) -> pl.DataFrame:
    return frame.filter(
        pl.col("position").is_in(sorted(GENERAL_POSITIONS))
        & (pl.col("fielding_outs") >= 300)
        & (pl.col("chances") >= 100)
        & pl.all_horizontal([pl.col(feature).is_not_null() for feature in GENERAL_FEATURES])
        & pl.col("current_level_group").is_not_null()
    )


def _fit_general_normalizer(profiles: pl.DataFrame, input_years: set[int]) -> GeneralNormalizer:
    source = _eligible_general(profiles.filter(pl.col("season").is_in(sorted(input_years))))
    if source.is_empty():
        raise RuntimeError("no general normalization source rows")
    cell: dict[str, dict[tuple[str, str], Moment]] = {feature: {} for feature in GENERAL_FEATURES}
    position: dict[str, dict[str, Moment]] = {feature: {} for feature in GENERAL_FEATURES}
    global_: dict[str, Moment] = {}
    for feature in GENERAL_FEATURES:
        global_moment = _moment([float(v) for v in source.get_column(feature).drop_nulls().to_list()])
        if global_moment is None or global_moment.sd <= 1e-12:
            raise RuntimeError(f"degenerate global moment for {feature}")
        global_[feature] = global_moment
        for row in source.group_by(["position", "current_level_group"]).agg(
            pl.col(feature).mean().alias("mean"),
            pl.col(feature).std(ddof=0).alias("sd"),
            pl.len().alias("n"),
        ).iter_rows(named=True):
            if int(row["n"]) >= 30 and row["sd"] is not None and float(row["sd"]) > 1e-12:
                cell[feature][(str(row["position"]), str(row["current_level_group"]))] = Moment(
                    float(row["mean"]), float(row["sd"]), int(row["n"])
                )
        for row in source.group_by("position").agg(
            pl.col(feature).mean().alias("mean"),
            pl.col(feature).std(ddof=0).alias("sd"),
            pl.len().alias("n"),
        ).iter_rows(named=True):
            if row["sd"] is not None and float(row["sd"]) > 1e-12:
                position[feature][str(row["position"])] = Moment(
                    float(row["mean"]), float(row["sd"]), int(row["n"])
                )
    return GeneralNormalizer(cell=cell, position=position, global_=global_)


def _general_z(row: Mapping[str, Any], feature: str, normalizer: GeneralNormalizer) -> float:
    key = (str(row["position"]), str(row["current_level_group"]))
    moment = normalizer.cell[feature].get(key)
    if moment is None:
        moment = normalizer.position[feature].get(str(row["position"]))
    if moment is None:
        moment = normalizer.global_[feature]
    return (float(row[feature]) - moment.mean) / moment.sd


def _fit_catcher_normalizer(catcher: pl.DataFrame, input_years: set[int], feature: str, kind: str) -> CatcherNormalizer:
    source = catcher.filter(
        pl.col("season").is_in(sorted(input_years))
        & (pl.col("fielding_outs") >= 300)
        & pl.col(feature).is_not_null()
    )
    if kind == "throwing":
        source = source.filter(pl.col("steal_attempts") >= 10)
    values = [float(v) for v in source.get_column(feature).drop_nulls().to_list()]
    moment = _moment(values)
    if moment is None or moment.sd <= 1e-12:
        raise RuntimeError(f"degenerate catcher normalizer {kind}")
    return CatcherNormalizer(feature=feature, moment=moment)


def _catcher_z(row: Mapping[str, Any], normalizer: CatcherNormalizer) -> float:
    return (float(row[normalizer.feature]) - normalizer.moment.mean) / normalizer.moment.sd


def _general_matrix(
    profiles: pl.DataFrame,
    targets: dict[int, pl.DataFrame],
    target_years: set[int],
    normalizer: GeneralNormalizer,
    family: str,
) -> tuple[np.ndarray, np.ndarray, list[dict[str, Any]]]:
    index = {(int(r["season"]), int(r["player_id"])): r for r in profiles.iter_rows(named=True)}
    x_rows: list[list[float]] = []
    y_rows: list[float] = []
    meta: list[dict[str, Any]] = []
    for target_year in sorted(target_years):
        input_year = INPUT_BY_TARGET[target_year]
        current = _eligible_general(profiles.filter(pl.col("season") == input_year))
        joined = current.join(
            targets[target_year].select("player_id", pl.col("position").alias("target_position"), "target_z"),
            on="player_id",
            how="inner",
        ).filter(pl.col("position") == pl.col("target_position"))
        for row in joined.iter_rows(named=True):
            current_z = {feature: _general_z(row, feature, normalizer) for feature in GENERAL_FEATURES}
            if family == "U1":
                features = [current_z[feature] for feature in GENERAL_FEATURES]
            elif family == "U2":
                prior = index.get((input_year - 1, int(row["player_id"])))
                history: list[float] = []
                for feature in GENERAL_FEATURES:
                    if (
                        prior is not None
                        and prior["position"] in GENERAL_POSITIONS
                        and int(prior["fielding_outs"]) >= 300
                        and int(prior["chances"]) >= 100
                        and prior[feature] is not None
                        and prior["current_level_group"] is not None
                    ):
                        prior_z = _general_z(prior, feature, normalizer)
                        current_outs = float(row["fielding_outs"])
                        prior_outs = float(prior["fielding_outs"])
                        value = (current_outs * current_z[feature] + 0.5 * prior_outs * prior_z) / (current_outs + 0.5 * prior_outs)
                    else:
                        value = current_z[feature]
                    history.append(value)
                features = history
            else:
                raise ValueError(family)
            if not all(math.isfinite(v) for v in features):
                continue
            x_rows.append(features)
            y_rows.append(float(row["target_z"]))
            meta.append({"player_id": int(row["player_id"]), "target_year": target_year})
    return np.asarray(x_rows, dtype=float), np.asarray(y_rows, dtype=float), meta


def _catcher_matrix(
    catcher: pl.DataFrame,
    targets: dict[int, pl.DataFrame],
    target_years: set[int],
    normalizer: CatcherNormalizer,
    family: str,
    kind: str,
) -> tuple[np.ndarray, np.ndarray, list[dict[str, Any]]]:
    index = {(int(r["season"]), int(r["player_id"])): r for r in catcher.iter_rows(named=True)}
    x_rows: list[list[float]] = []
    y_rows: list[float] = []
    meta: list[dict[str, Any]] = []
    for target_year in sorted(target_years):
        input_year = INPUT_BY_TARGET[target_year]
        current = catcher.filter(
            (pl.col("season") == input_year)
            & (pl.col("fielding_outs") >= 300)
            & pl.col(normalizer.feature).is_not_null()
        )
        if kind == "throwing":
            current = current.filter(pl.col("steal_attempts") >= 10)
        joined = current.join(targets[target_year].select("player_id", "target_z"), on="player_id", how="inner")
        for row in joined.iter_rows(named=True):
            current_z = _catcher_z(row, normalizer)
            if family == "C1":
                feature = current_z
            elif family == "C2":
                prior = index.get((input_year - 1, int(row["player_id"])))
                if prior is not None and int(prior["fielding_outs"]) >= 300 and prior[normalizer.feature] is not None:
                    if kind != "throwing" or int(prior["steal_attempts"]) >= 10:
                        prior_z = _catcher_z(prior, normalizer)
                        current_exposure = float(row["steal_attempts"] if kind == "throwing" else row["fielding_outs"])
                        prior_exposure = float(prior["steal_attempts"] if kind == "throwing" else prior["fielding_outs"])
                        feature = (current_exposure * current_z + 0.5 * prior_exposure * prior_z) / (current_exposure + 0.5 * prior_exposure)
                    else:
                        feature = current_z
                else:
                    feature = current_z
            else:
                raise ValueError(family)
            if not math.isfinite(feature):
                continue
            x_rows.append([feature])
            y_rows.append(float(row["target_z"]))
            meta.append({"player_id": int(row["player_id"]), "target_year": target_year})
    return np.asarray(x_rows, dtype=float), np.asarray(y_rows, dtype=float), meta


def _evaluate_general(profiles: pl.DataFrame, targets: dict[int, pl.DataFrame]) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    b0_folds: dict[int, dict[str, Any]] = {}
    b0_oof_y: list[np.ndarray] = []
    b0_oof_p: list[np.ndarray] = []

    for held_year in TARGET_YEARS:
        train_years = set(TARGET_YEARS) - {held_year}
        normalizer = _fit_general_normalizer(profiles, {INPUT_BY_TARGET[y] for y in train_years})
        _, y_hold, _ = _general_matrix(profiles, targets, {held_year}, normalizer, "U1")
        pred = np.zeros(len(y_hold), dtype=float)
        b0_folds[held_year] = _metrics(y_hold, pred)
        b0_oof_y.append(y_hold)
        b0_oof_p.append(pred)
    b0_pooled = _metrics(np.concatenate(b0_oof_y), np.concatenate(b0_oof_p))

    for family in ("U1", "U2"):
        for lam in LAMBDA_GRID:
            folds: list[dict[str, Any]] = []
            oof_y: list[np.ndarray] = []
            oof_pred: list[np.ndarray] = []
            finite = True
            for held_year in TARGET_YEARS:
                train_years = set(TARGET_YEARS) - {held_year}
                normalizer = _fit_general_normalizer(profiles, {INPUT_BY_TARGET[y] for y in train_years})
                x_train, y_train, _ = _general_matrix(profiles, targets, train_years, normalizer, family)
                x_hold, y_hold, _ = _general_matrix(profiles, targets, {held_year}, normalizer, family)
                if not len(y_train) or not len(y_hold):
                    finite = False
                    fold_metrics = _metrics(y_hold, np.zeros(len(y_hold)))
                    pred = np.zeros(len(y_hold))
                    beta = np.array([])
                else:
                    beta = _ridge_fit(x_train, y_train, lam)
                    pred = _predict(beta, x_hold)
                    finite = finite and bool(np.isfinite(beta).all() and np.isfinite(pred).all())
                    fold_metrics = _metrics(y_hold, pred)
                baseline = b0_folds[held_year]
                fold_metrics.update(
                    {
                        "target_year": held_year,
                        "baseline_mse": baseline["mse"],
                        "mse_relative_vs_b0": (
                            (fold_metrics["mse"] - baseline["mse"]) / baseline["mse"]
                            if fold_metrics["mse"] is not None and baseline["mse"] not in {None, 0.0}
                            else None
                        ),
                        "train_player_count": int(len(y_train)),
                        "coefficients": beta.tolist(),
                    }
                )
                folds.append(fold_metrics)
                oof_y.append(y_hold)
                oof_pred.append(pred)
            y_all = np.concatenate(oof_y)
            p_all = np.concatenate(oof_pred)
            pooled = _metrics(y_all, p_all)
            b0_mse = float(b0_pooled["mse"])
            pooled_improvement = (b0_mse - float(pooled["mse"])) / b0_mse
            folds_better = sum(
                1 for fold in folds
                if fold["mse"] is not None and fold["baseline_mse"] is not None and fold["mse"] < fold["baseline_mse"]
            )
            worst_relative = max(float(fold["mse_relative_vs_b0"]) for fold in folds if fold["mse_relative_vs_b0"] is not None)
            passes = bool(
                finite
                and folds_better >= 2
                and pooled_improvement >= 0.02
                and worst_relative <= 0.05
                and pooled["spearman"] is not None
                and pooled["spearman"] >= 0.10
            )
            candidates.append(
                {
                    "family": family,
                    "lambda": lam,
                    "folds": folds,
                    "pooled": pooled,
                    "pooled_mse_improvement_vs_b0": pooled_improvement,
                    "folds_mse_better_than_b0": folds_better,
                    "worst_fold_mse_relative_vs_b0": worst_relative,
                    "finite": finite,
                    "passed": passes,
                }
            )

    eligible = [row for row in candidates if row["passed"]]
    if eligible:
        eligible.sort(key=lambda row: (row["pooled"]["mse"], 0 if row["family"] == "U1" else 1, row["lambda"]))
        selected = {"family": eligible[0]["family"], "lambda": eligible[0]["lambda"]}
    else:
        selected = {"family": "B0", "lambda": None}
    return {
        "baseline": {"folds": [{"target_year": year, **b0_folds[year]} for year in TARGET_YEARS], "pooled": b0_pooled},
        "candidates": candidates,
        "selected": selected,
        "universal_general_range_passed": selected["family"] != "B0",
    }


def _evaluate_catcher(catcher: pl.DataFrame, targets: dict[int, pl.DataFrame], kind: str, feature: str) -> dict[str, Any]:
    families = ("C1", "C2")
    b0_folds: dict[int, dict[str, Any]] = {}
    b0_y: list[np.ndarray] = []
    for held_year in TARGET_YEARS:
        train_years = set(TARGET_YEARS) - {held_year}
        normalizer = _fit_catcher_normalizer(catcher, {INPUT_BY_TARGET[y] for y in train_years}, feature, kind)
        _, y_hold, _ = _catcher_matrix(catcher, targets, {held_year}, normalizer, "C1", kind)
        b0_folds[held_year] = _metrics(y_hold, np.zeros(len(y_hold)))
        b0_y.append(y_hold)
    b0_pooled = _metrics(np.concatenate(b0_y), np.zeros(sum(len(y) for y in b0_y)))

    candidates = []
    for family in families:
        folds = []
        oof_y: list[np.ndarray] = []
        oof_pred: list[np.ndarray] = []
        finite = True
        for held_year in TARGET_YEARS:
            train_years = set(TARGET_YEARS) - {held_year}
            normalizer = _fit_catcher_normalizer(catcher, {INPUT_BY_TARGET[y] for y in train_years}, feature, kind)
            x_train, y_train, _ = _catcher_matrix(catcher, targets, train_years, normalizer, family, kind)
            x_hold, y_hold, _ = _catcher_matrix(catcher, targets, {held_year}, normalizer, family, kind)
            beta = _ridge_fit(x_train, y_train, 0.0)
            pred = _predict(beta, x_hold)
            finite = finite and bool(np.isfinite(beta).all() and np.isfinite(pred).all())
            metric = _metrics(y_hold, pred)
            baseline = b0_folds[held_year]
            metric.update(
                {
                    "target_year": held_year,
                    "baseline_mse": baseline["mse"],
                    "mse_relative_vs_b0": (
                        (metric["mse"] - baseline["mse"]) / baseline["mse"]
                        if metric["mse"] is not None and baseline["mse"] not in {None, 0.0}
                        else None
                    ),
                    "train_player_count": int(len(y_train)),
                    "coefficients": beta.tolist(),
                }
            )
            folds.append(metric)
            oof_y.append(y_hold)
            oof_pred.append(pred)
        y_all = np.concatenate(oof_y)
        p_all = np.concatenate(oof_pred)
        pooled = _metrics(y_all, p_all)
        b0_mse = float(b0_pooled["mse"])
        improvement = (b0_mse - float(pooled["mse"])) / b0_mse
        folds_better = sum(1 for fold in folds if fold["mse"] < fold["baseline_mse"])
        worst_relative = max(float(fold["mse_relative_vs_b0"]) for fold in folds)
        all_counts = all(int(fold["player_count"]) >= 30 for fold in folds)
        passes = bool(
            finite
            and all_counts
            and folds_better >= 2
            and improvement >= 0.02
            and worst_relative <= 0.075
            and pooled["spearman"] is not None
            and pooled["spearman"] >= 0.10
        )
        candidates.append(
            {
                "family": family,
                "folds": folds,
                "pooled": pooled,
                "pooled_mse_improvement_vs_b0": improvement,
                "folds_mse_better_than_b0": folds_better,
                "worst_fold_mse_relative_vs_b0": worst_relative,
                "all_fold_counts_ge_30": all_counts,
                "finite": finite,
                "passed": passes,
            }
        )
    eligible = [row for row in candidates if row["passed"]]
    if eligible:
        eligible.sort(key=lambda row: (row["pooled"]["mse"], 0 if row["family"] == "C1" else 1))
        selected = eligible[0]["family"]
    else:
        selected = "B0"
    return {
        "component": kind,
        "feature": feature,
        "baseline": {"folds": [{"target_year": year, **b0_folds[year]} for year in TARGET_YEARS], "pooled": b0_pooled},
        "candidates": candidates,
        "selected": selected,
        "component_passed": selected != "B0",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    args = parser.parse_args()

    primary, meta = _load_profiles(args.source_root)
    catcher = meta.pop("catcher")
    general_targets = _general_targets()
    throwing_targets = _catcher_targets("throwing")
    blocking_targets = _catcher_targets("blocking")

    general = _evaluate_general(primary, general_targets)
    throwing = _evaluate_catcher(catcher, throwing_targets, "throwing", "caught_stealing_pct")
    blocking = _evaluate_catcher(catcher, blocking_targets, "blocking", "passed_balls_per_9")

    report = {
        "report_schema_version": "0.1",
        "gate": "defense_v1_universal_development",
        "contract": "docs/defense-v1-development-contract.md",
        "source": {
            "historical_source_run_id": 32148467330,
            "artifact_name": "position-role-historical-source-2021-2024",
            "target_years": list(TARGET_YEARS),
            **meta,
            "general_target_rows": {str(year): int(frame.height) for year, frame in general_targets.items()},
            "throwing_target_rows": {str(year): int(frame.height) for year, frame in throwing_targets.items()},
            "blocking_target_rows": {str(year): int(frame.height) for year, frame in blocking_targets.items()},
        },
        "general_range": general,
        "catcher_throwing": throwing,
        "catcher_blocking": blocking,
        "decision": {
            "selected_general_range_family": general["selected"],
            "selected_catcher_throwing_family": throwing["selected"],
            "selected_catcher_blocking_family": blocking["selected"],
            "any_universal_component_passed": bool(
                general["universal_general_range_passed"] or throwing["component_passed"] or blocking["component_passed"]
            ),
            "tracked_incremental_challenger_authorized_next": bool(
                general["universal_general_range_passed"] or throwing["component_passed"] or blocking["component_passed"]
            ),
            "age_challenger_authorized_next": bool(general["universal_general_range_passed"]),
            "2025_confirmation_authorized": False,
            "defense_v1_frozen": False,
            "war_value_authorized": False,
        },
        "boundary": {
            "2025_defensive_targets_accessed": False,
            "tracked_evidence_used": False,
            "age_used": False,
            "playing_time_v1_modified": False,
            "position_role_v1_modified": False,
            "run_value_conversion_performed": False,
        },
    }
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    (REPORT_ROOT / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Defense v1 universal development",
        "",
        f"- general selected: {general['selected']}",
        f"- catcher throwing selected: {throwing['selected']}",
        f"- catcher blocking selected: {blocking['selected']}",
        f"- any component passed: {report['decision']['any_universal_component_passed']}",
        "- 2025 defensive targets accessed: False",
        "- Defense v1 frozen: False",
        "- WAR/value authorized: False",
        "",
    ]
    (REPORT_ROOT / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
