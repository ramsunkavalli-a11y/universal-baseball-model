"""Pre-scoring richer-feature attachment for frozen Current Talent challenger 2.

This module reuses challenger 1's certified tracked-BBE feature construction and
capability provenance.  It adds only the challenger-2 pre-scoring contract:

- fit feature centering/scaling once from eligible 2021-07-15 player features;
- apply those exact moments unchanged to later frozen 2022 snapshots;
- preserve player-level source capability provenance;
- left-join features to the canonical future target without dropping an event;
- mark richer applicability exactly at >=20 observed complete tracked BBE with two
  finite standardized features;
- encode the unavailable richer adjustment as an exact zero fallback.

No richer coefficients, future losses, calibration, promotion rule, or 2023 data
are accessed here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Iterable

import polars as pl

from universal_baseball.current_talent_batted_ball_capability import (
    PLAYER_TRACKING_CAPABILITY_SCHEMA,
    build_player_tracking_capability,
)
from universal_baseball.current_talent_batted_ball_quality import (
    TRACKED_FEATURE_SCHEMA,
    build_batted_ball_quality_features,
)
from universal_baseball.current_talent_batted_ball_reconciliation import (
    RECONCILED_TRACKED_BBE_SCHEMA,
)
from universal_baseball.current_talent_batted_ball_standardization import (
    BattedBallFeatureStandardization,
    fit_batted_ball_feature_standardization,
    standardize_batted_ball_quality_features,
)
from universal_baseball.current_talent_contact_value_evidence import (
    CONTACT_VALUE_FROZEN_CUTOFFS,
    CONTACT_VALUE_TARGET_KEY,
)


CONTACT_VALUE_FEATURE_TRAINING_CUTOFF = date(2021, 7, 15)
CONTACT_VALUE_FEATURE_EVALUATION_CUTOFFS = (
    date(2022, 7, 15),
    date(2022, 8, 1),
    date(2022, 9, 1),
)
CONTACT_VALUE_FEATURE_CUTOFFS = (
    CONTACT_VALUE_FEATURE_TRAINING_CUTOFF,
    *CONTACT_VALUE_FEATURE_EVALUATION_CUTOFFS,
)
CONTACT_VALUE_FEATURE_CUTOFF_SET = frozenset(CONTACT_VALUE_FEATURE_CUTOFFS)
CONTACT_VALUE_TRACKING_SOURCE_YEARS = frozenset({2021, 2022})


@dataclass(frozen=True, slots=True)
class ContactValueFeatureSnapshot:
    cutoff_date: date
    raw_features: pl.DataFrame
    standardized_features: pl.DataFrame
    capability: pl.DataFrame
    metrics: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ContactValueFeaturePreparation:
    standardization: BattedBallFeatureStandardization
    snapshots: dict[date, ContactValueFeatureSnapshot]
    metrics: dict[str, Any]


def _validate_tracking(frame: pl.DataFrame, *, expected_years: set[int], label: str) -> None:
    missing = sorted(set(RECONCILED_TRACKED_BBE_SCHEMA) - set(frame.columns))
    if missing:
        raise ValueError(f"{label} missing reconciled tracking fields: {missing}")
    if frame.is_empty():
        raise ValueError(f"{label} must not be empty")
    years = {
        int(value)
        for value in frame.get_column("season").cast(pl.Int64, strict=False).drop_nulls().unique().to_list()
    }
    if years != expected_years:
        raise ValueError(f"{label} season mismatch: observed={sorted(years)}, expected={sorted(expected_years)}")
    if years - set(CONTACT_VALUE_TRACKING_SOURCE_YEARS):
        raise ValueError(f"{label} contains unauthorized tracking years: {sorted(years)}")
    duplicate = (
        frame.group_by(["game_pk", "player_id", "at_bat_number", "pitch_number"])
        .len()
        .filter(pl.col("len") != 1)
    )
    if not duplicate.is_empty():
        raise ValueError(f"{label} violates canonical tracked-BBE pitch grain")


def _feature_snapshot(
    tracking_history: pl.DataFrame,
    *,
    cutoff: date,
    standardization: BattedBallFeatureStandardization,
) -> ContactValueFeatureSnapshot:
    if cutoff not in CONTACT_VALUE_FEATURE_CUTOFF_SET:
        raise ValueError(f"contact-value feature cutoff is not frozen/authorized: {cutoff.isoformat()}")

    raw = build_batted_ball_quality_features(tracking_history, cutoff=cutoff)
    standardized = standardize_batted_ball_quality_features(raw, standardization)
    capability = build_player_tracking_capability(tracking_history, cutoff=cutoff)

    if raw.is_empty():
        raise ValueError(f"contact-value tracking feature snapshot is empty at {cutoff}")
    if standardized.height != raw.height:
        raise ValueError("standardized feature snapshot changed player coverage")
    if capability.height != raw.height:
        raise ValueError("tracking capability snapshot changed observed player coverage")

    grain = ["as_of_date", "player_id"]
    for label, frame in (
        ("raw richer features", raw),
        ("standardized richer features", standardized),
        ("tracking capability", capability),
    ):
        duplicate = frame.group_by(grain).len().filter(pl.col("len") != 1)
        if not duplicate.is_empty():
            raise ValueError(f"{label} violates as_of_date + player_id grain")
        dates = set(frame.get_column("as_of_date").unique().to_list())
        if dates != {cutoff}:
            raise ValueError(f"{label} carries wrong as-of date at {cutoff}")

    joined = raw.select("as_of_date", "player_id", "raw_complete_tracked_bbe").join(
        capability.select("as_of_date", "player_id", "observed_model_bbe"),
        on=["as_of_date", "player_id"],
        how="inner",
        validate="1:1",
    )
    if joined.height != raw.height:
        raise ValueError("tracking capability lost observed feature players")
    if joined.filter(
        pl.col("raw_complete_tracked_bbe") != pl.col("observed_model_bbe")
    ).height:
        raise ValueError("tracking feature count disagrees with capability observed BBE count")

    eligible = standardized.filter(
        pl.col("tracked_bbe_eligible")
        & pl.col("z_mean_exit_velocity").is_not_null()
        & pl.col("z_mean_exit_velocity").is_finite()
        & pl.col("z_sweet_spot_share").is_not_null()
        & pl.col("z_sweet_spot_share").is_finite()
    )
    metrics: dict[str, Any] = {
        "cutoff_date": cutoff.isoformat(),
        "observed_tracking_player_count": int(raw.height),
        "richer_eligible_player_count": int(eligible.height),
        "ineligible_observed_player_count": int(raw.height - eligible.height),
        "raw_complete_tracked_bbe": int(raw.get_column("raw_complete_tracked_bbe").sum()),
        "capability_observed_model_bbe": int(capability.get_column("observed_model_bbe").sum()),
        "source_family_groups": sorted(
            str(value) for value in capability.get_column("source_family_group").unique().to_list()
        ),
        "source_capability_tier_count": len(
            {
                token
                for value in capability.get_column("observed_source_capability_tiers").to_list()
                for token in str(value).split("|")
                if token
            }
        ),
        "standardization_refit": False,
        "model_scoring": False,
        "richer_coefficients_fitted": False,
        "accessed_2023": False,
    }
    return ContactValueFeatureSnapshot(
        cutoff_date=cutoff,
        raw_features=raw,
        standardized_features=standardized,
        capability=capability,
        metrics=metrics,
    )


def prepare_contact_value_feature_snapshots(
    tracking_2021: pl.DataFrame,
    tracking_2022: pl.DataFrame,
) -> ContactValueFeaturePreparation:
    """Build the four frozen feature snapshots using one 2021 training fit."""

    _validate_tracking(tracking_2021, expected_years={2021}, label="2021 tracking")
    _validate_tracking(tracking_2022, expected_years={2022}, label="2022 tracking")

    training_raw = build_batted_ball_quality_features(
        tracking_2021,
        cutoff=CONTACT_VALUE_FEATURE_TRAINING_CUTOFF,
    )
    standardization = fit_batted_ball_feature_standardization(training_raw)

    # The training snapshot is rebuilt through the same path as evaluation after
    # fitting its moments, while 2022 snapshots see combined 2021+2022 history.
    history = pl.concat([tracking_2021, tracking_2022], how="vertical_relaxed").sort(
        ["game_date", "game_pk", "player_id", "at_bat_number", "pitch_number"]
    )
    snapshots: dict[date, ContactValueFeatureSnapshot] = {}
    snapshots[CONTACT_VALUE_FEATURE_TRAINING_CUTOFF] = _feature_snapshot(
        tracking_2021,
        cutoff=CONTACT_VALUE_FEATURE_TRAINING_CUTOFF,
        standardization=standardization,
    )
    for cutoff in CONTACT_VALUE_FEATURE_EVALUATION_CUTOFFS:
        snapshots[cutoff] = _feature_snapshot(
            history,
            cutoff=cutoff,
            standardization=standardization,
        )

    training_eligible = snapshots[CONTACT_VALUE_FEATURE_TRAINING_CUTOFF].standardized_features.filter(
        pl.col("tracked_bbe_eligible")
        & pl.col("z_mean_exit_velocity").is_not_null()
        & pl.col("z_sweet_spot_share").is_not_null()
    )
    if training_eligible.height != standardization.fitted_player_count:
        raise ValueError("training standardization player count disagrees with eligible snapshot")

    metrics: dict[str, Any] = {
        "training_cutoff": CONTACT_VALUE_FEATURE_TRAINING_CUTOFF.isoformat(),
        "standardization_fitted_player_count": int(standardization.fitted_player_count),
        "standardization_mean_exit_velocity": float(standardization.mean_exit_velocity),
        "standardization_scale_exit_velocity": float(standardization.scale_exit_velocity),
        "standardization_mean_sweet_spot_share": float(standardization.mean_sweet_spot_share),
        "standardization_scale_sweet_spot_share": float(standardization.scale_sweet_spot_share),
        "snapshot_cutoffs": [cutoff.isoformat() for cutoff in CONTACT_VALUE_FEATURE_CUTOFFS],
        "standardization_fit_source": "eligible_2021_07_15_player_features_only",
        "standardization_reused_unchanged_for_2022": True,
        "model_scoring": False,
        "richer_coefficients_fitted": False,
        "accessed_2023": False,
    }
    return ContactValueFeaturePreparation(
        standardization=standardization,
        snapshots=snapshots,
        metrics=metrics,
    )


def attach_contact_value_features_to_future_contacts(
    future_contacts: pl.DataFrame,
    snapshot: ContactValueFeatureSnapshot,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Attach richer availability/provenance without changing target coverage."""

    required_future = {
        "event_date",
        "player_id",
        "terminal_value",
        "contact_bin",
        "level_group",
        *CONTACT_VALUE_TARGET_KEY,
    }
    missing = sorted(required_future - set(future_contacts.columns))
    if missing:
        raise ValueError(f"future contact-value target missing fields: {missing}")
    if future_contacts.is_empty():
        raise ValueError("future contact-value target must not be empty")

    key_columns = list(CONTACT_VALUE_TARGET_KEY)
    duplicate = future_contacts.group_by(key_columns).len().filter(pl.col("len") != 1)
    if not duplicate.is_empty():
        raise ValueError("future contact-value target violates canonical event key grain")

    features = snapshot.standardized_features.select(
        "as_of_date",
        "player_id",
        "tracked_bbe_eligible",
        "z_mean_exit_velocity",
        "z_sweet_spot_share",
    )
    capability = snapshot.capability.select(*PLAYER_TRACKING_CAPABILITY_SCHEMA)
    feature_capability = features.join(
        capability,
        on=["as_of_date", "player_id"],
        how="inner",
        validate="1:1",
    )
    if feature_capability.height != features.height:
        raise ValueError("feature/capability attachment lost observed tracking players")

    joined = future_contacts.join(
        feature_capability.drop("as_of_date"),
        on="player_id",
        how="left",
        validate="m:1",
    )
    if joined.height != future_contacts.height:
        raise ValueError("richer feature attachment changed future target row coverage")
    if joined.group_by(key_columns).len().filter(pl.col("len") != 1).height:
        raise ValueError("richer feature attachment duplicated future target event keys")

    applies = (
        pl.col("tracked_bbe_eligible").fill_null(False)
        & pl.col("z_mean_exit_velocity").is_not_null()
        & pl.col("z_mean_exit_velocity").is_finite()
        & pl.col("z_sweet_spot_share").is_not_null()
        & pl.col("z_sweet_spot_share").is_finite()
    )
    attached = (
        joined.with_columns(
            pl.col("tracked_bbe_eligible").fill_null(False).alias("tracked_bbe_eligible"),
            pl.col("observed_model_bbe").fill_null(0).cast(pl.Int64).alias("observed_model_bbe"),
            pl.col("observed_tracked_game_count")
            .fill_null(0)
            .cast(pl.Int64)
            .alias("observed_tracked_game_count"),
            pl.col("observed_mlb_bbe").fill_null(0).cast(pl.Int64).alias("observed_mlb_bbe"),
            pl.col("observed_milb_bbe").fill_null(0).cast(pl.Int64).alias("observed_milb_bbe"),
            applies.alias("contact_value_residual_applies"),
        )
        .with_columns(
            pl.when(~pl.col("contact_value_residual_applies"))
            .then(pl.lit(0.0))
            .otherwise(pl.lit(None, dtype=pl.Float64))
            .alias("unavailable_richer_residual_fallback"),
        )
        .sort(["event_date", *key_columns])
    )

    paired = attached.filter(pl.col("contact_value_residual_applies"))
    fallback = attached.filter(~pl.col("contact_value_residual_applies"))
    if fallback.filter(pl.col("unavailable_richer_residual_fallback") != 0.0).height:
        raise ValueError("unavailable richer residual fallback is not exactly zero")
    if paired.filter(pl.col("unavailable_richer_residual_fallback").is_not_null()).height:
        raise ValueError("eligible richer rows must not carry a pre-fit fallback value")

    tier_event_counts: dict[str, int] = {}
    if not paired.is_empty():
        tier_values = paired.get_column("observed_source_capability_tiers").drop_nulls().to_list()
        tiers = sorted(
            {
                token
                for value in tier_values
                for token in str(value).split("|")
                if token
            }
        )
        for tier in tiers:
            tier_event_counts[tier] = int(
                paired.filter(
                    pl.col("observed_source_capability_tiers")
                    .fill_null("")
                    .str.split("|")
                    .list.contains(tier)
                ).height
            )

    metrics: dict[str, Any] = {
        "cutoff_date": snapshot.cutoff_date.isoformat(),
        "future_target_contact_count": int(future_contacts.height),
        "attached_target_contact_count": int(attached.height),
        "paired_richer_target_contact_count": int(paired.height),
        "zero_fallback_target_contact_count": int(fallback.height),
        "paired_player_count": int(paired.get_column("player_id").n_unique()) if not paired.is_empty() else 0,
        "any_observed_milb_paired_contact_count": int(
            paired.filter(pl.col("observed_milb_bbe") > 0).height
        ) if not paired.is_empty() else 0,
        "exact_capability_tier_paired_contact_counts": tier_event_counts,
        "target_key_coverage_unchanged": True,
        "comparator_richer_paired_keys_identical_by_construction": True,
        "zero_fallback_exact": True,
        "model_scoring": False,
        "richer_coefficients_fitted": False,
        "accessed_2023": False,
    }
    return attached, metrics
