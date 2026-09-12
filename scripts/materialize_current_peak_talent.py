#!/usr/bin/env python3
"""Materialize current prospect peak-rate talent without public-rank inputs."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

from audit_one_year_talent_development import HITTER_COMPONENTS, PITCHER_COMPONENTS
from materialize_current_future_talent import (
    _hitter_runs,
    _model_predict,
    _pitcher_runs,
    _prepare,
)
from universal_baseball.storage import write_canonical_parquet


BASIC_ROOT = Path("reports/generated/current-basic-talent/2026-09-08/tables")
PEAK_REPORT = Path("reports/generated/age-to-peak-talent/report.json")
OUTPUT_ROOT = Path("reports/generated/current-peak-talent/2026-09-08")


def _rank_prospects(frame: pl.DataFrame) -> pl.DataFrame:
    eligible = (
        frame.filter(
            (pl.col("ranking_status") == "ranked")
            & (pl.col("as_of_level_group") != "MLB")
            & pl.col("age_years").is_not_null()
            & (pl.col("age_years") <= 25)
        )
        .sort(
            ["peak_runs_rate", "effective_evidence", "player_id"],
            descending=[True, True, False],
        )
        .with_row_index("prospect_peak_rate_rank", offset=1)
    )
    other = frame.join(
        eligible.select("player_id"),
        on="player_id",
        how="anti",
    ).with_columns(pl.lit(None, dtype=pl.UInt32).alias("prospect_peak_rate_rank"))
    return pl.concat([eligible, other], how="diagonal_relaxed")


def _materialize(
    frame: pl.DataFrame,
    components: tuple[str, ...],
    fit: dict[str, object],
    *,
    player_type: str,
) -> pl.DataFrame:
    present = frame.select([f"p_{name}" for name in components]).to_numpy()
    peak = _model_predict(frame, components, fit)
    age = frame.get_column("age_years").to_numpy()
    minor = frame.get_column("as_of_level_group").to_numpy() != "MLB"
    if player_type == "hitter":
        apply_model = minor & (age >= 16) & (age <= 23)
        present_runs = frame.get_column("present_offense_runs_per_600_pa").to_numpy()
        model_runs = _hitter_runs(peak, present, present_runs)
        status = "historical_gate_passed"
    else:
        apply_model = minor & (age >= 16) & (age <= 23)
        present_runs = frame.get_column("present_pitching_runs_per_800_bf").to_numpy()
        model_runs = _pitcher_runs(peak, present, present_runs)
        status = "historical_gate_passed"
    peak[~apply_model] = present[~apply_model]
    peak_runs = np.where(apply_model, model_runs, present_runs)
    policy = np.where(
        apply_model,
        f"age_24_to_26_{fit['form']}",
        "carry_forward_outside_supported_age",
    )
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
        pl.Series("present_runs_rate", present_runs),
        pl.Series("peak_runs_rate", peak_runs),
        pl.Series("peak_runs_change", peak_runs - present_runs),
        pl.Series("peak_policy", policy),
        pl.lit(status).alias("peak_validation_status"),
        *(pl.Series(f"present_{name}_rate", present[:, index]) for index, name in enumerate(components)),
        *(pl.Series(f"peak_{name}_rate", peak[:, index]) for index, name in enumerate(components)),
    )
    return _rank_prospects(output)


def main() -> int:
    report = json.loads(PEAK_REPORT.read_text(encoding="utf-8"))
    hitters = _materialize(
        _prepare(
            BASIC_ROOT / "current_hitter_talent.parquet",
            HITTER_COMPONENTS,
            player_type="hitter",
        ),
        HITTER_COMPONENTS,
        report["hitters"]["current_fit"],
        player_type="hitter",
    )
    pitchers = _materialize(
        _prepare(
            BASIC_ROOT / "current_pitcher_talent.parquet",
            PITCHER_COMPONENTS,
            player_type="pitcher",
        ),
        PITCHER_COMPONENTS,
        report["pitchers"]["current_fit"],
        player_type="pitcher",
    )
    tables = OUTPUT_ROOT / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    storage = {}
    for name, frame in (("hitters", hitters), ("pitchers", pitchers)):
        path = tables / f"current_peak_{name}.parquet"
        storage[name] = write_canonical_parquet(
            frame,
            path,
            table_name=f"current_peak_{name}_talent",
        ).as_record()
        frame.write_csv(path.with_suffix(".csv"))
        frame.filter(pl.col("prospect_peak_rate_rank") <= 100).sort(
            "prospect_peak_rate_rank"
        ).write_csv(tables / f"current_peak_{name}_top100.csv")
    output_report = {
        "report_schema_version": "0.1",
        "status": "inspectable_prospect_peak_rate",
        "ranking_universe": (
            "ranked non-MLB players age 25 or younger, separately for hitters and pitchers"
        ),
        "hitters": {
            "validation": report["hitters"]["promotion"],
            "under_20": "modeled; explicit strikeout component passes supported subgroup breadth",
        },
        "pitchers": {"validation": report["pitchers"]["promotion"]},
        "public_rank_role": "joined after scoring for audit only",
        "excluded": ["playing time", "arrival", "position", "defense", "contracts"],
        "storage": storage,
    }
    (OUTPUT_ROOT / "report.json").write_text(
        json.dumps(output_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": output_report["status"],
        "hitter_top": hitters.filter(
            pl.col("prospect_peak_rate_rank").is_not_null()
        ).sort("prospect_peak_rate_rank").select(
            "prospect_peak_rate_rank", "player_name", "peak_runs_rate"
        ).head(10).to_dicts(),
        "pitcher_top": pitchers.filter(
            pl.col("prospect_peak_rate_rank").is_not_null()
        ).sort("prospect_peak_rate_rank").select(
            "prospect_peak_rate_rank", "player_name", "peak_runs_rate"
        ).head(10).to_dicts(),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
