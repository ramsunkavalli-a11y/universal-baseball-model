#!/usr/bin/env python3
"""Test direct age-24-to-26 component talent from pre-24 evidence."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from audit_one_year_talent_development import (
    ALPHAS,
    FORMS,
    HITTER_COMPONENTS,
    PITCHER_COMPONENTS,
    _composition,
    _context,
    _features,
    _hitter_components,
    _load_sources,
    _paired_uncertainty,
    _pitcher_components,
    _predict,
    _responses,
    _score,
    _serialize_fitted_model,
)
from universal_baseball.level_component_translation import (
    build_translated_affiliated_profiles,
    fit_same_season_component_translation,
    translate_component_probabilities_to_mlb,
)
from universal_baseball.projection_composition import sequential_helmert_ilr_basis


ROOT = Path("reports/generated/age-to-peak-talent")
INVALID_PEAK_END_YEARS = {2020, 2021, 2022}
CURRENT_EVIDENCE_YEAR = 2026


def _completed_fit_examples(examples: pl.DataFrame) -> pl.DataFrame:
    return examples.filter(pl.col("peak_window_end_year") < CURRENT_EVIDENCE_YEAR)


def _fit_peak(
    rows: list[dict[str, object]],
    components: tuple[str, ...],
    form: str,
    alpha: float,
    basis: np.ndarray,
) -> object:
    return make_pipeline(StandardScaler(), Ridge(alpha=alpha)).fit(
        _features(rows, components, form, basis),
        _responses(rows, components, basis),
    )


def _player_score(
    predictions: np.ndarray,
    rows: list[dict[str, object]],
    components: tuple[str, ...],
) -> dict[str, float | int]:
    counts = np.asarray([
        [float(row[f"target_{component}"]) for component in components] for row in rows
    ])
    target = counts / counts.sum(axis=1)[:, None]
    return {
        "players": len(rows),
        "log_loss": float(
            np.mean(-(target * np.log(np.clip(predictions, 1e-12, 1.0))).sum(axis=1))
        ),
        "brier": float(
            np.mean(
                1.0
                - 2.0 * (target * predictions).sum(axis=1)
                + (predictions**2).sum(axis=1)
            )
        ),
    }


def _player_uncertainty(
    candidate: np.ndarray,
    baseline: np.ndarray,
    rows: list[dict[str, object]],
    components: tuple[str, ...],
    *,
    draws: int = 500,
) -> dict[str, object]:
    counts = np.asarray([
        [float(row[f"target_{component}"]) for component in components] for row in rows
    ])
    target = counts / counts.sum(axis=1)[:, None]
    candidate_log = -(target * np.log(np.clip(candidate, 1e-12, 1.0))).sum(axis=1)
    baseline_log = -(target * np.log(np.clip(baseline, 1e-12, 1.0))).sum(axis=1)
    candidate_brier = (
        1.0 - 2.0 * (target * candidate).sum(axis=1) + (candidate**2).sum(axis=1)
    )
    baseline_brier = (
        1.0 - 2.0 * (target * baseline).sum(axis=1) + (baseline**2).sum(axis=1)
    )
    rng = np.random.default_rng(20260912)
    log_draws = np.empty(draws)
    brier_draws = np.empty(draws)
    for draw in range(draws):
        indices = rng.integers(0, len(rows), size=len(rows))
        log_draws[draw] = np.mean(candidate_log[indices] - baseline_log[indices])
        brier_draws[draw] = np.mean(candidate_brier[indices] - baseline_brier[indices])
    return {
        "method": "paired equal-player bootstrap",
        "draws": draws,
        "log_loss_delta_p025": float(np.quantile(log_draws, 0.025)),
        "log_loss_delta_p975": float(np.quantile(log_draws, 0.975)),
        "brier_delta_p025": float(np.quantile(brier_draws, 0.025)),
        "brier_delta_p975": float(np.quantile(brier_draws, 0.975)),
    }


def _player_subgroups(
    candidate: np.ndarray,
    baseline: np.ndarray,
    rows: list[dict[str, object]],
    components: tuple[str, ...],
) -> list[dict[str, object]]:
    labels = {
        "level": [str(row["level_group"]) for row in rows],
        "age_band": [str(row["origin_age_band"]) for row in rows],
    }
    labels["level_age"] = [
        f"{level}|{age}"
        for level, age in zip(labels["level"], labels["age_band"])
    ]
    output = []
    for dimension, values in labels.items():
        value_array = np.asarray(values)
        for value in sorted(set(values)):
            indices = np.flatnonzero(value_array == value)
            if len(indices) < 50:
                continue
            subset_rows = [rows[int(index)] for index in indices]
            candidate_score = _player_score(
                candidate[indices], subset_rows, components
            )
            baseline_score = _player_score(
                baseline[indices], subset_rows, components
            )
            output.append({
                "dimension": dimension,
                "value": value,
                "players": len(indices),
                "log_loss_delta": (
                    candidate_score["log_loss"] - baseline_score["log_loss"]
                ),
                "brier_delta": (
                    candidate_score["brier"] - baseline_score["brier"]
                ),
            })
    return output


def _peak_target(
    source: pl.DataFrame,
    offsets: pl.DataFrame,
    *,
    origin: int,
    exposure: str,
    components: tuple[str, ...],
) -> pl.DataFrame:
    annual = (
        source.filter(
            (pl.col("season") > origin)
            & (pl.col("season") != 2020)
            & pl.col("reported_age").is_between(24, 26, closed="both")
            & (pl.col(exposure) > 0)
        )
        .group_by("player_id", "season", "reported_age", "level_group")
        .agg(
            pl.col(exposure).sum().alias(exposure),
            *(pl.col(component).sum().alias(component) for component in components),
        )
    )
    rows: list[dict[str, object]] = []
    for row in annual.iter_rows(named=True):
        amount = float(row[exposure])
        raw = {
            component: (float(row[component]) + 0.5) / (amount + 0.5 * len(components))
            for component in components
        }
        translated = translate_component_probabilities_to_mlb(
            raw,
            level_group=str(row["level_group"]),
            offsets=offsets,
        )
        rows.append({
            "player_id": int(row["player_id"]),
            "target_season": int(row["season"]),
            "target_age": float(row["reported_age"]),
            "target_exposure_part": amount,
            **{
                f"target_{component}": amount * translated[component]
                for component in components
            },
        })
    if not rows:
        return pl.DataFrame()
    return (
        pl.DataFrame(rows)
        .group_by("player_id")
        .agg(
            pl.col("target_exposure_part").sum().alias("target_exposure"),
            pl.col("target_age").n_unique().alias("target_age_count"),
            pl.col("target_age").max().alias("target_max_age"),
            pl.col("target_season").max().alias("peak_window_end_year"),
            *(pl.col(f"target_{component}").sum() for component in components),
        )
        .filter(
            (pl.col("target_exposure") >= 150)
            & (pl.col("target_age_count") >= 2)
            & (pl.col("target_max_age") >= 26)
            & ~pl.col("peak_window_end_year").is_in(INVALID_PEAK_END_YEARS)
        )
    )


def _origin_fold(
    source: pl.DataFrame,
    *,
    origin: int,
    exposure: str,
    components: tuple[str, ...],
    regression: float,
) -> pl.DataFrame:
    completed = tuple(
        year
        for year in range(int(source.get_column("season").min()), origin + 1)
        if year != 2020
    )
    offsets = fit_same_season_component_translation(
        source,
        exposure_column=exposure,
        component_columns=components,
        completed_seasons=completed,
        minimum_level_exposure=30,
    ).offsets
    context = _context(source, origin, exposure).filter(
        pl.col("age_years").is_between(16, 23, closed="both")
    )
    profiles = build_translated_affiliated_profiles(
        context.select("player_id"),
        source.filter(pl.col("season") != 2020),
        offsets,
        exposure_column=exposure,
        component_columns=components,
        current_season=origin,
        reference_season=origin,
        regression_exposure=regression,
    )
    target = _peak_target(
        source,
        offsets,
        origin=origin,
        exposure=exposure,
        components=components,
    )
    if target.is_empty():
        return target
    return (
        profiles.join(context, on="player_id", how="inner")
        .join(target, on="player_id", how="inner")
        .with_columns(
            pl.lit(origin).alias("origin_year"),
            pl.when(pl.col("age_years") < 20)
            .then(pl.lit("under_20"))
            .when(pl.col("age_years") < 22)
            .then(pl.lit("20_to_21"))
            .otherwise(pl.lit("22_to_23"))
            .alias("origin_age_band"),
        )
    )


def _build_examples(
    source: pl.DataFrame,
    *,
    exposure: str,
    components: tuple[str, ...],
    regression: float,
) -> pl.DataFrame:
    cache = ROOT / "tables" / f"{exposure}_examples.parquet"
    if cache.exists():
        cached = pl.read_parquet(cache)
        required = {
            *(f"p_{component}" for component in components),
            *(f"target_{component}" for component in components),
        }
        if required.issubset(cached.columns):
            return cached
    frames = [
        _origin_fold(
            source,
            origin=origin,
            exposure=exposure,
            components=components,
            regression=regression,
        )
        for origin in range(2005, 2023)
        if origin != 2020
    ]
    result = (
        pl.concat([frame for frame in frames if not frame.is_empty()], how="vertical_relaxed")
        .sort(["player_id", "origin_age_band", "origin_year"])
        .unique(["player_id", "origin_age_band"], keep="last")
    )
    cache.parent.mkdir(parents=True, exist_ok=True)
    result.write_parquet(cache)
    return result


def _evaluate(
    examples: pl.DataFrame,
    components: tuple[str, ...],
    *,
    player_type: str,
) -> dict[str, object]:
    basis = sequential_helmert_ilr_basis(len(components))
    train = examples.filter(pl.col("peak_window_end_year") <= 2014).to_dicts()
    development = examples.filter(
        pl.col("peak_window_end_year").is_between(2015, 2017, closed="both")
    ).to_dicts()
    selection = []
    for form in FORMS:
        for alpha in ALPHAS:
            model = _fit_peak(train, components, form, alpha, basis)
            candidate_predictions = _predict(
                model, development, components, form, basis
            )
            baseline_predictions = np.asarray([
                _composition(row, components, "p_") for row in development
            ])
            candidate = _player_score(
                candidate_predictions, development, components
            )
            baseline = _player_score(
                baseline_predictions, development, components
            )
            candidate_event = _score(candidate_predictions, development, components)
            baseline_event = _score(baseline_predictions, development, components)
            selection.append({
                "form": form,
                "alpha": alpha,
                "log_loss_delta": candidate["log_loss"] - baseline["log_loss"],
                "brier_delta": candidate["brier"] - baseline["brier"],
                "event_log_loss_delta": (
                    candidate_event["log_loss"] - baseline_event["log_loss"]
                ),
                "event_brier_delta": (
                    candidate_event["brier"] - baseline_event["brier"]
                ),
            })
    eligible = [
        row
        for row in selection
        if row["log_loss_delta"] < 0
        and row["brier_delta"] < 0
        and row["event_log_loss_delta"] <= 0
        and row["event_brier_delta"] <= 0
    ]
    selected = min(
        eligible or selection,
        key=lambda row: (row["log_loss_delta"], row["brier_delta"], row["alpha"]),
    )
    replay = []
    for end_year in (2018, 2019, 2023, 2024, 2025):
        target_rows = examples.filter(pl.col("peak_window_end_year") == end_year).to_dicts()
        prior_rows = examples.filter(pl.col("peak_window_end_year") < end_year).to_dicts()
        model = _fit_peak(
            prior_rows,
            components,
            str(selected["form"]),
            float(selected["alpha"]),
            basis,
        )
        candidate_predictions = _predict(
            model,
            target_rows,
            components,
            str(selected["form"]),
            basis,
        )
        baseline_predictions = np.asarray([
            _composition(row, components, "p_") for row in target_rows
        ])
        candidate = _player_score(candidate_predictions, target_rows, components)
        baseline = _player_score(baseline_predictions, target_rows, components)
        candidate_event = _score(candidate_predictions, target_rows, components)
        baseline_event = _score(baseline_predictions, target_rows, components)
        replay.append({
            "peak_window_end_year": end_year,
            "guardrail_players": 0,
            "candidate": candidate,
            "carry_forward": baseline,
            "log_loss_delta": candidate["log_loss"] - baseline["log_loss"],
            "brier_delta": candidate["brier"] - baseline["brier"],
            "event_log_loss_delta": (
                candidate_event["log_loss"] - baseline_event["log_loss"]
            ),
            "event_brier_delta": (
                candidate_event["brier"] - baseline_event["brier"]
            ),
            "uncertainty": _player_uncertainty(
                candidate_predictions,
                baseline_predictions,
                target_rows,
                components,
            ),
            "event_uncertainty": _paired_uncertainty(
                candidate_predictions,
                baseline_predictions,
                target_rows,
                components,
            ),
            "subgroups": _player_subgroups(
                candidate_predictions,
                baseline_predictions,
                target_rows,
                components,
            ),
        })
    # The active season is current evidence only. Never let its incomplete peak
    # window enter the fit used to score that same season's players.
    final_rows = _completed_fit_examples(examples).to_dicts()
    final_model = _fit_peak(
        final_rows,
        components,
        str(selected["form"]),
        float(selected["alpha"]),
        basis,
    )
    age_level_model = _fit_peak(
        final_rows,
        components,
        "age_level",
        100.0,
        basis,
    )
    log_wins = sum(row["log_loss_delta"] < 0 for row in replay)
    brier_wins = sum(row["brier_delta"] < 0 for row in replay)
    event_log_wins = sum(row["event_log_loss_delta"] < 0 for row in replay)
    event_brier_wins = sum(row["event_brier_delta"] < 0 for row in replay)
    uncertainty_passes = sum(
        row["uncertainty"]["log_loss_delta_p975"] <= 0
        and row["uncertainty"]["brier_delta_p975"] <= 0
        for row in replay
    )
    gate_passed = (
        bool(eligible)
        and log_wins >= 4
        and brier_wins >= 4
        and event_log_wins >= 4
        and event_brier_wins >= 4
        and uncertainty_passes >= 4
    )
    if gate_passed:
        promotion = "pass"
    else:
        promotion = "reject"
    return {
        "examples": examples.height,
        "players": examples.get_column("player_id").n_unique(),
        "selection": selection,
        "development_selection_gate_passed": bool(eligible),
        "selected": selected,
        "replay": replay,
        "log_loss_wins": log_wins,
        "brier_wins": brier_wins,
        "event_log_loss_wins": event_log_wins,
        "event_brier_wins": event_brier_wins,
        "uncertainty_passes": uncertainty_passes,
        "promotion": promotion,
        "guardrail": None,
        "current_fit_max_peak_window_end_year": CURRENT_EVIDENCE_YEAR - 1,
        "current_fit": _serialize_fitted_model(
            final_model,
            form=str(selected["form"]),
            alpha=float(selected["alpha"]),
            basis=basis,
            training_rows=len(final_rows),
            training_origins=sorted(set(row["origin_year"] for row in final_rows)),
        ),
        "age_level_current_fit": _serialize_fitted_model(
            age_level_model,
            form="age_level",
            alpha=100.0,
            basis=basis,
            training_rows=len(final_rows),
            training_origins=sorted(set(row["origin_year"] for row in final_rows)),
        ),
    }


def main() -> int:
    hitters = _build_examples(
        _hitter_components(_load_sources("affiliated_hitting_components.parquet")),
        exposure="plate_appearances",
        components=HITTER_COMPONENTS,
        regression=1200.0,
    )
    pitchers = _build_examples(
        _pitcher_components(_load_sources("affiliated_pitching_components.parquet")),
        exposure="batters_faced",
        components=PITCHER_COMPONENTS,
        regression=800.0,
    )
    report = {
        "report_schema_version": "0.1",
        "status": "historical_peak_rate_research",
        "target": "translated aggregate component rates at reported ages 24 through 26",
        "minimum_target_exposure": 150,
        "minimum_target_ages": 2,
        "one_snapshot_per_player_age_band": True,
        "public_rank_or_fv_used": False,
        "playing_time_or_arrival_used": False,
        "hitters": _evaluate(hitters, HITTER_COMPONENTS, player_type="hitter"),
        "pitchers": _evaluate(pitchers, PITCHER_COMPONENTS, player_type="pitcher"),
    }
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        player_type: {
            key: report[player_type][key]
            for key in ("examples", "players", "selected", "log_loss_wins", "brier_wins", "uncertainty_passes")
        }
        for player_type in ("hitters", "pitchers")
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
