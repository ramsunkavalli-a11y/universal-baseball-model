"""Materialize chronology-safe inputs for the detailed hitter challenger.

The functions in this module stop at feature construction.  They deliberately do
not choose a forecasting algorithm or inspect 2026.  The forecast grain is one
player and one completed source season; the target is the following season.
"""

from __future__ import annotations

import math

import polars as pl


EVENT_KEY = ("season", "game_pk", "at_bat_index")
CONTACT_BINS = (
    "PULL_GB",
    "CENTER_GB",
    "OPPO_GB",
    "PULL_LD",
    "CENTER_LD",
    "OPPO_LD",
    "PULL_OFFB",
    "CENTER_OFFB",
    "OPPO_OFFB",
    "IFFB",
)
CONTACT_OUTCOMES = (
    "1B",
    "2B",
    "3B",
    "HR",
    "ROE",
    "FC_REACH",
    "SF",
    "MULTI_OUT",
    "OTHER_OUT",
)
PARK_COMPONENTS = ("ubb", "hbp", "single", "double", "triple", "hr", "other")
PITCHER_CONTEXT_COLUMNS = (
    "K_prior_pitcher_log_odds_residual",
    "UBB_prior_pitcher_log_odds_residual",
    "HBP_prior_pitcher_log_odds_residual",
    "HR_prior_pitcher_log_odds_residual",
    "NON_HR_REACH_prior_pitcher_log_odds_residual",
    "HIT_COMPOSITION_prior_pitcher_alr_residual_1B",
    "HIT_COMPOSITION_prior_pitcher_alr_residual_2B",
    "HIT_COMPOSITION_prior_pitcher_alr_residual_3B",
)
PITCHER_SUPPORT_COLUMNS = (
    "K_prior_pitcher_denominator",
    "UBB_prior_pitcher_denominator",
    "HBP_prior_pitcher_denominator",
    "HR_prior_pitcher_denominator",
    "NON_HR_REACH_prior_pitcher_denominator",
    "HIT_COMPOSITION_prior_pitcher_denominator",
)


def _require(frame: pl.DataFrame, columns: set[str], label: str) -> None:
    if missing := sorted(columns - set(frame.columns)):
        raise ValueError(f"{label} missing fields: {missing}")


def _assert_unique(frame: pl.DataFrame, key: tuple[str, ...], label: str) -> None:
    if frame.group_by(list(key)).len().filter(pl.col("len") != 1).height:
        raise ValueError(f"{label} violates {'/'.join(key)} grain")


def join_contact_context_events(
    contacts: pl.DataFrame,
    pa_context: pl.DataFrame,
    games: pl.DataFrame,
) -> pl.DataFrame:
    """Join exact terminal contacts to venue and strictly-prior opponent context.

    Every contact survives.  A missing or disagreeing context row gets neutral
    opponent features and an explicit ``opponent_context_known=False`` flag.
    """

    _require(
        contacts,
        {
            *EVENT_KEY,
            "league_id",
            "source_level",
            "player_id",
            "source_pitcher_id",
            "batter_side",
            "core_bin",
            "canonical_outcome",
        },
        "terminal contacts",
    )
    _require(
        pa_context,
        {
            *EVENT_KEY,
            "player_id",
            "pitcher_id",
            "batter_side",
            "pitcher_hand",
            "canonical_outcome",
            "context_label_ready",
            *PITCHER_CONTEXT_COLUMNS,
            *PITCHER_SUPPORT_COLUMNS,
        },
        "PA context",
    )
    _require(
        games,
        {
            "season",
            "game_pk",
            "game_date",
            "sport_id",
            "venue_id",
            "home_team_id",
            "away_team_id",
        },
        "game context",
    )
    _assert_unique(contacts, EVENT_KEY, "terminal contacts")
    _assert_unique(pa_context, EVENT_KEY, "PA context")
    _assert_unique(games, ("season", "game_pk"), "game context")
    if contacts.filter(pl.col("season") >= 2026).height:
        raise ValueError("protected 2026 contacts are not allowed")

    context = pa_context.select(
        *EVENT_KEY,
        pl.col("player_id").alias("context_player_id"),
        pl.col("pitcher_id").alias("context_pitcher_id"),
        pl.col("batter_side").alias("context_batter_side"),
        "pitcher_hand",
        pl.col("canonical_outcome").alias("context_outcome"),
        "context_label_ready",
        *PITCHER_CONTEXT_COLUMNS,
        *PITCHER_SUPPORT_COLUMNS,
    )
    result = contacts.join(
        context, on=list(EVENT_KEY), how="left", validate="1:1"
    ).join(
        games.select(
            "season",
            "game_pk",
            "game_date",
            "sport_id",
            "venue_id",
            "home_team_id",
            "away_team_id",
        ),
        on=["season", "game_pk"],
        how="left",
        validate="m:1",
    )
    exact = (
        pl.col("context_label_ready").fill_null(False)
        & (pl.col("player_id") == pl.col("context_player_id"))
        & (pl.col("source_pitcher_id") == pl.col("context_pitcher_id"))
        & (pl.col("batter_side") == pl.col("context_batter_side"))
        & (pl.col("canonical_outcome") == pl.col("context_outcome"))
        & pl.col("pitcher_hand").is_in(["L", "R"])
    )
    result = result.with_columns(
        exact.alias("opponent_context_known"),
        pl.col("venue_id").is_not_null().alias("venue_known"),
    ).with_columns(
        pl.when(pl.col("opponent_context_known"))
        .then(pl.col(column))
        .otherwise(0.0)
        .fill_nan(0.0)
        .fill_null(0.0)
        .alias(column)
        for column in (*PITCHER_CONTEXT_COLUMNS, *PITCHER_SUPPORT_COLUMNS)
    )
    return result.drop(
        "context_player_id",
        "context_pitcher_id",
        "context_batter_side",
        "context_outcome",
        "context_label_ready",
    ).sort(list(EVENT_KEY))


def make_park_vintage(
    factors: pl.DataFrame,
    *,
    source_season: int,
    prior_exposure: float,
) -> pl.DataFrame:
    """Convert long park factors into one feature row per venue and vintage."""

    _require(
        factors,
        {
            "venue_id",
            "component",
            "training_precision",
            "training_seasons",
            "park_clr_effect",
        },
        "park factors",
    )
    if not math.isfinite(prior_exposure) or prior_exposure < 0:
        raise ValueError("prior_exposure must be finite and nonnegative")
    if set(factors["component"].unique().to_list()) != set(PARK_COMPONENTS):
        raise ValueError("park factor components are incomplete")
    _assert_unique(factors, ("venue_id", "component"), "park factors")
    support = factors.group_by("venue_id").agg(
        pl.col("training_precision").first().alias("park_training_precision"),
        pl.col("training_precision").n_unique().alias("_precision_values"),
        pl.col("training_seasons").first().alias("park_training_seasons"),
        pl.col("training_seasons").n_unique().alias("_season_values"),
    )
    if support.filter(
        (pl.col("_precision_values") != 1) | (pl.col("_season_values") != 1)
    ).height:
        raise ValueError("park support differs across components")
    wide = factors.select("venue_id", "component", "park_clr_effect").pivot(
        on="component", index="venue_id", values="park_clr_effect"
    ).rename({value: f"park_effect__{value}" for value in PARK_COMPONENTS})
    return (
        support.drop("_precision_values", "_season_values")
        .join(wide, on="venue_id", validate="1:1")
        .with_columns(
            pl.lit(int(source_season)).alias("park_factor_through_season"),
            (
                pl.col("park_training_precision")
                / (pl.col("park_training_precision") + prior_exposure)
            ).alias("park_factor_reliability"),
            pl.lit(True).alias("park_factor_known"),
        )
        .sort("venue_id")
    )


def attach_as_of_park_features(
    events: pl.DataFrame, vintages: pl.DataFrame
) -> pl.DataFrame:
    """Attach the factor available at each completed source-season origin."""

    _require(events, {"season", "venue_id"}, "contact events")
    _require(
        vintages,
        {
            "venue_id",
            "park_factor_through_season",
            "park_factor_known",
            "park_training_precision",
            "park_training_seasons",
            "park_factor_reliability",
            *(f"park_effect__{value}" for value in PARK_COMPONENTS),
        },
        "park vintages",
    )
    _assert_unique(
        vintages,
        ("park_factor_through_season", "venue_id"),
        "park vintages",
    )
    result = events.join(
        vintages,
        left_on=["season", "venue_id"],
        right_on=["park_factor_through_season", "venue_id"],
        how="left",
        validate="m:1",
    )
    # Polars removes the identical right join key. Recreate it explicitly so the
    # lineage remains visible in the saved event table.
    return result.with_columns(
        pl.col("season").alias("park_factor_through_season"),
        pl.col("park_factor_known").fill_null(False),
        pl.col("park_training_precision").fill_null(0.0),
        pl.col("park_training_seasons").fill_null(0),
        pl.col("park_factor_reliability").fill_null(0.0),
        *(pl.col(f"park_effect__{value}").fill_null(0.0) for value in PARK_COMPONENTS),
    )


def build_contact_cell_features(
    events: pl.DataFrame, *, player_prior: float = 100.0
) -> pl.DataFrame:
    """Build all 90 smoothed contact-bin by outcome probabilities per player-year."""

    if not math.isfinite(player_prior) or player_prior <= 0:
        raise ValueError("player_prior must be finite and positive")
    _require(
        events,
        {"season", "player_id", "source_level", "core_bin", "canonical_outcome"},
        "contact events",
    )
    invalid_bins = set(events["core_bin"].unique().to_list()) - set(CONTACT_BINS)
    invalid_outcomes = set(events["canonical_outcome"].unique().to_list()) - set(
        CONTACT_OUTCOMES
    )
    if invalid_bins or invalid_outcomes:
        raise ValueError(
            f"unsupported contact cells: bins={sorted(invalid_bins)}, "
            f"outcomes={sorted(invalid_outcomes)}"
        )

    observed_level_counts = events.group_by(
        "season", "source_level", "core_bin", "canonical_outcome"
    ).len(name="_level_cell_n")
    level_bins = events.select("season", "source_level", "core_bin").unique()
    outcome_grid = pl.DataFrame({"canonical_outcome": list(CONTACT_OUTCOMES)})
    level_counts = level_bins.join(outcome_grid, how="cross").join(
        observed_level_counts,
        on=["season", "source_level", "core_bin", "canonical_outcome"],
        how="left",
        validate="1:1",
    ).with_columns(pl.col("_level_cell_n").fill_null(0))
    level_totals = level_counts.group_by(
        "season", "source_level", "core_bin"
    ).agg(pl.col("_level_cell_n").sum().alias("_level_bin_n"))
    level_prior = level_counts.join(
        level_totals,
        on=["season", "source_level", "core_bin"],
        validate="m:1",
    ).with_columns(
        (pl.col("_level_cell_n") / pl.col("_level_bin_n")).alias("_level_prior")
    )
    player_level_bin = events.group_by(
        "season", "player_id", "source_level", "core_bin"
    ).len(name="_player_level_bin_n")
    player_priors = (
        player_level_bin.join(
            level_prior,
            on=["season", "source_level", "core_bin"],
            how="left",
            validate="m:m",
        )
        .group_by("season", "player_id", "core_bin", "canonical_outcome")
        .agg(
            (
                (pl.col("_player_level_bin_n") * pl.col("_level_prior")).sum()
                / pl.col("_player_level_bin_n").sum()
            ).alias("_player_level_prior")
        )
    )
    player_counts = events.group_by(
        "season", "player_id", "core_bin", "canonical_outcome"
    ).len(name="_cell_n")
    player_bins = events.group_by("season", "player_id", "core_bin").len(
        name="_bin_n"
    )
    players = events.select("season", "player_id").unique()
    cells = pl.DataFrame(
        {
            "core_bin": [
                contact_bin
                for contact_bin in CONTACT_BINS
                for _ in CONTACT_OUTCOMES
            ],
            "canonical_outcome": list(CONTACT_OUTCOMES) * len(CONTACT_BINS),
        }
    )
    complete = (
        players.join(cells, how="cross")
        .join(
            player_counts,
            on=["season", "player_id", "core_bin", "canonical_outcome"],
            how="left",
            validate="1:1",
        )
        .join(
            player_bins,
            on=["season", "player_id", "core_bin"],
            how="left",
            validate="m:1",
        )
        .join(
            player_priors,
            on=["season", "player_id", "core_bin", "canonical_outcome"],
            how="left",
            validate="1:1",
        )
        .with_columns(
            pl.col("_cell_n").fill_null(0),
            pl.col("_bin_n").fill_null(0),
        )
    )
    global_counts = events.group_by("season", "canonical_outcome").len(
        name="_global_n"
    )
    global_prior = (
        events.select("season").unique().join(outcome_grid, how="cross")
        .join(
            global_counts,
            on=["season", "canonical_outcome"],
            how="left",
            validate="1:1",
        )
        .with_columns(pl.col("_global_n").fill_null(0))
        .with_columns(
            (pl.col("_global_n") / pl.col("_global_n").sum().over("season")).alias(
                "_global_prior"
            )
        )
        .select("season", "canonical_outcome", "_global_prior")
    )
    complete = complete.join(
        global_prior,
        on=["season", "canonical_outcome"],
        how="left",
        validate="m:1",
    ).with_columns(
        pl.col("_player_level_prior").fill_null(pl.col("_global_prior"))
    ).with_columns(
        (
            (pl.col("_cell_n") + player_prior * pl.col("_player_level_prior"))
            / (pl.col("_bin_n") + player_prior)
        ).alias("_probability")
    )
    probabilities = complete.select(
        "season", "player_id", "core_bin", "canonical_outcome", "_probability"
    ).with_columns(
        pl.concat_str("core_bin", "canonical_outcome", separator="__").alias("_cell")
    ).pivot(
        on="_cell", index=["season", "player_id"], values="_probability"
    ).rename(
        {
            f"{contact_bin}__{outcome}": f"contact_result__{contact_bin}__{outcome}"
            for contact_bin in CONTACT_BINS
            for outcome in CONTACT_OUTCOMES
        }
    )
    bin_grid = pl.DataFrame({"core_bin": list(CONTACT_BINS)})
    support = players.join(bin_grid, how="cross").join(
        player_bins,
        on=["season", "player_id", "core_bin"],
        how="left",
        validate="1:1",
    ).with_columns(pl.col("_bin_n").fill_null(0)).pivot(
        on="core_bin", index=["season", "player_id"], values="_bin_n"
    ).rename(
        {contact_bin: f"contact_count__{contact_bin}" for contact_bin in CONTACT_BINS}
    )
    return players.join(
        probabilities, on=["season", "player_id"], validate="1:1"
    ).join(
        support, on=["season", "player_id"], how="left", validate="1:1"
    ).with_columns(
        *(pl.col(f"contact_count__{value}").fill_null(0) for value in CONTACT_BINS)
    ).sort("season", "player_id")


def build_player_season_features(
    events: pl.DataFrame,
    annual_surfaces: pl.DataFrame,
    *,
    player_prior: float = 100.0,
) -> pl.DataFrame:
    """Aggregate event context and detailed contact cells to player/source season."""

    _require(annual_surfaces, {"season", "player_id", "source_level"}, "annual surfaces")
    _assert_unique(annual_surfaces, ("season", "player_id"), "annual surfaces")
    cells = build_contact_cell_features(events, player_prior=player_prior)
    context = events.group_by("season", "player_id").agg(
        pl.len().alias("materialized_contacts"),
        pl.col("opponent_context_known").mean().alias("opponent_context_known_rate"),
        pl.col("venue_known").mean().alias("venue_known_rate"),
        (pl.col("pitcher_hand") == "L").mean().alias("contact_share_vs_lhp"),
        (pl.col("pitcher_hand") == "R").mean().alias("contact_share_vs_rhp"),
        *(pl.col(value).mean().alias(f"mean__{value}") for value in PITCHER_CONTEXT_COLUMNS),
        *(
            pl.col(value).mean().alias(f"mean__{value}")
            for value in PITCHER_SUPPORT_COLUMNS
        ),
        pl.col("park_factor_known").mean().alias("park_factor_known_rate"),
        pl.col("park_factor_reliability").mean().alias("mean_park_factor_reliability"),
        pl.col("park_training_seasons").mean().alias("mean_park_training_seasons"),
        *(pl.col(f"park_effect__{value}").mean() for value in PARK_COMPONENTS),
    )
    return (
        annual_surfaces.join(
            cells, on=["season", "player_id"], how="inner", validate="1:1"
        )
        .join(context, on=["season", "player_id"], validate="1:1")
        .with_columns((pl.col("season") + 1).alias("target_season"))
        .sort("season", "player_id")
    )


def build_modeling_rows(
    player_features: pl.DataFrame, benchmark: pl.DataFrame
) -> pl.DataFrame:
    """Attach frozen next-year targets and mandatory benchmark predictions."""

    _require(player_features, {"season", "target_season", "player_id"}, "player features")
    _require(
        benchmark,
        {"origin_year", "player_id", "source_level", "target_source_level"},
        "benchmark",
    )
    _assert_unique(player_features, ("season", "player_id"), "player features")
    _assert_unique(benchmark, ("origin_year", "player_id"), "benchmark")
    result = benchmark.join(
        player_features,
        left_on=["origin_year", "player_id"],
        right_on=["season", "player_id"],
        how="inner",
        validate="1:1",
        suffix="__feature",
    ).with_columns((pl.col("origin_year") + 1).alias("target_season"))
    if result.filter(pl.col("target_season") <= pl.col("origin_year")).height:
        raise ValueError("target season must be after every feature origin")
    if result.filter(pl.col("target_season") >= 2026).height:
        raise ValueError("protected 2026 target rows are not allowed")
    return result.sort("origin_year", "player_id")


def build_fold_manifest(modeling_rows: pl.DataFrame) -> pl.DataFrame:
    """Freeze expanding-window train/evaluation membership for every outer fold."""

    _require(modeling_rows, {"origin_year", "target_season", "player_id"}, "modeling rows")
    origins = sorted(int(value) for value in modeling_rows["origin_year"].unique())
    rows: list[dict[str, int | str]] = []
    for evaluation_origin in origins:
        for origin in origins:
            if origin > evaluation_origin:
                continue
            role = "evaluation" if origin == evaluation_origin else "training"
            selected = modeling_rows.filter(pl.col("origin_year") == origin)
            for row in selected.select("player_id", "target_season").iter_rows(named=True):
                rows.append(
                    {
                        "evaluation_origin": evaluation_origin,
                        "row_origin": origin,
                        "target_season": int(row["target_season"]),
                        "player_id": int(row["player_id"]),
                        "role": role,
                    }
                )
    manifest = pl.DataFrame(rows)
    if manifest.filter(
        (pl.col("role") == "training")
        & (pl.col("target_season") > pl.col("evaluation_origin"))
    ).height:
        raise ValueError("fold manifest leaks a future target into training")
    return manifest.sort("evaluation_origin", "role", "row_origin", "player_id")
