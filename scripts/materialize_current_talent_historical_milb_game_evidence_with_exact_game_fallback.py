#!/usr/bin/env python
"""Historical MiLB Current Talent materializer with sparse source-authority fallbacks.

This is a thin orchestration wrapper around the certified historical materializer.
Every source/contact/identity/reconciliation function remains unchanged except
for narrow, fail-closed source-authority seams:

1. a single positive-PA source game absent from official gameLog may be
   quarantined only when that row exactly equals the independent season-aggregate
   residual and removing its full outcome vector exactly matches official gameLog;
2. any proven quarantined player/game key is removed consistently from outcome,
   contact-control, and same-player contact grains without reattribution;
3. if a remaining gameLog omission has exact official true-PA evidence, that
   evidence may confirm the source row only on a complete vector match;
4. if a regular-season PBP game lacks reusable same-game league identity, exact
   official game identity may fill it only after the existing sport/league checks;
   when the exact official game endpoint itself returns 404, that unauthorizable
   PBP game is quarantined rather than inheriting filename-level identity.

The base gameLog adjudicator, same-game enrichment, league validation, and exact
season-aggregate reconciliation still run afterward. No model fitting,
Projection scoring, or 2025 access occurs here.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import polars as pl

import materialize_current_talent_historical_milb_game_evidence as base
from universal_baseball.current_talent_era import current_talent_level_spec
from universal_baseball.current_talent_evidence_quarantine import (
    quarantine_game_ids,
    quarantine_player_game_keys,
)
from universal_baseball.current_talent_official_game_fallback import (
    augment_game_log_with_exact_pa_fallback,
    source_only_positive_pa_games,
)
from universal_baseball.current_talent_official_game_identity import (
    augment_game_league_map_with_official_identity,
    project_official_game_league_identity,
)
from universal_baseball.current_talent_source_residual_quarantine import (
    quarantine_single_source_only_exact_residual,
)
from universal_baseball.official import project_official_play_by_play


_BASE_ENRICH_HISTORICAL_PBP_LEAGUE_ID = base.enrich_historical_pbp_league_id
_BASE_APPLY_PARTICIPANT_AUTHORITY = base._apply_participant_authority
_LEVEL_TOKEN = re.compile(r"^(?P<season>\d{4}).*_(?P<level>aaa|aa|a\+|a|rk)_pbp\.csv$", re.I)
_QUARANTINED_PLAYER_GAME_KEYS: set[tuple[int, int]] = set()


def _source_asset_spec(source_asset: str):
    name = Path(str(source_asset)).name
    match = _LEVEL_TOKEN.match(name)
    if match is None:
        raise ValueError(
            f"cannot derive certified era slice from historical PBP asset name: {name!r}"
        )
    season = int(match.group("season"))
    level = match.group("level").lower()
    return season, level, current_talent_level_spec(season, level)


def _regular_game_ids(frame: pl.DataFrame, *, game_type: str | None) -> set[int]:
    if "game_pk" not in frame.columns:
        raise ValueError("historical PBP fallback frame missing game_pk")
    working = frame
    if game_type is not None:
        if "game_type" not in frame.columns:
            raise ValueError("historical PBP fallback frame missing game_type")
        working = working.filter(pl.col("game_type").cast(pl.String) == str(game_type))
    return {
        int(value)
        for value in working.get_column("game_pk")
        .cast(pl.Int64, strict=False)
        .drop_nulls()
        .unique()
        .to_list()
    }


def _enrich_historical_pbp_league_id_with_exact_game_fallback(
    pbp_rows: pl.DataFrame,
    game_league_map: pl.DataFrame,
    *,
    source_asset: str,
    game_type: str | None = "R",
):
    pbp_games = _regular_game_ids(pbp_rows, game_type=game_type)
    mapped_games = {
        int(value)
        for value in game_league_map.get_column("game_pk").cast(pl.Int64).unique().to_list()
    }
    missing_games = sorted(pbp_games - mapped_games)
    if not missing_games:
        return _BASE_ENRICH_HISTORICAL_PBP_LEAGUE_ID(
            pbp_rows,
            game_league_map,
            source_asset=source_asset,
            game_type=game_type,
        )

    season, level, spec = _source_asset_spec(source_asset)
    identities = []
    snapshots: list[dict[str, Any]] = []
    official_404_games: list[int] = []
    slug = "aplus" if level == "a+" else level
    raw_dir = (
        Path("reports/generated/current-talent-historical-milb-game-evidence")
        / str(season)
        / slug
        / "official-game-identity-raw"
    )
    raw_dir.mkdir(parents=True, exist_ok=True)
    session = base.new_official_session()
    try:
        for game_id in missing_games:
            endpoint = f"game/{int(game_id)}/feed/live"
            probe_url = f"https://statsapi.mlb.com/api/v1/{endpoint}"
            response = session.get(probe_url, timeout=30)
            if response.status_code == 404:
                official_404_games.append(int(game_id))
                snapshots.append(
                    {
                        "game_id": int(game_id),
                        "endpoint": endpoint,
                        "url": probe_url,
                        "http_status": 404,
                        "classification": "official_exact_game_not_found_quarantine",
                    }
                )
                continue
            if not 200 <= response.status_code < 300:
                raise RuntimeError(
                    f"official exact-game identity probe failed: game={game_id}, "
                    f"status={response.status_code}"
                )

            capture = base.capture_official_json(endpoint, session=session)
            raw_path = raw_dir / f"game_{int(game_id)}_feed_live.json"
            capture.write_raw(raw_path)
            if not isinstance(capture.data, dict):
                raise RuntimeError(f"official live feed for game {game_id} is not an object")
            identity = project_official_game_league_identity(int(game_id), capture.data)
            identities.append(identity)
            snapshots.append(
                {
                    "game_id": int(game_id),
                    "endpoint": capture.endpoint,
                    "url": capture.url,
                    "http_status": 200,
                    "retrieved_at_utc": capture.retrieved_at_utc.isoformat(),
                    "content_sha256": capture.content_sha256,
                    "raw_path": str(raw_path),
                    "official_game_date": identity.game_date.isoformat(),
                    "official_league_id": identity.league_id,
                    "official_sport_id": identity.sport_id,
                    "away_team_id": identity.away_team_id,
                    "home_team_id": identity.home_team_id,
                    "classification": "official_exact_game_identity_available",
                }
            )
    finally:
        session.close()

    working_pbp, orphan_quarantine = quarantine_game_ids(
        pbp_rows,
        official_404_games,
        game_column="game_pk",
        label="pbp_missing_same_game_league_and_official_exact_game_404",
    )
    if identities:
        augmented_map, fallback_metrics = augment_game_league_map_with_official_identity(
            game_league_map,
            identities,
            expected_league_ids=spec.league_ids,
            expected_sport_id=spec.official_sport_id,
        )
    else:
        augmented_map = game_league_map
        fallback_metrics = {
            "official_identity_count": 0,
            "inserted_game_count": 0,
            "authority": "no_official_identity_insert_needed_after_404_quarantine",
        }

    enriched, metrics = _BASE_ENRICH_HISTORICAL_PBP_LEAGUE_ID(
        working_pbp,
        augmented_map,
        source_asset=source_asset,
        game_type=game_type,
    )
    metrics = dict(metrics)
    metrics["player_game_same_game_map_original_count"] = int(game_league_map.height)
    metrics["official_exact_game_identity_fallback"] = fallback_metrics
    metrics["official_exact_game_identity_snapshots"] = snapshots
    metrics["unresolved_official_404_game_quarantine"] = orphan_quarantine
    metrics["league_id_authority"] = (
        "player_game_same_game_plus_sparse_official_identity_with_unverifiable_games_quarantined"
    )
    return enriched, metrics


def _comparison_row(
    pre_comparison: pl.DataFrame,
    *,
    player_id: int,
    league_id: int,
) -> dict[str, Any]:
    rows = pre_comparison.filter(
        (pl.col("player_id") == int(player_id))
        & (pl.col("league_id") == int(league_id))
    ).to_dicts()
    if len(rows) != 1:
        raise RuntimeError(
            f"expected one pre-reconciliation row for player={player_id} league={league_id}; "
            f"found={len(rows)}"
        )
    return rows[0]


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
    _QUARANTINED_PLAYER_GAME_KEYS.clear()
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

            corrected, residual_quarantine = quarantine_single_source_only_exact_residual(
                corrected,
                official,
                _comparison_row(
                    pre_comparison,
                    player_id=player_id,
                    league_id=league_id,
                ),
                player_id=player_id,
                league_id=league_id,
            )
            if residual_quarantine.get("applied"):
                game_id, quarantine_player = residual_quarantine["quarantined_player_game_key"]
                _QUARANTINED_PLAYER_GAME_KEYS.add((int(game_id), int(quarantine_player)))

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
                official_pa = pl.concat(pa_frames, how="vertical_relaxed")
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
            metrics["source_only_exact_residual_quarantine"] = residual_quarantine
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
    exact_residual_quarantine_count = 0
    for row in adjudications:
        key = str(row["classification"])
        classifications[key] = classifications.get(key, 0) + 1
        exact_game_fallback_count += int(
            row.get("game_log_gap_fallback", {}).get("exact_game_pbp_confirmed_count", 0)
        )
        exact_residual_quarantine_count += int(
            bool(row.get("source_only_exact_residual_quarantine", {}).get("applied"))
        )
    return corrected, evidence, {
        "pre_reconciliation": pre_metrics,
        "pre_residual_player_league_count": len(pre_keys),
        "pre_residual_keys": [list(key) for key in sorted(pre_keys)],
        "official_adjudication_count": len(adjudications),
        "classification_counts": classifications,
        "adjudications": adjudications,
        "official_snapshots": snapshots,
        "source_only_exact_residual_quarantine_count": exact_residual_quarantine_count,
        "source_only_exact_residual_quarantined_keys": [
            list(key) for key in sorted(_QUARANTINED_PLAYER_GAME_KEYS)
        ],
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


def _apply_participant_authority_with_source_quarantine(
    contacts: pl.DataFrame,
    controls: pl.DataFrame,
):
    filtered_controls, control_metrics = quarantine_player_game_keys(
        controls,
        _QUARANTINED_PLAYER_GAME_KEYS,
        game_column="game_id",
        player_column="player_id",
        label="player_game_contact_controls_exact_source_residual",
    )
    filtered_contacts, contact_metrics = quarantine_player_game_keys(
        contacts,
        _QUARANTINED_PLAYER_GAME_KEYS,
        game_column="game_pk",
        player_column="source_batter_id",
        label="pbp_contacts_exact_source_residual",
    )
    authorized, metrics = _BASE_APPLY_PARTICIPANT_AUTHORITY(
        filtered_contacts,
        filtered_controls,
    )
    return authorized, {
        **metrics,
        "exact_source_residual_cross_grain_quarantine": {
            "keys": [list(key) for key in sorted(_QUARANTINED_PLAYER_GAME_KEYS)],
            "controls": control_metrics,
            "contacts": contact_metrics,
        },
    }


# Replace only sparse source-authority seams. All other behavior remains the
# certified base materializer's implementation.
base.enrich_historical_pbp_league_id = _enrich_historical_pbp_league_id_with_exact_game_fallback
base._adjudicate_outcomes = _adjudicate_outcomes_with_exact_game_fallback
base._apply_participant_authority = _apply_participant_authority_with_source_quarantine


if __name__ == "__main__":
    raise SystemExit(base.main())
