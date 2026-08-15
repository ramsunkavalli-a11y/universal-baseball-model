from __future__ import annotations

import polars as pl

from universal_baseball.run_expectancy import (
    add_half_inning_boundaries,
    attach_re24,
    estimate_run_expectancy,
    run_expectancy_coverage,
)


def _row(
    *,
    game: int,
    inning: int,
    half: str,
    at_bat: int,
    transition: int,
    start_outs: int,
    end_outs: int,
    start_bases: int,
    end_bases: int,
    runs: int,
    start_score: int,
    end_score: int,
) -> dict:
    return {
        "game_pk": game,
        "inning": inning,
        "half_inning": half,
        "at_bat_index": at_bat,
        "transition_index": transition,
        "start_outs": start_outs,
        "end_outs": end_outs,
        "start_bases_code": start_bases,
        "end_bases_code": end_bases,
        "runs_scored": runs,
        "start_bat_score": start_score,
        "end_bat_score": end_score,
        "re24_state_event_candidate": True,
        "quality_flags_json": "[]",
    }


def _transitions() -> pl.DataFrame:
    rows = [
        # Complete half: one run scores.
        _row(game=1, inning=1, half="top", at_bat=0, transition=0,
             start_outs=0, end_outs=0, start_bases=0, end_bases=1,
             runs=0, start_score=0, end_score=0),
        _row(game=1, inning=1, half="top", at_bat=1, transition=0,
             start_outs=0, end_outs=1, start_bases=1, end_bases=1,
             runs=0, start_score=0, end_score=0),
        _row(game=1, inning=1, half="top", at_bat=2, transition=0,
             start_outs=1, end_outs=1, start_bases=1, end_bases=0,
             runs=1, start_score=0, end_score=1),
        _row(game=1, inning=1, half="top", at_bat=3, transition=0,
             start_outs=1, end_outs=2, start_bases=0, end_bases=0,
             runs=0, start_score=1, end_score=1),
        _row(game=1, inning=1, half="top", at_bat=4, transition=0,
             start_outs=2, end_outs=3, start_bases=0, end_bases=0,
             runs=0, start_score=1, end_score=1),
        # Incomplete walkoff/truncated half. It must not alter the RE estimator.
        _row(game=2, inning=9, half="bottom", at_bat=0, transition=0,
             start_outs=0, end_outs=0, start_bases=0, end_bases=1,
             runs=0, start_score=2, end_score=2),
        _row(game=2, inning=9, half="bottom", at_bat=1, transition=0,
             start_outs=0, end_outs=0, start_bases=1, end_bases=0,
             runs=1, start_score=2, end_score=3),
    ]
    return pl.DataFrame(rows)


def test_estimator_uses_only_three_out_completed_halves() -> None:
    matrix = estimate_run_expectancy(_transitions())
    lookup = {
        (row["start_outs"], row["start_bases_code"]): row
        for row in matrix.to_dicts()
    }

    # The incomplete half also starts 0 outs / empty with one remaining run. If
    # it leaked into the sample, state_sample_size would be 2 rather than 1.
    assert lookup[(0, 0)]["state_sample_size"] == 1
    assert lookup[(0, 0)]["run_expectancy"] == 1.0
    assert lookup[(0, 1)]["run_expectancy"] == 1.0
    assert lookup[(1, 1)]["run_expectancy"] == 1.0
    assert lookup[(1, 0)]["run_expectancy"] == 0.0
    assert lookup[(2, 0)]["run_expectancy"] == 0.0


def test_half_terminal_metadata_detects_walkoff_without_hardcoded_inning_rule() -> None:
    bounded = add_half_inning_boundaries(_transitions())
    walkoff = bounded.filter(
        (pl.col("game_pk") == 2) & pl.col("is_half_terminal_transition")
    ).to_dicts()[0]
    assert walkoff["half_completed_three_outs"] is False
    assert walkoff["half_final_outs"] == 0
    assert walkoff["half_final_bat_score"] == 3


def test_re24_telescopes_with_matrix_and_final_half_re_after_zero() -> None:
    transitions = _transitions()
    matrix = estimate_run_expectancy(transitions)
    result = attach_re24(transitions, matrix)

    complete = result.filter(pl.col("game_pk") == 1).sort("at_bat_index")
    assert complete.get_column("re24_available").to_list() == [True] * 5
    assert complete.get_column("re24").to_list() == [0.0] * 5

    # The walkoff's final state is 0 outs / empty, which has an RE estimate of
    # 1.0 in this toy matrix. The event still gets RE(after)=0 because the half
    # ended; otherwise the game-ending event would retain phantom future runs.
    walkoff = result.filter(
        (pl.col("game_pk") == 2) & pl.col("is_half_terminal_transition")
    ).to_dicts()[0]
    assert walkoff["run_expectancy_after"] == 0.0
    assert walkoff["re24_available"] is True


def test_grouped_environment_matrices_do_not_cross_contaminate() -> None:
    transitions = _transitions().with_columns(
        pl.when(pl.col("game_pk") == 1)
        .then(pl.lit("AAA-2025"))
        .otherwise(pl.lit("MLB-2025"))
        .alias("environment")
    )
    matrix = estimate_run_expectancy(
        transitions, group_columns=["environment"]
    )
    assert matrix.get_column("environment").unique().to_list() == ["AAA-2025"]


def test_missing_matrix_state_remains_explicitly_unavailable() -> None:
    transitions = _transitions()
    matrix = estimate_run_expectancy(transitions).filter(
        ~((pl.col("start_outs") == 0) & (pl.col("start_bases_code") == 1))
    )
    result = attach_re24(transitions, matrix)
    coverage = run_expectancy_coverage(result)
    assert coverage["re24_missing_count"] > 0
    assert coverage["re24_coverage_rate"] < 1.0
