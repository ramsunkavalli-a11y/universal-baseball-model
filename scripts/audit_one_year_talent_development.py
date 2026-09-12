#!/usr/bin/env python3
"""Chronologically test one-year hitter and pitcher component development."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from universal_baseball.level_component_translation import (
    LEVEL_ORDER,
    build_translated_affiliated_profiles,
    fit_same_season_component_translation,
    translate_component_probabilities_to_mlb,
)
from universal_baseball.projection_composition import (
    ilr_transform,
    inverse_ilr_transform,
    sequential_helmert_ilr_basis,
)


ROOT = Path("reports/generated")
OUTPUT = ROOT / "one-year-talent-development"
HITTER_COMPONENTS = ("ubb", "hbp", "single", "double", "triple", "hr", "other")
PITCHER_COMPONENTS = ("so", "ubb", "hbp", "hr", "other")
LEVELS = tuple(LEVEL_ORDER)
ALPHAS = (1.0, 10.0, 100.0, 1000.0)
FORMS = ("age_level", "component_development")
TRAIN_MAX_ORIGIN = 2014
DEVELOPMENT_ORIGINS = (2015, 2016, 2017)
REPLAY_ORIGINS = (2018, 2021, 2022, 2023, 2024)
INVALID_TARGET_YEARS = {2020}


def _load_sources(name: str) -> pl.DataFrame:
    paths = (
        ROOT / "affiliated-skill-source-2003-2007" / "tables" / name,
        ROOT / "affiliated-skill-source-2008-2017" / "tables" / name,
        ROOT / "affiliated-skill-source-2018-2022" / "tables" / name,
        ROOT / "affiliated-skill-source" / "tables" / name,
    )
    frames = [pl.read_parquet(path) for path in paths]
    result = pl.concat(frames, how="vertical_relaxed").sort(
        ["season", "player_id", "sport_id", "team_id"]
    )
    if result.group_by(["season", "player_id", "sport_id", "team_id"]).len().filter(
        pl.col("len") > 1
    ).height:
        raise ValueError("combined affiliated source contains duplicate canonical rows")
    return result


def _hitter_components(frame: pl.DataFrame) -> pl.DataFrame:
    return frame.with_columns(
        (pl.col("base_on_balls") - pl.col("intentional_walks")).alias("ubb"),
        (pl.col("hits") - pl.col("doubles") - pl.col("triples") - pl.col("home_runs")).alias("single"),
        pl.col("doubles").alias("double"),
        pl.col("triples").alias("triple"),
        pl.col("home_runs").alias("hr"),
        pl.col("hit_by_pitch").alias("hbp"),
    ).with_columns(
        (pl.col("plate_appearances") - pl.sum_horizontal(*HITTER_COMPONENTS[:-1])).alias("other")
    )


def _pitcher_components(frame: pl.DataFrame) -> pl.DataFrame:
    return frame.with_columns(
        pl.col("strike_outs").alias("so"),
        (pl.col("base_on_balls") - pl.col("intentional_walks")).alias("ubb"),
        pl.col("hit_batters").alias("hbp"),
        pl.col("home_runs").alias("hr"),
    ).with_columns(
        (pl.col("batters_faced") - pl.sum_horizontal(*PITCHER_COMPONENTS[:-1])).alias("other")
    )


def _context(source: pl.DataFrame, origin: int, exposure: str) -> pl.DataFrame:
    current = source.filter((pl.col("season") == origin) & (pl.col(exposure) > 0)).with_columns(
        pl.col("level_group").replace_strict(LEVEL_ORDER, return_dtype=pl.Int64).alias("level_order")
    )
    grouped = current.group_by("player_id").agg(
        pl.col("level_order").max().alias("level_order"),
        pl.col("reported_age").drop_nulls().median().alias("age_years"),
        pl.col(exposure).sum().alias("origin_raw_exposure"),
    ).with_columns(
        pl.col("level_order").replace_strict(
            {value: key for key, value in LEVEL_ORDER.items()}, return_dtype=pl.String
        ).alias("level_group")
    )
    medians = grouped.group_by("level_group").agg(
        pl.col("age_years").median().alias("level_median_age")
    )
    return grouped.join(medians, on="level_group", how="left").with_columns(
        (pl.col("age_years") - pl.col("level_median_age")).alias("age_relative_to_level")
    )


def _annual_translated_target(
    source: pl.DataFrame,
    offsets: pl.DataFrame,
    *,
    target_year: int,
    exposure: str,
    components: tuple[str, ...],
) -> pl.DataFrame:
    annual = source.filter((pl.col("season") == target_year) & (pl.col(exposure) > 0)).group_by(
        "player_id", "level_group"
    ).agg(
        pl.col(exposure).sum().alias(exposure),
        *(pl.col(component).sum().alias(component) for component in components),
    )
    rows: list[dict[str, object]] = []
    for row in annual.iter_rows(named=True):
        amount = float(row[exposure])
        raw = {
            component: (float(row[component]) + 0.5) / (amount + 0.5 * len(components))
            for component in components
        }
        translated = translate_component_probabilities_to_mlb(
            raw, level_group=str(row["level_group"]), offsets=offsets
        )
        rows.append({
            "player_id": int(row["player_id"]),
            "target_exposure_part": amount,
            **{f"target_{component}": amount * translated[component] for component in components},
        })
    return pl.DataFrame(rows).group_by("player_id").agg(
        pl.col("target_exposure_part").sum().alias("target_exposure"),
        *(pl.col(f"target_{component}").sum() for component in components),
    ).filter(pl.col("target_exposure") >= 50)


def _fold(
    source: pl.DataFrame,
    *,
    origin: int,
    exposure: str,
    components: tuple[str, ...],
    regression: float,
) -> pl.DataFrame:
    target_year = origin + 1
    if target_year in INVALID_TARGET_YEARS:
        return pl.DataFrame()
    completed = tuple(
        value for value in range(int(source.get_column("season").min()), origin + 1) if value != 2020
    )
    offsets = fit_same_season_component_translation(
        source,
        exposure_column=exposure,
        component_columns=components,
        completed_seasons=completed,
        minimum_level_exposure=30,
    ).offsets
    context = _context(source, origin, exposure)
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
    target = _annual_translated_target(
        source,
        offsets,
        target_year=target_year,
        exposure=exposure,
        components=components,
    )
    joined = profiles.join(context, on="player_id", how="inner").join(
        target, on="player_id", how="inner"
    )
    return joined.with_columns(
        pl.lit(origin).alias("origin_year"),
        pl.lit(target_year).alias("target_year"),
    )


def _composition(row: dict[str, object], components: tuple[str, ...], prefix: str) -> np.ndarray:
    return np.asarray([float(row[f"{prefix}{component}"]) for component in components])


def _features(
    rows: list[dict[str, object]],
    components: tuple[str, ...],
    form: str,
    basis: np.ndarray,
) -> np.ndarray:
    output = []
    for row in rows:
        age = float(row["age_years"] if row["age_years"] is not None else 24.0)
        relative = float(
            row["age_relative_to_level"] if row["age_relative_to_level"] is not None else 0.0
        )
        evidence = float(row["weighted_affiliated_exposure"])
        base = [
            age - 24.0,
            max(0.0, age - 20.0),
            max(0.0, age - 24.0),
            max(0.0, age - 28.0),
            relative,
            math.log1p(evidence),
            *(1.0 if row["level_group"] == level else 0.0 for level in LEVELS[:-1]),
        ]
        if form == "component_development":
            coordinates = np.asarray(
                ilr_transform(_composition(row, components, "p_"), basis=basis)
            )
            base.extend(coordinates.tolist())
            base.extend((coordinates * relative).tolist())
        output.append(base)
    return np.asarray(output, dtype=float)


def _responses(
    rows: list[dict[str, object]],
    components: tuple[str, ...],
    basis: np.ndarray,
) -> np.ndarray:
    response = []
    for row in rows:
        current = np.asarray(
            ilr_transform(_composition(row, components, "p_"), basis=basis)
        )
        target = _composition(row, components, "target_") / float(row["target_exposure"])
        response.append(np.asarray(ilr_transform(target, basis=basis)) - current)
    return np.asarray(response)


def _predict(
    model: object,
    rows: list[dict[str, object]],
    components: tuple[str, ...],
    form: str,
    basis: np.ndarray,
) -> np.ndarray:
    delta = model.predict(_features(rows, components, form, basis))
    predicted = []
    for index, row in enumerate(rows):
        current = np.asarray(
            ilr_transform(_composition(row, components, "p_"), basis=basis)
        )
        predicted.append(inverse_ilr_transform(current + delta[index], basis=basis))
    return np.asarray(predicted)


def _score(
    predictions: np.ndarray,
    rows: list[dict[str, object]],
    components: tuple[str, ...],
) -> dict[str, float | int]:
    counts = np.asarray([
        [float(row[f"target_{component}"]) for component in components] for row in rows
    ])
    exposure = counts.sum(axis=1)
    probabilities = counts / exposure[:, None]
    total = float(exposure.sum())
    log_loss = -float((counts * np.log(np.clip(predictions, 1e-12, 1.0))).sum()) / total
    brier = float((exposure * (1.0 - 2.0 * (probabilities * predictions).sum(axis=1) + (predictions**2).sum(axis=1))).sum()) / total
    return {
        "players": len(rows),
        "target_exposure": int(round(total)),
        "log_loss": log_loss,
        "brier": brier,
    }


def _fit(
    rows: list[dict[str, object]],
    components: tuple[str, ...],
    form: str,
    alpha: float,
    basis: np.ndarray,
) -> object:
    weights = np.sqrt(np.minimum(
        np.asarray([float(row["target_exposure"]) for row in rows]),
        600.0 if len(components) == 7 else 800.0,
    ))
    return make_pipeline(StandardScaler(), Ridge(alpha=alpha)).fit(
        _features(rows, components, form, basis),
        _responses(rows, components, basis),
        ridge__sample_weight=weights,
    )


def _evaluate_player_type(
    source: pl.DataFrame,
    *,
    exposure: str,
    components: tuple[str, ...],
    regression: float,
) -> dict[str, object]:
    origins = tuple(range(2005, 2025))
    folds = {
        origin: _fold(
            source,
            origin=origin,
            exposure=exposure,
            components=components,
            regression=regression,
        )
        for origin in origins
        if origin not in INVALID_TARGET_YEARS and origin + 1 not in INVALID_TARGET_YEARS
    }
    basis = sequential_helmert_ilr_basis(len(components))
    training = pl.concat(
        [frame for origin, frame in folds.items() if origin <= TRAIN_MAX_ORIGIN],
        how="vertical_relaxed",
    ).to_dicts()
    selection = []
    for form in FORMS:
        for alpha in ALPHAS:
            model = _fit(training, components, form, alpha, basis)
            dev_rows = pl.concat([folds[origin] for origin in DEVELOPMENT_ORIGINS]).to_dicts()
            candidate = _score(_predict(model, dev_rows, components, form, basis), dev_rows, components)
            baseline = _score(
                np.asarray([_composition(row, components, "p_") for row in dev_rows]),
                dev_rows,
                components,
            )
            selection.append({
                "form": form,
                "alpha": alpha,
                "candidate": candidate,
                "carry_forward": baseline,
                "log_loss_delta": float(candidate["log_loss"]) - float(baseline["log_loss"]),
                "brier_delta": float(candidate["brier"]) - float(baseline["brier"]),
            })
    eligible = [row for row in selection if row["brier_delta"] < 0]
    selected = min(eligible or selection, key=lambda row: (row["log_loss_delta"], row["brier_delta"], row["alpha"]))
    simple_selection = min(
        (row for row in selection if row["form"] == "age_level"),
        key=lambda row: (row["log_loss_delta"], row["brier_delta"], row["alpha"]),
    )

    replay = []
    for origin in REPLAY_ORIGINS:
        train_rows = pl.concat(
            [frame for fold_origin, frame in folds.items() if fold_origin + 1 <= origin],
            how="vertical_relaxed",
        ).to_dicts()
        target_rows = folds[origin].to_dicts()
        model = _fit(
            train_rows,
            components,
            str(selected["form"]),
            float(selected["alpha"]),
            basis,
        )
        simple_model = _fit(
            train_rows,
            components,
            "age_level",
            float(simple_selection["alpha"]),
            basis,
        )
        candidate = _score(
            _predict(model, target_rows, components, str(selected["form"]), basis),
            target_rows,
            components,
        )
        simple = _score(
            _predict(simple_model, target_rows, components, "age_level", basis),
            target_rows,
            components,
        )
        baseline = _score(
            np.asarray([_composition(row, components, "p_") for row in target_rows]),
            target_rows,
            components,
        )
        replay.append({
            "origin_year": origin,
            "target_year": origin + 1,
            "candidate": candidate,
            "age_level_comparator": simple,
            "carry_forward": baseline,
            "log_loss_delta": float(candidate["log_loss"]) - float(baseline["log_loss"]),
            "brier_delta": float(candidate["brier"]) - float(baseline["brier"]),
            "rich_minus_simple_log_loss": (
                float(candidate["log_loss"]) - float(simple["log_loss"])
            ),
            "rich_minus_simple_brier": (
                float(candidate["brier"]) - float(simple["brier"])
            ),
        })
    rich_log_wins = sum(row["rich_minus_simple_log_loss"] < 0 for row in replay)
    rich_brier_wins = sum(row["rich_minus_simple_brier"] < 0 for row in replay)
    selected_form = str(selected["form"])
    if selected_form == "component_development" and (
        rich_log_wins < 4 or rich_brier_wins < 4
    ):
        decision = {
            "form": "age_level",
            "alpha": simple_selection["alpha"],
            "reason": "richer form did not beat the simpler form in at least four of five replay folds on both scores",
        }
    else:
        decision = {
            "form": selected_form,
            "alpha": selected["alpha"],
            "reason": "selected development form retained broad replay support",
        }
    return {
        "training_origins": [origin for origin in folds if origin <= TRAIN_MAX_ORIGIN],
        "development_origins": list(DEVELOPMENT_ORIGINS),
        "replay_origins": list(REPLAY_ORIGINS),
        "selection": selection,
        "selected": {"form": selected["form"], "alpha": selected["alpha"]},
        "simple_comparator": {
            "form": "age_level",
            "alpha": simple_selection["alpha"],
        },
        "research_decision": decision,
        "replay": replay,
        "replay_log_loss_wins": sum(row["log_loss_delta"] < 0 for row in replay),
        "replay_brier_wins": sum(row["brier_delta"] < 0 for row in replay),
        "rich_vs_simple_log_loss_wins": rich_log_wins,
        "rich_vs_simple_brier_wins": rich_brier_wins,
    }


def main() -> int:
    hitters = _hitter_components(_load_sources("affiliated_hitting_components.parquet"))
    pitchers = _pitcher_components(_load_sources("affiliated_pitching_components.parquet"))
    report = {
        "report_schema_version": "0.1",
        "status": "historical_replay_not_current_ranking",
        "question": "Can age, level, evidence and present components improve one-year future talent over carry-forward?",
        "rules": {
            "playing_time_used_as_feature": False,
            "public_rank_or_fv_used": False,
            "organization_used": False,
            "target": "next-year translated component rate at any affiliated level",
            "missing_future_season_treatment": "reported missing; not scored as bad talent",
            "translation_fit": "same-player same-season movers through each historical origin only",
            "2020": "excluded because the affiliated minor-league season did not exist",
        },
        "hitters": _evaluate_player_type(
            hitters,
            exposure="plate_appearances",
            components=HITTER_COMPONENTS,
            regression=1200.0,
        ),
        "pitchers": _evaluate_player_type(
            pitchers,
            exposure="batters_faced",
            components=PITCHER_COMPONENTS,
            regression=800.0,
        ),
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        player_type: {
            "selected": report[player_type]["selected"],
            "decision": report[player_type]["research_decision"],
            "log_loss_wins": report[player_type]["replay_log_loss_wins"],
            "brier_wins": report[player_type]["replay_brier_wins"],
            "replay": [
                {
                    "target_year": row["target_year"],
                    "log_loss_delta": row["log_loss_delta"],
                    "brier_delta": row["brier_delta"],
                    "rich_minus_simple_log_loss": row["rich_minus_simple_log_loss"],
                    "rich_minus_simple_brier": row["rich_minus_simple_brier"],
                }
                for row in report[player_type]["replay"]
            ],
        }
        for player_type in ("hitters", "pitchers")
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
