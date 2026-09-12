#!/usr/bin/env python3
"""Turn frozen historical development fits into inspectable current talent paths."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import polars as pl

from audit_one_year_talent_development import (
    HITTER_COMPONENTS,
    PITCHER_COMPONENTS,
    _features,
)
from universal_baseball.hitter_v2_evaluation import (
    NEUTRAL_WOBA_SCALE,
    NEUTRAL_WOBA_WEIGHTS,
)
from universal_baseball.projection_composition import (
    ilr_transform,
    inverse_ilr_transform,
)
from universal_baseball.storage import write_canonical_parquet


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--basic-root",
        type=Path,
        default=Path("reports/generated/current-basic-talent/2026-09-08/tables"),
    )
    parser.add_argument(
        "--one-year-report",
        type=Path,
        default=Path("reports/generated/one-year-talent-development/report.json"),
    )
    parser.add_argument(
        "--two-year-report",
        type=Path,
        default=Path("reports/generated/two-year-talent-development/report.json"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/current-future-talent/2026-09-08"),
    )
    return parser.parse_args()


def _model_predict(
    frame: pl.DataFrame,
    components: tuple[str, ...],
    fit: dict[str, object],
) -> np.ndarray:
    rows = frame.to_dicts()
    basis = np.asarray(fit["ilr_basis"], dtype=float)
    if fit.get("feature_family") == "component_development_plus_one_year_trend":
        from audit_peak_talent_trend import _trend_features

        features = _trend_features(rows, components, str(fit["form"]), basis)
    else:
        features = _features(rows, components, str(fit["form"]), basis)
    mean = np.asarray(fit["scaler_mean"], dtype=float)
    scale = np.asarray(fit["scaler_scale"], dtype=float)
    coefficients = np.asarray(fit["ridge_coefficients"], dtype=float)
    intercept = np.asarray(fit["ridge_intercept"], dtype=float)
    delta = ((features - mean) / scale) @ coefficients.T + intercept
    output = []
    for index, row in enumerate(rows):
        current = np.asarray(
            ilr_transform(
                np.asarray([float(row[f"p_{name}"]) for name in components]),
                basis=basis,
            )
        )
        output.append(inverse_ilr_transform(current + delta[index], basis=basis))
    return np.asarray(output)


def _prepare(
    path: Path,
    components: tuple[str, ...],
    *,
    player_type: str,
) -> pl.DataFrame:
    frame = pl.read_parquet(path)
    rate_columns = [f"predicted_{name}_rate" for name in components]
    level_medians = frame.group_by("as_of_level_group").agg(
        pl.col("age_years").median().alias("level_median_age")
    )
    return (
        frame.join(level_medians, on="as_of_level_group", how="left")
        .with_columns(
            pl.col("as_of_level_group").alias("level_group"),
            pl.col("effective_evidence").alias("weighted_affiliated_exposure"),
            (pl.col("age_years") - pl.col("level_median_age")).alias(
                "age_relative_to_level"
            ),
            *(pl.col(column).alias(f"p_{name}") for column, name in zip(rate_columns, components)),
            pl.lit(player_type).alias("player_type"),
        )
    )


def _hitter_runs(
    probabilities: np.ndarray,
    present: np.ndarray,
    present_runs: np.ndarray,
) -> np.ndarray:
    weights = np.asarray([
        0.0,
        NEUTRAL_WOBA_WEIGHTS["UBB"],
        NEUTRAL_WOBA_WEIGHTS["HBP"],
        NEUTRAL_WOBA_WEIGHTS["1B"],
        NEUTRAL_WOBA_WEIGHTS["2B"],
        NEUTRAL_WOBA_WEIGHTS["3B"],
        NEUTRAL_WOBA_WEIGHTS["HR"],
        0.0,
    ])
    return present_runs + (probabilities - present) @ weights * 600.0 / NEUTRAL_WOBA_SCALE


def _pitcher_runs(
    probabilities: np.ndarray,
    present: np.ndarray,
    present_runs: np.ndarray,
) -> np.ndarray:
    # Preserve the same neutral run-value mapping already used by the present-rate table.
    weights = np.asarray([
        0.0,
        NEUTRAL_WOBA_WEIGHTS["UBB"],
        NEUTRAL_WOBA_WEIGHTS["HBP"],
        NEUTRAL_WOBA_WEIGHTS["HR"],
        0.0,
    ])
    known_present = present[:, 1:4] @ weights[1:4]
    implied_other_weight = np.divide(
        0.3188 - present_runs * NEUTRAL_WOBA_SCALE / 800.0 - known_present,
        present[:, 4],
        out=np.zeros_like(known_present),
        where=present[:, 4] > 0,
    )
    weights[4] = float(np.median(implied_other_weight[present[:, 4] > 0]))
    return present_runs - (probabilities - present) @ weights * 800.0 / NEUTRAL_WOBA_SCALE


def _materialize_type(
    frame: pl.DataFrame,
    components: tuple[str, ...],
    fits: list[tuple[int, dict[str, object]]],
    *,
    player_type: str,
) -> pl.DataFrame:
    present = frame.select([f"p_{name}" for name in components]).to_numpy()
    outputs = []
    for horizon, fit in fits:
        projected = _model_predict(frame, components, fit)
        if player_type == "hitter":
            mlb = frame.get_column("level_group").to_numpy() == "MLB"
            projected[mlb] = present[mlb]
            policy = np.where(
                mlb,
                "carry_forward_mlb_guardrail",
                str(fit["form"]),
            )
            present_runs = frame.get_column("present_offense_runs_per_600_pa").to_numpy()
            future_runs = _hitter_runs(projected, present, present_runs)
        else:
            policy = np.full(frame.height, str(fit["form"]), dtype=object)
            present_runs = frame.get_column("present_pitching_runs_per_800_bf").to_numpy()
            future_runs = _pitcher_runs(projected, present, present_runs)
        output = frame.select(
            "player_id",
            "player_name",
            "player_type",
            "as_of_level_group",
            "age_years",
            "effective_evidence",
            "reliability",
            "evidence_band",
            "ranking_status",
            *(
                column
                for column in ("external_rank_audit_only", "external_fv_audit_only")
                if column in frame.columns
            ),
        ).with_columns(
            pl.lit(horizon).alias("horizon_years"),
            pl.Series("present_runs_rate", present_runs),
            pl.Series("projected_runs_rate", future_runs),
            pl.Series("development_runs_change", future_runs - present_runs),
            pl.Series("development_policy", policy),
            *(pl.Series(f"present_{name}_rate", present[:, index]) for index, name in enumerate(components)),
            *(pl.Series(f"projected_{name}_rate", projected[:, index]) for index, name in enumerate(components)),
        )
        ranked = (
            output.filter(pl.col("ranking_status") == "ranked")
            .sort(
                ["projected_runs_rate", "effective_evidence", "player_id"],
                descending=[True, True, False],
            )
            .with_row_index("future_rate_rank", offset=1)
        )
        unresolved = output.filter(pl.col("ranking_status") != "ranked").with_columns(
            pl.lit(None, dtype=pl.UInt32).alias("future_rate_rank")
        )
        outputs.append(pl.concat([ranked, unresolved], how="diagonal_relaxed"))
    return pl.concat(outputs, how="vertical_relaxed")


def main() -> int:
    args = _args()
    reports = [
        (1, json.loads(args.one_year_report.read_text(encoding="utf-8"))),
        (2, json.loads(args.two_year_report.read_text(encoding="utf-8"))),
    ]
    hitters = _prepare(
        args.basic_root / "current_hitter_talent.parquet",
        HITTER_COMPONENTS,
        player_type="hitter",
    )
    pitchers = _prepare(
        args.basic_root / "current_pitcher_talent.parquet",
        PITCHER_COMPONENTS,
        player_type="pitcher",
    )
    hitter_output = _materialize_type(
        hitters,
        HITTER_COMPONENTS,
        [(horizon, report["hitters"]["current_fit"]) for horizon, report in reports],
        player_type="hitter",
    )
    pitcher_output = _materialize_type(
        pitchers,
        PITCHER_COMPONENTS,
        [(horizon, report["pitchers"]["current_fit"]) for horizon, report in reports],
        player_type="pitcher",
    )
    table_root = args.output_root / "tables"
    table_root.mkdir(parents=True, exist_ok=True)
    storage = {}
    for name, frame in (("hitters", hitter_output), ("pitchers", pitcher_output)):
        path = table_root / f"current_future_{name}.parquet"
        storage[name] = write_canonical_parquet(
            frame,
            path,
            table_name=f"current_future_{name}_talent",
        ).as_record()
        frame.write_csv(path.with_suffix(".csv"))
    report = {
        "report_schema_version": "0.1",
        "status": "diagnostic_near_term_rate_not_prospect_rank",
        "players": {"hitters": hitters.height, "pitchers": pitchers.height},
        "horizons": [1, 2],
        "hitter_mlb_guardrail": (
            "carry forward present rate because the development model did not retain "
            "broad proper-score support for MLB hitters"
        ),
        "promotion": (
            "rejected as universal talent rank; teenage players require a separate "
            "age-to-peak target"
        ),
        "excluded": [
            "playing time",
            "arrival probability",
            "position",
            "defense",
            "contracts",
            "public rank or FV as model input",
        ],
        "storage": storage,
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({key: report[key] for key in ("status", "players", "horizons")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
