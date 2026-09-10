#!/usr/bin/env python3
"""Choose a simple destination rule after validated fringe advancement."""

from __future__ import annotations

import json
from math import log
from pathlib import Path

import polars as pl

from audit_prospect_post_arrival_workload import _rows


OUTPUT_JSON = Path("docs/prospect-post-arrival-destination-result.json")
OUTPUT_MD = Path("docs/prospect-post-arrival-destination-result.md")


def _advanced_rows() -> pl.DataFrame:
    return pl.concat(
        [
            _rows(player_type)
            .filter(
                (pl.col("from_state") == "FRINGE_MLB")
                & (pl.col("advanced") == 1)
            )
            .select(
                "player_id",
                "outcome_year",
                "to_state",
                pl.lit(player_type).alias("player_type"),
            )
            for player_type in ("hitter", "pitcher")
        ],
        how="vertical",
    ).with_columns(
        (pl.col("to_state") == "ESTABLISHED_MLB")
        .cast(pl.Int64)
        .alias("direct_established")
    )


def _probability(frame: pl.DataFrame) -> float:
    # Jeffreys smoothing prevents an unsupported 0 or 1 probability.
    return (float(frame["direct_established"].sum()) + 0.5) / (frame.height + 1.0)


def _score(frame: pl.DataFrame, probabilities: dict[str, float] | float) -> dict[str, float | int]:
    rows = []
    for row in frame.iter_rows(named=True):
        probability = (
            float(probabilities[row["player_type"]])
            if isinstance(probabilities, dict)
            else float(probabilities)
        )
        target = int(row["direct_established"])
        rows.append(
            {
                "log_loss": -log(probability if target else 1.0 - probability),
                "brier": (probability - target) ** 2,
            }
        )
    losses = pl.DataFrame(rows)
    return {
        "players": frame.height,
        "direct_established": int(frame["direct_established"].sum()),
        "log_loss": float(losses["log_loss"].mean()),
        "brier": float(losses["brier"].mean()),
    }


def main() -> int:
    rows = _advanced_rows()
    folds = []
    for outcome_year in (2023, 2024, 2025):
        training = rows.filter(pl.col("outcome_year") < outcome_year)
        evaluation = rows.filter(pl.col("outcome_year") == outcome_year)
        pooled = _probability(training)
        by_type = {
            player_type: _probability(training.filter(pl.col("player_type") == player_type))
            for player_type in ("hitter", "pitcher")
        }
        pooled_score = _score(evaluation, pooled)
        split_score = _score(evaluation, by_type)
        folds.append(
            {
                "outcome_year": outcome_year,
                "training_players": training.height,
                "pooled_probability": pooled,
                "player_type_probabilities": by_type,
                "pooled": pooled_score,
                "player_type_split": split_score,
                "split_minus_pooled": {
                    metric: float(split_score[metric]) - float(pooled_score[metric])
                    for metric in ("log_loss", "brier")
                },
            }
        )
    split_passed = all(
        fold["split_minus_pooled"][metric] < 0
        for fold in folds
        for metric in ("log_loss", "brier")
    )
    final_pooled = _probability(rows)
    report = {
        "report_schema_version": "0.1",
        "status": "post_arrival_destination_test_complete",
        "plan": "docs/prospect-post-arrival-destination-plan.md",
        "current_2026_used": False,
        "shortened_2020_outcomes_excluded": True,
        "rows": rows.height,
        "support": rows.group_by("player_type", "to_state").len().sort(
            "player_type", "to_state"
        ).to_dicts(),
        "folds": folds,
        "decision": (
            "use_player_type_destination_split"
            if split_passed
            else "retain_pooled_destination_probability"
        ),
        "selected_direct_established_probability": (
            {
                player_type: _probability(rows.filter(pl.col("player_type") == player_type))
                for player_type in ("hitter", "pitcher")
            }
            if split_passed
            else final_pooled
        ),
        "production_changed": False,
    }
    OUTPUT_JSON.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    fold_lines = "\n".join(
        f"| {fold['outcome_year']} | {fold['pooled']['players']} | "
        f"{fold['split_minus_pooled']['log_loss']:+.6f} | "
        f"{fold['split_minus_pooled']['brier']:+.6f} |"
        for fold in folds
    )
    OUTPUT_MD.write_text(
        f"""# Post-arrival advancement destination result

Status: research test complete; no current value changed.

Among {rows.height} observed fringe-to-higher advances, this test asks whether the
chance of jumping directly to established should differ for hitters and pitchers.
Negative score differences favor the player-type split.

| Outcome year | Advances | Split minus pooled log loss | Split minus pooled Brier |
|---:|---:|---:|---:|
{fold_lines}

Decision: **{report['decision'].replace('_', ' ')}**. The final pooled direct-to-
established probability is {final_pooled:.1%}. This rule applies only after a separate
advancement draw succeeds. It is a simulator input, not a current ranking adjustment.
""",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
