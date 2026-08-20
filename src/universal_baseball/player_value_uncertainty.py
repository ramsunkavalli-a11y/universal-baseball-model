"""Deterministic forecast-uncertainty primitives for Player Value v1."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np


UNCERTAINTY_ID = "player_value_v1_forecast_uncertainty_2024"
MASTER_SEED = 20240820
SIMULATION_DRAWS = 20_000
NB2_ALPHA = 0.7461189032566083

GENERAL_RANGE_MSE = {
    "T1": 0.878640460280284,
    "U1": 0.8900360540992999,
    "B0": 0.9304792055721907,
}
CATCHER_MSE = {
    "throwing": {"C2": 0.9385276019479529, "B0": 1.0063647479219435},
    "blocking": {"C2": 0.8506475669670914, "B0": 0.9532962787607702},
    "framing": {"F1": 0.6478744253399015, "F0": 0.9846201792216872},
}


def _finite_positive(value: object, label: str) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be finite and positive") from exc
    if not math.isfinite(numeric) or numeric <= 0.0:
        raise ValueError(f"{label} must be finite and positive")
    return numeric


def recover_untruncated_nb2_mean(
    positive_truncated_mean: object,
    *,
    alpha: object = NB2_ALPHA,
    tolerance: float = 1e-12,
) -> float:
    """Invert E[Y | Y>0] for the NB2 mean used by the frozen hurdle model."""

    target = _finite_positive(positive_truncated_mean, "positive_truncated_mean")
    dispersion = _finite_positive(alpha, "alpha")
    if target <= 1.0:
        raise ValueError("zero-truncated count mean must exceed one")
    size = 1.0 / dispersion

    def truncated_mean(mu: float) -> float:
        probability = size / (size + mu)
        p_zero = probability**size
        return mu / (1.0 - p_zero)

    low = 0.0
    high = target
    for _ in range(200):
        midpoint = (low + high) / 2.0
        if truncated_mean(midpoint) < target:
            low = midpoint
        else:
            high = midpoint
        if high - low <= tolerance * max(1.0, target):
            break
    result = (low + high) / 2.0
    if abs(truncated_mean(result) - target) > 1e-10 * target:
        raise RuntimeError("NB2 truncated-mean inversion did not converge")
    return result


def sample_hurdle_plate_appearances(
    rng: np.random.Generator,
    *,
    draws: int,
    participation_probability: object,
    positive_truncated_mean: object,
    alpha: object = NB2_ALPHA,
) -> np.ndarray:
    """Draw the exact Bernoulli/zero-truncated-NB2 frozen Playing Time model."""

    if draws <= 0:
        raise ValueError("draws must be positive")
    probability = float(participation_probability)
    if not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
        raise ValueError("participation_probability must lie in [0, 1]")
    dispersion = _finite_positive(alpha, "alpha")
    mu = recover_untruncated_nb2_mean(
        positive_truncated_mean, alpha=dispersion
    )
    size = 1.0 / dispersion
    nb_probability = size / (size + mu)
    participates = rng.random(draws) < probability
    result = np.zeros(draws, dtype=np.float64)
    active = int(participates.sum())
    if active == 0:
        return result
    values = rng.negative_binomial(size, nb_probability, size=active)
    zero = values == 0
    while bool(zero.any()):
        values[zero] = rng.negative_binomial(size, nb_probability, size=int(zero.sum()))
        zero = values == 0
    result[participates] = values.astype(np.float64)
    return result


def batting_run_variance(
    sampled_pa: np.ndarray,
    *,
    probabilities: Sequence[object],
    centered_bin_run_values: Sequence[object],
    core_event_rate_per_pa: object,
    posterior_concentration: object,
) -> np.ndarray:
    """Moment-matched Dirichlet-multinomial batting-run variance by PA draw."""

    pa = np.asarray(sampled_pa, dtype=np.float64)
    if pa.ndim != 1 or np.any(~np.isfinite(pa)) or np.any(pa < 0.0):
        raise ValueError("sampled_pa must be a finite nonnegative vector")
    probabilities_array = np.asarray(probabilities, dtype=np.float64)
    values = np.asarray(centered_bin_run_values, dtype=np.float64)
    if probabilities_array.shape != values.shape or probabilities_array.ndim != 1:
        raise ValueError("batting probabilities and values must be aligned vectors")
    if np.any(probabilities_array < 0.0) or abs(float(probabilities_array.sum()) - 1.0) > 1e-9:
        raise ValueError("batting probabilities must form a simplex")
    if np.any(~np.isfinite(values)):
        raise ValueError("centered batting run values must be finite")
    coverage = float(core_event_rate_per_pa)
    if not math.isfinite(coverage) or not 0.0 <= coverage <= 1.0:
        raise ValueError("core_event_rate_per_pa must lie in [0, 1]")
    concentration = _finite_positive(posterior_concentration, "posterior_concentration")

    mean_value = float(probabilities_array @ values)
    second_moment = float(probabilities_array @ np.square(values))
    posterior_mean_variance = max(
        0.0, (second_moment - mean_value * mean_value) / (concentration + 1.0)
    )
    finite_event_variance = max(
        0.0,
        coverage * second_moment
        - coverage * coverage * mean_value * mean_value,
    )
    variance = (
        pa * finite_event_variance
        + np.maximum(0.0, pa * pa - pa)
        * coverage
        * coverage
        * posterior_mean_variance
    )
    return np.maximum(variance, 0.0)


def defense_run_variance_at_expected_pa(
    *,
    final_row: Mapping[str, object],
    catcher_opportunities: Mapping[str, object],
    general_run_rates: Mapping[str, object],
    catcher_run_rates: Mapping[str, object],
) -> float:
    """Convert frozen family residual MSEs to point-exposure run variance."""

    raw_families = final_row.get("defense_families_json")
    if not isinstance(raw_families, str):
        raise ValueError("defense_families_json must be present")
    families = json.loads(raw_families)
    variance = 0.0
    range_families = families.get("range_families")
    if not isinstance(range_families, dict):
        raise ValueError("range_families must be an object")
    for position, family_value in sorted(range_families.items()):
        family = str(family_value)
        if family not in GENERAL_RANGE_MSE:
            raise ValueError(f"unsupported general-range family: {family}")
        opportunity = float(final_row[f"projected_outs_{position}"])
        run_rate = float(general_run_rates[position])
        variance += GENERAL_RANGE_MSE[family] * (opportunity * run_rate) ** 2

    component_specs = (
        ("throwing", "throwing_family", "H1_fixed_50_50_hybrid"),
        ("blocking", "blocking_family", "H1_fixed_50_50_hybrid"),
        ("framing", "framing_family", "B0_raw_persistence"),
    )
    for component, family_key, opportunity_column in component_specs:
        family = str(families[family_key])
        if family not in CATCHER_MSE[component]:
            raise ValueError(f"unsupported catcher {component} family: {family}")
        row = catcher_opportunities.get(component)
        opportunity = float(row[opportunity_column]) if isinstance(row, Mapping) else 0.0
        run_rate = float(catcher_run_rates[component])
        variance += CATCHER_MSE[component][family] * (opportunity * run_rate) ** 2
    if not math.isfinite(variance) or variance < 0.0:
        raise ValueError("defense run variance must be finite and nonnegative")
    return variance


@dataclass(frozen=True, slots=True)
class PlayerUncertaintyResult:
    simulated_mean_war: float
    median_war: float
    war_p025: float
    war_p10: float
    war_p90: float
    war_p975: float
    interval_80_width: float
    interval_95_width: float
    playing_time_variance_share: float
    batting_variance_share: float
    defense_variance_share: float
    total_variance_war2: float


def structural_zero_uncertainty() -> PlayerUncertaintyResult:
    return PlayerUncertaintyResult(*(0.0 for _ in range(12)))


def simulate_player_uncertainty(
    *,
    player_id: int,
    point_war: object,
    point_runs_above_replacement: object,
    expected_pa: object,
    participation_probability: object,
    positive_truncated_mean: object,
    runs_per_win: object,
    batting_probabilities: Sequence[object],
    centered_bin_run_values: Sequence[object],
    core_event_rate_per_pa: object,
    batting_posterior_concentration: object,
    defense_variance_at_expected_pa: object,
    draws: int = SIMULATION_DRAWS,
    master_seed: int = MASTER_SEED,
) -> PlayerUncertaintyResult:
    """Simulate one deterministic player forecast under the frozen contract."""

    if player_id <= 0:
        raise ValueError("player_id must be positive")
    expected = _finite_positive(expected_pa, "expected_pa")
    rpw = _finite_positive(runs_per_win, "runs_per_win")
    point_rar = float(point_runs_above_replacement)
    point = float(point_war)
    defense_variance = float(defense_variance_at_expected_pa)
    if not all(math.isfinite(value) for value in (point_rar, point, defense_variance)):
        raise ValueError("point inputs must be finite")
    if defense_variance < 0.0:
        raise ValueError("defense variance must be nonnegative")
    if abs(point_rar / rpw - point) > 1e-10:
        raise ValueError("point WAR does not reconcile")

    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([master_seed, player_id])))
    sampled_pa = sample_hurdle_plate_appearances(
        rng,
        draws=draws,
        participation_probability=participation_probability,
        positive_truncated_mean=positive_truncated_mean,
    )
    scale = sampled_pa / expected
    exposure_runs = point_rar * scale
    batting_variance = batting_run_variance(
        sampled_pa,
        probabilities=batting_probabilities,
        centered_bin_run_values=centered_bin_run_values,
        core_event_rate_per_pa=core_event_rate_per_pa,
        posterior_concentration=batting_posterior_concentration,
    )
    scaled_defense_variance = defense_variance * np.square(scale)
    batting_noise = rng.normal(0.0, np.sqrt(batting_variance))
    defense_noise = rng.normal(0.0, np.sqrt(scaled_defense_variance))
    war = (exposure_runs + batting_noise + defense_noise) / rpw
    if np.any(~np.isfinite(war)):
        raise RuntimeError("uncertainty simulation produced non-finite WAR")
    quantiles = np.quantile(war, [0.025, 0.10, 0.50, 0.90, 0.975], method="linear")

    component_variances = np.asarray(
        [
            float(np.var(exposure_runs, ddof=0)),
            float(np.mean(batting_variance)),
            float(np.mean(scaled_defense_variance)),
        ],
        dtype=np.float64,
    ) / (rpw * rpw)
    total_variance = float(component_variances.sum())
    shares = (
        component_variances / total_variance
        if total_variance > 0.0
        else np.zeros(3, dtype=np.float64)
    )
    return PlayerUncertaintyResult(
        simulated_mean_war=float(np.mean(war)),
        median_war=float(quantiles[2]),
        war_p025=float(quantiles[0]),
        war_p10=float(quantiles[1]),
        war_p90=float(quantiles[3]),
        war_p975=float(quantiles[4]),
        interval_80_width=float(quantiles[3] - quantiles[1]),
        interval_95_width=float(quantiles[4] - quantiles[0]),
        playing_time_variance_share=float(shares[0]),
        batting_variance_share=float(shares[1]),
        defense_variance_share=float(shares[2]),
        total_variance_war2=total_variance,
    )
