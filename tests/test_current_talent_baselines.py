from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.current_talent_baselines import (
    BASELINE0_METHOD,
    BASELINE1_METHOD,
    aggregate_translated_player_profile,
    build_baseline_profiles,
    fit_leave_one_out_age_level_prior,
    translate_level_profile_to_mlb,
)
from universal_baseball.performance_season import ALL_CORE_BINS


def _offsets(*, level: str = "AAA", k_effect: float = 0.0) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for level_group in (level, "MLB"):
        for core_bin in ALL_CORE_BINS:
            effect = 0.0
            if level_group != "MLB":
                if core_bin == "K":
                    effect = k_effect
                elif core_bin == "BB_HBP":
                    effect = -k_effect
            rows.append(
                {
                    "level_group": level_group,
                    "core_bin": core_bin,
                    "clr_environment_effect": effect,
                }
            )
    return pl.DataFrame(rows)


def _level_profile(counts: dict[str, float], *, player_id: int = 1, level: str = "AAA") -> pl.DataFrame:
    total = sum(counts.values())
    return pl.DataFrame(
        [
            {
                "player_id": player_id,
                "level_group": level,
                "core_bin": core_bin,
                "effective_occurrence_count": count,
                "effective_core_events": total,
            }
            for core_bin, count in counts.items()
            if count > 0
        ]
    )


def _translated_players(player_counts: dict[int, dict[str, float]]) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for player_id, supplied in player_counts.items():
        counts = {core_bin: float(supplied.get(core_bin, 0.0)) for core_bin in ALL_CORE_BINS}
        total = sum(counts.values())
        assert total > 0
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


def test_zero_environment_effect_preserves_smoothed_profile_and_evidence_total() -> None:
    profile = _level_profile({"K": 6.0, "BB_HBP": 4.0})
    result = translate_level_profile_to_mlb(profile, _offsets(k_effect=0.0))

    assert result.height == len(ALL_CORE_BINS)
    assert result.get_column("translated_effective_count").sum() == pytest.approx(10.0)
    k = result.filter(pl.col("core_bin") == "K").to_dicts()[0]
    expected_k = (6.0 + 0.5) / (10.0 + 0.5 * len(ALL_CORE_BINS))
    assert k["translated_mlb_rate"] == pytest.approx(expected_k)


def test_translation_direction_removes_level_effect_before_aggregation() -> None:
    profile = _level_profile({"K": 6.0, "BB_HBP": 4.0})
    zero = translate_level_profile_to_mlb(profile, _offsets(k_effect=0.0))
    adjusted = translate_level_profile_to_mlb(profile, _offsets(k_effect=-0.30))

    zero_k = zero.filter(pl.col("core_bin") == "K").item(0, "translated_mlb_rate")
    adjusted_k = adjusted.filter(pl.col("core_bin") == "K").item(0, "translated_mlb_rate")
    zero_bb = zero.filter(pl.col("core_bin") == "BB_HBP").item(0, "translated_mlb_rate")
    adjusted_bb = adjusted.filter(pl.col("core_bin") == "BB_HBP").item(0, "translated_mlb_rate")

    assert adjusted_k > zero_k
    assert adjusted_bb < zero_bb


def test_already_translated_level_segments_aggregate_by_effective_evidence() -> None:
    first = translate_level_profile_to_mlb(
        _level_profile({"K": 8.0, "BB_HBP": 2.0}, player_id=1),
        _offsets(),
    )
    second = translate_level_profile_to_mlb(
        _level_profile({"K": 2.0, "BB_HBP": 8.0}, player_id=1, level="MLB"),
        _offsets(),
    )
    combined = aggregate_translated_player_profile(pl.concat([first, second], how="vertical_relaxed"))

    assert combined.get_column("effective_core_events").unique().to_list() == [20.0]
    assert combined.get_column("translated_effective_count").sum() == pytest.approx(20.0)
    assert combined.get_column("translated_mlb_rate").sum() == pytest.approx(1.0)


def test_baseline0_prior_is_leave_one_out_and_falls_back_only_when_needed() -> None:
    translated = _translated_players(
        {
            1: {"K": 90.0, "BB_HBP": 10.0},
            2: {"K": 20.0, "BB_HBP": 80.0},
            3: {"K": 30.0, "BB_HBP": 70.0},
        }
    )
    context = pl.DataFrame(
        {
            "player_id": [1, 2, 3],
            "age_years": [22.2, 22.7, 22.9],
            "as_of_level_group": ["AAA", "AAA", "AAA"],
            "as_of_environment_ambiguous": [False, False, False],
        }
    )
    prior = fit_leave_one_out_age_level_prior(
        translated,
        context,
        age_band_width_years=2.0,
        min_age_level_peers=2,
    )

    p1_k = prior.filter((pl.col("player_id") == 1) & (pl.col("core_bin") == "K")).to_dicts()[0]
    # Player 1's extreme K rate is excluded: only players 2 and 3 enter this pool.
    denominator = 200.0 + 0.5 * len(ALL_CORE_BINS)
    assert p1_k["prior_probability"] == pytest.approx((20.0 + 30.0 + 0.5) / denominator)
    assert p1_k["prior_peer_source"] == "age_level"
    assert p1_k["prior_peer_player_count"] == 2
    assert p1_k["baseline0_method"] == BASELINE0_METHOD


def test_baseline1_shrinks_player_evidence_toward_baseline0_prior() -> None:
    translated = _translated_players(
        {
            1: {"K": 90.0, "BB_HBP": 10.0},
            2: {"K": 20.0, "BB_HBP": 80.0},
            3: {"K": 30.0, "BB_HBP": 70.0},
        }
    )
    context = pl.DataFrame(
        {
            "player_id": [1, 2, 3],
            "age_years": [22.2, 22.7, 22.9],
            "as_of_level_group": ["AAA", "AAA", "AAA"],
            "as_of_environment_ambiguous": [False, False, False],
        }
    )
    prior = fit_leave_one_out_age_level_prior(
        translated,
        context,
        min_age_level_peers=2,
    )
    result = build_baseline_profiles(
        translated,
        prior,
        prior_strength_core_events=100.0,
    )

    row = result.profile.filter(
        (pl.col("player_id") == 1) & (pl.col("core_bin") == "K")
    ).to_dicts()[0]
    player_rate = 0.90
    assert row["baseline0_latent_probability"] < row["baseline1_latent_probability"] < player_rate
    assert row["baseline1_method"] == BASELINE1_METHOD

    sums = result.profile.group_by("player_id").agg(
        pl.col("baseline0_latent_probability").sum().alias("b0"),
        pl.col("baseline1_latent_probability").sum().alias("b1"),
    )
    assert sums.filter((pl.col("b0") - 1.0).abs() > 1e-9).is_empty()
    assert sums.filter((pl.col("b1") - 1.0).abs() > 1e-9).is_empty()
