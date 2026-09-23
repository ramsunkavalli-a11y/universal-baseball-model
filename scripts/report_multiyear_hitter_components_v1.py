"""Deliver the separate component-ledger development view and team-filter explorer."""
from __future__ import annotations

import json
from pathlib import Path
import shutil

import numpy as np
import polars as pl
import requests

from fit_multiyear_hitter_components_v1 import OUT, OLD, CURRENT, COMPONENTS, ROLE, load_sources, save
from universal_baseball.storage import sha256_file

PACKAGE=Path("model_artifacts/multiyear-hitter-components-v1-2026-09-22")
TEMPLATE=Path("templates/multiyear-hitter-components-v1-explorer.html")


def organization_mapping(stats):
    paths=sorted((OLD/"affiliated-team-context/captures").glob("teams-2025-sport-*.json"))
    mapping={}; hashes={}
    for path in paths:
        hashes[str(path)]=sha256_file(path)
        for team in json.loads(path.read_text(encoding="utf-8"))["teams"]:
            if int(team["season"])!=2025: raise ValueError("Wrong team year")
            is_mlb=team["sport"]["id"]==1
            name=team["name"] if is_mlb else team.get("parentOrgName")
            if not name: continue
            row=(int(team.get("parentOrgId") or team["id"]),name)
            if team["id"] in mapping and mapping[team["id"]]!=row: raise ValueError("Conflicting parent")
            mapping[team["id"]]=row
    groups=[]
    for (pid,),f in stats.filter(pl.col("season")==2025).partition_by("player_id",as_dict=True).items():
        organizations=sorted({mapping[t][1] for t in f["team_id"] if t in mapping})
        groups.append({"player_id":pid,"organizations":organizations or ["Unknown / no 2025 batting stint"]})
    return pl.DataFrame(groups), hashes


def assemble(original, predictions, evidence, organizations, names):
    current=original.sort("player_id")
    current=current.join(organizations,on="player_id",how="left",validate="1:1",maintain_order="left").with_columns(
        pl.col("organizations").fill_null(pl.lit(["Unknown / no 2025 batting stint"])))
    current=current.join(names,on="player_id",how="left",validate="1:1",maintain_order="left").with_columns(
        pl.coalesce("player_name","historical_name").alias("player_name")).drop("historical_name")
    current=current.join(evidence.select("player_id","role_missing",*ROLE,
        *[pl.col(f"{c}_lag0_available").alias(c+"_recent_mlb_measurement") for c in ("general","framing","throwing","blocking")]),
        on="player_id",how="left",validate="1:1",maintain_order="left")
    # Receiving/framing/noncatcher coverage must be interpreted with actual role.
    current=current.with_columns(pl.when(pl.col("role_missing")==0).then(pl.Series("position_label",
        [ROLE[int(np.argmax(row))][5:] for row in current.select(ROLE).to_numpy()])).otherwise(pl.lit("Unknown")).alias("position_label"))
    for h in (1,2,3):
        for c in COMPONENTS:
            part=predictions.filter((pl.col("horizon")==h)&(pl.col("component")==c)).select("player_id",
                pl.col("selected").alias(f"{c}_runs_h{h}"),pl.col("selected_model").alias(f"{c}_method_h{h}"))
            current=current.join(part,on="player_id",how="left",validate="1:1",maintain_order="left")
        current=current.with_columns((pl.col(f"value_{2025+h}")+pl.sum_horizontal([pl.col(f"{c}_runs_h{h}") for c in COMPONENTS])/10).alias(f"integrated_h{h}"))
        current=current.with_columns((pl.col(f"integrated_h{h}")-pl.col(f"framing_runs_h{h}")/10).alias(f"no_framing_h{h}"))
    current=current.with_columns(pl.sum_horizontal([f"integrated_h{h}" for h in (1,2,3)]).alias("integrated_c3"),
        ((pl.col("position_runs_h1")>pl.col("expected_pa_h1")*12.5/600+1.) |
         (pl.col("position_runs_h1")<pl.col("expected_pa_h1")*(-17.5)/600-1.)).alias("position_workload_review"))
    if current.height!=3907 or current["player_id"].n_unique()!=3907: raise ValueError("Population changed")
    for c in ("value_2026","value_2027","value_2028","value_three_years","expected_pa_h1","expected_pa_h2","expected_pa_h3"):
        np.testing.assert_array_equal(current[c].to_numpy(),original.sort("player_id")[c].to_numpy())
    for c in ("war_h1","war_h2","war_h3","pa_h1","pa_h2","pa_h3"):
        if current[c].null_count()!=3907: raise ValueError("Future outcomes present")
    return current


def explorer(current, report):
    keep=["player_id","player_name","age","stage","level","organizations","position_label","role_missing","year1_evidence",
          "integrated_c3","value_three_years","opportunity_source","general_recent_mlb_measurement","role_C","position_workload_review"]
    for h in (1,2,3):
        keep += [f"value_{2025+h}",f"integrated_h{h}",f"no_framing_h{h}",f"expected_pa_h{h}",f"activity_h{h}"]
        keep += [f"{c}_{suffix}_h{h}" for c in COMPONENTS for suffix in ("runs","method")]
    data=json.dumps(current.select(keep).to_dicts(),allow_nan=False).replace("</","<\\/")
    payload={"release":report["integrated"]["release_as_development"],"origins":report["integrated"]["normal_cumulative_origins"],
        "rmse_before":report["integrated"]["cumulative"]["normal"]["metrics"]["neutral"]["rmse"],
        "rmse_after":report["integrated"]["cumulative"]["normal"]["metrics"]["selected"]["rmse"]}
    return TEMPLATE.read_text(encoding="utf-8").replace("__PLAYER_DATA__",data).replace("__REPORT_DATA__",json.dumps(payload))


def main():
    report=json.loads((OUT/"score-report.json").read_text())
    if sha256_file(OUT/"component-predictions.parquet")!=report["prediction_sha256"]: raise ValueError("Predictions changed")
    original=pl.read_parquet(CURRENT)
    f=pl.read_parquet(OUT/"component-predictions.parquet").filter(pl.col("origin_year")==2025)
    evidence=pl.read_parquet(OUT/"component-panel.parquet").filter(pl.col("origin_year")==2025)
    stats,_,_=load_sources(); orgs,team_hashes=organization_mapping(stats)
    names=stats.sort(["season","plate_appearances"],descending=True).unique("player_id",keep="first").select("player_id",pl.col("player_name").alias("historical_name"))
    identity_path=OLD/"affiliated-full-roster-source-audit/tables/player_candidate_inventory.parquet"
    # Display-only identity lookup. Do not read current roster/organization/status
    # fields or use this table in predictors, selection, or cohort membership.
    identities=pl.read_parquet(identity_path,columns=["player_id","player_name"]).unique("player_id").rename({"player_name":"identity_name"})
    names=names.join(identities,on="player_id",how="full",coalesce=True,validate="1:1").select("player_id",pl.coalesce("historical_name","identity_name").alias("historical_name"))
    current=assemble(original,f,evidence,orgs,names)
    missing_ids=current.filter(pl.col("player_name").is_null())["player_id"].to_list()
    display_capture=OUT/"display-only-player-names.json"
    if missing_ids and not display_capture.exists():
        response=requests.get("https://statsapi.mlb.com/api/v1/people",params={
            "personIds":",".join(map(str,missing_ids)),"fields":"people,id,fullName"},timeout=30)
        response.raise_for_status(); save(display_capture,response.json())
    if missing_ids:
        identity_rows=json.loads(display_capture.read_text(encoding="utf-8"))["people"]
        lookup={r["id"]:r["fullName"] for r in identity_rows}
        if set(lookup)!=set(missing_ids): raise ValueError("Identity response differs from requested players")
        current=current.with_columns(pl.Series("player_name",[r["player_name"] or lookup.get(r["player_id"]) for r in current.iter_rows(named=True)]))
    native_ids=pl.read_parquet(OUT/"native-fielding-history.parquet").filter(pl.col("season")==2025)["player_id"].to_list()
    current=current.with_columns(pl.col("player_id").is_in(native_ids).cast(pl.Int8).alias("general_recent_mlb_measurement"))
    current.write_parquet(OUT/"forecast-2026-2028.parquet")
    (OUT/"index.html").write_text(explorer(current,report),encoding="utf-8",newline="\n")
    summary={"rows":current.height,"organizations":sorted(set(v for xs in current["organizations"] for v in xs)),
        "team_mapping":"Any 2025 batting stint's historical parent organization, not current roster or rights ownership",
        "multiple_organizations":current.filter(pl.col("organizations").list.len()>1).height,
        "unknown_organization":current.filter(pl.col("organizations").list.contains("Unknown / no 2025 batting stint")).height,
        "no_recent_native_measurement":current.filter(pl.col("general_recent_mlb_measurement")==0).height,
        "position_workload_review":int(current["position_workload_review"].sum()),
        "position_workload_note":"Diagnostic: direct position runs exceed the fixed 600-PA accounting envelope by >1 run; not a physical limit or post-hoc forecast correction.",
        "missing_names":current["player_name"].null_count(),"display_only_identity_hash":sha256_file(identity_path),
        "display_only_name_capture_sha256":sha256_file(display_capture) if display_capture.exists() else None,
        "name_note":"ID/name-only public lookup fills missing display names; no stats, affiliations, roster status, or model inputs requested/changed.",
        "batting_and_pa_unchanged":True,"old_packages_unchanged":True,"development_only":True,
        "release_gate":report["integrated"]["release_as_development"],"confirmation_support":report["integrated"]["confirmation_support"],
        "team_source_hashes":team_hashes,"current_selections":f.select("component","horizon","selected_model").unique().sort("component","horizon").to_dicts()}
    save(OUT/"delivery-report.json",summary)
    PACKAGE.mkdir(exist_ok=True,parents=True)
    for name in ("forecast-2026-2028.parquet","component-predictions.parquet","integrated-predictions.parquet","annual-component-labels.parquet",
                 "score-report.json","fit-manifest.json","delivery-report.json","native-source-certification.json","source-audit.json"):
        shutil.copyfile(OUT/name,PACKAGE/name)
    save(PACKAGE/"manifest.json",{"version":"multiyear-hitter-components-v1","cutoff":"2025-12-31","status":"provisional_development_not_confirmation",
        "source_forecast_sha256":sha256_file(CURRENT),"template_sha256":sha256_file(TEMPLATE),
        "build_code_hashes":{str(p):sha256_file(p) for p in [Path(__file__),Path("scripts/score_multiyear_hitter_components_v1.py"),
            Path("scripts/verify_multiyear_hitter_components_v1.py"),TEMPLATE]},
        "files":{p.name:sha256_file(p) for p in PACKAGE.iterdir() if p.is_file() and p.name!="manifest.json"}})
    print(json.dumps(summary,indent=2))


if __name__=="__main__": main()
