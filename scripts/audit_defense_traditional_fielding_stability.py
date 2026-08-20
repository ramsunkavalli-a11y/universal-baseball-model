#!/usr/bin/env python3
"""Screen traditional official fielding rates for adjacent-year reliability."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import polars as pl


SEASONS = {2021, 2022, 2023, 2024}
LEVEL_BY_LEAGUE = {
    103: "MLB", 104: "MLB", 112: "AAA", 117: "AAA",
    109: "AA", 111: "AA", 113: "AA",
    116: "HIGH_A", 118: "HIGH_A", 126: "HIGH_A",
    110: "SINGLE_A", 122: "SINGLE_A", 123: "SINGLE_A",
    121: "ROOKIE_COMPLEX", 124: "ROOKIE_COMPLEX", 130: "ROOKIE_COMPLEX",
}
REPORT_ROOT = Path("reports/generated/defense-traditional-fielding-stability")
TRANSITIONS = ((2021, 2022), (2022, 2023), (2023, 2024))
FEATURES = (
    "fielding_pct",
    "range_factor_per_9",
    "errors_per_9",
    "throwing_errors_per_9",
    "double_plays_per_9",
    "caught_stealing_pct",
    "passed_balls_per_9",
    "catcher_interference_per_9",
)


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
    raise RuntimeError(f"cannot infer season/league from path: {path}")


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


def _rankdata(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(len(values), dtype=float)
    i = 0
    while i < len(values):
        j = i + 1
        while j < len(values) and values[order[j]] == values[order[i]]:
            j += 1
        average_rank = (i + 1 + j) / 2.0
        ranks[order[i:j]] = average_rank
        i = j
    return ranks


def _corr(x: np.ndarray, y: np.ndarray) -> float | None:
    if len(x) < 2 or np.std(x) == 0 or np.std(y) == 0:
        return None
    value = float(np.corrcoef(x, y)[0, 1])
    return value if math.isfinite(value) else None


def _metrics(x: np.ndarray, y: np.ndarray) -> dict[str, Any]:
    pearson = _corr(x, y)
    spearman = _corr(_rankdata(x), _rankdata(y)) if len(x) else None
    return {
        "pair_count": int(len(x)),
        "pearson": pearson,
        "spearman": spearman,
        "current_mean": float(np.mean(x)) if len(x) else None,
        "current_median": float(np.median(x)) if len(x) else None,
        "next_mean": float(np.mean(y)) if len(y) else None,
        "next_median": float(np.median(y)) if len(y) else None,
    }


def _eligible(frame: pl.DataFrame, feature: str) -> pl.DataFrame:
    out = frame.filter(
        (pl.col("current_fielding_outs") >= 300)
        & (pl.col("next_fielding_outs") >= 300)
        & pl.col(f"current_{feature}").is_not_null()
        & pl.col(f"next_{feature}").is_not_null()
    )
    if feature == "fielding_pct":
        out = out.filter(
            (pl.col("current_chances") >= 100)
            & (pl.col("next_chances") >= 100)
        )
    if feature == "caught_stealing_pct":
        out = out.filter(
            (pl.col("position") == "C")
            & (pl.col("current_steal_attempts") >= 10)
            & (pl.col("next_steal_attempts") >= 10)
        )
    if feature in {"passed_balls_per_9", "catcher_interference_per_9"}:
        out = out.filter(pl.col("position") == "C")
    return out


def _feature_pair(frame: pl.DataFrame, feature: str) -> tuple[np.ndarray, np.ndarray]:
    eligible = _eligible(frame, feature)
    return (
        eligible.get_column(f"current_{feature}").to_numpy().astype(float),
        eligible.get_column(f"next_{feature}").to_numpy().astype(float),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    args = parser.parse_args()

    capture_paths = sorted(args.source_root.rglob("fielding_offset_*.json"))
    if not capture_paths:
        raise RuntimeError("no retained fielding capture pages found")

    rows: list[dict[str, Any]] = []
    observed_pairs: set[tuple[int, int]] = set()
    for path in capture_paths:
        season, league_id = _infer_context(path)
        observed_pairs.add((season, league_id))
        payload = json.loads(path.read_text(encoding="utf-8"))
        groups = payload.get("stats") or []
        if len(groups) != 1:
            raise RuntimeError(f"expected one stats group in {path}")
        for split in groups[0].get("splits") or []:
            split = _mapping(split)
            player = _mapping(split.get("player") or split.get("person"))
            position = _mapping(split.get("position"))
            stat = _mapping(split.get("stat"))
            abbreviation = str(position.get("abbreviation") or "").strip()
            if abbreviation in {"P", "DH", ""}:
                continue
            is_catcher = abbreviation == "C"
            rows.append(
                {
                    "season": season,
                    "player_id": _integer(player.get("id"), field="player.id"),
                    "position": abbreviation,
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

    expected_pairs = {(season, league_id) for season in SEASONS for league_id in LEVEL_BY_LEAGUE}
    if observed_pairs != expected_pairs:
        raise RuntimeError(
            f"source pair mismatch missing={sorted(expected_pairs-observed_pairs)} "
            f"unexpected={sorted(observed_pairs-expected_pairs)}"
        )

    raw = pl.DataFrame(rows)
    season_position = (
        raw.group_by(["season", "player_id", "position"])
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
        .sort(["season", "player_id", "position"])
    )

    fold_frames: dict[tuple[int, int], pl.DataFrame] = {}
    for current_season, next_season in TRANSITIONS:
        current = season_position.filter(pl.col("season") == current_season).drop("season")
        next_frame = season_position.filter(pl.col("season") == next_season).drop("season")
        current = current.rename({column: f"current_{column}" for column in current.columns if column not in {"player_id", "position"}})
        next_frame = next_frame.rename({column: f"next_{column}" for column in next_frame.columns if column not in {"player_id", "position"}})
        fold_frames[(current_season, next_season)] = current.join(
            next_frame,
            on=["player_id", "position"],
            how="inner",
        )

    results: list[dict[str, Any]] = []
    warranted: list[str] = []
    for feature in FEATURES:
        folds: list[dict[str, Any]] = []
        pooled_x: list[np.ndarray] = []
        pooled_y: list[np.ndarray] = []
        for transition in TRANSITIONS:
            x, y = _feature_pair(fold_frames[transition], feature)
            metric = _metrics(x, y)
            metric["current_season"] = transition[0]
            metric["next_season"] = transition[1]
            folds.append(metric)
            pooled_x.append(x)
            pooled_y.append(y)
        x_all = np.concatenate(pooled_x) if pooled_x else np.array([], dtype=float)
        y_all = np.concatenate(pooled_y) if pooled_y else np.array([], dtype=float)
        pooled = _metrics(x_all, y_all)
        qualifying_folds = sum(
            1 for fold in folds
            if fold["pair_count"] >= 100
            and fold["spearman"] is not None
            and fold["spearman"] >= 0.10
        )
        all_folds_sufficient = all(fold["pair_count"] >= 100 for fold in folds)
        passes = bool(
            all_folds_sufficient
            and qualifying_folds >= 2
            and pooled["spearman"] is not None
            and pooled["spearman"] >= 0.15
        )
        if passes:
            warranted.append(feature)
        results.append(
            {
                "feature": feature,
                "folds": folds,
                "pooled": pooled,
                "folds_with_spearman_ge_0_10": qualifying_folds,
                "all_folds_pair_count_ge_100": all_folds_sufficient,
                "predictive_target_test_warranted": passes,
            }
        )

    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    report = {
        "report_schema_version": "0.1",
        "gate": "defense_traditional_fielding_adjacent_year_stability",
        "contract": "docs/defense-traditional-fielding-stability-contract.md",
        "source": {
            "historical_source_run_id": 32148467330,
            "artifact_name": "position-role-historical-source-2021-2024",
            "raw_non_pitcher_non_dh_split_count": int(raw.height),
            "player_season_position_count": int(season_position.height),
            "transitions": [list(pair) for pair in TRANSITIONS],
        },
        "features": results,
        "decision": {
            "predictive_target_test_warranted_features": warranted,
            "tracked_target_opening_authorized_for_these_features": bool(warranted),
            "traditional_fielding_skill_established": False,
            "tier_c_fallback_frozen": False,
            "defense_projection_authorized": False,
            "war_value_authorized": False,
        },
        "boundary": {
            "2025_accessed": False,
            "source_refetched": False,
            "tracked_oaa_or_framing_target_accessed": False,
            "regression_model_fit": False,
            "traditional_stat_weight_selected": False,
            "untracked_player_defense_imputed": False,
        },
    }
    (REPORT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Traditional fielding stability screen",
        "",
        f"- player-season-position rows: {season_position.height:,}",
        f"- features screened: {len(FEATURES)}",
        f"- predictive-target tests warranted: {len(warranted)}",
    ]
    for row in results:
        pooled = row["pooled"]
        lines.append(
            f"- {row['feature']}: pooled Spearman={pooled['spearman']}, "
            f"pairs={pooled['pair_count']}, warranted={row['predictive_target_test_warranted']}"
        )
    lines.extend(
        [
            "",
            "## Warranted for later tracked-target test",
            *(f"- `{feature}`" for feature in warranted),
            "" if warranted else "- none",
            "- Traditional fielding skill established: False",
            "- Tier-C fallback frozen: False",
            "- WAR/value authorized: False",
            "",
        ]
    )
    (REPORT_ROOT / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
