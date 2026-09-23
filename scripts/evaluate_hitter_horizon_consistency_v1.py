"""Same-family horizon diagnostics and one fixed rich Year-2 challenger."""
from __future__ import annotations
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import warnings

import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

from evaluate_multiyear_hitter_v1 import ridge, shared_year1, limit_model, RICH, CURRENT
from evaluate_multiyear_hitter_followup_v2 import save_json
from universal_baseball.hitter_horizon_consistency import horizon_training, fixed_groups
from universal_baseball.hitter_model_tournament import make_engine_models, _fit_standard_two_part
from universal_baseball.hitter_target_architecture import feature_columns,matrix_from_panel,_lgbm_classifier,_lgbm_regressor
from universal_baseball.multiyear_hitter_value import training_mask
from universal_baseball.multiyear_hitter_followup import compare_losses
from universal_baseball.storage import sha256_file

V1 = Path("reports/generated/multiyear-hitter-v1")
V2 = Path("model_artifacts/multiyear-hitter-followup-v2-2026-09-22")
OUT = Path("reports/generated/hitter-horizon-consistency-v1")
PACKAGE = Path("model_artifacts/hitter-horizon-consistency-v1-2026-09-22")
PLAN = Path("docs/hitter-horizon-consistency-v1-plan.md")
ORIGINS = [2016,2017,2018,2019,2021,2022,2023]


def rich_year2(panel,rich,current,origin,fallback):
    test = panel.filter(pl.col("origin_year")==origin)
    scoring = current if origin==2025 else rich.filter(pl.col("origin_year")==origin)
    train = horizon_training(rich,panel,origin,2)
    note = {"origin":origin,"train_origins":sorted(train["origin_year"].unique().to_list()),"train_rows":train.height,
            "latest_target":int(train["target_season"].max()) if train.height else None}
    if train["origin_year"].n_unique()<2 or scoring.is_empty():
        return fallback,np.zeros(test.height,dtype=bool),{**note,"rich_scored":0},None
    columns = feature_columns(rich)
    x,tx = matrix_from_panel(train,columns),matrix_from_panel(scoring,columns)
    y,pa,active = (train[c].to_numpy() for c in ("target_component_war","target_mlb_pa","target_mlb_active"))
    use = active==1
    probability = limit_model(_lgbm_classifier(417)).fit(x,active).predict_proba(tx)[:,1]
    direct = limit_model(_lgbm_regressor(418)).fit(x,y).predict(tx)
    pt = limit_model(_lgbm_regressor(420)).fit(x[use],pa[use]).predict(tx)
    rate = limit_model(_lgbm_regressor(421)).fit(x[use],train["target_conditional_component_war_per_600"].to_numpy()[use],
        sample_weight=np.sqrt(np.maximum(pa[use],1))).predict(tx)
    members = {"lightgbm_direct":direct,"lightgbm_threepart":probability*np.clip(pt,0,750)*np.clip(rate,-5,10)/600}
    for engine in ("xgboost","ebm","ridge"):
        print(f"  {origin}: {engine} Year 2",flush=True)
        models = make_engine_models(engine,417,"balanced")
        limit_model(models.classifier); limit_model(models.regressor)
        p,conditional = _fit_standard_two_part(models,x,tx,active,y)
        members[engine] = p*conditional
    ensemble = np.mean(list(members.values()),axis=0)
    lookup = dict(zip(scoring["player_id"].to_list(),ensemble))
    predictions = np.array([lookup.get(i,fallback[j]) for j,i in enumerate(test["player_id"])])
    matched = np.array([i in lookup for i in test["player_id"]])
    member_frame = scoring.select("origin_year","player_id").with_columns(*[pl.Series(k,v) for k,v in members.items()])
    return predictions,matched,{**note,"rich_scored":int(matched.sum())},member_frame


def fit_origin(panel,manifest,rich,current,origin,fingerprint):
    path = OUT/"fits"/f"{fingerprint}-{origin}.parquet"
    if path.exists(): return pl.read_parquet(path)
    print(f"Fitting horizon comparison {origin}",flush=True)
    test = panel.filter(pl.col("origin_year")==origin)
    x,tx = panel.select(manifest["full_features"]).to_numpy(),test.select(manifest["full_features"]).to_numpy()
    predictions = {}
    for h in (1,2,3):
        mask = training_mask(panel,origin,h)
        predictions[f"ridge_h{h}"] = ridge().fit(x[mask],panel[f"war_h{h}"].to_numpy()[mask]).predict(tx)
    common = training_mask(panel,origin,2)&training_mask(panel,origin,1)
    for h in (1,2):
        predictions[f"matched_ridge_h{h}"] = ridge().fit(x[common],panel[f"war_h{h}"].to_numpy()[common]).predict(tx)
    original_path = list((V1/"fits").glob(f"*-{origin}-returning.parquet"))
    if original_path:
        old = test.select("player_id").join(pl.read_parquet(original_path[0]),on="player_id",validate="1:1",maintain_order="left")
        year1 = old["year1"].to_numpy()
        np.testing.assert_allclose(predictions["ridge_h2"],old["D1_h2"].to_numpy(),rtol=1e-10,atol=1e-10)
        np.testing.assert_allclose(predictions["ridge_h3"],old["D1_h3"].to_numpy(),rtol=1e-10,atol=1e-10)
    else:
        # Extend the exact existing first-year recipe to the new 2023 fold.
        bcols = manifest["base_features"]
        mask = training_mask(panel,origin,1)
        fallback = ridge().fit(panel.select(bcols).to_numpy()[mask],panel["war_h1"].to_numpy()[mask]).predict(test.select(bcols).to_numpy())
        year1,_ = shared_year1(panel,origin,False,fallback)
    candidate,matched,note,members = rich_year2(panel,rich,current,origin,predictions["ridge_h2"])
    out = test.select("origin_year","player_id","age","stage","war_h1","war_h2","war_h3","war_c3").with_columns(
        *[pl.Series(k,v) for k,v in predictions.items()],pl.Series("reference_h1",year1),
        pl.Series("candidate_h2",candidate),pl.Series("rich_matched",matched))
    out = out.with_columns(pl.col("ridge_h2").alias("reference_h2"),
        (pl.col("reference_h1")+pl.col("ridge_h2")+pl.col("ridge_h3")).alias("reference_c3"),
        (pl.col("reference_h1")+pl.col("candidate_h2")+pl.col("ridge_h3")).alias("candidate_c3"))
    out.write_parquet(path); save_json(path.with_suffix(".json"),note)
    if members is not None: members.write_parquet(path.with_name(path.stem+"-members.parquet"))
    return out


def metrics(frame,pred,target):
    rows = []
    for f in frame.partition_by("origin_year"):
        y,p = f[target].to_numpy(),f[pred].to_numpy()
        rows.append([np.mean((p-y)**2),np.mean(abs(p-y)),np.mean(p-y),np.mean(p),np.mean(y)])
    m = np.mean(rows,axis=0)
    return dict(zip(("mse","mae","bias","predicted","actual"),map(float,m)))|{"rmse":float(np.sqrt(m[0]))}


def trajectory(frame):
    result = {}
    for name,(a,b) in {"reference":("reference_h1","reference_h2"),"same_family":("ridge_h1","ridge_h2"),
                       "same_family_same_rows":("matched_ridge_h1","matched_ridge_h2"),"rich_year2":("reference_h1","candidate_h2")}.items():
        folds = []
        for f in frame.partition_by("origin_year"):
            folds.append({"h1":float(f[a].mean()),"h2":float(f[b].mean()),"change":float((f[b]-f[a]).mean()),
                          "fraction_improving":float((f[b]>f[a]).mean())})
        result[name] = {k:float(np.mean([r[k] for r in folds])) for k in folds[0]}
    observed = frame.filter(pl.col("war_h2").is_not_null())
    if observed.height:
        result["observed"] = {k:float(np.mean([f[c].mean() for f in observed.partition_by("origin_year")])) for k,c in (("h1","war_h1"),("h2","war_h2"))}
        result["observed"]["change"] = result["observed"]["h2"]-result["observed"]["h1"]
    return result


def evaluate(history):
    history = history.with_columns(((pl.col("candidate_h2")-pl.col("war_h2"))**2).alias("candidate_loss"),
                                  ((pl.col("reference_h2")-pl.col("war_h2"))**2).alias("reference_loss"))
    comparison = compare_losses(history,"candidate_loss","reference_loss")
    eligible = [int(y) for y in history["origin_year"].unique() if history.filter((pl.col("origin_year")==y)&pl.col("rich_matched")).height>=100]
    groups = {}
    for name,mask in fixed_groups(history).items():
        f = history.filter(pl.Series(mask))
        groups[name] = {"rows":f.height,"origins":f["origin_year"].n_unique(),"supported":f.height>=100 and f["origin_year"].n_unique()>=3,
            "reference":metrics(f,"reference_h2","war_h2"),"candidate":metrics(f,"candidate_h2","war_h2"),"trajectory":trajectory(f)}
    nonpandemic = history.filter(~((pl.col("origin_year")<2020)&(pl.col("origin_year")+2>=2020)))
    np_scores = {k:metrics(nonpandemic,k+"_h2","war_h2") for k in ("reference","candidate")}
    np_groups = {name:{"rows":f.height,"trajectory":trajectory(f)} for name,mask in fixed_groups(nonpandemic).items()
                 for f in [nonpandemic.filter(pl.Series(mask))] if f.height}
    complete = history.filter(pl.col("war_c3").is_not_null())
    c3 = {"overall":{k:metrics(complete,k+"_c3","war_c3") for k in ("reference","candidate")}}
    for name,mask in fixed_groups(complete).items():
        f=complete.filter(pl.Series(mask))
        if f.height>=100 and f["origin_year"].n_unique()>=3:
            c3[name]={k:metrics(f,k+"_c3","war_c3") for k in ("reference","candidate")}
    overall = {k:metrics(history,k+"_h2","war_h2") for k in ("reference","candidate")}
    gates = {"eligible_origins":len(eligible)>=3,"paired_MSE":comparison["interval95"][1]<0,
        "majority_eligible_origins":sum(r["delta"]<0 for r in comparison["folds"] if r["origin"] in eligible)>len(eligible)/2,
        "nonpandemic":np_scores["candidate"]["mse"]<np_scores["reference"]["mse"],
        "MAE":overall["candidate"]["mae"]<=overall["reference"]["mae"],
        "group_MSE":all(r["candidate"]["mse"]<=1.05*r["reference"]["mse"] for r in groups.values() if r["supported"]),
        "group_bias":all(abs(r["candidate"]["bias"])<=abs(r["reference"]["bias"])+.1 for r in groups.values() if r["supported"]),
        "cumulative_guard":all(r["candidate"]["mse"]<=1.05*r["reference"]["mse"] for r in c3.values())}
    return {"accepted":all(gates.values()),"gates":gates,"eligible_origins":eligible,"overall":overall,"comparison":comparison,
        "groups":groups,"nonpandemic":np_scores,"nonpandemic_groups":np_groups,"cumulative":c3,
        "same_family_year1_diagnostic":{k:metrics(history,k,"war_h1") for k in ("reference_h1","ridge_h1","matched_ridge_h1")}}


def main():
    OUT.mkdir(parents=True,exist_ok=True);(OUT/"fits").mkdir(exist_ok=True)
    sources = [PLAN,V1/"panel.parquet",V1/"manifest.json",RICH,CURRENT,V2/"forecast-2026-2028.parquet",
        Path(__file__),Path("src/universal_baseball/hitter_horizon_consistency.py"),Path("scripts/evaluate_multiyear_hitter_v1.py"),
        Path("src/universal_baseball/hitter_model_tournament.py"),Path("src/universal_baseball/hitter_target_architecture.py"),
        *sorted((V1/"fits").glob("*-returning.parquet"))]
    hashes={str(p):sha256_file(p) for p in sources}
    fingerprint=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()[:16]
    manifest={"hashes":hashes,"fingerprint":fingerprint,"protected_outcomes_used":False,"cutoff":"2025-12-31",
              "versions":{n:importlib.metadata.version(n) for n in ("numpy","polars","scikit-learn","lightgbm","xgboost","interpret")}}
    save_json(OUT/"source-manifest.json",manifest)
    panel=pl.read_parquet(V1/"panel.parquet")
    rich=pl.read_parquet(RICH);current=pl.read_parquet(CURRENT)
    if panel["origin_year"].max()!=2025 or rich["origin_year"].max()>2024 or current["origin_year"].max()!=2025:
        raise ValueError("Unexpected source vintage")
    meta=json.loads((V1/"manifest.json").read_text())
    frames=[fit_origin(panel,meta,rich,current,y,fingerprint) for y in [*ORIGINS,2025]]
    history=pl.concat(frames[:-1]); forecast=frames[-1]
    history.write_parquet(OUT/"historical-predictions.parquet");forecast.write_parquet(OUT/"current-diagnostics.parquet")
    report=evaluate(history)
    report["current_groups"]={name:{"rows":f.height,"trajectory":trajectory(f)} for name,mask in fixed_groups(forecast).items()
        for f in [forecast.filter(pl.Series(mask))] if f.height}
    report["support"]=[json.loads((OUT/"fits"/f"{fingerprint}-{year}.json").read_text()) for year in [*ORIGINS,2025]]
    report["source_manifest"]=manifest
    save_json(OUT/"report.json",report)
    PACKAGE.mkdir(parents=True,exist_ok=True)
    for name in ("historical-predictions.parquet","current-diagnostics.parquet","source-manifest.json","report.json"):
        shutil.copyfile(OUT/name,PACKAGE/name)
    save_json(PACKAGE/"manifest.json",{"status":"candidate_passed_pending_delivery" if report["accepted"] else "retain_v2",
        "protected_outcomes_used":False,"plan_sha256":sha256_file(PLAN),
        "files":{p.name:sha256_file(p) for p in PACKAGE.iterdir() if p.name!="manifest.json"}})
    print(json.dumps({"accepted":report["accepted"],"gates":report["gates"],"overall":report["overall"],
                      "current_top50":report["current_groups"]["Top50"]},indent=2),flush=True)


if __name__=="__main__":
    warnings.filterwarnings("ignore",message="X does not have valid feature names")
    with threadpool_limits(limits=4):main()
