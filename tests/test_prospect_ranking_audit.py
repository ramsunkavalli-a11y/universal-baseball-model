from universal_baseball.prospect_ranking_audit import (
    build_recent_pitcher_evidence,
    difference_reason,
    explain_player,
    issue_priority,
    review_flags,
)


def test_explanation_uses_model_baseball_components() -> None:
    row = {
        "model_rank": 7,
        "age_years": 20.0,
        "level_tier": "AA",
        "model_player_type": "hitter",
        "model_arrival_probability": 0.81,
        "model_meaningful_role_probability": 0.55,
        "conditional_skill_war_rate": 2.3,
        "skill_rate_unit": "600 PA",
        "expected_workload": 1400.0,
        "expected_six_year_war": 4.1,
        "batting_runs_per_600": 5.0,
        "baserunning_runs_per_600": 1.0,
        "defense_runs_per_600": 0.0,
        "positional_runs_per_600": 2.0,
    }

    explanation = explain_player(row)

    assert "Age 20 at AA" in explanation
    assert "81% six-year MLB chance" in explanation
    assert "2.30 conditional WAR per 600 PA" in explanation
    assert "public" not in explanation.lower()


def test_review_flags_missing_and_large_difference() -> None:
    missing = review_flags({"source_rank": 3, "player_id": None, "model_rank": None})
    assert missing == [
        "source_identity_unmatched",
        "missing_from_model_prospect_pool",
    ]

    complete = {
        "source_rank": 2,
        "player_id": 123,
        "model_rank": 80,
        "age_years": 20.0,
        "level_tier": "AA",
        "model_arrival_probability": 0.8,
        "model_meaningful_role_probability": 0.5,
        "conditional_skill_war_rate": 2.0,
        "expected_workload": 1200.0,
        "expected_six_year_war": 3.0,
        "skill_reliability": 0.5,
        "skill_evidence_tier": "affiliated_history",
    }
    assert review_flags(complete) == ["large_external_rank_difference"]


def test_review_flags_position_value_dominating_weak_offense() -> None:
    row = {
        "model_rank": 20,
        "model_player_type": "hitter",
        "age_years": 22.0,
        "level_tier": "AAA",
        "model_arrival_probability": 0.8,
        "model_meaningful_role_probability": 0.5,
        "conditional_skill_war_rate": 2.0,
        "expected_workload": 900.0,
        "expected_six_year_war": 2.0,
        "position_war_contribution": 0.8,
        "batting_runs_per_600": -4.0,
    }

    assert review_flags(row) == ["position_value_dominant"]


def test_graduated_player_is_an_eligibility_difference_not_missing_data() -> None:
    row = {
        "source_rank": 4,
        "player_id": 456,
        "model_rank": None,
        "comparison_status": "graduated_to_mlb",
    }

    assert review_flags(row) == []
    assert "MLB pool" in explain_player(row)


def test_pitcher_explanation_exposes_basic_component_rates() -> None:
    row = {
        "model_rank": 12,
        "age_years": 21.0,
        "level_tier": "AA",
        "model_player_type": "pitcher",
        "model_arrival_probability": 0.9,
        "model_meaningful_role_probability": 0.6,
        "conditional_skill_war_rate": 1.2,
        "skill_rate_unit": "800 BF",
        "expected_workload": 900.0,
        "expected_six_year_war": 1.4,
        "pitching_runs_above_average_per_800": -6.0,
        "predicted_so_rate": 0.25,
        "predicted_ubb_rate": 0.08,
        "predicted_hr_rate": 0.03,
    }

    explanation = explain_player(row)

    assert "projected K/BB/HR rates: 25%/8%/3%" in explanation


def test_difference_reason_traces_pitcher_compression_without_using_public_grade() -> None:
    row = {
        "comparison_status": "source_top_50_model_lower",
        "model_rank": 400,
        "model_player_type": "pitcher",
        "conditional_skill_war_rate": 0.4,
        "skill_reliability": 0.35,
        "level_tier": "AA",
        "model_arrival_probability": 0.9,
        "model_meaningful_role_probability": 0.7,
    }

    assert difference_reason(row) == (
        "Model lower: translated pitcher run rate is weak"
    )


def test_difference_reason_identifies_advanced_level_model_preference() -> None:
    row = {
        "comparison_status": "model_top_50_only",
        "model_rank": 10,
        "model_player_type": "hitter",
        "level_tier": "AAA",
        "model_arrival_probability": 0.95,
    }

    assert difference_reason(row) == (
        "Model higher: advanced level and high MLB arrival chance"
    )


def test_issue_priority_turns_repeated_reasons_into_roadmap() -> None:
    assert issue_priority(
        "Model lower: translated pitcher run rate is weak"
    ) == "P0 pitcher translation"
    assert issue_priority(
        "Model higher: premium-position value offsets limited offense"
    ) == "P0 position persistence"


def test_recent_pitcher_evidence_keeps_raw_rates_unadjusted() -> None:
    import polars as pl

    history = pl.DataFrame(
        {
            "season": [2023, 2024, 2025, 2026, 2026],
            "player_id": [1, 1, 1, 1, 2],
            "level_group": ["AA", "AA", "AAA", "AA", "MLB"],
            "batters_faced": [100, 100, 200, 100, 100],
            "strike_outs": [100, 20, 60, 40, 100],
            "base_on_balls": [0, 10, 20, 5, 0],
            "intentional_walks": [0, 1, 2, 0, 0],
            "home_runs": [0, 3, 4, 3, 0],
        }
    )

    result = build_recent_pitcher_evidence(history, current_season=2026)

    assert result.height == 1
    assert result.item(0, "raw_pitcher_bf") == 400
    assert result.item(0, "raw_pitcher_so_rate") == 0.30
    assert result.item(0, "raw_pitcher_ubb_rate") == 0.08
    assert result.item(0, "raw_pitcher_hr_rate") == 0.025
