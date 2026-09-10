"""Structural and statistical-law checks for the private playable preview."""

from __future__ import annotations

from typing import Any

import polars as pl

from universal_baseball.prospect_value import display_fv, model_fv_from_expected_war


TOLERANCE = 1e-8


def _check(name: str, failures: int, rows: int) -> dict[str, Any]:
    return {
        "name": name,
        "status": "pass" if failures == 0 else "fail",
        "failures": int(failures),
        "rows_checked": int(rows),
    }


def _outside_unit_interval(frame: pl.DataFrame, columns: tuple[str, ...]) -> int:
    expression = pl.any_horizontal(
        pl.col(column).is_null()
        | ~pl.col(column).is_finite()
        | (pl.col(column) < 0.0)
        | (pl.col(column) > 1.0)
        for column in columns
    )
    return frame.filter(expression).height


def audit_private_preview_laws(
    hitter_paths: pl.DataFrame,
    pitcher_paths: pl.DataFrame,
    nested: pl.DataFrame,
    values: pl.DataFrame,
) -> dict[str, Any]:
    """Audit identities and boundaries that must hold without model fitting."""

    checks: list[dict[str, Any]] = []
    expected_seasons = {2027, 2028, 2029, 2030, 2031, 2032}
    for player_type, frame in (("hitter", hitter_paths), ("pitcher", pitcher_paths)):
        duplicates = frame.group_by("player_id", "season").len().filter(pl.col("len") != 1)
        checks.append(_check(f"{player_type}_unique_player_season", duplicates.height, frame.height))
        bad_horizons = frame.group_by("player_id").agg(
            pl.len().alias("rows"), pl.col("season").n_unique().alias("seasons")
        ).filter((pl.col("rows") != 6) | (pl.col("seasons") != 6))
        wrong_seasons = set(frame.get_column("season").unique().to_list()) != expected_seasons
        checks.append(
            _check(
                f"{player_type}_complete_six_year_path",
                bad_horizons.height + int(wrong_seasons),
                frame.get_column("player_id").n_unique(),
            )
        )
        checks.append(
            _check(
                f"{player_type}_active_probability_bounds",
                _outside_unit_interval(frame, ("mlb_active_probability",)),
                frame.height,
            )
        )

    hitter_component_columns = (
        "predicted_ubb_rate", "predicted_hbp_rate", "predicted_single_rate",
        "predicted_double_rate", "predicted_triple_rate", "predicted_hr_rate",
        "predicted_other_rate",
    )
    hitter_bad_components = hitter_paths.filter(
        pl.any_horizontal(
            (pl.col(column) < 0.0) | (pl.col(column) > 1.0)
            for column in hitter_component_columns
        )
        | ((pl.sum_horizontal(*hitter_component_columns) - 1.0).abs() > TOLERANCE)
    ).height
    checks.append(_check("hitter_component_simplex", hitter_bad_components, hitter_paths.height))

    pitcher_component_columns = (
        "predicted_other_rate", "predicted_so_rate", "predicted_ubb_rate",
        "predicted_hbp_rate", "predicted_hr_rate",
    )
    pitcher_bad_components = pitcher_paths.filter(
        pl.any_horizontal(
            (pl.col(column) < 0.0) | (pl.col(column) > 1.0)
            for column in pitcher_component_columns
        )
        | ((pl.sum_horizontal(*pitcher_component_columns) - 1.0).abs() > TOLERANCE)
    ).height
    checks.append(_check("pitcher_component_simplex", pitcher_bad_components, pitcher_paths.height))

    role_columns = (
        "starter_probability_if_active", "swingman_probability_if_active",
        "reliever_probability_if_active",
    )
    pitcher_bad_roles = pitcher_paths.filter(
        pl.any_horizontal(
            (pl.col(column) < 0.0) | (pl.col(column) > 1.0)
            for column in role_columns
        )
        | ((pl.sum_horizontal(*role_columns) - 1.0).abs() > TOLERANCE)
    ).height
    checks.append(_check("pitcher_role_probability_simplex", pitcher_bad_roles, pitcher_paths.height))

    for player_type, frame, conditional, expected, denominator, rate in (
        ("hitter", hitter_paths, "conditional_mlb_pa", "expected_mlb_pa", 600.0,
         "conditional_war_per_600_pa"),
        ("pitcher", pitcher_paths, "conditional_mlb_bf", "expected_mlb_bf", 800.0,
         "conditional_war_per_800_bf"),
    ):
        bad_workload = frame.filter(
            (pl.col(expected) - pl.col("mlb_active_probability") * pl.col(conditional)).abs()
            > TOLERANCE
        ).height
        bad_war = frame.filter(
            (pl.col("expected_war") - pl.col(rate) * pl.col(expected) / denominator).abs()
            > TOLERANCE
        ).height
        checks.append(_check(f"{player_type}_expected_workload_identity", bad_workload, frame.height))
        checks.append(_check(f"{player_type}_expected_war_identity", bad_war, frame.height))

    applicable = nested.filter(pl.col("ordered_arrival_probability").is_not_null())
    nested_failures = applicable.filter(
        (pl.col("ordered_arrival_probability") < pl.col("ordered_meaningful_probability"))
        | (pl.col("ordered_meaningful_probability") < pl.col("ordered_established_probability"))
        | (pl.col("established_probability") < 0.0)
        | (pl.col("meaningful_only_probability") < 0.0)
        | (pl.col("fringe_probability") < 0.0)
        | (
            (
                pl.col("fringe_probability")
                + pl.col("meaningful_only_probability")
                + pl.col("established_probability")
                - pl.col("ordered_arrival_probability")
            ).abs()
            > TOLERANCE
        )
    ).height
    checks.append(_check("nested_probability_order_and_partition", nested_failures, applicable.height))

    expected_grades = nested.select(
        "player_id", "three_tier_expected_six_year_war", "model_player_type",
        "three_tier_model_fv_granular", "three_tier_model_fv_display",
    ).with_columns(
        pl.struct("three_tier_expected_six_year_war", "model_player_type")
        .map_elements(
            lambda row: model_fv_from_expected_war(
                float(row["three_tier_expected_six_year_war"]),
                str(row["model_player_type"]),
            ),
            return_dtype=pl.Float64,
        )
        .alias("expected_granular")
    ).with_columns(
        pl.col("expected_granular").map_elements(display_fv, return_dtype=pl.Int64)
        .alias("expected_display")
    )
    bad_grade = expected_grades.filter(
        (
            (pl.col("three_tier_model_fv_granular") - pl.col("expected_granular"))
            .abs()
            > TOLERANCE
        )
        | (pl.col("three_tier_model_fv_display") != pl.col("expected_display"))
    ).height
    checks.append(_check("war_to_fv_mapping_exact", bad_grade, nested.height))

    source_type_failures = nested.filter(
        ((pl.col("hitter_path_rows") > 0) & (pl.col("pitcher_path_rows") == 0)
         & (pl.col("model_player_type") != "hitter"))
        | ((pl.col("pitcher_path_rows") > 0) & (pl.col("hitter_path_rows") == 0)
           & (pl.col("model_player_type") != "pitcher"))
        | ((pl.col("pitcher_path_rows") == 0) & (pl.col("hitter_path_rows") == 0))
    ).height
    checks.append(_check("player_type_follows_available_path", source_type_failures, nested.height))

    duplicate_values = values.group_by("player_id").len().filter(pl.col("len") != 1).height
    interval_failures = values.filter(
        (pl.col("expected_remaining_war_lower") > pl.col("expected_remaining_war"))
        | (pl.col("expected_remaining_war") > pl.col("expected_remaining_war_upper"))
        | (pl.col("transferable_value_lower_dollars") > pl.col("transferable_value_dollars"))
        | (pl.col("transferable_value_dollars") > pl.col("transferable_value_upper_dollars"))
    ).height
    checks.append(_check("current_value_unique_player", duplicate_values, values.height))
    checks.append(_check("current_value_interval_order", interval_failures, values.height))

    return {
        "checks": checks,
        "passed": sum(check["status"] == "pass" for check in checks),
        "failed": sum(check["status"] == "fail" for check in checks),
    }
