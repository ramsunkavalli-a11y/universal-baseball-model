"""Read-only integrity, chronology, identity and bookkeeping checks."""
import json
from pathlib import Path

import numpy as np
import polars as pl

from report_multiyear_hitter_components_v1 import PACKAGE, CURRENT, COMPONENTS, OUT
from universal_baseball.storage import sha256_file


def main():
    manifest=json.loads((PACKAGE/"manifest.json").read_text())
    for p,digest in manifest["files"].items():
        assert sha256_file(PACKAGE/p)==digest,p
    for p,digest in manifest["build_code_hashes"].items():
        assert sha256_file(Path(p))==digest,p
    assert sha256_file(CURRENT)==manifest["source_forecast_sha256"]
    fits=json.loads((PACKAGE/"fit-manifest.json").read_text())
    for p,digest in fits["code_hashes"].items():
        assert sha256_file(Path(p))==digest,p
    for note in fits["fits"]:
        year,h=note["origin"],note["horizon"]
        assert note["latest_label_year"] is None or note["latest_label_year"]<=year
        assert all(y+h<=year and not(y<2020<=y+h) for y in note["training_origins"])
        assert all(y+h<=year and y<year and not(y<2020<=y+h) for y in note["selection"]["origins"])
        assert year<=2025
    old=pl.read_parquet(CURRENT).sort("player_id")
    new=pl.read_parquet(PACKAGE/"forecast-2026-2028.parquet").sort("player_id")
    np.testing.assert_array_equal(old["player_id"],new["player_id"])
    assert new.height==3907 and new["player_name"].null_count()==0
    for h in (1,2,3):
        for col in (f"value_{2025+h}",f"expected_pa_h{h}",f"activity_h{h}"):
            np.testing.assert_array_equal(old[col],new[col])
        assert new[f"war_h{h}"].null_count()==new.height
        assert new[f"pa_h{h}"].null_count()==new.height
        add=sum(new[f"{c}_runs_h{h}"].to_numpy() for c in COMPONENTS)/10
        np.testing.assert_allclose(new[f"integrated_h{h}"],new[f"value_{2025+h}"]+add,atol=1e-12)
        np.testing.assert_allclose(new[f"no_framing_h{h}"],new[f"integrated_h{h}"]-new[f"framing_runs_h{h}"]/10,atol=1e-12)
    np.testing.assert_allclose(new["integrated_c3"],sum(new[f"integrated_h{h}"] for h in (1,2,3)),atol=1e-12)
    f=pl.read_parquet(PACKAGE/"component-predictions.parquet")
    assert f.unique(["origin_year","horizon","component","player_id"]).height==f.height
    assert f.filter(pl.col("origin_year")==2025)["actual"].null_count()==3907*3*7
    for year,h,c in f.select("origin_year","horizon","component").unique().iter_rows():
        p=f.filter((pl.col("origin_year")==year)&(pl.col("horizon")==h)&(pl.col("component")==c))
        selected=p["selected_model"][0]
        np.testing.assert_array_equal(p["selected"],p[selected])
    labels=pl.read_parquet(PACKAGE/"annual-component-labels.parquet")
    assert labels["season"].max()==2025
    assert labels.filter(pl.col("season")<2018)["blocking"].null_count()==labels.filter(pl.col("season")<2018).height
    report=json.loads((PACKAGE/"score-report.json").read_text())
    assert report["integrated"]["normal_cumulative_origins"]==2
    assert report["integrated"]["confirmation_support"] is False
    assert new.filter(pl.col("player_id")==683679)["organizations"][0].to_list()==["New York Yankees","San Francisco Giants"]
    outcome={"status":"verified","players":new.height,"component_prediction_rows":f.height,"fits_checked":len(fits["fits"]),
        "old_value_and_pa_unchanged":True,"future_labels_absent":True,"teams_dated_2025":True,"normal_cumulative_origins":2}
    print(json.dumps(outcome,indent=2))


if __name__=="__main__": main()
