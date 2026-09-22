"""Score the frozen procedure and deliver an honest three-year player explorer."""
from __future__ import annotations

import json
import importlib.metadata
from pathlib import Path
import numpy as np
import polars as pl

from evaluate_multiyear_hitter_v1 import ROOT, CONTRACT, FORMS, groups
from universal_baseball.storage import sha256_file


def metrics(y, p):
    e = np.asarray(p) - np.asarray(y)
    return {"rows": len(e), "mse": float(np.mean(e**2)), "rmse": float(np.sqrt(np.mean(e**2))),
            "mae": float(np.mean(np.abs(e))), "bias": float(np.mean(e))}


def equal_origin(frame, col, target="war_c3"):
    rows = [metrics(f[target].to_numpy(), f[col].to_numpy()) for f in frame.partition_by("origin_year")]
    mse = float(np.mean([r["mse"] for r in rows]))
    return {"mse": mse, "rmse": float(np.sqrt(mse)), "bias": float(np.mean([r["bias"] for r in rows]))}


def paired_cluster_interval(frame, draws=1000):
    ids, inv = np.unique(frame["player_id"].to_numpy(), return_inverse=True)
    origins = sorted(frame["origin_year"].unique())
    a, b, n = [np.zeros((len(ids), len(origins))) for _ in range(3)]
    y = frame["war_c3"].to_numpy()
    losses = [(frame[c].to_numpy() - y)**2 for c in ("selected_c3", "B0_c3")]
    for j, year in enumerate(origins):
        use = frame["origin_year"].to_numpy() == year
        np.add.at(a[:, j], inv[use], losses[0][use]); np.add.at(b[:, j], inv[use], losses[1][use])
        np.add.at(n[:, j], inv[use], 1)
    rng = np.random.default_rng(417)
    deltas = []
    for _ in range(draws):
        ix = rng.integers(0, len(ids), len(ids))
        counts = n[ix].sum(axis=0)
        deltas.append(float(np.mean((a[ix].sum(axis=0) - b[ix].sum(axis=0)) / counts)))
    return np.quantile(deltas, [.025, .975]).tolist()


def probability_score(y, p):
    p = np.clip(p, 1e-8, 1-1e-8)
    return {"brier": float(np.mean((p-y)**2)), "log_loss": float(-np.mean(y*np.log(p)+(1-y)*np.log1p(-p))),
            "predicted_active": float(p.mean()), "actual_active": float(y.mean())}


def distribution_score(residuals, observations):
    """Empirical-distribution CRPS, without a quadratic pairwise matrix."""
    r = np.sort(np.asarray(residuals))
    obs = np.asarray(observations)
    n = len(r)
    prefix = np.r_[0., np.cumsum(r)]
    i = np.searchsorted(r, obs, side="right")
    mean_abs = (obs*i-prefix[i] + prefix[-1]-prefix[i]-obs*(n-i))/n
    half_pair_distance = np.sum((2*np.arange(1, n+1)-n-1)*r)/(n*n)
    lo, hi = np.quantile(r, [.1, .9])
    return {"crps": float(np.mean(mean_abs-half_pair_distance)), "coverage_80": float(np.mean((obs >= lo) & (obs <= hi))), "width_80": float(hi-lo)}


def evaluate(frame, contract, selection):
    forms = [*FORMS, "selected", "C1"]
    overall = {k: equal_origin(frame, f"{k}_c3") for k in forms}
    pooled = {k: metrics(frame["war_c3"].to_numpy(), frame[f"{k}_c3"].to_numpy()) for k in forms}
    folds = []
    for year in sorted(frame["origin_year"].unique()):
        f = frame.filter(pl.col("origin_year") == year)
        folds.append({"origin": year, "selected": f["selected_form"][0],
                      "scores": {k: metrics(f["war_c3"].to_numpy(), f[f"{k}_c3"].to_numpy()) for k in forms}})
    interval = paired_cluster_interval(frame, contract["bootstrap_draws"])
    annual = {str(h): {k: equal_origin(frame, f"{k}_h{h}", f"war_h{h}") for k in ("B0", "selected")} for h in (2,3)}
    subgroup = {}
    for name, mask in groups(frame).items():
        sub = frame.filter(pl.Series(mask))
        active = int(((sub["pa_h1"] + sub["pa_h2"] + sub["pa_h3"]) > 0).sum())
        if sub.is_empty():
            continue
        a, b = equal_origin(sub, "selected_c3"), equal_origin(sub, "B0_c3")
        limit = contract["guardrails"].get(name)
        supported = limit is not None and sub.height >= contract["subgroup_min_rows"] and active >= contract["subgroup_min_active"]
        passed = a["mse"]-b["mse"] <= limit["mse_worsening_margin"] and abs(a["bias"])-abs(b["bias"]) <= limit["absolute_bias_worsening_margin"] if supported else None
        subgroup[name] = {"rows": sub.height, "active": active, "selected": a, "B0": b, "gate_supported": supported, "passed": passed}
    sensitivity = {}
    for name, years in {"nonpandemic": [2016,2021,2022], "pandemic": [2017,2018,2019], "nonoverlap": [2016,2019,2022]}.items():
        f = frame.filter(pl.col("origin_year").is_in(years))
        sensitivity[name] = {"years": years, "selected": equal_origin(f,"selected_c3"), "B0": equal_origin(f,"B0_c3")}
    # Fixed nonoverlapping blocks expose common season shocks; only three blocks.
    block_deltas = [r["scores"]["selected"]["mse"]-r["scores"]["B0"]["mse"] for r in folds if r["origin"] in [2016,2019,2022]]
    rng = np.random.default_rng(417)
    sensitivity["nonoverlap_block_interval"] = np.quantile(np.mean(rng.choice(block_deltas, size=(1000,3)), axis=1), [.025,.975]).tolist()
    disjoint = []
    key = sha256_file(CONTRACT)[:12]
    for row in selection["folds"]:
        f = pl.read_parquet(ROOT / "fits" / f"{key}-{row['origin']}-disjoint.parquet")
        disjoint.append(f.with_columns(pl.col(f"{row['selected_form']}_c3").alias("selected_c3")))
    df = pl.concat(disjoint)
    sensitivity["player_disjoint"] = {"selected": equal_origin(df,"selected_c3"), "B0": equal_origin(df,"B0_c3")}
    gates = {"paired_interval_favorable": interval[1] < 0,
        "majority_origins": sum(r["scores"]["selected"]["mse"] < r["scores"]["B0"]["mse"] for r in folds) > len(folds)/2,
        "subgroups": all(r["passed"] for r in subgroup.values() if r["gate_supported"]),
        "annual_retention": all(annual[str(h)]["selected"]["mse"] <= annual[str(h)]["B0"]["mse"] * 1.05 for h in (2,3)),
        "season_sensitivities": all(sensitivity[k]["selected"]["mse"] < sensitivity[k]["B0"]["mse"] for k in ("nonpandemic","nonoverlap")),
        "year1_retained": True, "shared_participation_unchanged": True}
    probabilities = {str(h): {"accepted_opportunity": probability_score((frame[f"pa_h{h}"].to_numpy()>0).astype(int), frame[f"activity_h{h}"].to_numpy())} for h in (1,2,3)}
    for h in (2,3):
        probabilities[str(h)]["D3_internal_diagnostic_only"] = probability_score((frame[f"pa_h{h}"].to_numpy()>0).astype(int), frame[f"D3_probability_h{h}"].to_numpy())
    modern = frame.filter(pl.col("year1_evidence").str.starts_with("refit"))
    matched = {"rows": modern.height, "refit_modern": metrics(modern["war_h1"].to_numpy(),modern["year1"].to_numpy()),
               "simple_B0": metrics(modern["war_h1"].to_numpy(),modern["B0_raw_h1"].to_numpy()),
               "candidate_difference": 0., "note": "Shared first year; no replacement of modern stack. Corrected target, same matching rows."}
    return {"status": "development_selected" if all(gates.values()) else "retain_B0_later_years",
        "gates": gates, "equal_origin": overall, "pooled": pooled, "folds": folds, "annual": annual,
        "paired_player_cluster_MSE_delta_interval": interval, "subgroups": subgroup, "sensitivity": sensitivity,
        "participation": probabilities, "year1_matched": matched,
        "scope": "batting plus replacement only; not whole WAR, service-controlled value, or dollars",
        "historical_evidence": "exposed development, not prospective confirmation", "protected_2026_used": False}


def residual_ranges(history, current, chosen):
    rows, scores = [], []
    for form in ("B0", "selected"):
        for year in sorted(history["origin_year"].unique()):
            test = history.filter(pl.col("origin_year")==year)
            for stage in test["stage"].unique():
                for h in (1,2,3,"c3"):
                    horizon = 3 if h == "c3" else h
                    target = "war_c3" if h == "c3" else f"war_h{h}"
                    pred = "year1" if h == 1 else f"{form}_{h if h == 'c3' else f'h{h}'}"
                    prior = history.filter((pl.col("origin_year")+horizon<=year) & (pl.col("stage")==stage))
                    if prior["origin_year"].n_unique()<2 or prior.height<200:
                        continue
                    sub = test.filter(pl.col("stage")==stage)
                    score = distribution_score((prior[target]-prior[pred]).to_numpy(), (sub[target]-sub[pred]).to_numpy())
                    scores.append({"origin":year,"stage":stage,"horizon":h,"form":form,"rows":sub.height,**score})
                    # Display-safety audit only, not an added model-selection gate.
                    threshold = float(np.quantile(prior[pred].to_numpy(), .8))
                    high = sub.filter(pl.col(pred) >= threshold)
                    if high.height:
                        check = distribution_score((prior[target]-prior[pred]).to_numpy(),(high[target]-high[pred]).to_numpy())
                        scores.append({"origin":year,"stage":stage+" / high predicted value","horizon":h,"form":form,"rows":high.height,**check})
    # Current ranges use only fully mature outer residuals, on their own horizon.
    for stage in current["stage"].unique():
        for h in (1,2,3,"c3"):
            horizon = 3 if h == "c3" else h
            target = "war_c3" if h == "c3" else f"war_h{h}"
            pred = "year1" if h == 1 else f"{chosen}_{h if h == 'c3' else f'h{h}'}"
            prior = history.filter((pl.col("origin_year")+horizon<=2025) & (pl.col("stage")==stage))
            if prior["origin_year"].n_unique()<2 or prior.height<200:
                continue
            lo, hi = np.quantile((prior[target]-prior[pred]).to_numpy(), [.1,.9])
            rows.append({"stage":stage,"horizon":str(h),"lower_offset":float(lo),"upper_offset":float(hi),"residual_rows":prior.height,"origins":prior["origin_year"].n_unique()})
    return rows, scores


def explorer(current, report):
    # All data are local, no server-side calls or protected-season content.
    records = json.dumps(current.to_dicts(), allow_nan=False).replace("</", "<\\/")
    template = Path("templates/multiyear-hitter-explorer.html").read_text(encoding="utf-8")
    status = "selected mean forecast for development; not prospectively confirmed" if report["status"]=="development_selected" else "simple baseline retained"
    return template.replace("__PLAYER_DATA__", records).replace("__MODEL_STATUS__", status)


def main():
    contract = json.loads(CONTRACT.read_text())
    selection = json.loads((ROOT/"selection.json").read_text())
    if selection["contract_sha256"] != sha256_file(CONTRACT):
        raise ValueError("Selection contract changed")
    history = pl.read_parquet(ROOT/"outer-predictions.parquet")
    report = evaluate(history, contract, selection)
    chosen = "selected" if report["status"] == "development_selected" else "B0"
    current = pl.read_parquet(ROOT/"current-candidates.parquet")
    offsets, scores = residual_ranges(history,current,chosen)
    report["distribution_checks"] = scores
    report["interval_delivery"] = "withheld: post-fit display-safety audit finds severe undercoverage among high-predicted-value players; no interval retuning in this batch"
    report["delivered_later_year_form"] = selection["current"] if chosen == "selected" else "B0"
    report["contract_sha256"] = sha256_file(CONTRACT)
    report["interval_note"] = "Raw stage-residual nominal 80% offsets retained for diagnosis only. Published player ranges are null because average stage coverage hid severe high-value-player undercoverage. This extra diagnostic does not alter point-model selection."
    all_history = pl.read_parquet(ROOT/"panel.parquet")
    historical_names = all_history.filter(pl.col("player_name").is_not_null()).sort("origin_year",descending=True).unique("player_id",keep="first").select("player_id",pl.col("player_name").alias("historical_name"))
    panel = all_history.filter(pl.col("origin_year")==2025).join(historical_names,on="player_id",how="left",validate="1:1").with_columns(pl.coalesce("player_name","historical_name").alias("player_name"))
    current = current.join(panel.select("player_id","player_name","team_id","level","age_missing","missing_lag0","on_40man","mlb_pa_lag0","home_run_rate_lag0","strikeout_rate_lag0"), on="player_id",validate="1:1")
    current = current.with_columns(pl.col("year1").alias("value_2026"),pl.col(f"{chosen}_h2").alias("value_2027"),pl.col(f"{chosen}_h3").alias("value_2028"),pl.col(f"{chosen}_c3").alias("value_three_years"))
    for h, pred in ((1,"value_2026"),(2,"value_2027"),(3,"value_2028"),("c3","value_three_years")):
        table = pl.DataFrame([r for r in offsets if r["horizon"]==str(h)]).select("stage","lower_offset","upper_offset")
        current = current.join(table,on="stage",how="left",validate="m:1").with_columns((pl.col(pred)+pl.col("lower_offset")).alias(pred+"_lower80"),(pl.col(pred)+pl.col("upper_offset")).alias(pred+"_upper80")).drop("lower_offset","upper_offset")
    # The literal stage-residual intervals were tested, not tuned. Withhold them
    # after the tail-coverage diagnostic failed; keep raw offsets in the audit.
    range_columns = [c for c in current.columns if c.endswith(("_lower80","_upper80"))]
    current = current.with_columns(*[pl.lit(None,dtype=pl.Float64).alias(c) for c in range_columns],
        pl.lit("withheld_pending_conditional_calibration").alias("interval_status"))
    current = current.with_columns(pl.lit(report["delivered_later_year_form"]).alias("delivered_later_year_form"),pl.lit("development; batting + replacement only").alias("scope"))
    current = current.with_columns(((pl.col("mlb_pa_lag0").fill_null(0)>0)&(pl.col("on_40man")==0)).alias("opportunity_roster_review"))
    report["opportunity_limitations"] = {"jointly_reconciled_with_value":False,"current_MLB_rows_absent_40man_list":int(current["opportunity_roster_review"].sum()),
        "note":"The reused opportunity form can discount established hitters, especially when absent from the reconstructed 40-man list. Do not divide direct value by these PA estimates to infer talent or treat the pair as a coherent joint distribution. No hand corrections applied.",
        "examples":current.filter(pl.col("player_id").is_in([592450,624413])).select("player_name","on_40man","mlb_pa_lag0","value_2028","activity_h3","expected_pa_h3").to_dicts()}
    if not np.allclose(current["value_three_years"].to_numpy(),sum(current[f"value_{y}"].to_numpy() for y in (2026,2027,2028))):
        raise ValueError("Annual reconciliation fails")
    if current.height!=3907 or current["player_id"].n_unique()!=3907 or current["war_h1"].null_count()!=3907:
        raise ValueError("Current population/protected target guard failed")
    current.sort("value_three_years",descending=True).write_parquet(ROOT/"player-forecast-2026-2028.parquet")
    report["artifact_hashes"] = {str(p):sha256_file(p) for p in [ROOT/"player-forecast-2026-2028.parquet",ROOT/"outer-predictions.parquet",ROOT/"current-candidates.parquet",ROOT/"selection.json"]}
    report["source_code_hashes"] = {str(p):sha256_file(p) for p in [Path("scripts/materialize_multiyear_hitter_v1.py"),Path("scripts/evaluate_multiyear_hitter_v1.py"),Path(__file__),Path("src/universal_baseball/multiyear_hitter_value.py")]}
    report["package_versions"] = {name:importlib.metadata.version(name) for name in ("numpy","polars","scikit-learn","catboost","lightgbm","xgboost","interpret")}
    (ROOT/"report.json").write_text(json.dumps(report,indent=2,allow_nan=False),encoding="utf-8")
    (ROOT/"interval-offsets.json").write_text(json.dumps(offsets,indent=2),encoding="utf-8")
    (ROOT/"index.html").write_text(explorer(current,report),encoding="utf-8")
    compact = {k:v for k,v in report.items() if k!="distribution_checks"}
    Path("docs/multiyear-hitter-v1-result.json").write_text(json.dumps(compact,indent=2),encoding="utf-8")
    package = Path("model_artifacts/multiyear-hitter-development-2026-09-22")
    package.mkdir(parents=True,exist_ok=True)
    current.sort("value_three_years",descending=True).write_parquet(package/"forecast-2026-2028.parquet")
    history.write_parquet(package/"outer-predictions.parquet")
    (package/"report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    (package/"interval-offsets.json").write_text(json.dumps(offsets,indent=2),encoding="utf-8")
    (package/"source-manifest.json").write_text((ROOT/"manifest.json").read_text(encoding="utf-8"),encoding="utf-8")
    (package/"selection.json").write_text(json.dumps(selection,indent=2),encoding="utf-8")
    (package/"manifest.json").write_text(json.dumps({"version":"multiyear-hitter-development-2026-09-22","status":report["status"],"cutoff":"2025-12-31","forecast_seasons":[2026,2027,2028],"protected_outcomes_used":False,"target":contract["target"],"contract_sha256":sha256_file(CONTRACT),"files":{p.name:sha256_file(p) for p in sorted(package.iterdir()) if p.name!="manifest.json"}},indent=2),encoding="utf-8")
    print(json.dumps({"status":report["status"],"gates":report["gates"],"scores":report["equal_origin"],"interval":report["paired_player_cluster_MSE_delta_interval"],"current":report["delivered_later_year_form"]},indent=2))


if __name__ == "__main__":
    main()
