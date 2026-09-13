#!/usr/bin/env python3
"""Build a self-contained local webpage for exploring Phase 1 results."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.model_law_audit import audit_private_preview_laws
from universal_baseball.projection_lineage import (
    PLAYABLE_OPPORTUNITY_MODEL_ID,
    validate_recorded_arrival_source,
    validate_recorded_opportunity_source,
)
from universal_baseball.prospect_arrival import ARRIVAL_MODEL_ID
from universal_baseball.results_explorer import write_explorer


REPORT_ROOTS = (
    Path("reports/generated/phase1-sequential-replay"),
    Path("reports/generated/current-and-future-contract-economics-v2"),
    Path("reports/generated/league-control"),
)
PHASE2_ROOT = Path("reports/generated/phase2-current-value")


def audit_phase2_checkpoint(
    as_of_date: str, value_path: Path, annual_path: Path
) -> dict[str, object]:
    """Refuse to open a Phase 2 checkpoint that violates model identities."""

    generated = Path("reports/generated")
    conditional = generated / "phase2-conditional-war-paths" / as_of_date / "tables"
    paths = {
        "hitter": conditional / "hitter_expected_war_paths.parquet",
        "pitcher": conditional / "pitcher_expected_war_paths.parquet",
        "nested": generated / "phase2-nested-career-fv" / as_of_date
        / "nested-career-model-fv.parquet",
        "values": value_path,
        "annual": annual_path,
    }
    if missing := [path for path in paths.values() if not path.exists()]:
        joined = "\n".join(f"- {path}" for path in missing)
        raise FileNotFoundError(f"Phase 2 law-audit inputs are missing:\n{joined}")
    conditional_report = Path("reports/generated/phase2-conditional-war-paths")
    conditional_report = conditional_report / as_of_date / "report.json"
    if not conditional_report.exists():
        raise FileNotFoundError(
            f"Phase 2 projection-lineage report is missing: {conditional_report}"
        )
    conditional_metadata = json.loads(
        conditional_report.read_text(encoding="utf-8")
    )
    recorded_source = conditional_metadata.get("opportunity_source")
    if not isinstance(recorded_source, dict):
        raise ValueError("Phase 2 projection-lineage record is missing")
    validate_recorded_opportunity_source(
        recorded_source,
        expected_model_id=PLAYABLE_OPPORTUNITY_MODEL_ID,
    )
    model_fv_report = generated / "phase2-model-fv" / as_of_date / "report.json"
    if not model_fv_report.exists():
        raise FileNotFoundError(
            f"Phase 2 model-FV lineage report is missing: {model_fv_report}"
        )
    model_fv_metadata = json.loads(model_fv_report.read_text(encoding="utf-8"))
    recorded_arrival = model_fv_metadata.get("arrival_source")
    if not isinstance(recorded_arrival, dict):
        raise ValueError("Phase 2 arrival-model lineage record is missing")
    validate_recorded_arrival_source(
        recorded_arrival,
        expected_model_id=ARRIVAL_MODEL_ID,
    )
    result = audit_private_preview_laws(
        pl.read_parquet(paths["hitter"]),
        pl.read_parquet(paths["pitcher"]),
        pl.read_parquet(paths["nested"]),
        pl.read_parquet(paths["values"]),
        runs_per_win=float(
            conditional_metadata["reference_environment"]["runs_per_win"]
        ),
        annual_contract_economics=pl.read_parquet(paths["annual"]),
    )
    if result["failed"]:
        failures = ", ".join(
            str(check["name"])
            for check in result["checks"]
            if check["status"] == "fail"
        )
        raise RuntimeError(f"Phase 2 model-law audit failed: {failures}")
    return result


def phase2_model_details(as_of_date: str) -> pl.DataFrame:
    """Assemble display-only component explanations from existing model outputs."""

    generated = Path("reports/generated")
    path_root = generated / "phase2-conditional-war-paths" / as_of_date / "tables"
    nested = pl.read_parquet(
        generated / "phase2-nested-career-fv" / as_of_date
        / "nested-career-model-fv.parquet"
    ).select(
        "player_id", "model_player_type", "primary_position",
        "three_tier_expected_workload", "three_tier_expected_six_year_war",
    )
    hitter = pl.read_parquet(path_root / "hitter_expected_war_paths.parquet").group_by(
        "player_id"
    ).agg(
        pl.col("conditional_war_per_600_pa").mean().alias("conditional_war_rate"),
        pl.lit("WAR per 600 PA").alias("conditional_war_rate_unit"),
        pl.col("batting_runs_per_600").mean(),
        pl.col("baserunning_runs_per_600").mean(),
        pl.col("defense_runs_per_600").mean(),
        pl.col("positional_runs_per_600").mean(),
    )
    pitcher = pl.read_parquet(
        path_root / "pitcher_expected_war_paths.parquet"
    ).group_by("player_id").agg(
        pl.col("conditional_war_per_800_bf").mean().alias("conditional_war_rate"),
        pl.lit("WAR per 800 BF").alias("conditional_war_rate_unit"),
        pl.col("pitching_runs_above_average_per_800").mean(),
    )
    details = nested.join(hitter, on="player_id", how="left", validate="1:1").join(
        pitcher,
        on="player_id",
        how="left",
        validate="1:1",
        suffix="_pitcher",
    ).with_columns(
        pl.when(pl.col("model_player_type") == "pitcher")
        .then(pl.col("conditional_war_rate_pitcher"))
        .otherwise(pl.col("conditional_war_rate"))
        .alias("conditional_war_rate"),
        pl.when(pl.col("model_player_type") == "pitcher")
        .then(pl.col("conditional_war_rate_unit_pitcher"))
        .otherwise(pl.col("conditional_war_rate_unit"))
        .alias("conditional_war_rate_unit"),
    ).drop("conditional_war_rate_pitcher", "conditional_war_rate_unit_pitcher")
    uncertainty_path = (
        generated / "phase2-prospect-workload-uncertainty" / as_of_date
        / "prospect-workload-uncertainty.parquet"
    )
    if not uncertainty_path.exists():
        raise FileNotFoundError(
            f"Phase 2 prospect workload uncertainty is missing: {uncertainty_path}"
        )
    uncertainty = pl.read_parquet(uncertainty_path)
    details = details.join(uncertainty, on="player_id", how="left", validate="1:1")
    applicable = details.filter(pl.col("three_tier_expected_workload").is_not_null())
    if applicable.filter(pl.col("workload_war_mean").is_null()).height:
        raise ValueError("prospect workload uncertainty coverage is incomplete")
    if applicable.filter(
        (
            pl.col("workload_war_mean")
            - pl.col("three_tier_expected_six_year_war")
        ).abs()
        > 1e-8
    ).height:
        raise ValueError("prospect workload uncertainty does not preserve point means")
    dependent_path = (
        generated / "phase2-dependent-career-value" / as_of_date
        / "dependent-career-value.parquet"
    )
    if dependent_path.exists():
        dependent = pl.read_parquet(dependent_path).select(
            "player_id",
            pl.col("mean_discounted_surplus_value_dollars").alias(
                "research_mean_value_dollars"
            ),
            pl.col("p10_discounted_surplus_value_dollars").alias(
                "research_p10_value_dollars"
            ),
            pl.col("median_discounted_surplus_value_dollars").alias(
                "research_median_value_dollars"
            ),
            pl.col("p90_discounted_surplus_value_dollars").alias(
                "research_p90_value_dollars"
            ),
            pl.col("mean_controlled_war").alias("research_mean_controlled_war"),
            pl.col("p10_controlled_war").alias("research_p10_controlled_war"),
            pl.col("median_controlled_war").alias("research_median_controlled_war"),
            pl.col("p90_controlled_war").alias("research_p90_controlled_war"),
            pl.col("expected_discounted_cost_dollars").alias(
                "research_expected_cost_dollars"
            ),
            pl.col("arrival_probability").alias("research_arrival_probability"),
            pl.col("bust_probability").alias("research_bust_probability"),
            pl.col("regular_probability").alias("research_regular_probability"),
            pl.col("star_probability").alias("research_star_probability"),
        )
        details = details.join(dependent, on="player_id", how="left", validate="1:1")
        research_applicable = details.filter(
            pl.col("three_tier_expected_workload").is_not_null()
        )
        if research_applicable.filter(
            pl.col("research_mean_value_dollars").is_null()
        ).height:
            raise ValueError("dependent career-value research coverage is incomplete")
    upside_root = generated / "peak-talent-upside"
    upside_paths = {
        player_type: upside_root / f"current_{player_type}_upside.parquet"
        for player_type in ("hitter", "pitcher")
    }
    if all(path.exists() for path in upside_paths.values()):
        upside = pl.concat(
            [
                pl.read_parquet(path).select(
                    "player_id",
                    pl.lit(player_type).alias("model_player_type"),
                    pl.col("peak_runs_rate").alias("peak_talent_runs_rate"),
                    "peak_above_average_probability",
                    "peak_impact_probability",
                    *(
                        column
                        for column in (
                            "pitch_process_applied",
                            "pitch_process_runs_change",
                            "process_whiff",
                            "process_strike",
                            "process_swing",
                            "process_ppbf",
                        )
                        if column in pl.read_parquet(path).columns
                    ),
                )
                for player_type, path in upside_paths.items()
            ],
            how="diagonal_relaxed",
        )
        details = details.join(
            upside,
            on=["player_id", "model_player_type"],
            how="left",
            validate="1:1",
        )
    return details


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--as-of-date",
        help="Checkpoint date; defaults to the latest date present in all inputs",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/generated/results-explorer/index.html"),
    )
    return parser.parse_args()


def latest_common_date(roots: tuple[Path, ...] = REPORT_ROOTS) -> str:
    date_sets = [
        {child.name for child in root.iterdir() if child.is_dir()}
        if root.exists()
        else set()
        for root in roots
    ]
    common = set.intersection(*date_sets)
    if not common:
        raise FileNotFoundError("No common dated current-results checkpoint was found")
    return max(common)


def main() -> int:
    args = _args()
    phase2_dates = (
        {child.name for child in PHASE2_ROOT.iterdir() if child.is_dir()}
        if PHASE2_ROOT.exists()
        else set()
    )
    as_of_date = args.as_of_date or (
        max(phase2_dates) if phase2_dates else latest_common_date()
    )
    phase2_dated = PHASE2_ROOT / as_of_date
    if (phase2_dated / "value-records.parquet").exists():
        value_path = phase2_dated / "value-records.parquet"
        annual_path = phase2_dated / "annual-contract-economics.parquet"
    else:
        value_path = (
            Path("reports/generated/phase1-sequential-replay")
            / as_of_date
            / "value-records.parquet"
        )
        annual_path = (
            Path("reports/generated/current-and-future-contract-economics-v2")
            / as_of_date
            / "annual-contract-economics.parquet"
        )
    names_path = (
        Path("reports/generated/league-control")
        / as_of_date
        / "league-control-snapshot.parquet"
    )
    missing = [path for path in (value_path, annual_path, names_path) if not path.exists()]
    if missing:
        joined = "\n".join(f"- {path}" for path in missing)
        raise FileNotFoundError(f"Required model outputs are missing:\n{joined}")
    law_result = None
    if (phase2_dated / "value-records.parquet").exists():
        law_result = audit_phase2_checkpoint(as_of_date, value_path, annual_path)
    model_details = phase2_model_details(as_of_date) if law_result is not None else None
    payload = write_explorer(
        value_path,
        annual_path,
        names_path,
        args.output,
        model_details=model_details,
    )
    print(f"Results explorer created: {args.output.resolve()}")
    print(
        f"Players: {payload['meta']['player_count']:,} | "
        f"usable: {payload['meta']['available_count']:,} | "
        f"review: {payload['meta']['review_count']:,}"
    )
    if law_result is not None:
        print(f"Model-law checks: {law_result['passed']} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
