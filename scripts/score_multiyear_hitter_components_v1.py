"""Score frozen component candidates and the prequential integration policy."""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import polars as pl

from fit_multiyear_hitter_components_v1 import OUT, PLAN, save
from universal_baseball.multiyear_hitter_components import COMPONENTS
from universal_baseball.multiyear_hitter_followup import compare_losses
from universal_baseball.storage import sha256_file

FORMS = ("neutral","benchmark","direct","selected")


def groups(f):
    return {"all":f,**{s:f.filter(pl.col("stage")==s) for s in ("Current MLB","Upper minors","Lower minors")},
            "Under23 upper minors":f.filter((pl.col("stage")=="Upper minors")&(pl.col("age")<23))}


def mean(f, col):
    return float(f.group_by("origin_year").agg(pl.col(col).mean())[col].mean())


def metrics(f, forms=FORMS):
    result={}
    for k in forms:
        e=f.with_columns(((pl.col(k)-pl.col("actual"))**2).alias("loss"),
            (pl.col(k)-pl.col("actual")).abs().alias("abs"),(pl.col(k)-pl.col("actual")).alias("bias"))
        result[k]={"rmse":float(np.sqrt(mean(e,"loss"))),"mae":mean(e,"abs"),"bias":mean(e,"bias")}
    return result


def summarize(f, forms=FORMS, baseline="neutral"):
    f=f.filter(pl.col("actual").is_not_null())
    if f.is_empty(): return None
    e=f.with_columns(*[((pl.col(k)-pl.col("actual"))**2).alias(k+"_loss") for k in forms])
    return {"rows":f.height,"origins":sorted(f["origin_year"].unique().to_list()),"metrics":metrics(f,forms),
        "by_origin":{str(y):metrics(g,forms) for (y,),g in f.partition_by("origin_year",as_dict=True).items()},
        "paired_selected":compare_losses(e,"selected_loss",baseline+"_loss",draws=1000),
        "groups":{k:{"rows":g.height,"origins":g["origin_year"].n_unique(),
            "supported":g.height>=100 and g["origin_year"].n_unique()>=3,"metrics":metrics(g,forms)}
            for k,g in groups(f).items() if g.height}}


def integration(f):
    rows=[]
    for (year,h),part in f.filter(pl.col("batting").is_not_null()).partition_by(["origin_year","horizon"],as_dict=True).items():
        base=part.filter(pl.col("component")==COMPONENTS[0]).select("origin_year","player_id","horizon","pandemic","age","stage","batting","actual_batting")
        for c in COMPONENTS:
            base=base.join(part.filter(pl.col("component")==c).select("player_id",
                pl.col("actual").alias(c+"_actual"),*[pl.col(k).alias(c+"_"+k) for k in FORMS]),on="player_id",validate="1:1",maintain_order="left")
        # Strict common support, not sum_horizontal's null-skipping default.
        base=base.with_columns(pl.all_horizontal([pl.col(c+"_actual").is_not_null() for c in COMPONENTS]).alias("complete_components"))
        base=base.with_columns((pl.col("actual_batting")+pl.sum_horizontal([pl.col(c+"_actual") for c in COMPONENTS])/10).alias("actual"),
            *[(pl.col("batting")+pl.sum_horizontal([pl.col(c+"_"+k) for c in COMPONENTS])/10).alias(k) for k in FORMS])
        rows.append(base)
    return pl.concat(rows,how="vertical_relaxed")


def score_stack(f):
    annual={str(h):{label:summarize(f.filter((pl.col("horizon")==h)&(pl.col("pandemic")==stress)&pl.col("complete_components")))
        for label,stress in (("normal",False),("pandemic_stress",True))} for h in (1,2,3)}
    paths=f.group_by("origin_year","player_id").agg(pl.col("horizon").n_unique().alias("n_h"),pl.col("pandemic").any(),
        pl.col("complete_components").all(),pl.col("age").first(),pl.col("stage").first(),pl.col("actual").sum(),
        *[pl.col(k).sum() for k in FORMS]).filter((pl.col("n_h")==3)&pl.col("complete_components"))
    cumulative={label:summarize(paths.filter(pl.col("pandemic")==stress)) for label,stress in (("normal",False),("pandemic_stress",True))}
    normal=cumulative["normal"]
    gate={"cumulative_better":normal["metrics"]["selected"]["rmse"]<normal["metrics"]["neutral"]["rmse"],
        "annual_overall_no_harm":all(r["normal"]["metrics"]["selected"]["rmse"]<=r["normal"]["metrics"]["neutral"]["rmse"] for r in annual.values()),
        "annual_supported_groups":all(g["metrics"]["selected"]["rmse"]**2<=1.05*g["metrics"]["neutral"]["rmse"]**2
            for r in annual.values() for g in r["normal"]["groups"].values() if g["supported"]),
        "cumulative_supported_groups":all(g["metrics"]["selected"]["rmse"]**2<=1.05*g["metrics"]["neutral"]["rmse"]**2
            for g in normal["groups"].values() if g["supported"])}
    paths.write_parquet(OUT/"cumulative-component-predictions.parquet")
    return {"annual":annual,"cumulative":cumulative,"gates":gate,"release_as_development":all(gate.values()),
            "normal_cumulative_origins":len(normal["origins"]),
            "confirmation_support":len(normal["origins"])>=3,
            "support_note":"Numerical gates are not confirmation: common blocking coverage removes 2016-origin cumulative paths; only 2021/22 remain."}


def main():
    manifest=json.loads((OUT/"fit-manifest.json").read_text())
    for p,digest in manifest["source_hashes"].items():
        if sha256_file(Path(p))!=digest: raise ValueError("Input changed: "+p)
    f=pl.read_parquet(OUT/"component-predictions.parquet").filter(pl.col("origin_year")<2025)
    primary=f.filter(pl.col("batting").is_not_null()); results={}
    for c in COMPONENTS:
        results[c]={str(h):summarize(primary.filter((pl.col("component")==c)&(pl.col("horizon")==h)&~pl.col("pandemic"))) for h in (1,2,3)}
        print(c,{h: {k:round(v['rmse'],4) for k,v in r['metrics'].items()} for h,r in results[c].items() if r},flush=True)
    stack=integration(f); stack.write_parquet(OUT/"integrated-predictions.parquet")
    integrated=score_stack(stack)
    ablations={}
    for c in COMPONENTS:
        ablations[c]={}
        for h in (1,2,3):
            part=stack.filter((pl.col("horizon")==h)&~pl.col("pandemic")&pl.col("complete_components"))
            part=part.with_columns((pl.col("selected")-pl.col(c+"_selected")/10).alias("without"))
            ablations[c][str(h)]=summarize(part,forms=("without","selected"),baseline="without")
    later={c:{str(h):summarize(f.filter((pl.col("component")==c)&(pl.col("horizon")==h)&pl.col("batting").is_null())) for h in (1,2)} for c in COMPONENTS}
    report={"status":"development_component_integration", "plan_sha256":sha256_file(PLAN),"protected_outcomes_used":False,
        "scope":"standardized batting+replacement plus measured component ledger, not complete FanGraphs WAR",
        "components":results,"integrated":integrated,"ablations":ablations,"later_component_only_different_pa_proxy":later,
        "coverage":stack.group_by("origin_year","horizon").agg(pl.len().alias("all_starting_players"),pl.col("complete_components").sum().alias("complete_measurements")).sort("origin_year","horizon").to_dicts(),
        "limitations":["Retrospective metrics, not archived publication vintages","Only two normal cumulative origins on complete common component support; player intervals do not capture independent-season uncertainty",
            "Model choices are an earlier-fold policy; the final 2025 choice itself has no untouched test","Full-ABS zero-framing is a scenario, not a fitted 2026 adjustment",
            "No first-base receiving/GIDP residual; weak MiLB defense translations remain diagnostics","General/running/catcher native rates are not available throughout the minors"],
        "source_hashes":manifest["source_hashes"],"fit_manifest_sha256":sha256_file(OUT/"fit-manifest.json"),
        "prediction_sha256":sha256_file(OUT/"component-predictions.parquet")}
    save(OUT/"score-report.json",report)
    print(json.dumps({"integrated_gate":integrated["gates"],"cumulative":integrated["cumulative"]["normal"]["metrics"]},indent=2))


if __name__=="__main__": main()
