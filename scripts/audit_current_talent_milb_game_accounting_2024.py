#!/usr/bin/env python
"""Diagnose 2024 MiLB player-game PA vs contact-evidence accounting.

This audit exists because Current Talent chronology is game-grain while the
certified Performance core profile preserves reusable physical contact evidence.
ADR 002 explicitly keeps PA and pitch/contact grains separate.  The audit does
not repair or discard evidence; it measures exactly where player-game contact
observations differ from boxscore-derived result-contact counts and where the
prototype PA-partition assumption fails.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

import build_batting_performance_level_poc as performance
import materialize_current_talent_milb_game_evidence_2024 as materializer
from universal_baseball.performance_level_config import performance_level_spec_2024


SEASON = 2024
LEVELS = ("aaa", "aa", "a+", "a", "rk")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--level", required=True, choices=LEVELS)
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("data/quarantine/current-talent-milb-accounting-audit-2024"),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/current-talent-milb-accounting-audit-2024"),
    )
    return parser.parse_args()


def _build_accounting(
    controls: pl.DataFrame,
    outcomes: pl.DataFrame,
    contacts: pl.DataFrame,
) -> pl.DataFrame:
    contact_counts = (
        contacts.group_by(["season", "league_id", "game_pk", "batter_mlbam_id"])
        .agg(
            pl.len().cast(pl.Int64).alias("observed_contact_count"),
            pl.col("at_bat_index").n_unique().cast(pl.Int64).alias("contact_sequence_count"),
            pl.col("core_bin").is_not_null().sum().cast(pl.Int64).alias("core_contact_count"),
            pl.col("at_bat_index")
            .filter(pl.col("core_bin").is_not_null())
            .n_unique()
            .cast(pl.Int64)
            .alias("core_contact_sequence_count"),
            (pl.col("contact_profile_status") == "special_bunt")
            .sum()
            .cast(pl.Int64)
            .alias("bunt_contact_count"),
            (pl.col("contact_profile_status") == "foul_air_excluded")
            .sum()
            .cast(pl.Int64)
            .alias("foul_air_excluded_count"),
            pl.col("contact_profile_status")
            .str.starts_with("unknown")
            .sum()
            .cast(pl.Int64)
            .alias("unknown_contact_count"),
        )
        .rename({"game_pk": "game_id", "batter_mlbam_id": "player_id"})
    )

    batting = outcomes.filter(
        (pl.col("game_type") == "R")
        & pl.col("batting_PA").is_not_null()
        & (pl.col("batting_PA") > 0)
    ).with_columns(pl.col("game_date").dt.year().cast(pl.Int64).alias("season"))

    control_view = controls.select(
        pl.col("game_id").cast(pl.Int64),
        pl.col("player_id").cast(pl.Int64),
        pl.col("expected_contact_count").cast(pl.Int64),
    )

    joined = (
        batting.join(control_view, on=["game_id", "player_id"], how="left")
        .join(
            contact_counts,
            on=["season", "league_id", "game_id", "player_id"],
            how="left",
        )
        .with_columns(
            *[
                pl.col(column).fill_null(0).cast(pl.Int64)
                for column in (
                    "observed_contact_count",
                    "contact_sequence_count",
                    "core_contact_count",
                    "core_contact_sequence_count",
                    "bunt_contact_count",
                    "foul_air_excluded_count",
                    "unknown_contact_count",
                )
            ]
        )
    )

    return (
        joined.with_columns(
            (
                pl.col("batting_AB")
                - pl.col("batting_SO")
                + pl.col("batting_SF")
                + pl.col("batting_SH")
            ).alias("derived_expected_contact_count"),
            (
                pl.col("batting_PA")
                - pl.col("batting_AB")
                - pl.col("batting_BB")
                - pl.col("batting_HBP")
                - pl.col("batting_SF")
                - pl.col("batting_SH")
                - pl.col("batting_CI")
            ).alias("pa_identity_residual"),
            (pl.col("observed_contact_count") - pl.col("expected_contact_count")).alias(
                "contact_count_residual"
            ),
            (pl.col("contact_sequence_count") - pl.col("expected_contact_count")).alias(
                "contact_sequence_residual"
            ),
            (pl.col("observed_contact_count") - pl.col("contact_sequence_count")).alias(
                "multi_contact_row_excess"
            ),
            (pl.col("core_contact_count") - pl.col("core_contact_sequence_count")).alias(
                "multi_core_contact_row_excess"
            ),
            (
                pl.col("batting_BB")
                + pl.col("batting_HBP")
                + pl.col("batting_SO")
                + pl.col("core_contact_count")
                + pl.col("bunt_contact_count")
                + pl.col("foul_air_excluded_count")
                + pl.col("batting_CI")
                - pl.col("batting_PA")
            ).alias("prototype_pa_overage"),
        )
        .sort(
            ["prototype_pa_overage", "contact_count_residual", "multi_contact_row_excess"],
            descending=[True, True, True],
        )
    )


def main() -> int:
    args = parse_args()
    spec = performance_level_spec_2024(args.level)
    work_dir = args.work_root / args.level
    report_dir = args.report_root / args.level
    work_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    source_contacts, _ = performance._load_reusable_contacts(
        args.level, spec.league_ids, work_dir
    )
    controls, control_metrics = materializer._load_contact_controls(
        level=args.level,
        work_dir=work_dir,
        league_ids=spec.league_ids,
    )
    authorized, authority_metrics = materializer._apply_sequence_participant_authority(
        source_contacts,
        controls,
    )
    classified = performance._classify_contacts(authorized)
    outcomes, outcome_metrics = materializer._load_current_outcomes(
        level=args.level,
        work_dir=work_dir,
        league_ids=spec.league_ids,
    )

    accounting = _build_accounting(controls, outcomes, classified)
    anomalies = accounting.filter(
        (pl.col("prototype_pa_overage") > 0)
        | (pl.col("contact_count_residual") != 0)
        | (pl.col("pa_identity_residual") != 0)
        | (pl.col("multi_contact_row_excess") != 0)
    )
    overages = accounting.filter(pl.col("prototype_pa_overage") > 0)

    metrics = {
        "season": SEASON,
        "filename_level": args.level,
        "level_group": spec.level_group,
        "player_game_count": accounting.height,
        "anomaly_player_game_count": anomalies.height,
        "prototype_pa_overage_player_game_count": overages.height,
        "positive_contact_residual_player_game_count": accounting.filter(
            pl.col("contact_count_residual") > 0
        ).height,
        "negative_contact_residual_player_game_count": accounting.filter(
            pl.col("contact_count_residual") < 0
        ).height,
        "nonzero_contact_sequence_residual_player_game_count": accounting.filter(
            pl.col("contact_sequence_residual") != 0
        ).height,
        "multi_contact_row_player_game_count": accounting.filter(
            pl.col("multi_contact_row_excess") > 0
        ).height,
        "multi_core_contact_row_player_game_count": accounting.filter(
            pl.col("multi_core_contact_row_excess") > 0
        ).height,
        "pa_identity_residual_player_game_count": accounting.filter(
            pl.col("pa_identity_residual") != 0
        ).height,
        "sum_contact_count_residual": int(accounting.get_column("contact_count_residual").sum() or 0),
        "sum_contact_sequence_residual": int(
            accounting.get_column("contact_sequence_residual").sum() or 0
        ),
        "sum_multi_contact_row_excess": int(
            accounting.get_column("multi_contact_row_excess").sum() or 0
        ),
        "sum_multi_core_contact_row_excess": int(
            accounting.get_column("multi_core_contact_row_excess").sum() or 0
        ),
        "sum_pa_identity_residual": int(accounting.get_column("pa_identity_residual").sum() or 0),
        "max_prototype_pa_overage": int(accounting.get_column("prototype_pa_overage").max() or 0),
        "max_contact_count_residual": int(accounting.get_column("contact_count_residual").max() or 0),
        "min_contact_count_residual": int(accounting.get_column("contact_count_residual").min() or 0),
        "contact_control_resolution": control_metrics,
        "participant_authority": authority_metrics,
        "outcome_resolution": outcome_metrics,
        "interpretation": (
            "Diagnostic only. PA counts and reusable contact observations remain separate evidence grains; "
            "no rows are clipped, dropped, or reassigned by this audit."
        ),
    }

    anomalies.write_csv(report_dir / "accounting_anomalies.csv")
    overages.write_csv(report_dir / "prototype_pa_overages.csv")
    (report_dir / "report.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True), encoding="utf-8"
    )

    top_columns = [
        "game_id",
        "player_id",
        "batting_PA",
        "expected_contact_count",
        "observed_contact_count",
        "contact_sequence_count",
        "core_contact_count",
        "bunt_contact_count",
        "foul_air_excluded_count",
        "batting_BB",
        "batting_HBP",
        "batting_SO",
        "batting_CI",
        "pa_identity_residual",
        "contact_count_residual",
        "contact_sequence_residual",
        "multi_contact_row_excess",
        "prototype_pa_overage",
    ]
    print(f"# {SEASON} Current Talent accounting audit — {spec.display_name}")
    print(json.dumps({k: v for k, v in metrics.items() if isinstance(v, (int, str))}, indent=2))
    print("\nTop PA-overage/anomaly rows:")
    print(anomalies.select(top_columns).head(25))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
