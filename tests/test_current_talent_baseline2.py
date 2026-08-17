from __future__ import annotations

from datetime import date, timedelta

import polars as pl
import pytest
from polars.testing import assert_frame_equal

from universal_baseball.current_talent_baselines import (
    build_recency_weighted_level_profile,
    build_translated_player_evidence,
)
from universal_baseball.current_talent_evidence import EvidenceWindow
from universal_baseball.performance_season import ALL_CORE_BINS


B2_LOOKBACK_DAYS = 1095
FROZEN_HALF_LIFE_DAYS = 180.0


def _summary_and_profile(game_dates: list[date], bins: list[str] | None = None) -> tuple[pl.DataFrame, pl.DataFrame]:
    if bins is None:
        bins = ["K"] * len(game_dates)
    if len(bins) != len(game_dates):
        raise ValueError("bins must align with game_dates")

    summary_rows: list[dict[str, object]] = []
    profile_rows: list[dict[str, object]] = []
    for index, (game_date, core_bin) in enumerate(zip(game_dates, bins, strict=True), start=1):
        summary_rows.append(
            {
                "season": game_date.year,
                "game_date": game_date.isoformat(),
                "game_pk": index,
                "league_id": 117,
                "player_id": 10,
                "level_group": "AAA",
                "batting_plate_appearances": 1,
                "expected_contact_count": 0,
                "observed_contact_count": 0,
                "contact_count_residual": 0,
                "core_profile_event_count": 1,
                "bunt_contact_count": 0,
                "foul_air_excluded_count": 0,
                "unknown_contact_count": 0,
                "special_noncontact_count": 0,
                "pa_accounting_residual": 0,
                "participant_authority_status": "source_default",
                "source_capability_tier": "universal_result_contact_profile_v2",
            }
        )
        profile_rows.append(
            {
                "season": game_date.year,
                "game_date": game_date.isoformat(),
                "game_pk": index,
                "league_id": 117,
                "player_id": 10,
                "level_group": "AAA",
                "core_bin": core_bin,
                "occurrence_count": 1,
            }
        )
    return pl.DataFrame(summary_rows), pl.DataFrame(profile_rows)


def _zero_offsets() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "level_group": level_group,
                "core_bin": core_bin,
                "clr_environment_effect": 0.0,
            }
            for level_group in ("AAA", "MLB")
            for core_bin in ALL_CORE_BINS
        ]
    )


def _b1_window() -> EvidenceWindow:
    return EvidenceWindow(
        label="frozen_b1_season_to_date_180d",
        lookback_days=None,
        half_life_days=FROZEN_HALF_LIFE_DAYS,
    )


def _b2_window() -> EvidenceWindow:
    return EvidenceWindow(
        label="baseline2_multiseason_1095d_180d",
        lookback_days=B2_LOOKBACK_DAYS,
        half_life_days=FROZEN_HALF_LIFE_DAYS,
    )


def test_baseline2_window_crosses_seasons_without_reset_and_enforces_cap() -> None:
    cutoff = date(2024, 7, 1)
    ages = [1, 180, 365, 1095, 1096, -1]
    game_dates = [cutoff - timedelta(days=days_old) for days_old in ages]
    summary, profile = _summary_and_profile(game_dates)

    result = build_recency_weighted_level_profile(
        summary,
        profile,
        cutoff=cutoff,
        window=_b2_window(),
    )

    expected_days = [1, 180, 365, 1095]
    expected_weight = sum(2 ** (-days_old / FROZEN_HALF_LIFE_DAYS) for days_old in expected_days)

    assert result.height == 1
    assert result.item(0, "core_bin") == "K"
    assert result.item(0, "effective_occurrence_count") == pytest.approx(expected_weight)
    assert result.item(0, "effective_core_events") == pytest.approx(expected_weight)

    # The 365-day observation is in the prior season but receives the same
    # continuous exponential weighting implied by its calendar age; Opening Day
    # does not reset its weight.
    assert 2 ** (-365 / FROZEN_HALF_LIFE_DAYS) > 0


def test_baseline2_equals_frozen_b1_when_only_current_season_evidence_exists() -> None:
    cutoff = date(2024, 7, 15)
    summary, profile = _summary_and_profile(
        [cutoff - timedelta(days=1), cutoff - timedelta(days=30)],
        ["K", "BB_HBP"],
    )

    b1 = build_translated_player_evidence(
        summary,
        profile,
        _zero_offsets(),
        cutoff=cutoff,
        window=_b1_window(),
    )
    b2 = build_translated_player_evidence(
        summary,
        profile,
        _zero_offsets(),
        cutoff=cutoff,
        window=_b2_window(),
    )

    assert_frame_equal(b1, b2, check_row_order=True, check_column_order=True)


def test_baseline2_adds_prior_season_player_evidence_without_changing_current_events() -> None:
    cutoff = date(2024, 7, 15)
    prior_date = date(2023, 8, 15)
    current_date = cutoff - timedelta(days=1)
    summary, profile = _summary_and_profile(
        [prior_date, current_date],
        ["BB_HBP", "K"],
    )
    current_summary = summary.filter(pl.col("season") == cutoff.year)
    current_profile = profile.filter(pl.col("season") == cutoff.year)

    b1 = build_translated_player_evidence(
        current_summary,
        current_profile,
        _zero_offsets(),
        cutoff=cutoff,
        window=_b1_window(),
    )
    b2 = build_translated_player_evidence(
        summary,
        profile,
        _zero_offsets(),
        cutoff=cutoff,
        window=_b2_window(),
    )

    b1_total = b1.get_column("effective_core_events").unique().item()
    b2_total = b2.get_column("effective_core_events").unique().item()
    assert b2_total > b1_total

    b1_bb = b1.filter(pl.col("core_bin") == "BB_HBP").item(0, "translated_mlb_rate")
    b2_bb = b2.filter(pl.col("core_bin") == "BB_HBP").item(0, "translated_mlb_rate")
    assert b2_bb > b1_bb
