#!/usr/bin/env python3
"""Compare the linked pitcher career-path challenger with the current simulation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.storage import sha256_file


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--incumbent",
        type=Path,
        default=Path(
            "reports/generated/phase2-dependent-career-value/2026-09-08/dependent-career-value.parquet"
        ),
    )
    parser.add_argument(
        "--challenger",
        type=Path,
        default=Path(
            "reports/generated/phase2-dependent-career-value-linked-pitcher/2026-09-08/dependent-career-value.parquet"
        ),
    )
    parser.add_argument(
        "--pooled-challenger",
        type=Path,
        default=Path(
            "reports/generated/phase2-dependent-career-value-linked-pitcher-pooled/"
            "2026-09-08/dependent-career-value.parquet"
        ),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("docs/dependent-career-linked-pitcher-audit-result.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/dependent-career-linked-pitcher-audit-result.md"),
    )
    args = parser.parse_args()
    incumbent = pl.read_parquet(args.incumbent)
    challenger = pl.read_parquet(args.challenger)
    pooled = pl.read_parquet(args.pooled_challenger)
    joined = (
        incumbent.join(
            challenger,
            on=["player_id", "model_player_type"],
            how="inner",
            validate="1:1",
            suffix="_linked",
        )
        .join(
            pooled,
            on=["player_id", "model_player_type"],
            how="inner",
            validate="1:1",
            suffix="_pooled",
        )
        .filter(pl.col("model_player_type") == "pitcher")
    )
    if (
        joined.height
        != incumbent.filter(pl.col("model_player_type") == "pitcher").height
    ):
        raise ValueError("linked challenger does not cover every incumbent pitcher")

    old_war = float(joined["mean_controlled_war"].sum())
    new_war = float(joined["mean_controlled_war_linked"].sum())
    old_value = float(joined["mean_discounted_surplus_value_dollars"].sum())
    new_value = float(joined["mean_discounted_surplus_value_dollars_linked"].sum())
    pooled_war = float(joined["mean_controlled_war_pooled"].sum())
    pooled_value = float(joined["mean_discounted_surplus_value_dollars_pooled"].sum())
    rank_correlation = float(
        np.corrcoef(
            joined["mean_discounted_surplus_value_dollars"].rank().to_numpy(),
            joined["mean_discounted_surplus_value_dollars_linked"].rank().to_numpy(),
        )[0, 1]
    )
    value_counts = {
        str(threshold): joined.filter(
            pl.col("mean_discounted_surplus_value_dollars_linked") >= threshold
        ).height
        for threshold in (5_000_000, 10_000_000, 15_000_000, 20_000_000)
    }
    report = {
        "report_schema_version": 1,
        "status": "scale_challenger_ready_not_promoted",
        "pitchers": joined.height,
        "incumbent_total_expected_controlled_war": old_war,
        "linked_total_expected_controlled_war": new_war,
        "war_ratio": new_war / old_war,
        "incumbent_total_expected_value_dollars": old_value,
        "linked_total_expected_value_dollars": new_value,
        "pooled_total_expected_controlled_war": pooled_war,
        "pooled_total_expected_value_dollars": pooled_value,
        "value_ratio": new_value / old_value,
        "incumbent_p99_expected_war": float(
            joined["mean_controlled_war"].quantile(0.99)
        ),
        "linked_p99_expected_war": float(
            joined["mean_controlled_war_linked"].quantile(0.99)
        ),
        "pooled_p99_expected_war": float(
            joined["mean_controlled_war_pooled"].quantile(0.99)
        ),
        "mean_six_year_arrival_probability": float(
            joined["arrival_probability"].mean()
        ),
        "mean_established_probability": float(joined["regular_probability"].mean()),
        "value_rank_correlation": rank_correlation,
        "linked_value_threshold_counts": value_counts,
        "decision": "do_not_promote_before_fresh_confirmation_and_incumbent_replay",
        "replay_requirement": (
            "The first cutoff-safe 2021 development replay is complete. Next compare "
            "the pooled challenger with a reconstructed incumbent on identical rows "
            "and reserve a later cohort for fresh confirmation."
        ),
        "limits": [
            "The six-year constant-hazard arrival probabilities are already known to be optimistic.",
            "Individual prospect conditional quality did not beat a population mean, so challenger ordering is mostly hurdle and role probability.",
            "This current-date sensitivity is not predictive validation.",
            "No outside FV opinion or 2026 partial outcome was used.",
        ],
        "model_effect": "none",
        "sources": {
            args.incumbent.as_posix(): sha256_file(args.incumbent),
            args.challenger.as_posix(): sha256_file(args.challenger),
            args.pooled_challenger.as_posix(): sha256_file(args.pooled_challenger),
        },
    }
    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    markdown = f"""# Linked pitcher career-path challenger

Status: **not promoted**; current rankings and values are unchanged.

The challenger samples annual pitcher performance, workload and role from the same
historical career instead of applying one current prospect rate to every simulated
season.

| Measure | Current | Tier-linked | Arrival-only pooled |
|---|---:|---:|---:|
| Pitcher prospects | {joined.height:,} | {joined.height:,} | {joined.height:,} |
| Total expected controlled WAR | {old_war:,.1f} | {new_war:,.1f} | {pooled_war:,.1f} |
| 99th percentile player WAR | {report["incumbent_p99_expected_war"]:.2f} | {report["linked_p99_expected_war"]:.2f} | {report["pooled_p99_expected_war"]:.2f} |
| Total expected value | ${old_value / 1e9:.2f}B | ${new_value / 1e9:.2f}B | ${pooled_value / 1e9:.2f}B |

This repairs the implausibly compressed scale, but the change is too large to accept
without replay: total pitcher-prospect WAR rises {report["war_ratio"]:.1f} times and
rank correlation is only {rank_correlation:.3f}. The current hurdle averages
{report["mean_six_year_arrival_probability"]:.1%} arrival and
{report["mean_established_probability"]:.1%} established; its long-horizon form is
already known to overpredict. Because player-specific conditional quality failed its
own later test, this ordering is driven mainly by hurdle and role probabilities.
The replay did not show that tier splitting beats the simpler arrival-only pool, so
neither challenger is promoted.

The cutoff-specific 2021 development replay is now complete: the broad linked scale is
plausible, but the tier split did not beat the simpler pool. Next compare that pooled
challenger with a reconstructed incumbent on identical rows and reserve a later cohort
for fresh confirmation. Until then, no player value or rank changes.
"""
    args.output_md.write_text(markdown, encoding="utf-8")
    print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
