from __future__ import annotations

from datetime import date, timedelta

import polars as pl
import pytest

from universal_baseball.current_talent_contact_value import FROZEN_TERMINAL_OUTCOME_VALUES
from universal_baseball.current_talent_contact_value_evidence import (
    CONTACT_VALUE_ALLOWED_LEVEL_GROUPS,
    build_contact_value_cutoff_surface,
    prepare_contact_value_evidence,
)
from universal_baseball.performance_season import CONTACT_CORE_BINS


LEVEL_LEAGUE = {
    "MLB": 103,
    "AAA": 112,
    "AA": 109,
    "HIGH_A": 116,
    "SINGLE_A": 110,
    "ROOKIE_COMPLEX": 121,
}


def _row(
    *,
    event_date: date,
    game_pk: int,
    at_bat_index: int,
    pitch_number: int,
    level_group: str = "MLB",
    contact_bin: str = "IFFB",
    terminal_group: str = "OUT",
) -> dict[str, object]:
    return {
        "event_date": event_date,
        "game_pk": game_pk,
        "at_bat_index": at_bat_index,
        "pitch_number": pitch_number,
        "league_id": LEVEL_LEAGUE.get(level_group, 999),
        "level_group": level_group,
        "player_id": 500000 + game_pk,
        "participant_authority": "fixture",
        "contact_bin": contact_bin,
        "terminal_outcome_group": terminal_group,
        "terminal_outcome_status": "fixture_supported",
    }


def _full_rank_cutoff_fixture(cutoff: date = date(2022, 7, 15)) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    game_pk = 1
    # Full cross-product before the cutoff guarantees support/full rank for the
    # frozen additive contact-bin + level-group baseline.
    for level in sorted(CONTACT_VALUE_ALLOWED_LEVEL_GROUPS):
        for index, contact_bin in enumerate(CONTACT_CORE_BINS):
            terminal_group = list(FROZEN_TERMINAL_OUTCOME_VALUES)[index % 9]
            rows.append(
                _row(
                    event_date=cutoff - timedelta(days=1),
                    game_pk=game_pk,
                    at_bat_index=index,
                    pitch_number=1,
                    level_group=level,
                    contact_bin=contact_bin,
                    terminal_group=terminal_group,
                )
            )
            game_pk += 1

    # Exact half-open boundary probes.
    rows.extend(
        [
            _row(
                event_date=cutoff,
                game_pk=1001,
                at_bat_index=1,
                pitch_number=1,
                level_group="MLB",
                contact_bin="CENTER_LD",
                terminal_group="1B",
            ),
            _row(
                event_date=cutoff + timedelta(days=89),
                game_pk=1002,
                at_bat_index=1,
                pitch_number=1,
                level_group="AAA",
                contact_bin="PULL_GB",
                terminal_group="HR",
            ),
            _row(
                event_date=cutoff + timedelta(days=90),
                game_pk=1003,
                at_bat_index=1,
                pitch_number=1,
                level_group="AA",
                contact_bin="OPPO_GB",
                terminal_group="OUT",
            ),
        ]
    )
    return pl.DataFrame(rows)


def test_prepare_combines_sources_and_attaches_exact_frozen_values() -> None:
    frame = pl.DataFrame(
        [
            _row(
                event_date=date(2021, 6, 1),
                game_pk=1,
                at_bat_index=1,
                pitch_number=1,
                terminal_group="HR",
            ),
            _row(
                event_date=date(2022, 6, 1),
                game_pk=2,
                at_bat_index=1,
                pitch_number=1,
                level_group="AAA",
                terminal_group="MULTI_OUT",
            ),
        ]
    )
    valued, metrics = prepare_contact_value_evidence([frame.head(1), frame.tail(1)])
    assert valued.height == 2
    by_group = {
        row["terminal_outcome_group"]: row["terminal_value"] for row in valued.to_dicts()
    }
    assert by_group["HR"] == FROZEN_TERMINAL_OUTCOME_VALUES["HR"]
    assert by_group["MULTI_OUT"] == FROZEN_TERMINAL_OUTCOME_VALUES["MULTI_OUT"]
    assert metrics["source_frame_count"] == 2
    assert metrics["terminal_values_attached"] is True
    assert metrics["model_scoring"] is False
    assert metrics["accessed_2023"] is False


def test_prepare_rejects_duplicate_target_keys_across_sources() -> None:
    row = pl.DataFrame(
        [
            _row(
                event_date=date(2022, 6, 1),
                game_pk=5,
                at_bat_index=2,
                pitch_number=1,
            )
        ]
    )
    with pytest.raises(ValueError, match="duplicate target contact keys"):
        prepare_contact_value_evidence([row, row])


def test_prepare_rejects_2023_before_any_scoring() -> None:
    frame = pl.DataFrame(
        [
            _row(
                event_date=date(2023, 4, 1),
                game_pk=6,
                at_bat_index=1,
                pitch_number=1,
            )
        ]
    )
    with pytest.raises(ValueError, match="unauthorized source years.*2023"):
        prepare_contact_value_evidence([frame])


def test_prepare_rejects_unknown_group_bin_and_level() -> None:
    base = _row(
        event_date=date(2022, 6, 1),
        game_pk=7,
        at_bat_index=1,
        pitch_number=1,
    )
    for field, value, match in (
        ("terminal_outcome_group", "MAGIC", "unsupported terminal groups"),
        ("contact_bin", "MOONSHOT", "unsupported contact bins"),
        ("level_group", "UNKNOWN_LEVEL", "unsupported level groups"),
    ):
        changed = dict(base)
        changed[field] = value
        with pytest.raises(ValueError, match=match):
            prepare_contact_value_evidence([pl.DataFrame([changed])])


def test_cutoff_surface_enforces_exact_half_open_90_day_window() -> None:
    cutoff = date(2022, 7, 15)
    valued, _ = prepare_contact_value_evidence([_full_rank_cutoff_fixture(cutoff)])
    surface = build_contact_value_cutoff_surface(valued, cutoff_date=cutoff)

    assert surface.baseline_contacts.get_column("event_date").max() == cutoff - timedelta(days=1)
    assert surface.future_end_exclusive == cutoff + timedelta(days=90)
    assert surface.future_contacts.get_column("event_date").to_list() == [
        cutoff,
        cutoff + timedelta(days=89),
    ]
    assert surface.future_contacts.get_column("game_pk").to_list() == [1001, 1002]
    assert surface.metrics["future_window_calendar_days"] == 90
    assert surface.metrics["future_target_contact_count"] == 2
    assert surface.metrics["baseline_fit_event_count"] == len(CONTACT_CORE_BINS) * len(
        CONTACT_VALUE_ALLOWED_LEVEL_GROUPS
    )
    assert set(surface.baseline_fit.contact_bin_effects) == set(CONTACT_CORE_BINS)
    assert set(surface.baseline_fit.fitted_level_groups) == set(CONTACT_VALUE_ALLOWED_LEVEL_GROUPS)
    assert surface.metrics["model_scoring"] is False
    assert surface.metrics["richer_features_attached"] is False
    assert surface.metrics["accessed_2023"] is False


def test_cutoff_surface_rejects_nonfrozen_cutoff_including_2023() -> None:
    valued, _ = prepare_contact_value_evidence([_full_rank_cutoff_fixture()])
    with pytest.raises(ValueError, match="not frozen/authorized"):
        build_contact_value_cutoff_surface(valued, cutoff_date=date(2023, 7, 15))


def test_cutoff_surface_requires_all_frozen_baseline_bins() -> None:
    cutoff = date(2022, 7, 15)
    frame = _full_rank_cutoff_fixture(cutoff).filter(pl.col("contact_bin") != "IFFB")
    valued, _ = prepare_contact_value_evidence([frame])
    with pytest.raises(ValueError, match="lacks frozen contact-bin support.*IFFB"):
        build_contact_value_cutoff_surface(valued, cutoff_date=cutoff)


def test_future_key_surface_is_exactly_the_future_target_rows() -> None:
    cutoff = date(2022, 7, 15)
    valued, _ = prepare_contact_value_evidence([_full_rank_cutoff_fixture(cutoff)])
    surface = build_contact_value_cutoff_surface(valued, cutoff_date=cutoff)
    expected = surface.future_contacts.select("game_pk", "at_bat_index", "pitch_number").sort(
        ["game_pk", "at_bat_index", "pitch_number"]
    )
    assert surface.future_target_keys.equals(expected)
    assert surface.metrics["comparator_richer_paired_key_contract"] == (
        "same_future_target_key_surface_required"
    )
