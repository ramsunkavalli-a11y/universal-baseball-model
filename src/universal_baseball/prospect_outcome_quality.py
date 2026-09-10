"""Observed post-debut workload paths for prospect outcome-quality priors."""

from __future__ import annotations

import polars as pl


SHORTENED_2020_SCALE = 162.0 / 60.0


def build_post_debut_workload_paths(
    people: pl.DataFrame,
    stats: pl.DataFrame,
    *,
    player_type: str,
    horizon: int = 6,
    shortened_2020_scale: float = SHORTENED_2020_SCALE,
) -> pl.DataFrame:
    """Build complete six-calendar-year MLB workload paths from true debut dates."""

    if player_type not in {"hitter", "pitcher"}:
        raise ValueError("player_type must be hitter or pitcher")
    if horizon < 1 or shortened_2020_scale <= 0:
        raise ValueError("horizon and shortened-season scale must be positive")
    required_people = {"player_id", "mlb_debut_date"}
    if missing := sorted(required_people - set(people.columns)):
        raise ValueError(f"people missing columns: {missing}")
    workload = "batting_pa" if player_type == "hitter" else "pitching_bf"
    required_stats = {"season", "player_id", workload}
    if player_type == "pitcher":
        required_stats.update({"pitching_games", "pitching_starts"})
    if missing := sorted(required_stats - set(stats.columns)):
        raise ValueError(f"stats missing columns: {missing}")
    minimum_season = int(stats.get_column("season").min())
    maximum_season = int(stats.get_column("season").max())
    maximum_complete_debut = maximum_season - horizon + 1
    eligible = (
        people.filter(pl.col("mlb_debut_date").is_not_null())
        .select("player_id", "mlb_debut_date")
        .with_columns(pl.col("mlb_debut_date").dt.year().alias("debut_year"))
        .filter(
            pl.col("debut_year").is_between(
                minimum_season, maximum_complete_debut, closed="both"
            )
        )
        .unique("player_id")
    )
    if eligible.is_empty():
        raise ValueError("no complete debut cohorts in supplied history")
    aggregated_expressions: list[pl.Expr] = [pl.col(workload).sum().alias("workload")]
    if player_type == "pitcher":
        aggregated_expressions.extend(
            [
                pl.col("pitching_games").sum().alias("games"),
                pl.col("pitching_starts").sum().alias("starts"),
            ]
        )
    season_stats = stats.group_by("player_id", "season").agg(
        *aggregated_expressions
    )
    rows: list[dict[str, object]] = []
    stats_lookup = {
        (int(row["player_id"]), int(row["season"])): row
        for row in season_stats.iter_rows(named=True)
    }
    for person in eligible.iter_rows(named=True):
        player_id = int(person["player_id"])
        debut_year = int(person["debut_year"])
        total = 0.0
        active_seasons = 0
        meaningful_seasons = 0
        regular_seasons = 0
        established_support_seasons = 0
        games = 0.0
        starts = 0.0
        for season in range(debut_year, debut_year + horizon):
            observed = stats_lookup.get((player_id, season), {})
            raw_workload = float(observed.get("workload") or 0.0)
            adjusted = raw_workload * (
                shortened_2020_scale if season == 2020 else 1.0
            )
            total += adjusted
            active_seasons += int(raw_workload > 0)
            meaningful_seasons += int(adjusted >= 200.0)
            regular_seasons += int(adjusted >= 400.0)
            support_threshold = 300.0 if player_type == "hitter" else 200.0
            established_support_seasons += int(adjusted >= support_threshold)
            games += float(observed.get("games") or 0.0)
            starts += float(observed.get("starts") or 0.0)
        if total <= 0:
            # A true MLB debut can be as a fielder, runner, or the other player type.
            # It is not evidence for this workload population.
            continue
        outcome_tier = "fringe" if meaningful_seasons == 0 else "meaningful"
        if meaningful_seasons == 0:
            outcome_tier_v2 = "fringe"
        elif regular_seasons >= 1 or established_support_seasons >= 2:
            outcome_tier_v2 = "established"
        else:
            outcome_tier_v2 = "meaningful_only"
        if player_type == "hitter":
            role = "hitter"
        elif games <= 0:
            role = "unknown"
        elif starts == 0:
            role = "reliever"
        elif starts * 2 >= games:
            role = "starter"
        else:
            role = "swingman"
        rows.append(
            {
                "player_id": player_id,
                "player_type": player_type,
                "debut_year": debut_year,
                "window_end_year": debut_year + horizon - 1,
                "horizon_years": horizon,
                "active_seasons": active_seasons,
                "meaningful_seasons": meaningful_seasons,
                "regular_seasons": regular_seasons,
                "established_support_seasons": established_support_seasons,
                "outcome_tier": outcome_tier,
                "outcome_tier_v2": outcome_tier_v2,
                "career_role": role,
                "adjusted_total_workload": total,
                "shortened_2020_scale": shortened_2020_scale,
            }
        )
    return pl.DataFrame(rows, infer_schema_length=None).sort(
        ["player_type", "debut_year", "player_id"]
    )


def build_post_debut_annual_workload_paths(
    people: pl.DataFrame,
    stats: pl.DataFrame,
    *,
    player_type: str,
    horizon: int = 6,
    shortened_2020_scale: float = SHORTENED_2020_SCALE,
) -> pl.DataFrame:
    """Retain each mature player's complete ordered post-debut workload vector."""

    summaries = build_post_debut_workload_paths(
        people,
        stats,
        player_type=player_type,
        horizon=horizon,
        shortened_2020_scale=shortened_2020_scale,
    )
    workload = "batting_pa" if player_type == "hitter" else "pitching_bf"
    aggregations: list[pl.Expr] = [pl.col(workload).sum().alias("workload")]
    if player_type == "pitcher":
        aggregations.extend(
            pl.col(column).sum().alias(output)
            for column, output in (
                ("pitching_games", "games"),
                ("pitching_starts", "starts"),
            )
        )
    season_stats = stats.group_by("player_id", "season").agg(*aggregations)
    lookup = {
        (int(row["player_id"]), int(row["season"])): row
        for row in season_stats.iter_rows(named=True)
    }
    rows: list[dict[str, object]] = []
    for summary in summaries.iter_rows(named=True):
        player_id = int(summary["player_id"])
        debut_year = int(summary["debut_year"])
        for path_year in range(1, horizon + 1):
            season = debut_year + path_year - 1
            observed = lookup.get((player_id, season), {})
            raw_workload = float(observed.get("workload") or 0.0)
            adjusted_workload = raw_workload * (
                shortened_2020_scale if season == 2020 else 1.0
            )
            games = float(observed.get("games") or 0.0)
            starts = float(observed.get("starts") or 0.0)
            if raw_workload <= 0:
                annual_role = "inactive"
            elif player_type == "hitter":
                annual_role = "hitter"
            elif games <= 0:
                annual_role = "unknown"
            elif starts == 0:
                annual_role = "reliever"
            elif starts * 2 >= games:
                annual_role = "starter"
            else:
                annual_role = "swingman"
            rows.append(
                {
                    "path_player_id": player_id,
                    "player_type": player_type,
                    "debut_year": debut_year,
                    "window_end_year": int(summary["window_end_year"]),
                    "outcome_tier_v2": str(summary["outcome_tier_v2"]),
                    "career_role": str(summary["career_role"]),
                    "path_year": path_year,
                    "source_season": season,
                    "adjusted_workload": adjusted_workload,
                    "active": raw_workload > 0,
                    "annual_role": annual_role,
                    "games": games,
                    "starts": starts,
                    "shortened_2020_scale": shortened_2020_scale,
                }
            )
    result = pl.DataFrame(rows, infer_schema_length=None).sort(
        ["player_type", "debut_year", "path_player_id", "path_year"]
    )
    path_checks = result.group_by("path_player_id", "player_type").agg(
        pl.len().alias("years"),
        pl.col("path_year").n_unique().alias("unique_years"),
        pl.col("adjusted_workload").sum().alias("annual_total"),
    ).join(
        summaries.select(
            pl.col("player_id").alias("path_player_id"),
            "player_type",
            "adjusted_total_workload",
        ),
        on=["path_player_id", "player_type"],
        how="inner",
        validate="1:1",
    )
    if path_checks.height != summaries.height or path_checks.filter(
        (pl.col("years") != horizon)
        | (pl.col("unique_years") != horizon)
        | (
            (pl.col("annual_total") - pl.col("adjusted_total_workload")).abs()
            > 1e-8
        )
    ).height:
        raise RuntimeError("annual workload paths do not reconcile to career summaries")
    return result


def summarize_workload_priors(paths: pl.DataFrame) -> pl.DataFrame:
    """Summarize means and tails without dropping real high-workload careers."""

    required = {
        "player_type", "outcome_tier", "career_role", "adjusted_total_workload"
    }
    if missing := sorted(required - set(paths.columns)):
        raise ValueError(f"paths missing columns: {missing}")
    grouped = paths.group_by("player_type", "outcome_tier", "career_role").agg(
        pl.len().alias("players"),
        pl.col("adjusted_total_workload").mean().alias("mean_workload"),
        pl.col("adjusted_total_workload").median().alias("median_workload"),
        pl.col("adjusted_total_workload").quantile(0.1).alias("p10_workload"),
        pl.col("adjusted_total_workload").quantile(0.9).alias("p90_workload"),
        pl.col("active_seasons").mean().alias("mean_active_seasons"),
    )
    pooled = (
        paths.group_by("player_type", "outcome_tier")
        .agg(
            pl.len().alias("players"),
            pl.col("adjusted_total_workload").mean().alias("mean_workload"),
            pl.col("adjusted_total_workload").median().alias("median_workload"),
            pl.col("adjusted_total_workload").quantile(0.1).alias("p10_workload"),
            pl.col("adjusted_total_workload").quantile(0.9).alias("p90_workload"),
            pl.col("active_seasons").mean().alias("mean_active_seasons"),
        )
        .with_columns(pl.lit("ALL").alias("career_role"))
        .select(grouped.columns)
    )
    return (
        pl.concat([grouped, pooled], how="vertical")
        .sort("player_type", "outcome_tier", "career_role")
    )


def summarize_three_tier_workload_priors(paths: pl.DataFrame) -> pl.DataFrame:
    """Summarize fringe, meaningful-only, and established workload priors."""

    required = {
        "player_type", "outcome_tier_v2", "career_role", "adjusted_total_workload"
    }
    if missing := sorted(required - set(paths.columns)):
        raise ValueError(f"paths missing columns: {missing}")
    projected = paths.with_columns(
        pl.col("outcome_tier_v2").alias("outcome_tier")
    )
    return summarize_workload_priors(projected)


def workload_prior(
    priors: pl.DataFrame,
    *,
    player_type: str,
    outcome_tier: str,
    career_role: str,
    minimum_role_players: int = 30,
) -> tuple[float, str]:
    """Use a supported role mean, otherwise regress fully to the pooled tier mean."""

    if minimum_role_players < 1:
        raise ValueError("minimum_role_players must be positive")
    cell = priors.filter(
        (pl.col("player_type") == player_type)
        & (pl.col("outcome_tier") == outcome_tier)
        & (pl.col("career_role") == career_role)
    )
    if cell.height == 1 and int(cell.item(0, "players")) >= minimum_role_players:
        return float(cell.item(0, "mean_workload")), "role"
    pooled = priors.filter(
        (pl.col("player_type") == player_type)
        & (pl.col("outcome_tier") == outcome_tier)
        & (pl.col("career_role") == "ALL")
    )
    if pooled.height != 1:
        raise ValueError("workload priors require one pooled player-type/tier row")
    return float(pooled.item(0, "mean_workload")), "pooled"
