#!/usr/bin/env python3
"""Summarize calibration stability across chronological Current Talent folds."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.performance_season import ALL_CORE_BINS


VARIANTS = {"fitted_translation", "zero_offset_translation"}
MODELS = {"baseline0", "baseline1"}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expected-fold-count", type=int, default=9)
    return parser.parse_args()


def _write_table(frame: pl.DataFrame, output_dir: Path, name: str) -> dict[str, object]:
    parquet = output_dir / f"{name}.parquet"
    csv = output_dir / f"{name}.csv"
    frame.write_parquet(parquet, compression="zstd")
    frame.write_csv(csv)
    return {
        "parquet": str(parquet),
        "csv": str(csv),
        "row_count": int(frame.height),
        "column_count": len(frame.columns),
    }


def _load_fold_metrics(input_root: Path) -> pl.DataFrame:
    coefficient_paths = sorted(input_root.rglob("calibration_coefficients.csv"))
    if not coefficient_paths:
        raise FileNotFoundError(f"no calibration coefficient tables found under {input_root}")

    frames: list[pl.DataFrame] = []
    for coefficient_path in coefficient_paths:
        variant = coefficient_path.parent.name
        cutoff = coefficient_path.parent.parent.name
        season_text = coefficient_path.parent.parent.parent.name
        if variant not in VARIANTS:
            continue
        try:
            season = int(season_text)
        except ValueError as exc:
            raise ValueError(
                f"cannot infer season from calibration path {coefficient_path}"
            ) from exc
        if not cutoff.startswith(f"{season}-"):
            raise ValueError(
                f"calibration path season/cutoff mismatch: season={season}, cutoff={cutoff}"
            )

        reliability_path = coefficient_path.parent / "calibration_summary.csv"
        if not reliability_path.exists():
            raise FileNotFoundError(
                f"missing reliability summary beside coefficients: {reliability_path}"
            )
        coefficients = pl.read_csv(coefficient_path)
        reliability = pl.read_csv(reliability_path).select(
            "model",
            "core_bin",
            pl.col("future_core_events").alias("reliability_future_core_events"),
            "event_weighted_expected_calibration_error",
            "max_bin_absolute_calibration_error",
            "occupied_calibration_bins",
        )
        joined = coefficients.join(reliability, on=["model", "core_bin"], how="inner")
        if joined.height != 2 * len(ALL_CORE_BINS):
            raise ValueError(
                "incomplete model/component calibration fold: "
                f"season={season}, cutoff={cutoff}, variant={variant}, rows={joined.height}"
            )
        if joined.filter(
            pl.col("future_core_events") != pl.col("reliability_future_core_events")
        ).height:
            raise ValueError(
                f"calibration exposure mismatch: season={season}, cutoff={cutoff}, variant={variant}"
            )
        if joined.filter(~pl.col("converged")).height:
            raise ValueError(
                f"nonconverged calibration coefficients: season={season}, cutoff={cutoff}, variant={variant}"
            )
        frames.append(
            joined.with_columns(
                pl.lit(season).cast(pl.Int64).alias("season"),
                pl.lit(cutoff).str.to_date().alias("as_of_date"),
                pl.lit(variant).alias("translation_variant"),
            ).drop("reliability_future_core_events")
        )

    result = pl.concat(frames, how="vertical_relaxed").sort(
        ["as_of_date", "translation_variant", "model", "core_bin"]
    )
    grain = ["season", "as_of_date", "translation_variant", "model", "core_bin"]
    duplicate = result.group_by(grain).len().filter(pl.col("len") != 1)
    if not duplicate.is_empty():
        raise ValueError("multi-fold calibration review violates fold/model/component grain")
    return result


def _validate_complete_grid(frame: pl.DataFrame, expected_fold_count: int) -> list[dict[str, object]]:
    folds = frame.select("season", "as_of_date").unique().sort(["season", "as_of_date"])
    if folds.height != expected_fold_count:
        raise ValueError(
            f"expected {expected_fold_count} calibration folds, observed {folds.height}: {folds.to_dicts()}"
        )
    for fold in folds.iter_rows(named=True):
        subset = frame.filter(
            (pl.col("season") == fold["season"])
            & (pl.col("as_of_date") == fold["as_of_date"])
        )
        if set(subset.get_column("translation_variant").unique().to_list()) != VARIANTS:
            raise ValueError(f"fold missing translation variant: {fold}")
        if set(subset.get_column("model").unique().to_list()) != MODELS:
            raise ValueError(f"fold missing baseline model: {fold}")
        for variant in VARIANTS:
            for model in MODELS:
                bins = set(
                    subset.filter(
                        (pl.col("translation_variant") == variant)
                        & (pl.col("model") == model)
                    ).get_column("core_bin").to_list()
                )
                if bins != set(ALL_CORE_BINS):
                    raise ValueError(
                        f"fold incomplete core profile: fold={fold}, variant={variant}, model={model}"
                    )
    return folds.to_dicts()


def _weighted_summaries(frame: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    weight = pl.col("future_core_events").cast(pl.Float64)
    component = (
        frame.group_by(["translation_variant", "model", "core_bin"])
        .agg(
            pl.len().cast(pl.Int64).alias("fold_count"),
            pl.col("future_core_events").sum().cast(pl.Int64).alias("summed_fold_component_exposure"),
            ((pl.col("calibration_intercept") * weight).sum() / weight.sum()).alias(
                "event_weighted_mean_intercept"
            ),
            ((pl.col("absolute_intercept_error") * weight).sum() / weight.sum()).alias(
                "event_weighted_mean_absolute_intercept_error"
            ),
            ((pl.col("calibration_slope") * weight).sum() / weight.sum()).alias(
                "event_weighted_mean_slope"
            ),
            ((pl.col("absolute_slope_error") * weight).sum() / weight.sum()).alias(
                "event_weighted_mean_absolute_slope_error"
            ),
            (
                (
                    pl.col("event_weighted_expected_calibration_error") * weight
                ).sum()
                / weight.sum()
            ).alias("event_weighted_mean_ece"),
            pl.col("absolute_intercept_error").max().alias("worst_absolute_intercept_error"),
            pl.col("absolute_slope_error").max().alias("worst_absolute_slope_error"),
            pl.col("event_weighted_expected_calibration_error").max().alias("worst_ece"),
            (pl.col("calibration_slope") < 1.0).sum().cast(pl.Int64).alias("slope_below_one_fold_count"),
            (pl.col("calibration_slope") > 1.0).sum().cast(pl.Int64).alias("slope_above_one_fold_count"),
        )
        .sort(["translation_variant", "model", "core_bin"])
    )
    overall = (
        frame.group_by(["translation_variant", "model"])
        .agg(
            pl.len().cast(pl.Int64).alias("fold_component_count"),
            ((pl.col("absolute_intercept_error") * weight).sum() / weight.sum()).alias(
                "event_weighted_mean_absolute_intercept_error"
            ),
            ((pl.col("absolute_slope_error") * weight).sum() / weight.sum()).alias(
                "event_weighted_mean_absolute_slope_error"
            ),
            (
                (
                    pl.col("event_weighted_expected_calibration_error") * weight
                ).sum()
                / weight.sum()
            ).alias("event_weighted_mean_ece"),
            pl.col("absolute_intercept_error").max().alias("worst_absolute_intercept_error"),
            pl.col("absolute_slope_error").max().alias("worst_absolute_slope_error"),
            pl.col("event_weighted_expected_calibration_error").max().alias("worst_ece"),
        )
        .sort(["translation_variant", "model"])
    )
    return component, overall


def _b1_vs_b0_comparison(frame: pl.DataFrame) -> pl.DataFrame:
    keys = ["season", "as_of_date", "translation_variant", "core_bin"]
    metrics = [
        "absolute_intercept_error",
        "absolute_slope_error",
        "event_weighted_expected_calibration_error",
    ]
    b0 = frame.filter(pl.col("model") == "baseline0").select(*keys, *metrics).rename(
        {metric: f"baseline0_{metric}" for metric in metrics}
    )
    b1 = frame.filter(pl.col("model") == "baseline1").select(*keys, *metrics).rename(
        {metric: f"baseline1_{metric}" for metric in metrics}
    )
    joined = b0.join(b1, on=keys, how="inner")
    if joined.height != b0.height or joined.height != b1.height:
        raise ValueError("B1-vs-B0 calibration comparison coverage mismatch")
    return joined.with_columns(
        *[
            (pl.col(f"baseline1_{metric}") - pl.col(f"baseline0_{metric}")).alias(
                f"baseline1_minus_baseline0_{metric}"
            )
            for metric in metrics
        ]
    ).sort(keys)


def _fitted_vs_zero_b1_comparison(frame: pl.DataFrame) -> pl.DataFrame:
    keys = ["season", "as_of_date", "model", "core_bin"]
    metrics = [
        "absolute_intercept_error",
        "absolute_slope_error",
        "event_weighted_expected_calibration_error",
    ]
    b1 = frame.filter(pl.col("model") == "baseline1")
    fitted = b1.filter(pl.col("translation_variant") == "fitted_translation").select(
        *keys, *metrics
    ).rename({metric: f"fitted_{metric}" for metric in metrics})
    zero = b1.filter(pl.col("translation_variant") == "zero_offset_translation").select(
        *keys, *metrics
    ).rename({metric: f"zero_{metric}" for metric in metrics})
    joined = fitted.join(zero, on=keys, how="inner")
    if joined.height != fitted.height or joined.height != zero.height:
        raise ValueError("fitted-vs-zero B1 calibration comparison coverage mismatch")
    return joined.with_columns(
        *[
            (pl.col(f"fitted_{metric}") - pl.col(f"zero_{metric}")).alias(
                f"fitted_minus_zero_{metric}"
            )
            for metric in metrics
        ]
    ).sort(keys)


def _comparison_summary(frame: pl.DataFrame, prefix: str) -> dict[str, object]:
    delta_columns = [column for column in frame.columns if column.startswith(prefix)]
    output: dict[str, object] = {"comparison_count": int(frame.height)}
    for column in delta_columns:
        values = frame.get_column(column)
        output[f"{column}_win_count"] = int((values < 0).sum())
        output[f"{column}_loss_count"] = int((values > 0).sum())
        output[f"{column}_tie_count"] = int((values == 0).sum())
        output[f"{column}_mean"] = float(values.mean() or 0.0)
    return output


def main() -> int:
    args = _parse_args()
    frame = _load_fold_metrics(args.input_root)
    folds = _validate_complete_grid(frame, int(args.expected_fold_count))
    component_summary, overall_summary = _weighted_summaries(frame)
    b1_vs_b0 = _b1_vs_b0_comparison(frame)
    fitted_vs_zero = _fitted_vs_zero_b1_comparison(frame)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "fold_component_metrics": _write_table(frame, args.output_dir, "fold_component_calibration_metrics"),
        "component_summary": _write_table(component_summary, args.output_dir, "component_calibration_summary"),
        "overall_summary": _write_table(overall_summary, args.output_dir, "overall_calibration_summary"),
        "b1_vs_b0": _write_table(b1_vs_b0, args.output_dir, "baseline1_vs_baseline0_calibration"),
        "fitted_vs_zero_b1": _write_table(
            fitted_vs_zero,
            args.output_dir,
            "baseline1_fitted_vs_zero_calibration",
        ),
    }

    report = {
        "report_schema_version": "0.1",
        "fold_count": len(folds),
        "folds": [
            {
                "season": int(row["season"]),
                "as_of_date": row["as_of_date"].isoformat(),
            }
            for row in folds
        ],
        "ideal_calibration": {"intercept": 0.0, "slope": 1.0},
        "overall_summary": overall_summary.to_dicts(),
        "baseline1_vs_baseline0": _comparison_summary(
            b1_vs_b0,
            "baseline1_minus_baseline0_",
        ),
        "baseline1_fitted_vs_zero_translation": _comparison_summary(
            fitted_vs_zero,
            "fitted_minus_zero_",
        ),
        "outputs": outputs,
        "interpretation": (
            "Calibration review only. Negative comparison deltas mean the first named variant is "
            "closer to ideal calibration. No coefficients are applied back to predictions and no "
            "hyperparameters are selected by this report."
        ),
    }
    (args.output_dir / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
