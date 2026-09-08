"""CBA-defined service-time and team-control calculations.

The module deliberately begins with dated roster-state intervals. Stats API
rosters and transactions are the evidence used to create those intervals; this
layer owns only the published CBA arithmetic. Contract terms remain a separate
external-data join because they can override the statutory eligibility path.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from math import ceil

import polars as pl


SERVICE_DAYS_PER_YEAR = 172
OPTION_DAYS_PER_YEAR = 20
FULL_PRO_SEASON_ACTIVE_DAYS = 90
FULL_PRO_SEASON_MIN_ACTIVE_DAYS = 30
SUPER_TWO_MIN_CURRENT_DAYS = 86
SUPER_TWO_SHARE = 0.22

ROSTER_STATES = frozenset(
    {
        "mlb_active",
        "mlb_injured",
        "mlb_service_list",
        "minors_optioned",
        "pro_active",
        "pro_injured",
        "pro_inactive",
        "service_excluded",
    }
)

CONTROL_STINT_SCHEMA: dict[str, pl.DataType] = {
    "player_id": pl.Int64,
    "season": pl.Int64,
    "start_date": pl.Date,
    "end_date": pl.Date,
    "roster_state": pl.String,
    "source_snapshot_id": pl.String,
}

SEASON_WINDOW_SCHEMA: dict[str, pl.DataType] = {
    "season": pl.Int64,
    "start_date": pl.Date,
    "end_date": pl.Date,
}

CONTROL_PLAYER_SCHEMA: dict[str, pl.DataType] = {
    "player_id": pl.Int64,
    "player_name": pl.String,
    "birth_date": pl.Date,
    "first_pro_contract_date": pl.Date,
    "on_40man": pl.Boolean,
    "service_days_before_window": pl.Int64,
    "option_years_used_before_window": pl.Int64,
    "full_pro_seasons_before_window": pl.Int64,
    "history_complete": pl.Boolean,
    "source_snapshot_ids": pl.String,
}

CONTROL_YEAR_SCHEMA: dict[str, pl.DataType] = {
    "player_id": pl.Int64,
    "season": pl.Int64,
    "service_days": pl.Int64,
    "optioned_days": pl.Int64,
    "option_year_used": pl.Boolean,
    "pro_active_days": pl.Int64,
    "pro_active_or_injured_days": pl.Int64,
    "full_pro_season": pl.Boolean,
}

TEAM_CONTROL_SUMMARY_SCHEMA: dict[str, pl.DataType] = {
    "as_of_date": pl.Date,
    "player_id": pl.Int64,
    "player_name": pl.String,
    "service_days": pl.Int64,
    "service_years": pl.Int64,
    "service_remainder_days": pl.Int64,
    "service_time": pl.String,
    "option_years_used": pl.Int64,
    "option_years_allowed": pl.Int64,
    "options_remaining": pl.Int64,
    "full_pro_seasons": pl.Int64,
    "rule5_eligibility_year": pl.Int64,
    "rule5_status": pl.String,
    "cba_eligibility_class": pl.String,
    "super_two_cutoff_days": pl.Int64,
    "calculation_confidence": pl.String,
    "review_reasons": pl.String,
    "source_snapshot_ids": pl.String,
}

SUPER_TWO_POOL_SCHEMA: dict[str, pl.DataType] = {
    "as_of_date": pl.Date,
    "player_id": pl.Int64,
    "service_days": pl.Int64,
    "current_service_days": pl.Int64,
    "pool_rank": pl.Int64,
    "cutoff_days": pl.Int64,
    "selected": pl.Boolean,
    "cutoff_tie": pl.Boolean,
}


Interval = tuple[date, date]


def _conform(frame: pl.DataFrame, schema: dict[str, pl.DataType], label: str) -> pl.DataFrame:
    missing = sorted(set(schema) - set(frame.columns))
    extra = sorted(set(frame.columns) - set(schema))
    if missing:
        raise ValueError(f"{label} missing columns: {missing}")
    if extra:
        raise ValueError(f"{label} has undeclared columns: {extra}")
    return frame.select(list(schema)).cast(schema, strict=True)


def _merge_intervals(intervals: list[Interval]) -> list[Interval]:
    merged: list[list[date]] = []
    for start, end in sorted(intervals):
        if not merged or start > merged[-1][1] + timedelta(days=1):
            merged.append([start, end])
        elif end > merged[-1][1]:
            merged[-1][1] = end
    return [(start, end) for start, end in merged]


def _clip(intervals: list[Interval], window: Interval) -> list[Interval]:
    start_bound, end_bound = window
    return _merge_intervals(
        [
            (max(start, start_bound), min(end, end_bound))
            for start, end in intervals
            if max(start, start_bound) <= min(end, end_bound)
        ]
    )


def _subtract(base: list[Interval], excluded: list[Interval]) -> list[Interval]:
    remaining = _merge_intervals(base)
    for excluded_start, excluded_end in _merge_intervals(excluded):
        next_remaining: list[Interval] = []
        for start, end in remaining:
            if excluded_end < start or excluded_start > end:
                next_remaining.append((start, end))
                continue
            if excluded_start > start:
                next_remaining.append((start, excluded_start - timedelta(days=1)))
            if excluded_end < end:
                next_remaining.append((excluded_end + timedelta(days=1), end))
        remaining = next_remaining
    return remaining


def _days(intervals: list[Interval]) -> int:
    return sum((end - start).days + 1 for start, end in _merge_intervals(intervals))


def calculate_control_years(
    stints: pl.DataFrame,
    season_windows: pl.DataFrame,
    *,
    as_of_date: date,
) -> pl.DataFrame:
    """Apply service-time, option-year and full-pro-season day rules.

    Intervals are inclusive. Season windows should be sourced from the official
    schedule and cut off at ``as_of_date`` for an in-season calculation.
    Overlapping evidence is unioned, so duplicate roster evidence cannot create
    extra service or option days.
    """

    source = _conform(stints, CONTROL_STINT_SCHEMA, "control_stints")
    windows = _conform(season_windows, SEASON_WINDOW_SCHEMA, "season_windows")
    if windows.group_by("season").len().filter(pl.col("len") > 1).height:
        raise ValueError("season_windows has duplicate seasons")
    if windows.filter(pl.col("start_date") > pl.col("end_date")).height:
        raise ValueError("season_windows has an inverted interval")
    if source.filter(
        (pl.col("player_id") <= 0)
        | (pl.col("start_date") > pl.col("end_date"))
        | (pl.col("end_date") > pl.lit(as_of_date))
        | (~pl.col("roster_state").is_in(sorted(ROSTER_STATES)))
        | (pl.col("source_snapshot_id").str.strip_chars() == "")
    ).height:
        raise ValueError("control_stints has invalid identity, interval, state or source")
    known_seasons = set(windows.get_column("season").to_list())
    if set(source.get_column("season").to_list()) - known_seasons:
        raise ValueError("control_stints contains a season without a season window")

    window_map = {
        int(row["season"]): (row["start_date"], min(row["end_date"], as_of_date))
        for row in windows.iter_rows(named=True)
    }
    grouped: dict[tuple[int, int], dict[str, list[Interval]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for row in source.iter_rows(named=True):
        grouped[(int(row["player_id"]), int(row["season"]))][
            str(row["roster_state"])
        ].append((row["start_date"], row["end_date"]))

    rows: list[dict[str, object]] = []
    for (player_id, season), by_state in sorted(grouped.items()):
        window = window_map[season]
        service_base = _clip(
            by_state["mlb_active"]
            + by_state["mlb_injured"]
            + by_state["mlb_service_list"],
            window,
        )
        service_intervals = _subtract(
            service_base, _clip(by_state["service_excluded"], window)
        )
        service_days = min(SERVICE_DAYS_PER_YEAR, _days(service_intervals))
        optioned_days = _days(_clip(by_state["minors_optioned"], window))
        pro_active = _clip(
            by_state["mlb_active"]
            + by_state["minors_optioned"]
            + by_state["pro_active"],
            window,
        )
        pro_active_or_injured = _clip(
            pro_active + by_state["mlb_injured"] + by_state["pro_injured"],
            window,
        )
        active_days = _days(pro_active)
        active_or_injured_days = _days(pro_active_or_injured)
        full_pro_season = active_days >= FULL_PRO_SEASON_ACTIVE_DAYS or (
            active_days >= FULL_PRO_SEASON_MIN_ACTIVE_DAYS
            and active_or_injured_days >= FULL_PRO_SEASON_ACTIVE_DAYS
        )
        rows.append(
            {
                "player_id": player_id,
                "season": season,
                "service_days": service_days,
                "optioned_days": optioned_days,
                "option_year_used": optioned_days >= OPTION_DAYS_PER_YEAR,
                "pro_active_days": active_days,
                "pro_active_or_injured_days": active_or_injured_days,
                "full_pro_season": full_pro_season,
            }
        )
    return (
        pl.DataFrame(rows, schema=CONTROL_YEAR_SCHEMA)
        if rows
        else pl.DataFrame(schema=CONTROL_YEAR_SCHEMA)
    )


def _age_on(birth_date: date, event_date: date) -> int:
    return event_date.year - birth_date.year - (
        (event_date.month, event_date.day) < (birth_date.month, birth_date.day)
    )


def _rule5_year(birth_date: date | None, signed: date | None) -> int | None:
    if birth_date is None or signed is None:
        return None
    protection_seasons = 5 if _age_on(birth_date, signed) <= 18 else 4
    return signed.year + protection_seasons - 1


def _super_two_cutoff(
    totals: list[dict[str, object]],
) -> tuple[int | None, set[int], bool]:
    pool = [
        row
        for row in totals
        if 2 * SERVICE_DAYS_PER_YEAR <= int(row["service_days"]) < 3 * SERVICE_DAYS_PER_YEAR
        and int(row["current_service_days"]) >= SUPER_TWO_MIN_CURRENT_DAYS
    ]
    if not pool:
        return None, set(), False
    slots = max(1, ceil(len(pool) * SUPER_TWO_SHARE))
    ordered = sorted(pool, key=lambda row: (-int(row["service_days"]), int(row["player_id"])))
    cutoff = int(ordered[slots - 1]["service_days"])
    selected = {int(row["player_id"]) for row in pool if int(row["service_days"]) >= cutoff}
    cutoff_tie = sum(int(row["service_days"]) == cutoff for row in pool) > 1
    return cutoff, selected, cutoff_tie


def build_super_two_pool(
    service: pl.DataFrame,
    *,
    as_of_date: date,
    pool_complete: bool,
) -> pl.DataFrame:
    """Rank the league-wide two-to-three-year pool under the published 22% rule."""

    required = {"player_id", "service_days", "current_service_days"}
    missing = sorted(required - set(service.columns))
    if missing:
        raise ValueError(f"super two service input missing columns: {missing}")
    if not pool_complete:
        raise ValueError("Super Two requires an explicitly complete league-wide pool")
    source = service.select(sorted(required)).cast(
        {
            "player_id": pl.Int64,
            "service_days": pl.Int64,
            "current_service_days": pl.Int64,
        },
        strict=True,
    )
    if source.group_by("player_id").len().filter(pl.col("len") > 1).height:
        raise ValueError("super two service input has duplicate players")
    if source.filter(
        (pl.col("player_id") <= 0)
        | (pl.col("service_days") < 0)
        | (pl.col("current_service_days") < 0)
        | (pl.col("current_service_days") > SERVICE_DAYS_PER_YEAR)
    ).height:
        raise ValueError("super two service input has invalid values")
    pool = source.filter(
        (pl.col("service_days") >= 2 * SERVICE_DAYS_PER_YEAR)
        & (pl.col("service_days") < 3 * SERVICE_DAYS_PER_YEAR)
        & (pl.col("current_service_days") >= SUPER_TWO_MIN_CURRENT_DAYS)
    ).sort(["service_days", "player_id"], descending=[True, False])
    if pool.is_empty():
        return pl.DataFrame(schema=SUPER_TWO_POOL_SCHEMA)
    slots = max(1, ceil(pool.height * SUPER_TWO_SHARE))
    cutoff = int(pool.item(slots - 1, "service_days"))
    cutoff_tie = pool.filter(pl.col("service_days") == cutoff).height > 1
    return (
        pool.with_row_index("pool_rank", offset=1)
        .with_columns(
            pl.lit(as_of_date).cast(pl.Date).alias("as_of_date"),
            pl.lit(cutoff).cast(pl.Int64).alias("cutoff_days"),
            (pl.col("service_days") >= cutoff).alias("selected"),
            pl.lit(cutoff_tie).alias("cutoff_tie"),
        )
        .select(list(SUPER_TWO_POOL_SCHEMA))
        .cast(SUPER_TWO_POOL_SCHEMA, strict=True)
    )


def build_team_control_summary(
    players: pl.DataFrame,
    control_years: pl.DataFrame,
    *,
    as_of_date: date,
    super_two_pool_complete: bool = False,
) -> pl.DataFrame:
    """Create one CBA calculation row per player for a contract-data join.

    The result states statutory eligibility only. A guaranteed contract,
    non-tender, release, special service award or negotiated clause can change
    the real-world result and belongs in the later contract/exception join.
    """

    people = _conform(players, CONTROL_PLAYER_SCHEMA, "control_players")
    years = _conform(control_years, CONTROL_YEAR_SCHEMA, "control_years")
    if people.group_by("player_id").len().filter(pl.col("len") > 1).height:
        raise ValueError("control_players has duplicate player_id")
    if people.filter(
        (pl.col("player_id") <= 0)
        | (pl.col("service_days_before_window") < 0)
        | (pl.col("option_years_used_before_window") < 0)
        | (pl.col("full_pro_seasons_before_window") < 0)
        | (pl.col("source_snapshot_ids").str.strip_chars() == "")
    ).height:
        raise ValueError("control_players has invalid identity, baseline or source")
    outside = years.select("player_id").unique().join(
        people.select("player_id"), on="player_id", how="anti"
    )
    if outside.height:
        raise ValueError("control_years contains players outside control_players")

    by_player: dict[int, list[dict[str, object]]] = defaultdict(list)
    for row in years.iter_rows(named=True):
        by_player[int(row["player_id"])].append(row)

    totals: list[dict[str, object]] = []
    for person in people.iter_rows(named=True):
        player_id = int(person["player_id"])
        annual = by_player[player_id]
        service_days = int(person["service_days_before_window"]) + sum(
            int(row["service_days"]) for row in annual
        )
        option_years = int(person["option_years_used_before_window"]) + sum(
            bool(row["option_year_used"]) for row in annual
        )
        full_seasons = int(person["full_pro_seasons_before_window"]) + sum(
            bool(row["full_pro_season"]) for row in annual
        )
        current_service_days = sum(
            int(row["service_days"])
            for row in annual
            if int(row["season"]) == as_of_date.year
        )
        totals.append(
            {
                **person,
                "service_days": service_days,
                "option_years": option_years,
                "full_seasons": full_seasons,
                "current_service_days": current_service_days,
            }
        )

    cutoff, super_two_ids, cutoff_tie = (
        _super_two_cutoff(totals) if super_two_pool_complete else (None, set(), False)
    )
    output: list[dict[str, object]] = []
    for row in totals:
        player_id = int(row["player_id"])
        service_days = int(row["service_days"])
        option_years = int(row["option_years"])
        full_seasons = int(row["full_seasons"])
        allowed_options = 4 if option_years >= 4 or (
            option_years >= 3 and full_seasons < 5
        ) else 3
        remaining_options = max(allowed_options - option_years, 0)
        rule5_year = _rule5_year(row["birth_date"], row["first_pro_contract_date"])
        if bool(row["on_40man"]):
            rule5_status = "protected_40man"
        elif rule5_year is None:
            rule5_status = "unknown"
        elif rule5_year <= as_of_date.year:
            rule5_status = "eligible_next_rule5_draft"
        else:
            rule5_status = "not_yet_eligible"

        if service_days >= 6 * SERVICE_DAYS_PER_YEAR:
            eligibility = "free_agent_eligible"
        elif service_days >= 3 * SERVICE_DAYS_PER_YEAR:
            eligibility = "arbitration_eligible"
        elif player_id in super_two_ids:
            eligibility = "super_two_eligible"
        elif (
            not super_two_pool_complete
            and 2 * SERVICE_DAYS_PER_YEAR <= service_days < 3 * SERVICE_DAYS_PER_YEAR
            and int(row["current_service_days"]) >= SUPER_TWO_MIN_CURRENT_DAYS
        ):
            eligibility = "super_two_candidate"
        else:
            eligibility = "pre_arbitration"

        reasons: list[str] = []
        if not bool(row["history_complete"]):
            reasons.append("incomplete_statsapi_history")
        if rule5_year is None and not bool(row["on_40man"]):
            reasons.append("missing_rule5_inputs")
        if option_years > allowed_options:
            reasons.append("option_year_count_conflict")
        if allowed_options == 4 and option_years == 3:
            reasons.append("fourth_option_requires_milb_calendar_validation")
        if eligibility == "super_two_candidate":
            reasons.append("super_two_pool_incomplete")
        if cutoff_tie and player_id in super_two_ids and service_days == cutoff:
            reasons.append("super_two_cutoff_tie")
        confidence = (
            "insufficient_history"
            if "incomplete_statsapi_history" in reasons
            else "bounded_edge_case"
            if reasons
            else "rule_calculated"
        )
        service_years, remainder = divmod(service_days, SERVICE_DAYS_PER_YEAR)
        output.append(
            {
                "as_of_date": as_of_date,
                "player_id": player_id,
                "player_name": str(row["player_name"]),
                "service_days": service_days,
                "service_years": service_years,
                "service_remainder_days": remainder,
                "service_time": f"{service_years}.{remainder:03d}",
                "option_years_used": option_years,
                "option_years_allowed": allowed_options,
                "options_remaining": remaining_options,
                "full_pro_seasons": full_seasons,
                "rule5_eligibility_year": rule5_year,
                "rule5_status": rule5_status,
                "cba_eligibility_class": eligibility,
                "super_two_cutoff_days": cutoff,
                "calculation_confidence": confidence,
                "review_reasons": ",".join(reasons),
                "source_snapshot_ids": str(row["source_snapshot_ids"]),
            }
        )
    return (
        pl.DataFrame(output, schema=TEAM_CONTROL_SUMMARY_SCHEMA)
        if output
        else pl.DataFrame(schema=TEAM_CONTROL_SUMMARY_SCHEMA)
    ).sort("player_id")
