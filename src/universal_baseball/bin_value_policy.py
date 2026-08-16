"""Certified production policy for MiLB Performance-bin value estimation.

The policy records only choices that survived pre-registered held-out validation.
A positive prior strength means an environment/bin is shrunk toward the same bin
from other leagues at the *same affiliated level and same season*, excluding the
target environment. Strength zero means use the direct league-season estimate.

This module is about league-typical Performance-bin values, not player-talent
shrinkage and not pitch-process evidence availability.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


EstimatorStatus = Literal["certified_pooled", "certified_direct", "uncertified"]


@dataclass(frozen=True)
class BinValuePolicy:
    level_group: str
    prior_strength: int
    status: EstimatorStatus
    prior_scope: str | None
    evidence: str

    @property
    def uses_pooling(self) -> bool:
        return self.status == "certified_pooled" and self.prior_strength > 0


# Current MLB Stats API affiliated-league IDs represented in the certified gates.
LEAGUE_LEVEL_GROUP: dict[int, str] = {
    112: "AAA",  # International League
    117: "AAA",  # Pacific Coast League
    109: "AA",  # Texas League
    111: "AA",  # Southern League
    113: "AA",  # Eastern League
    116: "HIGH_A",  # South Atlantic League
    118: "HIGH_A",  # Midwest League
    126: "HIGH_A",  # Northwest League
    110: "SINGLE_A",  # California League
    122: "SINGLE_A",  # Carolina League
    123: "SINGLE_A",  # Florida State League
    121: "ROOKIE_COMPLEX",  # Arizona Complex League
    124: "ROOKIE_COMPLEX",  # Florida Complex League
    130: "ROOKIE_COMPLEX",  # Dominican Summer League
}


_CERTIFIED_BY_LEVEL: dict[str, BinValuePolicy] = {
    "AAA": BinValuePolicy(
        level_group="AAA",
        prior_strength=25,
        status="certified_pooled",
        prior_scope="same_level_same_season_leave_target_environment_out",
        evidence=(
            "2025 split-half + five-fold primary validation and pre-specified "
            "independent 2024 confirmation; ADR 014"
        ),
    ),
    "AA": BinValuePolicy(
        level_group="AA",
        prior_strength=75,
        status="certified_pooled",
        prior_scope="same_level_same_season_leave_target_environment_out",
        evidence=(
            "2025 screened split-half + five-fold validation followed by "
            "pre-specified 2024 confirmation; ADR 017"
        ),
    ),
    "HIGH_A": BinValuePolicy(
        level_group="HIGH_A",
        prior_strength=0,
        status="certified_direct",
        prior_scope=None,
        evidence=(
            "2025 nominated lambda=150, but pre-specified 2024 confirmation "
            "failed event-MAE criterion; direct retained; ADR 017"
        ),
    ),
    "SINGLE_A": BinValuePolicy(
        level_group="SINGLE_A",
        prior_strength=25,
        status="certified_pooled",
        prior_scope="same_level_same_season_leave_target_environment_out",
        evidence=(
            "2025 screened split-half + five-fold validation followed by "
            "pre-specified 2024 confirmation; ADR 017"
        ),
    ),
    "ROOKIE_COMPLEX": BinValuePolicy(
        level_group="ROOKIE_COMPLEX",
        prior_strength=0,
        status="certified_direct",
        prior_scope=None,
        evidence=(
            "split-half and five-fold evidence disagreed on positive pooling; "
            "conservative direct estimator retained"
        ),
    ),
}


def bin_value_policy_for_level(level_group: str) -> BinValuePolicy:
    """Return the certified policy for a normalized affiliated level group."""

    key = str(level_group).strip().upper().replace("-", "_")
    if key in _CERTIFIED_BY_LEVEL:
        return _CERTIFIED_BY_LEVEL[key]
    return BinValuePolicy(
        level_group=key,
        prior_strength=0,
        status="uncertified",
        prior_scope=None,
        evidence="no certified Performance-bin estimator policy for this level group",
    )


def bin_value_policy_for_league(league_id: int) -> BinValuePolicy:
    """Resolve a current affiliated league ID to its certified estimator policy."""

    level = LEAGUE_LEVEL_GROUP.get(int(league_id))
    if level is None:
        return BinValuePolicy(
            level_group="UNKNOWN",
            prior_strength=0,
            status="uncertified",
            prior_scope=None,
            evidence=f"league_id={int(league_id)} is not in the certified affiliated map",
        )
    return bin_value_policy_for_level(level)
