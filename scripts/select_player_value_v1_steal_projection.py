#!/usr/bin/env python
"""Run the predeclared portable steal projection selection and confirmation gate."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
from typing import Any

import requests

from universal_baseball.player_value_steal_data import build_loo_player_season_summaries
from universal_baseball.player_value_steal_projection import (
    CONFIRMATION_YEAR,
    DEVELOPMENT_YEARS,
    StealCandidate,
    confirmation_passes,
    score_all_candidates,
    score_candidate,
    select_development_candidate,
    steal_candidates,
)
from universal_baseball.player_value_steal_sources import (
    fetch_milb_steal_stints,
    fetch_mlb_steal_stints,
    full_mlb_reference_steal_rates,
)


SOURCE_SEASONS = (2019, 2020, 2021, 2022, 2023, 2024)


def _candidate_by_id(candidate_id: str) -> StealCandidate:
    matches = [candidate for candidate in steal_candidates() if candidate.candidate_id == candidate_id]
    if len(matches) != 1:
        raise ValueError(f"unknown steal candidate: {candidate_id}")
    return matches[0]


def _score_payload(score) -> dict[str, Any]:
    return asdict(score)


def _run_channel(rows, channel: str) -> dict[str, Any]:
    development_scores = score_all_candidates(
        rows,
        channel=channel,  # type: ignore[arg-type]
        target_years=DEVELOPMENT_YEARS,
    )
    selection = select_development_candidate(
        development_scores,
        channel=channel,  # type: ignore[arg-type]
    )

    baseline_candidate = _candidate_by_id("B0_neutral")
    baseline_2024 = score_candidate(
        rows,
        baseline_candidate,
        channel=channel,  # type: ignore[arg-type]
        target_years=(CONFIRMATION_YEAR,),
    )
    confirmation_scores = [baseline_2024]
    if selection.selected_candidate_id != "B0_neutral":
        selected_candidate = _candidate_by_id(selection.selected_candidate_id)
        confirmation_scores.append(
            score_candidate(
                rows,
                selected_candidate,
                channel=channel,  # type: ignore[arg-type]
                target_years=(CONFIRMATION_YEAR,),
            )
        )

    confirmed, confirmation_reversals = confirmation_passes(
        selection.selected_candidate_id,
        confirmation_scores,
    )
    frozen_candidate_id = (
        selection.selected_candidate_id
        if selection.development_passed and confirmed
        else "B0_neutral"
    )
    return {
        "channel": channel,
        "development_scores": [
            _score_payload(score)
            for score in sorted(
                development_scores,
                key=lambda value: value.candidate_id,
            )
        ],
        "development_selection": asdict(selection),
        "confirmation_scores": [
            _score_payload(score)
            for score in sorted(
                confirmation_scores,
                key=lambda value: value.candidate_id,
            )
        ],
        "confirmation_passed": confirmed,
        "confirmation_catastrophic_tier_reversals": list(confirmation_reversals),
        "frozen_candidate_id": frozen_candidate_id,
        "confirmation_candidate_ids_inspected": [
            score.candidate_id for score in confirmation_scores
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/player-value-v1-steal-projection-selection-result.json"),
    )
    args = parser.parse_args()

    with requests.Session() as session:
        session.headers.setdefault(
            "User-Agent", "universal-baseball-model-player-value-steal-selection/0.1"
        )
        mlb_stints, mlb_captures = fetch_mlb_steal_stints(
            SOURCE_SEASONS,
            session=session,
        )
        milb_stints, milb_captures = fetch_milb_steal_stints(
            SOURCE_SEASONS,
            session=session,
        )

    stints = [*mlb_stints, *milb_stints]
    summaries, environment_audit = build_loo_player_season_summaries(stints)

    summary_counts_by_season = {
        str(season): sum(1 for row in summaries if row.season == season)
        for season in SOURCE_SEASONS
    }
    summary_counts_by_tier = {
        tier: sum(1 for row in summaries if row.tier == tier)
        for tier in sorted({row.tier for row in summaries})
    }

    attempt = _run_channel(summaries, "attempt")
    success = _run_channel(summaries, "success")
    reference = full_mlb_reference_steal_rates(mlb_stints, season=CONFIRMATION_YEAR)

    payload = {
        "status": "player_value_v1_steal_projection_selection_completed",
        "verified_source_commit": str(os.environ.get("GITHUB_SHA") or "").strip() or None,
        "contracts": [
            "docs/player-value-v1-baserunning-source-audit-contract.md",
            "docs/player-value-v1-steal-projection-selection-contract.md",
            "docs/player-value-v1-steal-projection-diagnostic-thresholds.md",
        ],
        "source_seasons": list(SOURCE_SEASONS),
        "development_target_seasons": list(DEVELOPMENT_YEARS),
        "confirmation_target_season": CONFIRMATION_YEAR,
        "source": {
            "mlb_stint_row_count": len(mlb_stints),
            "milb_stint_row_count": len(milb_stints),
            "mlb_captures": mlb_captures,
            "milb_captures": milb_captures,
            "player_season_summary_count": len(summaries),
            "player_season_summary_counts_by_season": summary_counts_by_season,
            "player_season_summary_counts_by_dominant_tier": summary_counts_by_tier,
            "environment_audit": asdict(environment_audit),
        },
        "attempt_propensity": attempt,
        "success_skill": success,
        "mlb_2024_full_population_reference": reference,
        "firewall": {
            "all_candidate_target_seasons": list(DEVELOPMENT_YEARS),
            "confirmation_alternatives_inspected": False,
            "confirmation_only_scores_b0_and_preselected_winner": True,
            "uses_2025_for_selection": False,
        },
        "notes": [
            "Target-year environment baselines are leave-one-player-out; production reference rates are full-population MLB aggregates.",
            "The portable opportunity denominator is 1B + BB + HBP - IBB and is not claimed to equal Statcast pitch-level steal opportunities.",
            "This gate selects portable steal behavior only; final steal run weights and non-steal advancement remain open.",
        ],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
