"""One frozen performance-anchor/change/opportunity challenger; no 2026 results."""
from __future__ import annotations
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import warnings

import numpy as np
import polars as pl
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression,PoissonRegressor,Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from evaluate_multiyear_hitter_followup_v2 import save_json
from evaluate_hitter_horizon_consistency_v1 import metrics,ORIGINS
from universal_baseball.hitter_target_architecture import _lgbm_regressor
from universal_baseball.hitter_horizon_consistency import fixed_groups
from universal_baseball.hitter_anchored_development import (
    EXTRA_FEATURES,normalized_pa_weights,active_rate_rows,attach_anchors,later_training,weighted_rate_mse,
)
from universal_baseball.multiyear_hitter_followup import compare_losses
from universal_baseball.storage import sha256_file

V1=Path("reports/generated/multiyear-hitter-v1")
V2=Path("model_artifacts/multiyear-hitter-followup-v2-2026-09-22")
PREVIOUS=Path("model_artifacts/hitter-horizon-consistency-v1-2026-09-22")
PLAN=Path("docs/hitter-anchored-development-v1-plan.md")
OUT=Path("reports/generated/hitter-anchored-development-v1")
PACKAGE=Path("model_artifacts/hitter-anchored-development-v1-2026-09-22")
ANCHOR_YEARS=[y for y in range(2012,2024) if y!=2020]+[2025]


def standardized(model):
    return make_pipeline(SimpleImputer(strategy="median",keep_empty_features=True),StandardScaler(),model)


def anchor_at_origin(panel,features,origin):
    train=active_rate_rows(panel,origin,1)
    test=panel.filter(pl.col("origin_year")==origin)
    model=_lgbm_regressor(417).set_params(n_jobs=4)
    raw=model.fit(train.select(features).to_numpy(),train["actual_rate"].to_numpy(),
                  sample_weight=normalized_pa_weights(train["pa_h1"])).predict(test.select(features).to_numpy())
    result=test.select("origin_year","player_id").with_columns(pl.Series("performance_anchor",np.clip(raw,-5,10)),
        pl.lit(origin).alias("anchor_cutoff"),pl.lit(int(train["origin_year"].max())+1).alias("latest_anchor_target"))
    return result,{"origin":origin,"train_rows":train.height,"train_origins":sorted(train["origin_year"].unique().to_list()),
        "latest_target":int(train["origin_year"].max())+1,"rows":test.height,"clipped":int(((raw< -5)|(raw>10)).sum())}


def fit_later(panel,features,origin):
    train=later_training(panel,origin)
    test=panel.filter(pl.col("origin_year")==origin)
    x,tx=train.select(features).to_numpy(),test.select(features).to_numpy()
    active=train["pa_h2"].to_numpy()>0
    pa=train["pa_h2"].to_numpy()[active]
    rate=train["war_h2"].to_numpy()[active]*600/pa
    anchor=train["performance_anchor"].to_numpy()[active]
    current_anchor=test["performance_anchor"].to_numpy()
    probability=standardized(LogisticRegression(C=.1,max_iter=2000,random_state=417)).fit(x,active.astype(int)).predict_proba(tx)[:,1]
    pt=standardized(PoissonRegressor(alpha=1.,max_iter=2000)).fit(x[active],pa)
    raw_pa=pt.predict(tx);conditional_pa=np.clip(raw_pa,1,750)
    delta=standardized(Ridge(alpha=20.)).fit(x[active],rate-anchor,ridge__sample_weight=normalized_pa_weights(pa)).predict(tx)
    direct=standardized(Ridge(alpha=20.)).fit(x[active],rate,ridge__sample_weight=normalized_pa_weights(pa)).predict(tx)
    adjusted=current_anchor+delta
    result=test.select("origin_year","player_id","performance_anchor","anchor_cutoff").with_columns(
        pl.Series("activity_h2_challenger",probability),pl.Series("conditional_pa_h2_challenger",conditional_pa),
        pl.Series("expected_pa_h2_challenger",probability*conditional_pa),pl.Series("rate_delta",delta),
        pl.Series("rate_A",np.clip(adjusted,-5,10)),pl.Series("rate_D",np.clip(direct,-5,10))).with_columns(
            (pl.col("expected_pa_h2_challenger")*pl.col("rate_A")/600).alias("A_h2"),
            (pl.col("expected_pa_h2_challenger")*pl.col("rate_D")/600).alias("D_h2"),
            (pl.col("expected_pa_h2_challenger")*pl.col("performance_anchor")/600).alias("C_h2"))
    return result,{"origin":origin,"train_rows":train.height,"active_rows":int(active.sum()),
        "train_origins":sorted(train["origin_year"].unique().to_list()),"latest_target":int(train["origin_year"].max())+2,
        "conditional_pa_clips":int(((raw_pa<1)|(raw_pa>750)).sum()),"poisson_iterations":int(pt[-1].n_iter_),
        "A_rate_clips":int(((adjusted< -5)|(adjusted>10)).sum()),"D_rate_clips":int(((direct< -5)|(direct>10)).sum())}


def evaluate(frame):
    frame=frame.with_columns(*[((pl.col(f"{k}_h2")-pl.col("war_h2"))**2).alias(k+"_loss") for k in ("reference","A","C","D")],
        (pl.col("reference_h1")+pl.col("A_h2")+pl.col("ridge_h3")).alias("A_c3"))
    comparisons={k:compare_losses(frame,"A_loss",k+"_loss") for k in ("reference","C","D")}
    overall={k:metrics(frame,k+"_h2","war_h2") for k in ("reference","A","C","D")}
    groups={}
    for name,mask in fixed_groups(frame).items():
        f=frame.filter(pl.Series(mask))
        groups[name]={"rows":f.height,"origins":f["origin_year"].n_unique(),"supported":f.height>=100 and f["origin_year"].n_unique()>=3,
            **{k:metrics(f,k+"_h2","war_h2") for k in ("reference","A","C","D")}}
    np_frame=frame.filter(~((pl.col("origin_year")<2020)&(pl.col("origin_year")+2>=2020)))
    nonpandemic={k:metrics(np_frame,k+"_h2","war_h2") for k in ("reference","A","C","D")}
    active=frame.filter(pl.col("pa_h2")>0)
    rate_scores={}
    for name,col in {"A":"rate_A","C":"performance_anchor","D":"rate_D"}.items():
        rate_scores[name]=float(np.mean([weighted_rate_mse(f["pa_h2"],f["war_h2"]*600/f["pa_h2"],f[col]) for f in active.partition_by("origin_year")]))
    components=[]
    for f in frame.partition_by("origin_year"):
        y=f["pa_h2"].to_numpy();p=np.clip(f["activity_h2_challenger"].to_numpy(),1e-8,1-1e-8);a=y>0
        components.append({"origin":int(f["origin_year"][0]),"brier":float(np.mean((p-a)**2)),
            "log_loss":float(-np.mean(a*np.log(p)+(~a)*np.log1p(-p))),
            "predicted_activity":float(p.mean()),"actual_activity":float(a.mean()),
            "pa_mae":float(np.mean(abs(f["expected_pa_h2_challenger"].to_numpy()-y))),
            "pa_rmse":float(np.sqrt(np.mean((f["expected_pa_h2_challenger"].to_numpy()-y)**2))),
            "conditional_pa_mae":float(np.mean(abs(f["conditional_pa_h2_challenger"].to_numpy()[a]-y[a])))})
    complete=frame.filter(pl.col("war_c3").is_not_null())
    cumulative={"overall":{k:metrics(complete,k+"_c3","war_c3") for k in ("reference","A")}}
    for name,mask in fixed_groups(complete).items():
        f=complete.filter(pl.Series(mask))
        if f.height>=100 and f["origin_year"].n_unique()>=3:
            cumulative[name]={k:metrics(f,k+"_c3","war_c3") for k in ("reference","A")}
    gates={"paired_value":comparisons["reference"]["interval95"][1]<0,
        "majority_origins":comparisons["reference"]["improving_origins"]>len(ORIGINS)/2,
        "MAE":overall["A"]["mae"]<=overall["reference"]["mae"],"nonpandemic":nonpandemic["A"]["mse"]<nonpandemic["reference"]["mse"],
        "group_MSE":all(r["A"]["mse"]<=1.05*r["reference"]["mse"] for r in groups.values() if r["supported"]),
        "group_bias":all(abs(r["A"]["bias"])<=abs(r["reference"]["bias"])+.1 for r in groups.values() if r["supported"]),
        "cumulative":all(r["A"]["mse"]<=1.05*r["reference"]["mse"] for r in cumulative.values()),
        "development_value":comparisons["C"]["interval95"][1]<0,"development_rate":rate_scores["A"]<rate_scores["C"]}
    return {"accepted":all(gates.values()),"gates":gates,"overall":overall,"comparisons":comparisons,
        "groups":groups,"nonpandemic":nonpandemic,"PA_weighted_active_rate_MSE":rate_scores,"component_diagnostics":components,
        "cumulative":cumulative,"scope":"batting + replacement; conditional rate is not identified universal pure talent",
        "protected_outcomes_used":False}


def main():
    OUT.mkdir(parents=True,exist_ok=True);(OUT/"fits").mkdir(exist_ok=True)
    sources=[PLAN,V1/"panel.parquet",V1/"manifest.json",PREVIOUS/"historical-predictions.parquet",PREVIOUS/"current-diagnostics.parquet",
        V2/"forecast-2026-2028.parquet",Path(__file__),Path("src/universal_baseball/hitter_anchored_development.py"),
        Path("src/universal_baseball/hitter_target_architecture.py"),Path("src/universal_baseball/hitter_horizon_consistency.py"),
        Path("src/universal_baseball/multiyear_hitter_followup.py"),Path("scripts/evaluate_hitter_horizon_consistency_v1.py")]
    hashes={str(p):sha256_file(p) for p in sources}
    key=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()[:16]
    manifest={"hashes":hashes,"fingerprint":key,"protected_outcomes_used":False,
        "versions":{n:importlib.metadata.version(n) for n in ("numpy","polars","scikit-learn","lightgbm")}}
    save_json(OUT/"source-manifest.json",manifest)
    panel=pl.read_parquet(V1/"panel.parquet")
    features=json.loads((V1/"manifest.json").read_text())["full_features"]
    if len(features)!=77 or panel["origin_year"].max()!=2025:raise ValueError("Changed frozen population/features")
    anchors,anchor_notes=[],[]
    for origin in ANCHOR_YEARS:
        path=OUT/"fits"/f"{key}-anchor-{origin}.parquet"
        if path.exists():
            a=pl.read_parquet(path);note=json.loads(path.with_suffix(".json").read_text())
        else:
            a,note=anchor_at_origin(panel,features,origin);a.write_parquet(path);save_json(path.with_suffix(".json"),note)
        anchors.append(a);anchor_notes.append(note)
        print(f"Cutoff-only performance anchor {origin} ready",flush=True)
    anchors=pl.concat(anchors);anchors.write_parquet(OUT/"historical-anchors.parquet")
    modeled=attach_anchors(panel,anchors)
    later,notes=[],[]
    for origin in [*ORIGINS,2025]:
        predictions,note=fit_later(modeled,features+EXTRA_FEATURES,origin)
        later.append(predictions);notes.append(note)
        print(f"Development and opportunity {origin} fitted",flush=True)
    forecasts=pl.concat(later)
    label_columns=["pa_h2"]
    reference=pl.concat([pl.read_parquet(PREVIOUS/"historical-predictions.parquet"),pl.read_parquet(PREVIOUS/"current-diagnostics.parquet")])
    combined=reference.join(forecasts,on=["origin_year","player_id"],validate="1:1",maintain_order="left").join(
        panel.select("origin_year","player_id",*label_columns),on=["origin_year","player_id"],validate="1:1",maintain_order="left")
    combined=combined.drop("candidate_h2","rich_matched")
    history=combined.filter(pl.col("origin_year").is_in(ORIGINS));current=combined.filter(pl.col("origin_year")==2025)
    history.write_parquet(OUT/"historical-predictions.parquet");current.write_parquet(OUT/"current-diagnostics.parquet")
    report=evaluate(history)
    report["anchor_support"]=anchor_notes;report["head_support"]=notes;report["source_manifest"]=manifest
    report["current_top50"]=current.sort("reference_h1",descending=True).head(50).select(
        *[pl.col(c).mean() for c in ("reference_h1","reference_h2","A_h2","C_h2","D_h2")]).to_dicts()[0]
    save_json(OUT/"report.json",report)
    PACKAGE.mkdir(parents=True,exist_ok=True)
    for name in ("historical-anchors.parquet","historical-predictions.parquet","current-diagnostics.parquet","report.json","source-manifest.json"):
        shutil.copyfile(OUT/name,PACKAGE/name)
    save_json(PACKAGE/"manifest.json",{"status":"passed_pending_delivery" if report["accepted"] else "retain_v2",
        "plan_sha256":sha256_file(PLAN),"protected_outcomes_used":False,
        "files":{p.name:sha256_file(p) for p in PACKAGE.iterdir() if p.name!="manifest.json"}})
    print(json.dumps({"accepted":report["accepted"],"gates":report["gates"],"overall":report["overall"],
                      "rate_errors":report["PA_weighted_active_rate_MSE"],"current_top50":report["current_top50"]},indent=2),flush=True)


if __name__=="__main__":
    warnings.filterwarnings("ignore",message="X does not have valid feature names")
    with threadpool_limits(limits=4):main()
