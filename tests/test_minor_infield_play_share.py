import polars as pl
from universal_baseball.minor_infield_play_share import annual, pooled, eligible_balls


def source():
    rows = []
    for team in [10, 20]:
        for i, (pos, outcome) in enumerate([(6, "OUT"), (8, "1B"), (4, "MULTI_OUT"), (5, "ROE")]):
            rows.append(dict(game_pk=team, at_bat_index=i, season=2024, level="a", league_id=123,
                stand="R", p_throws="R", park_key="park", defense_team=team,
                fielder_4=team+4, fielder_5=team+5, fielder_6=team+6,
                hit_location=pos, terminal_outcome_group=outcome, has_source_conflict=False, any_bunt=False))
    return pl.DataFrame(rows)


def test_through_hit_and_credit_conservation():
    f, audit = annual(source())
    assert audit["eligible_balls"] == 8
    assert audit["credits"] == 4  # DP is one range credit
    assert f["ground_balls"].sum() == 24
    ss = f.filter(pl.col("player_id") == 16).row(0, named=True)
    assert ss["ground_balls"] == 4 and ss["touches"] == 1


def test_reference_excludes_own_team():
    s = source().with_columns(pl.when(pl.col("defense_team") == 10).then(pl.lit("OUT")).otherwise(pl.col("terminal_outcome_group")).alias("terminal_outcome_group"))
    f, _ = annual(s)
    own = f.filter(pl.col("player_id") == 15).row(0, named=True)
    assert own["credits"] == 1
    assert own["expected_credits"] == 0  # other team third baseman made none


def test_conflicts_unknown_outs_and_bunts_not_failure_labels():
    s = source().with_columns(pl.when(pl.col("at_bat_index") == 0).then(pl.lit(None)).otherwise(pl.col("hit_location")).alias("hit_location"))
    assert eligible_balls(s).height == 6
    s = source().with_columns((pl.col("at_bat_index") == 1).alias("any_bunt"))
    assert eligible_balls(s).height == 6


def test_missing_season_not_zero_quality_and_future_excluded():
    f, _ = annual(source())
    old = f.with_columns(pl.lit(2022, dtype=pl.Int64).alias("season"))
    both = pl.concat([old, f])
    q = pooled(both, 2023)
    assert q["ground_balls"].sum() == 12  # only 2022 at half weight
    assert q["credits"].sum() == 2
