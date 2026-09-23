"""Read-only predictions audit; supplemental diagnostics, never a selection pass."""
import json
from pathlib import Path
import numpy as np
import polars as pl

from evaluate_hitter_anchored_development_v1 import PACKAGE,V1,V2,metrics
from evaluate_multiyear_hitter_followup_v2 import save_json
from universal_baseball.hitter_horizon_consistency import fixed_groups
from universal_baseball.multiyear_hitter_followup import compare_losses
from universal_baseball.storage import sha256_file


def mean_origin(frame,col):
    # Fix reduction order so repeated audits retain identical artifact hashes.
    ordered=frame.sort(["origin_year","player_id"])
    return float(np.mean([f[col].to_numpy().mean()
        for f in ordered.partition_by("origin_year",maintain_order=True)]))


def opportunity_metrics(frame,pcol,pacol):
    pa=frame["pa_h2"].to_numpy();y=pa>0;p=np.clip(frame[pcol].to_numpy(),1e-8,1-1e-8)
    pred=frame[pacol].to_numpy()
    scored=frame.with_columns(pl.Series("brier",(p-y)**2),pl.Series("logloss",-(y*np.log(p)+(~y)*np.log1p(-p))),
        pl.Series("mse",(pred-pa)**2),pl.Series("mae",abs(pred-pa)),pl.Series("pa_bias",pred-pa),
        pl.Series("conditional_error",abs(pred/p-pa)))
    result={k:mean_origin(scored,k) for k in ("brier","logloss","mse","mae","pa_bias")}
    result["conditional_pa_mae"]=mean_origin(scored.filter(pl.col("pa_h2")>0),"conditional_error")
    return result


def main():
    manifest=json.loads((PACKAGE/"manifest.json").read_text())
    report=json.loads((PACKAGE/"report.json").read_text())
    for name,expected in manifest["files"].items():assert sha256_file(PACKAGE/name)==expected,name
    for name,expected in report["source_manifest"]["hashes"].items():assert sha256_file(Path(name))==expected,name
    history=pl.read_parquet(PACKAGE/"historical-predictions.parquet")
    current=pl.read_parquet(PACKAGE/"current-diagnostics.parquet")
    anchors=pl.read_parquet(PACKAGE/"historical-anchors.parquet")
    assert current.height==3907 and all(current[c].null_count()==3907 for c in ("war_h1","war_h2","war_h3","war_c3","pa_h2"))
    assert anchors.filter((pl.col("anchor_cutoff")!=pl.col("origin_year"))|(pl.col("latest_anchor_target")>pl.col("anchor_cutoff"))).is_empty()
    for frame in (history,current):
        for form,rate in (("A","rate_A"),("C","performance_anchor"),("D","rate_D")):
            np.testing.assert_allclose(frame[f"{form}_h2"],frame["activity_h2_challenger"]*frame["conditional_pa_h2_challenger"]*frame[rate]/600,rtol=1e-12,atol=1e-12)
        assert all(np.isfinite(frame[col].to_numpy()).all() for col in ("A_h2","C_h2","D_h2","activity_h2_challenger","expected_pa_h2_challenger"))
    nonpandemic=history.filter(~((pl.col("origin_year")<2020)&(pl.col("origin_year")+2>=2020)))
    groups={name:{"rows":f.height,**{k:metrics(f,k+"_h2","war_h2") for k in ("reference","A","C","D")}}
            for name,mask in fixed_groups(nonpandemic).items() for f in [nonpandemic.filter(pl.Series(mask))]}
    h=history.with_columns(((pl.col("C_h2")-pl.col("war_h2"))**2).alias("C_loss"),
                          ((pl.col("reference_h2")-pl.col("war_h2"))**2).alias("reference_loss"))
    base_path=V1/"outer-predictions.parquet";update_path=V2/"opportunity-predictions.parquet"
    base=pl.read_parquet(base_path).select("origin_year","player_id",pl.col("activity_h2").alias("old_p"),pl.col("expected_pa_h2").alias("old_pa"))
    updates=pl.read_parquet(update_path).filter(pl.col("horizon")==2).select("origin_year","player_id",pl.col("p1").alias("update_p"),pl.col("pa1").alias("update_pa"))
    base=base.join(updates,on=["origin_year","player_id"],how="left",validate="1:1").with_columns(
        pl.coalesce("update_p","old_p").alias("accepted_p"),pl.coalesce("update_pa","old_pa").alias("accepted_pa"))
    matched=history.join(base,on=["origin_year","player_id"],how="inner",validate="1:1")
    component_groups={"overall":np.ones(matched.height,dtype=bool),**fixed_groups(matched)}
    components={name:{"rows":f.height,"accepted_v2":opportunity_metrics(f,"accepted_p","accepted_pa"),
        "challenger":opportunity_metrics(f,"activity_h2_challenger","expected_pa_h2_challenger")}
        for name,mask in component_groups.items() for f in [matched.filter(pl.Series(mask))]}
    result={"status":"verified; diagnostics only, no new promotion choice","composition_rows":history.height+current.height,
        "source_and_original_forecast_hashes_verified":True,"protected_outcomes_used":False,
        "nonpandemic_groups":groups,"carry_forward_vs_reference_diagnostic":compare_losses(h,"C_loss","reference_loss"),
        "opportunity_comparison":components,"opportunity_origins":sorted(matched["origin_year"].unique().to_list()),
        "opportunity_scope":"Six archived origins with accepted v2 replay; 2023 has no archived v2 opportunity replay and is excluded only here, not in value gates.",
        "extra_source_hashes":{str(p):sha256_file(p) for p in (Path(__file__),base_path,update_path)}}
    save_json(PACKAGE/"supplemental-audit.json",result)
    manifest["files"]["supplemental-audit.json"]=sha256_file(PACKAGE/"supplemental-audit.json")
    save_json(PACKAGE/"manifest.json",manifest)
    print(json.dumps({"status":result["status"],"carry_forward_vs_reference":result["carry_forward_vs_reference_diagnostic"],
        "nonpandemic_young_top":groups["Top50 under26"],"opportunity_top50":components["Top50"]},indent=2))


if __name__=="__main__":main()
