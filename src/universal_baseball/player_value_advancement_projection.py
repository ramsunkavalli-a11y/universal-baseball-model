"""Chronological Player Value v1 non-steal advancement projection selection."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Literal


DEVELOPMENT_YEARS = (2022, 2023)
CONFIRMATION_YEAR = 2024
TIE_DECIMALS = 8
CATASTROPHIC_SCORE_RATIO = 1.10

HistoryFamily = Literal["A0", "A1", "A2"]


@dataclass(frozen=True, slots=True)
class PlayerSeasonAdvancementSummary:
    player_id: int
    season: int
    runs_xb: float
    opportunities_xb: float

    def __post_init__(self) -> None:
        if self.player_id <= 0:
            raise ValueError("player_id must be positive")
        if self.season < 2016:
            raise ValueError("season must be 2016 or later")
        if not math.isfinite(self.runs_xb):
            raise ValueError("runs_xb must be finite")
        if not math.isfinite(self.opportunities_xb) or self.opportunities_xb < 0:
            raise ValueError("opportunities_xb must be finite and nonnegative")


@dataclass(frozen=True, slots=True)
class AdvancementCandidate:
    candidate_id: str
    history_family: HistoryFamily
    prior_strength: float | None


@dataclass(frozen=True, slots=True)
class AdvancementScoreCell:
    score: float
    exposure: float
    observation_count: int
    weighted_mae: float
    player_rmse: float
    correlation: float | None


@dataclass(frozen=True, slots=True)
class AdvancementCandidateScore:
    candidate_id: str
    yearly: dict[int, AdvancementScoreCell]
    equal_year_mean_primary: float


@dataclass(frozen=True, slots=True)
class AdvancementSelectionResult:
    selected_candidate_id: str
    development_player_specific_winner: str | None
    development_baseline_score: float
    development_selected_score: float
    development_passed: bool
    catastrophic_development_years: tuple[int, ...]


def advancement_candidates() -> tuple[AdvancementCandidate, ...]:
    candidates = [AdvancementCandidate("A0_neutral", "A0", None)]
    for family in ("A1", "A2"):
        for strength in (25.0, 75.0, 225.0):
            candidates.append(
                AdvancementCandidate(
                    candidate_id=f"{family}_k{int(strength)}",
                    history_family=family,
                    prior_strength=strength,
                )
            )
    return tuple(candidates)


def _history_weight(
    candidate: AdvancementCandidate,
    target_season: int,
    evidence_season: int,
) -> float:
    years_back = target_season - evidence_season
    if years_back <= 0:
        return 0.0
    if candidate.history_family == "A0":
        return 0.0
    if candidate.history_family == "A1":
        return 1.0 if years_back == 1 else 0.0
    if candidate.history_family == "A2":
        return {1: 1.0, 2: 0.5, 3: 0.25}.get(years_back, 0.0)
    raise ValueError(f"unsupported history family: {candidate.history_family}")


def projected_advancement_rate(
    target: PlayerSeasonAdvancementSummary,
    history: Iterable[PlayerSeasonAdvancementSummary],
    candidate: AdvancementCandidate,
) -> float:
    if candidate.history_family == "A0":
        return 0.0
    if candidate.prior_strength is None or candidate.prior_strength <= 0:
        raise ValueError("player-specific advancement candidate requires positive prior strength")

    weighted_runs = 0.0
    weighted_opportunities = 0.0
    for row in history:
        if row.player_id != target.player_id:
            continue
        weight = _history_weight(candidate, target.season, row.season)
        if weight <= 0:
            continue
        weighted_runs += weight * row.runs_xb
        weighted_opportunities += weight * row.opportunities_xb

    if weighted_opportunities <= 0:
        return 0.0
    return weighted_runs / (candidate.prior_strength + weighted_opportunities)


def _pearson_correlation(observed: list[float], predicted: list[float]) -> float | None:
    if len(observed) < 2 or len(observed) != len(predicted):
        return None
    mean_observed = sum(observed) / len(observed)
    mean_predicted = sum(predicted) / len(predicted)
    centered_observed = [value - mean_observed for value in observed]
    centered_predicted = [value - mean_predicted for value in predicted]
    observed_ss = sum(value * value for value in centered_observed)
    predicted_ss = sum(value * value for value in centered_predicted)
    if observed_ss <= 0 or predicted_ss <= 0:
        return None
    covariance = sum(
        left * right for left, right in zip(centered_observed, centered_predicted, strict=True)
    )
    return covariance / math.sqrt(observed_ss * predicted_ss)


def score_candidate(
    rows: Iterable[PlayerSeasonAdvancementSummary],
    candidate: AdvancementCandidate,
    *,
    target_years: Iterable[int],
) -> AdvancementCandidateScore:
    data = list(rows)
    years = tuple(int(year) for year in target_years)
    if not years:
        raise ValueError("target_years must be nonempty")

    yearly: dict[int, AdvancementScoreCell] = {}
    for year in years:
        weighted_squared_error = 0.0
        weighted_absolute_error = 0.0
        exposure = 0.0
        player_squared_error = 0.0
        observed_rates: list[float] = []
        predicted_rates: list[float] = []

        for target in data:
            if target.season != year or target.opportunities_xb <= 0:
                continue
            observed_rate = target.runs_xb / target.opportunities_xb
            predicted_rate = projected_advancement_rate(target, data, candidate)
            error = observed_rate - predicted_rate
            weighted_squared_error += target.opportunities_xb * error * error
            weighted_absolute_error += target.opportunities_xb * abs(error)
            exposure += target.opportunities_xb
            player_squared_error += error * error
            observed_rates.append(observed_rate)
            predicted_rates.append(predicted_rate)

        count = len(observed_rates)
        if exposure <= 0 or count == 0:
            raise ValueError(f"no scoreable advancement exposure for target year {year}")
        yearly[year] = AdvancementScoreCell(
            score=weighted_squared_error / exposure,
            exposure=exposure,
            observation_count=count,
            weighted_mae=weighted_absolute_error / exposure,
            player_rmse=math.sqrt(player_squared_error / count),
            correlation=_pearson_correlation(observed_rates, predicted_rates),
        )

    return AdvancementCandidateScore(
        candidate_id=candidate.candidate_id,
        yearly=yearly,
        equal_year_mean_primary=sum(yearly[year].score for year in years) / len(years),
    )


def score_all_candidates(
    rows: Iterable[PlayerSeasonAdvancementSummary],
    *,
    target_years: Iterable[int],
) -> tuple[AdvancementCandidateScore, ...]:
    data = list(rows)
    return tuple(
        score_candidate(data, candidate, target_years=target_years)
        for candidate in advancement_candidates()
    )


def catastrophic_year_reversals(
    candidate: AdvancementCandidateScore,
    baseline: AdvancementCandidateScore,
    *,
    target_years: Iterable[int],
) -> tuple[int, ...]:
    problems: list[int] = []
    for year in target_years:
        candidate_cell = candidate.yearly[int(year)]
        baseline_cell = baseline.yearly[int(year)]
        if baseline_cell.score <= 0:
            continue
        if candidate_cell.score >= CATASTROPHIC_SCORE_RATIO * baseline_cell.score:
            problems.append(int(year))
    return tuple(sorted(problems))


def select_development_candidate(
    scores: Iterable[AdvancementCandidateScore],
) -> AdvancementSelectionResult:
    score_list = list(scores)
    by_id = {score.candidate_id: score for score in score_list}
    baseline = by_id.get("A0_neutral")
    if baseline is None:
        raise ValueError("A0_neutral score is required")

    candidate_specs = {
        candidate.candidate_id: candidate for candidate in advancement_candidates()
    }
    eligible: list[AdvancementCandidateScore] = []
    reversals_by_id: dict[str, tuple[int, ...]] = {}
    for score in score_list:
        if score.candidate_id == "A0_neutral":
            continue
        reversals = catastrophic_year_reversals(
            score,
            baseline,
            target_years=DEVELOPMENT_YEARS,
        )
        reversals_by_id[score.candidate_id] = reversals
        if not reversals:
            eligible.append(score)

    if not eligible:
        return AdvancementSelectionResult(
            selected_candidate_id="A0_neutral",
            development_player_specific_winner=None,
            development_baseline_score=baseline.equal_year_mean_primary,
            development_selected_score=baseline.equal_year_mean_primary,
            development_passed=False,
            catastrophic_development_years=tuple(),
        )

    def selection_key(score: AdvancementCandidateScore) -> tuple[float, int, float]:
        spec = candidate_specs[score.candidate_id]
        family_priority = 0 if spec.history_family == "A1" else 1
        strength_priority = -(spec.prior_strength or 0.0)
        return (
            round(score.equal_year_mean_primary, TIE_DECIMALS),
            family_priority,
            strength_priority,
        )

    winner = min(eligible, key=selection_key)
    passed = winner.equal_year_mean_primary < baseline.equal_year_mean_primary
    return AdvancementSelectionResult(
        selected_candidate_id=winner.candidate_id if passed else "A0_neutral",
        development_player_specific_winner=winner.candidate_id,
        development_baseline_score=baseline.equal_year_mean_primary,
        development_selected_score=(
            winner.equal_year_mean_primary
            if passed
            else baseline.equal_year_mean_primary
        ),
        development_passed=passed,
        catastrophic_development_years=reversals_by_id.get(
            winner.candidate_id,
            tuple(),
        ),
    )


def confirmation_passes(
    selected_candidate_id: str,
    scores_2024: Iterable[AdvancementCandidateScore],
) -> bool:
    if selected_candidate_id == "A0_neutral":
        return True
    by_id = {score.candidate_id: score for score in scores_2024}
    baseline = by_id["A0_neutral"]
    selected = by_id[selected_candidate_id]
    return selected.equal_year_mean_primary < baseline.equal_year_mean_primary
