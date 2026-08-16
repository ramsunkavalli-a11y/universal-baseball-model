"""Reusable MLB Performance-bin calibration helpers.

This module promotes the baseball semantics from the certified MLB bin-value
audits into production code.  It does not choose or validate a shrinkage
strength; ADR 023 owns that policy.  It only:

- identifies deterministic intraleague game samples from a completed schedule;
- maps official PA/contact evidence to the frozen core Performance taxonomy;
- joins true-PA state transitions to a caller-supplied 24-state RE matrix.

Network fetching and artifact provenance remain orchestration concerns so these
transforms stay unit-testable.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import polars as pl

from universal_baseball.contact_profile import classify_contact_profile_events
from universal_baseball.mlb_season_stats import MLB_LEAGUE_IDS
from universal_baseball.official import project_official_play_by_play
from universal_baseball.performance_events import BB_HBP_EVENT_TYPES, STRIKEOUT_EVENT_TYPES
from universal_baseball.run_expectancy import attach_re24
from universal_baseball.state_transitions_v2 import build_official_state_transitions_v2


MLB_LEAGUE_NAMES = {103: "AL", 104: "NL"}


def spread_sample(rows: Sequence[Mapping[str, Any]], n: int) -> list[dict[str, Any]]:
    """Return a deterministic date-spread sample without randomness."""

    if n <= 0:
        return []
    ordered = sorted(
        (dict(row) for row in rows),
        key=lambda row: (str(row["game_date"]), int(row["game_pk"])),
    )
    if len(ordered) < n:
        raise ValueError(f"requested {n} games from only {len(ordered)} candidates")
    if n == 1:
        return [ordered[len(ordered) // 2]]
    indices = [round(i * (len(ordered) - 1) / (n - 1)) for i in range(n)]
    if len(set(indices)) != n:
        raise RuntimeError("deterministic spread sample produced duplicate indices")
    return [ordered[index] for index in indices]


def intraleague_schedule_candidates(
    schedule_payload: Mapping[str, Any],
    team_to_league: Mapping[int, int],
) -> dict[int, list[dict[str, Any]]]:
    """Project final regular-season MLB schedule rows to AL/NL intraleague games."""

    candidates: dict[int, list[dict[str, Any]]] = {league_id: [] for league_id in MLB_LEAGUE_IDS}
    for date_row in schedule_payload.get("dates") or []:
        game_date = str(date_row.get("date") or "")
        for game in date_row.get("games") or []:
            if str(game.get("gameType") or "") != "R":
                continue
            status = game.get("status") or {}
            if str(status.get("abstractGameState") or "") != "Final":
                continue
            teams = game.get("teams") or {}
            home = int(((teams.get("home") or {}).get("team") or {}).get("id"))
            away = int(((teams.get("away") or {}).get("team") or {}).get("id"))
            home_league = team_to_league.get(home)
            away_league = team_to_league.get(away)
            if home_league is None or away_league is None:
                raise ValueError(f"schedule game has team absent from league authority: {game.get('gamePk')}")
            if home_league != away_league or int(home_league) not in MLB_LEAGUE_IDS:
                continue
            league_id = int(home_league)
            candidates[league_id].append(
                {
                    "game_pk": int(game["gamePk"]),
                    "game_date": game_date,
                    "home_team_id": home,
                    "away_team_id": away,
                    "league_id": league_id,
                }
            )
    missing = sorted(int(value) for value in MLB_LEAGUE_IDS if not candidates[int(value)])
    if missing:
        raise ValueError(f"schedule lacks intraleague candidates for MLB leagues: {missing}")
    return candidates


def performance_core_from_official(
    pa: pl.DataFrame,
    pitch: pl.DataFrame,
    *,
    season: int,
    league_id: int,
) -> pl.DataFrame:
    """Map official PA/contact evidence to one frozen core-bin row per true PA."""

    if int(league_id) not in MLB_LEAGUE_IDS:
        raise ValueError(f"unsupported MLB league_id: {league_id}")
    required_pa = {
        "game_pk",
        "at_bat_number",
        "batter_id",
        "batter_side",
        "event_type",
        "description",
    }
    required_pitch = {
        "game_pk",
        "at_bat_number",
        "pitch_number",
        "is_in_play",
        "hit_trajectory",
        "hit_coord_x",
        "hit_coord_y",
    }
    missing_pa = sorted(required_pa - set(pa.columns))
    missing_pitch = sorted(required_pitch - set(pitch.columns))
    if missing_pa:
        raise ValueError(f"official PA frame missing calibration fields: {missing_pa}")
    if missing_pitch:
        raise ValueError(f"official pitch frame missing calibration fields: {missing_pitch}")

    pa_work = pa.select(
        pl.col("game_pk").cast(pl.Int64),
        pl.col("at_bat_number").cast(pl.Int64).alias("at_bat_index"),
        pl.col("batter_id").cast(pl.Int64).alias("batter_mlbam_id"),
        pl.col("batter_side").cast(pl.String),
        pl.col("event_type").cast(pl.String),
        pl.col("description").cast(pl.String).alias("result_description"),
    )
    duplicate_pa = pa_work.group_by(["game_pk", "at_bat_index"]).len().filter(pl.col("len") > 1)
    if not duplicate_pa.is_empty():
        raise ValueError("official calibration PA frame contains duplicate play sequences")

    contact_pitch = pitch.filter(pl.col("is_in_play") == True).select(  # noqa: E712
        pl.col("game_pk").cast(pl.Int64),
        pl.col("at_bat_number").cast(pl.Int64).alias("at_bat_index"),
        pl.col("pitch_number").cast(pl.Int64),
        pl.col("hit_trajectory").cast(pl.String).alias("bb_type"),
        pl.col("hit_coord_x").cast(pl.Float64, strict=False).alias("hc_x"),
        pl.col("hit_coord_y").cast(pl.Float64, strict=False).alias("hc_y"),
    )
    duplicate_contacts = (
        contact_pitch.group_by(["game_pk", "at_bat_index"])
        .len()
        .filter(pl.col("len") > 1)
    )
    if not duplicate_contacts.is_empty():
        raise ValueError("official calibration has multiple in-play pitches in one true PA")

    if contact_pitch.is_empty():
        contact_bins = pl.DataFrame(
            schema={"game_pk": pl.Int64, "at_bat_index": pl.Int64, "contact_core_bin": pl.String}
        )
    else:
        contact_input = contact_pitch.join(
            pa_work.select(
                "game_pk",
                "at_bat_index",
                "batter_mlbam_id",
                "batter_side",
                "result_description",
            ),
            on=["game_pk", "at_bat_index"],
            how="inner",
        ).with_columns(
            pl.lit(int(season)).alias("season"),
            pl.lit(int(league_id)).alias("league_id"),
            pl.lit("official_calibration").alias("participant_authority"),
            pl.lit("official_calibration").alias("result_description_authority"),
        )
        classified = classify_contact_profile_events(contact_input)
        contact_bins = classified.select(
            "game_pk",
            "at_bat_index",
            pl.col("core_bin").alias("contact_core_bin"),
        )

    return (
        pa_work.join(contact_bins, on=["game_pk", "at_bat_index"], how="left")
        .with_columns(
            pl.when(pl.col("event_type").is_in(sorted(BB_HBP_EVENT_TYPES)))
            .then(pl.lit("BB_HBP"))
            .when(pl.col("event_type").is_in(sorted(STRIKEOUT_EVENT_TYPES)))
            .then(pl.lit("K"))
            .otherwise(pl.col("contact_core_bin"))
            .alias("core_bin"),
            pl.lit(int(season)).alias("season"),
            pl.lit(int(league_id)).alias("league_id"),
        )
        .select("season", "game_pk", "at_bat_index", "league_id", "core_bin")
    )


def calibration_events_from_official_payload(
    game_pk: int,
    payload: Mapping[str, Any],
    re_matrix: pl.DataFrame,
    *,
    season: int,
    league_id: int,
    game_date: str | None = None,
    source_snapshot_id: str = "production:official",
    normalization_id: str = "production:mlb-calibration-v1",
) -> pl.DataFrame:
    """Return valued core Performance events for one official MLB game."""

    pa, pitch = project_official_play_by_play(int(game_pk), payload)
    core = performance_core_from_official(
        pa,
        pitch,
        season=int(season),
        league_id=int(league_id),
    )
    transitions = build_official_state_transitions_v2(
        int(game_pk),
        payload,
        source_snapshot_id=source_snapshot_id,
        normalization_id=normalization_id,
    )
    valued = attach_re24(transitions, re_matrix)
    terminal = valued.filter(
        pl.col("is_plate_appearance_result") & pl.col("re24_available")
    ).select("game_pk", "at_bat_index", "re24")
    joined = core.filter(pl.col("core_bin").is_not_null()).join(
        terminal,
        on=["game_pk", "at_bat_index"],
        how="left",
    )
    if joined.filter(pl.col("re24").is_null()).height:
        raise ValueError(f"core Performance PA lacks RE24 in game {int(game_pk)}")
    if game_date is not None:
        joined = joined.with_columns(pl.lit(str(game_date)).alias("game_date"))
    return joined.sort(["game_pk", "at_bat_index"])
