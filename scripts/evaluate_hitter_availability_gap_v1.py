"""Fixed position-adjusted workload-gap test and unreconciled league ledger."""
import json
from datetime import date
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.impute import SimpleImputer
from sklearn.linear_model import PoissonRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from universal_baseball.hitter_anchored_development import EXTRA_FEATURES, attach_anchors
from universal_baseball.hitter_availability_gap import CONTEXT, GAPS, build_gap_features
from universal_baseball.hitter_health_budget import exposure_training, budget_ledger, normalize_records
from universal_baseball.hitter_horizon_consistency import fixed_groups
from universal_baseball.multiyear_hitter_followup import compare_losses
from universal_baseball.storage import sha256_file

BASE = Path("reports/generated/multiyear-hitter-v1")
PRIOR = Path("model_artifacts/hitter-anchored-development-v1-2026-09-22")
CURRENT = Path("model_artifacts/multiyear-hitter-followup-v2-2026-09-22/forecast-2026-2028.parquet")
OLD = Path("C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/universal-baseball-model/reports/generated")
FIELD = OLD / "mlb-fielding-outcome-inventory-2004-2025/tables/mlb_fielding_usage_2004_2025.parquet"
PITCH = OLD / "career-mlb-outcome-inventory-2009-2025/tables/mlb_pitching_2009_2025.parquet"
OUT = Path("model_artifacts/hitter-availability-gap-v1-2026-09-22")
PLAN = Path("docs/hitter-availability-gap-v1-plan.md")
YEARS = [2019, 2021, 2022, 2023]


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def mean(frame, col):
    return float(np.mean([g[col].to_numpy().mean() for g in frame.sort(["origin_year", "player_id"]).partition_by("origin_year", maintain_order=True)]))


def scores(frame, form):
    mse = mean(frame, form+"_loss")
    return {"pa_mse": mse, "pa_rmse": float(np.sqrt(mse)), "pa_mae": mean(frame, form+"_mae"),
            "pa_bias": mean(frame, form+"_error"), "fixed_rate_value_mse": mean(frame, form+"_value_loss")}


def evaluate(frame):
    ordinary = frame.filter(pl.col("origin_year") != 2019)
    result = {}
    for name, f in (("all", frame), ("ordinary", ordinary)):
        groups = {"overall": np.ones(f.height, dtype=bool), **fixed_groups(f),
                  "measured_regular": f["gap_measured_0"].to_numpy() > 0}
        result[name] = {group: {"rows": g.height, "origins": g["origin_year"].n_unique(),
            **{form: scores(g, form) for form in ("E", "T", "P")}} for group, mask in groups.items()
            for g in [f.filter(pl.Series(mask))] if g.height}
    paired = {form: compare_losses(ordinary, "P_loss", form+"_loss") for form in ("E", "T")}
    affected = ordinary.filter(pl.col("gap_measured_0") > 0)
    affected_supported = affected.height >= 100 and affected["origin_year"].n_unique() >= 2
    health_pair = compare_losses(affected, "P_loss", "T_loss") if affected_supported else None
    normal = result["ordinary"]["overall"]
    gates = {"paired_pa": paired["T"]["interval95"][1] < 0,
        "majority_origins": paired["T"]["improving_origins"] >= 2,
        "ordinary_mae": normal["P"]["pa_mae"] <= normal["T"]["pa_mae"],
        "regular_pair": affected_supported and health_pair["interval95"][1] < 0,
        "regular_mae": affected_supported and result["ordinary"]["measured_regular"]["P"]["pa_mae"] <= result["ordinary"]["measured_regular"]["T"]["pa_mae"],
        "ordinary_value": normal["P"]["fixed_rate_value_mse"] <= 1.01*normal["T"]["fixed_rate_value_mse"],
        "supported_group_value": all(g["P"]["fixed_rate_value_mse"] <= 1.05*g["T"]["fixed_rate_value_mse"]
            for scope in result.values() for g in scope.values() if g["rows"] >= 100 and g["origins"] >= 3),
        "calendar_stress": all(result["all"]["overall"]["P"][key] <= 1.05*result["all"]["overall"]["T"][key]
            for key in ("pa_mse", "fixed_rate_value_mse"))}
    return {"eligible_for_further_validation": all(gates.values()), "gates": gates, "scores": result,
            "ordinary_paired": paired, "regular_paired": health_pair,
            "per_origin": {str(y): {form: scores(frame.filter(pl.col("origin_year") == y), form) for form in ("E", "T", "P")}
                for y in YEARS}, "direct_reference_value_mse": mean(frame, "reference_value_loss")}


def league_audit(targets, schedules, panel, predictions):
    annual = targets.group_by("season").agg(pl.col("mlb_pa").sum(), pl.col("component_war").sum()).sort("season")
    pitching = pl.read_parquet(PITCH).filter(pl.col("season") <= 2025).group_by("season").agg(pl.col("pitching_bf").sum())
    joint = annual.join(pitching, on="season", validate="1:1")
    assert joint.height == annual.height and (joint["mlb_pa"] == joint["pitching_bf"]).all()
    fractions = {r["season"]: 2*r["completed_games"]/(162*r["teams"]) for r in schedules.iter_rows(named=True)}
    pools = {r["season"]: r["mlb_pa"]/fractions[r["season"]] for r in annual.iter_rows(named=True)}
    totals = {r["season"]: r for r in annual.iter_rows(named=True)}
    for year, row in totals.items():
        assert abs(row["component_war"]-570*fractions[year]) < 1e-7
    current = pl.read_parquet(CURRENT)
    assert all(current[c].null_count() == current.height for c in ("war_h1", "war_h2", "war_h3"))
    budget = float(np.median([pools[y] for y in (2023, 2024, 2025)]))
    current_rows = [{"season": 2025+h, **budget_ledger(float(current[f"expected_pa_h{h}"].sum()),
        float(current[f"value_{2025+h}"].sum()), budget, 570.)} for h in (1, 2, 3)]
    stage_rows = [{"stage": stage, "players": f.height,
        **{c: float(f[c].to_numpy().sum()) for c in [*[f"expected_pa_h{h}" for h in (1, 2, 3)],
                                                    *[f"value_{year}" for year in (2026, 2027, 2028)]]}}
        for stage in sorted(current["stage"].unique())
        for f in [current.filter(pl.col("stage") == stage).sort("player_id")]]
    historical = []
    for y in YEARS:
        f = predictions.filter(pl.col("origin_year") == y)
        full = totals[y+2]
        cohort = panel.filter(pl.col("origin_year") == y)
        cohort_pa, cohort_value = int(cohort["pa_h2"].sum()), float(cohort["war_h2"].sum())
        outsiders = targets.filter(pl.col("season") == y+2).join(cohort.select("player_id"), on="player_id", how="anti")
        assert cohort_pa+int(outsiders["mlb_pa"].sum()) == full["mlb_pa"]
        np.testing.assert_allclose(cohort_value+float(outsiders["component_war"].sum()), full["component_war"], atol=1e-8)
        prior = sorted(s for s in pools if s <= y and s != 2020)[-3:]
        pool = float(np.median([pools[s] for s in prior]))
        historical.append({"origin": y, "target": y+2, "known_pool_years": prior,
            "actual_league_pa": full["mlb_pa"], "actual_cohort_pa": cohort_pa,
            "actual_outsider_pa": int(outsiders["mlb_pa"].sum()), "actual_outsider_partial_value": float(outsiders["component_war"].sum()),
            "forms": {form: budget_ledger(float(f[form+"_pa"].sum()), float(f[form+"_value"].sum()), pool, 570.) for form in ("E", "T", "P")}})
    return {"scope": "Partial batting-plus-replacement only; not full WAR", "league_pa_bf_verified_seasons": joint.height,
        "current_budget_years": [2023, 2024, 2025], "current": current_rows, "current_by_cutoff_stage": stage_rows, "historical": historical,
        "rescaled_or_redistributed": False, "full_war_budget_verified": False}


def main():
    sources = [PLAN, Path("docs/hitter-health-budget-v1-plan.md"), Path(__file__).relative_to(Path.cwd()),
        *[Path("src/universal_baseball")/name for name in ("hitter_health_budget.py", "hitter_availability_gap.py",
            "historical_injury_features.py", "hitter_anchored_development.py", "hitter_horizon_consistency.py", "multiyear_hitter_followup.py")],
        BASE/"panel.parquet", BASE/"targets.parquet", BASE/"schedules.parquet", BASE/"manifest.json",
        PRIOR/"historical-anchors.parquet", PRIOR/"historical-predictions.parquet", CURRENT, FIELD, PITCH]
    initial_hashes = {str(p): sha256_file(p) for p in sources}
    panel = pl.read_parquet(BASE/"panel.parquet").filter(pl.col("origin_year").is_between(2016, 2023))
    targets = pl.read_parquet(BASE/"targets.parquet")
    schedules = pl.read_parquet(BASE/"schedules.parquet")
    fractions = {r["season"]: 2*r["completed_games"]/(162*r["teams"]) for r in schedules.iter_rows(named=True)}
    fielding = pl.read_parquet(FIELD).filter(pl.col("season") <= 2023)
    features, reference_notes = build_gap_features(panel, targets, fielding, fractions)
    anchored = attach_anchors(panel, pl.read_parquet(PRIOR/"historical-anchors.parquet"))
    modeled = anchored.join(features, on=["origin_year", "player_id"], validate="1:1").sort(["origin_year", "player_id"])
    columns = json.loads((BASE/"manifest.json").read_text())["full_features"] + EXTRA_FEATURES
    saved = pl.read_parquet(PRIOR/"historical-predictions.parquet")
    forecasts, fit_notes = [], []
    for y in YEARS:
        train, exposure = exposure_training(modeled, y, fractions)
        test = modeled.filter(pl.col("origin_year") == y)
        out = test.select("origin_year", "player_id", "gap_measured_0", "gap_prior_position", "gap_shortfall_0", "gap_expected_pa_0", "gap_observed_pa_0")
        for form, cols in (("E", columns), ("T", columns+CONTEXT), ("P", columns+CONTEXT+GAPS)):
            model = make_pipeline(SimpleImputer(strategy="median", keep_empty_features=True), StandardScaler(), PoissonRegressor(alpha=1., max_iter=2000))
            model.fit(train.select(cols).to_numpy(), train["pa_h2"].to_numpy()/exposure, poissonregressor__sample_weight=exposure)
            raw = model.predict(test.select(cols).to_numpy())
            out = out.with_columns(pl.Series(form+"_q", np.clip(raw, 1, 750)))
            fit_notes.append({"origin": y, "form": form, "train_rows": train.height, "train_origins": sorted(train["origin_year"].unique().to_list()),
                "latest_target": int(train["origin_year"].max())+2, "feature_count": len(cols), "iterations": int(model[-1].n_iter_),
                "clipped": int(((raw < 1)|(raw > 750)).sum())})
        forecasts.append(out)
        print(f"Fixed exposure/position/shortfall fits complete: {y}", flush=True)
    prediction = pl.concat(forecasts).join(saved, on=["origin_year", "player_id"], validate="1:1").sort(["origin_year", "player_id"])
    for form in ("E", "T", "P"):
        prediction = prediction.with_columns((pl.col(form+"_q")*pl.col("activity_h2_challenger")).alias(form+"_pa")).with_columns(
            (pl.col(form+"_pa")*pl.col("performance_anchor")/600).alias(form+"_value"),
            (pl.col(form+"_pa")-pl.col("pa_h2")).alias(form+"_error")).with_columns(
            pl.col(form+"_error").pow(2).alias(form+"_loss"), pl.col(form+"_error").abs().alias(form+"_mae"),
            (pl.col(form+"_value")-pl.col("war_h2")).pow(2).alias(form+"_value_loss"))
    prediction = prediction.with_columns((pl.col("reference_h2")-pl.col("war_h2")).pow(2).alias("reference_value_loss"))
    report = evaluate(prediction)
    report["fit_support"] = fit_notes
    report["feature_support"] = features.group_by("origin_year").agg(pl.len().alias("rows"), pl.col("gap_measured_0").sum().alias("measured_regulars"),
        (pl.col("gap_prior_position") == "unknown").sum().alias("unknown_prior_position")).sort("origin_year").to_dicts()
    report["budget_audit"] = league_audit(targets, schedules, panel, prediction)
    captures, team_ids = [], set()
    for year in range(2015, 2024):
        root = Path("reports/generated/hitter-injury-history-v2") / ("source-2015" if year == 2015 else "source") / "captures"
        transaction, schedule = root/f"transactions-{year}.json", root/f"schedule-{year}.json"
        sources.extend([transaction, schedule])
        captures.append((year, json.loads(transaction.read_text())))
        for day in json.loads(schedule.read_text())["dates"]:
            for game in day["games"]:
                if game["gameType"] == "R":
                    team_ids.update(game["teams"][side]["team"]["id"] for side in ("home", "away"))
    events, source_audit = normalize_records(captures, team_ids, date(2023, 12, 31))
    report["transaction_source_audit_not_a_health_fit"] = source_audit
    report["forecast_changed"] = False
    report["protected_outcomes_used"] = False
    report["limitations"] = ["Workload gap is not a diagnosis", "MLB positional proxy; minors unsupported",
        "Exposed development folds", "No model promotion", "League residuals are not pure outsider talent"]
    assert all(sha256_file(Path(p)) == digest for p, digest in initial_hashes.items())
    OUT.mkdir(parents=True, exist_ok=True)
    prediction.write_parquet(OUT/"historical-predictions.parquet")
    features.write_parquet(OUT/"availability-features.parquet")
    events.write_parquet(OUT/"conservative-injury-events.parquet")
    save(OUT/"reference-support.json", reference_notes)
    save(OUT/"report.json", report)
    save(OUT/"manifest.json", {"status": "diagnostic_complete_no_delivery", "forecast_changed": False, "protected_outcomes_used": False,
        "sources": {str(p): sha256_file(p) for p in sources}, "files": {name: sha256_file(OUT/name) for name in
            ("historical-predictions.parquet", "availability-features.parquet", "conservative-injury-events.parquet", "reference-support.json", "report.json")}})
    print(json.dumps({"gates": report["gates"], "ordinary": report["scores"]["ordinary"]["overall"],
        "regulars": report["scores"]["ordinary"]["measured_regular"], "budget": report["budget_audit"]["current"]}, indent=2))


if __name__ == "__main__":
    with threadpool_limits(limits=4):
        main()
