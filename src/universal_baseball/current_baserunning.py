"""Apply the frozen Player Value v1 baserunning models to current evidence."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Iterable, Mapping

import polars as pl

from universal_baseball.player_value_advancement_projection import (
    AdvancementCandidate,
    PlayerSeasonAdvancementSummary,
    projected_advancement_rate,
)
from universal_baseball.player_value_baserunning_runs import (
    BaserunningReference,
    project_baserunning_runs,
)
from universal_baseball.player_value_steal_data import (
    EnvironmentAudit,
    StealStint,
    build_loo_player_season_summaries,
)
from universal_baseball.player_value_steal_projection import (
    PlayerSeasonStealSummary,
    StealCandidate,
    attempt_multiplier,
    success_log_odds_residual,
)


TIER_BY_LEVEL = {
    "MLB": "MLB",
    "AAA": "AAA",
    "AA": "AA",
    "HIGH_A": "A+",
    "SINGLE_A": "A",
    "ROOKIE_COMPLEX": "RK",
}
ATTEMPT_CANDIDATE = StealCandidate("B2_k5", "B2", 5.0)
SUCCESS_CANDIDATE = StealCandidate("B2_k45", "B2", 45.0)
ADVANCEMENT_CANDIDATE = AdvancementCandidate("A2_k25", "A2", 25.0)
BASERUNNING_MODEL_ID = "player_value_v1_B2k5_B2k45_A2k25_current"


def build_steal_history(
    components: pl.DataFrame,
) -> tuple[list[PlayerSeasonStealSummary], EnvironmentAudit]:
    """Convert official affiliated component rows to frozen steal-model inputs."""

    required = {
        "season", "player_id", "player_name", "sport_id", "level_group",
        "plate_appearances", "hits", "doubles", "triples", "home_runs",
        "base_on_balls", "intentional_walks", "hit_by_pitch", "stolen_bases",
        "caught_stealing",
    }
    if missing := sorted(required - set(components.columns)):
        raise ValueError(f"affiliated baserunning source missing columns: {missing}")
    stints: list[StealStint] = []
    for row in components.iter_rows(named=True):
        level = str(row["level_group"])
        if level not in TIER_BY_LEVEL:
            raise ValueError(f"unsupported baserunning level: {level}")
        is_mlb = level == "MLB"
        stints.append(
            StealStint(
                season=int(row["season"]),
                source="MLB" if is_mlb else "MiLB",
                environment_id="MLB" if is_mlb else f"MILB_SPORT:{int(row['sport_id'])}",
                tier=TIER_BY_LEVEL[level],
                player_id=int(row["player_id"]),
                player_name=str(row["player_name"]),
                plate_appearances=float(row["plate_appearances"]),
                hits=float(row["hits"]),
                doubles=float(row["doubles"]),
                triples=float(row["triples"]),
                home_runs=float(row["home_runs"]),
                walks=float(row["base_on_balls"]),
                intentional_walks=float(row["intentional_walks"]),
                hit_by_pitch=float(row["hit_by_pitch"]),
                stolen_bases=float(row["stolen_bases"]),
                caught_stealing=float(row["caught_stealing"]),
            )
        )
    return build_loo_player_season_summaries(stints)


def build_advancement_history(
    rows_by_season: Mapping[int, Iterable[Mapping[str, Any]]],
) -> list[PlayerSeasonAdvancementSummary]:
    """Project audited Savant rows to the frozen advancement-model interface."""

    result: list[PlayerSeasonAdvancementSummary] = []
    for season, rows in sorted(rows_by_season.items()):
        for row in rows:
            result.append(
                PlayerSeasonAdvancementSummary(
                    player_id=int(row["player_id"]),
                    season=int(season),
                    runs_xb=float(row["runner_runs_xb"]),
                    opportunities_xb=float(row["n_runner_moved_xb"]),
                )
            )
    keys = [(row.player_id, row.season) for row in result]
    if len(keys) != len(set(keys)):
        raise ValueError("Savant advancement history has duplicate player-season rows")
    return result


def _has_recent_evidence(player_id: int, season: int, evidence: Iterable[Any]) -> bool:
    return any(
        row.player_id == player_id and 1 <= season - row.season <= 3
        for row in evidence
    )


def build_current_baserunning_rates(
    players: pl.DataFrame,
    steal_history: Iterable[PlayerSeasonStealSummary],
    advancement_history: Iterable[PlayerSeasonAdvancementSummary],
    *,
    forecast_seasons: tuple[int, ...],
    reference: BaserunningReference,
) -> pl.DataFrame:
    """Produce centered baserunning runs per 600 PA for every player-year."""

    if set(players.columns) != {"player_id"}:
        raise ValueError("baserunning players require only player_id")
    if players.get_column("player_id").n_unique() != players.height:
        raise ValueError("baserunning player IDs must be unique")
    steals = list(steal_history)
    advancement = list(advancement_history)
    rows: list[dict[str, object]] = []
    for player_id in players.get_column("player_id"):
        pid = int(player_id)
        for season in forecast_seasons:
            target_steal = PlayerSeasonStealSummary(
                player_id=pid, season=int(season), tier="MLB",
                opportunity_proxy=0.0, attempts=0.0, successes=0.0,
                expected_attempts=0.0, expected_successes=0.0,
            )
            target_advancement = PlayerSeasonAdvancementSummary(
                player_id=pid, season=int(season), runs_xb=0.0,
                opportunities_xb=0.0,
            )
            steal_evidence = _has_recent_evidence(pid, int(season), steals)
            advancement_evidence = _has_recent_evidence(pid, int(season), advancement)
            projection = project_baserunning_runs(
                projected_mlb_pa=600.0,
                attempt_multiplier=attempt_multiplier(
                    target_steal, steals, ATTEMPT_CANDIDATE
                ),
                success_logodds_residual=success_log_odds_residual(
                    target_steal, steals, SUCCESS_CANDIDATE
                ),
                advancement_rate=projected_advancement_rate(
                    target_advancement, advancement, ADVANCEMENT_CANDIDATE
                ),
                reference=reference,
            )
            tier = (
                "steal_and_advancement"
                if steal_evidence and advancement_evidence
                else "steal_only"
                if steal_evidence
                else "advancement_only"
                if advancement_evidence
                else "population_neutral"
            )
            rows.append(
                {
                    "player_id": pid,
                    "season": int(season),
                    "baserunning_runs_per_600": projection.baserunning_runs,
                    "steal_runs_per_600": projection.steal_runs,
                    "advancement_runs_per_600": projection.advancement_runs,
                    "baserunning_evidence_tier": tier,
                    "baserunning_model_id": BASERUNNING_MODEL_ID,
                }
            )
    return pl.DataFrame(rows).sort(["player_id", "season"])


def steal_history_frame(rows: Iterable[PlayerSeasonStealSummary]) -> pl.DataFrame:
    return pl.DataFrame([asdict(row) for row in rows]).sort(["season", "player_id"])


def advancement_history_frame(
    rows: Iterable[PlayerSeasonAdvancementSummary],
) -> pl.DataFrame:
    return pl.DataFrame([asdict(row) for row in rows]).sort(["season", "player_id"])
