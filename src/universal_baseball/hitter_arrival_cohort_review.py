"""Outcome-blind readiness profiles and explicit calendar-context support."""
import polars as pl

FIELDS = ["row_id", "AAA_0_pa", "AA_0_pa", "scout_rank_score_0", "on_40man",
          "milb_canceled_0", "milb_canceled_1", "milb_canceled_2"]
KEYS = ["prior_debut", "upper_now", "upper_exposure", "age_band",
        "protected_listing", "fresh_rank_positive", "calendar_context"]


def profiles(f):
    upper = pl.col("AAA_0_pa") + pl.col("AA_0_pa")
    return f.with_columns(
        (upper > 0).alias("upper_now"),
        pl.when(upper == 0).then(pl.lit("none"))
        .when(upper < 200).then(pl.lit("under200"))
        .otherwise(pl.lit("200plus")).alias("upper_exposure"),
        pl.when(pl.col("age") <= 25).then(pl.lit("through25"))
        .when(pl.col("age") <= 33).then(pl.lit("26to33"))
        .otherwise(pl.lit("34plus")).alias("age_band"),
        (pl.col("on_40man") > 0).alias("protected_listing"),
        (pl.col("scout_rank_score_0") > 0).alias("fresh_rank_positive"),
        pl.concat_str([pl.col("milb_canceled_"+str(k)).cast(pl.Int8).cast(pl.String)
                       for k in range(3)], separator="/").alias("calendar_context"),
        pl.when(pl.col("AAA_0_pa") > 0).then(pl.lit("some_AAA"))
        .when(pl.col("AA_0_pa") > 0).then(pl.lit("AA_without_AAA"))
        .otherwise(pl.lit("no_current_upper" )).alias("upper_level"),
    )


def support(train, query):
    tr, te = profiles(train), profiles(query)
    generic = KEYS[:-1]
    counts = tr.group_by(generic).agg(pl.col("player_id").n_unique().alias("readiness_people"))
    exact = tr.group_by(KEYS).agg(pl.col("player_id").n_unique().alias("calendar_readiness_people"))
    return te.select("row_id", *KEYS).join(counts, on=generic, how="left", validate="m:1").join(
        exact, on=KEYS, how="left", validate="m:1").with_columns(
            pl.col("readiness_people").fill_null(0), pl.col("calendar_readiness_people").fill_null(0)
        ).with_columns(
            (pl.col("calendar_readiness_people") == 0).alias("calendar_context_absent"),
            (pl.col("calendar_readiness_people") < 20).alias("calendar_context_under20_warning"))


def probability_bands(f):
    p = pl.col("observation_p")
    return f.with_columns(
        pl.when(p < .01).then(pl.lit("0_to_.01"))
        .when(p < .1).then(pl.lit(".01_to_.1"))
        .when(p < .3).then(pl.lit(".1_to_.3"))
        .when(p < .7).then(pl.lit(".3_to_.7"))
        .otherwise(pl.lit(".7_to_1")).alias("probability_band"))
