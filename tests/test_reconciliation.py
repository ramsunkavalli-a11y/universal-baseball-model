from __future__ import annotations

import polars as pl

from universal_baseball.reconciliation import (
    aggregate_pa_batting,
    compare_batting_lines,
    profile_pa_event_types,
)


def _pa_frame() -> pl.DataFrame:
    away_events = [
        "single",
        "double",
        "home_run",
        "walk",
        "intent_walk",
        "hit_by_pitch",
        "strikeout",
        "sac_fly",
        "sac_bunt",
        "catcher_interf",
        "field_out",
    ]
    home_events = ["triple", "field_error", "strikeout_double_play", "field_out"]
    return pl.DataFrame(
        {
            "game_pk": ["1"] * (len(away_events) + len(home_events)),
            "batting_side": ["away"] * len(away_events)
            + ["home"] * len(home_events),
            "event_type": away_events + home_events,
            "result_type": ["atBat"] * (len(away_events) + len(home_events)),
        }
    )


def test_aggregate_pa_batting_reconstructs_standard_accounting() -> None:
    result = aggregate_pa_batting(_pa_frame())
    away = result.filter(pl.col("batting_side") == "away").to_dicts()[0]
    home = result.filter(pl.col("batting_side") == "home").to_dicts()[0]

    assert away["plate_appearances"] == 11
    assert away["base_on_balls"] == 2
    assert away["intentional_walks"] == 1
    assert away["hit_by_pitch"] == 1
    assert away["sac_flies"] == 1
    assert away["sac_bunts"] == 1
    assert away["catchers_interference"] == 1
    assert away["at_bats"] == 5
    assert away["hits"] == 3
    assert away["doubles"] == 1
    assert away["triples"] == 0
    assert away["home_runs"] == 1
    assert away["strikeouts"] == 1

    assert home["plate_appearances"] == 4
    assert home["at_bats"] == 4
    assert home["hits"] == 1
    assert home["triples"] == 1
    assert home["strikeouts"] == 1


def test_compare_batting_lines_reports_exact_and_stat_level_mismatches() -> None:
    derived = aggregate_pa_batting(_pa_frame())
    official = derived.select(
        [
            "game_pk",
            "batting_side",
            "plate_appearances",
            "at_bats",
            "hits",
            "doubles",
            "triples",
            "home_runs",
            "base_on_balls",
            "intentional_walks",
            "hit_by_pitch",
            "strikeouts",
            "sac_bunts",
            "sac_flies",
            "catchers_interference",
        ]
    )

    exact = compare_batting_lines(derived, official)
    assert exact["all_reconciled"] is True
    assert exact["exact_match_line_count"] == 2
    assert exact["mismatch_line_count"] == 0

    changed = official.with_columns(
        pl.when(pl.col("batting_side") == "away")
        .then(pl.col("hits") + 1)
        .otherwise(pl.col("hits"))
        .alias("hits")
    )
    mismatch = compare_batting_lines(derived, changed)
    assert mismatch["all_reconciled"] is False
    assert mismatch["mismatch_line_count"] == 1
    assert mismatch["stat_mismatch_counts"] == {"hits": 1}
    assert mismatch["mismatch_rows"][0]["differences_derived_minus_official"]["hits"] == -1


def test_event_type_profile_keeps_structured_vocabulary_visible() -> None:
    frame = pl.DataFrame({"event_type": ["single", "single", "walk", None, ""]})
    result = profile_pa_event_types(frame)

    assert result["null_or_blank_count"] == 2
    assert result["counts"] == {"single": 2, "walk": 1}
