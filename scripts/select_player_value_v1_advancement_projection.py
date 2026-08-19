#!/usr/bin/env python
"""Run the predeclared MLB non-steal advancement projection selection gate."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import requests

from universal_baseball.player_value_advancement_projection import (
    CONFIRMATION_YEAR,
    DEVELOPMENT_YEARS,
    AdvancementCandidate,
    PlayerSeasonAdvancementSummary,
    advancement_candidates,
    confirmation_passes,
    score_all_candidates,
    score_candidate,
    select_development_candidate,
)
from universal_baseball.player_value_baserunning_sources import (
    SAVANT_BASERUNNING_RUN_VALUE_URL,
    audit_savant_baserunning_rows,
    parse_savant_baserunning_csv,
    savant_baserunning_query_params,
)


SOURCE_SEASONS = (2019, 2020, 2021, 2022, 2023, 2024)


def _candidate_by_id(candidate_id: str) -> AdvancementCandidate:
    matches = [
        candidate
        for candidate in advancement_candidates()
        if candidate.candidate_id == candidate_id
    ]
    if len(matches) != 1:
        raise ValueError(f"unknown advancement candidate: {candidate_id}")
    return matches[0]


def _certified_hashes(path: Path) -> dict[int, str]:
    payload = json.loads(path.read_text())
    source = payload.get("mlb_statcast_advancement") or {}
    if not source.get("all_audited_seasons_usable"):
        raise ValueError("certified Savant advancement source audit is not usable")
    captures = source.get("captures") or []
    hashes = {
        int(capture["season"]): str(capture["response_sha256"])
        for capture in captures
    }
    missing = sorted(set(SOURCE_SEASONS) - set(hashes))
    if missing:
        raise ValueError(
            f"certified Savant advancement audit missing source seasons: {missing}"
        )
    return hashes


def _fetch_season(
    session: requests.Session,
    *,
    season: int,
    certified_sha256: str,
) -> tuple[list[PlayerSeasonAdvancementSummary], dict[str, Any], dict[str, Any]]:
    response = session.get(
        SAVANT_BASERUNNING_RUN_VALUE_URL,
        params=savant_baserunning_query_params(season),
        timeout=60,
    )
    response.raise_for_status()
    response_sha256 = hashlib.sha256(response.content).hexdigest()
    if response_sha256 != certified_sha256:
        raise ValueError(
            "Savant advancement response changed since source certification "
            f"for {season}: certified={certified_sha256}, live={response_sha256}"
        )

    rows = parse_savant_baserunning_csv(response.content.decode("utf-8-sig"))
    audit = audit_savant_baserunning_rows(rows)
    if not audit["advancement_source_usable"]:
        raise ValueError(f"Savant advancement source failed selection audit for {season}")

    summaries = [
        PlayerSeasonAdvancementSummary(
            player_id=int(float(row["player_id"])),
            season=season,
            runs_xb=float(row["runner_runs_xb"]),
            opportunities_xb=float(row["n_runner_moved_xb"]),
        )
        for row in rows
    ]
    capture = {
        "season": season,
        "requested_url": response.url,
        "response_sha256": response_sha256,
        "response_bytes": len(response.content),
        "row_count": len(rows),
    }
    return summaries, audit, capture


def _score_payload(score) -> dict[str, Any]:
    return asdict(score)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-audit",
        type=Path,
        default=Path("docs/player-value-v1-baserunning-source-audit-result.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "docs/player-value-v1-advancement-projection-selection-result.json"
        ),
    )
    args = parser.parse_args()

    certified_hashes = _certified_hashes(args.source_audit)
    summaries: list[PlayerSeasonAdvancementSummary] = []
    source_audits: dict[str, Any] = {}
    captures: list[dict[str, Any]] = []

    with requests.Session() as session:
        session.headers.setdefault(
            "User-Agent",
            "universal-baseball-model-player-value-advancement-selection/0.1",
        )
        for season in SOURCE_SEASONS:
            season_rows, audit, capture = _fetch_season(
                session,
                season=season,
                certified_sha256=certified_hashes[season],
            )
            summaries.extend(season_rows)
            source_audits[str(season)] = audit
            captures.append(capture)

    development_scores = score_all_candidates(
        summaries,
        target_years=DEVELOPMENT_YEARS,
    )
    selection = select_development_candidate(development_scores)

    baseline_2024 = score_candidate(
        summaries,
        _candidate_by_id("A0_neutral"),
        target_years=(CONFIRMATION_YEAR,),
    )
    confirmation_scores = [baseline_2024]
    if selection.selected_candidate_id != "A0_neutral":
        confirmation_scores.append(
            score_candidate(
                summaries,
                _candidate_by_id(selection.selected_candidate_id),
                target_years=(CONFIRMATION_YEAR,),
            )
        )
    confirmed = confirmation_passes(
        selection.selected_candidate_id,
        confirmation_scores,
    )
    frozen_candidate_id = (
        selection.selected_candidate_id
        if selection.development_passed and confirmed
        else "A0_neutral"
    )

    reference_rows = [
        row for row in summaries if row.season == CONFIRMATION_YEAR
    ]
    reference_opportunities = sum(row.opportunities_xb for row in reference_rows)
    reference_runs = sum(row.runs_xb for row in reference_rows)
    payload = {
        "status": "player_value_v1_advancement_projection_selection_completed",
        "verified_source_commit": str(os.environ.get("GITHUB_SHA") or "").strip()
        or None,
        "contracts": [
            "docs/player-value-v1-baserunning-source-audit-contract.md",
            "docs/player-value-v1-advancement-projection-selection-contract.md",
        ],
        "source_seasons": list(SOURCE_SEASONS),
        "development_target_seasons": list(DEVELOPMENT_YEARS),
        "confirmation_target_season": CONFIRMATION_YEAR,
        "source": {
            "provider": "Baseball Savant",
            "endpoint": SAVANT_BASERUNNING_RUN_VALUE_URL,
            "certified_audit": str(args.source_audit),
            "captures": captures,
            "season_audits": source_audits,
            "player_season_row_count": len(summaries),
            "scoreable_rows_by_season": {
                str(season): sum(
                    1
                    for row in summaries
                    if row.season == season and row.opportunities_xb > 0
                )
                for season in SOURCE_SEASONS
            },
        },
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
        "confirmation_candidate_ids_inspected": [
            score.candidate_id for score in confirmation_scores
        ],
        "frozen_candidate_id": frozen_candidate_id,
        "mlb_2024_advancement_reference": {
            "runner_row_count": len(reference_rows),
            "nonsteal_advancement_opportunities": reference_opportunities,
            "nonsteal_advancement_runs": reference_runs,
            "observed_runs_per_opportunity": (
                reference_runs / reference_opportunities
                if reference_opportunities > 0
                else None
            ),
            "note": (
                "Final production opportunity rate per MLB PA remains a separate "
                "post-selection materialization using the certified MLB PA reference."
            ),
        },
        "firewall": {
            "all_candidate_target_seasons": list(DEVELOPMENT_YEARS),
            "confirmation_only_scores_a0_and_preselected_winner": True,
            "confirmation_alternatives_inspected": False,
            "uses_2025_for_selection": False,
            "live_source_hashes_required_to_match_certified_audit": True,
        },
        "notes": [
            "This gate tests persistence of source-defined non-steal advancement run value; it does not refit Statcast's event model.",
            "Realized target advancement opportunities are used only as retrospective scoring exposure.",
            "MiLB-only players remain neutral for this channel unless a separately certified translation is later predeclared.",
        ],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
