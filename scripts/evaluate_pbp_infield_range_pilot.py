#!/usr/bin/env python
"""Chronologically validate the first PBP Total-Zone-style infield model.

This pilot reads already materialized opportunity partitions.  It compares a
classic park/opponent context model with the same model plus coordinate bins,
tunes regression only on older folds, and predicts later player-position range
rates.  It is a component-signal test, not yet a WAR-stack promotion test.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.historical_fielding_range import (
    aggregate_player_fielding_seasons,
    evaluate_fielding_projection,
    pooled_projection_metrics,
    score_contextual_fielding_residuals,
    score_joint_park_defense_fielding_residuals,
    score_visitor_anchored_park_fielding_residuals,
)


REGRESSION_GRID = (0.0, 100.0, 250.0, 400.0, 800.0, 1200.0, 2000.0)
MINIMUM_PRIOR_SELECTION_PAIRS = 25


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-root",
        type=Path,
        default=Path("data/working/pbp-opportunity-foundation-v1"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/pbp-infield-range-pilot-v1"),
    )
    parser.add_argument("--minimum-target-opportunities", type=int, default=25)
    parser.add_argument(
        "--game-context",
        type=Path,
        default=Path(
            "reports/generated/defensive-venue-context-v1/affiliated-game-context.parquet"
        ),
    )
    return parser


def _load_fielding(root: Path, game_context_path: Path | None = None) -> pl.DataFrame:
    paths = sorted(root.glob("season=*/level=*/fielding/*.parquet"))
    if not paths:
        raise FileNotFoundError(f"no fielding opportunity partitions under {root}")
    columns = [
        "season",
        "level",
        "game_pk",
        "at_bat_index",
        "source_asset",
        "responsible_position",
        "responsible_fielder_id",
        "conversion_out",
        "bb_type",
        "stand",
        "p_throws",
        "park_key",
        "defense_team",
        "home_team",
        "batter",
        "hc_x",
        "hc_y",
    ]
    frame = pl.concat(
        [pl.read_parquet(path, columns=columns) for path in paths],
        how="diagonal_relaxed",
    )
    # The pilot should not double-count an overlapping public release snapshot.
    frame = frame.sort(["game_pk", "at_bat_index", "source_asset"]).unique(
        subset=["game_pk", "at_bat_index"], keep="first", maintain_order=True
    )
    if game_context_path is not None and game_context_path.exists():
        context = pl.read_parquet(
            game_context_path, columns=["game_pk", "venue_id"]
        ).unique(subset=["game_pk"], keep="none")
        frame = frame.join(context, on="game_pk", how="left", validate="m:1").with_columns(
            pl.when(pl.col("venue_id").is_not_null())
            .then(
                pl.concat_str(
                    [pl.col("season"), pl.lit("venue"), pl.col("venue_id")],
                    separator=":",
                )
            )
            .otherwise(pl.col("park_key"))
            .alias("park_key")
        )
    return frame


def _candidate_fold_rows(
    player_seasons: pl.DataFrame,
    *,
    minimum_target_opportunities: int,
) -> tuple[dict[tuple[int, float], pl.DataFrame], list[dict[str, Any]]]:
    years = sorted(player_seasons.get_column("season").unique().to_list())
    target_years = [year for year in years if any(old < year for old in years)]
    pairs: dict[tuple[int, float], pl.DataFrame] = {}
    metrics: list[dict[str, Any]] = []
    for year in target_years:
        for regression in REGRESSION_GRID:
            paired, row = evaluate_fielding_projection(
                player_seasons,
                target_season=int(year),
                regression_opportunities=regression,
                minimum_target_opportunities=minimum_target_opportunities,
            )
            pairs[(int(year), regression)] = paired
            metrics.append({**row, "regression_opportunities": regression})
    return pairs, metrics


def _prior_error(
    pairs: dict[tuple[int, float], pl.DataFrame],
    *,
    target_year: int,
    regression: float,
) -> tuple[float, int]:
    prior = [
        frame
        for (year, candidate), frame in pairs.items()
        if year < target_year and candidate == regression and not frame.is_empty()
    ]
    if not prior:
        return float("inf"), 0
    pooled = pl.concat(prior, how="diagonal_relaxed")
    return float(pooled.get_column("candidate_error").pow(2).sum()), int(pooled.height)


def _nested_selected(
    all_pairs: dict[str, dict[tuple[int, float], pl.DataFrame]],
) -> tuple[list[pl.DataFrame], list[dict[str, Any]]]:
    years = sorted(
        {
            year
            for pairs in all_pairs.values()
            for year, _ in pairs
        }
    )
    selected_frames: list[pl.DataFrame] = []
    selection_rows: list[dict[str, Any]] = []
    for year in years:
        choices: list[tuple[float, int, str, float]] = []
        for model_name, pairs in all_pairs.items():
            for regression in REGRESSION_GRID:
                squared_error, count = _prior_error(
                    pairs, target_year=year, regression=regression
                )
                choices.append((squared_error, -count, model_name, regression))
        usable = [
            choice
            for choice in choices
            if -choice[1] >= MINIMUM_PRIOR_SELECTION_PAIRS
        ]
        if not usable:
            # First fold is warm-up evidence only; it is not reported as a
            # nested selected result because no older fold could choose it.
            continue
        squared_error, negative_count, model_name, regression = min(usable)
        frame = all_pairs[model_name][(year, regression)]
        if frame.is_empty():
            continue
        selected_frames.append(
            frame.with_columns(
                pl.lit(model_name).alias("selected_measurement_model"),
                pl.lit(regression).alias("selected_regression_opportunities"),
            )
        )
        selection_rows.append(
            {
                "target_season": int(year),
                "selected_measurement_model": model_name,
                "selected_regression_opportunities": regression,
                "prior_selection_player_position_count": -negative_count,
                "prior_selection_sse": squared_error,
                "evaluation_player_position_count": int(frame.height),
            }
        )
    return selected_frames, selection_rows


def _main_report(
    opportunities: pl.DataFrame,
    scored_by_model: dict[str, pl.DataFrame],
    candidate_metrics: list[dict[str, Any]],
    selected_frames: list[pl.DataFrame],
    selection_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    nested = pooled_projection_metrics(selected_frames)
    coordinate_coverage = float(
        opportunities.select(
            (pl.col("hc_x").is_not_null() & pl.col("hc_y").is_not_null()).mean()
        ).item()
    )
    park_adjustments: dict[str, Any] = {}
    for name, scored in scored_by_model.items():
        adjustment = (
            scored.get_column("joint_park_effect")
            if "joint_park_effect" in scored.columns
            else scored.get_column("visitor_park_effect")
            if "visitor_park_effect" in scored.columns
            else scored.get_column("park_expected_out")
            - scored.get_column("context_expected_out")
        )
        park_adjustments[name] = {
            "mean_absolute_probability_adjustment": float(adjustment.abs().mean()),
            "p95_absolute_probability_adjustment": float(
                adjustment.abs().quantile(0.95)
            ),
        }
    report = {
        "report_schema_version": "0.2",
        "component": "pbp_total_zone_style_infield_range_pilot",
        "data_scope": "all nonempty materialized public 2016-2024 MiLB PBP partitions",
        "years": sorted(opportunities.get_column("season").unique().to_list()),
        "positions": [4, 5, 6],
        "batted_ball_types": ["ground_ball"],
        "opportunity_count": int(opportunities.height),
        "coordinate_coverage": coordinate_coverage,
        "physical_venue_coverage": (
            float(opportunities.get_column("venue_id").is_not_null().mean())
            if "venue_id" in opportunities.columns
            else 0.0
        ),
        "candidate_metrics": candidate_metrics,
        "nested_selection": selection_rows,
        "minimum_prior_selection_pairs": MINIMUM_PRIOR_SELECTION_PAIRS,
        "nested_pooled_metrics": nested,
        "park_adjustment_diagnostics": park_adjustments,
        "protected_2026_accessed": False,
        "promotion_decision": "pilot_only_pending_full_history_and_WAR_stack_validation",
    }
    if "joint_park_team_player" in scored_by_model:
        report["joint_park_diagnostics"] = _joint_park_diagnostics(
            scored_by_model["coordinate_bins"],
            scored_by_model["joint_park_team_player"],
        )
    return report


def _joint_park_diagnostics(
    naive: pl.DataFrame, joint: pl.DataFrame
) -> dict[str, Any]:
    keys = ["season", "level", "responsible_position", "park_context"]
    side = (
        joint.group_by(*keys, "defense_is_home")
        .agg(
            pl.col("joint_base_residual").mean().alias("mean_base_residual"),
            pl.len().alias("opportunities"),
        )
    )
    home = side.filter(pl.col("defense_is_home")).select(
        *keys,
        pl.col("mean_base_residual").alias("home_mean_base_residual"),
        pl.col("opportunities").alias("home_opportunities"),
    )
    visitor = side.filter(~pl.col("defense_is_home")).select(
        *keys,
        pl.col("mean_base_residual").alias("visitor_mean_base_residual"),
        pl.col("opportunities").alias("visitor_opportunities"),
    )
    paired_sides = home.join(visitor, on=keys, how="inner", validate="1:1").filter(
        (pl.col("home_opportunities") >= 25)
        & (pl.col("visitor_opportunities") >= 25)
    )

    naive_effect = naive.group_by(keys).agg(
        (
            pl.col("park_expected_out") - pl.col("context_expected_out")
        ).mean().alias("naive_park_effect")
    )
    joint_effect = joint.group_by(keys).agg(
        pl.col("joint_park_effect").mean().alias("joint_park_effect"),
        pl.len().alias("opportunities"),
    )
    compared = naive_effect.join(joint_effect, on=keys, validate="1:1").with_columns(
        (pl.col("joint_park_effect") - pl.col("naive_park_effect")).alias(
            "joint_minus_naive"
        )
    )
    largest = (
        compared.with_columns(pl.col("joint_park_effect").abs().alias("absolute_effect"))
        .sort("absolute_effect", descending=True)
        .head(12)
        .drop("absolute_effect")
        .to_dicts()
    )
    return {
        "method": "crossed_shrunken_park_defensive_team_responsible_fielder_backfit",
        "visitor_opportunity_share": float(
            joint.get_column("defense_is_home").not_().mean()
        ),
        "park_position_groups": int(compared.height),
        "home_visitor_validation_groups": int(paired_sides.height),
        "home_visitor_raw_residual_correlation": (
            float(
                paired_sides.select(
                    pl.corr(
                        "home_mean_base_residual", "visitor_mean_base_residual"
                    )
                ).item()
            )
            if paired_sides.height >= 2
            else None
        ),
        "naive_joint_park_effect_correlation": float(
            compared.select(pl.corr("naive_park_effect", "joint_park_effect")).item()
        ),
        "mean_absolute_joint_minus_naive": float(
            compared.get_column("joint_minus_naive").abs().mean()
        ),
        "joint_park_effect_standard_deviation": float(
            compared.get_column("joint_park_effect").std()
        ),
        "largest_absolute_joint_park_effects": largest,
    }


def _event_fold_metric(
    scored: pl.DataFrame,
    player_seasons: pl.DataFrame,
    *,
    target_season: int,
    regression: float,
    minimum_target_opportunities: int,
) -> dict[str, Any]:
    from universal_baseball.historical_fielding_range import (
        project_player_fielding_rates,
    )

    projected = project_player_fielding_rates(
        player_seasons,
        target_season=target_season,
        regression_opportunities=regression,
    )
    eligible = player_seasons.filter(
        (pl.col("season") == target_season)
        & (pl.col("fielding_opportunities") >= minimum_target_opportunities)
    ).select("responsible_fielder_id", "responsible_position")
    events = (
        scored.filter(pl.col("season") == target_season)
        .join(
            eligible,
            on=["responsible_fielder_id", "responsible_position"],
            how="inner",
            validate="m:1",
        )
        .join(
            projected.select(
                "responsible_fielder_id",
                "responsible_position",
                "projected_range_rate",
            ),
            on=["responsible_fielder_id", "responsible_position"],
            how="inner",
            validate="m:1",
        )
        .with_columns(
            pl.col("expected_out_probability").clip(0.001, 0.999).alias(
                "neutral_probability"
            ),
            (
                pl.col("expected_out_probability")
                + pl.col("projected_range_rate")
            )
            .clip(0.001, 0.999)
            .alias("candidate_probability"),
        )
    )
    if events.is_empty():
        return {
            "target_season": int(target_season),
            "regression_opportunities": float(regression),
            "event_count": 0,
        }
    totals = events.select(
        pl.len().alias("event_count"),
        pl.struct("responsible_fielder_id", "responsible_position")
        .n_unique()
        .alias("player_position_count"),
        (pl.col("candidate_probability") - pl.col("actual_out"))
        .pow(2)
        .sum()
        .alias("candidate_sse"),
        (pl.col("neutral_probability") - pl.col("actual_out"))
        .pow(2)
        .sum()
        .alias("neutral_sse"),
        (
            -pl.col("actual_out") * pl.col("candidate_probability").log()
            - (1.0 - pl.col("actual_out"))
            * (1.0 - pl.col("candidate_probability")).log()
        )
        .sum()
        .alias("candidate_log_loss_sum"),
        (
            -pl.col("actual_out") * pl.col("neutral_probability").log()
            - (1.0 - pl.col("actual_out"))
            * (1.0 - pl.col("neutral_probability")).log()
        )
        .sum()
        .alias("neutral_log_loss_sum"),
    ).row(0, named=True)
    n = int(totals["event_count"])
    return {
        "target_season": int(target_season),
        "regression_opportunities": float(regression),
        **{key: int(value) if key.endswith("count") else float(value) for key, value in totals.items()},
        "candidate_brier": float(totals["candidate_sse"] / n),
        "neutral_brier": float(totals["neutral_sse"] / n),
        "brier_improvement": float(
            (totals["neutral_sse"] - totals["candidate_sse"]) / n
        ),
        "candidate_log_loss": float(totals["candidate_log_loss_sum"] / n),
        "neutral_log_loss": float(totals["neutral_log_loss_sum"] / n),
        "log_loss_improvement": float(
            (totals["neutral_log_loss_sum"] - totals["candidate_log_loss_sum"])
            / n
        ),
    }


def _pool_event_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    usable = [row for row in rows if row.get("event_count", 0)]
    if not usable:
        return {"event_count": 0}
    n = sum(int(row["event_count"]) for row in usable)
    candidate_sse = sum(float(row["candidate_sse"]) for row in usable)
    neutral_sse = sum(float(row["neutral_sse"]) for row in usable)
    candidate_log = sum(float(row["candidate_log_loss_sum"]) for row in usable)
    neutral_log = sum(float(row["neutral_log_loss_sum"]) for row in usable)
    return {
        "event_count": n,
        "candidate_brier": candidate_sse / n,
        "neutral_brier": neutral_sse / n,
        "brier_improvement": (neutral_sse - candidate_sse) / n,
        "candidate_log_loss": candidate_log / n,
        "neutral_log_loss": neutral_log / n,
        "log_loss_improvement": (neutral_log - candidate_log) / n,
    }


def _event_level_chronological_comparison(
    scored_by_model: dict[str, pl.DataFrame],
    *,
    minimum_target_opportunities: int,
) -> dict[str, Any]:
    specifications: dict[str, tuple[pl.DataFrame, pl.DataFrame]] = {
        model_name: (scored, aggregate_player_fielding_seasons(scored))
        for model_name, scored in scored_by_model.items()
    }
    if {
        "joint_park_team_player",
        "visitor_anchored_park",
    }.issubset(scored_by_model):
        visitor_seasons = aggregate_player_fielding_seasons(
            scored_by_model["visitor_anchored_park"]
        )
        joint_seasons = aggregate_player_fielding_seasons(
            scored_by_model["joint_park_team_player"]
        )
        specifications["joint_context_plus_visitor_player"] = (
            scored_by_model["joint_park_team_player"],
            visitor_seasons,
        )
        specifications["visitor_context_plus_joint_player"] = (
            scored_by_model["visitor_anchored_park"],
            joint_seasons,
        )
        blend_keys = ["season", "responsible_fielder_id", "responsible_position"]
        for joint_weight in (0.25, 0.5, 0.75):
            blended = (
                visitor_seasons.join(
                    joint_seasons.select(
                        *blend_keys,
                        pl.col("fielding_outs_above_expected").alias("joint_outs"),
                        pl.col("fielding_outs_above_expected_rate").alias(
                            "joint_rate"
                        ),
                    ),
                    on=blend_keys,
                    how="inner",
                    validate="1:1",
                )
                .with_columns(
                    (
                        (1.0 - joint_weight)
                        * pl.col("fielding_outs_above_expected")
                        + joint_weight * pl.col("joint_outs")
                    ).alias("fielding_outs_above_expected"),
                    (
                        (1.0 - joint_weight)
                        * pl.col("fielding_outs_above_expected_rate")
                        + joint_weight * pl.col("joint_rate")
                    ).alias("fielding_outs_above_expected_rate"),
                )
                .drop("joint_outs", "joint_rate")
            )
            label = int(round(joint_weight * 100))
            specifications[f"visitor_context_player_blend_joint_{label}"] = (
                scored_by_model["visitor_anchored_park"],
                blended,
            )
    if {
        "joint_park_team_player",
        "coordinate_bins",
    }.issubset(scored_by_model):
        specifications["joint_context_plus_coordinate_player"] = (
            scored_by_model["joint_park_team_player"],
            aggregate_player_fielding_seasons(scored_by_model["coordinate_bins"]),
        )

    rows: list[dict[str, Any]] = []
    for model_name, (scored, seasons) in specifications.items():
        years = sorted(seasons.get_column("season").unique().to_list())
        for year in years[1:]:
            for regression in REGRESSION_GRID:
                rows.append(
                    {
                        **_event_fold_metric(
                            scored,
                            seasons,
                            target_season=int(year),
                            regression=regression,
                            minimum_target_opportunities=minimum_target_opportunities,
                        ),
                        "measurement_model": model_name,
                    }
                )

    model_selected: list[dict[str, Any]] = []
    overall_selected: list[dict[str, Any]] = []
    years = sorted({int(row["target_season"]) for row in rows})
    for year in years:
        for model_name in specifications:
            choices = []
            for regression in REGRESSION_GRID:
                prior = [
                    row
                    for row in rows
                    if row["measurement_model"] == model_name
                    and row["regression_opportunities"] == regression
                    and row["target_season"] < year
                    and row.get("event_count", 0)
                ]
                if prior:
                    choices.append(
                        (
                            sum(row["candidate_sse"] for row in prior)
                            / sum(row["event_count"] for row in prior),
                            regression,
                        )
                    )
            if not choices:
                continue
            _, selected_regression = min(choices)
            selected = next(
                row
                for row in rows
                if row["measurement_model"] == model_name
                and row["regression_opportunities"] == selected_regression
                and row["target_season"] == year
            )
            model_selected.append(selected)

        overall_choices = []
        for model_name in specifications:
            for regression in REGRESSION_GRID:
                prior = [
                    row
                    for row in rows
                    if row["measurement_model"] == model_name
                    and row["regression_opportunities"] == regression
                    and row["target_season"] < year
                    and row.get("event_count", 0)
                ]
                if prior:
                    overall_choices.append(
                        (
                            sum(row["candidate_sse"] for row in prior)
                            / sum(row["event_count"] for row in prior),
                            model_name,
                            regression,
                        )
                    )
        if overall_choices:
            _, selected_model, selected_regression = min(overall_choices)
            overall_selected.append(
                next(
                    row
                    for row in rows
                    if row["measurement_model"] == selected_model
                    and row["regression_opportunities"] == selected_regression
                    and row["target_season"] == year
                )
            )

    per_model = {
        model_name: {
            "pooled": _pool_event_rows(
                [
                    row
                    for row in model_selected
                    if row["measurement_model"] == model_name
                ]
            ),
            "folds": [
                row
                for row in model_selected
                if row["measurement_model"] == model_name
            ],
        }
        for model_name in specifications
    }
    visitor_family_names = {
        name
        for name in specifications
        if name == "visitor_anchored_park"
        or name == "visitor_context_plus_joint_player"
        or name.startswith("visitor_context_player_blend_joint_")
    }
    visitor_family_selected: list[dict[str, Any]] = []
    for year in years:
        choices = []
        for model_name in visitor_family_names:
            for regression in REGRESSION_GRID:
                prior = [
                    row
                    for row in rows
                    if row["measurement_model"] == model_name
                    and row["regression_opportunities"] == regression
                    and row["target_season"] < year
                    and row.get("event_count", 0)
                ]
                if prior:
                    choices.append(
                        (
                            sum(row["candidate_sse"] for row in prior)
                            / sum(row["event_count"] for row in prior),
                            model_name,
                            regression,
                        )
                    )
        if choices:
            _, selected_model, selected_regression = min(choices)
            visitor_family_selected.append(
                next(
                    row
                    for row in rows
                    if row["measurement_model"] == selected_model
                    and row["regression_opportunities"] == selected_regression
                    and row["target_season"] == year
                )
            )
    return {
        "selection_rule": "lowest pooled prior-fold next-season event Brier score",
        "per_model_nested": per_model,
        "overall_nested": {
            "pooled": _pool_event_rows(overall_selected),
            "folds": overall_selected,
        },
        "visitor_family_nested": {
            "selection_rule": (
                "lowest pooled prior-fold Brier score among visitor-context "
                "joint/visitor player weights and regression values"
            ),
            "pooled": _pool_event_rows(visitor_family_selected),
            "folds": visitor_family_selected,
        },
        "all_fold_metrics": rows,
    }


def _write_markdown(path: Path, report: dict[str, Any]) -> None:
    pooled = report["nested_pooled_metrics"]
    lines = [
        "# PBP infield-range pilot",
        "",
        "This is the first clean test of the historical Total Zone idea: compare each",
        "ground ball with similar balls after level, position, handedness, park and batter",
        "adjustment, then ask whether a player's residual persists into later seasons.",
        "",
        f"- Scope: {report['data_scope']}",
        f"- Years: {report['years']}",
        f"- Infield ground-ball opportunities: {report['opportunity_count']:,}",
        f"- Coordinate coverage: {report['coordinate_coverage']:.1%}",
        f"- Physical venue-ID coverage: {report['physical_venue_coverage']:.1%}",
        "- 2026 accessed: **false**",
        "",
        "## Chronological result",
        "",
    ]
    if pooled.get("player_position_count"):
        lines.extend(
            [
                f"- Later-season player-position tests: {pooled['player_position_count']:,}",
                f"- Candidate RMSE: {pooled['candidate_rmse']:.6f} outs per opportunity",
                f"- Neutral RMSE: {pooled['neutral_rmse']:.6f}",
                f"- RMSE change: {pooled['rmse_change']:+.6f}",
                f"- Prediction/actual correlation: {pooled['correlation']:.4f}",
            ]
        )
    else:
        lines.append("- Insufficient repeated player-position samples for a pooled result.")
    lines.extend(
        [
            "",
            "## Nested choices",
            "",
            *[
                (
                    f"- {row['target_season']}: {row['selected_measurement_model']}, "
                    f"regression={row['selected_regression_opportunities']:.0f} opportunities, "
                    f"test pairs={row['evaluation_player_position_count']}"
                )
                for row in report["nested_selection"]
            ],
            "",
            "## Interpretation",
            "",
            "A negative RMSE change means prior play-by-play range information beat treating",
            "every returning infielder as exactly average. This pilot is deliberately not a",
            "promotion decision: the full 2016-2024 history, position translation, age effects",
            "and downstream WAR validation remain required.",
        ]
    )
    diagnostics = report.get("joint_park_diagnostics")
    if diagnostics:
        lines.extend(
            [
                "",
                "## Park/defense separation",
                "",
                "The joint model estimates park, defensive-team, and responsible-fielder",
                "effects together. Visiting defenses identify whether a result follows the",
                "park rather than the home club.",
                "",
                f"- Visiting share of opportunities: {diagnostics['visitor_opportunity_share']:.1%}",
                f"- Home/visitor validation groups: {diagnostics['home_visitor_validation_groups']:,}",
                f"- Home/visitor raw park correlation: {diagnostics['home_visitor_raw_residual_correlation']:.4f}",
                f"- Naive/joint park-effect correlation: {diagnostics['naive_joint_park_effect_correlation']:.4f}",
                f"- Mean absolute change from naive park effect: {diagnostics['mean_absolute_joint_minus_naive']:.6f}",
            ]
        )
    event_result = report.get("event_level_chronological_comparison")
    if event_result:
        lines.extend(
            [
                "",
                "## Common-outcome next-season test",
                "",
                "Every measurement method is judged against the same later-season ground-ball",
                "outcomes. Positive improvement means the prior player rating improved the",
                "event probability beyond that method's neutral context estimate.",
                "",
            ]
        )
        for model_name, result in event_result["per_model_nested"].items():
            pooled_model = result["pooled"]
            lines.append(
                f"- {model_name}: Brier improvement "
                f"{pooled_model['brier_improvement']:+.8f}; log-loss improvement "
                f"{pooled_model['log_loss_improvement']:+.8f}; "
                f"events={pooled_model['event_count']:,}"
            )
        selected_event = event_result["overall_nested"]["pooled"]
        visitor_nested = event_result["visitor_family_nested"]["pooled"]
        lines.extend(
            [
                "",
                f"Overall nested Brier improvement: {selected_event['brier_improvement']:+.8f}",
                f"Overall nested log-loss improvement: {selected_event['log_loss_improvement']:+.8f}",
                "",
                f"Visitor-family nested Brier improvement: {visitor_nested['brier_improvement']:+.8f}",
                f"Visitor-family nested log-loss improvement: {visitor_nested['log_loss_improvement']:+.8f}",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = _parser().parse_args()
    fielding = _load_fielding(args.input_root, args.game_context)
    infield = fielding.filter(
        pl.col("responsible_position").is_in([4, 5, 6])
        & (pl.col("bb_type") == "ground_ball")
    )
    scored_by_model = {
        "classic_no_coordinates": score_contextual_fielding_residuals(
            infield, use_coordinates=False
        ),
        "coordinate_bins": score_contextual_fielding_residuals(
            infield, use_coordinates=True
        ),
        "joint_park_team_player": score_joint_park_defense_fielding_residuals(
            infield
        ),
        "visitor_anchored_park": score_visitor_anchored_park_fielding_residuals(
            infield
        ),
    }
    all_pairs: dict[str, dict[tuple[int, float], pl.DataFrame]] = {}
    candidate_metrics: list[dict[str, Any]] = []
    for model_name, scored in scored_by_model.items():
        seasons = aggregate_player_fielding_seasons(scored)
        pairs, metrics = _candidate_fold_rows(
            seasons,
            minimum_target_opportunities=args.minimum_target_opportunities,
        )
        all_pairs[model_name] = pairs
        candidate_metrics.extend(
            {**row, "measurement_model": model_name} for row in metrics
        )
    selected_frames, selection_rows = _nested_selected(all_pairs)
    report = _main_report(
        infield,
        scored_by_model,
        candidate_metrics,
        selected_frames,
        selection_rows,
    )
    report["event_level_chronological_comparison"] = (
        _event_level_chronological_comparison(
            scored_by_model,
            minimum_target_opportunities=args.minimum_target_opportunities,
        )
    )
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    _write_markdown(args.output_root / "report.md", report)
    if selected_frames:
        pl.concat(selected_frames, how="diagonal_relaxed").write_parquet(
            args.output_root / "nested_predictions.parquet"
        )
    pl.DataFrame(candidate_metrics).write_parquet(
        args.output_root / "candidate_fold_metrics.parquet"
    )
    pl.DataFrame(
        report["event_level_chronological_comparison"]["all_fold_metrics"]
    ).write_parquet(args.output_root / "event_fold_metrics.parquet")
    print((args.output_root / "report.md").read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
