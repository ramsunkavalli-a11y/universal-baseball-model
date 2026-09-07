import polars as pl
import pytest

from universal_baseball.mlb_opportunity import (
    project_pages,
    certify_participation,
    build_cohort,
    label_cohort,
    predict_opportunity,
)


def page(rows, total=2, season=2022):
    return {
        "stats": [
            {
                "totalSplits": total,
                "splits": [
                    {
                        "season": str(season),
                        "player": {"id": pid},
                        "stat": {"plateAppearances": pa},
                    }
                    for pid, pa in rows
                ],
            }
        ]
    }


def test_participation_refuses_partial_duplicate_and_wrong_season():
    with pytest.raises(ValueError, match="Incomplete"):
        project_pages([page([(1, 10)])], 2022)
    with pytest.raises(ValueError, match="Duplicate"):
        project_pages([page([(1, 10), (1, 20)])], 2022)
    with pytest.raises(ValueError, match="season"):
        project_pages([page([(1, 10), (2, 20)])], 2023)
    with pytest.raises(ValueError, match="changed"):
        project_pages([page([(1, 10)]), page([(2, 20)], total=3)], 2022)


def test_cross_league_traded_player_counted_once_with_summed_pa():
    overall = project_pages([page([(1, 30), (2, 50)])], 2022)
    al = project_pages([page([(1, 10)], total=1)], 2022)
    nl = project_pages([page([(1, 20), (2, 50)])], 2022)
    assert certify_participation(overall, al, nl).equals(overall)
    with pytest.raises(ValueError, match="disagree"):
        certify_participation(overall, al, al)


def test_cohort_keeps_nonarrival_and_noneligible_history_and_bulk_only_player():
    history = pl.DataFrame(
        {
            "season": [2021, 2021, 2021, 2020],
            "player_id": [1, 2, 2, 4],
            "level_group": ["AA", "AAA", "MLB", "AA"],
            "batting_PA": [100, 200, 500, 100],
            "modeling_eligible": [False, True, True, True],
        }
    )
    official = pl.DataFrame({"player_id": [2, 3], "mlb_pa": [10, 150]})
    cohort = build_cohort(history, official, 2022)
    assert cohort["player_id"].to_list() == [1, 2, 3]
    assert cohort.filter(pl.col("player_id") == 2)["origin"].item() == "AAA"
    target = pl.DataFrame({"player_id": [2], "mlb_pa": [40]})
    labeled = label_cohort(cohort, target)
    assert labeled["mlb_pa"].to_list() == [0, 40, 0]
    with pytest.raises(ValueError, match="cutoff"):
        build_cohort(history, official, 2021)


def test_baseline_uses_only_past_and_preserves_nested_probabilities():
    training = pl.DataFrame(
        {
            "year": [2022] * 3,
            "origin": ["AA", "AA", "MLB"],
            "exposure": ["0", "0", "100+"],
            "any_pa": [0.0, 1.0, 1.0],
            "pa100": [0.0, 0.0, 1.0],
            "mlb_pa": [0, 50, 300],
        }
    )
    cohort = pl.DataFrame(
        {
            "year": [2023] * 3,
            "player_id": [1, 2, 3],
            "origin": ["AA", "RK", "AAA"],
            "exposure": ["0", "0", "1-99"],
        }
    )
    prediction, parameters = predict_opportunity(training, cohort)
    assert parameters["training_years"] == [2022]
    assert prediction["LEVEL_any_pa"].to_list() == pytest.approx([0.5, 0.5, 2 / 3])
    assert (prediction["LEVEL_any_pa"] >= prediction["LEVEL_pa100"]).all()
    assert prediction["LEVEL_mlb_pa"].to_list() == pytest.approx([25, 25, 350 / 3])
    with pytest.raises(ValueError, match="precede"):
        predict_opportunity(training, cohort.with_columns(pl.lit(2022).alias("year")))
