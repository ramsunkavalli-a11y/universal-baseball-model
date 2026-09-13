#!/usr/bin/env python3
"""Build six-calendar-year prospect outcome distributions without calling them control."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

from materialize_prospect_hitter_comparables import (
    _history_stats,
    _outcomes as hitter_outcomes,
    _validation_summary,
)
from materialize_prospect_pitcher_comparables import _outcomes as pitcher_outcomes
from universal_baseball.prospect_arrival import build_arrival_cohort
from universal_baseball.prospect_historical_comparables import (
    DEFAULT_COMPARABLES,
    primary_exact_level,
    score_hitter_comparables,
    score_pitcher_comparables,
)
from universal_baseball.storage import write_canonical_parquet


HORIZON = 6
ORIGINS = (2018, 2019)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/prospect-historical-comparables"),
    )
    return parser.parse_args()


def _rename_horizon(frame: pl.DataFrame) -> pl.DataFrame:
    return frame.rename({column: column.replace("_4y", "_6y") for column in frame.columns if "_4y" in column})


def main() -> int:
    args = _args()
    generated = Path("reports/generated")
    history_root = generated / "opportunity-history-sources-v2/tables"
    stats = _history_stats(history_root)
    membership = pl.read_parquet(
        generated / "opportunity-40man-history/tables/historical_40man_membership.parquet"
    )
    demographics = pl.read_parquet(
        generated / "player-demographics/tables/player-demographics.parquet"
    )
    debut = pl.read_parquet(
        generated / "career-mlb-outcome-inventory-2009-2025/tables/people-debut-dates.parquet"
    )
    runs_per_win = float(
        json.loads(Path("docs/prospect-component-uncertainty-result.json").read_text())[
            "runs_per_win"
        ]
    )
    output = args.output_root / args.as_of_date.isoformat()
    output.mkdir(parents=True, exist_ok=True)
    reports: dict[str, object] = {}
    for player_type in ("hitter", "pitcher"):
        hitter = player_type == "hitter"
        exposure = "plate_appearances" if hitter else "batters_faced"
        snapshots = pl.read_parquet(
            history_root / ("hitter_snapshots.parquet" if hitter else "pitcher_snapshots.parquet")
        )
        skill = pl.read_parquet(
            generated / "phase2-arrival-skill-source/tables"
            / ("affiliated_hitting_components.parquet" if hitter else "affiliated_pitching_components.parquet")
        )
        outcomes_source = pl.read_parquet(
            generated / "career-mlb-outcome-inventory-2009-2025/tables"
            / ("mlb_hitting_components_2009_2025.parquet" if hitter else "mlb_pitching_2009_2025.parquet")
        )
        outcome_builder = hitter_outcomes if hitter else pitcher_outcomes
        scorer = score_hitter_comparables if hitter else score_pitcher_comparables
        rate_basis = 600.0 if hitter else 800.0
        cohorts: dict[int, pl.DataFrame] = {}
        for origin in ORIGINS:
            cohort = build_arrival_cohort(
                snapshots,
                stats,
                membership,
                skill,
                debut,
                snapshot_year=origin,
                horizon=HORIZON,
                player_type=player_type,
                demographics=demographics,
            )
            cohorts[origin] = (
                cohort.join(
                    primary_exact_level(skill, season=origin, exposure=exposure),
                    on="player_id",
                    how="left",
                    validate="1:1",
                )
                .with_columns(
                    pl.col("primary_level_group").fill_null(pl.col("primary_level_tier")),
                    pl.col("primary_exact_level_workload_share").fill_null(
                        pl.col("primary_level_workload_share")
                    ),
                )
                .join(
                    outcome_builder(
                        cohort,
                        outcomes_source,
                        origin=origin,
                        runs_per_win=runs_per_win,
                        horizon=HORIZON,
                    ),
                    on="player_id",
                    how="left",
                    validate="1:1",
                )
                .with_columns(
                    pl.col("later_component_war").fill_null(0.0),
                    pl.col("later_mlb_workload").fill_null(0.0),
                    pl.lit(origin).alias("origin_year"),
                )
            )
        validation_reference = cohorts[2018].join(
            cohorts[2019].select("player_id"), on="player_id", how="anti"
        )
        validation = scorer(
            validation_reference,
            cohorts[2019],
            comparable_count=DEFAULT_COMPARABLES,
        ).join(
            cohorts[2019].select(
                "player_id", "later_component_war", "later_mlb_workload"
            ),
            on="player_id",
            validate="1:1",
        )
        reference = (
            pl.concat([cohorts[2018], cohorts[2019]], how="vertical_relaxed")
            .sort(["player_id", "origin_year"])
            .unique("player_id", keep="last", maintain_order=True)
        )
        current = pl.read_parquet(
            generated / "phase2-prospect-arrival" / args.as_of_date.isoformat()
            / f"{player_type}-arrival-probabilities.parquet"
        )
        current_skill = pl.read_parquet(
            generated / "affiliated-skill-source/tables"
            / ("affiliated_hitting_components.parquet" if hitter else "affiliated_pitching_components.parquet")
        )
        current = (
            current.join(
                primary_exact_level(
                    current_skill, season=args.as_of_date.year, exposure=exposure
                ),
                on="player_id",
                how="left",
                validate="1:1",
            )
            .with_columns(
                pl.col("primary_level_group").fill_null(pl.col("primary_level_tier")),
                pl.col("primary_exact_level_workload_share").fill_null(
                    pl.col("primary_level_workload_share")
                ),
            )
        )
        scored = _rename_horizon(scorer(reference, current))
        write_canonical_parquet(
            scored,
            output / f"{player_type}-comparables-6y.parquet",
            table_name=f"prospect_{player_type}_historical_comparables_6y",
        )
        reports[player_type] = {
            "reference_players": reference.height,
            "diagnostic_players": validation.height,
            "retrospective_diagnostic": _validation_summary(
                validation, validation_reference, rate_basis=rate_basis
            ),
        }
    report = {
        "as_of_date": args.as_of_date.isoformat(),
        "status": "six_calendar_year_partial_war_diagnostic_rejected",
        "decision": "do_not_promote",
        "chronology_safe_validation": False,
        "chronology_note": (
            "The reference outcome window overlaps the diagnostic target origin. "
            "This is an optimistic retrospective diagnostic, not a held-out gate."
        ),
        "horizon_calendar_years": HORIZON,
        "reference_origins": list(ORIGINS),
        "nonarrivals_scored_zero": True,
        "one_row_per_reference_player": True,
        "outside_fv_used": False,
        "player_types": reports,
    }
    (output / "six-year-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    Path("docs/prospect-six-calendar-year-comparables-result.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
