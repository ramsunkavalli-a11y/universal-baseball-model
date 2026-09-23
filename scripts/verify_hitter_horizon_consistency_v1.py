"""Read-only source, ensemble-alignment and forecast-preservation checks."""
import json
from pathlib import Path

import numpy as np
import polars as pl

from evaluate_hitter_horizon_consistency_v1 import OUT,PACKAGE,V2,PLAN
from universal_baseball.storage import sha256_file


def main():
    manifest=json.loads((PACKAGE/"manifest.json").read_text())
    report=json.loads((PACKAGE/"report.json").read_text())
    for name,expected in manifest["files"].items():
        assert sha256_file(PACKAGE/name)==expected,name
    assert sha256_file(PLAN)==manifest["plan_sha256"]
    for name,expected in report["source_manifest"]["hashes"].items():
        assert sha256_file(Path(name))==expected,name
    key=report["source_manifest"]["fingerprint"]
    checked=0
    for note in report["support"]:
        assert note["latest_target"] is None or note["latest_target"]<=note["origin"]
        if not note["rich_scored"]:continue
        raw=pl.read_parquet(OUT/"fits"/f"{key}-{note['origin']}-members.parquet")
        cols=["lightgbm_direct","lightgbm_threepart","xgboost","ebm","ridge"]
        raw=raw.with_columns(pl.Series("ensemble",raw.select(cols).to_numpy().mean(axis=1)))
        fit=pl.read_parquet(OUT/"fits"/f"{key}-{note['origin']}.parquet").filter(pl.col("rich_matched"))
        matched=fit.join(raw.select("player_id","ensemble"),on="player_id",validate="1:1")
        assert matched.height==note["rich_scored"]
        np.testing.assert_allclose(matched["candidate_h2"],matched["ensemble"],rtol=1e-12,atol=1e-12)
        checked+=matched.height
    original=pl.read_parquet(V2/"forecast-2026-2028.parquet")
    current=pl.read_parquet(PACKAGE/"current-diagnostics.parquet")
    joined=current.join(original.select("player_id","value_2026","value_2027","value_2028"),on="player_id",validate="1:1")
    for a,b in [("reference_h1","value_2026"),("reference_h2","value_2027"),("ridge_h3","value_2028")]:
        np.testing.assert_allclose(joined[a],joined[b],rtol=1e-10,atol=1e-10)
    assert all(current[c].null_count()==3907 for c in ("war_h1","war_h2","war_h3","war_c3"))
    print(json.dumps({"status":"verified","package_files":len(manifest["files"]),"ensemble_rows_verified":checked,
        "v2_forecast_unchanged":True,"protected_outcomes_used":False},indent=2))


if __name__=="__main__":main()
