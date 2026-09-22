"""Clean-slate historical hitter features and next-season value targets."""

from __future__ import annotations

from collections.abc import Iterable

import polars as pl

from universal_baseball.conditional_war_rates import HITTER_WAR_ALLOCATION
from universal_baseball.hitter_v2_evaluation import (
    NEUTRAL_WOBA_SCALE,
    NEUTRAL_WOBA_WEIGHTS,
)


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
STAT_COMPONENTS = (
    "plate_appearances",
    "at_bats",
    "hits",
    "doubles",
    "triples",
    "home_runs",
    "base_on_balls",
    "intentional_walks",
    "hit_by_pitch",
    "strike_outs",
    "sac_bunts",
    "sac_flies",
    "stolen_bases",
    "caught_stealing",
    "ground_into_double_play",
)
LEVEL_ORDER = {
    "RK": 0,
    "ROOKIE": 0,
    "A-": 1,
    "A": 2,
    "A+": 3,
    "AA": 4,
    "AAA": 5,
    "MLB": 6,
}
LEVEL_ALIASES = {
    "HIGH_A": "A+",
    "SINGLE_A": "A",
    "ROOKIE_COMPLEX": "RK",
}
MODEL_ORIGINS = (2015, 2016, 2017, 2018, 2021, 2022, 2023, 2024)


def _require(frame: pl.DataFrame, columns: set[str], label: str) -> None:
    if missing := sorted(columns - set(frame.columns)):
        raise ValueError(f"{label} missing fields: {missing}")


def _assert_unique(frame: pl.DataFrame, key: tuple[str, ...], label: str) -> None:
    if frame.group_by(list(key)).len().filter(pl.col("len") != 1).height:
        raise ValueError(f"{label} violates {'/'.join(key)} grain")


def build_hitter_stat_features(frame: pl.DataFrame) -> pl.DataFrame:
    """Aggregate team/level batting lines to one player-season feature row."""

    _require(
        frame,
        {"season", "player_id", "level_group", *STAT_COMPONENTS},
        "affiliated hitter statistics",
    )
    source = frame.with_columns(
        pl.col("level_group").cast(pl.String).str.to_uppercase().alias("_level"),
    ).with_columns(
        pl.col("_level").replace(LEVEL_ALIASES).alias("_level")
    ).with_columns(
        pl.col("_level")
        .replace_strict(LEVEL_ORDER, default=-1)
        .cast(pl.Int64)
        .alias("_level_rank")
    )
    if source.filter(pl.col("_level_rank") < 0).height:
        unsupported = sorted(source.filter(pl.col("_level_rank") < 0)["_level"].unique())
        raise ValueError(f"unsupported hitter levels: {unsupported}")

    level_pa = (
        source.group_by("season", "player_id", "_level")
        .agg(pl.col("plate_appearances").sum().alias("pa"))
        .pivot(on="_level", index=["season", "player_id"], values="pa")
    )
    for level in LEVEL_ORDER:
        if level not in level_pa.columns:
            level_pa = level_pa.with_columns(pl.lit(0).alias(level))
    level_pa = level_pa.select(
        "season",
        "player_id",
        *(pl.col(level).fill_null(0).alias(f"pa_level__{level}") for level in LEVEL_ORDER),
    )

    totals = source.group_by("season", "player_id").agg(
        *(pl.col(column).sum().alias(column) for column in STAT_COMPONENTS),
        pl.col("_level")
        .sort_by("_level_rank")
        .last()
        .alias("highest_level"),
        pl.col("reported_age").drop_nulls().mean().alias("reported_age")
        if "reported_age" in source.columns
        else pl.lit(None, dtype=pl.Float64).alias("reported_age"),
    )
    totals = totals.with_columns(
        (pl.col("base_on_balls") - pl.col("intentional_walks")).alias("ubb"),
        (
            pl.col("hits")
            - pl.col("doubles")
            - pl.col("triples")
            - pl.col("home_runs")
        ).alias("singles"),
    ).with_columns(
        (
            pl.col("plate_appearances")
            - pl.sum_horizontal(
                "ubb", "hit_by_pitch", "singles", "doubles", "triples", "home_runs"
            )
        ).alias("other_pa")
    )
    if totals.filter(
        pl.any_horizontal(
            pl.col("ubb") < 0,
            pl.col("singles") < 0,
            pl.col("other_pa") < 0,
        )
    ).height:
        raise ValueError("hitter component accounting produced a negative count")
    rate_columns = {
        "ubb_rate": "ubb",
        "bb_rate": "base_on_balls",
        "ibb_rate": "intentional_walks",
        "hbp_rate": "hit_by_pitch",
        "strikeout_rate": "strike_outs",
        "single_rate": "singles",
        "double_rate": "doubles",
        "triple_rate": "triples",
        "home_run_rate": "home_runs",
        "other_pa_rate": "other_pa",
        "stolen_base_rate": "stolen_bases",
        "caught_stealing_rate": "caught_stealing",
        "gidp_rate": "ground_into_double_play",
    }
    totals = totals.with_columns(
        pl.col("plate_appearances").log1p().alias("log_plate_appearances"),
        *[
            (pl.col(source_column) / pl.col("plate_appearances")).alias(output)
            for output, source_column in rate_columns.items()
        ],
    ).with_columns(
        pl.col("plate_appearances").fill_nan(0),
        *(
            pl.col(column).fill_nan(0.0).fill_null(0.0)
            for column in rate_columns
        ),
    )
    return totals.join(
        level_pa, on=["season", "player_id"], how="left", validate="1:1"
    ).sort("season", "player_id")


def build_hitter_contact_features(events: pl.DataFrame) -> pl.DataFrame:
    """Build joint contact-type/outcome features without preselecting interactions."""

    _require(
        events,
        {"season", "player_id", "source_level", "core_bin", "canonical_outcome"},
        "hitter contact events",
    )
    unsupported_bins = sorted(set(events["core_bin"].unique()) - set(CONTACT_BINS))
    unsupported_outcomes = sorted(
        set(events["canonical_outcome"].unique()) - set(CONTACT_OUTCOMES)
    )
    if unsupported_bins or unsupported_outcomes:
        raise ValueError(
            f"unsupported contact cells: bins={unsupported_bins}, outcomes={unsupported_outcomes}"
        )
    keyed = events.with_columns(
        (pl.col("core_bin") + pl.lit("___") + pl.col("canonical_outcome")).alias(
            "_cell"
        ),
        pl.col("source_level").cast(pl.String).str.to_uppercase().alias("_level"),
    ).with_columns(
        pl.col("_level").replace(LEVEL_ALIASES).alias("_level")
    ).with_columns(
        pl.col("_level")
        .replace_strict(LEVEL_ORDER, default=-1)
        .cast(pl.Int64)
        .alias("_level_rank")
    )
    if keyed.filter(pl.col("_level_rank") < 0).height:
        unsupported = sorted(keyed.filter(pl.col("_level_rank") < 0)["_level"].unique())
        raise ValueError(f"unsupported contact levels: {unsupported}")
    totals = keyed.group_by("season", "player_id").agg(
        pl.len().alias("contact_events"),
        pl.col("_level")
        .sort_by("_level_rank")
        .last()
        .alias("contact_highest_level"),
    )
    level_contacts = (
        keyed.group_by("season", "player_id", "_level")
        .len(name="level_contacts")
        .pivot(
            on="_level",
            index=["season", "player_id"],
            values="level_contacts",
        )
    )
    for level in LEVEL_ORDER:
        if level not in level_contacts.columns:
            level_contacts = level_contacts.with_columns(pl.lit(0).alias(level))
    level_contacts = level_contacts.select(
        "season",
        "player_id",
        *(
            pl.col(level).fill_null(0).alias(f"contacts_level__{level}")
            for level in LEVEL_ORDER
        ),
    )
    cells = (
        keyed.group_by("season", "player_id", "_cell")
        .len(name="cell_count")
        .pivot(
            on="_cell",
            index=["season", "player_id"],
            values="cell_count",
        )
    )
    all_cells = [f"{contact_bin}___{outcome}" for contact_bin in CONTACT_BINS for outcome in CONTACT_OUTCOMES]
    for cell in all_cells:
        if cell not in cells.columns:
            cells = cells.with_columns(pl.lit(0).alias(cell))
    result = totals.join(
        cells, on=["season", "player_id"], how="left", validate="1:1"
    ).join(
        level_contacts, on=["season", "player_id"], how="left", validate="1:1"
    )
    prior = 0.5
    result = result.with_columns(
        pl.col("contact_events").log1p().alias("log_contact_events"),
        *(
            (
                (pl.col(cell).fill_null(0) + prior)
                / (pl.col("contact_events") + prior * len(all_cells))
            ).alias(f"contact_cell_rate__{cell}")
            for cell in all_cells
        ),
    )
    return result.select(
        "season",
        "player_id",
        "contact_events",
        "log_contact_events",
        "contact_highest_level",
        *(f"contacts_level__{level}" for level in LEVEL_ORDER),
        *(f"contact_cell_rate__{cell}" for cell in all_cells),
    ).sort("season", "player_id")


def build_neutral_mlb_value_targets(
    hitting: pl.DataFrame,
    *,
    runs_per_win: float = 10.0,
) -> pl.DataFrame:
    """Compute batting-plus-replacement value from observed MLB components."""

    required = {
        "season",
        "player_id",
        "batting_plate_appearances",
        "batting_hits",
        "batting_doubles",
        "batting_triples",
        "batting_home_runs",
        "batting_base_on_balls",
        "batting_intentional_walks",
        "batting_hit_by_pitch",
    }
    _require(hitting, required, "MLB hitting outcomes")
    if runs_per_win <= 0:
        raise ValueError("runs_per_win must be positive")
    grouped = (
        hitting.group_by("season", "player_id")
        .agg(*(pl.col(column).sum() for column in required - {"season", "player_id"}))
        .filter(pl.col("batting_plate_appearances") > 0)
        .with_columns(
        (pl.col("batting_base_on_balls") - pl.col("batting_intentional_walks")).alias(
            "ubb"
        ),
        pl.col("batting_hit_by_pitch").alias("hbp"),
        (
            pl.col("batting_hits")
            - pl.col("batting_doubles")
            - pl.col("batting_triples")
            - pl.col("batting_home_runs")
        ).alias("single"),
        pl.col("batting_doubles").alias("double"),
        pl.col("batting_triples").alias("triple"),
        pl.col("batting_home_runs").alias("hr"),
        )
    )
    weights = {
        "ubb": NEUTRAL_WOBA_WEIGHTS["UBB"],
        "hbp": NEUTRAL_WOBA_WEIGHTS["HBP"],
        "single": NEUTRAL_WOBA_WEIGHTS["1B"],
        "double": NEUTRAL_WOBA_WEIGHTS["2B"],
        "triple": NEUTRAL_WOBA_WEIGHTS["3B"],
        "hr": NEUTRAL_WOBA_WEIGHTS["HR"],
    }
    environment = grouped.group_by("season").agg(
        pl.col("batting_plate_appearances").sum().alias("league_pa"),
        *(pl.col(component).sum().alias(f"league_{component}") for component in weights),
    ).with_columns(
        sum(
            pl.col(f"league_{component}") / pl.col("league_pa") * weight
            for component, weight in weights.items()
        ).alias("league_woba"),
        (HITTER_WAR_ALLOCATION * runs_per_win * 600.0 / pl.col("league_pa")).alias(
            "replacement_runs_per_600"
        ),
    )
    return (
        grouped.join(environment, on="season", validate="m:1")
        .with_columns(
            (
                sum(pl.col(component) * weight for component, weight in weights.items())
                / pl.col("batting_plate_appearances")
            ).alias("observed_woba")
        )
        .with_columns(
            (
                (pl.col("observed_woba") - pl.col("league_woba"))
                * 600.0
                / NEUTRAL_WOBA_SCALE
            ).alias("batting_runs_above_average_per_600")
        )
        .with_columns(
            (
                (
                    pl.col("batting_runs_above_average_per_600")
                    + pl.col("replacement_runs_per_600")
                )
                / runs_per_win
            ).alias("conditional_component_war_per_600")
        )
        .with_columns(
            (
                pl.col("batting_plate_appearances")
                * pl.col("conditional_component_war_per_600")
                / 600.0
            ).alias("component_war"),
            (pl.col("batting_plate_appearances") > 0)
            .cast(pl.Int8)
            .alias("mlb_active"),
        )
        .select(
            "season",
            "player_id",
            pl.col("batting_plate_appearances").alias("mlb_pa"),
            "mlb_active",
            "conditional_component_war_per_600",
            "component_war",
        )
        .sort("season", "player_id")
    )


def build_hitter_value_panel(
    stat_features: pl.DataFrame,
    contact_features: pl.DataFrame,
    age_features: pl.DataFrame,
    value_targets: pl.DataFrame,
    *,
    origins: Iterable[int] = MODEL_ORIGINS,
    lags: tuple[int, ...] = (0, 1, 2),
) -> pl.DataFrame:
    """Build chronology-safe rows for total value and component diagnostics."""

    origins = tuple(int(value) for value in origins)
    if any(year >= 2025 for year in origins):
        raise ValueError("development origins may not expose a 2026 target")
    if 2019 in origins or 2020 in origins:
        raise ValueError("2019/2020 cannot define a normal next-season MiLB transition")
    if not lags or lags[0] != 0 or any(lag < 0 for lag in lags):
        raise ValueError("lags must begin at zero and be nonnegative")
    _assert_unique(value_targets, ("season", "player_id"), "value targets")
    panel = _build_hitter_feature_rows(
        stat_features,
        contact_features,
        age_features,
        origins=origins,
        lags=lags,
    )

    target = value_targets.with_columns(
        (pl.col("season") - 1).alias("origin_year")
    ).select(
        "origin_year",
        "player_id",
        pl.col("mlb_pa").alias("target_mlb_pa"),
        pl.col("mlb_active").alias("target_mlb_active"),
        pl.col("conditional_component_war_per_600").alias(
            "target_conditional_component_war_per_600"
        ),
        pl.col("component_war").alias("target_component_war"),
    )
    panel = panel.join(
        target,
        on=["origin_year", "player_id"],
        how="left",
        validate="1:1",
    ).with_columns(
        pl.col("target_mlb_pa").fill_null(0.0),
        pl.col("target_mlb_active").fill_null(0),
        pl.col("target_component_war").fill_null(0.0),
    )
    if panel.filter(pl.col("target_season") >= 2026).height:
        raise ValueError("protected 2026 targets entered the hitter value panel")
    return panel.sort("origin_year", "player_id")


def _build_hitter_feature_rows(
    stat_features: pl.DataFrame,
    contact_features: pl.DataFrame,
    age_features: pl.DataFrame,
    *,
    origins: Iterable[int],
    lags: tuple[int, ...],
) -> pl.DataFrame:
    for frame, label in (
        (stat_features, "stat features"),
        (contact_features, "contact features"),
        (age_features, "age features"),
    ):
        _assert_unique(frame, ("season", "player_id"), label)

    base = stat_features.join(
        contact_features,
        on=["season", "player_id"],
        how="left",
        validate="1:1",
    ).with_columns(
        pl.col("contact_events")
        .is_not_null()
        .cast(pl.Int8)
        .alias("contact_feature_available"),
        pl.lit(1).cast(pl.Int8).alias("season_available"),
        pl.col("contact_events").fill_null(0),
        pl.col("log_contact_events").fill_null(0.0),
        *(
            pl.col(f"contacts_level__{level}").fill_null(0)
            for level in LEVEL_ORDER
        ),
    ).join(
        age_features,
        on=["season", "player_id"],
        how="left",
        validate="1:1",
    )
    panel = base.filter(pl.col("season").is_in(origins)).select(
        pl.col("season").alias("origin_year"), "player_id"
    )
    feature_columns = [column for column in base.columns if column not in {"season", "player_id"}]
    for lag in lags:
        renamed = {
            column: f"lag{lag}__{column}"
            for column in feature_columns
        }
        shifted = base.with_columns((pl.col("season") + lag).alias("origin_year")).select(
            "origin_year", "player_id", *feature_columns
        ).rename(renamed)
        panel = panel.join(
            shifted,
            on=["origin_year", "player_id"],
            how="left",
            validate="1:1",
        ).with_columns(
            pl.col(f"lag{lag}__season_available")
            .is_null()
            .cast(pl.Int8)
            .alias(f"lag{lag}__missing")
        ).with_columns(
            pl.col(f"lag{lag}__season_available").fill_null(0),
            pl.col(f"lag{lag}__contact_feature_available").fill_null(0),
        )

    return panel.with_columns(
        (pl.col("origin_year") + 1).alias("target_season"),
        (pl.col("origin_year") >= 2021).cast(pl.Int8).alias("post_2020_reorg"),
        (pl.col("origin_year") <= 2019)
        .cast(pl.Int8)
        .alias("short_season_structure_present"),
    ).sort("origin_year", "player_id")


def build_hitter_forecast_panel(
    stat_features: pl.DataFrame,
    contact_features: pl.DataFrame,
    age_features: pl.DataFrame,
    *,
    origin: int,
    lags: tuple[int, ...] = (0, 1, 2),
) -> pl.DataFrame:
    """Build target-free rows for a protected next-season forecast."""

    origin = int(origin)
    if origin in {2019, 2020}:
        raise ValueError("2019/2020 cannot define a normal next-season MiLB transition")
    if not lags or lags[0] != 0 or any(lag < 0 for lag in lags):
        raise ValueError("lags must begin at zero and be nonnegative")
    return _build_hitter_feature_rows(
        stat_features,
        contact_features,
        age_features,
        origins=(origin,),
        lags=lags,
    )
