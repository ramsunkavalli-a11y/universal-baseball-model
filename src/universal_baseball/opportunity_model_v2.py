"""Universal hitter-opportunity v2 surfaces and predeclared selection rule."""

from __future__ import annotations

from dataclasses import dataclass

import polars as pl

from universal_baseball.playing_time_model import (
    PT_FORM_U0,
    PT_V2_FORM_COMPLEXITY,
    PT_V2_FORMS,
    PlayingTimeHurdleFit,
    build_playing_time_design,
    fit_playing_time_hurdle,
    score_playing_time_hurdle,
)
from universal_baseball.playing_time_selection import pooled_playing_time_metrics


ROW_KEY_MULTIPLIER = 10_000_000
FULL_NLL_TIE_TOLERANCE = 0.001
MAE_WORSE_TOLERANCE = 0.02


@dataclass(frozen=True, slots=True)
class OpportunityFold:
    snapshot_year: int
    target_year: int
    predictors: pl.DataFrame
    targets: pl.DataFrame


@dataclass(frozen=True, slots=True)
class OpportunityV2Evaluation:
    selected_form: str
    fold_metrics: pl.DataFrame
    pooled_metrics: pl.DataFrame
    selection: dict[str, object]
    final_fit: PlayingTimeHurdleFit


def build_universal_hitter_opportunity_predictors(
    snapshot: pl.DataFrame,
    current_stats: pl.DataFrame,
    membership: pl.DataFrame,
    *,
    snapshot_year: int,
) -> pl.DataFrame:
    """Build one universal as-of predictor surface without future outcomes."""

    required_snapshot = {"snapshot_year", "player_id", "age_years", "as_of_level_group"}
    if required_snapshot - set(snapshot.columns):
        raise ValueError("universal opportunity snapshot has an unexpected schema")
    players = snapshot.filter(pl.col("snapshot_year") == snapshot_year).select(
        "player_id", "age_years", "as_of_level_group"
    )
    if players.is_empty() or players.group_by("player_id").len().filter(
        pl.col("len") != 1
    ).height:
        raise ValueError("universal opportunity snapshot is empty or has duplicate players")
    current_pa = current_stats.filter(pl.col("stat_group") == "hitting").group_by(
        "player_id"
    ).agg(
        pl.when(pl.col("sport_id") == 1)
        .then(pl.col("plate_appearances"))
        .otherwise(0)
        .sum()
        .cast(pl.Int64)
        .alias("current_season_mlb_pa"),
        pl.when(pl.col("sport_id") != 1)
        .then(pl.col("plate_appearances"))
        .otherwise(0)
        .sum()
        .cast(pl.Int64)
        .alias("current_season_milb_pa"),
    )
    on_40man = membership.filter(pl.col("season") == snapshot_year).select(
        "player_id", "on_40man"
    )
    if on_40man.group_by("player_id").len().filter(pl.col("len") != 1).height:
        raise ValueError("40-man history violates season-player grain")
    return (
        players.join(current_pa, on="player_id", how="left")
        .join(on_40man, on="player_id", how="left")
        .with_columns(
            pl.col("current_season_mlb_pa").fill_null(0).cast(pl.Int64),
            pl.col("current_season_milb_pa").fill_null(0).cast(pl.Int64),
            pl.col("on_40man").fill_null(False).cast(pl.Boolean),
        )
        .sort("player_id")
    )


def build_universal_hitter_opportunity_fold(
    snapshot: pl.DataFrame,
    current_stats: pl.DataFrame,
    next_stats: pl.DataFrame,
    membership: pl.DataFrame,
    *,
    snapshot_year: int,
    target_year: int | None = None,
) -> OpportunityFold:
    """Create one zero-inclusive direct snapshot-to-target hitter fold."""

    predictors = build_universal_hitter_opportunity_predictors(
        snapshot,
        current_stats,
        membership,
        snapshot_year=snapshot_year,
    )
    players = predictors.select("player_id")
    future_pa = next_stats.filter(
        (pl.col("stat_group") == "hitting") & (pl.col("sport_id") == 1)
    ).group_by("player_id").agg(
        pl.col("plate_appearances")
        .sum()
        .cast(pl.Int64)
        .alias("next_year_mlb_pa")
    )
    targets = (
        players.select("player_id")
        .join(future_pa, on="player_id", how="left")
        .with_columns(pl.col("next_year_mlb_pa").fill_null(0).cast(pl.Int64))
        .sort("player_id")
    )
    resolved_target_year = snapshot_year + 1 if target_year is None else target_year
    if resolved_target_year <= snapshot_year:
        raise ValueError("hitter opportunity target year must follow snapshot year")
    return OpportunityFold(
        snapshot_year=snapshot_year,
        target_year=resolved_target_year,
        predictors=predictors,
        targets=targets,
    )


def _combined_training(
    folds: list[OpportunityFold], *, form: str
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
            fold.targets.with_columns((pl.col("player_id") + offset).alias("player_id"))
        )
    return pl.concat(designs), pl.concat(targets)


def select_universal_opportunity_form(
    fold_metrics: pl.DataFrame, pooled_metrics: pl.DataFrame
) -> dict[str, object]:
    """Apply the fixed rolling-development rule without rescue tuning."""

    baseline = pooled_metrics.filter(pl.col("form") == PT_FORM_U0).row(0, named=True)
    decisions = []
    for form in PT_V2_FORMS[1:]:
        candidate = pooled_metrics.filter(pl.col("form") == form).row(0, named=True)
        comparison = fold_metrics.filter(pl.col("form").is_in([PT_FORM_U0, form])).pivot(
            on="form",
            index="target_year",
            values="mean_full_negative_log_likelihood",
        )
        wins = comparison.filter(pl.col(form) < pl.col(PT_FORM_U0)).height
        gates = {
            "pooled_full_nll_lower_than_u0": (
                float(candidate["mean_full_negative_log_likelihood"])
                < float(baseline["mean_full_negative_log_likelihood"])
            ),
            "full_nll_wins_at_least_three_of_four_folds": wins >= 3,
            "pooled_participation_log_loss_no_worse_than_u0": (
                float(candidate["participation_log_loss"])
                <= float(baseline["participation_log_loss"])
            ),
            "pooled_pa_mae_within_two_percent_of_u0": (
                float(candidate["unconditional_mlb_pa_mae"])
                <= float(baseline["unconditional_mlb_pa_mae"])
                * (1.0 + MAE_WORSE_TOLERANCE)
            ),
        }
        decisions.append(
            {
                "form": form,
                "full_nll_fold_wins": wins,
                "gates": gates,
                "eligible": all(gates.values()),
                "pooled_full_nll": float(candidate["mean_full_negative_log_likelihood"]),
            }
        )
    eligible = [row for row in decisions if row["eligible"]]
    if not eligible:
        selected = PT_FORM_U0
    else:
        best_nll = min(float(row["pooled_full_nll"]) for row in eligible)
        tied = [
            row
            for row in eligible
            if float(row["pooled_full_nll"]) <= best_nll + FULL_NLL_TIE_TOLERANCE
        ]
        selected = str(
            min(tied, key=lambda row: PT_V2_FORM_COMPLEXITY[str(row["form"])])["form"]
        )
    return {
        "selected_form": selected,
        "candidate_decisions": decisions,
        "full_nll_tie_tolerance": FULL_NLL_TIE_TOLERANCE,
        "mae_worse_tolerance": MAE_WORSE_TOLERANCE,
        "protected_2026_outcomes_used": False,
    }


def evaluate_universal_opportunity_forms(
    folds: list[OpportunityFold],
) -> OpportunityV2Evaluation:
    """Run four expanding-window evaluations and freeze the selected fit."""

    expected_years = [2018, 2021, 2022, 2023, 2024]
    if [fold.snapshot_year for fold in folds] != expected_years:
        raise ValueError(f"opportunity v2 requires exact snapshot years {expected_years}")
    scored_by_form: dict[str, list[pl.DataFrame]] = {form: [] for form in PT_V2_FORMS}
    metric_rows: list[dict[str, object]] = []
    for evaluation_index in range(1, len(folds)):
        training = folds[:evaluation_index]
        evaluation = folds[evaluation_index]
        for form in PT_V2_FORMS:
            train_design, train_targets = _combined_training(training, form=form)
            fit = fit_playing_time_hurdle(train_design, train_targets, form=form)
            score_design = build_playing_time_design(evaluation.predictors, form=form)
            scored, metrics = score_playing_time_hurdle(
                fit, score_design, evaluation.targets
            )
            scored_by_form[form].append(scored)
            metric_rows.append(
                {
                    "form": form,
                    "target_year": evaluation.target_year,
                    "training_snapshot_years": ",".join(
                        str(fold.snapshot_year) for fold in training
                    ),
                    **metrics,
                }
            )
    fold_metrics = pl.DataFrame(metric_rows).sort(["target_year", "form"])
    pooled_rows = []
    for form in PT_V2_FORMS:
        metrics = pooled_playing_time_metrics(pl.concat(scored_by_form[form]))
        pooled_rows.append({"form": form, **metrics})
    pooled_metrics = pl.DataFrame(pooled_rows).sort("form")
    selection = select_universal_opportunity_form(fold_metrics, pooled_metrics)
    selected_form = str(selection["selected_form"])
    final_design, final_targets = _combined_training(folds, form=selected_form)
    final_fit = fit_playing_time_hurdle(
        final_design, final_targets, form=selected_form
    )
    return OpportunityV2Evaluation(
        selected_form=selected_form,
        fold_metrics=fold_metrics,
        pooled_metrics=pooled_metrics,
        selection=selection,
        final_fit=final_fit,
    )
