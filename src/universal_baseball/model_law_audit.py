"""Structural and statistical-law checks for the private playable preview."""

from __future__ import annotations

from typing import Any

import polars as pl

from universal_baseball.prospect_value import display_fv, model_fv_from_expected_war


TOLERANCE = 1e-8
DOLLAR_TOLERANCE = 1e-5


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


def _invalid_simplex(frame: pl.DataFrame, columns: tuple[str, ...]) -> int:
    invalid_member = pl.any_horizontal(
        pl.col(column).is_null()
        | ~pl.col(column).is_finite()
        | (pl.col(column) < 0.0)
        | (pl.col(column) > 1.0)
        for column in columns
    )
    invalid_sum = (
        pl.sum_horizontal(*columns).is_null()
        | ~pl.sum_horizontal(*columns).is_finite()
        | ((pl.sum_horizontal(*columns) - 1.0).abs() > TOLERANCE)
    )
    return frame.filter(invalid_member | invalid_sum).height


def audit_contract_economics_laws(annual: pl.DataFrame) -> list[dict[str, Any]]:
    """Check accounting identities and legal-decision boundaries on annual value rows."""

    required = {
        "player_id", "organization_id", "season", "projected_war_mean",
        "projected_war_lower", "projected_war_upper", "control_status",
        "dollars_per_war", "fa_equivalent_value_dollars", "salary_cost_dollars",
        "static_surplus_dollars", "contract_control_value_dollars",
        "optionality_premium_dollars", "contract_value_lower_dollars",
        "contract_value_upper_dollars", "discount_factor",
        "discounted_contract_value_dollars", "decision_at_mean",
        "calculation_status",
    }
    if missing := sorted(required - set(annual.columns)):
        raise ValueError(f"annual contract economics missing fields: {missing}")
    checks: list[dict[str, Any]] = []
    duplicates = (
        annual.group_by("player_id", "organization_id", "season")
        .len()
        .filter(pl.col("len") != 1)
        .height
    )
    checks.append(_check("contract_unique_player_team_season", duplicates, annual.height))

    numeric_outputs = (
        "dollars_per_war", "fa_equivalent_value_dollars", "salary_cost_dollars",
        "static_surplus_dollars", "contract_control_value_dollars",
        "optionality_premium_dollars", "contract_value_lower_dollars",
        "contract_value_upper_dollars", "discount_factor",
        "discounted_contract_value_dollars",
    )
    available = annual.filter(pl.col("calculation_status") == "available")
    review = annual.filter(pl.col("calculation_status") != "available")
    invalid_available = available.filter(
        pl.any_horizontal(
            pl.col(column).is_null() | ~pl.col(column).is_finite()
            for column in numeric_outputs
        )
    ).height
    decision_outputs = (
        "salary_cost_dollars", "static_surplus_dollars",
        "contract_control_value_dollars", "optionality_premium_dollars",
        "contract_value_lower_dollars", "contract_value_upper_dollars",
        "discounted_contract_value_dollars",
    )
    populated_review = review.filter(
        pl.any_horizontal(pl.col(column).is_not_null() for column in decision_outputs)
    ).height
    checks.append(
        _check("contract_available_outputs_finite", invalid_available, available.height)
    )
    checks.append(
        _check("contract_review_outputs_fail_closed", populated_review, review.height)
    )

    accounting_failures = available.filter(
        (
            (
                pl.max_horizontal(pl.col("projected_war_mean"), pl.lit(0.0))
                * pl.col("dollars_per_war")
                - pl.col("fa_equivalent_value_dollars")
            ).abs() > DOLLAR_TOLERANCE
        )
        | (
            (
                pl.col("static_surplus_dollars")
                + pl.col("optionality_premium_dollars")
                - pl.col("contract_control_value_dollars")
            ).abs() > DOLLAR_TOLERANCE
        )
        | (
            (
                pl.col("contract_control_value_dollars") * pl.col("discount_factor")
                - pl.col("discounted_contract_value_dollars")
            ).abs() > DOLLAR_TOLERANCE
        )
        | (pl.col("discount_factor") <= 0.0)
        | (pl.col("discount_factor") > 1.0)
    ).height
    interval_failures = available.filter(
        (pl.col("projected_war_lower") > pl.col("projected_war_mean"))
        | (pl.col("projected_war_mean") > pl.col("projected_war_upper"))
        | (pl.col("contract_value_lower_dollars") > pl.col("contract_control_value_dollars"))
        | (pl.col("contract_control_value_dollars") > pl.col("contract_value_upper_dollars"))
    ).height
    checks.append(
        _check("contract_value_accounting_identities", accounting_failures, available.height)
    )
    checks.append(
        _check("contract_annual_interval_order", interval_failures, available.height)
    )

    allowed_decisions = {
        "current_season_committed": {"current_season_committed"},
        "pre_arbitration": {"tender", "non_tender"},
        "arbitration": {"tender", "non_tender"},
        "arbitration_eligible": {"tender", "non_tender"},
        "super_two_eligible": {"tender", "non_tender"},
        "club_option": {"exercise_club_option", "decline_club_option"},
        "player_option": {"player_stays", "player_leaves"},
        "player_opt_out": {"player_stays", "player_leaves"},
        "mutual_option": {"decline_mutual_option"},
        "guaranteed_contract": {"guaranteed"},
        "free_agent": {"no_incumbent_rights"},
        "free_agent_eligible": {"no_incumbent_rights"},
    }
    decision_failures = sum(
        str(row["decision_at_mean"])
        not in (
            allowed_decisions.get(str(row["control_status"]), set())
            | {"prior_non_tender_no_incumbent_rights"}
        )
        for row in available.iter_rows(named=True)
    )
    ended_rights_failures = available.filter(
        (pl.col("decision_at_mean") == "prior_non_tender_no_incumbent_rights")
        & pl.any_horizontal(
            pl.col(column).abs() > DOLLAR_TOLERANCE
            for column in (
                "salary_cost_dollars", "static_surplus_dollars",
                "contract_control_value_dollars", "optionality_premium_dollars",
                "contract_value_lower_dollars", "contract_value_upper_dollars",
                "discounted_contract_value_dollars",
            )
        )
    ).height
    free_agent_failures = available.filter(
        pl.col("control_status").is_in(["free_agent", "free_agent_eligible"])
        & (
            (pl.col("salary_cost_dollars").abs() > TOLERANCE)
            | (pl.col("contract_control_value_dollars").abs() > TOLERANCE)
            | (pl.col("optionality_premium_dollars").abs() > TOLERANCE)
        )
    ).height
    checks.append(
        _check("contract_decision_matches_rights_state", decision_failures, available.height)
    )
    checks.append(
        _check("prior_non_tender_ends_later_rights", ended_rights_failures, available.height)
    )
    checks.append(
        _check("free_agent_has_no_incumbent_value", free_agent_failures, available.height)
    )
    return checks


def audit_projection_statistical_laws(
    frame: pl.DataFrame, *, player_type: str
) -> list[dict[str, Any]]:
    """Check the evidence shrinkage, aging and neutrality rules of a WAR path."""

    if player_type not in {"hitter", "pitcher"}:
        raise ValueError("player_type must be hitter or pitcher")
    evidence_column = (
        "weighted_history_pa" if player_type == "hitter" else "weighted_history_bf"
    )
    required = {
        "player_id", "season", "target_age", "reliability", evidence_column,
        "posterior_concentration", "event_run_variance",
        "posterior_run_rate_variance", "uses_current_team_depth",
    }
    if missing := sorted(required - set(frame.columns)):
        raise ValueError(f"{player_type} statistical path missing fields: {missing}")

    reliability_failures = frame.filter(
        pl.col("reliability").is_null()
        | ~pl.col("reliability").is_finite()
        | (pl.col("reliability") < 0.0)
        | (pl.col("reliability") > 1.0)
    ).height
    evidence_failures = frame.filter(
        pl.col(evidence_column).is_null()
        | ~pl.col(evidence_column).is_finite()
        | (pl.col(evidence_column) < 0.0)
        | pl.col("posterior_concentration").is_null()
        | ~pl.col("posterior_concentration").is_finite()
        | (pl.col("posterior_concentration") <= 0.0)
        | (
            (pl.col("reliability") > 0.0)
            & (
                (
                    pl.col("posterior_concentration")
                    - pl.col(evidence_column) / pl.col("reliability")
                ).abs()
                > TOLERANCE
            )
        )
        | (
            (pl.col("reliability") == 0.0)
            & (pl.col(evidence_column).abs() > TOLERANCE)
        )
    ).height
    uncertainty_failures = frame.filter(
        pl.col("event_run_variance").is_null()
        | ~pl.col("event_run_variance").is_finite()
        | (pl.col("event_run_variance") < 0.0)
        | pl.col("posterior_run_rate_variance").is_null()
        | ~pl.col("posterior_run_rate_variance").is_finite()
        | (pl.col("posterior_run_rate_variance") < 0.0)
        | (
            (
                pl.col("posterior_run_rate_variance")
                - pl.col("event_run_variance")
                / (pl.col("posterior_concentration") + 1.0)
            ).abs()
            > TOLERANCE
        )
    ).height
    age_failures = (
        frame.with_columns((pl.col("target_age") - pl.col("season")).alias("age_offset"))
        .group_by("player_id")
        .agg(
            pl.col("age_offset").n_unique().alias("offsets"),
            pl.col("target_age").null_count().alias("null_ages"),
            pl.len().alias("rows"),
        )
        .filter(
            (pl.col("offsets") > 1)
            | (
                (pl.col("null_ages") != 0)
                & (pl.col("null_ages") != pl.col("rows"))
            )
        )
        .height
    )
    depth_failures = frame.filter(
        pl.col("uses_current_team_depth").is_null()
        | pl.col("uses_current_team_depth")
    ).height
    checks = [
        _check(f"{player_type}_reliability_bounds", reliability_failures, frame.height),
        _check(
            f"{player_type}_evidence_concentration_identity",
            evidence_failures,
            frame.height,
        ),
        _check(
            f"{player_type}_posterior_variance_identity",
            uncertainty_failures,
            frame.height,
        ),
        _check(
            f"{player_type}_age_advances_one_per_season",
            age_failures,
            frame.get_column("player_id").n_unique(),
        ),
        _check(f"{player_type}_team_depth_neutral", depth_failures, frame.height),
    ]
    if player_type == "pitcher":
        if "aging_source" not in frame.columns:
            raise ValueError("pitcher statistical path missing aging_source")
        aging_failures = frame.filter(
            pl.col("aging_source") != "tango_adjacent_pitching_regressed_part2"
        ).height
        checks.append(
            _check("pitcher_tango_aging_source", aging_failures, frame.height)
        )
    return checks


def audit_private_preview_laws(
    hitter_paths: pl.DataFrame,
    pitcher_paths: pl.DataFrame,
    nested: pl.DataFrame,
    values: pl.DataFrame,
    *,
    runs_per_win: float | None = None,
    annual_contract_economics: pl.DataFrame | None = None,
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

        workload_columns = (
            ("conditional_mlb_pa", "conditional_mlb_pa_variance", "expected_mlb_pa")
            if player_type == "hitter"
            else ("conditional_mlb_bf", "conditional_mlb_bf_variance", "expected_mlb_bf")
        )
        invalid_workload = frame.filter(
            pl.any_horizontal(
                pl.col(column).is_null()
                | ~pl.col(column).is_finite()
                | (pl.col(column) < 0.0)
                for column in workload_columns
            )
        ).height
        checks.append(
            _check(
                f"{player_type}_finite_nonnegative_opportunity",
                invalid_workload,
                frame.height,
            )
        )
        checks.append(
            _check(
                f"{player_type}_active_probability_bounds",
                _outside_unit_interval(frame, ("mlb_active_probability",)),
                frame.height,
            )
        )
        statistical_fields = {
            "target_age", "reliability", "posterior_concentration",
            "event_run_variance", "posterior_run_rate_variance",
            "uses_current_team_depth",
            "weighted_history_pa" if player_type == "hitter" else "weighted_history_bf",
        }
        if statistical_fields <= set(frame.columns):
            checks.extend(
                audit_projection_statistical_laws(frame, player_type=player_type)
            )

    hitter_component_columns = (
        "predicted_ubb_rate", "predicted_hbp_rate", "predicted_single_rate",
        "predicted_double_rate", "predicted_triple_rate", "predicted_hr_rate",
        "predicted_other_rate",
    )
    hitter_bad_components = _invalid_simplex(hitter_paths, hitter_component_columns)
    checks.append(_check("hitter_component_simplex", hitter_bad_components, hitter_paths.height))

    pitcher_component_columns = (
        "predicted_other_rate", "predicted_so_rate", "predicted_ubb_rate",
        "predicted_hbp_rate", "predicted_hr_rate",
    )
    pitcher_bad_components = _invalid_simplex(pitcher_paths, pitcher_component_columns)
    checks.append(_check("pitcher_component_simplex", pitcher_bad_components, pitcher_paths.height))

    role_columns = (
        "starter_probability_if_active", "swingman_probability_if_active",
        "reliever_probability_if_active",
    )
    pitcher_bad_roles = _invalid_simplex(pitcher_paths, role_columns)
    checks.append(_check("pitcher_role_probability_simplex", pitcher_bad_roles, pitcher_paths.height))

    for player_type, frame, conditional, expected, denominator, rate in (
        ("hitter", hitter_paths, "conditional_mlb_pa", "expected_mlb_pa", 600.0,
         "conditional_war_per_600_pa"),
        ("pitcher", pitcher_paths, "conditional_mlb_bf", "expected_mlb_bf", 800.0,
         "conditional_war_per_800_bf"),
    ):
        bad_workload = frame.filter(
            pl.col(expected).is_null()
            | ~pl.col(expected).is_finite()
            | (
                (
                    pl.col(expected)
                    - pl.col("mlb_active_probability") * pl.col(conditional)
                ).abs()
                > TOLERANCE
            )
        ).height
        bad_war = frame.filter(
            pl.col(rate).is_null()
            | ~pl.col(rate).is_finite()
            | pl.col("expected_war").is_null()
            | ~pl.col("expected_war").is_finite()
            | (
                (
                    pl.col("expected_war")
                    - pl.col(rate) * pl.col(expected) / denominator
                ).abs()
                > TOLERANCE
            )
        ).height
        checks.append(_check(f"{player_type}_expected_workload_identity", bad_workload, frame.height))
        checks.append(_check(f"{player_type}_expected_war_identity", bad_war, frame.height))

        if {"is_controlled_season", "controlled_expected_war"} <= set(frame.columns):
            control_presence_failures = frame.filter(
                pl.col("is_controlled_season").is_null()
                != pl.col("controlled_expected_war").is_null()
            ).height
            known_control = frame.filter(pl.col("is_controlled_season").is_not_null())
            controlled_failures = known_control.filter(
                pl.col("controlled_expected_war").is_null()
                | ~pl.col("controlled_expected_war").is_finite()
                | (
                    (
                        pl.col("controlled_expected_war")
                        - pl.when(pl.col("is_controlled_season"))
                        .then(pl.col("expected_war"))
                        .otherwise(0.0)
                    ).abs() > TOLERANCE
                )
            ).height
            checks.append(
                _check(
                    f"{player_type}_controlled_war_identity",
                    controlled_failures,
                    known_control.height,
                )
            )
            checks.append(
                _check(
                    f"{player_type}_unknown_control_preserved",
                    control_presence_failures,
                    frame.height,
                )
            )

    if runs_per_win is not None:
        if not 0.0 < float(runs_per_win) < float("inf"):
            raise ValueError("runs_per_win must be finite and positive")
        hitter_runs = pl.sum_horizontal(
            "batting_runs_per_600", "baserunning_runs_per_600",
            "defense_runs_per_600", "positional_runs_per_600",
            "replacement_runs_per_600",
        )
        hitter_component_failures = hitter_paths.filter(
            (hitter_runs / float(runs_per_win) - pl.col("conditional_war_per_600_pa")).abs()
            > TOLERANCE
        ).height
        pitcher_component_failures = pitcher_paths.filter(
            (
                (
                    pl.col("pitching_runs_above_average_per_800")
                    + pl.col("replacement_runs_per_800")
                ) / float(runs_per_win)
                - pl.col("conditional_war_per_800_bf")
            ).abs() > TOLERANCE
        ).height
        checks.append(
            _check("hitter_component_to_war_identity", hitter_component_failures, hitter_paths.height)
        )
        checks.append(
            _check("pitcher_component_to_war_identity", pitcher_component_failures, pitcher_paths.height)
        )

    applicable = nested.filter(pl.col("ordered_arrival_probability").is_not_null())
    nested_probability_columns = (
        "ordered_arrival_probability",
        "ordered_meaningful_probability",
        "ordered_established_probability",
        "established_probability",
        "meaningful_only_probability",
        "fringe_probability",
    )
    nested_failures = applicable.filter(
        pl.any_horizontal(
            pl.col(column).is_null()
            | ~pl.col(column).is_finite()
            | (pl.col(column) < 0.0)
            | (pl.col(column) > 1.0)
            for column in nested_probability_columns
        )
        | (pl.col("ordered_arrival_probability") < pl.col("ordered_meaningful_probability"))
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
    available_values = (
        values.filter(pl.col("calculation_status") == "available")
        if "calculation_status" in values.columns
        else values
    )
    war_bounds_present = pl.col("expected_remaining_war_lower").is_not_null()
    value_bounds_present = pl.col("transferable_value_lower_dollars").is_not_null()
    incomplete_intervals = available_values.filter(
        (
            pl.col("expected_remaining_war_lower").is_null()
            != pl.col("expected_remaining_war_upper").is_null()
        )
        | (
            pl.col("transferable_value_lower_dollars").is_null()
            != pl.col("transferable_value_upper_dollars").is_null()
        )
        | (war_bounds_present != value_bounds_present)
    ).height
    bounded_values = available_values.filter(war_bounds_present & value_bounds_present)
    interval_failures = bounded_values.filter(
        pl.any_horizontal(
            pl.col(column).is_null() | ~pl.col(column).is_finite()
            for column in (
                "expected_remaining_war_lower",
                "expected_remaining_war",
                "expected_remaining_war_upper",
                "transferable_value_lower_dollars",
                "transferable_value_dollars",
                "transferable_value_upper_dollars",
            )
        )
        | (pl.col("expected_remaining_war_lower") > pl.col("expected_remaining_war"))
        | (pl.col("expected_remaining_war") > pl.col("expected_remaining_war_upper"))
        | (pl.col("transferable_value_lower_dollars") > pl.col("transferable_value_dollars"))
        | (pl.col("transferable_value_dollars") > pl.col("transferable_value_upper_dollars"))
    ).height
    checks.append(_check("current_value_unique_player", duplicate_values, values.height))
    checks.append(
        _check(
            "current_value_interval_completeness",
            incomplete_intervals,
            available_values.height,
        )
    )
    checks.append(
        _check("current_value_interval_order", interval_failures, bounded_values.height)
    )

    if annual_contract_economics is not None:
        checks.extend(audit_contract_economics_laws(annual_contract_economics))

    return {
        "checks": checks,
        "passed": sum(check["status"] == "pass" for check in checks),
        "failed": sum(check["status"] == "fail" for check in checks),
    }
