#!/usr/bin/env python
"""Historical MiLB Current Talent materializer with exact-game gameLog fallback.

This is a thin orchestration wrapper around the certified historical materializer.
Every source/contact/identity/reconciliation function remains unchanged.  The
only replaced step is sparse outcome adjudication: if an official player
``gameLog`` omits a positive-PA source game, exact official game play-by-play may
confirm that game only when its complete true-PA outcome vector matches source.

The base gameLog adjudicator and exact season-aggregate reconciliation still run
afterward unchanged.  No model fitting or Projection logic is performed here.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import polars as pl

import materialize_current_talent_historical_milb_game_evidence as base
from universal_baseball.current_talent_official_game_fallback import (
    augment_game_log_with_exact_pa_fallback,
    source_only_positive_pa_games,
)
from universal_baseball.official import project_official_play_by_play


def _adjudicate_outcomes_with_exact_game_fallback(
    *,
    outcomes: pl.DataFrame,
    season_stats: pl.DataFrame,
    season: int,
    level: str,
    league_ids: frozenset[int],
    sport_id: int,
    raw_official_dir: Path,
) -> tuple[pl.DataFrame, pl.DataFrame, dict[str, Any]]:
    pre_comparison, pre_metrics = base.reconcile_resolved_outcomes_to_season_aggregates(
        outcomes,
        season_stats,
        season=season,
        expected_league_ids=league_ids,
        require_exact=False,
    )
    pre_mismatch = pre_comparison.filter(pl.col("has_any_mismatch"))
    pre_keys = base._key_set(pre_mismatch)
    corrected = outcomes.with_columns(pl.lit("player_game_source").alias("outcome_authority"))

    evidence_frames: list[pl.DataFrame] = []
    adjudications: list[dict[str, Any]] = []
    snapshots: list[dict[str, Any]] = []
    raw_official_dir.mkdir(parents=True, exist_ok=True)
    official_session = base.new_official_session()
    try:
        for league_id, player_id in sorted(pre_keys):
            endpoint = base.official_game_log_endpoint(
                player_id=player_id,
                sport_id=sport_id,
                season=season,
            )
            capture = base.capture_official_json(endpoint, session=official_session)
            raw_path = raw_official_dir / f"player_{player_id}_sport_{sport_id}_gamelog.json"
            capture.write_raw(raw_path)
            if not isinstance(capture.data, dict):
                raise RuntimeError(f"official gameLog for player {player_id} is not an object")
            official = base.project_official_hitting_game_log(
                capture.data,
                player_id=player_id,
                sport_id=sport_id,
            )

            source_only_games = source_only_positive_pa_games(
                corrected,
                official,
                player_id=player_id,
                league_id=league_id,
            )
            fallback_snapshots: list[dict[str, Any]] = []
            if source_only_games:
                pa_frames: list[pl.DataFrame] = []
                for game_id in source_only_games:
                    pbp_endpoint = f"game/{int(game_id)}/playByPlay"
                    pbp_capture = base.capture_official_json(
                        pbp_endpoint,
                        session=official_session,
                    )
                    pbp_path = raw_official_dir / (
                        f"player_{player_id}_game_{game_id}_playbyplay.json"
                    )
                    pbp_capture.write_raw(pbp_path)
                    if not isinstance(pbp_capture.data, dict):
                        raise RuntimeError(
                            f"official exact-game playByPlay for game {game_id} is not an object"
                        )
                    pa_frame, _ = project_official_play_by_play(
                        int(game_id),
                        pbp_capture.data,
                    )
                    pa_frames.append(pa_frame)
                    fallback_snapshots.append(
                        {
                            "game_id": int(game_id),
                            "endpoint": pbp_capture.endpoint,
                            "url": pbp_capture.url,
                            "retrieved_at_utc": pbp_capture.retrieved_at_utc.isoformat(),
                            "content_sha256": pbp_capture.content_sha256,
                            "raw_path": str(pbp_path),
                            "official_true_pa_count": int(pa_frame.height),
                            "target_player_true_pa_count": int(
                                pa_frame.filter(pl.col("batter_id") == int(player_id)).height
                            ),
                        }
                    )
                official_pa = (
                    pl.concat(pa_frames, how="vertical_relaxed")
                    if pa_frames
                    else pl.DataFrame(
                        schema={"game_pk": pl.String, "batter_id": pl.Int64, "event_type": pl.String}
                    )
                )
                official, fallback_metrics = augment_game_log_with_exact_pa_fallback(
                    corrected,
                    official,
                    official_pa,
                    player_id=player_id,
                    league_id=league_id,
                )
            else:
                fallback_metrics = {
                    "source_only_game_log_gap_count": 0,
                    "exact_game_pbp_confirmed_count": 0,
                    "confirmed_game_ids": [],
                }

            corrected, evidence, metrics = base.apply_official_game_log_outcome_authority(
                corrected,
                official,
                player_id=player_id,
                league_id=league_id,
            )
            metrics = dict(metrics)
            metrics["game_log_gap_fallback"] = fallback_metrics
            if not evidence.is_empty():
                evidence_frames.append(evidence)
            adjudications.append(metrics)
            snapshots.append(
                {
                    "league_id": league_id,
                    "player_id": player_id,
                    "endpoint": capture.endpoint,
                    "url": capture.url,
                    "retrieved_at_utc": capture.retrieved_at_utc.isoformat(),
                    "content_sha256": capture.content_sha256,
                    "raw_path": str(raw_path),
                    "exact_game_fallback_snapshots": fallback_snapshots,
                }
            )
    finally:
        official_session.close()

    post_comparison, post_metrics = base.reconcile_resolved_outcomes_to_season_aggregates(
        corrected,
        season_stats,
        season=season,
        expected_league_ids=league_ids,
        require_exact=False,
    )
    post_mismatch = post_comparison.filter(pl.col("has_any_mismatch"))
    post_keys = base._key_set(post_mismatch)
    if not post_keys.issubset(pre_keys):
        raise RuntimeError(
            f"{season} {level} official outcome adjudication introduced new season residuals: "
            f"{sorted(post_keys - pre_keys)}"
        )
    if len(adjudications) != len(pre_keys):
        raise RuntimeError(
            f"{season} {level} did not adjudicate every pre-existing outcome residual"
        )

    if evidence_frames:
        evidence = pl.concat(evidence_frames, how="vertical_relaxed").sort(
            ["league_id", "player_id", "game_id", "field"]
        )
    else:
        evidence = pl.DataFrame(
            schema={
                "player_id": pl.Int64,
                "league_id": pl.Int64,
                "game_id": pl.Int64,
                "field": pl.String,
                "source_value": pl.Int64,
                "official_value": pl.Int64,
                "action": pl.String,
                "source_game_date": pl.Date,
                "official_game_date": pl.Date,
                "retained_game_date": pl.Date,
                "game_date_authority": pl.String,
            }
        )

    classifications: dict[str, int] = {}
    exact_game_fallback_count = 0
    for row in adjudications:
        key = str(row["classification"])
        classifications[key] = classifications.get(key, 0) + 1
        exact_game_fallback_count += int(
            row.get("game_log_gap_fallback", {}).get("exact_game_pbp_confirmed_count", 0)
        )
    return corrected, evidence, {
        "pre_reconciliation": pre_metrics,
        "pre_residual_player_league_count": len(pre_keys),
        "pre_residual_keys": [list(key) for key in sorted(pre_keys)],
        "official_adjudication_count": len(adjudications),
        "classification_counts": classifications,
        "adjudications": adjudications,
        "official_snapshots": snapshots,
        "exact_game_game_log_gap_fallback_count": exact_game_fallback_count,
        "changed_field_evidence_count": int(evidence.height),
        "post_reconciliation": post_metrics,
        "remaining_season_asset_residual_count": len(post_keys),
        "remaining_season_asset_residual_keys": [list(key) for key in sorted(post_keys)],
        "accepted": True,
        "temporal_semantics": (
            "retrospective_event_cutoff_corrected_history_not_vintage_information_set"
        ),
    }


# Replace only the private sparse outcome-adjudication seam.  All other behavior
# remains the certified base materializer's implementation.
base._adjudicate_outcomes = _adjudicate_outcomes_with_exact_game_fallback


if __name__ == "__main__":
    raise SystemExit(base.main())
