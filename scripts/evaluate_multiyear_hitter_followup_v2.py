"""Execute the predeclared v2 opportunity and uncertainty comparison, <=2025 only."""
from __future__ import annotations

import json
from pathlib import Path
import warnings

import lightgbm as lgb
import numpy as np
import polars as pl
from sklearn.linear_model import LogisticRegression, PoissonRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from audit_established_hitter_opportunity import _season_rows
from evaluate_multiyear_hitter_v1 import baseline, ridge
from universal_baseball.multiyear_hitter_followup import (
    calibrate, compare_losses, interval_score, opportunity_mask,
)
from universal_baseball.multiyear_hitter_value import training_mask
from universal_baseball.storage import sha256_file

V1 = Path("reports/generated/multiyear-hitter-v1")
OUT = Path("reports/generated/multiyear-hitter-followup-v2")
PLAN = Path("docs/multiyear-hitter-followup-v2-plan.md")
SOURCE = Path("C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/universal-baseball-model/reports/generated/career-mlb-outcome-inventory-2009-2025/tables/mlb_hitting_components_2009_2025.parquet")
OUTERS = [2016, 2017, 2018, 2019, 2021, 2022]
YEARS = [2012, 2013, 2014, 2015, *OUTERS, 2025]
HORIZONS = ["h1", "h2", "h3", "c3"]


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False)+"\n", encoding="utf-8", newline="\n")


def established_features(panel):
    raw = pl.scan_parquet(SOURCE).filter(pl.col("season") <= 2025).collect()
    rows = _season_rows(raw)
    league = rows.group_by("season").agg((pl.col("batting_value").sum()/pl.col("pa").sum()).alias("league_rate"))
    rows = rows.join(league, on="season", validate="m:1").with_columns(
        ((pl.col("batting_value")+1200*pl.col("league_rate"))/(pl.col("pa")+1200)-pl.col("league_rate")).alias("quality"))
    result = panel.join(rows.select(pl.col("season").alias("origin_year"), "player_id", "quality"),
                        on=["origin_year", "player_id"], how="left", validate="1:1", maintain_order="left")
    return result.with_columns(((pl.col("mlb_pa_lag0").fill_null(0)>0) & (pl.col("age_missing")==0)
        & pl.col("age").is_not_null() & pl.col("quality").is_not_null()
        & (pl.max_horizontal("mlb_pa_lag1", "mlb_pa_lag2")>=200)).fill_null(False).alias("established"))


def p_matrix(frame, h):
    return np.column_stack([frame["age"].to_numpy()+h,
        *[np.log1p(frame[f"mlb_pa_lag{lag}"].fill_null(0).to_numpy()) for lag in range(3)],
        frame["quality"].to_numpy()])


def fit_opportunity(panel, history, current):
    rows, fit_notes = [], []
    for year in [*OUTERS, 2025]:
        base = current if year==2025 else history.filter(pl.col("origin_year")==year)
        test = panel.filter((pl.col("origin_year")==year) & pl.col("established"))
        for h in (1, 2, 3):
            train = panel.filter(pl.Series(opportunity_mask(panel, year, h)))
            x, tx = p_matrix(train, h), p_matrix(test, h)
            y = train[f"pa_h{h}"].to_numpy()
            model = make_pipeline(StandardScaler(), LogisticRegression(C=1., max_iter=2000, random_state=417)).fit(x, y>0)
            prob = model.predict_proba(tx)[:, 1]
            workload = make_pipeline(StandardScaler(), PoissonRegressor(alpha=1., max_iter=2000)).fit(x[y>0], y[y>0])
            raw_pa = workload.predict(tx)
            # Attach arrays before joining: joins need not preserve row order.
            scored = test.select("origin_year", "player_id", "stage", pl.col(f"pa_h{h}").alias("actual_pa")).with_columns(
                pl.Series("p1", prob), pl.Series("conditional_pa2", np.clip(raw_pa, 1, 750)), pl.lit(h).alias("horizon")).join(
                base.select("player_id", pl.col(f"activity_h{h}").alias("p0"), pl.col(f"expected_pa_h{h}").alias("pa0")),
                on="player_id", validate="1:1", maintain_order="left")
            scored = scored.with_columns((pl.col("pa0")/pl.col("p0")).alias("conditional_pa0"))
            scored = scored.with_columns((pl.col("p1")*pl.col("conditional_pa0")).alias("pa1"),
                                          (pl.col("p1")*pl.col("conditional_pa2")).alias("pa2"))
            rows.append(scored)
            fit_notes.append({"origin": year, "horizon": h, "train_rows": train.height,
                "latest_training_origin": int(train["origin_year"].max()), "test_rows": test.height,
                "conditional_clipped": int(((raw_pa<1)|(raw_pa>750)).sum()),
                "logistic_intercept": model[-1].intercept_.tolist(), "logistic_coefficients": model[-1].coef_.tolist(),
                "logistic_means": model[0].mean_.tolist(), "logistic_scales": model[0].scale_.tolist(),
                "poisson_intercept": float(workload[-1].intercept_), "poisson_coefficients": workload[-1].coef_.tolist(),
                "poisson_means": workload[0].mean_.tolist(), "poisson_scales": workload[0].scale_.tolist()})
        print(f"Opportunity fits {year} complete", flush=True)
    result = pl.concat(rows)
    result.write_parquet(OUT/"opportunity-predictions.parquet")
    save_json(OUT/"opportunity-fits.json", fit_notes)
    return result


def probability_losses(frame):
    y = (frame["actual_pa"].to_numpy()>0).astype(float)
    cols = []
    for k in (0,1):
        p = np.clip(frame[f"p{k}"].to_numpy(), 1e-8, 1-1e-8)
        cols.extend([pl.Series(f"brier{k}",(p-y)**2), pl.Series(f"log{k}",-y*np.log(p)-(1-y)*np.log1p(-p))])
    for k in (0,1,2):
        e = frame[f"pa{k}"].to_numpy()-frame["actual_pa"].to_numpy()
        cols.extend([pl.Series(f"mse{k}", e**2),pl.Series(f"mae{k}",abs(e))])
    return frame.with_columns(cols)


def mean_loss(frame, col):
    return float(frame.group_by("origin_year").agg(pl.col(col).mean())[col].mean())


def score_opportunity(predictions):
    f = probability_losses(predictions.filter(pl.col("origin_year").is_in(OUTERS)))
    comparisons = {name: compare_losses(f, a, b) for name,a,b in [
        ("brier","brier1","brier0"),("log_loss","log1","log0"),
        ("pa_mse","mse2","mse1"),("pa_mae","mae2","mae1")]}
    horizons = {str(h): {c:mean_loss(g,c) for c in ("brier0","brier1","log0","log1","mse0","mse1","mse2","mae0","mae1","mae2")}
                for h in (1,2,3) for g in [f.filter(pl.col("horizon")==h)]}
    nonpandemic = f.filter(~((pl.col("origin_year")<2020)&(pl.col("origin_year")+pl.col("horizon")>=2020)))
    p1 = {"brier_interval":comparisons["brier"]["interval95"][1]<0,
          "log_loss_interval":comparisons["log_loss"]["interval95"][1]<0,
          "four_origins_both": all(comparisons[k]["improving_origins"]>=4 for k in ("brier","log_loss")),
          "horizon_guards":all(r[a]<=1.05*r[b] for r in horizons.values() for a,b in [("brier1","brier0"),("log1","log0")]),
          "nonpandemic_both":all(mean_loss(nonpandemic,a)<mean_loss(nonpandemic,b) for a,b in [("brier1","brier0"),("log1","log0")])}
    p2 = {"p1_passes":all(p1.values()), "mse_interval":comparisons["pa_mse"]["interval95"][1]<0,
          "mae_lower":comparisons["pa_mae"]["delta"]<0,
          "majority_origins":comparisons["pa_mse"]["improving_origins"]>3,
          "horizon_mae_guards":all(r["mae2"]<=1.05*r["mae1"] for r in horizons.values())}
    return {"selected":"P2" if all(p2.values()) else "P1" if all(p1.values()) else "P0",
        "comparisons":comparisons,"horizons":horizons,"P1_gates":p1,"P2_gates":p2,
        "rows": f.height, "players":f["player_id"].n_unique(),
        "nonpandemic":{c:mean_loss(nonpandemic,c) for c in ("brier0","brier1","log0","log1","mse1","mse2","mae1","mae2")}}


def fixed_mean(panel, manifest, year):
    if year >= 2016:
        path = next((V1/"fits").glob(f"*-{year}-returning.parquet"))
        cached = pl.read_parquet(path)
        return cached.select("player_id",pl.col("year1").alias("h1"),pl.col("D1_h2").alias("h2"),
                             pl.col("D1_h3").alias("h3"),pl.col("D1_c3").alias("c3"))
    test = panel.filter(pl.col("origin_year")==year)
    b = baseline(panel,manifest,year,False)
    predictions = [b[:,0]]
    x, tx = panel.select(manifest["full_features"]).to_numpy(),test.select(manifest["full_features"]).to_numpy()
    for h in (2,3):
        mask = training_mask(panel,year,h)
        predictions.append(ridge().fit(x[mask],panel[f"war_h{h}"].to_numpy()[mask]).predict(tx))
    return test.select("player_id").with_columns(*[pl.Series(f"h{i+1}",p) for i,p in enumerate(predictions)],
                                                pl.Series("c3",sum(predictions)))


def fit_quantiles(panel, manifest, fingerprint):
    rows, notes = [], []
    x = panel.select(manifest["full_features"]).to_numpy()
    for year in YEARS:
        cache = OUT/"fits"/f"{fingerprint}-{year}.parquet"
        note_path = cache.with_suffix(".json")
        if cache.exists() and note_path.exists():
            rows.append(pl.read_parquet(cache)); notes.extend(json.loads(note_path.read_text())); continue
        test = panel.filter(pl.col("origin_year")==year)
        means = fixed_mean(panel,manifest,year)
        test = test.join(means,on="player_id",validate="1:1")
        tx = test.select(manifest["full_features"]).to_numpy()
        annual, year_notes = [], []
        for key in HORIZONS:
            h = 3 if key=="c3" else int(key[-1])
            target = "war_"+key
            mask = training_mask(panel,year,h) & np.isfinite(panel[target].to_numpy())
            predictions = []
            for alpha in (.1,.9):
                model = lgb.LGBMRegressor(objective="quantile",alpha=alpha,n_estimators=300,learning_rate=.03,
                    num_leaves=7,max_depth=3,min_child_samples=100,reg_lambda=8,random_state=417,n_jobs=4,verbosity=-1)
                predictions.append(model.fit(x[mask],panel[target].to_numpy()[mask]).predict(tx))
            lo, hi = predictions
            year_notes.append({"origin":year,"horizon":key,"train_rows":int(mask.sum()),
                               "crossed_endpoints":int((lo>hi).sum())})
            annual.append(test.select("origin_year","player_id","stage",pl.col(target).alias("actual"),
                pl.col(key).alias("mean")).with_columns(pl.lit(key).alias("horizon"),
                    pl.Series("raw_lo",np.minimum(lo,hi)),pl.Series("raw_hi",np.maximum(lo,hi))))
        combined = pl.concat(annual)
        combined.write_parquet(cache); save_json(note_path,year_notes)
        rows.append(combined); notes.extend(year_notes)
        print(f"Quantile fits {year} complete",flush=True)
    result = pl.concat(rows)
    result.write_parquet(OUT/"raw-quantile-predictions.parquet")
    save_json(OUT/"quantile-fit-notes.json",notes)
    return result


def interval_metrics(frame, prefix):
    y, lo, hi = (frame[c].to_numpy() for c in ("actual",prefix+"_lo",prefix+"_hi"))
    scored = frame.with_columns(pl.Series("loss",interval_score(y,lo,hi)),
        pl.Series("covered",((y>=lo)&(y<=hi)).astype(float)),pl.Series("width",hi-lo))
    return {"rows":frame.height,"origins":frame["origin_year"].n_unique(),
        "coverage":mean_loss(scored,"covered"),"width":mean_loss(scored,"width"),"score":mean_loss(scored,"loss")}


def score_quantiles(raw):
    results, calibrated = {}, []
    for key in HORIZONS:
        h = 3 if key=="c3" else int(key[-1])
        history = raw.filter(pl.col("horizon")==key)
        rows = [calibrate(history,history.filter(pl.col("origin_year")==year),year,h) for year in [*OUTERS,2025]]
        all_rows = pl.concat(rows)
        calibrated.append(all_rows)
        outer = all_rows.filter(pl.col("origin_year").is_in(OUTERS))
        valid = outer.filter(pl.all_horizontal(*[pl.col(c).is_not_null() for c in ("q0_lo","q0_hi","q2_lo","q2_hi")]))
        valid = valid.with_columns(*[pl.Series("loss"+k,interval_score(valid["actual"],valid[f"q{k}_lo"],valid[f"q{k}_hi"])) for k in ("0","2")])
        comparison = compare_losses(valid,"loss2","loss0")
        groups = {}
        for stage in sorted(outer["stage"].unique()):
            for label,selector in [("all",pl.lit(True)),("high_prior",pl.col("high_prior")),("high_current",pl.col("high_current"))]:
                cell = valid.filter((pl.col("stage")==stage)&selector)
                if cell.is_empty(): continue
                m = interval_metrics(cell,"q2")
                groups[stage+" / "+label] = {**m,"supported":m["rows"]>=100 and m["origins"]>=3}
        overall = {k:interval_metrics(valid,k) for k in ("q0","raw","q2")}
        nonpandemic = valid.filter(~((pl.col("origin_year")<2020)&(pl.col("origin_year")+h>=2020)))
        nonpandemic_delta = mean_loss(nonpandemic,"loss2")-mean_loss(nonpandemic,"loss0")
        gates = {"three_origins":valid["origin_year"].n_unique()>=3,"paired_interval":comparison["interval95"][1]<0,
            "majority_origins":comparison["improving_origins"]>valid["origin_year"].n_unique()/2,
            "overall_coverage":overall["q2"]["coverage"]>=.75,
            "supported_group_coverage":all(r["coverage"]>=.75 for r in groups.values() if r["supported"]),
            "nonpandemic":nonpandemic_delta<0}
        results[key] = {"accepted":all(gates.values()),"gates":gates,"comparison":comparison,"overall":overall,
            "groups":groups,"nonpandemic_score_delta":nonpandemic_delta,"unscored_rows":outer.height-valid.height}
    pl.concat(calibrated).write_parquet(OUT/"calibrated-predictions.parquet")
    return results


def main():
    OUT.mkdir(parents=True,exist_ok=True); (OUT/"fits").mkdir(exist_ok=True)
    sources = [PLAN,V1/"panel.parquet",V1/"outer-predictions.parquet",V1/"player-forecast-2026-2028.parquet",SOURCE,
        Path(__file__),Path("src/universal_baseball/multiyear_hitter_followup.py")]
    hashes = {str(p):sha256_file(p) for p in sources}
    fingerprint = __import__("hashlib").sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()[:16]
    manifest = {"plan":str(PLAN),"hashes":hashes,"cache_key":fingerprint,"protected_2026_used":False,
        "outer_origins":OUTERS,"bootstrap_draws":1000,"stage_threshold":"within stage, calibration-pool 80th percentile",
        "Q0":"all mature origins >=2, stage >=200 rows, same residual recipe as v1",
        "evidence":"exposed chronological development; no independent prospective confirmation"}
    save_json(OUT/"source-manifest.json",manifest)
    panel = pl.read_parquet(V1/"panel.parquet")
    if panel["origin_year"].max()!=2025 or panel.filter(pl.col("origin_year")==2025)["war_h1"].null_count()!=3907:
        raise ValueError("Protected target boundary failed")
    history, current = [pl.read_parquet(V1/name) for name in ("outer-predictions.parquet","player-forecast-2026-2028.parquet")]
    opportunity = fit_opportunity(established_features(panel),history,current)
    p_result = score_opportunity(opportunity)
    save_json(OUT/"opportunity-result.json",p_result)
    print("Opportunity selected: "+p_result["selected"],flush=True)
    raw = fit_quantiles(panel,json.loads((V1/"manifest.json").read_text()),fingerprint)
    q_result = score_quantiles(raw)
    report = {"opportunity":p_result,"uncertainty":q_result,"source_manifest":manifest,
              "means_changed":False,"protected_2026_used":False}
    save_json(OUT/"report.json",report)
    print(json.dumps({"opportunity":p_result["selected"],"uncertainty":{k:{"accepted":v["accepted"],"gates":v["gates"]} for k,v in q_result.items()}},indent=2),flush=True)


if __name__=="__main__":
    warnings.filterwarnings("ignore",message="X does not have valid feature names")
    with threadpool_limits(limits=4):
        main()
