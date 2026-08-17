#!/usr/bin/env python3
"""Materialize one chronological universal Current Talent baseline validation gate."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import date
from pathlib import Path

import polars as pl

from universal_baseball.certification import download_file
from universal_baseball.chadwick import (
    CHADWICK_ARCHIVE_URL,
    CHADWICK_SNAPSHOT_SHA,
    build_mlbam_age_as_of,
    read_chadwick_people_archive,
)
from universal_baseball.current_talent_baselines import (
    build_baseline_profiles,
    build_translated_player_evidence,
    fit_leave_one_out_age_level_prior,
)
from universal_baseball.current_talent_evidence import EvidenceWindow
from universal_baseball.current_talent_scoring import (
    project_latent_profiles_to_target_environment,
    score_current_talent_profiles,
)
from universal_baseball.current_talent_translation import (
    build_training_environment_transition_evidence,
    fit_level_clr_translation,
)
from universal_baseball.current_talent_universal_evidence import (
    combine_universal_player_game_evidence,
)
from universal_baseball.current_talent_validation_dataset import (
    build_validation_snapshot_dataset,
)


FILENAME_LEVEL_TOKENS = {
    "aaa": "aaa",
    "aa": "aa",
    "a+": "aplus",
    "a": "a",
    "rk": "rk",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--mlb-input-root", type=Path, required=True)
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--as-of-date", type=str, required=True)
    parser.add_argument("--half-life-days", type=float, default=90.0)
    parser.add_argument("--prior-strength-core-events", type=float, default=100.0)
    parser.add_argument("--age-band-width-years", type=float, default=2.0)
    parser.add_argument("--min-age-level-peers", type=int, default=12)
    parser.add_argument("--min-core-events-per-stint", type=int, default=20)
    parser.add_argument("--max-gap-days", type=int, default=365)
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("data/quarantine/current-talent-baseline-validation"),
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def _one(root: Path, pattern: str) -> Path:
    matches = sorted(root.rglob(pattern))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {pattern} under {root}, found {len(matches)}")
    return matches[0]


def _load_universal_evidence(
    milb_root: Path,
    mlb_root: Path,
    season: int,
) -> tuple[pl.DataFrame, pl.DataFrame, dict[str, object], list[dict[str, str]]]:
    summaries: list[pl.DataFrame] = []
    profiles: list[pl.DataFrame] = []
    inputs: list[dict[str, str]] = []

    for filename_level, token in FILENAME_LEVEL_TOKENS.items():
        summary_path = _one(milb_root, f"current_talent_game_summary_{season}_{token}.parquet")
        profile_path = _one(milb_root, f"current_talent_game_profile_{season}_{token}.parquet")
        summaries.append(pl.read_parquet(summary_path))
        profiles.append(pl.read_parquet(profile_path))
        inputs.append(
            {
                "source_group": "affiliated_milb",
                "filename_level": filename_level,
                "summary": str(summary_path),
                "profile": str(profile_path),
            }
        )

    mlb_summary_path = _one(mlb_root, f"current_talent_game_summary_{season}_mlb.parquet")
    mlb_profile_path = _one(mlb_root, f"current_talent_game_profile_{season}_mlb.parquet")
    summaries.append(pl.read_parquet(mlb_summary_path))
    profiles.append(pl.read_parquet(mlb_profile_path))
    inputs.append(
        {
            "source_group": "mlb",
            "filename_level": "mlb",
            "summary": str(mlb_summary_path),
            "profile": str(mlb_profile_path),
        }
    )

    summary, profile, metrics = combine_universal_player_game_evidence(
        summaries,
        profiles,
        expected_seasons={int(season)},
        require_all_universal_leagues=False,
    )
    observed_levels = set(summary.get_column("level_group").unique().to_list())
    expected_levels = {"MLB", "AAA", "AA", "HIGH_A", "SINGLE_A", "ROOKIE_COMPLEX"}
    if observed_levels != expected_levels:
        raise ValueError(
            "baseline validation universal level coverage mismatch: "
            f"observed={sorted(observed_levels)}, expected={sorted(expected_levels)}"
        )
    return summary, profile, metrics, inputs


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


def _aggregate_metric_rows(frame: pl.DataFrame) -> dict[str, dict[str, object]]:
    if frame.is_empty():
        return {}
    return {
        str(row["model"]): {
            key: value
            for key, value in row.items()
            if key != "model"
        }
        for row in frame.iter_rows(named=True)
    }


def main() -> int:
    args = _parse_args()
    cutoff = date.fromisoformat(args.as_of_date)
    if args.half_life_days <= 0:
        raise ValueError("half-life-days must be positive")

    summary, profile, combination_metrics, inputs = _load_universal_evidence(
        args.input_root,
        args.mlb_input_root,
        int(args.season),
    )
    window = EvidenceWindow(
        label=f"season_to_date_half_life_{args.half_life_days:g}d",
        lookback_days=None,
        half_life_days=float(args.half_life_days),
    )

    translation_evidence = build_training_environment_transition_evidence(
        summary,
        profile,
        training_end=cutoff,
        min_core_events_per_stint=int(args.min_core_events_per_stint),
        max_gap_days=int(args.max_gap_days),
    )
    translation_fit = fit_level_clr_translation(
        translation_evidence.pair_summary,
        translation_evidence.pair_profile,
        anchor_level="MLB",
    )

    validation = build_validation_snapshot_dataset(
        summary,
        profile,
        cutoff=cutoff,
        window=window,
    )
    predictor_ids = sorted(
        int(value) for value in validation.predictor_summary.get_column("player_id").to_list()
    )
    archive_path = args.work_dir / f"register-{CHADWICK_SNAPSHOT_SHA}.zip"
    archive_metadata = download_file(CHADWICK_ARCHIVE_URL, archive_path)
    people = read_chadwick_people_archive(archive_path)
    ages = build_mlbam_age_as_of(people, predictor_ids, as_of_date=cutoff)
    missing_age = ages.filter(pl.col("age_source_status") != "exact_birth_date")
    if not missing_age.is_empty():
        raise ValueError(
            "baseline validation requires exact age for the first gate; missing player IDs="
            f"{missing_age.get_column('player_id').to_list()}"
        )

    context = (
        validation.predictor_summary.select(
            "player_id",
            "as_of_level_group",
            "as_of_environment_ambiguous",
            "prior_mlb_evidence",
            "effective_core_events",
        )
        .join(ages, on="player_id", how="left")
        .sort("player_id")
    )
    translated = build_translated_player_evidence(
        summary,
        profile,
        translation_fit.offsets,
        cutoff=cutoff,
        window=window,
    )
    prior = fit_leave_one_out_age_level_prior(
        translated,
        context,
        age_band_width_years=float(args.age_band_width_years),
        min_age_level_peers=int(args.min_age_level_peers),
    )
    baselines = build_baseline_profiles(
        translated,
        prior,
        prior_strength_core_events=float(args.prior_strength_core_events),
    )

    projected = project_latent_profiles_to_target_environment(
        baselines.profile,
        validation.target_summary,
        translation_fit.offsets,
    )
    scoring_context = (
        validation.scoring_rows.join(
            ages.select("player_id", "age_years"),
            on="player_id",
            how="left",
        )
        .join(
            translated.select("player_id", "effective_core_events").unique(),
            on="player_id",
            how="left",
            suffix="_translated",
        )
    )
    score_report = score_current_talent_profiles(
        projected,
        validation.target_profile,
        scoring_context=scoring_context,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_tables = {
        "translation_offsets": _write_table(translation_fit.offsets, args.output_dir, "translation_offsets"),
        "ages": _write_table(ages, args.output_dir, "ages"),
        "predictor_summary": _write_table(validation.predictor_summary, args.output_dir, "predictor_summary"),
        "target_summary": _write_table(validation.target_summary, args.output_dir, "target_summary"),
        "target_profile": _write_table(validation.target_profile, args.output_dir, "target_profile"),
        "scoring_context": _write_table(scoring_context, args.output_dir, "scoring_context"),
        "translated_player_evidence": _write_table(translated, args.output_dir, "translated_player_evidence"),
        "baseline0_prior": _write_table(prior, args.output_dir, "baseline0_prior"),
        "baseline_profiles": _write_table(baselines.profile, args.output_dir, "baseline_profiles"),
        "projected_target_profile": _write_table(projected, args.output_dir, "projected_target_profile"),
        "environment_scores": _write_table(score_report.environment_scores, args.output_dir, "environment_scores"),
        "component_calibration": _write_table(score_report.component_calibration, args.output_dir, "component_calibration"),
        "aggregate_metrics": _write_table(score_report.aggregate_metrics, args.output_dir, "aggregate_metrics"),
        "stratified_metrics": _write_table(score_report.stratified_metrics, args.output_dir, "stratified_metrics"),
    }

    aggregate = _aggregate_metric_rows(score_report.aggregate_metrics)
    comparison: dict[str, float | None] = {
        "baseline1_minus_baseline0_event_weighted_log_loss": None,
        "baseline1_minus_baseline0_event_weighted_multinomial_brier": None,
    }
    if "baseline0" in aggregate and "baseline1" in aggregate:
        comparison = {
            "baseline1_minus_baseline0_event_weighted_log_loss": float(
                aggregate["baseline1"]["event_weighted_log_loss"]
                - aggregate["baseline0"]["event_weighted_log_loss"]
            ),
            "baseline1_minus_baseline0_event_weighted_multinomial_brier": float(
                aggregate["baseline1"]["event_weighted_multinomial_brier"]
                - aggregate["baseline0"]["event_weighted_multinomial_brier"]
            ),
        }

    peer_source_counts = Counter(
        str(value) for value in prior.select("player_id", "prior_peer_source").unique().get_column("prior_peer_source").to_list()
    )
    report = {
        "report_schema_version": "0.1",
        "accepted": True,
        "season": int(args.season),
        "as_of_date": cutoff.isoformat(),
        "temporal_semantics": "retrospective_event_cutoff_corrected_history_not_vintage_information_set",
        "predictor_window": {
            "label": window.label,
            "lookback_days": window.lookback_days,
            "half_life_days": window.half_life_days,
        },
        "candidate_hyperparameters_not_frozen": {
            "prior_strength_core_events": float(args.prior_strength_core_events),
            "age_band_width_years": float(args.age_band_width_years),
            "min_age_level_peers": int(args.min_age_level_peers),
            "min_core_events_per_translation_stint": int(args.min_core_events_per_stint),
            "translation_max_gap_days": int(args.max_gap_days),
        },
        "inputs": inputs,
        "combined_evidence_metrics": combination_metrics,
        "translation_evidence_metrics": translation_evidence.metrics,
        "translation_fit_metrics": translation_fit.metrics,
        "validation_dataset_metrics": validation.metrics,
        "chadwick_snapshot_sha": CHADWICK_SNAPSHOT_SHA,
        "chadwick_archive": archive_metadata,
        "age_exact_coverage": {
            "predictor_player_count": len(predictor_ids),
            "exact_age_count": int(ages.filter(pl.col("age_source_status") == "exact_birth_date").height),
            "missing_exact_age_count": int(missing_age.height),
        },
        "baseline_metrics": baselines.metrics,
        "baseline0_prior_peer_source_player_counts": dict(sorted(peer_source_counts.items())),
        "score_metrics": score_report.metrics,
        "aggregate_proper_scores": aggregate,
        "baseline_comparison": comparison,
        "output_tables": output_tables,
        "interpretation": (
            "First chronological universal Baseline 0/Baseline 1 predictive validation gate. "
            "All translation and predictor evidence is strictly pre-cutoff; future core outcomes "
            "are scored in their realized target level. Candidate hyperparameters are not frozen "
            "from this single cutoff."
        ),
    }
    report_path = args.output_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
