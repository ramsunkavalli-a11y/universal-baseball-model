from universal_baseball.prospect_ranking_audit import explain_player, review_flags


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
