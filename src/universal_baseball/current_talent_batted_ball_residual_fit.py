"""Training contract and deterministic fit for the first richer Current Talent tier.

The richer batted-ball challenger is defined in latent MLB-scale space, but its
training likelihood must respect the actual future environment in which contact
outcomes were observed. This module therefore builds a fail-closed training table
that combines:

- frozen Baseline 2 latent conditional-contact probabilities;
- training-only standardized EV / sweet-spot features;
- fitted training-only target-level CLR environment effects; and
- future contact-bin counts from the existing 90-day Current Talent target.

Only the ten contact bins are fit. BB/HBP and K never enter the residual feature
relationship. The optimizer is dependency-light and deterministic: a convex
multinomial offset model with one fixed shared L2 penalty and no held-out penalty
search.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import exp, isfinite, log
from typing import Any

import polars as pl

from universal_baseball.current_talent_validation_dataset import TARGET_ENVIRONMENT_KEY
from universal_baseball.performance_season import ALL_CORE_BINS, CONTACT_CORE_BINS


FIXED_RESIDUAL_L2_PENALTY = 0.01
DEFAULT_MAX_ITERATIONS = 2000
DEFAULT_GRADIENT_TOLERANCE = 1e-8
DEFAULT_OBJECTIVE_TOLERANCE = 1e-12
MIN_BACKTRACK_STEP = 1e-12
ARMIJO_FRACTION = 1e-4

RESIDUAL_TRAINING_ENVIRONMENT_KEY = ("as_of_date", *TARGET_ENVIRONMENT_KEY)
RESIDUAL_TRAINING_SCHEMA: dict[str, pl.DataType] = {
    "as_of_date": pl.Date,
    "player_id": pl.Int64,
    "target_season": pl.Int64,
    "target_league_id": pl.Int64,
    "target_level_group": pl.String,
    "core_bin": pl.String,
    "z_mean_exit_velocity": pl.Float64,
    "z_sweet_spot_share": pl.Float64,
    "baseline2_latent_conditional_contact_probability": pl.Float64,
    "clr_environment_effect": pl.Float64,
    "baseline2_target_conditional_contact_probability": pl.Float64,
    "future_contact_occurrence_count": pl.Int64,
    "future_contact_events": pl.Int64,
    "future_core_events": pl.Int64,
}


@dataclass(frozen=True, slots=True)
class BattedBallResidualFit:
    coefficients: pl.DataFrame
    metrics: dict[str, Any]


def _require_columns(frame: pl.DataFrame, required: set[str], label: str) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{label} missing fields: {missing}")


def _softmax(values: list[float]) -> list[float]:
    maximum = max(values)
    numerators = [exp(value - maximum) for value in values]
    denominator = sum(numerators)
    if denominator <= 0 or not isfinite(denominator):
        raise ValueError("residual softmax denominator must be finite and positive")
    return [value / denominator for value in numerators]


def _validate_cutoff(frame: pl.DataFrame, *, expected_as_of_date: date, label: str) -> pl.DataFrame:
    _require_columns(frame, {"as_of_date"}, label)
    dated = frame.with_columns(pl.col("as_of_date").cast(pl.Date, strict=False).alias("as_of_date"))
    if dated.filter(pl.col("as_of_date").is_null()).height:
        raise ValueError(f"{label} contains an invalid as_of_date")
    mismatched = dated.filter(pl.col("as_of_date") != pl.lit(expected_as_of_date))
    if not mismatched.is_empty():
        raise ValueError(f"{label} cutoff does not match expected as_of_date")
    return dated


def build_batted_ball_residual_training_table(
    baseline2_profile: pl.DataFrame,
    standardized_features: pl.DataFrame,
    target_summary: pl.DataFrame,
    target_profile: pl.DataFrame,
    offsets: pl.DataFrame,
    *,
    expected_as_of_date: date,
    probability_tolerance: float = 1e-9,
) -> pl.DataFrame:
    """Build one cutoff's contact-residual training rows without future leakage.

    The table is one row per ``as_of + target environment + contact bin`` for
    richer-eligible players. Baseline 2 is first conditioned on a core contact in
    latent MLB-scale space. The realized target-level environment effect is then
    added in CLR/logit space and renormalized across the ten contact bins. Future
    BB/HBP and K counts are intentionally excluded from the fitted relationship.
    """

    if probability_tolerance < 0:
        raise ValueError("probability tolerance must be nonnegative")

    _require_columns(
        baseline2_profile,
        {"player_id", "core_bin", "baseline2_latent_probability"},
        "Baseline 2 profile",
    )
    _require_columns(
        standardized_features,
        {
            "as_of_date",
            "player_id",
            "tracked_bbe_eligible",
            "z_mean_exit_velocity",
            "z_sweet_spot_share",
        },
        "standardized tracked features",
    )
    _require_columns(
        target_summary,
        {"as_of_date", *TARGET_ENVIRONMENT_KEY, "future_core_events"},
        "future target summary",
    )
    _require_columns(
        target_profile,
        {"as_of_date", *TARGET_ENVIRONMENT_KEY, "core_bin", "future_occurrence_count"},
        "future target profile",
    )
    _require_columns(
        offsets,
        {"level_group", "core_bin", "clr_environment_effect"},
        "translation offsets",
    )

    features = _validate_cutoff(
        standardized_features,
        expected_as_of_date=expected_as_of_date,
        label="standardized tracked features",
    )
    summary = _validate_cutoff(
        target_summary,
        expected_as_of_date=expected_as_of_date,
        label="future target summary",
    )
    profile = _validate_cutoff(
        target_profile,
        expected_as_of_date=expected_as_of_date,
        label="future target profile",
    )

    duplicate_b2 = baseline2_profile.group_by(["player_id", "core_bin"]).len().filter(
        pl.col("len") != 1
    )
    if not duplicate_b2.is_empty():
        raise ValueError("Baseline 2 profile violates player_id + core_bin grain")
    duplicate_features = features.group_by(["as_of_date", "player_id"]).len().filter(
        pl.col("len") != 1
    )
    if not duplicate_features.is_empty():
        raise ValueError("standardized tracked features violate as_of_date + player_id grain")
    duplicate_summary = summary.group_by(list(RESIDUAL_TRAINING_ENVIRONMENT_KEY)).len().filter(
        pl.col("len") != 1
    )
    if not duplicate_summary.is_empty():
        raise ValueError("future target summary violates as_of + target-environment grain")
    duplicate_profile = profile.group_by(
        [*RESIDUAL_TRAINING_ENVIRONMENT_KEY, "core_bin"]
    ).len().filter(pl.col("len") != 1)
    if not duplicate_profile.is_empty():
        raise ValueError("future target profile violates as_of + target-environment + core-bin grain")
    duplicate_offsets = offsets.group_by(["level_group", "core_bin"]).len().filter(
        pl.col("len") != 1
    )
    if not duplicate_offsets.is_empty():
        raise ValueError("translation offsets violate level_group + core_bin grain")

    eligible_features = features.filter(
        pl.col("tracked_bbe_eligible")
        & pl.col("z_mean_exit_velocity").is_not_null()
        & pl.col("z_sweet_spot_share").is_not_null()
    )
    if eligible_features.is_empty():
        return pl.DataFrame(schema=RESIDUAL_TRAINING_SCHEMA)

    feature_lookup = {
        int(row["player_id"]): (
            float(row["z_mean_exit_velocity"]),
            float(row["z_sweet_spot_share"]),
        )
        for row in eligible_features.iter_rows(named=True)
    }

    b2_lookup: dict[int, dict[str, float]] = {}
    for row in baseline2_profile.iter_rows(named=True):
        player_id = int(row["player_id"])
        core_bin = str(row["core_bin"])
        if core_bin not in ALL_CORE_BINS:
            raise ValueError(f"unsupported Baseline 2 core bin: {core_bin}")
        probability = float(row["baseline2_latent_probability"])
        if probability <= 0 or probability >= 1 or not isfinite(probability):
            raise ValueError("Baseline 2 latent probabilities must lie strictly between zero and one")
        b2_lookup.setdefault(player_id, {})[core_bin] = probability
    for player_id, probabilities in b2_lookup.items():
        if set(probabilities) != set(ALL_CORE_BINS):
            raise ValueError(f"Baseline 2 profile incomplete for player {player_id}")
        if abs(sum(probabilities.values()) - 1.0) > probability_tolerance:
            raise ValueError(f"Baseline 2 profile does not sum to one for player {player_id}")

    offset_lookup: dict[str, dict[str, float]] = {}
    for row in offsets.iter_rows(named=True):
        core_bin = str(row["core_bin"])
        if core_bin not in ALL_CORE_BINS:
            continue
        level = str(row["level_group"])
        offset_lookup.setdefault(level, {})[core_bin] = float(row["clr_environment_effect"])

    count_lookup: dict[tuple[object, ...], dict[str, int]] = {}
    for row in profile.iter_rows(named=True):
        key = tuple(row[column] for column in RESIDUAL_TRAINING_ENVIRONMENT_KEY)
        core_bin = str(row["core_bin"])
        if core_bin not in ALL_CORE_BINS:
            raise ValueError(f"unsupported future target core bin: {core_bin}")
        count_lookup.setdefault(key, {})[core_bin] = int(row["future_occurrence_count"])

    rows: list[dict[str, object]] = []
    for target in summary.filter(pl.col("future_core_events") > 0).iter_rows(named=True):
        player_id = int(target["player_id"])
        if player_id not in feature_lookup or player_id not in b2_lookup:
            continue
        key = tuple(target[column] for column in RESIDUAL_TRAINING_ENVIRONMENT_KEY)
        counts = count_lookup.get(key, {})
        total_profile_count = sum(counts.get(core_bin, 0) for core_bin in ALL_CORE_BINS)
        future_core_events = int(target["future_core_events"])
        if total_profile_count != future_core_events:
            raise ValueError("future target profile counts do not reconcile to future_core_events")

        future_contact_events = sum(counts.get(core_bin, 0) for core_bin in CONTACT_CORE_BINS)
        if future_contact_events <= 0:
            continue

        level = str(target["target_level_group"])
        if level not in offset_lookup:
            raise ValueError(f"no translation offsets for target level {level}")
        if not set(CONTACT_CORE_BINS).issubset(offset_lookup[level]):
            raise ValueError(f"target level {level} lacks complete contact-bin translation offsets")

        probabilities = b2_lookup[player_id]
        contact_mass = sum(probabilities[core_bin] for core_bin in CONTACT_CORE_BINS)
        if contact_mass <= 0:
            raise ValueError("Baseline 2 contact probability mass must be positive")
        latent_conditional = {
            core_bin: probabilities[core_bin] / contact_mass for core_bin in CONTACT_CORE_BINS
        }
        target_logits = [
            log(latent_conditional[core_bin]) + offset_lookup[level][core_bin]
            for core_bin in CONTACT_CORE_BINS
        ]
        target_conditional_values = _softmax(target_logits)
        target_conditional = dict(
            zip(CONTACT_CORE_BINS, target_conditional_values, strict=True)
        )
        z_ev, z_ss = feature_lookup[player_id]

        for core_bin in CONTACT_CORE_BINS:
            rows.append(
                {
                    "as_of_date": expected_as_of_date,
                    "player_id": player_id,
                    "target_season": int(target["target_season"]),
                    "target_league_id": int(target["target_league_id"]),
                    "target_level_group": level,
                    "core_bin": core_bin,
                    "z_mean_exit_velocity": z_ev,
                    "z_sweet_spot_share": z_ss,
                    "baseline2_latent_conditional_contact_probability": latent_conditional[core_bin],
                    "clr_environment_effect": offset_lookup[level][core_bin],
                    "baseline2_target_conditional_contact_probability": target_conditional[core_bin],
                    "future_contact_occurrence_count": counts.get(core_bin, 0),
                    "future_contact_events": future_contact_events,
                    "future_core_events": future_core_events,
                }
            )

    if not rows:
        return pl.DataFrame(schema=RESIDUAL_TRAINING_SCHEMA)
    return (
        pl.DataFrame(rows, schema=RESIDUAL_TRAINING_SCHEMA)
        .sort([*RESIDUAL_TRAINING_ENVIRONMENT_KEY, "core_bin"])
    )


def _training_groups(training_table: pl.DataFrame) -> list[dict[str, object]]:
    _require_columns(training_table, set(RESIDUAL_TRAINING_SCHEMA), "residual training table")
    if training_table.is_empty():
        raise ValueError("residual fitting requires nonempty training data")

    duplicate = training_table.group_by(
        [*RESIDUAL_TRAINING_ENVIRONMENT_KEY, "core_bin"]
    ).len().filter(pl.col("len") != 1)
    if not duplicate.is_empty():
        raise ValueError("residual training table violates environment + core-bin grain")

    groups: list[dict[str, object]] = []
    for key, group in training_table.group_by(
        list(RESIDUAL_TRAINING_ENVIRONMENT_KEY), maintain_order=True
    ):
        bins = {str(value) for value in group.get_column("core_bin").to_list()}
        if bins != set(CONTACT_CORE_BINS):
            raise ValueError("each residual training environment must contain all ten contact bins")

        z_ev_values = {float(value) for value in group.get_column("z_mean_exit_velocity").to_list()}
        z_ss_values = {float(value) for value in group.get_column("z_sweet_spot_share").to_list()}
        contact_events_values = {int(value) for value in group.get_column("future_contact_events").to_list()}
        if len(z_ev_values) != 1 or len(z_ss_values) != 1:
            raise ValueError("standardized features must be constant within a training environment")
        if len(contact_events_values) != 1:
            raise ValueError("future_contact_events must be constant within a training environment")

        row_lookup = {str(row["core_bin"]): row for row in group.iter_rows(named=True)}
        counts = [int(row_lookup[core_bin]["future_contact_occurrence_count"]) for core_bin in CONTACT_CORE_BINS]
        n = next(iter(contact_events_values))
        if n <= 0 or sum(counts) != n:
            raise ValueError("future contact counts do not reconcile to future_contact_events")

        latent = [
            float(row_lookup[core_bin]["baseline2_latent_conditional_contact_probability"])
            for core_bin in CONTACT_CORE_BINS
        ]
        target = [
            float(row_lookup[core_bin]["baseline2_target_conditional_contact_probability"])
            for core_bin in CONTACT_CORE_BINS
        ]
        effects = [float(row_lookup[core_bin]["clr_environment_effect"]) for core_bin in CONTACT_CORE_BINS]
        if any(value <= 0 or value >= 1 for value in latent + target):
            raise ValueError("conditional contact probabilities must lie strictly between zero and one")
        if abs(sum(latent) - 1.0) > 1e-7 or abs(sum(target) - 1.0) > 1e-7:
            raise ValueError("conditional contact probabilities must sum to one")
        recomputed = _softmax([log(latent[index]) + effects[index] for index in range(len(CONTACT_CORE_BINS))])
        if max(abs(recomputed[index] - target[index]) for index in range(len(target))) > 1e-8:
            raise ValueError("stored target conditional probabilities do not match translation offsets")

        groups.append(
            {
                "key": key,
                "z_ev": next(iter(z_ev_values)),
                "z_ss": next(iter(z_ss_values)),
                "latent": latent,
                "effects": effects,
                "counts": counts,
                "n": n,
            }
        )
    return groups


def _objective_and_gradient(
    groups: list[dict[str, object]],
    beta: list[list[float]],
) -> tuple[float, float, list[list[float]]]:
    total_contacts = sum(int(group["n"]) for group in groups)
    if total_contacts <= 0:
        raise ValueError("residual fitting requires positive future contact events")

    negative_log_likelihood = 0.0
    gradient = [[0.0, 0.0] for _ in CONTACT_CORE_BINS]
    for group in groups:
        z_ev = float(group["z_ev"])
        z_ss = float(group["z_ss"])
        latent = list(group["latent"])
        effects = list(group["effects"])
        counts = list(group["counts"])
        n = int(group["n"])
        logits = [
            log(float(latent[index]))
            + float(effects[index])
            + beta[index][0] * z_ev
            + beta[index][1] * z_ss
            for index in range(len(CONTACT_CORE_BINS))
        ]
        probabilities = _softmax(logits)
        for index, probability in enumerate(probabilities):
            count = int(counts[index])
            if count:
                negative_log_likelihood -= count * log(probability)
            residual = n * probability - count
            gradient[index][0] += residual * z_ev
            gradient[index][1] += residual * z_ss

    mean_nll = negative_log_likelihood / total_contacts
    penalty = 0.5 * FIXED_RESIDUAL_L2_PENALTY * sum(
        coefficient * coefficient for pair in beta for coefficient in pair
    )
    for index in range(len(beta)):
        gradient[index][0] = (
            gradient[index][0] / total_contacts
            + FIXED_RESIDUAL_L2_PENALTY * beta[index][0]
        )
        gradient[index][1] = (
            gradient[index][1] / total_contacts
            + FIXED_RESIDUAL_L2_PENALTY * beta[index][1]
        )
    return mean_nll + penalty, mean_nll, gradient


def fit_batted_ball_residual_coefficients(
    training_table: pl.DataFrame,
    *,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    gradient_tolerance: float = DEFAULT_GRADIENT_TOLERANCE,
    objective_tolerance: float = DEFAULT_OBJECTIVE_TOLERANCE,
) -> BattedBallResidualFit:
    """Fit the fixed-penalty multinomial contact residual by batch gradient descent.

    The loss is mean future-contact negative log likelihood plus one shared ridge
    penalty of ``0.01`` across all twenty coefficients. The penalty is fixed by
    protocol and is not searched on development or confirmation outcomes.
    """

    if max_iterations < 1:
        raise ValueError("max_iterations must be positive")
    if gradient_tolerance <= 0 or objective_tolerance <= 0:
        raise ValueError("optimizer tolerances must be positive")

    groups = _training_groups(training_table)
    beta = [[0.0, 0.0] for _ in CONTACT_CORE_BINS]
    objective, mean_nll, gradient = _objective_and_gradient(groups, beta)
    initial_objective = objective
    initial_mean_nll = mean_nll
    converged = False
    iterations = 0

    for iteration in range(1, max_iterations + 1):
        iterations = iteration
        gradient_max_abs = max(abs(value) for pair in gradient for value in pair)
        if gradient_max_abs <= gradient_tolerance:
            converged = True
            break

        gradient_squared_norm = sum(value * value for pair in gradient for value in pair)
        step = 1.0
        accepted = False
        candidate: list[list[float]] = []
        candidate_objective = objective
        candidate_mean_nll = mean_nll
        candidate_gradient = gradient
        while step >= MIN_BACKTRACK_STEP:
            candidate = [
                [
                    beta[index][0] - step * gradient[index][0],
                    beta[index][1] - step * gradient[index][1],
                ]
                for index in range(len(beta))
            ]
            candidate_objective, candidate_mean_nll, candidate_gradient = _objective_and_gradient(
                groups, candidate
            )
            if candidate_objective <= objective - ARMIJO_FRACTION * step * gradient_squared_norm:
                accepted = True
                break
            step *= 0.5
        if not accepted:
            raise ValueError("residual optimizer could not find a descending step")

        improvement = objective - candidate_objective
        beta = candidate
        objective = candidate_objective
        mean_nll = candidate_mean_nll
        gradient = candidate_gradient
        if improvement <= objective_tolerance:
            converged = True
            break

    if not converged:
        raise ValueError("residual optimizer did not converge within max_iterations")

    coefficients = pl.DataFrame(
        [
            {
                "core_bin": core_bin,
                "beta_mean_exit_velocity": beta[index][0],
                "beta_sweet_spot_share": beta[index][1],
            }
            for index, core_bin in enumerate(CONTACT_CORE_BINS)
        ]
    ).sort("core_bin")
    if coefficients.select(
        pl.any_horizontal(
            pl.col("beta_mean_exit_velocity").is_nan(),
            pl.col("beta_sweet_spot_share").is_nan(),
        )
    ).item():
        raise ValueError("residual fit produced non-finite coefficients")

    unique_players = training_table.get_column("player_id").n_unique()
    unique_as_of = training_table.get_column("as_of_date").n_unique()
    total_contacts = sum(int(group["n"]) for group in groups)
    final_gradient_max_abs = max(abs(value) for pair in gradient for value in pair)
    metrics = {
        "training_only_fit": True,
        "model_family": "conditional_contact_multinomial_offset_residual",
        "feature_family": "mean_ev_plus_sweet_spot_share",
        "fixed_l2_penalty": FIXED_RESIDUAL_L2_PENALTY,
        "penalty_search_performed": False,
        "training_snapshot_count": int(unique_as_of),
        "training_player_count": int(unique_players),
        "training_target_environment_count": len(groups),
        "training_future_contact_events": int(total_contacts),
        "initial_mean_contact_log_loss": float(initial_mean_nll),
        "final_mean_contact_log_loss": float(mean_nll),
        "initial_penalized_objective": float(initial_objective),
        "final_penalized_objective": float(objective),
        "iterations": int(iterations),
        "converged": True,
        "final_gradient_max_abs": float(final_gradient_max_abs),
        "bb_hbp_or_k_coefficients_fit": False,
    }
    return BattedBallResidualFit(coefficients=coefficients, metrics=metrics)
