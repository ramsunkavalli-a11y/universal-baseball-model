"""Frozen 2024 affiliated-level inputs for batting Performance materialization.

This module centralizes environment-specific filenames and current actual-league
IDs so production scripts do not scatter hard-coded level assumptions. It does
not define model behavior; estimator behavior remains in ``bin_value_policy``.
"""

from __future__ import annotations

from dataclasses import dataclass

from universal_baseball.bin_value_policy import (
    LEAGUE_LEVEL_GROUP,
    bin_value_policy_for_league,
)


@dataclass(frozen=True)
class BattingPerformanceLevelSpec:
    filename_level: str
    level_group: str
    display_name: str
    league_ids: frozenset[int]
    calibration_asset: str
    season_batting_asset: str

    @property
    def season_batting_url(self) -> str:
        return (
            "https://github.com/armstjc/milb-data-repository/releases/download/"
            f"season_player_batting/{self.season_batting_asset}"
        )


PERFORMANCE_LEVEL_SPECS_2024: dict[str, BattingPerformanceLevelSpec] = {
    "aaa": BattingPerformanceLevelSpec(
        filename_level="aaa",
        level_group="AAA",
        display_name="Triple-A",
        league_ids=frozenset({112, 117}),
        calibration_asset="2024_6_aaa_pbp.csv",
        season_batting_asset="2024_aaa_season_batting_stats.csv",
    ),
    "aa": BattingPerformanceLevelSpec(
        filename_level="aa",
        level_group="AA",
        display_name="Double-A",
        league_ids=frozenset({109, 111, 113}),
        calibration_asset="2024_6_aa_pbp.csv",
        season_batting_asset="2024_aa_season_batting_stats.csv",
    ),
    "a+": BattingPerformanceLevelSpec(
        filename_level="a+",
        level_group="HIGH_A",
        display_name="High-A",
        league_ids=frozenset({116, 118, 126}),
        calibration_asset="2024_6_a+_pbp.csv",
        season_batting_asset="2024_a+_season_batting_stats.csv",
    ),
    "a": BattingPerformanceLevelSpec(
        filename_level="a",
        level_group="SINGLE_A",
        display_name="Single-A",
        league_ids=frozenset({110, 122, 123}),
        calibration_asset="2024_6_a_pbp.csv",
        season_batting_asset="2024_a_season_batting_stats.csv",
    ),
    "rk": BattingPerformanceLevelSpec(
        filename_level="rk",
        level_group="ROOKIE_COMPLEX",
        display_name="Rookie/complex",
        league_ids=frozenset({121, 124, 130}),
        calibration_asset="2024_6_rk_pbp.csv",
        season_batting_asset="2024_rk_season_batting_stats.csv",
    ),
}


def performance_level_spec_2024(filename_level: str) -> BattingPerformanceLevelSpec:
    key = str(filename_level).strip().lower()
    if key not in PERFORMANCE_LEVEL_SPECS_2024:
        raise KeyError(f"unsupported 2024 affiliated filename level: {filename_level!r}")
    return PERFORMANCE_LEVEL_SPECS_2024[key]


def validate_performance_level_specs_2024() -> None:
    """Fail loudly if level inputs drift away from the certified policy map."""

    seen: dict[int, str] = {}
    for slug, spec in PERFORMANCE_LEVEL_SPECS_2024.items():
        if spec.filename_level != slug:
            raise ValueError(f"level spec key {slug!r} disagrees with filename_level")
        if not spec.league_ids:
            raise ValueError(f"level spec {slug!r} has no actual league IDs")
        for league_id in spec.league_ids:
            previous = seen.get(int(league_id))
            if previous is not None:
                raise ValueError(
                    f"league_id={league_id} appears in both {previous!r} and {slug!r}"
                )
            seen[int(league_id)] = slug
            mapped_group = LEAGUE_LEVEL_GROUP.get(int(league_id))
            if mapped_group != spec.level_group:
                raise ValueError(
                    f"league_id={league_id} policy group={mapped_group!r} does not match "
                    f"level spec group={spec.level_group!r}"
                )
            policy = bin_value_policy_for_league(int(league_id))
            if policy.status == "uncertified":
                raise ValueError(f"league_id={league_id} has no certified bin-value policy")

    expected = set(LEAGUE_LEVEL_GROUP)
    if set(seen) != expected:
        missing = sorted(expected - set(seen))
        extra = sorted(set(seen) - expected)
        raise ValueError(
            f"2024 Performance level specs do not cover certified affiliated map; "
            f"missing={missing}, extra={extra}"
        )


validate_performance_level_specs_2024()
