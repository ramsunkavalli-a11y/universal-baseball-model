"""Canonical steal evidence and leave-one-out environment normalization."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import math
from typing import Iterable

from universal_baseball.player_value_steal_projection import PlayerSeasonStealSummary


MIN_MILB_ENV_OPPORTUNITY_PROXY = 500.0
MIN_MILB_ENV_STEAL_ATTEMPTS = 25.0


@dataclass(frozen=True, slots=True)
class StealStint:
    season: int
    source: str
    environment_id: str
    tier: str
    player_id: int
    player_name: str
    plate_appearances: float
    hits: float
    doubles: float
    triples: float
    home_runs: float
    walks: float
    intentional_walks: float
    hit_by_pitch: float
    stolen_bases: float
    caught_stealing: float

    def __post_init__(self) -> None:
        if self.player_id <= 0:
            raise ValueError("player_id must be positive")
        if not self.source or not self.environment_id or not self.tier:
            raise ValueError("source, environment_id, and tier must be nonempty")
        for field in (
            "plate_appearances",
            "hits",
            "doubles",
            "triples",
            "home_runs",
            "walks",
            "intentional_walks",
            "hit_by_pitch",
            "stolen_bases",
            "caught_stealing",
        ):
            value = float(getattr(self, field))
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"{field} must be finite and nonnegative")
        if self.doubles + self.triples + self.home_runs > self.hits:
            raise ValueError("extra-base hits cannot exceed hits")
        if self.intentional_walks > self.walks:
            raise ValueError("intentional walks cannot exceed walks")

    @property
    def singles(self) -> float:
        return self.hits - self.doubles - self.triples - self.home_runs

    @property
    def opportunity_proxy(self) -> float:
        return self.singles + self.walks + self.hit_by_pitch - self.intentional_walks

    @property
    def attempts(self) -> float:
        return self.stolen_bases + self.caught_stealing


@dataclass(frozen=True, slots=True)
class EnvironmentAudit:
    player_season_count: int
    player_environment_stint_count: int
    actual_environment_attempt_rows: int
    level_fallback_attempt_rows: int
    actual_environment_success_rows: int
    level_fallback_success_rows: int


def _sum_stints(stints: Iterable[StealStint]) -> list[StealStint]:
    grouped: dict[tuple[int, str, str, str, int], dict[str, object]] = {}
    for row in stints:
        key = (row.season, row.source, row.environment_id, row.tier, row.player_id)
        bucket = grouped.setdefault(
            key,
            {
                "player_name": row.player_name,
                "plate_appearances": 0.0,
                "hits": 0.0,
                "doubles": 0.0,
                "triples": 0.0,
                "home_runs": 0.0,
                "walks": 0.0,
                "intentional_walks": 0.0,
                "hit_by_pitch": 0.0,
                "stolen_bases": 0.0,
                "caught_stealing": 0.0,
            },
        )
        for field in (
            "plate_appearances",
            "hits",
            "doubles",
            "triples",
            "home_runs",
            "walks",
            "intentional_walks",
            "hit_by_pitch",
            "stolen_bases",
            "caught_stealing",
        ):
            bucket[field] = float(bucket[field]) + float(getattr(row, field))
    result: list[StealStint] = []
    for (season, source, environment_id, tier, player_id), values in grouped.items():
        result.append(
            StealStint(
                season=season,
                source=source,
                environment_id=environment_id,
                tier=tier,
                player_id=player_id,
                player_name=str(values["player_name"]),
                plate_appearances=float(values["plate_appearances"]),
                hits=float(values["hits"]),
                doubles=float(values["doubles"]),
                triples=float(values["triples"]),
                home_runs=float(values["home_runs"]),
                walks=float(values["walks"]),
                intentional_walks=float(values["intentional_walks"]),
                hit_by_pitch=float(values["hit_by_pitch"]),
                stolen_bases=float(values["stolen_bases"]),
                caught_stealing=float(values["caught_stealing"]),
            )
        )
    return sorted(
        result,
        key=lambda row: (row.season, row.source, row.environment_id, row.player_id),
    )


def _add_counts(bucket: dict[str, float], row: StealStint) -> None:
    bucket["opportunity_proxy"] += row.opportunity_proxy
    bucket["attempts"] += row.attempts
    bucket["successes"] += row.stolen_bases


def _empty_counts() -> dict[str, float]:
    return {"opportunity_proxy": 0.0, "attempts": 0.0, "successes": 0.0}


def build_loo_player_season_summaries(
    stints: Iterable[StealStint],
) -> tuple[list[PlayerSeasonStealSummary], EnvironmentAudit]:
    """Normalize steal evidence to leave-one-player-out environment baselines."""

    rows = _sum_stints(stints)
    if not rows:
        raise ValueError("steal evidence cannot be empty")

    env_totals: dict[tuple[int, str, str, str], dict[str, float]] = defaultdict(_empty_counts)
    level_totals: dict[tuple[int, str, str], dict[str, float]] = defaultdict(_empty_counts)
    player_level_totals: dict[tuple[int, str, str, int], dict[str, float]] = defaultdict(_empty_counts)

    for row in rows:
        _add_counts(env_totals[(row.season, row.source, row.environment_id, row.tier)], row)
        _add_counts(level_totals[(row.season, row.source, row.tier)], row)
        _add_counts(player_level_totals[(row.season, row.source, row.tier, row.player_id)], row)

    normalized: list[dict[str, object]] = []
    actual_attempt = 0
    fallback_attempt = 0
    actual_success = 0
    fallback_success = 0

    for row in rows:
        env_key = (row.season, row.source, row.environment_id, row.tier)
        level_key = (row.season, row.source, row.tier)
        player_level_key = (row.season, row.source, row.tier, row.player_id)
        env = env_totals[env_key]
        level = level_totals[level_key]
        player_level = player_level_totals[player_level_key]

        env_opp = env["opportunity_proxy"] - row.opportunity_proxy
        env_attempts = env["attempts"] - row.attempts
        env_successes = env["successes"] - row.stolen_bases
        level_opp = level["opportunity_proxy"] - player_level["opportunity_proxy"]
        level_attempts = level["attempts"] - player_level["attempts"]
        level_successes = level["successes"] - player_level["successes"]

        is_mlb = row.source.upper() == "MLB"
        if row.opportunity_proxy > 0:
            if is_mlb or env_opp >= MIN_MILB_ENV_OPPORTUNITY_PROXY:
                if env_opp <= 0:
                    raise ValueError("MLB LOO attempt baseline has nonpositive exposure")
                attempt_rate = env_attempts / env_opp
                actual_attempt += 1
            else:
                if level_opp <= 0:
                    raise ValueError("MiLB level LOO attempt fallback has nonpositive exposure")
                attempt_rate = level_attempts / level_opp
                fallback_attempt += 1
            if attempt_rate <= 0:
                raise ValueError("LOO attempt baseline rate must be positive for scoreable exposure")
        else:
            attempt_rate = 0.0

        if row.attempts > 0:
            if is_mlb or env_attempts >= MIN_MILB_ENV_STEAL_ATTEMPTS:
                if env_attempts <= 0:
                    raise ValueError("MLB LOO success baseline has no attempts")
                success_rate = env_successes / env_attempts
                actual_success += 1
            else:
                if level_attempts <= 0:
                    raise ValueError("MiLB level LOO success fallback has no attempts")
                success_rate = level_successes / level_attempts
                fallback_success += 1
            if not 0 <= success_rate <= 1:
                raise ValueError("LOO success baseline must be within [0, 1]")
        else:
            success_rate = 0.0

        normalized.append(
            {
                "player_id": row.player_id,
                "season": row.season,
                "tier": row.tier,
                "opportunity_proxy": row.opportunity_proxy,
                "attempts": row.attempts,
                "successes": row.stolen_bases,
                "expected_attempts": row.opportunity_proxy * attempt_rate,
                "expected_successes": row.attempts * success_rate,
            }
        )

    player_season: dict[tuple[int, int], dict[str, object]] = {}
    tier_exposure: dict[tuple[int, int], dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for row in normalized:
        key = (int(row["player_id"]), int(row["season"]))
        bucket = player_season.setdefault(
            key,
            {
                "opportunity_proxy": 0.0,
                "attempts": 0.0,
                "successes": 0.0,
                "expected_attempts": 0.0,
                "expected_successes": 0.0,
            },
        )
        for field in (
            "opportunity_proxy",
            "attempts",
            "successes",
            "expected_attempts",
            "expected_successes",
        ):
            bucket[field] = float(bucket[field]) + float(row[field])
        tier_exposure[key][str(row["tier"])] += float(row["opportunity_proxy"])

    summaries: list[PlayerSeasonStealSummary] = []
    for (player_id, season), values in sorted(player_season.items(), key=lambda item: (item[0][1], item[0][0])):
        tiers = tier_exposure[(player_id, season)]
        dominant_tier = min(
            tiers,
            key=lambda tier: (-tiers[tier], tier),
        )
        summaries.append(
            PlayerSeasonStealSummary(
                player_id=player_id,
                season=season,
                tier=dominant_tier,
                opportunity_proxy=float(values["opportunity_proxy"]),
                attempts=float(values["attempts"]),
                successes=float(values["successes"]),
                expected_attempts=float(values["expected_attempts"]),
                expected_successes=float(values["expected_successes"]),
            )
        )

    return summaries, EnvironmentAudit(
        player_season_count=len(summaries),
        player_environment_stint_count=len(rows),
        actual_environment_attempt_rows=actual_attempt,
        level_fallback_attempt_rows=fallback_attempt,
        actual_environment_success_rows=actual_success,
        level_fallback_success_rows=fallback_success,
    )
