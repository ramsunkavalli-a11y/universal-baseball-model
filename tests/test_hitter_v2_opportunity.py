import polars as pl
from universal_baseball.hitter_v2_opportunity import (
    aggregate_player_game_gidp_opportunities,
    project_gidp_opportunities,
)


def _raw() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "game_pk": [1, 1, 1, 1],
            "at_bat_number": [1, 1, 2, 2],
            "pitch_number": [1, 2, 1, 2],
            "inning": [1, 1, 1, 1],
            "inning_half": ["Top"] * 4,
            "game_type": ["R"] * 4,
            "batter": [10] * 4,
            "on_1b": [20, 20, None, None],
            "outs_when_up": [0, 0, 1, 1],
        }
    )


def test_opening_state_produces_observed_gidp_opportunity() -> None:
    opportunities = project_gidp_opportunities(_raw(), base_state_semantics="post_pa")
    assert opportunities["gidp_opportunity"].to_list() == [0, 1]
    games = aggregate_player_game_gidp_opportunities(opportunities)
    assert games.item(0, "gidp_opportunities") == 1
    assert games.item(0, "observed_pbp_pa") == 2


def test_current_post_state_does_not_erase_pa_start_opportunity() -> None:
    opportunities = project_gidp_opportunities(_raw(), base_state_semantics="post_pa")
    second_pa = opportunities.filter(pl.col("at_bat_index") == 2).row(0, named=True)
    assert second_pa["runner_on_first_id"] == 20
    assert second_pa["gidp_opportunity"] == 1


def test_conflicting_prior_post_state_is_retained_fail_closed() -> None:
    conflict = pl.concat(
        [
            _raw(),
            _raw().filter(
                (pl.col("at_bat_number") == 1) & (pl.col("pitch_number") == 1)
            ).with_columns(pl.lit(None, dtype=pl.Int64).alias("on_1b")),
        ],
        how="vertical_relaxed",
    )
    opportunities = project_gidp_opportunities(
        conflict, base_state_semantics="post_pa"
    )
    ambiguous = opportunities.filter(pl.col("at_bat_index") == 2).row(0, named=True)
    assert ambiguous["gidp_opportunity"] is None
    assert ambiguous["opportunity_source_status"] == (
        "failed_closed_prior_post_state_conflict"
    )
    game = aggregate_player_game_gidp_opportunities(opportunities).row(0, named=True)
    assert game["gidp_opportunities"] is None
    assert game["gidp_opportunity_modeling_eligible"] is False


def test_pre_pa_source_uses_current_state_without_shift() -> None:
    opportunities = project_gidp_opportunities(
        _raw(), base_state_semantics="pre_pa"
    )
    assert opportunities["gidp_opportunity"].to_list() == [1, 0]
