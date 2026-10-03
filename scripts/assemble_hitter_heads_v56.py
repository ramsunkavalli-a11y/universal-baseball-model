"""One post-review assembly, preserving fitted head provenance and all rows."""
import json
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
import evaluate_hitter_prospect_pooling_v54 as e
from score_hitter_prospect_pooling_v54 import linear_trace
from score_hitter_readiness_v49 import probability_score
from score_practical_hitter_v31 import paired, rate_score
from universal_baseball.practical_hitter_v30 import score
from universal_baseball.storage import sha256_file

ROOT=e.ROOT
OUT=ROOT/"reports/generated/practical-hitter-head-assembly-v56"
STANDARD=ROOT/"reports/generated/practical-hitter-prospect-pooling-v54"
FIXED=ROOT/"reports/generated/practical-hitter-prospect-units-v55"


def write(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2, allow_nan=False)+"\n", encoding="utf8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    assert not (OUT/"predictions.parquet").exists(), "Do not silently replace an assembly."
    for folder in [STANDARD, FIXED]:
        assert e.read(folder/"verification.json")["player_walkthrough_status"]=="complete"
        pre=e.read(folder/"preflight.json")
        assert all(sha256_file(Path(p))==h for p,h in pre["input_hashes"].items())
        assert e.read(folder/"verification.json")["replayed_heads"]==105
    inputs=[STANDARD/"predictions.parquet", FIXED/"predictions.parquet",
        STANDARD/"report.json", FIXED/"report.json",
        ROOT/"docs/practical-hitter-head-assembly-v56-contract.md", Path(__file__)]
    write("preflight.json", dict(no_new_fits=True, prior_player_reviews_complete=True,
        input_hashes={str(p):sha256_file(p) for p in inputs}))
    standard=pl.read_parquet(STANDARD/"predictions.parquet").sort("row_id")
    fixed=pl.read_parquet(FIXED/"predictions.parquet").sort("row_id")
    old_cols=[c for c in standard.columns if not c.startswith(("shared_","prospect_pa_only_","prospect_rate_only_"))]
    assert standard.select(old_cols).equals(fixed.select(old_cols))
    assert len(standard)==30506
    assert not any(c.startswith("assembled_") for c in standard.columns)
    q=standard.with_columns(
        *[pl.col("shared_"+c).alias("standardized_"+c) for c in ["p","conditional_pa","pa","rate","value"]],
        *[fixed["shared_"+c].alias("fixed_"+c) for c in ["p","conditional_pa","pa","rate","value"]],
        *[pl.col("shared_"+c).alias("assembled_"+c) for c in ["p","conditional_pa","pa"]],
        fixed["shared_rate"].alias("assembled_rate"),
    ).with_columns(
        (pl.col("assembled_pa")*(pl.col("assembled_rate")/600+pl.col("origin_replacement_rate"))).alias("assembled_value")
    )
    established=q.filter(pl.col("prior_debut")==1)
    for c in ["p","conditional_pa","pa","rate","value"]:
        assert established["assembled_"+c].equals(established["repaired_"+c]),c
    assert np.isfinite(q.select(["assembled_"+c for c in ["p","conditional_pa","pa","rate","value"]]).to_numpy()).all()
    assert q.select(standard.columns).equals(standard)
    q.write_parquet(OUT/"predictions.parquet")
    never=q.filter(pl.col("prior_debut")==0)
    public=q.filter((pl.col("pa_0")>0)&pl.col("steamer_index").is_not_null()&pl.col("zips_index").is_not_null())
    assert len(public)==2627
    scopes=[("all",q),("never_debut",never),
        ("upper_never_debut",never.filter(pl.col("stage")=="Upper minors")),
        ("lower_never_debut",never.filter(pl.col("stage")=="Lower minors")),
        ("public_broad_unchanged",public)]
    scopes += [("never_origin_"+str(y),never.filter(pl.col("origin_year")==y)) for y in sorted(never["origin_year"].unique())]
    scopes += [("never_stage_"+s,never.filter(pl.col("stage")==s)) for s in sorted(never["stage"].unique())]
    scores=[]; intervals=[]
    for scope,g in scopes:
        if not len(g):continue
        arms=["repaired","standardized","fixed","prospect_pa_only","assembled"]
        if scope.startswith("public"):arms.append("steamer")
        scores.append(dict(scope=scope,rows=len(g),people=g["player_id"].n_unique(),
            actual_pa=float(g["next_pa"].sum()),actual_value=float(g["next_value"].sum()),
            scores={a:score(g,a) for a in arms},
            rates={a:rate_score(g,a+"_rate") for a in arms},
            probabilities={a:probability_score(g,a) for a in ["repaired","assembled"]}))
        if scope in ["all","never_debut","upper_never_debut","lower_never_debut"]:
            intervals += [dict(scope=scope,**paired(g,"assembled",b,"value")) for b in ["repaired","prospect_pa_only"]]
    write("scores.json",scores);write("intervals.json",intervals)
    selected={}
    def choose(rows,reason):
        o=rows.row(0,named=True); selected.setdefault(o["row_id"],[]).append(reason)
    for pid,y in [(701762,2024),(694671,2023),(641355,2016),(624413,2018),(806956,2024)]:
        choose(never.filter((pl.col("player_id")==pid)&(pl.col("origin_year")==y)),"fixed diagnostic")
    g=never.with_columns(
        ((pl.col("repaired_value")-pl.col("next_value"))**2-(pl.col("assembled_value")-pl.col("next_value"))**2).alias("gain"),
        (pl.col("assembled_value")-pl.col("next_value")).alias("error"))
    for why,ordered in [
        ("largest delivered gain",g.sort("gain",descending=True)),
        ("largest delivered harm",g.sort("gain")),
        ("false high",g.sort("error",descending=True)),
        ("false low",g.sort("error")),
        ("ordinary active prospect",g.filter(pl.col("next_pa").is_between(100,600)).sort(pl.col("error").abs()))
    ]:choose(ordered,why)
    source=pl.read_parquet(STANDARD/"features.parquet")
    names=e.read(STANDARD/"preflight.json")["features"]
    history=pl.read_parquet(ROOT/"reports/generated/practical-hitter-v31/counts.parquet")
    profiles=pl.read_parquet(STANDARD/"profile-support.parquet")
    cases=[]
    with threadpool_limits(limits=2):
        for rid,reasons in selected.items():
            o=q.filter(pl.col("row_id")==rid).row(0,named=True)
            te=source.filter(pl.col("row_id")==rid);x=te.select(names).to_numpy()[0]
            heads={}
            for folder,wanted in [(STANDARD,["participation","conditional_pa"]),(FIXED,["rate"])]:
                note=e.read(folder/f"fit-{o['origin_year']}-{o['outer_fold']}.json")
                for h in note["heads"]:
                    if h["head"] not in wanted:continue
                    assert sha256_file(Path(h["path"]))==h["sha256"]
                    t=linear_trace(joblib.load(h["path"]),x,names,h["head"]=="participation")
                    t.update(fit_path=h["path"],fit_sha256=h["sha256"],
                        transformation="standardized" if folder==STANDARD else "fixed baseball units")
                    if folder==FIXED:
                        for z in t["feature_effects"]:
                            z["fixed_reference"]=z.pop("training_mean");z["fixed_scale"]=z.pop("training_scale")
                    expected=o["assembled_"+{"participation":"p","conditional_pa":"conditional_pa","rate":"rate"}[h["head"]]]
                    linked=t["linked_prediction"]
                    if h["head"]=="conditional_pa":linked=float(np.clip(linked,1,800))
                    elif h["head"]=="participation" and (o["hard_unavailable"] or o["reported_retired"]):linked=0
                    assert np.isclose(linked,expected,atol=1e-10,rtol=0)
                    heads[h["head"]]=t
            peers=never.filter((pl.col("origin_year")==o["origin_year"])&(pl.col("stage")==o["stage"])&(pl.col("player_id")!=o["player_id"])).with_columns(
                (((pl.col("age")-o["age"])/3)**2+((pl.col("minor_pa_0")-o["minor_pa_0"])/250)**2+4*(pl.col("draft_rank")-o["draft_rank"])**2).alias("distance")
            ).sort("distance","player_id").head(4)
            cases.append(dict(origin=o,selection=reasons,actual_inputs={n:te[n][0] for n in names},
                known_highest_current=te["known_highest_current"][0],
                source_history=history.filter((pl.col("player_id")==o["player_id"])&pl.col("season").is_between(o["origin_year"]-2,o["origin_year"])).sort("season","bucket").to_dicts(),
                heads=heads,training_profile=profiles.filter(pl.col("row_id")==rid).to_dicts(),
                peers=peers.select("player_id","player_name","age","minor_pa_0","draft_rank","repaired_pa","assembled_p","assembled_conditional_pa","assembled_pa","assembled_rate","assembled_value","next_pa","next_batting_rate","next_value").to_dicts()))
    write("cases.json",cases)
    write("verification.json",dict(established_forecasts_bit_exact=True,original_columns_bit_exact=True,
        whole_evaluation_population_retained=True,no_new_fits=True,prior_heads_replayed=210,
        exact_case_linear_paths_verified=True,cases=len(cases),player_walkthrough_status="pending",
        protected_outcomes_used=False,frozen_forecast_changed=False))
    for s in scores[:5]:
        print(s["scope"],{a:(round(v["pa_rmse"],3),round(v["value_rmse"],6),round(s["rates"][a]["rmse"],4)) for a,v in s["scores"].items()},flush=True)
    print("Cases",[(c["origin"]["player_name"],c["origin"]["origin_year"],c["selection"]) for c in cases],flush=True)


if __name__=="__main__":main()
