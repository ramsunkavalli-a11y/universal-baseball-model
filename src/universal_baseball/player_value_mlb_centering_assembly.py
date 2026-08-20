"""Reference-cohort assembly helpers for Player Value v1 MLB centering.

The centering arithmetic lives in :mod:`player_value_mlb_centering`. This module
owns the stricter data-boundary checks needed to turn the frozen 2024 Playing
Time exposure surface plus official MLB membership into reference rows.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Mapping

from universal_baseball.player_value_mlb_centering import ReferencePlayerComponents

EXPECTED_2024_MLB_REFERENCE_PLAYER_COUNT = 651
REFERENCE_SEASON = 2024


@dataclass(frozen=True, slots=True)
class PlayingTimeReferenceCandidate:
    """Playing Time evidence used for projected exposure and source diagnostics."""

    player_id: int
    observed_mlb_pa: float
    projected_expected_mlb_pa: float


@dataclass(frozen=True, slots=True)
class OfficialMLBReferenceCandidate:
    """Official pooled MLB PA evidence used to define fixed membership."""

    player_id: int
    official_mlb_pa: float


@dataclass(frozen=True, slots=True)
class FixedMLBReferenceMember:
    """One fixed 2024 MLB reference member with frozen projected PA."""

    player_id: int
    projected_expected_mlb_pa: float


@dataclass(frozen=True, slots=True)
class FixedMLBReferenceMembershipSummary:
    reference_season: int
    reference_player_count: int
    aggregate_projected_mlb_pa: float


def _positive_player_id(value: object) -> int:
    if isinstance(value, bool):
        raise ValueError(f"player_id must be a positive integer; got {value!r}")
    try:
        numeric = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"player_id must be a positive integer; got {value!r}") from exc
    try:
        as_float = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"player_id must be a positive integer; got {value!r}") from exc
    if numeric <= 0 or not math.isfinite(as_float) or as_float != float(numeric):
        raise ValueError(f"player_id must be a positive integer; got {value!r}")
    return numeric


def _finite(value: object, *, field: str) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric; got {value!r}") from exc
    if not math.isfinite(numeric):
        raise ValueError(f"{field} must be finite; got {numeric}")
    return numeric


def _finite_nonnegative(value: object, *, field: str) -> float:
    numeric = _finite(value, field=field)
    if numeric < 0.0:
        raise ValueError(f"{field} must be nonnegative; got {numeric}")
    return numeric


def select_fixed_2024_mlb_reference_members(
    rows: Iterable[PlayingTimeReferenceCandidate],
    *,
    expected_player_count: int = EXPECTED_2024_MLB_REFERENCE_PLAYER_COUNT,
) -> tuple[FixedMLBReferenceMember, ...]:
    """Select a positive-observed-PA cohort from Playing Time evidence.

    This helper remains useful for isolated Playing Time validation. Production
    2024 centering membership must use
    :func:`reconcile_fixed_2024_mlb_reference_members`, because the Playing Time
    target's observed-PA accounting is not the official membership authority.
    """

    if int(expected_player_count) <= 0:
        raise ValueError("expected_player_count must be positive")

    seen_ids: set[int] = set()
    members: list[FixedMLBReferenceMember] = []

    for index, row in enumerate(rows):
        player_id = _positive_player_id(row.player_id)
        if player_id in seen_ids:
            raise ValueError(f"duplicate Playing Time player_id: {player_id}")
        seen_ids.add(player_id)

        observed_pa = _finite_nonnegative(
            row.observed_mlb_pa,
            field=f"rows[{index}].observed_mlb_pa",
        )
        projected_pa = _finite_nonnegative(
            row.projected_expected_mlb_pa,
            field=f"rows[{index}].projected_expected_mlb_pa",
        )
        if observed_pa <= 0.0:
            continue

        members.append(
            FixedMLBReferenceMember(
                player_id=player_id,
                projected_expected_mlb_pa=projected_pa,
            )
        )

    members.sort(key=lambda row: row.player_id)
    if len(members) != int(expected_player_count):
        raise ValueError(
            "fixed 2024 MLB reference cohort count mismatch: "
            f"expected {int(expected_player_count)}, got {len(members)}"
        )
    return tuple(members)


def reconcile_fixed_2024_mlb_reference_members(
    playing_time_rows: Iterable[PlayingTimeReferenceCandidate],
    official_rows: Iterable[OfficialMLBReferenceCandidate],
    *,
    expected_player_count: int = EXPECTED_2024_MLB_REFERENCE_PLAYER_COUNT,
) -> tuple[FixedMLBReferenceMember, ...]:
    """Anchor membership to official MLB PA and attach frozen projected PA.

    Positive pooled official MLB PA defines the binding cohort. Playing Time is
    required to provide one finite projected-PA exposure row for every official
    member. Its own ``observed_mlb_pa`` field is validated and retained only as a
    diagnostic; it may not override official membership or official PA totals.
    """

    if int(expected_player_count) <= 0:
        raise ValueError("expected_player_count must be positive")

    playing_time_by_id: dict[int, PlayingTimeReferenceCandidate] = {}
    for index, row in enumerate(playing_time_rows):
        player_id = _positive_player_id(row.player_id)
        if player_id in playing_time_by_id:
            raise ValueError(f"duplicate Playing Time player_id: {player_id}")
        observed_pa = _finite_nonnegative(
            row.observed_mlb_pa,
            field=f"playing_time_rows[{index}].observed_mlb_pa",
        )
        projected_pa = _finite_nonnegative(
            row.projected_expected_mlb_pa,
            field=f"playing_time_rows[{index}].projected_expected_mlb_pa",
        )
        playing_time_by_id[player_id] = PlayingTimeReferenceCandidate(
            player_id=player_id,
            observed_mlb_pa=observed_pa,
            projected_expected_mlb_pa=projected_pa,
        )

    official_positive_ids: set[int] = set()
    seen_official_ids: set[int] = set()
    for index, row in enumerate(official_rows):
        player_id = _positive_player_id(row.player_id)
        if player_id in seen_official_ids:
            raise ValueError(f"duplicate official MLB player_id: {player_id}")
        seen_official_ids.add(player_id)
        official_pa = _finite_nonnegative(
            row.official_mlb_pa,
            field=f"official_rows[{index}].official_mlb_pa",
        )
        if official_pa > 0.0:
            official_positive_ids.add(player_id)

    if len(official_positive_ids) != int(expected_player_count):
        raise ValueError(
            "official 2024 MLB positive-PA cohort count mismatch: "
            f"expected {int(expected_player_count)}, got {len(official_positive_ids)}"
        )

    missing_exposure_rows = sorted(official_positive_ids - set(playing_time_by_id))
    if missing_exposure_rows:
        raise ValueError(
            "official MLB centering members are missing Playing Time projected-PA rows: "
            f"{missing_exposure_rows[:10]}"
        )

    return tuple(
        FixedMLBReferenceMember(
            player_id=player_id,
            projected_expected_mlb_pa=playing_time_by_id[
                player_id
            ].projected_expected_mlb_pa,
        )
        for player_id in sorted(official_positive_ids)
    )


def summarize_fixed_mlb_reference_membership(
    members: Iterable[FixedMLBReferenceMember],
    *,
    reference_season: int = REFERENCE_SEASON,
) -> FixedMLBReferenceMembershipSummary:
    materialized = tuple(members)
    if not materialized:
        raise ValueError("fixed MLB reference membership must not be empty")

    ids: set[int] = set()
    projected_pa: list[float] = []
    for index, member in enumerate(materialized):
        player_id = _positive_player_id(member.player_id)
        if player_id in ids:
            raise ValueError(f"duplicate reference player_id: {player_id}")
        ids.add(player_id)
        projected_pa.append(
            _finite_nonnegative(
                member.projected_expected_mlb_pa,
                field=f"members[{index}].projected_expected_mlb_pa",
            )
        )

    aggregate_pa = math.fsum(projected_pa)
    if aggregate_pa <= 0.0:
        raise ValueError("aggregate projected MLB PA must be positive")

    return FixedMLBReferenceMembershipSummary(
        reference_season=int(reference_season),
        reference_player_count=len(materialized),
        aggregate_projected_mlb_pa=aggregate_pa,
    )


def _normalize_component_map(
    values: Mapping[int, object],
    *,
    component_name: str,
) -> dict[int, float]:
    normalized: dict[int, float] = {}
    for raw_player_id, raw_value in values.items():
        player_id = _positive_player_id(raw_player_id)
        if player_id in normalized:
            raise ValueError(f"duplicate {component_name} player_id: {player_id}")
        normalized[player_id] = _finite(
            raw_value,
            field=f"{component_name}[{player_id}]",
        )
    return normalized


def assemble_fixed_mlb_reference_components(
    members: Iterable[FixedMLBReferenceMember],
    *,
    batting_runs_by_player: Mapping[int, object],
    baserunning_runs_by_player: Mapping[int, object],
    defense_runs_by_player: Mapping[int, object],
    positional_runs_by_player: Mapping[int, object],
) -> tuple[ReferencePlayerComponents, ...]:
    """Attach all four frozen above-average components to every cohort member.

    Extra component rows outside the fixed reference cohort are harmless and are
    ignored. Missing component rows for a reference player are fatal: any neutral
    or universal fallback must have been materialized upstream as an explicit
    finite value (normally zero where the frozen contract says neutral).
    """

    materialized_members = tuple(members)
    if not materialized_members:
        raise ValueError("fixed MLB reference membership must not be empty")

    components = {
        "batting_runs": _normalize_component_map(
            batting_runs_by_player,
            component_name="batting_runs",
        ),
        "baserunning_runs": _normalize_component_map(
            baserunning_runs_by_player,
            component_name="baserunning_runs",
        ),
        "defense_runs": _normalize_component_map(
            defense_runs_by_player,
            component_name="defense_runs",
        ),
        "positional_runs": _normalize_component_map(
            positional_runs_by_player,
            component_name="positional_runs",
        ),
    }

    seen_ids: set[int] = set()
    assembled: list[ReferencePlayerComponents] = []
    for index, member in enumerate(materialized_members):
        player_id = _positive_player_id(member.player_id)
        if player_id in seen_ids:
            raise ValueError(f"duplicate reference player_id: {player_id}")
        seen_ids.add(player_id)
        projected_pa = _finite_nonnegative(
            member.projected_expected_mlb_pa,
            field=f"members[{index}].projected_expected_mlb_pa",
        )

        missing = [name for name, values in components.items() if player_id not in values]
        if missing:
            raise ValueError(
                f"reference player_id {player_id} is missing component rows: "
                + ", ".join(missing)
            )

        assembled.append(
            ReferencePlayerComponents(
                player_id=player_id,
                projected_expected_mlb_pa=projected_pa,
                batting_runs=components["batting_runs"][player_id],
                baserunning_runs=components["baserunning_runs"][player_id],
                defense_runs=components["defense_runs"][player_id],
                positional_runs=components["positional_runs"][player_id],
            )
        )

    assembled.sort(key=lambda row: row.player_id)
    return tuple(assembled)
