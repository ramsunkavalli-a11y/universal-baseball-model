"""Dated current-season workload, WAR, and base-salary remainder helpers."""

from __future__ import annotations

from datetime import date

import polars as pl


def project_team_schedule_calendar(
    payload: dict,
    *,
    season: int,
    as_of_date: date,
) -> tuple[pl.DataFrame, int, int]:
    """Project regular-season games to team calendars and league game counts."""

    games: dict[int, dict] = {}
    for day in payload.get("dates") or []:
        for game in day.get("games") or []:
            if str(game.get("gameType") or "") != "R":
                continue
            game_pk = int(game["gamePk"])
            official_date = date.fromisoformat(str(game["officialDate"]))
            teams = game.get("teams") or {}
            home_id = int((teams.get("home") or {}).get("team", {})["id"])
            away_id = int((teams.get("away") or {}).get("team", {})["id"])
            status = game.get("status") or {}
            postponed = str(status.get("detailedState") or "") == "Postponed"
            final = (
                str(status.get("abstractGameState") or "") == "Final"
                and not postponed
            )
            candidate = {
                "official_date": official_date,
                "home_id": home_id,
                "away_id": away_id,
                "completed": final and official_date <= as_of_date,
                "postponed": postponed,
            }
            previous = games.get(game_pk)
            if previous is None or (previous["postponed"] and not postponed):
                games[game_pk] = candidate
            elif postponed or previous == candidate:
                continue
            else:
                raise ValueError(f"conflicting non-postponed schedule gamePk: {game_pk}")
    if not games:
        raise ValueError("schedule payload has no regular-season games")
    by_team: dict[int, list[dict]] = {}
    for game in games.values():
        for team_id in (game["home_id"], game["away_id"]):
            by_team.setdefault(team_id, []).append(game)
    rows = []
    for team_id, team_games in sorted(by_team.items()):
        start = min(game["official_date"] for game in team_games)
        end = max(game["official_date"] for game in team_games)
        total_days = (end - start).days + 1
        remaining_days = max(0, (end - as_of_date).days)
        rows.append(
            {
                "season": int(season),
                "team_id": int(team_id),
                "championship_season_start": start,
                "championship_season_end": end,
                "championship_season_days": total_days,
                "remaining_days_after_as_of": remaining_days,
                "scheduled_games": len(team_games),
                "completed_games": sum(bool(game["completed"]) for game in team_games),
            }
        )
    completed = sum(bool(game["completed"]) for game in games.values())
    return pl.DataFrame(rows).sort("team_id"), completed, len(games)


def _build_ros_component(
    players: pl.DataFrame,
    current_counts: pl.DataFrame,
    next_year_opportunity: pl.DataFrame,
    next_year_rates: pl.DataFrame,
    *,
    as_of_date: date,
    observed_column: str,
    prior_column: str,
    rate_column: str,
    denominator: float,
    regression_exposure: float,
    completed_league_games: int,
    scheduled_league_games: int,
    component: str,
    recent_counts: pl.DataFrame | None = None,
    recent_team_games: float | None = None,
    recent_regression_exposure: float = 25.0,
) -> pl.DataFrame:
    if set(players.columns) != {"player_id"}:
        raise ValueError("ROS players require only player_id")
    if not 0 < completed_league_games < scheduled_league_games:
        raise ValueError("ROS build requires a partly completed league schedule")
    if regression_exposure <= 0 or denominator <= 0:
        raise ValueError("ROS regression and rate denominator must be positive")
    if (recent_counts is None) != (recent_team_games is None):
        raise ValueError("recent counts and recent team games must be supplied together")
    if recent_team_games is not None and (
        recent_team_games <= 0 or recent_regression_exposure <= 0
    ):
        raise ValueError("recent usage games and regression must be positive")
    observed = current_counts.group_by("player_id").agg(
        pl.col(observed_column).sum().alias("observed_to_date")
    )
    prior = next_year_opportunity.select(
        "player_id", pl.col(prior_column).alias("prior_full_season_opportunity")
    )
    rates = next_year_rates.select(
        "player_id", pl.col(rate_column).alias("conditional_war_rate")
    )
    joined = players.join(observed, on="player_id", how="left").join(
        prior, on="player_id", how="left", validate="1:1"
    ).join(rates, on="player_id", how="left", validate="1:1").with_columns(
        pl.col("observed_to_date").fill_null(0.0)
    )
    if joined.select("prior_full_season_opportunity", "conditional_war_rate").null_count().row(0) != (0, 0):
        raise ValueError(f"{component} ROS inputs lack universal opportunity or rate coverage")
    elapsed_team_games = 2.0 * completed_league_games / 30.0
    remaining_fraction = (scheduled_league_games - completed_league_games) / scheduled_league_games
    result = joined.with_columns(
        (pl.col("observed_to_date") / (pl.col("observed_to_date") + regression_exposure)).alias(
            "current_usage_reliability"
        ),
        (pl.col("observed_to_date") * 162.0 / elapsed_team_games).alias(
            "observed_full_season_pace"
        ),
    ).with_columns(
        (
            (
                pl.col("current_usage_reliability") * pl.col("observed_full_season_pace")
                + (1.0 - pl.col("current_usage_reliability"))
                * pl.col("prior_full_season_opportunity")
            )
            * remaining_fraction
        ).alias("base_projected_remaining_opportunity")
    )
    if recent_counts is not None:
        missing_recent = sorted({"player_id", "workload"} - set(recent_counts.columns))
        if missing_recent:
            raise ValueError(f"recent usage input missing fields: {missing_recent}")
        recent = recent_counts.select(
            "player_id", pl.col("workload").alias("recent_observed")
        )
        if recent.group_by("player_id").len().filter(pl.col("len") != 1).height:
            raise ValueError("recent usage input violates player grain")
        assert recent_team_games is not None
        result = result.join(
            recent, on="player_id", how="left", validate="1:1"
        ).with_columns(
            pl.col("recent_observed").fill_null(0.0),
        ).with_columns(
            (
                pl.col("recent_observed")
                / (pl.col("recent_observed") + recent_regression_exposure)
            ).alias("recent_usage_reliability"),
            (pl.col("recent_observed") * 162.0 / recent_team_games).alias(
                "recent_full_season_pace"
            ),
        ).with_columns(
            (
                (
                    pl.col("recent_usage_reliability")
                    * pl.col("recent_full_season_pace")
                    + (1.0 - pl.col("recent_usage_reliability"))
                    * (
                        pl.col("base_projected_remaining_opportunity")
                        / remaining_fraction
                    )
                )
                * remaining_fraction
            ).alias("unscaled_recent_projected_remaining_opportunity")
        )
        base_total = float(
            result.get_column("base_projected_remaining_opportunity").sum()
        )
        recent_total = float(
            result.get_column(
                "unscaled_recent_projected_remaining_opportunity"
            ).sum()
        )
        if recent_total <= 0:
            raise ValueError("recent usage challenger has no positive total")
        redistribution_scale = base_total / recent_total
        result = result.with_columns(
            (
                pl.col("unscaled_recent_projected_remaining_opportunity")
                * redistribution_scale
            ).alias("projected_remaining_opportunity"),
            pl.lit(redistribution_scale).alias("recent_redistribution_scale"),
            pl.lit("current_usage_plus_30_day_league_total_redistribution").alias(
                "workload_model_id"
            ),
        )
    else:
        result = result.with_columns(
            pl.col("base_projected_remaining_opportunity").alias(
                "projected_remaining_opportunity"
            ),
            pl.lit(None, dtype=pl.Float64).alias("recent_observed"),
            pl.lit(None, dtype=pl.Float64).alias("recent_usage_reliability"),
            pl.lit(None, dtype=pl.Float64).alias("recent_full_season_pace"),
            pl.lit(None, dtype=pl.Float64).alias(
                "unscaled_recent_projected_remaining_opportunity"
            ),
            pl.lit(None, dtype=pl.Float64).alias("recent_redistribution_scale"),
            pl.lit("current_usage_blended_with_next_full_season_prior").alias(
                "workload_model_id"
            ),
        )
    result = result.with_columns(
        (
            pl.col("projected_remaining_opportunity")
            * pl.col("conditional_war_rate") / denominator
        ).alias("projected_remaining_war"),
        pl.lit(as_of_date).alias("as_of_date"),
        pl.lit(int(as_of_date.year)).alias("season"),
        pl.lit(component).alias("component"),
        pl.lit("next_full_season_conditional_rate_proxy").alias("rate_basis"),
    )
    return result.select(
        "as_of_date", "season", "player_id", "component", "observed_to_date",
        "current_usage_reliability", "observed_full_season_pace",
        "prior_full_season_opportunity", "base_projected_remaining_opportunity",
        "recent_observed", "recent_usage_reliability", "recent_full_season_pace",
        "unscaled_recent_projected_remaining_opportunity",
        "recent_redistribution_scale", "projected_remaining_opportunity",
        "conditional_war_rate", "projected_remaining_war", "workload_model_id",
        "rate_basis",
    ).sort("player_id")


def build_hitter_ros_paths(
    players: pl.DataFrame,
    current_counts: pl.DataFrame,
    next_year_opportunity: pl.DataFrame,
    next_year_rates: pl.DataFrame,
    *,
    as_of_date: date,
    completed_league_games: int,
    scheduled_league_games: int,
    recent_counts: pl.DataFrame | None = None,
    recent_team_games: float | None = None,
) -> pl.DataFrame:
    return _build_ros_component(
        players, current_counts, next_year_opportunity, next_year_rates,
        as_of_date=as_of_date, observed_column="batting_plate_appearances",
        prior_column="expected_mlb_pa", rate_column="conditional_war_per_600_pa",
        denominator=600.0, regression_exposure=200.0,
        completed_league_games=completed_league_games,
        scheduled_league_games=scheduled_league_games, component="hitter",
        recent_counts=recent_counts, recent_team_games=recent_team_games,
    )


def build_pitcher_ros_paths(
    players: pl.DataFrame,
    current_counts: pl.DataFrame,
    next_year_opportunity: pl.DataFrame,
    next_year_rates: pl.DataFrame,
    *,
    as_of_date: date,
    completed_league_games: int,
    scheduled_league_games: int,
    recent_counts: pl.DataFrame | None = None,
    recent_team_games: float | None = None,
) -> pl.DataFrame:
    return _build_ros_component(
        players, current_counts, next_year_opportunity, next_year_rates,
        as_of_date=as_of_date, observed_column="pitching_batters_faced",
        prior_column="expected_mlb_bf", rate_column="conditional_war_per_800_bf",
        denominator=800.0, regression_exposure=200.0,
        completed_league_games=completed_league_games,
        scheduled_league_games=scheduled_league_games, component="pitcher",
        recent_counts=recent_counts, recent_team_games=recent_team_games,
    )


def build_remaining_base_salary(
    contract_years: pl.DataFrame,
    team_calendar: pl.DataFrame,
    *,
    as_of_date: date,
) -> pl.DataFrame:
    """Prorate accepted current base salary over team championship-season days."""

    required = {
        "player_id", "organization_id", "payroll_year", "amount_dollars",
        "term_label", "overlay_status", "source_snapshot_id",
    }
    if missing := sorted(required - set(contract_years.columns)):
        raise ValueError(f"salary source missing columns: {missing}")
    source = contract_years.filter(
        (pl.col("payroll_year") == as_of_date.year)
        & (pl.col("overlay_status") == "accepted_contract_overlay")
        & (pl.col("term_label") == "salary_or_option_amount")
    ).join(
        team_calendar.select(
            pl.col("team_id").alias("organization_id"),
            "championship_season_start", "championship_season_end",
            "championship_season_days", "remaining_days_after_as_of",
        ),
        on="organization_id", how="inner", validate="m:1",
    ).with_columns(
        (
            pl.col("amount_dollars") * pl.col("remaining_days_after_as_of")
            / pl.col("championship_season_days")
        ).round(0).cast(pl.Int64).alias("remaining_base_salary_dollars"),
        pl.lit(as_of_date).alias("as_of_date"),
        pl.lit("cba_championship_season_day_proration").alias("calculation_basis"),
        pl.lit("special_covenants_retained_cash_and_bonuses_not_resolved").alias(
            "exception_boundary"
        ),
    )
    if source.group_by("player_id", "organization_id", "payroll_year").len().filter(
        pl.col("len") != 1
    ).height:
        raise ValueError("remaining base salary violates player-team-season grain")
    return source.select(
        "as_of_date", "player_id", "organization_id",
        pl.col("payroll_year").alias("season"), "amount_dollars",
        "championship_season_start", "championship_season_end",
        "championship_season_days", "remaining_days_after_as_of",
        "remaining_base_salary_dollars", "calculation_basis", "exception_boundary",
        "source_snapshot_id",
    ).sort(["organization_id", "player_id"])
