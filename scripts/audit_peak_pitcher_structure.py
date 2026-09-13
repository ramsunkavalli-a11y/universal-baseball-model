#!/usr/bin/env python3
"""Test simple pitcher structure beyond the frozen peak component model.

The challenger follows the public KATOH/OOPSY lesson without importing public
grades: keep translated components primary, then ask whether origin starter share
and level-specific component effects improve later age-24-to-26 component talent.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

from audit_age_to_peak_talent import (
    ALPHAS,
    PITCHER_COMPONENTS,
    ROOT as PEAK_ROOT,
    _completed_fit_examples,
    _fit_peak,
    _player_score,
    _player_uncertainty,
)
from audit_one_year_talent_development import (
    LEVELS,
    _composition,
    _features,
    _load_sources,
    _pitcher_components,
    _predict as _baseline_predict,
    _responses,
    _score,
)
from universal_baseball.projection_composition import (
    ilr_transform,
    inverse_ilr_transform,
    sequential_helmert_ilr_basis,
)
from universal_baseball.draft_source import draft_pedigree_as_of


OUT = Path("reports/generated/peak-pitcher-structure")
FORMS = (
    "starter_history",
    "level_components",
    "role_and_level",
    "draft_pedigree",
    "role_and_pedigree",
    "all_structure",
)


def _attach_origin_role(examples: pl.DataFrame, source: pl.DataFrame) -> pl.DataFrame:
    role = (
        source.filter(pl.col("games") > 0)
        .group_by("player_id", pl.col("season").alias("origin_year"))
        .agg(pl.col("games").sum(), pl.col("starts").sum())
        .with_columns(
            (pl.col("starts") / pl.col("games")).clip(0.0, 1.0).alias("start_share")
        )
        .select("player_id", "origin_year", "start_share")
    )
    result = examples.join(
        role, on=["player_id", "origin_year"], how="left", validate="m:1"
    ).with_columns(pl.col("start_share").fill_null(0.0))
    if result.height != examples.height:
        raise ValueError("role join changed peak-example row count")
    return result


def _attach_origin_pedigree(
    examples: pl.DataFrame, draft_history: pl.DataFrame
) -> pl.DataFrame:
    frames = []
    for origin in sorted(examples.get_column("origin_year").unique().to_list()):
        cohort = examples.filter(pl.col("origin_year") == origin)
        pedigree = draft_pedigree_as_of(draft_history, int(origin))
        frames.append(cohort.join(pedigree, on="player_id", how="left", validate="m:1"))
    return pl.concat(frames, how="vertical_relaxed").with_columns(
        pl.col("rule4_drafted").fill_null(False),
        pl.col("draft_pick_quality").fill_null(0.0),
        pl.col("signing_bonus_percentile").fill_null(0.0),
        pl.col("signing_bonus_known").fill_null(False),
        pl.col("high_school_draftee").fill_null(False),
    ).sort(["player_id", "origin_age_band", "origin_year"])


def _structure_features(
    rows: list[dict[str, object]], form: str, basis: np.ndarray
) -> np.ndarray:
    if form not in FORMS:
        raise ValueError(f"unsupported pitcher structure form: {form}")
    base = _features(rows, PITCHER_COMPONENTS, "component_development", basis)
    extra: list[list[float]] = []
    for row in rows:
        start_share = float(row["start_share"])
        coordinates = np.asarray(
            ilr_transform(_composition(row, PITCHER_COMPONENTS, "p_"), basis=basis)
        )
        values: list[float] = []
        if form in {
            "starter_history", "role_and_level", "role_and_pedigree", "all_structure"
        }:
            values.extend((start_share, start_share * start_share))
        if form in {"level_components", "role_and_level", "all_structure"}:
            level_flags = np.asarray(
                [float(row["level_group"] == level) for level in LEVELS[:-1]]
            )
            values.extend(np.outer(level_flags, coordinates).ravel().tolist())
            # KATOH found diminishing marginal value for very high AAA strikeout
            # rates. Test that single published nonlinearity without a broad search.
            values.append(
                float(row["p_so"]) ** 2 * float(row["level_group"] == "AAA")
            )
        if form in {"draft_pedigree", "role_and_pedigree", "all_structure"}:
            drafted = float(bool(row["rule4_drafted"]))
            pick = float(row["draft_pick_quality"])
            bonus_known = float(bool(row["signing_bonus_known"]))
            bonus = float(row["signing_bonus_percentile"])
            high_school = float(bool(row["high_school_draftee"]))
            age = float(row["age_years"])
            values.extend(
                (
                    drafted,
                    pick,
                    bonus_known,
                    bonus * bonus_known,
                    high_school * drafted,
                    (age - 21.0) * pick,
                )
            )
        extra.append(values)
    return np.column_stack((base, np.asarray(extra, dtype=float)))


def _fit(
    rows: list[dict[str, object]], form: str, alpha: float, basis: np.ndarray
) -> object:
    from sklearn.linear_model import Ridge
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    return make_pipeline(StandardScaler(), Ridge(alpha=alpha)).fit(
        _structure_features(rows, form, basis),
        _responses(rows, PITCHER_COMPONENTS, basis),
    )


def _predict(
    model: object, rows: list[dict[str, object]], form: str, basis: np.ndarray
) -> np.ndarray:
    delta = model.predict(_structure_features(rows, form, basis))
    predicted = []
    for index, row in enumerate(rows):
        current = np.asarray(
            ilr_transform(_composition(row, PITCHER_COMPONENTS, "p_"), basis=basis)
        )
        predicted.append(
            inverse_ilr_transform(current + delta[index], basis=basis)
        )
    return np.asarray(predicted)


def _scores(prediction: np.ndarray, rows: list[dict[str, object]]) -> dict[str, float | int]:
    player = _player_score(prediction, rows, PITCHER_COMPONENTS)
    event = _score(prediction, rows, PITCHER_COMPONENTS)
    return {
        "players": player["players"],
        "player_log_loss": player["log_loss"],
        "player_brier": player["brier"],
        "event_log_loss": event["log_loss"],
        "event_brier": event["brier"],
    }


def _delta(candidate: dict[str, float | int], baseline: dict[str, float | int]) -> dict[str, float]:
    return {
        key: float(candidate[key]) - float(baseline[key])
        for key in ("player_log_loss", "player_brier", "event_log_loss", "event_brier")
    }


def main() -> int:
    source = _pitcher_components(_load_sources("affiliated_pitching_components.parquet"))
    examples = pl.read_parquet(PEAK_ROOT / "tables" / "batters_faced_examples.parquet")
    examples = _attach_origin_role(examples, source)
    examples = _attach_origin_pedigree(
        examples,
        pl.read_parquet("reports/generated/draft-history/draft-history.parquet"),
    )
    basis = sequential_helmert_ilr_basis(len(PITCHER_COMPONENTS))

    train = examples.filter(pl.col("peak_window_end_year") <= 2014).to_dicts()
    development = examples.filter(
        pl.col("peak_window_end_year").is_between(2015, 2017, closed="both")
    ).to_dicts()
    baseline = _fit_peak(train, PITCHER_COMPONENTS, "component_development", 100.0, basis)
    baseline_dev = _scores(
        _baseline_predict(
            baseline, development, PITCHER_COMPONENTS, "component_development", basis
        ),
        development,
    )
    selection = []
    for form in FORMS:
        for alpha in ALPHAS:
            model = _fit(train, form, alpha, basis)
            candidate = _scores(_predict(model, development, form, basis), development)
            selection.append({"form": form, "alpha": alpha, **_delta(candidate, baseline_dev)})
    eligible = [row for row in selection if all(row[key] < 0 for key in (
        "player_log_loss", "player_brier", "event_log_loss", "event_brier"
    ))]
    selected = min(
        eligible or selection,
        key=lambda row: (row["player_log_loss"], row["player_brier"], row["alpha"]),
    )

    replay = []
    for end_year in (2018, 2019, 2023, 2024, 2025):
        target = examples.filter(pl.col("peak_window_end_year") == end_year).to_dicts()
        prior = examples.filter(pl.col("peak_window_end_year") < end_year).to_dicts()
        baseline_model = _fit_peak(
            prior, PITCHER_COMPONENTS, "component_development", 100.0, basis
        )
        candidate_model = _fit(
            prior, str(selected["form"]), float(selected["alpha"]), basis
        )
        baseline_prediction = _baseline_predict(
            baseline_model, target, PITCHER_COMPONENTS, "component_development", basis
        )
        candidate_prediction = _predict(
            candidate_model, target, str(selected["form"]), basis
        )
        baseline_score = _scores(baseline_prediction, target)
        candidate_score = _scores(candidate_prediction, target)
        replay.append({
            "peak_window_end_year": end_year,
            "candidate": candidate_score,
            "baseline": baseline_score,
            "delta": _delta(candidate_score, baseline_score),
            "uncertainty": _player_uncertainty(
                candidate_prediction, baseline_prediction, target, PITCHER_COMPONENTS
            ),
        })

    metrics = ("player_log_loss", "player_brier", "event_log_loss", "event_brier")
    wins = {metric: sum(row["delta"][metric] < 0 for row in replay) for metric in metrics}
    uncertainty_passes = sum(
        row["uncertainty"]["log_loss_delta_p975"] <= 0
        and row["uncertainty"]["brier_delta_p975"] <= 0
        for row in replay
    )
    gate = bool(eligible) and all(value >= 4 for value in wins.values()) and uncertainty_passes >= 4
    report = {
        "report_schema_version": "0.1",
        "question": (
            "Do starter history, level-specific components or objective Rule 4 draft "
            "pedigree improve pitcher peak talent?"
        ),
        "baseline": {"form": "component_development", "alpha": 100.0},
        "selection": selection,
        "selected": selected,
        "development_gate_passed": bool(eligible),
        "replay": replay,
        "wins": wins,
        "uncertainty_passes": uncertainty_passes,
        "promotion": "pass" if gate else "reject",
        "public_rank_or_fv_used": False,
        "arrival_or_future_workload_used": False,
        "current_partial_peak_window_used": False,
        "current_fit_rows": _completed_fit_examples(examples).height,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "selected": selected,
        "wins": wins,
        "uncertainty_passes": uncertainty_passes,
        "promotion": report["promotion"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
