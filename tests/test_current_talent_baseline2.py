from __future__ import annotations

from datetime import date, timedelta

import polars as pl
import pytest
from polars.testing import assert_frame_equal

from universal_baseball.current_talent_baseline2 import (
    BASELINE2_LOOKBACK_DAYS,
    FROZEN_BASELINE2_HALF_LIFE_DAYS,
    build_baseline2_profiles,
    build_frozen_b1_vs_b2_scoring_pair,
)
from universal_baseball.current_talent_baselines import (
    build_baseline_profiles,
    build_recency_weighted_level_profile,
    build_translated_player_evidence,
    fit_leave_one_out_age_level_prior,
)
from universal_baseball.current_talent_evidence import EvidenceWindow
from universal_baseball.performance_season import ALL_CORE_BINS


B2_LOOKBACK_DAYS = BASELINE2_LOOKBACK_DAYS
FROZEN_HALF_LIFE_DAYS = FROZEN_BASELINE2_HALF_LIFE_DAYS


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


def _translated_players(player_counts: dict[int, dict[str, float]]) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for player_id, supplied in player_counts.items():
        counts = {core_bin: float(supplied.get(core_bin, 0.0)) for core_bin in ALL_CORE_BINS}
        total = sum(counts.values())
        for core_bin in ALL_CORE_BINS:
            rows.append(
                {
                    "player_id": player_id,
                    "core_bin": core_bin,
                    "translated_effective_count": counts[core_bin],
                    "effective_core_events": total,
                    "translated_mlb_rate": counts[core_bin] / total,
                }
            )
    return pl.DataFrame(rows)


def _frozen_prior(translated: pl.DataFrame) -> pl.DataFrame:
    context = pl.DataFrame(
        {
            "player_id": [1, 2, 3],
            "age_years": [22.2, 22.7, 22.9],
            "as_of_level_group": ["AAA", "AAA", "AAA"],
            "as_of_environment_ambiguous": [False, False, False],
        }
    )
    return fit_leave_one_out_age_level_prior(
        translated,
        context,
        min_age_level_peers=2,
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


def test_baseline2_reuses_frozen_prior_and_pairs_cleanly_for_scoring() -> None:
    current = _translated_players(
        {
            1: {"K": 90.0, "BB_HBP": 10.0},
            2: {"K": 20.0, "BB_HBP": 80.0},
            3: {"K": 30.0, "BB_HBP": 70.0},
        }
    )
    multiseason = _translated_players(
        {
            1: {"K": 100.0, "BB_HBP": 30.0},
            2: {"K": 30.0, "BB_HBP": 100.0},
            3: {"K": 45.0, "BB_HBP": 85.0},
        }
    )
    prior = _frozen_prior(current)
    frozen = build_baseline_profiles(current, prior, prior_strength_core_events=100.0)
    b2 = build_baseline2_profiles(multiseason, prior, prior_strength_core_events=100.0)
    pair = build_frozen_b1_vs_b2_scoring_pair(frozen, b2)

    expected_frozen = frozen.profile.select(
        "player_id",
        "core_bin",
        pl.col("baseline1_latent_probability").alias("baseline0_latent_probability"),
    )
    expected_b2 = b2.profile.select(
        "player_id",
        "core_bin",
        pl.col("baseline2_latent_probability").alias("baseline1_latent_probability"),
    )
    expected = expected_frozen.join(expected_b2, on=["player_id", "core_bin"]).sort(
        ["player_id", "core_bin"]
    )
    assert_frame_equal(pair, expected, check_row_order=True, check_column_order=True)


def test_baseline2_pair_rejects_a_changed_baseline0_prior() -> None:
    current = _translated_players(
        {
            1: {"K": 90.0, "BB_HBP": 10.0},
            2: {"K": 20.0, "BB_HBP": 80.0},
            3: {"K": 30.0, "BB_HBP": 70.0},
        }
    )
    prior = _frozen_prior(current)
    frozen = build_baseline_profiles(current, prior, prior_strength_core_events=100.0)
    b2 = build_baseline2_profiles(current, prior, prior_strength_core_events=100.0)
    broken = type(b2)(
        profile=b2.profile.with_columns(
            pl.when((pl.col("player_id") == 1) & (pl.col("core_bin") == "K"))
            .then(pl.col("baseline0_latent_probability") + 0.01)
            .otherwise(pl.col("baseline0_latent_probability"))
            .alias("baseline0_latent_probability")
        ),
        metrics=b2.metrics,
    )

    with pytest.raises(ValueError, match="does not share the frozen Baseline 0 prior"):
        build_frozen_b1_vs_b2_scoring_pair(frozen, broken)
