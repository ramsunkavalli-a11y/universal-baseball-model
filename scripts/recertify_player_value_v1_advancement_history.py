#!/usr/bin/env python
"""Freeze model-relevant advancement history after immaterial source drift."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Iterable

import polars as pl
import requests

from universal_baseball.player_value_advancement_projection import (
    AdvancementCandidateScore,
    PlayerSeasonAdvancementSummary,
    advancement_candidates,
    canonical_advancement_model_input_sha256,
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
DEVELOPMENT_YEARS = (2022, 2023)
CONFIRMATION_YEAR = 2024
FROZEN_CANDIDATE_ID = "A2_k25"
BASELINE_CANDIDATE_ID = "A0_neutral"
MAX_RELATIVE_SCORE_DRIFT = 0.001


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def relative_score_drift(current: float, frozen: float) -> float:
    if not math.isfinite(current) or not math.isfinite(frozen) or frozen == 0.0:
        raise ValueError("score comparison requires finite values and nonzero frozen score")
    return abs(current - frozen) / abs(frozen)


def _score_drift_rows(
    current: Iterable[AdvancementCandidateScore],
    frozen_rows: Iterable[dict[str, Any]],
    *,
    years: Iterable[int],
) -> list[dict[str, Any]]:
    current_by_id = {row.candidate_id: asdict(row) for row in current}
    frozen_by_id = {str(row["candidate_id"]): row for row in frozen_rows}
    if set(current_by_id) != set(frozen_by_id):
        raise ValueError("candidate IDs changed during source recertification")

    result: list[dict[str, Any]] = []
    for candidate_id in sorted(current_by_id):
        current_row = current_by_id[candidate_id]
        frozen_row = frozen_by_id[candidate_id]
        year_rows: dict[str, Any] = {}
        for year in years:
            current_cell = current_row["yearly"][int(year)]
            frozen_cell = frozen_row["yearly"][str(int(year))]
            if int(current_cell["observation_count"]) != int(frozen_cell["observation_count"]):
                raise ValueError(f"scoreable count changed for {candidate_id}/{year}")
            if float(current_cell["exposure"]) != float(frozen_cell["exposure"]):
                raise ValueError(f"scoreable opportunity exposure changed for {candidate_id}/{year}")
            drift = relative_score_drift(
                float(current_cell["score"]), float(frozen_cell["score"])
            )
            if drift > MAX_RELATIVE_SCORE_DRIFT:
                raise ValueError(
                    f"primary score drift exceeds limit for {candidate_id}/{year}: {drift}"
                )
            year_rows[str(year)] = {
                "frozen_score": float(frozen_cell["score"]),
                "recertified_score": float(current_cell["score"]),
                "relative_drift": drift,
                "observation_count": int(current_cell["observation_count"]),
                "opportunity_exposure": float(current_cell["exposure"]),
            }
        result.append({"candidate_id": candidate_id, "yearly": year_rows})
    return result


def _fetch_history(
    session: requests.Session,
    *,
    certified_captures: dict[int, dict[str, Any]],
) -> tuple[list[PlayerSeasonAdvancementSummary], list[dict[str, Any]]]:
    history: list[PlayerSeasonAdvancementSummary] = []
    captures: list[dict[str, Any]] = []
    for season in SOURCE_SEASONS:
        response = session.get(
            SAVANT_BASERUNNING_RUN_VALUE_URL,
            params=savant_baserunning_query_params(season),
            timeout=120,
        )
        response.raise_for_status()
        rows = parse_savant_baserunning_csv(response.content.decode("utf-8-sig"))
        source_audit = audit_savant_baserunning_rows(rows)
        if not source_audit["advancement_source_usable"]:
            raise ValueError(f"Savant advancement source unusable for {season}")
        certified = certified_captures[season]
        if len(rows) != int(certified["row_count"]):
            raise ValueError(f"Savant row count changed for {season}")
        for row in rows:
            history.append(
                PlayerSeasonAdvancementSummary(
                    player_id=int(float(row["player_id"])),
                    season=season,
                    runs_xb=float(row["runner_runs_xb"]),
                    opportunities_xb=float(row["n_runner_moved_xb"]),
                )
            )
        captures.append(
            {
                "season": season,
                "requested_url": response.url,
                "row_count": len(rows),
                "response_bytes": len(response.content),
                "response_sha256": hashlib.sha256(response.content).hexdigest(),
                "original_certified_response_bytes": int(certified["response_bytes"]),
                "original_certified_response_sha256": str(certified["response_sha256"]),
            }
        )
    return history, captures


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-audit",
        type=Path,
        default=Path("docs/player-value-v1-baserunning-source-audit-result.json"),
    )
    parser.add_argument(
        "--selection",
        type=Path,
        default=Path("docs/player-value-v1-advancement-projection-selection-result.json"),
    )
    parser.add_argument("--output-table", type=Path, required=True)
    parser.add_argument("--output-result", type=Path, required=True)
    args = parser.parse_args()

    audit = _load_json(args.source_audit)
    frozen = _load_json(args.selection)
    if frozen["frozen_candidate_id"] != FROZEN_CANDIDATE_ID:
        raise ValueError("frozen advancement candidate changed before recertification")
    certified_captures = {
        int(row["season"]): row
        for row in audit["mlb_statcast_advancement"]["captures"]
    }
    if set(certified_captures) != set(SOURCE_SEASONS):
        raise ValueError("original source audit does not cover exactly 2019-2024")

    with requests.Session() as session:
        session.headers["User-Agent"] = (
            "universal-baseball-model-advancement-source-recertification/0.1"
        )
        history, captures = _fetch_history(
            session, certified_captures=certified_captures
        )

    keys = [(row.season, row.player_id) for row in history]
    if len(keys) != len(set(keys)):
        raise ValueError("recertified advancement history has duplicate player-season keys")

    development_scores = score_all_candidates(
        history, target_years=DEVELOPMENT_YEARS
    )
    development_audit = _score_drift_rows(
        development_scores,
        frozen["development_scores"],
        years=DEVELOPMENT_YEARS,
    )
    development_selection = select_development_candidate(development_scores)
    if (
        development_selection.selected_candidate_id != FROZEN_CANDIDATE_ID
        or development_selection.development_player_specific_winner
        != FROZEN_CANDIDATE_ID
    ):
        raise ValueError("recertified source changes the frozen development winner")

    candidates = {row.candidate_id: row for row in advancement_candidates()}
    confirmation_scores = [
        score_candidate(
            history,
            candidates[candidate_id],
            target_years=(CONFIRMATION_YEAR,),
        )
        for candidate_id in (BASELINE_CANDIDATE_ID, FROZEN_CANDIDATE_ID)
    ]
    confirmation_audit = _score_drift_rows(
        confirmation_scores,
        frozen["confirmation_scores"],
        years=(CONFIRMATION_YEAR,),
    )
    confirmed = confirmation_passes(FROZEN_CANDIDATE_ID, confirmation_scores)
    if not confirmed:
        raise ValueError("recertified source changes the frozen confirmation verdict")

    table = pl.DataFrame(
        [
            {
                "season": row.season,
                "player_id": row.player_id,
                "runs_xb": row.runs_xb,
                "opportunities_xb": row.opportunities_xb,
            }
            for row in sorted(history, key=lambda row: (row.season, row.player_id))
        ],
        schema={
            "season": pl.Int32,
            "player_id": pl.Int64,
            "runs_xb": pl.Float64,
            "opportunities_xb": pl.Float64,
        },
    )
    args.output_table.parent.mkdir(parents=True, exist_ok=True)
    table.write_parquet(args.output_table)
    roundtrip = [
        PlayerSeasonAdvancementSummary(**row)
        for row in pl.read_parquet(args.output_table).to_dicts()
    ]
    canonical_hash = canonical_advancement_model_input_sha256(history)
    if canonical_advancement_model_input_sha256(roundtrip) != canonical_hash:
        raise ValueError("Parquet roundtrip changed canonical advancement model inputs")

    all_drifts = [
        float(cell["relative_drift"])
        for candidate in [*development_audit, *confirmation_audit]
        for cell in candidate["yearly"].values()
    ]
    payload = {
        "schema_version": "0.1",
        "status": "advancement_source_recertified_pending_immutable_artifact",
        "contract": "docs/player-value-v1-advancement-source-recertification-contract.md",
        "source_commit": str(os.environ.get("GITHUB_SHA") or "").strip() or None,
        "source_run_id": int(os.environ["GITHUB_RUN_ID"])
        if os.environ.get("GITHUB_RUN_ID")
        else None,
        "frozen_candidate_id": FROZEN_CANDIDATE_ID,
        "model_input": {
            "columns": ["season", "player_id", "runs_xb", "opportunities_xb"],
            "row_count": table.height,
            "canonical_sha256": canonical_hash,
            "table_path_within_artifact": args.output_table.name,
        },
        "captures": captures,
        "invariance_audit": {
            "development": development_audit,
            "confirmation": confirmation_audit,
            "development_winner_unchanged": True,
            "confirmation_verdict_unchanged": True,
            "maximum_relative_primary_score_drift": max(all_drifts),
            "relative_primary_score_drift_limit": MAX_RELATIVE_SCORE_DRIFT,
            "passes": True,
        },
        "boundary": {
            "model_refit": False,
            "model_reselection": False,
            "frozen_candidate_changed": False,
            "2025_data_accessed": False,
            "park_neutrality_audit_opened": False,
            "war_calculated": False,
        },
        "immutable_artifact": None,
    }
    args.output_result.parent.mkdir(parents=True, exist_ok=True)
    args.output_result.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
