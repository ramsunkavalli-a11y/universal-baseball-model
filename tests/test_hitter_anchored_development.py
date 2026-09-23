import numpy as np
import polars as pl
import pytest

from universal_baseball.hitter_anchored_development import (
    active_rate_rows,attach_anchors,later_training,normalized_pa_weights,weighted_rate_mse,
)


def test_only_mature_active_rows_receive_rate_labels():
    f=pl.DataFrame({"origin_year":[2012,2012,2013,2014],"player_id":[1,2,3,4],
                    "pa_h1":[100,0,200,300],"war_h1":[1.,0.,2.,3.]})
    actual=active_rate_rows(f,2013,1)
    assert actual["player_id"].to_list()==[1]
    assert actual["actual_rate"].to_list()==[6.]


def test_pa_weighting_accounts_for_rate_workload_dependence_in_mean():
    pa=np.array([100.,500.]);rate=np.array([6.,0.])
    weighted_rate=np.average(rate,weights=normalized_pa_weights(pa))
    assert pa.mean()*weighted_rate/600==pytest.approx(np.mean(pa*rate/600))
    assert pa.mean()*rate.mean()/600!=pytest.approx(np.mean(pa*rate/600))
    assert weighted_rate_mse(pa,rate,rate)==0
    with pytest.raises(ValueError):normalized_pa_weights([0,100])


def test_anchor_join_preserves_id_and_rejects_later_fit_vintage():
    panel=pl.DataFrame({"origin_year":[2012,2012],"player_id":[1,2],"age_centered":[0.,1.],"log_mlb_pa_lag0":[1.,2.]})
    anchors=pl.DataFrame({"origin_year":[2012,2012],"player_id":[2,1],"performance_anchor":[8.,3.],
                          "anchor_cutoff":[2012,2012],"latest_anchor_target":[2012,2012]})
    result=attach_anchors(panel,anchors)
    assert result["performance_anchor"].to_list()==[3.,8.]
    with pytest.raises(ValueError,match="own origin"):
        attach_anchors(panel,anchors.with_columns(pl.lit(2016).alias("anchor_cutoff")))
    with pytest.raises(ValueError,match="future outcomes"):
        attach_anchors(panel,anchors.with_columns(pl.lit(2013).alias("latest_anchor_target")))


def test_later_heads_include_no_play_but_not_unobserved_future():
    f=pl.DataFrame({"origin_year":[2012,2013,2014,2015],"pa_h2":[0,100,200,None],"war_h2":[0.,1.,2.,None]})
    assert later_training(f,2015)["origin_year"].to_list()==[2012,2013]


def test_future_labels_cannot_change_fitted_forecasts(monkeypatch):
    from pathlib import Path
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]/"scripts"))
    from evaluate_hitter_anchored_development_v1 import anchor_at_origin,fit_later
    years=np.repeat(np.arange(2012,2017),80)
    x=np.tile(np.linspace(-1,1,80),5)
    pa=np.where(x>-.5,200+100*x,0)
    f=pl.DataFrame({"origin_year":years,"player_id":np.tile(np.arange(80),5),
        "x":x,"pa_h1":pa,"war_h1":pa*(2+x)/600,
        "pa_h2":pa,"war_h2":pa*(2+.8*x)/600,
        "performance_anchor":2+x,"anchor_cutoff":years})
    changed=f.with_columns(*[
        pl.when(pl.col("origin_year")+h>2016).then(99999.)
        .otherwise(pl.col(f"{name}_h{h}")).alias(f"{name}_h{h}")
        for h in (1,2) for name in ("war","pa")])
    a,_=anchor_at_origin(f,["x"],2016)
    b,_=anchor_at_origin(changed,["x"],2016)
    assert a.equals(b)
    a,_=fit_later(f,["x","performance_anchor"],2016)
    b,_=fit_later(changed,["x","performance_anchor"],2016)
    assert a.equals(b)


def test_saved_package_recomposes_and_preserves_protected_labels():
    import json
    from pathlib import Path
    from universal_baseball.storage import sha256_file
    root=Path(__file__).resolve().parents[1]
    package=root/"model_artifacts/hitter-anchored-development-v1-2026-09-22"
    manifest=json.loads((package/"manifest.json").read_text())
    assert manifest["status"]=="retain_v2"
    for name,digest in manifest["files"].items():
        assert sha256_file(package/name)==digest
    current=pl.read_parquet(package/"current-diagnostics.parquet")
    assert current.height==current["player_id"].n_unique()==3907
    assert all(current[c].null_count()==3907 for c in ("war_h1","war_h2","war_h3","war_c3","pa_h2"))
    history=pl.read_parquet(package/"historical-predictions.parquet")
    assert history.height==30664
    assert history.unique(["origin_year","player_id"]).height==history.height
    for frame in (history,current):
        for form,rate in (("A","rate_A"),("C","performance_anchor"),("D","rate_D")):
            np.testing.assert_allclose(frame[f"{form}_h2"],frame["expected_pa_h2_challenger"]*frame[rate]/600)
    anchors=pl.read_parquet(package/"historical-anchors.parquet")
    assert anchors.filter((pl.col("anchor_cutoff")!=pl.col("origin_year"))|
                          (pl.col("latest_anchor_target")>pl.col("anchor_cutoff"))).is_empty()


def test_protected_cutoffs_are_rejected():
    with pytest.raises(ValueError):active_rate_rows(pl.DataFrame(),2026,1)
    with pytest.raises(ValueError):later_training(pl.DataFrame(),2026)
