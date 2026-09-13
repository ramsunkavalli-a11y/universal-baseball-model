#!/usr/bin/env python3
"""Test high-minors pitch-process evidence against the results-only baseline."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from audit_age_to_peak_talent import _player_score, _player_uncertainty
from audit_one_year_talent_development import (
    PITCHER_COMPONENTS,
    _features,
    _fold,
    _load_sources,
    _pitcher_components,
    _responses,
    _score,
)
from universal_baseball.certification import download_file
from universal_baseball.projection_composition import (
    ilr_transform,
    inverse_ilr_transform,
    sequential_helmert_ilr_basis,
)


YEARS = (2018, 2019, 2021, 2022, 2023, 2024, 2026)
ORIGIN_YEARS = (2018, 2021, 2022, 2023, 2024)
LEVELS = ("aaa", "aa", "a+", "a")
LEVEL_GROUP = {"aaa": "AAA", "aa": "AA", "a+": "HIGH_A", "a": "SINGLE_A"}
BASE_URL = "https://github.com/armstjc/milb-data-repository/releases/download/season_player_pitching"
WORK = Path("data/quarantine/pitcher-process-season")
OUT = Path("reports/generated/pitcher-process-challenger")
ALPHAS = (10.0, 100.0, 1000.0)
FEATURE_SETS = {
    "whiff": ("process_whiff",),
    "strike": ("process_strike",),
    "swing": ("process_swing",),
    "pitches_per_batter": ("process_ppbf",),
    "whiff_and_strike": ("process_whiff", "process_strike"),
    "all_process": (
        "process_whiff", "process_strike", "process_swing", "process_ppbf"
    ),
}


def _load_process() -> pl.DataFrame:
    frames = []
    WORK.mkdir(parents=True, exist_ok=True)
    for year in YEARS:
        for slug in LEVELS:
            name = f"{year}_{slug}_season_pitching_stats.csv"
            path = WORK / name
            if not path.exists():
                download_file(f"{BASE_URL}/{name}", path, timeout_seconds=120)
            raw = pl.read_csv(path, infer_schema_length=10_000, ignore_errors=False)
            frames.append(
                raw.select(
                    pl.col("season").cast(pl.Int64),
                    pl.col("player_id").cast(pl.Int64),
                    pl.lit(LEVEL_GROUP[slug]).alias("level_group"),
                    pl.col("pitching_BF").cast(pl.Float64).alias("bf"),
                    pl.col("pitching_PI").cast(pl.Float64).alias("pitches"),
                    pl.col("pitching_total_swings").cast(pl.Float64).alias("swings"),
                    pl.col("pitching_swing_and_misses").cast(pl.Float64).alias("whiffs"),
                    pl.col("pitching_PI_strikes").cast(pl.Float64).alias("strikes"),
                    pl.col("pitching_PI_balls").cast(pl.Float64).alias("balls"),
                )
            )
    rows = pl.concat(frames, how="vertical_relaxed").group_by(
        "season", "player_id", "level_group"
    ).agg(pl.col("bf", "pitches", "swings", "whiffs", "strikes", "balls").sum())
    invalid = rows.filter(
        (pl.col("whiffs") > pl.col("swings"))
        | (pl.col("swings") > pl.col("pitches"))
        | (pl.col("strikes") + pl.col("balls") != pl.col("pitches"))
    )
    if invalid.height:
        raise ValueError(f"invalid process accounting rows: {invalid.height}")
    return rows


def _process_features(process: pl.DataFrame) -> pl.DataFrame:
    frame = process.filter(
        (pl.col("bf") >= 30) & (pl.col("pitches") > 0) & (pl.col("swings") > 0)
    ).with_columns(
        (pl.col("whiffs").sum().over(["season", "level_group"])
         / pl.col("swings").sum().over(["season", "level_group"])).alias("prior_whiff"),
        (pl.col("strikes").sum().over(["season", "level_group"])
         / pl.col("pitches").sum().over(["season", "level_group"])).alias("prior_strike"),
        (pl.col("swings").sum().over(["season", "level_group"])
         / pl.col("pitches").sum().over(["season", "level_group"])).alias("prior_swing"),
        (pl.col("pitches").sum().over(["season", "level_group"])
         / pl.col("bf").sum().over(["season", "level_group"])).alias("prior_ppbf"),
    )
    return frame.with_columns(
        (((pl.col("whiffs") + 200 * pl.col("prior_whiff")) / (pl.col("swings") + 200))
         - pl.col("prior_whiff")).alias("process_whiff"),
        (((pl.col("strikes") + 500 * pl.col("prior_strike")) / (pl.col("pitches") + 500))
         - pl.col("prior_strike")).alias("process_strike"),
        (((pl.col("swings") + 500 * pl.col("prior_swing")) / (pl.col("pitches") + 500))
         - pl.col("prior_swing")).alias("process_swing"),
        (((pl.col("pitches") + 100 * pl.col("prior_ppbf")) / (pl.col("bf") + 100))
         - pl.col("prior_ppbf")).alias("process_ppbf"),
    ).select(
        "season", "player_id", "level_group", "bf",
        "process_whiff", "process_strike", "process_swing", "process_ppbf",
    )


def _cohort(source: pl.DataFrame, process: pl.DataFrame, origin: int) -> pl.DataFrame:
    outcomes = _fold(
        source, origin=origin, exposure="batters_faced",
        components=PITCHER_COMPONENTS, regression=800.0, horizon=1,
    ).filter(pl.col("level_group") != "ROOKIE_COMPLEX")
    current = process.filter(pl.col("season") == origin).drop("season")
    return outcomes.join(
        current, on=["player_id", "level_group"], how="inner", validate="m:1"
    ).with_columns(pl.lit(origin).alias("process_origin"))


def _design(
    rows: list[dict[str, object]], basis: np.ndarray, feature_set: str | None
) -> np.ndarray:
    base = _features(rows, PITCHER_COMPONENTS, "component_development", basis)
    if feature_set is None:
        return base
    columns = FEATURE_SETS[feature_set]
    extra = np.asarray([
        [float(row[column]) for column in columns]
        for row in rows
    ])
    return np.column_stack((base, extra))


def _fit(
    rows: list[dict[str, object]], basis: np.ndarray, alpha: float,
    feature_set: str | None,
) -> object:
    return make_pipeline(StandardScaler(), Ridge(alpha=alpha)).fit(
        _design(rows, basis, feature_set), _responses(rows, PITCHER_COMPONENTS, basis)
    )


def _predict(
    model: object, rows: list[dict[str, object]], basis: np.ndarray,
    feature_set: str | None,
) -> np.ndarray:
    delta = model.predict(_design(rows, basis, feature_set))
    output = []
    for index, row in enumerate(rows):
        current = np.asarray(ilr_transform(
            [float(row[f"p_{name}"]) for name in PITCHER_COMPONENTS], basis=basis
        ))
        output.append(inverse_ilr_transform(current + delta[index], basis=basis))
    return np.asarray(output)


def _metrics(prediction: np.ndarray, rows: list[dict[str, object]]) -> dict[str, float]:
    player = _player_score(prediction, rows, PITCHER_COMPONENTS)
    event = _score(prediction, rows, PITCHER_COMPONENTS)
    return {
        "player_log_loss": float(player["log_loss"]), "player_brier": float(player["brier"]),
        "event_log_loss": float(event["log_loss"]), "event_brier": float(event["brier"]),
    }


def main() -> int:
    source = _pitcher_components(_load_sources("affiliated_pitching_components.parquet"))
    process = _process_features(_load_process())
    cohorts = {year: _cohort(source, process, year) for year in ORIGIN_YEARS}
    basis = sequential_helmert_ilr_basis(len(PITCHER_COMPONENTS))

    training = cohorts[2018].to_dicts()
    development = cohorts[2021].to_dicts()
    selection = []
    for feature_set in FEATURE_SETS:
        for alpha in ALPHAS:
            base_model = _fit(training, basis, alpha, None)
            candidate_model = _fit(training, basis, alpha, feature_set)
            base = _metrics(_predict(base_model, development, basis, None), development)
            candidate = _metrics(
                _predict(candidate_model, development, basis, feature_set), development
            )
            selection.append({
                "feature_set": feature_set, "alpha": alpha,
                **{key: candidate[key] - base[key] for key in base},
            })
    eligible = [row for row in selection if all(row[key] < 0 for key in (
        "player_log_loss", "player_brier", "event_log_loss", "event_brier"
    ))]
    selected = min(
        eligible or selection,
        key=lambda row: (row["player_log_loss"], row["player_brier"]),
    )

    replay = []
    confirmation_origins = (2022, 2023, 2024)
    for origin in confirmation_origins:
        train_rows = pl.concat(
            [cohorts[year] for year in ORIGIN_YEARS if year < origin]
        ).to_dicts()
        target = cohorts[origin].to_dicts()
        base_model = _fit(train_rows, basis, float(selected["alpha"]), None)
        candidate_model = _fit(
            train_rows, basis, float(selected["alpha"]), str(selected["feature_set"])
        )
        base_prediction = _predict(base_model, target, basis, None)
        candidate_prediction = _predict(
            candidate_model, target, basis, str(selected["feature_set"])
        )
        base = _metrics(base_prediction, target)
        candidate = _metrics(candidate_prediction, target)
        replay.append({
            "origin": origin, "players": len(target),
            "delta": {key: candidate[key] - base[key] for key in base},
            "uncertainty": _player_uncertainty(
                candidate_prediction, base_prediction, target, PITCHER_COMPONENTS
            ),
        })
    keys = ("player_log_loss", "player_brier", "event_log_loss", "event_brier")
    wins = {key: sum(row["delta"][key] < 0 for row in replay) for key in keys}
    uncertainty = sum(
        row["uncertainty"]["log_loss_delta_p975"] <= 0
        and row["uncertainty"]["brier_delta_p975"] <= 0 for row in replay
    )
    passed = all(value == len(replay) for value in wins.values()) and uncertainty >= 1
    ablations = []
    for feature_set in FEATURE_SETS:
        chosen = min(
            (row for row in selection if row["feature_set"] == feature_set),
            key=lambda row: (row["player_log_loss"], row["player_brier"]),
        )
        feature_replay = []
        for origin in confirmation_origins:
            train_rows = pl.concat(
                [cohorts[year] for year in ORIGIN_YEARS if year < origin]
            ).to_dicts()
            target = cohorts[origin].to_dicts()
            base_model = _fit(train_rows, basis, float(chosen["alpha"]), None)
            candidate_model = _fit(
                train_rows, basis, float(chosen["alpha"]), feature_set
            )
            base = _metrics(_predict(base_model, target, basis, None), target)
            candidate = _metrics(
                _predict(candidate_model, target, basis, feature_set), target
            )
            feature_replay.append({
                "origin": origin,
                "delta": {key: candidate[key] - base[key] for key in base},
            })
        ablations.append({
            "feature_set": feature_set, "selected_alpha": chosen["alpha"],
            "development_delta": {key: chosen[key] for key in keys},
            "confirmation": feature_replay,
            "confirmation_wins": {
                key: sum(row["delta"][key] < 0 for row in feature_replay) for key in keys
            },
        })
    report = {
        "report_schema_version": "0.1", "selected": selected,
        "development": selection, "replay": replay, "ablations": ablations, "wins": wins,
        "uncertainty_passes": uncertainty, "promotion": "pass" if passed else "reject",
        "boundary": "next-year component estimate only; not direct peak or FV evidence",
        "rookie_process_used": False, "public_rank_or_fv_used": False,
        "cohort_rows": {str(year): frame.height for year, frame in cohorts.items()},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({key: report[key] for key in (
        "selected", "replay", "wins", "uncertainty_passes", "promotion", "cohort_rows"
    )}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
