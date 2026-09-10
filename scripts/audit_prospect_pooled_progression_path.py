#!/usr/bin/env python3
"""Test pooled post-arrival hazards after the full transition path reversed."""

from __future__ import annotations

import json
from pathlib import Path

from audit_prospect_ordered_transition_path import (
    C_GRID,
    _data,
    _scores,
    _transition_training,
)

from universal_baseball.prospect_career_state import (
    career_state_scores,
    fit_transition_hazard_model,
    predict_transition_path,
)


OUTPUT_JSON = Path("docs/prospect-pooled-progression-path-result.json")
OUTPUT_MD = Path("docs/prospect-pooled-progression-path-result.md")


def _pooled_score(data, *, player_type: str, c: float, evaluation_year: int):
    fit = fit_transition_hazard_model(
        _transition_training(data[2018], 2018),
        player_type=player_type, feature_set="level_exposure",
        regularization_c=c, progression_mode="pooled",
    )
    prediction = predict_transition_path(
        fit, data[evaluation_year][1], horizon=4
    ).join(
        data[evaluation_year][4].select(
            "player_id", "arrived_within_horizon",
            "meaningful_role_within_horizon", "established_role_within_horizon",
        ), on="player_id", validate="1:1", suffix="_target",
    ).drop(
        "arrived_within_horizon", "meaningful_role_within_horizon",
        "established_role_within_horizon",
    ).rename({
        "arrived_within_horizon_target": "arrived_within_horizon",
        "meaningful_role_within_horizon_target": "meaningful_role_within_horizon",
        "established_role_within_horizon_target": "established_role_within_horizon",
    })
    return career_state_scores(prediction)


def _one(player_type: str) -> dict[str, object]:
    data = _data(player_type)
    development = {
        "direct": {
            str(c): _scores(
                data, player_type=player_type, method="direct_endpoint",
                regularization_c=c, evaluation_year=2019,
            ) for c in C_GRID
        },
        "pooled_transition": {
            str(c): _pooled_score(
                data, player_type=player_type, c=c, evaluation_year=2019
            ) for c in C_GRID
        },
    }
    selected = {
        method: min(
            C_GRID,
            key=lambda c: development[method][str(c)]["multiclass_log_loss"],
        ) for method in development
    }
    selected_development = {
        method: development[method][str(selected[method])] for method in development
    }
    confirmation = {
        "direct": _scores(
            data, player_type=player_type, method="direct_endpoint",
            regularization_c=selected["direct"], evaluation_year=2021,
        ),
        "pooled_transition": _pooled_score(
            data, player_type=player_type, c=selected["pooled_transition"],
            evaluation_year=2021,
        ),
    }
    def deltas(values):
        return {
            "log_loss": values["pooled_transition"]["multiclass_log_loss"]
            - values["direct"]["multiclass_log_loss"],
            "brier": values["pooled_transition"]["multiclass_brier"]
            - values["direct"]["multiclass_brier"],
        }
    return {
        "selected_regularization": selected,
        "development_grid": development,
        "development_delta": deltas(selected_development),
        "confirmation": confirmation,
        "confirmation_delta": deltas(confirmation),
    }


def main() -> int:
    report = {
        "report_schema_version": "0.1",
        "status": "pooled_post_arrival_progression_test_complete",
        "design": (
            "full level/exposure design for NO_MLB transitions; only age and elapsed "
            "time for FRINGE_MLB and MEANINGFUL_MLB advancement"
        ),
        "hitter": _one("hitter"), "pitcher": _one("pitcher"),
        "current_2026_used": False, "production_changed": False,
        "promotion_allowed": False,
        "promotion_boundary": (
            "The rationale is predeclared from support counts, but the 2021 comparison "
            "was already disclosed by the prior full-transition audit."
        ),
    }
    OUTPUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    def line(name: str) -> str:
        value = report[name]
        return (
            f"| {name.title()} | {value['development_delta']['log_loss']:+.6f} | "
            f"{value['development_delta']['brier']:+.6f} | "
            f"{value['confirmation_delta']['log_loss']:+.6f} | "
            f"{value['confirmation_delta']['brier']:+.6f} |"
        )
    OUTPUT_MD.write_text(f"""# Pooled post-arrival prospect progression

Status: research-only sensitivity; promotion is not allowed from this test.

The full level/exposure model remains on the no-MLB arrival transition. Once a player
has reached fringe or meaningful MLB status, the challenger uses only age and elapsed
time. This follows the measured small progression risk sets and avoids pretending old
minor-league rates remain rich MLB-role evidence. Negative deltas are better.

| Group | 2019 log-loss delta | 2019 Brier delta | 2021 log-loss delta | 2021 Brier delta |
|---|---:|---:|---:|---:|
{line('hitter')}
{line('pitcher')}

Regularization was selected on the 2019 cohort. This cannot be promoted regardless
of result because the 2021 cohort was disclosed by the preceding transition audit.
It determines only whether pooled progression deserves a future confirmation.
""", encoding="utf-8")
    print(json.dumps({name: report[name] for name in ("hitter", "pitcher")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
