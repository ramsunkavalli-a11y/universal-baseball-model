from __future__ import annotations

from datetime import date

import polars as pl
import pytest

from universal_baseball.current_talent_baselines import (
    build_baseline_profiles,
    build_translated_player_evidence,
    fit_leave_one_out_age_level_prior,
)
from universal_baseball.current_talent_evidence import EvidenceWindow
from universal_baseball.performance_season import ALL_CORE_BINS
from universal_baseball.projection_current_talent import (
    FROZEN_B0_MIN_AGE_LEVEL_PEERS,
    build_projection_frozen_b2_snapshot_from_offsets,
)
from universal_baseball.projection_validation import PROJECTION_V1_DEVELOPMENT_FOLDS


def _evidence(rows: list[tuple[int, date, str]]) -> tuple[pl.DataFrame, pl.DataFrame]:
    summaries: list[dict[str, object]] = []
    profiles: list[dict[str, object]] = []
    for game_pk, (player_id, game_date, core_bin) in enumerate(rows, start=1):
        summaries.append(
            {
                "season": game_date.year,
                "game_date": game_date.isoformat(),
                "game_pk": game_pk,
                "league_id": 117,
                "player_id": player_id,
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
        profiles.append(
            {
                "season": game_date.year,
                "game_date": game_date.isoformat(),
                "game_pk": game_pk,
                "league_id": 117,
                "player_id": player_id,
                "level_group": "AAA",
                "core_bin": core_bin,
                "occurrence_count": 1,
            }
        )
    return pl.DataFrame(summaries), pl.DataFrame(profiles)


def _context(player_ids: list[int]) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "player_id": player_ids,
            "age_years": [22.0 + (index % 2) * 0.1 for index in range(len(player_ids))],
            "as_of_level_group": ["AAA"] * len(player_ids),
            "as_of_environment_ambiguous": [False] * len(player_ids),
            "prior_mlb_evidence": [False] * len(player_ids),
        }
    )


def _zero_offsets() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "level_group": level,
                "core_bin": core_bin,
                "clr_environment_effect": 0.0,
            }
            for level in ("AAA", "MLB")
            for core_bin in ALL_CORE_BINS
        ]
    )


def test_projection_2021_snapshot_reproduces_current_season_b2_collapse() -> None:
    fold = PROJECTION_V1_DEVELOPMENT_FOLDS[0]
    player_ids = list(range(1, FROZEN_B0_MIN_AGE_LEVEL_PEERS + 2))
    rows = [
        (player_id, date(2021, 9, 1), "K" if player_id % 2 else "BB_HBP")
        for player_id in player_ids
    ]
    current_summary, current_profile = _evidence(rows)

    snapshot = build_projection_frozen_b2_snapshot_from_offsets(
        current_summary,
        current_profile,
        current_summary,
        current_profile,
        _context(player_ids),
        _zero_offsets(),
        fold=fold,
    )

    translated = build_translated_player_evidence(
        current_summary,
        current_profile,
        _zero_offsets(),
        cutoff=fold.snapshot_date,
        window=EvidenceWindow(
            label="comparison",
            lookback_days=None,
            half_life_days=180.0,
        ),
    )
    prior = fit_leave_one_out_age_level_prior(
        translated,
        _context(player_ids),
        min_age_level_peers=FROZEN_B0_MIN_AGE_LEVEL_PEERS,
    )
    expected = build_baseline_profiles(
        translated,
        prior,
        prior_strength_core_events=100.0,
    ).profile.select(
        "player_id",
        "core_bin",
        pl.col("baseline1_latent_probability").alias("expected_probability"),
    )
    observed = snapshot.profile.select(
        "player_id",
        "core_bin",
        "baseline2_latent_probability",
    ).join(expected, on=["player_id", "core_bin"])

    assert observed.height == len(player_ids) * len(ALL_CORE_BINS)
    assert observed.select(
        (pl.col("baseline2_latent_probability") - pl.col("expected_probability"))
        .abs()
        .max()
    ).item() == pytest.approx(0.0, abs=1e-12)
    assert snapshot.player_context.get_column("prior_season_effective_core_events").abs().max() == pytest.approx(0.0, abs=1e-12)
    assert snapshot.metrics["future_outcomes_scored"] is False
    assert snapshot.metrics["confirmation_accessed"] is False


def test_projection_2022_snapshot_adds_prior_certified_player_history_only() -> None:
    fold = PROJECTION_V1_DEVELOPMENT_FOLDS[1]
    player_ids = list(range(1, FROZEN_B0_MIN_AGE_LEVEL_PEERS + 2))
    current_rows = [
        (player_id, date(2022, 9, 1), "K" if player_id % 2 else "BB_HBP")
        for player_id in player_ids
    ]
    prior_rows = [(1, date(2021, 9, 1), "BB_HBP")]
    current_summary, current_profile = _evidence(current_rows)
    prior_summary, prior_profile = _evidence(prior_rows)
    history_summary = pl.concat([prior_summary, current_summary], how="vertical_relaxed")
    history_profile = pl.concat([prior_profile, current_profile], how="vertical_relaxed")

    snapshot = build_projection_frozen_b2_snapshot_from_offsets(
        history_summary,
        history_profile,
        current_summary,
        current_profile,
        _context(player_ids),
        _zero_offsets(),
        fold=fold,
    )

    player1 = snapshot.player_context.filter(pl.col("player_id") == 1).row(0, named=True)
    player2 = snapshot.player_context.filter(pl.col("player_id") == 2).row(0, named=True)
    assert float(player1["prior_season_effective_core_events"]) > 0.0
    assert float(player2["prior_season_effective_core_events"]) == pytest.approx(0.0, abs=1e-12)


def test_projection_b2_snapshot_rejects_post_snapshot_history() -> None:
    fold = PROJECTION_V1_DEVELOPMENT_FOLDS[0]
    player_ids = list(range(1, FROZEN_B0_MIN_AGE_LEVEL_PEERS + 2))
    current_summary, current_profile = _evidence(
        [(player_id, date(2021, 9, 1), "K") for player_id in player_ids]
    )
    late_summary, late_profile = _evidence([(1, date(2021, 10, 16), "K")])

    with pytest.raises(ValueError, match="at or after Projection snapshot"):
        build_projection_frozen_b2_snapshot_from_offsets(
            pl.concat([current_summary, late_summary], how="vertical_relaxed"),
            pl.concat([current_profile, late_profile], how="vertical_relaxed"),
            current_summary,
            current_profile,
            _context(player_ids),
            _zero_offsets(),
            fold=fold,
        )
