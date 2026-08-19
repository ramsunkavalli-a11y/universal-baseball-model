"""Official MLB Stats API run-environment materialization for Player Value v1."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Mapping

import requests

from universal_baseball.mlb_season_stats import (
    MLB_LEAGUE_IDS,
    MLB_STATS_URL,
    _statsapi_get_with_retry,
)
from universal_baseball.player_value_runs_per_win import (
    RunsPerWinResult,
    calculate_v1_runs_per_win,
)


@dataclass(frozen=True)
class RunEnvironmentCapture:
    season: int
    league_id: int
    group: str
    offset: int
    returned_split_count: int
    total_splits: int | None
    response_sha256: str


@dataclass(frozen=True)
class MlbRunEnvironment:
    season: int
    batting_runs_scored: int
    pitching_runs_allowed: int
    pitching_outs: int
    innings_pitched: float
    captures: tuple[RunEnvironmentCapture, ...]
    runs_per_win: RunsPerWinResult


def _integer_count(value: Any, label: str) -> int:
    if value is None or str(value).strip() == "":
        raise ValueError(f"missing {label}")
    numeric = float(str(value))
    if not numeric.is_integer() or numeric < 0:
        raise ValueError(f"invalid {label}: {value!r}")
    return int(numeric)


def innings_pitched_to_outs(value: Any) -> int:
    """Parse baseball innings notation where .1/.2 mean one/two outs."""

    text = str(value).strip()
    if not text:
        raise ValueError("missing inningsPitched")
    if "." in text:
        whole_text, frac = text.split(".", 1)
    else:
        whole_text, frac = text, "0"
    whole = int(whole_text)
    if whole < 0 or frac not in {"0", "1", "2"}:
        raise ValueError(f"invalid inningsPitched: {value!r}")
    return whole * 3 + int(frac)


def _fetch_group_splits(
    session: requests.Session,
    *,
    season: int,
    league_id: int,
    group: str,
    page_limit: int,
    timeout_seconds: int,
) -> tuple[list[Mapping[str, Any]], list[RunEnvironmentCapture]]:
    offset = 0
    all_splits: list[Mapping[str, Any]] = []
    captures: list[RunEnvironmentCapture] = []
    while True:
        response = _statsapi_get_with_retry(
            session,
            MLB_STATS_URL,
            params={
                "stats": "season",
                "group": group,
                "season": int(season),
                "sportIds": 1,
                "leagueId": int(league_id),
                "playerPool": "ALL",
                "gameType": "R",
                "limit": int(page_limit),
                "offset": int(offset),
            },
            timeout_seconds=timeout_seconds,
        )
        payload = response.json()
        groups = payload.get("stats") or []
        if len(groups) != 1:
            raise RuntimeError(f"expected one {group} stats group, found {len(groups)}")
        block = groups[0]
        splits = block.get("splits") or []
        total = block.get("totalSplits")
        total_int = int(total) if total is not None else None
        captures.append(
            RunEnvironmentCapture(
                season=int(season),
                league_id=int(league_id),
                group=group,
                offset=offset,
                returned_split_count=len(splits),
                total_splits=total_int,
                response_sha256=sha256(response.content).hexdigest(),
            )
        )
        all_splits.extend(splits)
        if total_int is not None and len(all_splits) >= total_int:
            break
        if not splits or len(splits) < page_limit:
            break
        offset += len(splits)
        if offset > 5000:
            raise RuntimeError(f"{group} pagination exceeded safety bound")
    return all_splits, captures


def fetch_mlb_run_environment(
    season: int,
    *,
    page_limit: int = 500,
    session: requests.Session | None = None,
    timeout_seconds: int = 120,
) -> MlbRunEnvironment:
    """Fetch and reconcile completed-regular-season MLB run environment."""

    if int(season) <= 0:
        raise ValueError("season must be positive")
    owned = session is None
    active = session or requests.Session()
    batting_runs = 0
    pitching_runs = 0
    pitching_outs = 0
    captures: list[RunEnvironmentCapture] = []
    try:
        for league_id in MLB_LEAGUE_IDS:
            hitting, hit_caps = _fetch_group_splits(
                active,
                season=int(season),
                league_id=int(league_id),
                group="hitting",
                page_limit=page_limit,
                timeout_seconds=timeout_seconds,
            )
            pitching, pitch_caps = _fetch_group_splits(
                active,
                season=int(season),
                league_id=int(league_id),
                group="pitching",
                page_limit=page_limit,
                timeout_seconds=timeout_seconds,
            )
            captures.extend(hit_caps)
            captures.extend(pitch_caps)
            if not hitting or not pitching:
                raise RuntimeError(f"empty MLB run-environment source for league {league_id}")
            batting_runs += sum(
                _integer_count((split.get("stat") or {}).get("runs"), "hitting runs")
                for split in hitting
            )
            pitching_runs += sum(
                _integer_count((split.get("stat") or {}).get("runs"), "pitching runs")
                for split in pitching
            )
            pitching_outs += sum(
                innings_pitched_to_outs((split.get("stat") or {}).get("inningsPitched"))
                for split in pitching
            )
    finally:
        if owned:
            active.close()

    if batting_runs != pitching_runs:
        raise RuntimeError(
            "MLB runs-scored/runs-allowed reconciliation failed: "
            f"batting={batting_runs}, pitching={pitching_runs}"
        )
    if batting_runs <= 0 or pitching_outs <= 0:
        raise RuntimeError("MLB run environment must contain positive runs and pitching outs")

    innings = pitching_outs / 3.0
    rpw = calculate_v1_runs_per_win(
        batting_runs,
        innings,
        reference_season=int(season),
    )
    return MlbRunEnvironment(
        season=int(season),
        batting_runs_scored=batting_runs,
        pitching_runs_allowed=pitching_runs,
        pitching_outs=pitching_outs,
        innings_pitched=innings,
        captures=tuple(captures),
        runs_per_win=rpw,
    )
