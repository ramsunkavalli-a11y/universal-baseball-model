#!/usr/bin/env python3
"""Compare fitted level translation with a controlled zero-offset ablation."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import polars as pl

from materialize_current_talent_baseline_validation import (
    _load_universal_evidence,
    _write_table,
)
from universal_baseball.certification import download_file
from universal_baseball.chadwick import (
    CHADWICK_ARCHIVE_URL,
    CHADWICK_SNAPSHOT_SHA,
    build_mlbam_age_as_of,
    read_chadwick_people_archive,
)
from universal_baseball.current_talent_ablation import (
    FITTED_TRANSLATION_VARIANT,
    ZERO_TRANSLATION_VARIANT,
    build_baseline_validation_variant,
    zero_translation_offsets,
)
from universal_baseball.current_talent_evidence import EvidenceWindow
from universal_baseball.current_talent_translation import (
    build_training_environment_transition_evidence,
    fit_level_clr_translation,
)
from universal_baseball.current_talent_validation_dataset import (
    build_validation_snapshot_dataset,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--mlb-input-root", type=Path, required=True)
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--as-of-date", required=True)
    parser.add_argument("--half-life-days", type=float, default=90.0)
    parser.add_argument("--prior-strength-core-events", type=float, default=100.0)
    parser.add_argument("--age-band-width-years", type=float, default=2.0)
    parser.add_argument("--min-age-level-peers", type=int, default=12)
    parser.add_argument("--min-core-events-per-stint", type=int, default=20)
    parser.add_argument("--max-gap-days", type=int, default=365)
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("data/quarantine/current-talent-translation-ablation"),
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def _metric_lookup(frame: pl.DataFrame) -> dict[str, dict[str, object]]:
    return {
        str(row["model"]): dict(row)
        for row in frame.iter_rows(named=True)
    }


def _variant_tables(variant, output_dir: Path) -> dict[str, object]:
    variant_dir = output_dir / variant.variant
    variant_dir.mkdir(parents=True, exist_ok=True)
    return {
        "offsets": _write_table(variant.offsets, variant_dir, "translation_offsets"),
        "baseline_profiles": _write_table(
            variant.baselines.profile,
            variant_dir,
            "baseline_profiles",
        ),
        "projected_target_profile": _write_table(
            variant.score_report.projected_profile,
            variant_dir,
            "projected_target_profile",
        ),
        "environment_scores": _write_table(
            variant.score_report.environment_scores,
            variant_dir,
            "environment_scores",
        ),
        "aggregate_metrics": _write_table(
            variant.score_report.aggregate_metrics,
            variant_dir,
            "aggregate_metrics",
        ),
        "separate_stratified_metrics": _write_table(
            variant.separate_stratified_metrics,
            variant_dir,
            "separate_stratified_metrics",
        ),
        "component_scores": _write_table(
            variant.component_scores,
            variant_dir,
            "component_scores",
        ),
        "calibration_summary": _write_table(
            variant.calibration_summary,
            variant_dir,
            "calibration_summary",
        ),
    }


def _build_aggregate_comparison(fitted, zero) -> pl.DataFrame:
    fitted_metrics = fitted.score_report.aggregate_metrics.with_columns(
        pl.lit(FITTED_TRANSLATION_VARIANT).alias("translation_variant")
    )
    zero_metrics = zero.score_report.aggregate_metrics.with_columns(
        pl.lit(ZERO_TRANSLATION_VARIANT).alias("translation_variant")
    )
    combined = pl.concat([fitted_metrics, zero_metrics], how="vertical_relaxed")

    rows: list[dict[str, object]] = []
    fitted_lookup = _metric_lookup(fitted.score_report.aggregate_metrics)
    zero_lookup = _metric_lookup(zero.score_report.aggregate_metrics)
    if set(fitted_lookup) != set(zero_lookup):
        raise ValueError("translation ablation variants do not expose the same model set")
    for model in sorted(fitted_lookup):
        f = fitted_lookup[model]
        z = zero_lookup[model]
        if int(f["future_core_events"]) != int(z["future_core_events"]):
            raise ValueError(f"translation ablation future-event coverage differs for {model}")
        if int(f["target_environment_rows"]) != int(z["target_environment_rows"]):
            raise ValueError(f"translation ablation target-row coverage differs for {model}")
        rows.append(
            {
                "model": model,
                "future_core_events": int(f["future_core_events"]),
                "target_environment_rows": int(f["target_environment_rows"]),
                "fitted_translation_log_loss": float(f["event_weighted_log_loss"]),
                "zero_offset_log_loss": float(z["event_weighted_log_loss"]),
                "fitted_minus_zero_log_loss": float(f["event_weighted_log_loss"])
                - float(z["event_weighted_log_loss"]),
                "fitted_translation_brier": float(f["event_weighted_multinomial_brier"]),
                "zero_offset_brier": float(z["event_weighted_multinomial_brier"]),
                "fitted_minus_zero_brier": float(f["event_weighted_multinomial_brier"])
                - float(z["event_weighted_multinomial_brier"]),
            }
        )
    comparison = pl.DataFrame(rows).sort("model")
    return combined, comparison


def _build_stratum_comparison(fitted, zero) -> pl.DataFrame:
    keys = ["model", "stratum_type", "stratum_value"]
    f = fitted.separate_stratified_metrics.rename(
        {
            "event_weighted_log_loss": "fitted_translation_log_loss",
            "event_weighted_multinomial_brier": "fitted_translation_brier",
            "future_core_events": "fitted_future_core_events",
            "target_environment_rows": "fitted_target_environment_rows",
        }
    )
    z = zero.separate_stratified_metrics.rename(
        {
            "event_weighted_log_loss": "zero_offset_log_loss",
            "event_weighted_multinomial_brier": "zero_offset_brier",
            "future_core_events": "zero_future_core_events",
            "target_environment_rows": "zero_target_environment_rows",
        }
    )
    joined = f.join(z, on=keys, how="inner")
    expected = max(f.height, z.height)
    if joined.height != expected:
        raise ValueError(
            "translation ablation stratum coverage mismatch: "
            f"fitted={f.height}, zero={z.height}, joined={joined.height}"
        )
    mismatch = joined.filter(
        (pl.col("fitted_future_core_events") != pl.col("zero_future_core_events"))
        | (
            pl.col("fitted_target_environment_rows")
            != pl.col("zero_target_environment_rows")
        )
    )
    if not mismatch.is_empty():
        raise ValueError("translation ablation stratum event coverage differs")
    return (
        joined.with_columns(
            (
                pl.col("fitted_translation_log_loss") - pl.col("zero_offset_log_loss")
            ).alias("fitted_minus_zero_log_loss"),
            (
                pl.col("fitted_translation_brier") - pl.col("zero_offset_brier")
            ).alias("fitted_minus_zero_brier"),
        )
        .sort(keys)
    )


def _build_component_comparison(fitted, zero) -> pl.DataFrame:
    keys = ["model", "core_bin"]
    f = fitted.component_scores.rename(
        {
            "multinomial_log_loss_contribution": "fitted_translation_log_loss_contribution",
            "binary_brier_contribution": "fitted_translation_brier_contribution",
        }
    )
    z = zero.component_scores.rename(
        {
            "multinomial_log_loss_contribution": "zero_offset_log_loss_contribution",
            "binary_brier_contribution": "zero_offset_brier_contribution",
        }
    )
    keep_zero = keys + [
        "zero_offset_log_loss_contribution",
        "zero_offset_brier_contribution",
    ]
    joined = f.join(z.select(keep_zero), on=keys, how="inner")
    if joined.height != f.height or joined.height != z.height:
        raise ValueError("translation ablation component coverage mismatch")
    return joined.with_columns(
        (
            pl.col("fitted_translation_log_loss_contribution")
            - pl.col("zero_offset_log_loss_contribution")
        ).alias("fitted_minus_zero_log_loss_contribution"),
        (
            pl.col("fitted_translation_brier_contribution")
            - pl.col("zero_offset_brier_contribution")
        ).alias("fitted_minus_zero_brier_contribution"),
    ).sort(keys)


def main() -> int:
    args = _parse_args()
    cutoff = date.fromisoformat(args.as_of_date)
    window = EvidenceWindow(
        label=f"season_to_date_half_life_{args.half_life_days:g}d",
        lookback_days=None,
        half_life_days=float(args.half_life_days),
    )

    summary, profile, combination_metrics, inputs = _load_universal_evidence(
        args.input_root,
        args.mlb_input_root,
        int(args.season),
    )
    translation_evidence = build_training_environment_transition_evidence(
        summary,
        profile,
        training_end=cutoff,
        min_core_events_per_stint=int(args.min_core_events_per_stint),
        max_gap_days=int(args.max_gap_days),
    )
    fit = fit_level_clr_translation(
        translation_evidence.pair_summary,
        translation_evidence.pair_profile,
        anchor_level="MLB",
    )
    zero_offsets = zero_translation_offsets(fit.offsets)

    validation = build_validation_snapshot_dataset(
        summary,
        profile,
        cutoff=cutoff,
        window=window,
    )
    predictor_ids = sorted(
        int(value)
        for value in validation.predictor_summary.get_column("player_id").to_list()
    )
    archive_path = args.work_dir / f"register-{CHADWICK_SNAPSHOT_SHA}.zip"
    archive_metadata = download_file(CHADWICK_ARCHIVE_URL, archive_path)
    people = read_chadwick_people_archive(archive_path)
    ages = build_mlbam_age_as_of(people, predictor_ids, as_of_date=cutoff)
    missing_age = ages.filter(pl.col("age_source_status") != "exact_birth_date")
    if not missing_age.is_empty():
        raise ValueError("translation ablation requires exact age for every predictor player")

    common = dict(
        summary=summary,
        profile=profile,
        validation=validation,
        ages=ages,
        cutoff=cutoff,
        window=window,
        age_band_width_years=float(args.age_band_width_years),
        min_age_level_peers=int(args.min_age_level_peers),
        prior_strength_core_events=float(args.prior_strength_core_events),
    )
    fitted = build_baseline_validation_variant(
        offsets=fit.offsets,
        variant=FITTED_TRANSLATION_VARIANT,
        **common,
    )
    zero = build_baseline_validation_variant(
        offsets=zero_offsets,
        variant=ZERO_TRANSLATION_VARIANT,
        **common,
    )

    if fitted.metrics["prediction_player_count"] != zero.metrics["prediction_player_count"]:
        raise ValueError("translation ablation prediction-player coverage differs")
    if fitted.metrics["scored_player_count"] != zero.metrics["scored_player_count"]:
        raise ValueError("translation ablation scored-player coverage differs")
    if (
        fitted.metrics["scored_target_environment_count"]
        != zero.metrics["scored_target_environment_count"]
    ):
        raise ValueError("translation ablation target-environment coverage differs")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    fitted_outputs = _variant_tables(fitted, args.output_dir)
    zero_outputs = _variant_tables(zero, args.output_dir)
    combined_aggregate, aggregate_comparison = _build_aggregate_comparison(fitted, zero)
    stratum_comparison = _build_stratum_comparison(fitted, zero)
    component_comparison = _build_component_comparison(fitted, zero)
    _write_table(combined_aggregate, args.output_dir, "aggregate_metrics_all_variants")
    _write_table(aggregate_comparison, args.output_dir, "translation_ablation_aggregate_comparison")
    _write_table(stratum_comparison, args.output_dir, "translation_ablation_stratum_comparison")
    _write_table(component_comparison, args.output_dir, "translation_ablation_component_comparison")

    aggregate_rows = {
        str(row["model"]): dict(row)
        for row in aggregate_comparison.iter_rows(named=True)
    }
    b1_strata = stratum_comparison.filter(pl.col("model") == "baseline1")
    b1_components = component_comparison.filter(pl.col("model") == "baseline1")
    report = {
        "report_schema_version": "0.1",
        "accepted": True,
        "season": int(args.season),
        "as_of_date": cutoff.isoformat(),
        "ablation_question": (
            "Does the fitted training-only level CLR observation layer improve future scoring "
            "relative to identical zero level effects, holding baseline/scoring mechanics fixed?"
        ),
        "temporal_semantics": "retrospective_event_cutoff_corrected_history_not_vintage_information_set",
        "candidate_hyperparameters_held_fixed": {
            "half_life_days": float(args.half_life_days),
            "prior_strength_core_events": float(args.prior_strength_core_events),
            "age_band_width_years": float(args.age_band_width_years),
            "min_age_level_peers": int(args.min_age_level_peers),
        },
        "inputs": inputs,
        "combined_evidence_metrics": combination_metrics,
        "translation_fit_metrics": fit.metrics,
        "translation_evidence_metrics": translation_evidence.metrics,
        "validation_dataset_metrics": validation.metrics,
        "chadwick_snapshot_sha": CHADWICK_SNAPSHOT_SHA,
        "chadwick_archive": archive_metadata,
        "variant_metrics": {
            FITTED_TRANSLATION_VARIANT: fitted.metrics,
            ZERO_TRANSLATION_VARIANT: zero.metrics,
        },
        "aggregate_comparison": aggregate_rows,
        "baseline1_breadth": {
            "stratum_comparison_count": int(b1_strata.height),
            "fitted_translation_log_loss_win_count": int(
                b1_strata.filter(pl.col("fitted_minus_zero_log_loss") < 0).height
            ),
            "fitted_translation_brier_win_count": int(
                b1_strata.filter(pl.col("fitted_minus_zero_brier") < 0).height
            ),
            "component_comparison_count": int(b1_components.height),
            "fitted_translation_component_log_loss_win_count": int(
                b1_components.filter(
                    pl.col("fitted_minus_zero_log_loss_contribution") < 0
                ).height
            ),
            "fitted_translation_component_brier_win_count": int(
                b1_components.filter(
                    pl.col("fitted_minus_zero_brier_contribution") < 0
                ).height
            ),
        },
        "outputs": {
            FITTED_TRANSLATION_VARIANT: fitted_outputs,
            ZERO_TRANSLATION_VARIANT: zero_outputs,
        },
        "interpretation": (
            "Controlled translation ablation only. Negative fitted-minus-zero score deltas mean "
            "the learned level observation effects improve predictive scoring. Baseline 0 still "
            "uses current level in its peer prior in both variants."
        ),
    }
    (args.output_dir / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
