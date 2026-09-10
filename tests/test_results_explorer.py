from datetime import datetime, timezone

import polars as pl

from universal_baseball.results_explorer import (
    build_explorer_payload,
    render_explorer_html,
)
from scripts.build_results_explorer import latest_common_date


def test_explorer_payload_joins_names_and_annual_paths() -> None:
    values = pl.DataFrame(
        {
            "checkpoint_id": ["current"],
            "as_of_at_utc": [datetime(2026, 9, 8, tzinfo=timezone.utc)],
            "player_id": [1],
            "organization_id": [135],
            "rights_state": ["controlled"],
            "calculation_status": ["available"],
            "expected_remaining_war": [3.0],
            "expected_remaining_war_lower": [2.0],
            "expected_remaining_war_upper": [4.0],
            "expected_remaining_cost_dollars": [1_000_000.0],
            "transferable_value_dollars": [20_000_000.0],
            "transferable_value_lower_dollars": [10_000_000.0],
            "transferable_value_upper_dollars": [30_000_000.0],
            "coverage_tier": ["integrated"],
        }
    )
    annual = pl.DataFrame(
        {
            "player_id": [1],
            "season": [2027],
            "projected_war_mean": [3.0],
            "projected_war_lower": [2.0],
            "projected_war_upper": [4.0],
            "control_status": ["pre_arbitration"],
            "salary_cost_dollars": [1_000_000.0],
            "discounted_contract_value_dollars": [20_000_000.0],
            "discounted_contract_value_lower_dollars": [10_000_000.0],
            "discounted_contract_value_upper_dollars": [30_000_000.0],
            "calculation_status": ["available"],
            "review_reason": [""],
        }
    )
    payload = build_explorer_payload(
        values, annual, pl.DataFrame({"player_id": [1], "player_name": ["A Player"]})
    )

    assert payload["meta"]["available_count"] == 1
    assert payload["players"][0]["name"] == "A Player"
    assert payload["players"][0]["team"] == "Padres"
    assert payload["players"][0]["years"][0]["season"] == 2027

    nested_values = values.with_columns(
        pl.lit(3.0).alias("expected_controlled_war"),
        pl.lit("nested_career_model_fv_pre_mlb_benchmark_value").alias(
            "value_method"
        ),
    )
    nested = build_explorer_payload(
        nested_values,
        annual,
        pl.DataFrame({"player_id": [1], "player_name": ["A Player"]}),
        pl.DataFrame(
            {
                "player_id": [1],
                "primary_position": ["C"],
                "three_tier_expected_workload": [1200.0],
                "conditional_war_rate": [3.0],
                "conditional_war_rate_unit": ["WAR per 600 PA"],
                "batting_runs_per_600": [2.0],
                "baserunning_runs_per_600": [0.0],
                "defense_runs_per_600": [0.0],
                "positional_runs_per_600": [12.5],
                "pitching_runs_above_average_per_800": [None],
                "workload_war_p10": [0.0],
                "workload_war_p50": [1.0],
                "workload_war_p90": [5.0],
                "workload_only_star_probability": [0.01],
            }
        ),
    )
    assert nested["players"][0]["is_pre_mlb_value"] is True
    assert nested["players"][0]["years"] == []
    assert nested["players"][0]["expected_workload"] == 1200.0
    assert nested["players"][0]["positional_runs_per_600"] == 12.5
    assert nested["players"][0]["workload_war_p90"] == 5.0


def test_rendered_explorer_is_portable_and_escapes_script_boundary() -> None:
    payload = {
        "meta": {"checkpoint": "test", "warning": "research"},
        "players": [{"name": "</script><script>alert(1)</script>"}],
    }
    rendered = render_explorer_html(payload)

    assert "__EXPLORER_DATA__" not in rendered
    assert "<\\/script><script>alert(1)<\\/script>" in rendered
    assert rendered.count('<script id="explorer-data"') == 1
    assert "Meaningful-role chance" in rendered
    assert "Established-role chance" in rendered


def test_latest_common_date_uses_only_complete_checkpoints(tmp_path) -> None:
    roots = tuple(tmp_path / name for name in ("values", "annual", "names"))
    for root in roots:
        (root / "2026-09-08").mkdir(parents=True)
    (roots[0] / "2026-09-09").mkdir()

    assert latest_common_date(roots) == "2026-09-08"
