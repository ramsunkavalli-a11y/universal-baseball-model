from __future__ import annotations

import polars as pl

from universal_baseball.historical_matchup_profiles import (
    add_matchup_outcomes,
    build_matchup_cells,
    build_prior_profiles,
    build_prior_split_profiles,
)


def _events() -> pl.DataFrame:
    rows = []
    for season in (2021, 2022, 2023):
        for batter in (10, 11):
            for pitcher in (20, 21):
                for index in range(12):
                    strikeout = batter == 11 and index < 4
                    walk = pitcher == 21 and index == 5
                    home_run = batter == 10 and pitcher == 21 and index == 6
                    group = "HR" if home_run else None if strikeout or walk else "OUT"
                    rows.append(
                        {
                            "season": season,
                            "level": "a" if season < 2023 else "a+",
                            "batter_id": batter,
                            "pitcher_id": pitcher,
                            "pitcher_hand": "R",
                            "batter_side": "L" if batter == 10 else "R",
                            "bb_type": "fly_ball" if group else None,
                            "terminal_outcome_group": group,
                            "strikeout": int(strikeout),
                            "control_failure": int(walk),
                            "home_run": int(home_run),
                        }
                    )
    return add_matchup_outcomes(pl.DataFrame(rows))


def test_prior_profiles_are_strictly_historical() -> None:
    events = _events()
    profiles = build_prior_profiles(
        events,
        player_column="batter_id",
        prefix="h",
        target_seasons=[2022, 2023],
    )
    assert profiles.get_column("target_season").unique().sort().to_list() == [2022, 2023]
    first = profiles.filter(
        (pl.col("target_season") == 2022) & (pl.col("player_id") == 10)
    ).row(0, named=True)
    assert first["h_history_pa"] == 24
    assert first["h_last_level_rank"] == 2


def test_matchup_cells_mark_advancement_and_new_pair() -> None:
    events = _events()
    seasons = [2022, 2023]
    hitters = build_prior_profiles(
        events, player_column="batter_id", prefix="h", target_seasons=seasons
    )
    pitchers = build_prior_profiles(
        events, player_column="pitcher_id", prefix="p", target_seasons=seasons
    )
    cells = build_matchup_cells(
        events, hitter_profiles=hitters, pitcher_profiles=pitchers
    ).filter(pl.col("season").is_in(seasons))
    assert cells.filter(pl.col("season") == 2023).get_column("hitter_advanced").all()
    assert not cells.filter(pl.col("season") == 2022).get_column("new_pair").any()
    assert cells.get_column("pa").sum() == 96


def test_split_profiles_use_prior_matchup_side_and_shrink_to_overall() -> None:
    events = _events().with_columns(
        pl.when(pl.col("pitcher_id") == 21)
        .then(pl.lit("L"))
        .otherwise(pl.lit("R"))
        .alias("pitcher_hand")
    )
    overall = build_prior_profiles(
        events,
        player_column="batter_id",
        prefix="h",
        target_seasons=[2022],
    )
    splits = build_prior_split_profiles(
        events,
        player_column="batter_id",
        split_column="pitcher_hand",
        prefix="hs",
        overall_profiles=overall,
        target_seasons=[2022],
    )
    batter = splits.filter(pl.col("player_id") == 10).sort("pitcher_hand")
    assert batter.get_column("pitcher_hand").to_list() == ["L", "R"]
    assert batter.get_column("hs_history_pa").to_list() == [12, 12]
    assert batter.filter(pl.col("pitcher_hand") == "L").item(0, "hs_hr") > batter.filter(
        pl.col("pitcher_hand") == "R"
    ).item(0, "hs_hr")
