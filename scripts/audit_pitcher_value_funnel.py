#!/usr/bin/env python3
"""Reconcile pitcher value from skill through workload and current value."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl


REPRESENTATIVE_IDS = (657277, 669373, 694973, 824620, 809254)


def _round_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            key: round(value, 6) if isinstance(value, float) else value
            for key, value in row.items()
        }
        for row in rows
    ]


def _path_summary(frame: pl.DataFrame, prefix: str) -> pl.DataFrame:
    return frame.group_by("player_id").agg(
        pl.col("mlb_active_probability").first().alias(f"{prefix}_first_active"),
        pl.col("conditional_mlb_bf").first().alias(f"{prefix}_first_conditional_bf"),
        pl.col("conditional_war_per_800_bf").first().alias(f"{prefix}_first_war_rate"),
        pl.col("expected_mlb_bf").sum().alias(f"{prefix}_six_year_expected_bf"),
        pl.col("expected_war").sum().alias(f"{prefix}_six_year_expected_war"),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument("--generated-root", type=Path, default=Path("reports/generated"))
    parser.add_argument(
        "--output-json", type=Path,
        default=Path("docs/pitcher-value-funnel-audit-result.json"),
    )
    parser.add_argument(
        "--output-md", type=Path,
        default=Path("docs/pitcher-value-funnel-audit-result.md"),
    )
    args = parser.parse_args()
    dated = args.as_of_date.isoformat()
    root = args.generated_root
    old = pl.read_parquet(
        root / "current-conditional-war-paths" / dated
        / "tables/pitcher_expected_war_paths.parquet"
    )
    corrected = pl.read_parquet(
        root / "phase2-conditional-war-paths" / dated
        / "tables/pitcher_expected_war_paths.parquet"
    )
    control = pl.read_parquet(
        root / "league-control" / dated / "league-control-snapshot.parquet"
    ).select("player_id", "mlb_debut_date")
    names = (
        pl.read_parquet(
            root / "opportunity-current-source-2026-09-08"
            / "tables/2026/full_roster_details.parquet"
        )
        .group_by("player_id")
        .agg(pl.col("player_name").first())
    )
    comparison = (
        _path_summary(old, "stale")
        .join(_path_summary(corrected, "corrected"), on="player_id", validate="1:1")
        .join(control, on="player_id", how="left", validate="1:1")
        .join(names, on="player_id", how="left", validate="1:1")
        .with_columns(
            (
                pl.col("corrected_six_year_expected_war")
                - pl.col("stale_six_year_expected_war")
            ).alias("six_year_war_change")
        )
    )
    mlb = comparison.filter(pl.col("mlb_debut_date").is_not_null())
    pre_mlb = comparison.filter(pl.col("mlb_debut_date").is_null())

    values = pl.read_parquet(
        root / "phase2-current-value" / dated / "value-records.parquet"
    ).select(
        "player_id", "expected_remaining_war", "expected_remaining_cost_dollars",
        "transferable_value_dollars", "transferable_value_lower_dollars",
        "transferable_value_upper_dollars",
    )
    representatives = (
        comparison.filter(pl.col("player_id").is_in(REPRESENTATIVE_IDS))
        .join(values, on="player_id", how="left", validate="1:1")
        .select(
            "player_id", "player_name", "mlb_debut_date",
            "stale_first_active", "corrected_first_active",
            "stale_first_conditional_bf", "corrected_first_conditional_bf",
            "corrected_first_war_rate", "stale_six_year_expected_war",
            "corrected_six_year_expected_war", "six_year_war_change",
            "expected_remaining_war", "expected_remaining_cost_dollars",
            "transferable_value_dollars", "transferable_value_lower_dollars",
            "transferable_value_upper_dollars",
        )
        .sort("player_id")
    )

    nested = pl.read_parquet(
        root / "phase2-nested-career-fv" / dated / "nested-career-model-fv.parquet"
    ).filter(
        (pl.col("model_player_type") == "pitcher")
        & pl.col("ordered_arrival_probability").is_not_null()
    )
    assumed_workload = 6.0 * (
        800.0 * pl.col("starter_probability")
        + 250.0 * pl.col("reliever_probability")
        + 450.0
        * (1.0 - pl.col("starter_probability") - pl.col("reliever_probability"))
    )
    prospect_funnel = nested.select(
        pl.len().alias("players"),
        pl.col("ordered_arrival_probability").mean().alias("mean_arrival_probability"),
        pl.col("ordered_meaningful_probability").mean().alias("mean_meaningful_probability"),
        pl.col("ordered_established_probability").mean().alias("mean_established_probability"),
        pl.col("three_tier_expected_workload").mean().alias("mean_expected_six_year_bf"),
        pl.col("pitcher_six_control_year_war_if_arrived").mean().alias(
            "mean_six_control_year_war_if_arrived"
        ),
        (
            pl.col("pitcher_six_control_year_war_if_arrived") / assumed_workload
            * 800.0
        ).mean().alias("mean_conditional_war_per_800_bf"),
        pl.col("incumbent_expected_six_year_war").sum().alias("incumbent_total_war"),
        pl.col("three_tier_expected_six_year_war").sum().alias("nested_total_war"),
        pl.col("three_tier_expected_six_year_war").max().alias("maximum_nested_war"),
        (pl.col("three_tier_expected_six_year_war") < 0).sum().alias(
            "negative_expected_war_players"
        ),
    ).row(0, named=True)

    opportunity_report = json.loads(
        (
            root / "phase2-conditional-war-paths" / dated / "report.json"
        ).read_text(encoding="utf-8")
    )
    report = {
        "report_schema_version": "0.1",
        "as_of_date": dated,
        "status": "pitcher_value_funnel_reconciled",
        "decision": {
            "mlb_workload_join": "corrected_and_kept",
            "pitcher_demographic_adjustment": "removed_from_playable_build",
            "prospect_pitcher_values": "still_not_credible_as_final_rankings",
            "manual_or_outside_fv_floor": "rejected",
        },
        "lineage": opportunity_report["opportunity_source"],
        "mlb_path_totals": {
            "players": mlb.height,
            "stale_six_year_expected_war": float(
                mlb.get_column("stale_six_year_expected_war").sum()
            ),
            "corrected_six_year_expected_war": float(
                mlb.get_column("corrected_six_year_expected_war").sum()
            ),
            "change": float(mlb.get_column("six_year_war_change").sum()),
        },
        "pre_mlb_path_totals_before_nested_hurdle": {
            "players": pre_mlb.height,
            "stale_six_year_expected_war": float(
                pre_mlb.get_column("stale_six_year_expected_war").sum()
            ),
            "corrected_six_year_expected_war": float(
                pre_mlb.get_column("corrected_six_year_expected_war").sum()
            ),
            "change": float(pre_mlb.get_column("six_year_war_change").sum()),
        },
        "prospect_pitcher_funnel": {
            key: int(value) if key in {"players", "negative_expected_war_players"}
            else float(value)
            for key, value in prospect_funnel.items()
        },
        "representative_players": _round_rows(representatives.to_dicts()),
        "method_laws": [
            "Rates and playing time are estimated separately.",
            "Sparse evidence is regressed; no unregressed small-sample leader is promoted.",
            "Chronology determines training, selection, and outer evaluation windows.",
            "All failures and zero-MLB outcomes remain in prospect evaluation.",
            "Uncertainty widens ranges and does not silently reduce the mean twice.",
            "Outside FV opinions are diagnostics only and never model features or floors.",
        ],
        "next_test": (
            "Backtest conditional MLB WAR and linked career production for historical "
            "prospect pitchers; the separate horizon audit finds the hurdle probabilities "
            "optimistic, not suppressive."
        ),
    }
    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )

    rep_lines = []
    for row in report["representative_players"]:
        if row["mlb_debut_date"] is None:
            continue
        rep_lines.append(
            f"| {row['player_name']} | {row['stale_first_active']:.3f} | "
            f"{row['corrected_first_active']:.3f} | "
            f"{row['stale_first_conditional_bf']:.0f} | "
            f"{row['corrected_first_conditional_bf']:.0f} | "
            f"{row['stale_six_year_expected_war']:.2f} | "
            f"{row['corrected_six_year_expected_war']:.2f} |"
        )
    mlb_totals = report["mlb_path_totals"]
    prospect = report["prospect_pitcher_funnel"]
    markdown = f"""# Pitcher value funnel audit

**Status:** MLB workload defect corrected; prospect pitcher ranking still provisional

The playable results were joining the older generic opportunity paths after a better
MLB workload model had already been built. The corrected chain is now
`phase2-workload-paths -> phase2-conditional-war-paths -> uncertainty -> value` and
the source model and exact input hashes are recorded. The build can now reject the
wrong opportunity model instead of silently accepting it.

Across {mlb_totals['players']:,} debuted pitchers, the correction changes projected
six-year WAR from {mlb_totals['stale_six_year_expected_war']:.1f} to
{mlb_totals['corrected_six_year_expected_war']:.1f}. This is a mean correction, not
an uncertainty bonus.

| Player | Old 2027 active | New | Old conditional BF | New | Old 6y WAR | New |
|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(rep_lines)}

The prospect problem is not fixed. Among {prospect['players']:,} pre-MLB pitchers,
the nested model now totals only {prospect['nested_total_war']:.1f} expected WAR and
its maximum is {prospect['maximum_nested_war']:.2f}. The removed age/level/hand
adjustment had a small frozen point-score gain but uncertain bootstrap evidence and
a worse left-handed subgroup; its large effect on current top prospects was not
defensible enough to keep. No manual bonus or outside FV floor replaces it.

The separate four-year horizon audit finds that the hurdle probabilities are already
optimistic, not suppressive. The next required test therefore targets conditional MLB
WAR and linked career production: forecast pitchers at historical cutoffs, retain
every failure and zero, choose any correction on earlier cohorts, and score it once
on an untouched later cohort.

## Binding statistical rules

- Skill rate and playing time remain separate.
- Sparse samples are regressed toward a relevant population.
- Model choice is time-ordered and final evaluation stays untouched.
- Failures and non-arrivals remain in the denominator.
- Wider uncertainty does not lower the mean a second time.
- Outside FV is diagnostic only.
"""
    args.output_md.write_text(markdown, encoding="utf-8")
    print(json.dumps({
        "mlb_war_change": mlb_totals["change"],
        "prospect_pitcher_nested_war": prospect["nested_total_war"],
        "representatives": len(report["representative_players"]),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
