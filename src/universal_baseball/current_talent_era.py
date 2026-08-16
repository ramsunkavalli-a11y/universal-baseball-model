"""Era-safe affiliated environment topology for Current Talent history.

This module is intentionally narrower than Performance calibration config. It
only states which actual leagues belong to each reusable armstjc filename level
for the initial post-reorganization validation era certified by ADR 025.

It does not provide run values, calibration assets, level translations, age
priors, or model coefficients. Those quantities must be estimated inside the
appropriate chronological training surface.
"""

from __future__ import annotations

from dataclasses import dataclass


POST_REORGANIZATION_CURRENT_TALENT_YEARS = frozenset({2021, 2022, 2023, 2024})


@dataclass(frozen=True, slots=True)
class CurrentTalentEraLevelSpec:
    filename_level: str
    level_group: str
    display_name: str
    league_ids: frozenset[int]


POST_REORGANIZATION_LEVEL_SPECS: dict[str, CurrentTalentEraLevelSpec] = {
    "aaa": CurrentTalentEraLevelSpec(
        filename_level="aaa",
        level_group="AAA",
        display_name="Triple-A",
        league_ids=frozenset({112, 117}),
    ),
    "aa": CurrentTalentEraLevelSpec(
        filename_level="aa",
        level_group="AA",
        display_name="Double-A",
        league_ids=frozenset({109, 111, 113}),
    ),
    "a+": CurrentTalentEraLevelSpec(
        filename_level="a+",
        level_group="HIGH_A",
        display_name="High-A",
        league_ids=frozenset({116, 118, 126}),
    ),
    "a": CurrentTalentEraLevelSpec(
        filename_level="a",
        level_group="SINGLE_A",
        display_name="Single-A",
        league_ids=frozenset({110, 122, 123}),
    ),
    "rk": CurrentTalentEraLevelSpec(
        filename_level="rk",
        level_group="ROOKIE_COMPLEX",
        display_name="Rookie/complex",
        league_ids=frozenset({121, 124, 130}),
    ),
}


def current_talent_level_spec(season: int, filename_level: str) -> CurrentTalentEraLevelSpec:
    """Return the certified initial-era topology for one historical slice.

    Unsupported seasons fail rather than silently inheriting the post-2021 map.
    In particular, 2019 requires the separate pre-reorganization extension gate
    described by ADR 025.
    """

    year = int(season)
    if year not in POST_REORGANIZATION_CURRENT_TALENT_YEARS:
        raise KeyError(
            f"season {year} is outside the certified initial Current Talent era; "
            f"supported={sorted(POST_REORGANIZATION_CURRENT_TALENT_YEARS)}"
        )
    key = str(filename_level).strip().lower()
    if key not in POST_REORGANIZATION_LEVEL_SPECS:
        raise KeyError(f"unsupported affiliated filename level: {filename_level!r}")
    return POST_REORGANIZATION_LEVEL_SPECS[key]


def validate_post_reorganization_level_specs() -> None:
    """Require one-to-one actual-league ownership across filename levels."""

    seen: dict[int, str] = {}
    for key, spec in POST_REORGANIZATION_LEVEL_SPECS.items():
        if key != spec.filename_level:
            raise ValueError(f"level spec key {key!r} disagrees with filename_level")
        if not spec.league_ids:
            raise ValueError(f"level spec {key!r} has no actual leagues")
        for league_id in spec.league_ids:
            if int(league_id) in seen:
                raise ValueError(
                    f"league_id={league_id} appears in both {seen[int(league_id)]!r} and {key!r}"
                )
            seen[int(league_id)] = key


validate_post_reorganization_level_specs()
