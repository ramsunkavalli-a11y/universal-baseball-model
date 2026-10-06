"""Coarse ground-ball play share, not individual out probabilities or OAA."""

import numpy as np
import polars as pl

POSITIONS = (4, 5, 6)
CONTEXT = ["season", "level", "league_id", "position", "stand", "p_throws", "park_key"]
LEAGUE = ["season", "level", "league_id", "position"]


def eligible_balls(frame):
    out = pl.col("terminal_outcome_group").is_in(["OUT", "MULTI_OUT"])
    return frame.filter(
        ~pl.col("has_source_conflict").fill_null(True)
        & ~pl.col("any_bunt").fill_null(True)
        & pl.col("terminal_outcome_group").is_in(["OUT", "MULTI_OUT", "1B", "2B", "3B", "ROE"])
        & (~out | pl.col("hit_location").is_between(1, 9).fill_null(False))
    ).with_columns(out.alias("batter_out"))


def annual(frame):
    """Each position shares exposure; only the successful first handler earns credit."""
    balls = eligible_balls(frame)
    assert balls.select("game_pk", "at_bat_index").is_duplicated().sum() == 0
    rows = pl.concat([
        balls.select(
            *[pl.col(c) for c in CONTEXT if c != "position"], "defense_team",
            pl.lit(pos).alias("position"), pl.col(f"fielder_{pos}").alias("player_id"),
            ((pl.col("hit_location") == pos).fill_null(False) & pl.col("batter_out")).cast(pl.Float64).alias("credit"),
            (pl.col("hit_location") == pos).fill_null(False).cast(pl.Float64).alias("touch"),
        ) for pos in POSITIONS
    ]).filter(pl.col("player_id").is_not_null() & pl.col("defense_team").is_not_null())
    rows = rows.with_columns([
        pl.col(c).fill_null("UNKNOWN") for c in ["stand", "p_throws", "park_key"]
    ])
    assert rows["credit"].sum() <= balls.height
    groups = rows.group_by(CONTEXT + ["defense_team"]).agg(
        pl.len().alias("n"), pl.col("credit").sum().alias("c"), pl.col("touch").sum().alias("t")
    )
    for keys, prefix in [(CONTEXT, "local"), (LEAGUE, "league")]:
        total = groups.group_by(keys).agg(*[pl.col(c).sum().alias(f"{prefix}_{c}") for c in ["n", "c", "t"]])
        own = groups.group_by(keys + ["defense_team"]).agg(*[pl.col(c).sum().alias(f"own_{prefix}_{c}") for c in ["n", "c", "t"]])
        groups = groups.join(total, on=keys).join(own, on=keys + ["defense_team"])
        groups = groups.with_columns(*[(pl.col(f"{prefix}_{c}") - pl.col(f"own_{prefix}_{c}")).alias(f"other_{prefix}_{c}") for c in ["n", "c", "t"]])
    assert groups["other_league_n"].min() > 0
    groups = groups.with_columns(
        ((pl.col("other_local_c") + 250 * pl.col("other_league_c") / pl.col("other_league_n")) / (pl.col("other_local_n") + 250)).alias("expected_complete"),
        ((pl.col("other_local_c") + 250 * pl.col("other_league_c") / pl.col("other_league_t")) / (pl.col("other_local_t") + 250)).alias("expected_legacy"),
    )
    assert groups.select(pl.col("expected_legacy").is_finite().all()).item()
    rows = rows.join(groups.select(CONTEXT + ["defense_team", "expected_complete", "expected_legacy", "other_local_n"]), on=CONTEXT + ["defense_team"])
    return rows.group_by("season", "level", "league_id", "position", "player_id").agg(
        pl.len().alias("ground_balls"), pl.col("credit").sum().alias("credits"),
        pl.col("touch").sum().alias("touches"), pl.col("expected_complete").sum().alias("expected_credits"),
        (pl.col("touch") * pl.col("expected_legacy")).sum().alias("legacy_expected_credits"),
        (pl.col("other_local_n") == 0).sum().alias("no_other_local_exposures"),
    ), {"source_balls": frame.height, "eligible_balls": balls.height,
        "known_position_exposures": rows.height, "credits": rows["credit"].sum(),
        "unattributed_position_exposures": 3 * balls.height - rows.height}


def pooled(annual_frame, origin):
    f = annual_frame.filter(pl.col("season").is_between(origin - 2, origin)).with_columns(
        pl.lit(.5).pow(origin - pl.col("season")).alias("w")
    )
    f = f.group_by("player_id", "position").agg(*[
        (pl.col(c) * pl.col("w")).sum().alias(c) for c in
        ["ground_balls", "credits", "touches", "expected_credits", "legacy_expected_credits"]
    ])
    f = f.with_columns(
        ((pl.col("credits") - pl.col("expected_credits")) / (pl.col("ground_balls") + 600)).alias("complete_rate"),
        ((pl.col("credits") - pl.col("legacy_expected_credits")) / (pl.col("touches") + 600)).alias("legacy_rate"),
    )
    return f


def profile(row):
    age = row["age"]
    band = "unknown" if age is None else "<=20" if age <= 20 else "21-24" if age <= 24 else "25-29" if age <= 29 else "30+"
    pos = max(POSITIONS, key=lambda p: row[f"gb_{p}"])
    return row["level"], band, pos, row["prior_mlb_defense"]


def check_support(train, test, features, origin, fold):
    assert train["target_year"].max() <= origin
    assert train["origin_year"].max() < origin
    assert set(train["player_id"]).isdisjoint(test["player_id"])
    assert train.select("origin_year", "player_id").is_duplicated().sum() == 0
    assert test.select("origin_year", "player_id").is_duplicated().sum() == 0
    assert np.isfinite(train.select(features).to_numpy()).all()
    assert np.isfinite(test.select(features).to_numpy()).all()
    counts = {}
    for row in train.iter_rows(named=True):
        counts.setdefault(profile(row), set()).add(row["player_id"])
    support = [len(counts.get(profile(row), set())) for row in test.iter_rows(named=True)]
    distinct = train["player_id"].n_unique()
    years = train["target_year"].n_unique()
    return {"origin": origin, "fold": fold, "training_rows": train.height,
        "training_people": distinct, "training_target_years": years,
        "test_rows": test.height, "zero_profile": sum(n == 0 for n in support),
        "sparse_profile": sum(n < 20 for n in support),
        "fit_allowed": distinct >= 30 and years >= 2}, support
