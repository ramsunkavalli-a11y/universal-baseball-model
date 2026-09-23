import numpy as np
import polars as pl
import pytest

from universal_baseball.multiyear_hitter_components import COMPONENTS, attach_labels, choose_component, historical_rate, mature_mask, pandemic


def test_mature_labels_and_pandemic():
    f=pl.DataFrame({"origin_year":[2015,2016,2017,2021,2022],"general_h3":[1.]*5})
    assert mature_mask(f,2021,3,"general").tolist()==[True,True,False,False,False]
    assert pandemic(np.array([2016,2017,2021]),3).tolist()==[False,True,False]
    with pytest.raises(ValueError): mature_mask(f,2026,3,"general")


def test_absent_and_unknown_and_protected_are_distinct():
    annual=pl.DataFrame({"season":[2024,2025],"player_id":[1,1],**{c:[None,1.] for c in COMPONENTS}})
    panel=pl.DataFrame({"origin_year":[2023,2023,2025],"player_id":[1,2,1]})
    f=attach_labels(panel,annual)
    assert f["general_h1"].to_list()==[None,0.,None]
    with pytest.raises(ValueError): attach_labels(panel,pl.concat([annual,annual]))


def test_selector_ignores_future_and_different_proxy():
    rows=[]
    for year in (2016,2017,2024):
        for player in range(100):
            rows.append(dict(origin_year=year,player_id=player,component="general",horizon=1,pandemic=False,
                             actual=2.,neutral=0.,benchmark=1.,direct=2. if year<2024 else -100.,batting=1.))
    f=pl.DataFrame(rows)
    name,note=choose_component(f,2021,1,"general")
    assert name=="direct" and note["origins"]==[2016,2017]
    assert choose_component(f.with_columns(pl.lit(None).alias("batting")),2025,1,"general")[0]=="neutral"
    assert choose_component(f,2017,1,"general")[0]=="neutral"


def test_missing_history_not_zero_exposure():
    assert historical_rate([6,100,100],[600,10000,10000],[1,0,0])==3.
    assert historical_rate([0,0,0],[0,0,0],[0,0,0])==0.


def test_position_calendar_does_not_inflate_short_season(monkeypatch):
    from pathlib import Path
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]/"scripts"))
    from certify_multiyear_native_components_v1 import official_annual
    f=pl.DataFrame({"season":[2019,2020],"player_id":[1,1],"position_abbreviation":["C","C"],
                    "fielding_outs":[1000,1000],"games_started":[40,40]})
    result=official_annual(f).sort("season")
    np.testing.assert_allclose(result["position_runs"],[1000*12.5/4374]*2)


def test_empty_era_history_is_not_learned_zero_label():
    f=pl.DataFrame({"origin_year":[2014,2015,2016,2017],"blocking_h1":[None,None,None,1.]})
    assert mature_mask(f,2017,1,"blocking").tolist()==[False]*4
