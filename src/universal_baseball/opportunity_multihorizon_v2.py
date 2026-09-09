"""Chronology-safe direct multi-horizon opportunity development gate."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import polars as pl

from universal_baseball.hitter_opportunity_paths import (
    HITTER_OPPORTUNITY_HISTORY_SCHEMA,
    fit_hitter_opportunity_fallbacks,
    score_hitter_opportunity_paths,
)
from universal_baseball.opportunity_model_v2 import OpportunityFold
from universal_baseball.pitcher_opportunity_model_v2 import PitcherOpportunityFold
from universal_baseball.pitcher_opportunity_paths import (
    PITCHER_OPPORTUNITY_HISTORY_SCHEMA,
    fit_pitcher_opportunity_fallbacks,
    score_pitcher_opportunity_paths,
)
from universal_baseball.playing_time_model import (
    PITCHER_PT_V2_FORM_COMPLEXITY,
    PITCHER_PT_V2_FORMS,
    PT_FORM_P0,
    PT_FORM_U0,
    PT_V2_FORM_COMPLEXITY,
    PT_V2_FORMS,
    PlayingTimeHurdleFit,
    build_playing_time_design,
    fit_playing_time_hurdle,
    score_playing_time_hurdle,
)
from universal_baseball.playing_time_selection import pooled_playing_time_metrics


INCUMBENT_ID = "historical_cohort_fallback_v1"
ROW_KEY_MULTIPLIER = 10_000_000
FULL_NLL_TIE_TOLERANCE = 0.001
FORM_MAE_WORSE_TOLERANCE = 0.02
INCUMBENT_FOLD_MAE_WORSE_TOLERANCE = 0.10


@dataclass(frozen=True, slots=True)
class MultiHorizonEvaluation:
    component: str
    horizon: int
    selected_model: str
    fold_metrics: pl.DataFrame
    pooled_metrics: pl.DataFrame
    selection: dict[str, object]
    final_fit: PlayingTimeHurdleFit | None


def _combined_training(
    folds: list[OpportunityFold] | list[PitcherOpportunityFold], *, form: str
) -> tuple[pl.DataFrame, pl.DataFrame]:
    designs = []
    targets = []
    for index, fold in enumerate(folds, start=1):
        offset = index * ROW_KEY_MULTIPLIER
        designs.append(
            build_playing_time_design(fold.predictors, form=form).with_columns(
                (pl.col("player_id") + offset).alias("player_id")
            )
        )
        targets.append(
            fold.targets.select("player_id", "next_year_mlb_pa").with_columns(
                (pl.col("player_id") + offset).alias("player_id")
            )
        )
    return pl.concat(designs), pl.concat(targets)


def _hitter_history(folds: list[OpportunityFold], *, horizon: int) -> pl.DataFrame:
    return pl.concat(
        [
            fold.predictors.select(
                pl.lit(fold.snapshot_year).alias("snapshot_year"),
                "player_id",
                "age_years",
                "as_of_level_group",
            ).join(fold.targets, on="player_id", validate="1:1").select(
                "snapshot_year",
                "player_id",
                "age_years",
                "as_of_level_group",
                pl.lit(horizon).alias("horizon"),
                pl.col("next_year_mlb_pa").cast(pl.Float64).alias("future_mlb_pa"),
            )
            for fold in folds
        ]
    ).cast(HITTER_OPPORTUNITY_HISTORY_SCHEMA, strict=True)


def _pitcher_history(
    folds: list[PitcherOpportunityFold], *, horizon: int
) -> pl.DataFrame:
    return pl.concat(
        [
            fold.predictors.select(
                pl.lit(fold.snapshot_year).alias("snapshot_year"),
                "player_id",
                "age_years",
                "as_of_level_group",
                "as_of_role",
            ).join(fold.targets, on="player_id", validate="1:1").select(
                "snapshot_year",
                "player_id",
                "age_years",
                "as_of_level_group",
                "as_of_role",
                pl.lit(horizon).alias("horizon"),
                pl.col("next_year_mlb_pa").cast(pl.Float64).alias("future_mlb_bf"),
                pl.col("next_year_mlb_games").alias("future_mlb_games"),
                pl.col("next_year_mlb_starts").alias("future_mlb_starts"),
            )
            for fold in folds
        ]
    ).cast(PITCHER_OPPORTUNITY_HISTORY_SCHEMA, strict=True)


def _incumbent_score(
    component: str,
    training: list[OpportunityFold] | list[PitcherOpportunityFold],
    evaluation: OpportunityFold | PitcherOpportunityFold,
    *,
    horizon: int,
) -> pl.DataFrame:
    if component == "hitter":
        assert all(isinstance(fold, OpportunityFold) for fold in training)
        assert isinstance(evaluation, OpportunityFold)
        fit = fit_hitter_opportunity_fallbacks(
            _hitter_history(training, horizon=horizon),
            forecast_year=evaluation.snapshot_year + 1,
            horizons=[horizon],
        )
        paths = score_hitter_opportunity_paths(
            evaluation.predictors.select(
                "player_id", "age_years", "as_of_level_group"
            ),
            fit,
            as_of_date=date(evaluation.snapshot_year, 10, 15),
            forecast_year=evaluation.snapshot_year + 1,
        ).select(
            "player_id",
            pl.col("mlb_active_probability").alias("predicted_probability"),
            pl.col("expected_mlb_pa").alias("predicted_opportunity"),
        )
    elif component == "pitcher":
        assert all(isinstance(fold, PitcherOpportunityFold) for fold in training)
        assert isinstance(evaluation, PitcherOpportunityFold)
        fit = fit_pitcher_opportunity_fallbacks(
            _pitcher_history(training, horizon=horizon),
            forecast_year=evaluation.snapshot_year + 1,
            horizons=[horizon],
        )
        paths = score_pitcher_opportunity_paths(
            evaluation.predictors.select(
                "player_id", "age_years", "as_of_level_group", "as_of_role"
            ),
            fit,
            as_of_date=date(evaluation.snapshot_year, 10, 15),
            forecast_year=evaluation.snapshot_year + 1,
        ).select(
            "player_id",
            pl.col("mlb_active_probability").alias("predicted_probability"),
            pl.col("expected_mlb_bf").alias("predicted_opportunity"),
        )
    else:
        raise ValueError(f"unsupported component: {component}")
    return paths.join(
        evaluation.targets.select(
            "player_id", pl.col("next_year_mlb_pa").alias("observed_opportunity")
        ),
        on="player_id",
        validate="1:1",
    ).with_columns(
        (pl.col("observed_opportunity") > 0).cast(pl.Float64).alias("observed_active")
    )


def _incumbent_metrics(scored: pl.DataFrame) -> dict[str, float | int]:
    return {
        "scored_players": scored.height,
        "positive_players": scored.filter(pl.col("observed_opportunity") > 0).height,
        "participation_brier": float(
            scored.select(
                (pl.col("predicted_probability") - pl.col("observed_active")) ** 2
            ).select(pl.all().mean()).item()
        ),
        "opportunity_mae": float(
            scored.select(
                (pl.col("predicted_opportunity") - pl.col("observed_opportunity"))
                .abs()
                .mean()
            ).item()
        ),
        "observed_mean_opportunity": float(
            scored.get_column("observed_opportunity").mean()
        ),
        "predicted_mean_opportunity": float(
            scored.get_column("predicted_opportunity").mean()
        ),
    }


def evaluate_multi_horizon_forms(
    component: str,
    folds: list[OpportunityFold] | list[PitcherOpportunityFold],
    *,
    horizon: int,
    evaluation_snapshot_years: tuple[int, int, int, int],
) -> MultiHorizonEvaluation:
    """Evaluate one component/horizon against parametric and incumbent baselines."""

    if horizon not in {2, 3, 4}:
        raise ValueError("multi-horizon v2 supports only source-approved horizons 2-4")
    by_snapshot = {fold.snapshot_year: fold for fold in folds}
    if len(by_snapshot) != len(folds):
        raise ValueError("multi-horizon folds duplicate snapshot years")
    if any(fold.target_year != fold.snapshot_year + horizon for fold in folds):
        raise ValueError("multi-horizon fold target does not match horizon")
    if tuple(sorted(evaluation_snapshot_years)) != evaluation_snapshot_years:
        raise ValueError("evaluation snapshot years must be ordered")
    forms = PT_V2_FORMS if component == "hitter" else PITCHER_PT_V2_FORMS
    baseline_form = PT_FORM_U0 if component == "hitter" else PT_FORM_P0
    complexity = (
        PT_V2_FORM_COMPLEXITY
        if component == "hitter"
        else PITCHER_PT_V2_FORM_COMPLEXITY
    )
    scored_by_form = {form: [] for form in forms}
    incumbent_scored = []
    metric_rows = []
    incumbent_fold_rows = []
    for evaluation_year in evaluation_snapshot_years:
        evaluation = by_snapshot[evaluation_year]
        training = [
            fold
            for fold in folds
            if fold.target_year <= evaluation.snapshot_year
            and fold.snapshot_year < evaluation.snapshot_year
        ]
        if not training:
            raise ValueError("multi-horizon evaluation lacks chronology-safe training")
        incumbent = _incumbent_score(
            component, training, evaluation, horizon=horizon
        ).with_columns(pl.lit(evaluation_year).alias("evaluation_snapshot_year"))
        incumbent_scored.append(incumbent)
        incumbent_fold_rows.append(
            {
                "component": component,
                "horizon": horizon,
                "form": INCUMBENT_ID,
                "evaluation_snapshot_year": evaluation_year,
                "target_year": evaluation.target_year,
                "training_snapshot_years": ",".join(
                    str(fold.snapshot_year) for fold in training
                ),
                **_incumbent_metrics(incumbent),
            }
        )
        for form in forms:
            train_design, train_targets = _combined_training(training, form=form)
            fit = fit_playing_time_hurdle(train_design, train_targets, form=form)
            scored, metrics = score_playing_time_hurdle(
                fit,
                build_playing_time_design(evaluation.predictors, form=form),
                evaluation.targets,
            )
            scored_by_form[form].append(scored)
            metric_rows.append(
                {
                    "component": component,
                    "horizon": horizon,
                    "form": form,
                    "evaluation_snapshot_year": evaluation_year,
                    "target_year": evaluation.target_year,
                    "training_snapshot_years": ",".join(
                        str(fold.snapshot_year) for fold in training
                    ),
                    **metrics,
                }
            )
    fold_metrics = pl.concat(
        [pl.DataFrame(metric_rows), pl.DataFrame(incumbent_fold_rows)],
        how="diagonal_relaxed",
    ).sort(["evaluation_snapshot_year", "form"])
    pooled_rows = [
        {
            "component": component,
            "horizon": horizon,
            "form": form,
            **pooled_playing_time_metrics(pl.concat(scored_by_form[form])),
        }
        for form in forms
    ]
    incumbent_pooled = _incumbent_metrics(pl.concat(incumbent_scored))
    pooled_rows.append(
        {
            "component": component,
            "horizon": horizon,
            "form": INCUMBENT_ID,
            **incumbent_pooled,
        }
    )
    pooled_metrics = pl.DataFrame(pooled_rows, infer_schema_length=None).sort("form")
    baseline = next(row for row in pooled_rows if row["form"] == baseline_form)
    decisions = []
    for form in forms[1:]:
        candidate = next(row for row in pooled_rows if row["form"] == form)
        candidate_folds = fold_metrics.filter(pl.col("form") == form)
        baseline_folds = fold_metrics.filter(pl.col("form") == baseline_form).select(
            "evaluation_snapshot_year",
            pl.col("mean_full_negative_log_likelihood").alias("baseline_nll"),
        )
        incumbent_folds = fold_metrics.filter(pl.col("form") == INCUMBENT_ID).select(
            "evaluation_snapshot_year",
            pl.col("opportunity_mae").alias("incumbent_mae"),
        )
        comparison = candidate_folds.join(
            baseline_folds, on="evaluation_snapshot_year", validate="1:1"
        ).join(incumbent_folds, on="evaluation_snapshot_year", validate="1:1")
        nll_wins = comparison.filter(
            pl.col("mean_full_negative_log_likelihood") < pl.col("baseline_nll")
        ).height
        worst_incumbent_mae_ratio = float(
            (
                comparison.get_column("unconditional_mlb_pa_mae")
                / comparison.get_column("incumbent_mae")
            ).max()
        )
        gates = {
            "pooled_full_nll_lower_than_parametric_baseline": (
                float(candidate["mean_full_negative_log_likelihood"])
                < float(baseline["mean_full_negative_log_likelihood"])
            ),
            "full_nll_wins_at_least_three_of_four_folds": nll_wins >= 3,
            "pooled_participation_log_loss_no_worse": (
                float(candidate["participation_log_loss"])
                <= float(baseline["participation_log_loss"])
            ),
            "pooled_mae_within_two_percent_of_parametric_baseline": (
                float(candidate["unconditional_mlb_pa_mae"])
                <= float(baseline["unconditional_mlb_pa_mae"])
                * (1.0 + FORM_MAE_WORSE_TOLERANCE)
            ),
            "pooled_brier_no_worse_than_incumbent": (
                float(candidate["participation_brier"])
                <= float(incumbent_pooled["participation_brier"])
            ),
            "pooled_mae_no_worse_than_incumbent": (
                float(candidate["unconditional_mlb_pa_mae"])
                <= float(incumbent_pooled["opportunity_mae"])
            ),
            "every_fold_mae_within_ten_percent_of_incumbent": (
                worst_incumbent_mae_ratio
                <= 1.0 + INCUMBENT_FOLD_MAE_WORSE_TOLERANCE
            ),
        }
        decisions.append(
            {
                "form": form,
                "eligible": all(gates.values()),
                "full_nll_fold_wins": nll_wins,
                "worst_incumbent_mae_ratio": worst_incumbent_mae_ratio,
                "pooled_full_nll": float(
                    candidate["mean_full_negative_log_likelihood"]
                ),
                "gates": gates,
            }
        )
    eligible = [row for row in decisions if row["eligible"]]
    if not eligible:
        selected_model = INCUMBENT_ID
        final_fit = None
    else:
        best = min(float(row["pooled_full_nll"]) for row in eligible)
        tied = [
            row
            for row in eligible
            if float(row["pooled_full_nll"]) <= best + FULL_NLL_TIE_TOLERANCE
        ]
        selected_model = str(
            min(tied, key=lambda row: complexity[str(row["form"])])["form"]
        )
        final_design, final_targets = _combined_training(folds, form=selected_model)
        final_fit = fit_playing_time_hurdle(
            final_design, final_targets, form=selected_model
        )
    selection = {
        "selected_model": selected_model,
        "candidate_decisions": decisions,
        "incumbent_id": INCUMBENT_ID,
        "full_nll_tie_tolerance": FULL_NLL_TIE_TOLERANCE,
        "protected_2026_outcomes_used": False,
    }
    return MultiHorizonEvaluation(
        component=component,
        horizon=horizon,
        selected_model=selected_model,
        fold_metrics=fold_metrics,
        pooled_metrics=pooled_metrics,
        selection=selection,
        final_fit=final_fit,
    )
