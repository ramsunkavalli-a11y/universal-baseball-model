#!/usr/bin/env python3
"""Audit contact-shape semantics and stability without scoring offense."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.performance_season import CONTACT_CORE_BINS
from universal_baseball.storage import sha256_file, write_canonical_parquet


COMPONENTS = {
    "offb_per_contact": (
        ("PULL_OFFB", "CENTER_OFFB", "OPPO_OFFB"),
        CONTACT_CORE_BINS,
    ),
    "non_iffb_air_per_contact": (
        ("PULL_OFFB", "CENTER_OFFB", "OPPO_OFFB", "PULL_LD", "CENTER_LD", "OPPO_LD"),
        CONTACT_CORE_BINS,
    ),
    "pull_air_per_non_iffb_air": (
        ("PULL_OFFB", "PULL_LD"),
        ("PULL_OFFB", "CENTER_OFFB", "OPPO_OFFB", "PULL_LD", "CENTER_LD", "OPPO_LD"),
    ),
    "pull_offb_per_offb": (
        ("PULL_OFFB",),
        ("PULL_OFFB", "CENTER_OFFB", "OPPO_OFFB"),
    ),
    "pull_ld_per_ld": (
        ("PULL_LD",),
        ("PULL_LD", "CENTER_LD", "OPPO_LD"),
    ),
    "oppo_gb_per_gb": (
        ("OPPO_GB",),
        ("PULL_GB", "CENTER_GB", "OPPO_GB"),
    ),
    "gb_per_contact": (
        ("PULL_GB", "CENTER_GB", "OPPO_GB"),
        CONTACT_CORE_BINS,
    ),
    "iffb_per_contact": (("IFFB",), CONTACT_CORE_BINS),
}
EVIDENCE_BANDS = (
    (0, 25, "<25"),
    (25, 50, "25-49"),
    (50, 100, "50-99"),
    (100, 200, "100-199"),
    (200, None, "200+"),
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--shape-history",
        type=Path,
        default=Path(
            "reports/generated/hitter-v2-stage2b-contact-shape-source/tables/"
            "contact_shape_player_season.parquet"
        ),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2c-shape-stability"),
    )
    return parser.parse_args()


def _wide_profiles(history: pl.DataFrame, keys: list[str]) -> pl.DataFrame:
    wide = (
        history.group_by(*keys, "core_bin")
        .agg(pl.col("occurrence_count").sum())
        .pivot(on="core_bin", index=keys, values="occurrence_count")
    )
    return wide.with_columns(
        *[
            (
                pl.col(core_bin).fill_null(0).cast(pl.Int64)
                if core_bin in wide.columns
                else pl.lit(0, dtype=pl.Int64)
            ).alias(core_bin)
            for core_bin in CONTACT_CORE_BINS
        ]
    ).sort(*keys)


def _component_long(profiles: pl.DataFrame) -> pl.DataFrame:
    rows: list[pl.DataFrame] = []
    for component, (numerator_bins, denominator_bins) in COMPONENTS.items():
        numerator = pl.sum_horizontal(*[pl.col(value) for value in numerator_bins])
        denominator = pl.sum_horizontal(*[pl.col(value) for value in denominator_bins])
        rows.append(
            profiles.with_columns(
                pl.lit(component).alias("component"),
                numerator.cast(pl.Int64).alias("numerator"),
                denominator.cast(pl.Int64).alias("denominator"),
            )
            .filter(pl.col("denominator") > 0)
            .with_columns(
                (pl.col("numerator") / pl.col("denominator")).alias("rate")
            )
            .select(
                *[
                    column
                    for column in ("season", "player_id", "level_group")
                    if column in profiles.columns
                ],
                "component",
                "numerator",
                "denominator",
                "rate",
            )
        )
    sort_columns = [
        column
        for column in ("component", "player_id", "season", "level_group")
        if column in profiles.columns or column == "component"
    ]
    return pl.concat(rows, how="vertical_relaxed").sort(*sort_columns)


def _adjacent_pairs(
    component_rates: pl.DataFrame,
    *,
    same_level: bool,
) -> pl.DataFrame:
    left = component_rates.rename(
        {
            "season": "season_1",
            "numerator": "numerator_1",
            "denominator": "denominator_1",
            "rate": "rate_1",
        }
    )
    right = component_rates.rename(
        {
            "season": "season_2",
            "numerator": "numerator_2",
            "denominator": "denominator_2",
            "rate": "rate_2",
            "level_group": "level_group_2",
        }
    )
    join_keys = ["player_id", "component"]
    if same_level:
        right = right.rename({"level_group_2": "level_group"})
        join_keys.append("level_group")
    pairs = left.join(right, on=join_keys, how="inner").filter(
        pl.col("season_2") == pl.col("season_1") + 1
    )
    if same_level:
        pairs = pairs.with_columns(
            pl.col("level_group").alias("level_group_1"),
            pl.col("level_group").alias("level_group_2"),
        )
    pairs = pairs.with_columns(
        pl.min_horizontal("denominator_1", "denominator_2").alias(
            "minimum_denominator"
        ),
        (pl.col("rate_2") - pl.col("rate_1")).alias("rate_change"),
    )
    return pairs.sort(
        *[
            column
            for column in (
                "component",
                "player_id",
                "season_1",
                "season_2",
                "level_group_1",
                "level_group_2",
            )
            if column in pairs.columns
        ]
    )


def _pearson(left: np.ndarray, right: np.ndarray) -> float | None:
    if len(left) < 3 or np.std(left) <= 0.0 or np.std(right) <= 0.0:
        return None
    return float(np.corrcoef(left, right)[0, 1])


def _pair_summary(
    pairs: pl.DataFrame,
    *,
    dimensions: tuple[str, ...],
) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    groups = pairs.group_by(*dimensions, maintain_order=True) if dimensions else [((), pairs)]
    for key, frame in groups:
        frame = frame.sort(
            *[
                column
                for column in ("player_id", "season_1", "season_2")
                if column in frame.columns
            ]
        )
        keys = key if isinstance(key, tuple) else (key,)
        left = frame["rate_1"].to_numpy().astype(float)
        right = frame["rate_2"].to_numpy().astype(float)
        left_rank = frame["rate_1"].rank(method="average").to_numpy().astype(float)
        right_rank = frame["rate_2"].rank(method="average").to_numpy().astype(float)
        row = {dimension: keys[index] for index, dimension in enumerate(dimensions)}
        rows.append(
            {
                **row,
                "pairs": frame.height,
                "players": frame["player_id"].n_unique(),
                "events_season_1": int(frame["denominator_1"].sum()),
                "events_season_2": int(frame["denominator_2"].sum()),
                "pearson": _pearson(left, right),
                "spearman": _pearson(left_rank, right_rank),
                "mean_rate_1": float(np.mean(left)),
                "mean_rate_2": float(np.mean(right)),
                "mean_absolute_change": float(np.mean(np.abs(right - left))),
            }
        )
    return pl.DataFrame(rows, infer_schema_length=None).sort(*dimensions)


def _evidence_band_expression() -> pl.Expr:
    expression = pl.lit(None, dtype=pl.String)
    for lower, upper, label in EVIDENCE_BANDS:
        condition = pl.col("minimum_denominator") >= lower
        if upper is not None:
            condition &= pl.col("minimum_denominator") < upper
        expression = pl.when(condition).then(pl.lit(label)).otherwise(expression)
    return expression.alias("evidence_band")


def main() -> int:
    args = _parse_args()
    history = pl.read_parquet(args.shape_history)
    required = {
        "season",
        "league_id",
        "player_id",
        "level_group",
        "core_bin",
        "occurrence_count",
    }
    if missing := sorted(required - set(history.columns)):
        raise ValueError(f"shape history missing columns: {missing}")
    observed_bins = set(str(value) for value in history["core_bin"].unique())
    if observed_bins != set(CONTACT_CORE_BINS):
        raise ValueError("shape history does not contain the frozen ten-bin vocabulary")
    if history.filter(pl.col("occurrence_count") <= 0).height:
        raise ValueError("shape source must contain positive sparse counts")

    level_profiles = _wide_profiles(
        history, ["season", "player_id", "level_group"]
    )
    level_rates = _component_long(level_profiles)
    same_level_pairs = _adjacent_pairs(level_rates, same_level=True).with_columns(
        _evidence_band_expression()
    )

    player_level_totals = level_profiles.with_columns(
        pl.sum_horizontal(*[pl.col(value) for value in CONTACT_CORE_BINS]).alias(
            "contact_events"
        )
    )
    primary_level = (
        player_level_totals.sort(
            "player_id",
            "season",
            "contact_events",
            "level_group",
            descending=[False, False, True, False],
        )
        .unique(["player_id", "season"], keep="first", maintain_order=True)
        .select("player_id", "season", "level_group")
    )
    all_level_profiles = _wide_profiles(history, ["season", "player_id"]).join(
        primary_level, on=["player_id", "season"], how="left", validate="1:1"
    )
    all_level_rates = _component_long(all_level_profiles)
    transition_pairs = _adjacent_pairs(all_level_rates, same_level=False).with_columns(
        _evidence_band_expression(),
        pl.concat_str("level_group", "level_group_2", separator="->").alias(
            "level_transition"
        ),
    )

    overall = _pair_summary(same_level_pairs, dimensions=("component",))
    by_level = _pair_summary(
        same_level_pairs, dimensions=("component", "level_group")
    )
    by_evidence = _pair_summary(
        same_level_pairs, dimensions=("component", "evidence_band")
    )
    by_transition = _pair_summary(
        transition_pairs, dimensions=("component", "level_transition")
    )
    table_root = args.report_root / "tables"
    artifacts = {
        "same_level_pairs": write_canonical_parquet(
            same_level_pairs,
            table_root / "same_level_adjacent_season_pairs.parquet",
            table_name="hitter_v2_stage2c_same_level_adjacent_season_shape_pairs",
        ).as_record(),
        "transition_pairs": write_canonical_parquet(
            transition_pairs,
            table_root / "primary_level_transition_pairs.parquet",
            table_name="hitter_v2_stage2c_primary_level_transition_shape_pairs",
        ).as_record(),
        "overall": write_canonical_parquet(
            overall,
            table_root / "stability_overall.parquet",
            table_name="hitter_v2_stage2c_shape_stability_overall",
        ).as_record(),
        "by_level": write_canonical_parquet(
            by_level,
            table_root / "stability_by_level.parquet",
            table_name="hitter_v2_stage2c_shape_stability_by_level",
        ).as_record(),
        "by_evidence": write_canonical_parquet(
            by_evidence,
            table_root / "stability_by_evidence.parquet",
            table_name="hitter_v2_stage2c_shape_stability_by_evidence",
        ).as_record(),
        "by_transition": write_canonical_parquet(
            by_transition,
            table_root / "stability_by_transition.parquet",
            table_name="hitter_v2_stage2c_shape_stability_by_transition",
        ).as_record(),
    }
    report = {
        "report_schema_version": "0.1",
        "program": "hitter_v2",
        "stage": "2c_source_design",
        "status": "contact_shape_semantics_and_stability_audited_without_offensive_score",
        "candidate_fit": False,
        "candidate_scored": False,
        "offensive_target_loaded": False,
        "protected_2026_opened": False,
        "source": {
            "path": args.shape_history.as_posix(),
            "sha256": sha256_file(args.shape_history),
            "seasons": sorted(int(value) for value in history["season"].unique()),
            "bins": list(CONTACT_CORE_BINS),
            "events": int(history["occurrence_count"].sum()),
        },
        "semantics": {
            "direction": "batter-relative pull/center/opposite from hc_x/hc_y and event batter side",
            "center_boundary_degrees": 15.0,
            "unknown_side_or_coordinates": "failed_closed_null_direction",
            "trajectory": "Gameday hitData bb_type mapped to IFFB/OFFB/LD/GB",
            "mlb_milb_classifier_code_shared": True,
            "season_artifact_retains_batter_side": False,
            "switch_hitter_side_specific_profile_recoverable_from_artifact": False,
            "semantic_equivalence_across_source_systems_proven": False,
        },
        "components": {
            name: {
                "numerator_bins": list(numerator),
                "denominator_bins": list(denominator),
            }
            for name, (numerator, denominator) in COMPONENTS.items()
        },
        "pair_counts": {
            "same_level_component_pairs": same_level_pairs.height,
            "primary_level_transition_component_pairs": transition_pairs.height,
        },
        "overall_stability": overall.to_dicts(),
        "artifacts": artifacts,
        "limitations": [
            "Observed year-to-year correlation combines talent persistence, measurement error, and changing opportunity mix.",
            "The aggregate artifact cannot separate switch-hitter batting sides.",
            "Same classifier code does not prove identical raw coordinate or trajectory semantics across source systems.",
            "No offensive outcome or forecast candidate is fit or scored in this audit.",
        ],
        "next_step": "freeze_stage2c_source_and_development_contract_without_scoring",
    }
    args.report_root.mkdir(parents=True, exist_ok=True)
    report_path = args.report_root / "report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
