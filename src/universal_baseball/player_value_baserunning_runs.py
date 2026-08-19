"""Frozen Player Value v1 baserunning run conversion."""

from __future__ import annotations

from dataclasses import dataclass
import math


RUN_VALUE_STOLEN_BASE = 0.2
CAUGHT_STEALING_EXTRA_OUT_CONSTANT = 0.075
EPSILON = 1e-12


@dataclass(frozen=True, slots=True)
class BaserunningReference:
    season: int
    plate_appearances: float
    runs: float
    outs: float
    steal_opportunity_proxy: float
    steal_attempts: float
    stolen_bases: float
    advancement_opportunities: float
    runs_per_out: float
    run_value_stolen_base: float
    run_value_caught_stealing: float
    steal_opportunities_per_pa: float
    steal_attempt_rate: float
    steal_success_probability: float
    league_steal_runs_per_opportunity: float
    advancement_opportunities_per_pa: float


@dataclass(frozen=True, slots=True)
class BaserunningProjection:
    projected_mlb_pa: float
    projected_steal_opportunities: float
    projected_steal_attempts: float
    projected_stolen_bases: float
    projected_caught_stealing: float
    projected_steal_success_probability: float
    steal_runs: float
    projected_advancement_opportunities: float
    advancement_runs: float
    gidp_residual_runs: float
    baserunning_runs: float


def _finite_nonnegative(value: float, label: str) -> float:
    numeric = float(value)
    if not math.isfinite(numeric) or numeric < 0:
        raise ValueError(f"{label} must be finite and nonnegative")
    return numeric


def build_baserunning_reference(
    *,
    season: int,
    plate_appearances: float,
    runs: float,
    outs: float,
    steal_opportunity_proxy: float,
    steal_attempts: float,
    stolen_bases: float,
    advancement_opportunities: float,
) -> BaserunningReference:
    pa = _finite_nonnegative(plate_appearances, "plate_appearances")
    run_count = _finite_nonnegative(runs, "runs")
    out_count = _finite_nonnegative(outs, "outs")
    steal_opportunities = _finite_nonnegative(
        steal_opportunity_proxy,
        "steal_opportunity_proxy",
    )
    attempts = _finite_nonnegative(steal_attempts, "steal_attempts")
    successes = _finite_nonnegative(stolen_bases, "stolen_bases")
    advancement = _finite_nonnegative(
        advancement_opportunities,
        "advancement_opportunities",
    )

    if int(season) <= 0:
        raise ValueError("season must be positive")
    if pa <= 0 or out_count <= 0 or steal_opportunities <= 0 or attempts <= 0:
        raise ValueError("reference PA, outs, steal opportunities, and attempts must be positive")
    if attempts > steal_opportunities + EPSILON:
        raise ValueError("steal_attempts cannot exceed steal_opportunity_proxy")
    if successes > attempts + EPSILON:
        raise ValueError("stolen_bases cannot exceed steal_attempts")

    caught_stealing = attempts - successes
    runs_per_out = run_count / out_count
    run_value_caught_stealing = -(
        2.0 * runs_per_out + CAUGHT_STEALING_EXTRA_OUT_CONSTANT
    )
    league_steal_runs_per_opportunity = (
        successes * RUN_VALUE_STOLEN_BASE
        + caught_stealing * run_value_caught_stealing
    ) / steal_opportunities

    return BaserunningReference(
        season=int(season),
        plate_appearances=pa,
        runs=run_count,
        outs=out_count,
        steal_opportunity_proxy=steal_opportunities,
        steal_attempts=attempts,
        stolen_bases=successes,
        advancement_opportunities=advancement,
        runs_per_out=runs_per_out,
        run_value_stolen_base=RUN_VALUE_STOLEN_BASE,
        run_value_caught_stealing=run_value_caught_stealing,
        steal_opportunities_per_pa=steal_opportunities / pa,
        steal_attempt_rate=attempts / steal_opportunities,
        steal_success_probability=successes / attempts,
        league_steal_runs_per_opportunity=league_steal_runs_per_opportunity,
        advancement_opportunities_per_pa=advancement / pa,
    )


def _logit(probability: float) -> float:
    if not math.isfinite(probability) or probability <= 0 or probability >= 1:
        raise ValueError("probability must be finite and strictly between zero and one")
    return math.log(probability / (1.0 - probability))


def _logistic(value: float) -> float:
    if not math.isfinite(value):
        raise ValueError("log-odds value must be finite")
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def project_steal_runs(
    *,
    projected_mlb_pa: float,
    attempt_multiplier: float,
    success_logodds_residual: float,
    reference: BaserunningReference,
) -> tuple[float, float, float, float, float]:
    """Return opportunities, attempts, SB, CS, and centered steal runs."""

    pa = _finite_nonnegative(projected_mlb_pa, "projected_mlb_pa")
    multiplier = _finite_nonnegative(attempt_multiplier, "attempt_multiplier")
    residual = float(success_logodds_residual)
    if not math.isfinite(residual):
        raise ValueError("success_logodds_residual must be finite")

    opportunities = pa * reference.steal_opportunities_per_pa
    attempts = opportunities * reference.steal_attempt_rate * multiplier
    success_probability = _logistic(
        _logit(reference.steal_success_probability) + residual
    )
    stolen_bases = attempts * success_probability
    caught_stealing = attempts - stolen_bases
    steal_runs = (
        stolen_bases * reference.run_value_stolen_base
        + caught_stealing * reference.run_value_caught_stealing
        - opportunities * reference.league_steal_runs_per_opportunity
    )
    return opportunities, attempts, stolen_bases, caught_stealing, steal_runs


def project_advancement_runs(
    *,
    projected_mlb_pa: float,
    advancement_rate: float,
    reference: BaserunningReference,
) -> tuple[float, float]:
    """Return common-reference advancement opportunities and projected runs."""

    pa = _finite_nonnegative(projected_mlb_pa, "projected_mlb_pa")
    rate = float(advancement_rate)
    if not math.isfinite(rate):
        raise ValueError("advancement_rate must be finite")
    opportunities = pa * reference.advancement_opportunities_per_pa
    return opportunities, opportunities * rate


def project_baserunning_runs(
    *,
    projected_mlb_pa: float,
    attempt_multiplier: float,
    success_logodds_residual: float,
    advancement_rate: float,
    reference: BaserunningReference,
) -> BaserunningProjection:
    opportunities, attempts, stolen_bases, caught_stealing, steal_runs = (
        project_steal_runs(
            projected_mlb_pa=projected_mlb_pa,
            attempt_multiplier=attempt_multiplier,
            success_logodds_residual=success_logodds_residual,
            reference=reference,
        )
    )
    advancement_opportunities, advancement_runs = project_advancement_runs(
        projected_mlb_pa=projected_mlb_pa,
        advancement_rate=advancement_rate,
        reference=reference,
    )
    success_probability = (
        stolen_bases / attempts
        if attempts > 0
        else reference.steal_success_probability
    )
    gidp_residual_runs = 0.0
    return BaserunningProjection(
        projected_mlb_pa=float(projected_mlb_pa),
        projected_steal_opportunities=opportunities,
        projected_steal_attempts=attempts,
        projected_stolen_bases=stolen_bases,
        projected_caught_stealing=caught_stealing,
        projected_steal_success_probability=success_probability,
        steal_runs=steal_runs,
        projected_advancement_opportunities=advancement_opportunities,
        advancement_runs=advancement_runs,
        gidp_residual_runs=gidp_residual_runs,
        baserunning_runs=steal_runs + advancement_runs,
    )
