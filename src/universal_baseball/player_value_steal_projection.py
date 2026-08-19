"""Leakage-safe diagnostic core for Player Value v1 steal projection selection."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Literal


EPSILON = 1e-9
DEVELOPMENT_YEARS = (2022, 2023)
CONFIRMATION_YEAR = 2024
MEANINGFUL_TIER_EXPOSURE_SHARE = 0.05
CATASTROPHIC_SCORE_RATIO = 1.10
TIE_DECIMALS = 8

Channel = Literal["attempt", "success"]


@dataclass(frozen=True, slots=True)
class PlayerSeasonStealSummary:
    player_id: int
    season: int
    tier: str
    opportunity_proxy: float
    attempts: float
    successes: float
    expected_attempts: float
    expected_successes: float

    def __post_init__(self) -> None:
        numeric = {
            "opportunity_proxy": self.opportunity_proxy,
            "attempts": self.attempts,
            "successes": self.successes,
            "expected_attempts": self.expected_attempts,
            "expected_successes": self.expected_successes,
        }
        if self.player_id <= 0:
            raise ValueError("player_id must be positive")
        if not self.tier:
            raise ValueError("tier must be nonempty")
        for name, value in numeric.items():
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"{name} must be finite and nonnegative")
        if self.successes > self.attempts + EPSILON:
            raise ValueError("successes cannot exceed attempts")
        if self.expected_successes > self.attempts + EPSILON:
            raise ValueError("expected_successes cannot exceed observed attempts")


@dataclass(frozen=True, slots=True)
class StealCandidate:
    candidate_id: str
    history_family: Literal["B0", "B1", "B2"]
    prior_strength: float | None


@dataclass(frozen=True, slots=True)
class ScoreCell:
    score: float
    exposure: float
    observation_count: int
    secondary_score: float | None = None


@dataclass(frozen=True, slots=True)
class CandidateScore:
    candidate_id: str
    channel: Channel
    yearly: dict[int, ScoreCell]
    tier_yearly: dict[int, dict[str, ScoreCell]]
    equal_year_mean_primary: float


@dataclass(frozen=True, slots=True)
class SelectionResult:
    channel: Channel
    selected_candidate_id: str
    development_player_specific_winner: str | None
    development_baseline_score: float
    development_selected_score: float
    development_passed: bool
    catastrophic_development_tiers: tuple[str, ...]


def steal_candidates() -> tuple[StealCandidate, ...]:
    candidates = [StealCandidate("B0_neutral", "B0", None)]
    for family in ("B1", "B2"):
        for strength in (5.0, 15.0, 45.0):
            candidates.append(
                StealCandidate(
                    candidate_id=f"{family}_k{int(strength)}",
                    history_family=family,
                    prior_strength=strength,
                )
            )
    return tuple(candidates)


def _history_weight(candidate: StealCandidate, target_season: int, evidence_season: int) -> float:
    years_back = target_season - evidence_season
    if candidate.history_family == "B0":
        return 0.0
    if candidate.history_family == "B1":
        return 1.0 if years_back == 1 else 0.0
    if candidate.history_family == "B2":
        return {1: 1.0, 2: 0.5, 3: 0.25}.get(years_back, 0.0)
    raise ValueError(f"unsupported history family: {candidate.history_family}")


def _clip_probability(value: float) -> float:
    return min(1.0 - EPSILON, max(EPSILON, value))


def _logit(value: float) -> float:
    p = _clip_probability(value)
    return math.log(p / (1.0 - p))


def _logistic(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def attempt_multiplier(
    target: PlayerSeasonStealSummary,
    history: Iterable[PlayerSeasonStealSummary],
    candidate: StealCandidate,
) -> float:
    if candidate.history_family == "B0":
        return 1.0
    if candidate.prior_strength is None or candidate.prior_strength <= 0:
        raise ValueError("player-specific attempt candidate requires positive prior strength")

    observed = 0.0
    expected = 0.0
    for row in history:
        if row.player_id != target.player_id:
            continue
        weight = _history_weight(candidate, target.season, row.season)
        if weight <= 0:
            continue
        observed += weight * row.attempts
        expected += weight * row.expected_attempts
    if expected <= 0:
        return 1.0
    k = candidate.prior_strength
    return (k + observed) / (k + expected)


def success_log_odds_residual(
    target: PlayerSeasonStealSummary,
    history: Iterable[PlayerSeasonStealSummary],
    candidate: StealCandidate,
) -> float:
    if candidate.history_family == "B0":
        return 0.0
    if candidate.prior_strength is None or candidate.prior_strength <= 0:
        raise ValueError("player-specific success candidate requires positive prior strength")

    successes = 0.0
    attempts = 0.0
    expected_successes = 0.0
    for row in history:
        if row.player_id != target.player_id:
            continue
        weight = _history_weight(candidate, target.season, row.season)
        if weight <= 0:
            continue
        successes += weight * row.successes
        attempts += weight * row.attempts
        expected_successes += weight * row.expected_successes

    if attempts <= 0:
        return 0.0
    baseline = _clip_probability(expected_successes / attempts)
    k = candidate.prior_strength
    posterior = _clip_probability((k * baseline + successes) / (k + attempts))
    return _logit(posterior) - _logit(baseline)


def predict_attempt_mean(
    target: PlayerSeasonStealSummary,
    history: Iterable[PlayerSeasonStealSummary],
    candidate: StealCandidate,
) -> float:
    if target.expected_attempts <= 0:
        raise ValueError("scoreable attempt target requires positive expected_attempts")
    return target.expected_attempts * attempt_multiplier(target, history, candidate)


def predict_success_probability(
    target: PlayerSeasonStealSummary,
    history: Iterable[PlayerSeasonStealSummary],
    candidate: StealCandidate,
) -> float:
    if target.attempts <= 0:
        raise ValueError("scoreable success target requires positive attempts")
    baseline = _clip_probability(target.expected_successes / target.attempts)
    residual = success_log_odds_residual(target, history, candidate)
    return _clip_probability(_logistic(_logit(baseline) + residual))


def _poisson_nll(observed: float, mean: float) -> float:
    if mean <= 0 or not math.isfinite(mean):
        raise ValueError("Poisson mean must be finite and positive")
    if observed < 0 or not math.isfinite(observed):
        raise ValueError("Poisson observed count must be finite and nonnegative")
    return mean - observed * math.log(mean) + math.lgamma(observed + 1.0)


def _attempt_observation(
    target: PlayerSeasonStealSummary,
    history: list[PlayerSeasonStealSummary],
    candidate: StealCandidate,
) -> tuple[float, float, float]:
    mean = predict_attempt_mean(target, history, candidate)
    nll = _poisson_nll(target.attempts, mean)
    observed_rate = target.attempts / target.opportunity_proxy
    predicted_rate = mean / target.opportunity_proxy
    squared_error = (predicted_rate - observed_rate) ** 2
    return nll, target.opportunity_proxy, squared_error


def _success_observation(
    target: PlayerSeasonStealSummary,
    history: list[PlayerSeasonStealSummary],
    candidate: StealCandidate,
) -> tuple[float, float, float]:
    probability = predict_success_probability(target, history, candidate)
    failures = target.attempts - target.successes
    nll = -(
        target.successes * math.log(probability)
        + failures * math.log(1.0 - probability)
    )
    brier_total = target.successes * (1.0 - probability) ** 2 + failures * probability**2
    return nll, target.attempts, brier_total


def score_candidate(
    rows: Iterable[PlayerSeasonStealSummary],
    candidate: StealCandidate,
    *,
    channel: Channel,
    target_years: Iterable[int],
) -> CandidateScore:
    data = list(rows)
    years = tuple(int(year) for year in target_years)
    yearly: dict[int, ScoreCell] = {}
    tier_yearly: dict[int, dict[str, ScoreCell]] = {}

    for year in years:
        totals = {"loss": 0.0, "exposure": 0.0, "secondary": 0.0, "count": 0}
        tier_totals: dict[str, dict[str, float]] = {}
        for target in data:
            if target.season != year:
                continue
            if channel == "attempt":
                if target.opportunity_proxy <= 0 or target.expected_attempts <= 0:
                    continue
                loss, exposure, secondary = _attempt_observation(target, data, candidate)
            elif channel == "success":
                if target.attempts <= 0:
                    continue
                loss, exposure, secondary = _success_observation(target, data, candidate)
            else:
                raise ValueError(f"unsupported channel: {channel}")

            totals["loss"] += loss
            totals["exposure"] += exposure
            totals["secondary"] += secondary
            totals["count"] += 1
            bucket = tier_totals.setdefault(
                target.tier,
                {"loss": 0.0, "exposure": 0.0, "secondary": 0.0, "count": 0.0},
            )
            bucket["loss"] += loss
            bucket["exposure"] += exposure
            bucket["secondary"] += secondary
            bucket["count"] += 1.0

        if totals["exposure"] <= 0:
            raise ValueError(f"no scoreable {channel} exposure for target year {year}")
        yearly[year] = ScoreCell(
            score=totals["loss"] / totals["exposure"],
            exposure=totals["exposure"],
            observation_count=int(totals["count"]),
            secondary_score=totals["secondary"] / totals["exposure"],
        )
        tier_yearly[year] = {
            tier: ScoreCell(
                score=values["loss"] / values["exposure"],
                exposure=values["exposure"],
                observation_count=int(values["count"]),
                secondary_score=values["secondary"] / values["exposure"],
            )
            for tier, values in sorted(tier_totals.items())
            if values["exposure"] > 0
        }

    return CandidateScore(
        candidate_id=candidate.candidate_id,
        channel=channel,
        yearly=yearly,
        tier_yearly=tier_yearly,
        equal_year_mean_primary=sum(yearly[year].score for year in years) / len(years),
    )


def score_all_candidates(
    rows: Iterable[PlayerSeasonStealSummary],
    *,
    channel: Channel,
    target_years: Iterable[int],
) -> tuple[CandidateScore, ...]:
    data = list(rows)
    return tuple(
        score_candidate(data, candidate, channel=channel, target_years=target_years)
        for candidate in steal_candidates()
    )


def catastrophic_tier_reversals(
    candidate: CandidateScore,
    baseline: CandidateScore,
    *,
    target_years: Iterable[int],
) -> tuple[str, ...]:
    problems: list[str] = []
    for year in target_years:
        baseline_year = baseline.yearly[int(year)]
        for tier, cell in candidate.tier_yearly[int(year)].items():
            if cell.exposure < MEANINGFUL_TIER_EXPOSURE_SHARE * baseline_year.exposure:
                continue
            baseline_cell = baseline.tier_yearly[int(year)].get(tier)
            if baseline_cell is None or baseline_cell.score <= 0:
                continue
            if cell.score >= CATASTROPHIC_SCORE_RATIO * baseline_cell.score:
                problems.append(f"{year}:{tier}")
    return tuple(sorted(problems))


def select_development_candidate(
    scores: Iterable[CandidateScore],
    *,
    channel: Channel,
) -> SelectionResult:
    score_list = list(scores)
    by_id = {score.candidate_id: score for score in score_list}
    baseline = by_id.get("B0_neutral")
    if baseline is None:
        raise ValueError("B0_neutral score is required")

    eligible: list[CandidateScore] = []
    reversals_by_id: dict[str, tuple[str, ...]] = {}
    for score in score_list:
        if score.candidate_id == "B0_neutral":
            continue
        reversals = catastrophic_tier_reversals(
            score, baseline, target_years=DEVELOPMENT_YEARS
        )
        reversals_by_id[score.candidate_id] = reversals
        if not reversals:
            eligible.append(score)

    if not eligible:
        return SelectionResult(
            channel=channel,
            selected_candidate_id="B0_neutral",
            development_player_specific_winner=None,
            development_baseline_score=baseline.equal_year_mean_primary,
            development_selected_score=baseline.equal_year_mean_primary,
            development_passed=False,
            catastrophic_development_tiers=tuple(),
        )

    candidate_specs = {candidate.candidate_id: candidate for candidate in steal_candidates()}

    def selection_key(score: CandidateScore) -> tuple[float, int, float]:
        spec = candidate_specs[score.candidate_id]
        family_priority = 0 if spec.history_family == "B1" else 1
        strength_priority = -(spec.prior_strength or 0.0)
        return (
            round(score.equal_year_mean_primary, TIE_DECIMALS),
            family_priority,
            strength_priority,
        )

    winner = min(eligible, key=selection_key)
    passed = winner.equal_year_mean_primary < baseline.equal_year_mean_primary
    selected_id = winner.candidate_id if passed else "B0_neutral"
    selected_score = winner.equal_year_mean_primary if passed else baseline.equal_year_mean_primary
    return SelectionResult(
        channel=channel,
        selected_candidate_id=selected_id,
        development_player_specific_winner=winner.candidate_id,
        development_baseline_score=baseline.equal_year_mean_primary,
        development_selected_score=selected_score,
        development_passed=passed,
        catastrophic_development_tiers=reversals_by_id.get(winner.candidate_id, tuple()),
    )


def confirmation_passes(
    selected_candidate_id: str,
    scores_2024: Iterable[CandidateScore],
) -> tuple[bool, tuple[str, ...]]:
    if selected_candidate_id == "B0_neutral":
        return True, tuple()
    by_id = {score.candidate_id: score for score in scores_2024}
    baseline = by_id["B0_neutral"]
    selected = by_id[selected_candidate_id]
    reversals = catastrophic_tier_reversals(
        selected, baseline, target_years=(CONFIRMATION_YEAR,)
    )
    passes = (
        selected.equal_year_mean_primary < baseline.equal_year_mean_primary
        and not reversals
    )
    return passes, reversals
