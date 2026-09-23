import numpy as np
import polars as pl

from universal_baseball.hitter_horizon_consistency import horizon_training,fixed_groups
from universal_baseball.hitter_target_architecture import feature_columns


def test_year2_replaces_every_target_and_embargoes_future():
    rich=pl.DataFrame({"origin_year":[2016,2017,2018],"player_id":[1,2,3],"x":[10.,20.,30.],
        "target_mlb_active":[1,1,1],"target_mlb_pa":[999,999,999],"target_component_war":[99.,99.,99.],
        "target_conditional_component_war_per_600":[77.,77.,77.],"target_season":[2017,2018,2019]})
    panel=pl.DataFrame({"origin_year":[2016,2017,2018],"player_id":[1,2,3],"pa_h2":[0,300,600],"war_h2":[0.,2.,8.]})
    result=horizon_training(rich,panel,2019,2)
    assert result["player_id"].to_list()==[1,2]
    assert result["target_mlb_active"].to_list()==[0,1]
    assert result["target_mlb_pa"].to_list()==[0,300]
    assert result["target_component_war"].to_list()==[0.,2.]
    assert result["target_conditional_component_war_per_600"].to_list()==[0.,4.]
    assert result["target_season"].to_list()==[2018,2019]
    assert feature_columns(result)==["x"]


def test_missing_outcome_not_imputed_as_zero():
    rich=pl.DataFrame({"origin_year":[2016],"player_id":[1],"x":[1.]})
    panel=pl.DataFrame({"origin_year":[2016],"player_id":[1],"pa_h2":[None],"war_h2":[None]})
    assert horizon_training(rich,panel,2019,2).is_empty()


def test_group_membership_not_future_or_candidate_dependent():
    f=pl.DataFrame({"origin_year":[2022]*60,"player_id":list(range(60)),"age":[24.]*60,
        "stage":["Current MLB"]*60,"reference_h1":np.arange(60,dtype=float),"candidate_h2":np.arange(60,dtype=float)})
    a=fixed_groups(f)
    b=fixed_groups(f.with_columns(pl.lit(-100.).alias("candidate_h2"),pl.lit(999.).alias("war_h2")))
    np.testing.assert_array_equal(a["Top50"],b["Top50"])
    assert a["Top50"].sum()==50
    assert np.flatnonzero(a["Top50"])[0]==10


def test_target_join_is_keyed_and_future_mutation_cannot_change_training():
    rich=pl.DataFrame({"origin_year":[2016,2017,2018],"player_id":[8,9,10],"x":[1.,2.,3.]})
    panel=pl.DataFrame({"origin_year":[2018,2017,2016],"player_id":[10,9,8],
                       "pa_h2":[600,200,100],"war_h2":[9.,2.,1.]})
    a=horizon_training(rich,panel,2019,2)
    changed=panel.with_columns(pl.when(pl.col("origin_year")==2018).then(99999.).otherwise(pl.col("war_h2")).alias("war_h2"))
    b=horizon_training(rich.reverse(),changed,2019,2).sort("player_id")
    assert a.sort("player_id").equals(b)
    assert a["target_component_war"].to_list()==[1.,2.]


def test_protected_cutoff_rejected():
    import pytest
    with pytest.raises(ValueError,match="protected cutoff"):
        horizon_training(pl.DataFrame(),pl.DataFrame(),2026,2)


def test_committed_comparison_has_no_future_labels_and_retains_fallbacks():
    import json
    from pathlib import Path
    import pytest
    root=Path(__file__).resolve().parents[1]
    package=root/"model_artifacts/hitter-horizon-consistency-v1-2026-09-22"
    if not (package/"report.json").exists():
        pytest.skip("Comparison package not yet generated")
    current=pl.read_parquet(package/"current-diagnostics.parquet")
    assert current.height==current["player_id"].n_unique()==3907
    for col in ("war_h1","war_h2","war_h3","war_c3"):
        assert current[col].null_count()==3907
    history=pl.read_parquet(package/"historical-predictions.parquet")
    assert sorted(history["origin_year"].unique().to_list())==[2016,2017,2018,2019,2021,2022,2023]
    assert history.filter(pl.col("origin_year")==2023)["war_c3"].null_count()==history.filter(pl.col("origin_year")==2023).height
    fallback=history.filter(~pl.col("rich_matched"))
    np.testing.assert_array_equal(fallback["reference_h2"].to_numpy(),fallback["candidate_h2"].to_numpy())
    report=json.loads((package/"report.json").read_text())
    assert not report["accepted"]
    assert report["eligible_origins"]==[2018,2021,2022,2023]
