from pathlib import Path

import polars as pl
import pytest

from universal_baseball.hitter_v2_evaluation import score_nested_component_log_loss
from universal_baseball.hitter_v2_model import NESTED_NODES
from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES
from universal_baseball.hitter_v2_stage2f import (
    LEVELS,
    fit_reference_level_translations,
    probability_links,
    wrap_reference_level_probabilities,
)
from universal_baseball.hitter_v2_stage2f_selection import (
    aggregate_training_origin_target,
    backtranslate_predictions_to_scoring_level,
    nested_selection_scores,
    select_surface_configuration,
)


ROOT = Path(__file__).resolve().parents[1]


def _counts(**updates: int) -> dict[str, int]:
    values = {outcome: 0 for outcome in HITTER_TALENT_OUTCOMES}
    values.update(
        {
            "K": 20,
            "UBB": 10,
            "HBP": 2,
            "HR": 5,
            "1B": 15,
            "2B": 5,
            "3B": 1,
            "ROE": 2,
            "FC_REACH": 2,
            "SF": 3,
            "MULTI_OUT": 4,
            "OTHER_OUT": 31,
        }
    )
    values.update(updates)
    return values


def _training() -> pl.DataFrame:
    rows = []
    for player_id, season, counts in (
        (1, 2021, _counts()),
        (1, 2022, _counts(HR=10, OTHER_OUT=26)),
        (2, 2022, _counts(**{"1B": 20, "OTHER_OUT": 26})),
    ):
        rows.append(
            {
                "player_id": player_id,
                "season": season,
                "league_id": 103,
                "level_group": "MLB",
                "hitter_talent_pa": sum(counts.values()),
                "modeling_eligible": True,
                **counts,
            }
        )
    return pl.DataFrame(rows)


def test_origin_target_uses_only_players_with_strictly_prior_history() -> None:
    target = aggregate_training_origin_target(
        _training(), origin_season=2022, eligible_player_ids={1}
    )

    assert target["player_id"].to_list() == [1]
    assert target["HR"].item() == 10
    assert target["hitter_talent_pa"].item() == sum(_counts().values())


def test_origin_target_rejects_later_outer_history() -> None:
    with pytest.raises(ValueError, match="later outer-history"):
        aggregate_training_origin_target(
            _training().with_columns(
                pl.when(pl.col("season") == 2022)
                .then(2023)
                .otherwise(pl.col("season"))
                .alias("season")
            ),
            origin_season=2022,
            eligible_player_ids={1},
        )


def test_surface_tie_rule_prefers_larger_shrinkage() -> None:
    scores = pl.DataFrame(
        {
            "translation_prior_mover_pa": [250.0, 1000.0, 1000.0],
            "development_prior_sd": [0.05, 0.1, 0.05],
            "calibration_prior_sd": [0.1, 0.1, 0.1],
            "event_log_loss": [1.0, 1.0 + 5e-9, 1.0 + 5e-9],
        }
    )
    selected = select_surface_configuration(scores)

    assert selected["translation_prior_mover_pa"] == 1000.0
    assert selected["development_prior_sd"] == 0.05
    assert selected["calibration_prior_sd"] == 0.1


def test_nested_selection_score_uses_only_joined_prior_history_players() -> None:
    probabilities = {outcome: value / 100.0 for outcome, value in _counts().items()}
    predictions = pl.DataFrame(
        {
            "player_id": [1],
            **{
                f"p_{outcome}": [probabilities[outcome]]
                for outcome in HITTER_TALENT_OUTCOMES
            },
        }
    )
    target = aggregate_training_origin_target(
        _training(), origin_season=2022, eligible_player_ids={1}
    )
    rows, aggregate, events = nested_selection_scores(predictions, target)

    assert len(rows) == 9
    assert aggregate > 0.0
    assert events > 0
    for row, node in zip(rows, NESTED_NODES, strict=True):
        expected = score_nested_component_log_loss(
            predictions, target, component=node.name
        )
        assert row["events"] == expected["events"]
        assert row["event_log_loss"] == pytest.approx(
            expected["event_log_loss"], abs=1e-14
        )


def test_selection_runner_cannot_load_disclosed_validation_tables() -> None:
    source = (ROOT / "scripts/select_hitter_v2_stage2f_H0.py").read_text(
        encoding="utf-8"
    )

    assert "target_player_league_seasons.parquet" not in source
    assert "target_players.parquet" not in source
    assert "evaluation_players.parquet" not in source
    assert "score_hitter_v2_stage2_final_validation" not in source
    assert "protected_2026" in source


def test_reference_prediction_backtranslation_preserves_fixed_raw_target() -> None:
    probabilities = {outcome: value / 100.0 for outcome, value in _counts().items()}
    rows = []
    for component in probability_links(probabilities):
        for origin, destination in zip(LEVELS[:-1], LEVELS[1:], strict=True):
            rows.append(
                {
                    "component": component,
                    "origin_level": origin,
                    "destination_level": destination,
                    "age": 22.0,
                    "link_delta": 0.03,
                    "mover_pa": 500.0,
                    "origin_season": 2020,
                    "destination_season": 2021,
                }
            )
    translation = fit_reference_level_translations(
        pl.DataFrame(rows),
        predictor_cutoff_season=2021,
        prior_mover_pa=250.0,
    )
    reference = wrap_reference_level_probabilities(
        probabilities, observed_level="AA", translation=translation
    ).probabilities
    predictions = pl.DataFrame(
        {
            "player_id": [1],
            **{
                f"p_{outcome}": [reference[outcome]]
                for outcome in HITTER_TALENT_OUTCOMES
            },
        }
    )
    target = pl.DataFrame(
        {
            "player_id": [1],
            "level_group": ["AA"],
            "hitter_talent_pa": [100.0],
            **{
                outcome: [float(_counts()[outcome])]
                for outcome in HITTER_TALENT_OUTCOMES
            },
        }
    )
    scoring = backtranslate_predictions_to_scoring_level(
        predictions, target, translation
    ).row(0, named=True)

    for outcome in HITTER_TALENT_OUTCOMES:
        assert scoring[f"p_{outcome}"] == pytest.approx(
            probabilities[outcome], abs=1e-12
        )
