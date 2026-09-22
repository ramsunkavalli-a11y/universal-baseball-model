from __future__ import annotations

import polars as pl

from universal_baseball.pbp_opportunity_events import (
    add_sequence_start_state,
    build_fielding_opportunities,
    build_runner_advancement_opportunities,
    project_catcher_pitch_observations,
    project_terminal_play_observations,
    resolve_overlapping_terminal_plays,
)


def _raw() -> pl.DataFrame:
    rows: list[dict[str, object]] = []

    def play(
        at_bat: int,
        description: str,
        type_code: str,
        bb_type: str | None,
        hit_location: int | None,
        batter: int,
        *,
        outs: int,
        on_1b: int | None = None,
        on_2b: int | None = None,
        on_3b: int | None = None,
        bat_score: int = 0,
        post_bat_score: int = 0,
    ) -> None:
        for pitch_number in (1, 2):
            row: dict[str, object] = {
                "game_pk": 1,
                "at_bat_number": at_bat,
                "pitch_number": pitch_number,
                "league_id": 117,
                "batter": batter,
                "pitcher": 900,
                "inning": 1,
                "outs_when_up": outs,
                "hit_location": hit_location,
                "on_1b": on_1b,
                "on_2b": on_2b,
                "on_3b": on_3b,
                "bat_score": bat_score,
                "fld_score": 0,
                "post_bat_score": post_bat_score,
                "post_fld_score": 0,
                "game_date": "2024-04-01",
                "game_type": "R",
                "home_team": "HOM",
                "away_team": "AWY",
                "inning_top_bot": "Top",
                "stand": "R",
                "p_throws": "L",
                "type": type_code if pitch_number == 2 else "B",
                "bb_type": bb_type if pitch_number == 2 else None,
                "description": description,
                "des": description,
                "if_fielding_alignment": "Standard",
                "of_fielding_alignment": "Standard",
                "hc_x": 120.0 if pitch_number == 2 else None,
                "hc_y": 80.0 if pitch_number == 2 else None,
            }
            for position in range(2, 10):
                row[f"fielder_{position}"] = 1000 + position
            rows.append(row)

    play(
        0,
        "Runner One singles on a line drive to left fielder Left Fielder.",
        "D",
        "line_drive",
        7,
        101,
        outs=0,
        on_1b=101,
    )
    play(
        1,
        "Batter Two flies out to center fielder Center Fielder.",
        "X",
        "fly_ball",
        8,
        102,
        outs=0,
        on_1b=101,
    )
    play(
        2,
        "Batter Three doubles on a line drive to right fielder Right Fielder.   Runner One scores.",
        "E",
        "line_drive",
        9,
        103,
        outs=1,
        on_2b=103,
        bat_score=0,
        post_bat_score=1,
    )
    return pl.DataFrame(rows)


def test_terminal_projection_and_fielding_opportunities() -> None:
    terminal = project_terminal_play_observations(
        _raw(), source_asset="2024_4_aaa_pbp.csv", season=2024, level="aaa"
    )
    assert terminal.height == 3
    assert terminal.get_column("terminal_outcome_group").to_list() == ["1B", "OUT", "2B"]
    assert terminal.get_column("responsible_fielder_id").to_list() == [1007, 1008, 1009]
    assert terminal.get_column("park_key").unique().to_list() == ["2024:HOM"]

    fielding = build_fielding_opportunities(terminal)
    assert fielding.height == 3
    assert fielding.get_column("conversion_out").to_list() == [0, 1, 0]


def test_start_state_and_runner_advancement() -> None:
    terminal = project_terminal_play_observations(
        _raw(), source_asset="2024_4_aaa_pbp.csv", season=2024, level="aaa"
    )
    state = add_sequence_start_state(terminal)
    second = state.filter(pl.col("at_bat_index") == 1).row(0, named=True)
    assert second["start_runner_1b"] == 101
    assert second["outs_continuity_ok"] is True

    opportunities = build_runner_advancement_opportunities(state)
    scored = opportunities.filter(pl.col("at_bat_index") == 2).row(0, named=True)
    assert scored["runner_id"] == 101
    assert scored["origin_base"] == 1
    assert scored["destination_base"] == 4
    assert scored["opportunity_type"] == "first_on_double"
    assert scored["runner_result"] == "scored"


def test_overlapping_resolution_excludes_conflicting_key() -> None:
    left = project_terminal_play_observations(
        _raw(), source_asset="2024_4_aaa_pbp.csv", season=2024, level="aaa"
    )
    right = left.with_columns(
        pl.lit("2024_5_aaa_pbp.csv").alias("source_asset"),
        pl.when(pl.col("at_bat_index") == 1)
        .then(pl.lit("ground_ball"))
        .otherwise(pl.col("bb_type"))
        .alias("bb_type"),
    )
    resolved = resolve_overlapping_terminal_plays([left, right])
    assert resolved.height == 3
    statuses = dict(
        resolved.select("at_bat_index", "resolution_status").iter_rows()
    )
    assert statuses[0] == "resolved_non_null_consensus"
    assert statuses[1] == "excluded_source_conflict"


def test_catcher_pitch_projection_preserves_takes_and_clean_blocks() -> None:
    raw = _raw().with_columns(
        pl.lit(0).alias("balls"),
        pl.lit(0).alias("strikes"),
        pl.lit(0.1).alias("plate_x"),
        pl.lit(2.2).alias("plate_z"),
        pl.lit(3.4).alias("sz_top"),
        pl.lit(1.5).alias("sz_bot"),
    ).with_columns(
        pl.when(
            (pl.col("at_bat_number") == 1) & (pl.col("pitch_number") == 1)
        )
        .then(pl.lit("*B"))
        .otherwise(pl.col("type"))
        .alias("type")
    )
    terminal = add_sequence_start_state(
        project_terminal_play_observations(
            raw, source_asset="2024_4_aaa_pbp.csv", season=2024, level="aaa"
        )
    )
    pitches = project_catcher_pitch_observations(
        raw,
        source_asset="2024_4_aaa_pbp.csv",
        season=2024,
        level="aaa",
        terminal_plays=terminal,
    )
    candidate = pitches.filter(pl.col("block_candidate")).row(0, named=True)
    assert candidate["start_runner_count"] == 1
    assert candidate["clean_block_opportunity"] is True
    assert candidate["block_result"] == "blocked"
