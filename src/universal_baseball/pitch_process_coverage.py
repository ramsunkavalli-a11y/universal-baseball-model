"""Certified availability of pitch-process evidence by league and season.

This module is deliberately conservative. A row existing in play-by-play does
not imply that its intermediate pitch sequence represents physical pitches.
Only league-season combinations that have passed the dedicated official-feed
fidelity audit are marked eligible. Everything else is uncertified by default.

PA outcomes, terminal batted-ball evidence, and state transitions are separate
evidence surfaces and are not disabled by an ineligible pitch-process status.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


PitchProcessStatus = Literal[
    "eligible",
    "ineligible_synthetic_sequence",
    "uncertified",
]


@dataclass(frozen=True)
class PitchProcessCapability:
    season: int
    league_id: int
    league_name: str
    status: PitchProcessStatus
    evidence: str


# MLB Stats API league IDs used in the certified Rookie/complex samples.
_ACL = 121
_FCL = 124
_DSL = 130
_FULL_SEASON_LEAGUES = {
    109: "Southern League",
    110: "California League",
    111: "Eastern League",
    112: "International League",
    113: "Texas League",
    116: "South Atlantic League",
    117: "Pacific Coast League",
    118: "Midwest League",
    122: "Carolina League",
    123: "Florida State League",
    126: "Northwest League",
}


_CERTIFIED: dict[tuple[int, int], PitchProcessCapability] = {
    (2023, _ACL): PitchProcessCapability(
        season=2023,
        league_id=_ACL,
        league_name="Arizona Complex League",
        status="ineligible_synthetic_sequence",
        evidence="20-game August 2023 official-feed audit; outcome-minimal K/BB/BIP signatures",
    ),
    (2023, _FCL): PitchProcessCapability(
        season=2023,
        league_id=_FCL,
        league_name="Florida Complex League",
        status="ineligible_synthetic_sequence",
        evidence="20-game August 2023 official-feed audit; outcome-minimal K/BB/BIP signatures",
    ),
    (2023, _DSL): PitchProcessCapability(
        season=2023,
        league_id=_DSL,
        league_name="Dominican Summer League",
        status="ineligible_synthetic_sequence",
        evidence="20-game August 2023 official-feed audit; outcome-minimal K/BB/BIP signatures",
    ),
    (2024, _ACL): PitchProcessCapability(
        season=2024,
        league_id=_ACL,
        league_name="Arizona Complex League",
        status="eligible",
        evidence="20-game June 2024 official-feed audit; sequence distributions comparable to Single-A control",
    ),
    (2024, _FCL): PitchProcessCapability(
        season=2024,
        league_id=_FCL,
        league_name="Florida Complex League",
        status="eligible",
        evidence="20-game June 2024 official-feed audit; sequence distributions comparable to Single-A control",
    ),
    (2024, _DSL): PitchProcessCapability(
        season=2024,
        league_id=_DSL,
        league_name="Dominican Summer League",
        status="ineligible_synthetic_sequence",
        evidence="20-game June 2024 official-feed audit; outcome-minimal K/BB/BIP signatures",
    ),
}

# A 20-game-per-level August audit in each season sampled every actual full-season
# affiliated league. All showed normal pitch-count distributions near the Single-A
# control rather than the roughly 90% outcome-minimal Rookie signature.
for _season in (2018, 2019, 2021, 2022, 2023, 2024):
    for _league_id, _league_name in _FULL_SEASON_LEAGUES.items():
        _CERTIFIED[(_season, _league_id)] = PitchProcessCapability(
            season=_season,
            league_id=_league_id,
            league_name=_league_name,
            status="eligible",
            evidence=(
                f"20-game-per-level August {_season} official-feed audit; "
                "sequence distributions inconsistent with outcome-minimal entry"
            ),
        )
    if _season not in {2021, 2022}:
        continue
    for _league_id, _league_name in {
        _ACL: "Arizona Complex League",
        _FCL: "Florida Complex League",
        _DSL: "Dominican Summer League",
    }.items():
        _CERTIFIED[(_season, _league_id)] = PitchProcessCapability(
            season=_season,
            league_id=_league_id,
            league_name=_league_name,
            status="ineligible_synthetic_sequence",
            evidence=(
                f"20-game-per-level August {_season} official-feed audit; "
                "outcome-minimal K/BB/BIP signatures"
            ),
        )


def pitch_process_capability(season: int, league_id: int) -> PitchProcessCapability:
    """Return certified pitch-process capability, defaulting to uncertified."""

    key = (int(season), int(league_id))
    if key in _CERTIFIED:
        return _CERTIFIED[key]
    return PitchProcessCapability(
        season=int(season),
        league_id=int(league_id),
        league_name="unknown_or_uncertified",
        status="uncertified",
        evidence="no dedicated league-season pitch-sequence fidelity certification",
    )


def pitch_process_is_eligible(season: int, league_id: int) -> bool:
    """True only when the league-season has explicit fidelity certification."""

    return pitch_process_capability(season, league_id).status == "eligible"
