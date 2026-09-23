"""Score the preregistered three-year confirmation without refitting models."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil

import numpy as np
import polars as pl

from fit_hitter_three_year_opportunity_v1 import BASE, OUT, PACKAGE, ROSTER, save
from universal_baseball.hitter_three_year_opportunity import cohorts, monotone_arrival
from universal_baseball.multiyear_hitter_followup import compare_losses
from universal_baseball.storage import sha256_file

PA_FORMS = ("accepted", "candidate", "ensemble")
VALUE_FORMS = ("delivered", "replacement", "reconciled", "product_control", "ensemble_product")


def mean_origin(f, column):
    return float(f.group_by("origin_year").agg(pl.col(column).mean())[column].mean())


def add_errors(f, forms, target):
    return f.with_columns(*[expr for name in forms for expr in (
        ((pl.col(name)-pl.col(target))**2).alias(name+"_loss"),
        (pl.col(name)-pl.col(target)).abs().alias(name+"_abs"),
        (pl.col(name)-pl.col(target)).alias(name+"_bias"))])


def errors(f, forms, target):
    return {name: {"rmse": float(np.sqrt(mean_origin(f, name+"_loss"))),
                   "mae": mean_origin(f, name+"_abs"), "bias": mean_origin(f, name+"_bias"),
                   "predicted_mean": mean_origin(f, name), "actual_mean": mean_origin(f, target)} for name in forms}


def probability(f, col, target):
    p = np.clip(f[col].to_numpy(), 1e-8, 1-1e-8)
    y = f[target].to_numpy().astype(float)
    scored = f.with_columns(pl.Series("prob_brier", (p-y)**2),
        pl.Series("prob_log", -y*np.log(p)-(1-y)*np.log1p(-p)))
    return {"brier": mean_origin(scored, "prob_brier"), "log_loss": mean_origin(scored, "prob_log"),
            "predicted_probability": mean_origin(f, col), "actual_probability": mean_origin(f, target)}


def summarize(f, *, pa_forms=PA_FORMS, values=True, paired=True):
    f = add_errors(f, pa_forms, "actual_pa")
    if values:
        f = add_errors(f, VALUE_FORMS, "actual_value")
    f = f.with_columns((pl.col("actual_pa") > 0).alias("active"))
    results = {}
    for name, mask in cohorts(f).items():
        g = f.filter(mask)
        if not g.height:
            continue
        record = {"rows": g.height, "origins": g["origin_year"].n_unique(),
            "active": int(g["active"].sum()), "supported": g.height >= 100 and g["origin_year"].n_unique() >= 3,
            "pa": errors(g, pa_forms, "actual_pa"),
            "activity": {form: probability(g, form+"_p", "active") for form in pa_forms}}
        if values:
            record["value"] = errors(g, VALUE_FORMS, "actual_value")
        if paired and name in ("overall", "Never-debuted minors", "Top50"):
            record["paired_pa"] = {base: compare_losses(g, "candidate_loss", base+"_loss") for base in pa_forms if base != "candidate"}
            if values:
                record["paired_value"] = {form: compare_losses(g, form+"_loss", "delivered_loss") for form in ("replacement", "reconciled")}
        if "arrival_by_h" in g.columns and name.startswith(("Never-debuted", "Prospects")):
            record["arrival_by_deadline"] = probability(g, "arrival_by_h", "actual_arrival_by_h")
            record["raw_arrival_by_deadline"] = probability(g, "arrival_raw", "actual_arrival_by_h")
        results[name] = record
    return {"groups": results, "by_origin": {str(y): {
        "pa": errors(g, pa_forms, "actual_pa"),
        **({"value": errors(g, VALUE_FORMS, "actual_value")} if values else {})}
        for y in sorted(f["origin_year"].unique()) for g in [f.filter(pl.col("origin_year") == y)]}}


def path_table(f):
    keys = ["origin_year", "player_id"]
    columns = ["actual_pa", "actual_value", *PA_FORMS, *VALUE_FORMS, "arrival_by_h", "actual_arrival_by_h"]
    path = f.filter(pl.col("horizon") == 1).select(*keys, "age", "stage", "reference_h1", "prospect", "minor_returner", "recent_debut")
    for h in (1, 2, 3):
        path = path.join(f.filter(pl.col("horizon") == h).select(*keys,
            *[pl.col(c).alias(f"{c}_h{h}") for c in columns]), on=keys, validate="1:1", maintain_order="left")
    return path.with_columns(*[pl.sum_horizontal(*[f"{c}_h{h}" for h in (1, 2, 3)]).alias(c)
        for c in ["actual_pa", "actual_value", *PA_FORMS, *VALUE_FORMS]],
        ((pl.col("origin_year") < 2020) & (pl.col("origin_year")+3 >= 2020)).alias("pandemic"))


def paths_summary(path):
    scored = add_errors(add_errors(path, PA_FORMS, "actual_pa"), VALUE_FORMS, "actual_value")
    results = {}
    for name, mask in cohorts(scored).items():
        g = scored.filter(mask)
        if not g.height:
            continue
        rec = {"rows": g.height, "origins": g["origin_year"].n_unique(),
            "supported": g.height >= 100 and g["origin_year"].n_unique() >= 3,
            "pa": errors(g, PA_FORMS, "actual_pa"), "value": errors(g, VALUE_FORMS, "actual_value")}
        if name in ("overall", "Never-debuted minors", "Top50"):
            rec["paired_value"] = {k: compare_losses(g, k+"_loss", "delivered_loss") for k in ("replacement", "reconciled")}
        growth = {}
        for h in (2, 3):
            actual = (g[f"actual_pa_h{h}"]-g["actual_pa_h1"]).to_numpy()
            temp = g.with_columns(pl.Series("actual_growth", actual),
                *[pl.Series(k+"_growth", (g[f"{k}_h{h}"]-g[k+"_h1"]).to_numpy()) for k in PA_FORMS])
            temp = add_errors(temp, [k+"_growth" for k in PA_FORMS], "actual_growth")
            growth[str(h)] = errors(temp, [k+"_growth" for k in PA_FORMS], "actual_growth")
        rec["pa_growth_from_year1"] = growth
        results[name] = rec
    return {"groups": results, "by_origin": {str(y): errors(scored.filter(pl.col("origin_year") == y), VALUE_FORMS, "actual_value")
        for y in sorted(scored["origin_year"].unique())}}


def arrival_descriptions(f, path):
    rows, calibration = [], []
    for h in (1, 2, 3):
        normal = f.filter((pl.col("horizon") == h) & ~pl.col("pandemic") & pl.col("prospect"))
        for year in sorted(normal["origin_year"].unique()):
            for level in ("Upper minors", "Lower minors"):
                for young in (True, False):
                    g = normal.filter((pl.col("origin_year") == year) & (pl.col("stage") == level) & ((pl.col("age") < 23) == young))
                    if g.is_empty():
                        continue
                    calibration.append({"origin": year, "horizon": h, "stage": level, "under23": young, "rows": g.height,
                        "actual_pa": int(g["actual_pa"].sum()), "candidate_pa": float(g["candidate"].sum()),
                        "accepted_pa": float(g["accepted"].sum()),
                        **probability(g, "arrival_by_h", "actual_arrival_by_h")})
    # Outcome-defined groups below are descriptive only; never used for fitting or gates.
    for year in sorted(path["origin_year"].unique()):
        g = path.filter((pl.col("origin_year") == year) & pl.col("prospect"))
        actual = g.select("actual_pa_h1", "actual_pa_h2", "actual_pa_h3").to_numpy()
        first = np.where((actual > 0).any(axis=1), np.argmax(actual > 0, axis=1)+1, 0)
        for arrival in (0, 1, 2, 3):
            group = g.filter(first == arrival)
            if group.height:
                rows.append({"origin": year, "first_observed_mlb_pa_horizon": arrival, "rows": group.height,
                    "interpretation": "future-selected descriptive group, not an adoption test",
                    **{f"actual_mean_pa_h{h}": float(group[f"actual_pa_h{h}"].mean()) for h in (1, 2, 3)},
                    **{f"unconditional_predicted_mean_pa_h{h}": float(group[f"candidate_h{h}"].mean()) for h in (1, 2, 3)}})
    return {"prospective_level_age_calibration": calibration, "descriptive_arrival_paths": rows}


def league_ledger(f):
    targets = pl.read_parquet(BASE/"targets.parquet")
    rows = []
    for (year, h), g in f.partition_by(["origin_year", "horizon"], as_dict=True).items():
        actual = targets.filter(pl.col("season") == year+h)
        outside = actual.join(g.select("player_id"), on="player_id", how="anti")
        assert g["actual_pa"].sum()+outside["mlb_pa"].sum() == actual["mlb_pa"].sum()
        rows.append({"origin": year, "horizon": h, "actual_league_pa": int(actual["mlb_pa"].sum()),
            "actual_outside_original_cohort_pa": int(outside["mlb_pa"].sum()),
            "actual_named_pa": int(g["actual_pa"].sum()),
            **{name+"_named_pa": float(g[name].sum()) for name in PA_FORMS},
            "actual_no_debut_minors_pa": int(g.filter(pl.col("prospect"))["actual_pa"].sum()),
            "candidate_no_debut_minors_pa": float(g.filter(pl.col("prospect"))["candidate"].sum())})
    return sorted(rows, key=lambda r: (r["origin"], r["horizon"]))


def decision(annual, cumulative):
    pa = {}
    for h, r in annual.items():
        groups = r["normal"]["groups"]
        allg = groups["overall"]
        comp = allg["paired_pa"]["accepted"]
        guards = [g for g in groups.values() if g["supported"]]
        prospect = [g for name, g in groups.items() if g["supported"] and name.startswith(("Never-debuted", "Prospects"))]
        pa[h] = {"paired_improvement": comp["interval95"][1] < 0,
            "majority": comp["improving_origins"] > len(comp["folds"])/2,
            "mae": allg["pa"]["candidate"]["mae"] <= allg["pa"]["accepted"]["mae"],
            "no_ensemble_reversal": allg["pa"]["candidate"]["rmse"] <= allg["pa"]["ensemble"]["rmse"],
            "group_mse": all(g["pa"]["candidate"]["rmse"]**2 <= 1.05*g["pa"]["accepted"]["rmse"]**2 for g in guards),
            "prospect_probabilities": all(g["activity"]["candidate"][k] <= 1.05*g["activity"]["accepted"][k]
                                          for g in prospect for k in ("brier", "log_loss"))}
    value = {}
    groups = cumulative["normal"]["groups"]
    for form in ("replacement", "reconciled"):
        comp = groups["overall"]["paired_value"][form]
        value[form] = {"paired_cumulative_improvement": comp["interval95"][1] < 0,
            "majority": comp["improving_origins"] > len(comp["folds"])/2,
            "mae": groups["overall"]["value"][form]["mae"] <= groups["overall"]["value"]["delivered"]["mae"],
            "annual_groups": all(g["value"][form]["rmse"]**2 <= 1.05*g["value"]["delivered"]["rmse"]**2
                for r in annual.values() for g in r["normal"]["groups"].values() if g["supported"]),
            "cumulative_groups": all(g["value"][form]["rmse"]**2 <= 1.05*g["value"]["delivered"]["rmse"]**2
                for g in groups.values() if g["supported"]),
            "prospect_no_reversal": groups["Never-debuted minors"]["value"][form]["rmse"] <= groups["Never-debuted minors"]["value"]["delivered"]["rmse"]}
    return {"pa_gates": pa, "pa_confirmed": all(all(g.values()) for g in pa.values()),
            "value_gates": value, "value_recommended": [k for k, v in value.items() if all(v.values())]}


def main():
    manifest = json.loads((OUT/"fit-manifest.json").read_text())
    for p, digest in manifest["sources"].items():
        assert sha256_file(Path(p)) == digest, p
    for p, digest in manifest["files"].items():
        assert sha256_file(OUT/p) == digest, p
    f, cold = pl.read_parquet(OUT/"predictions.parquet"), pl.read_parquet(OUT/"cold-start.parquet")
    annual = {}
    for h in (1, 2, 3):
        part = f.filter(pl.col("horizon") == h)
        annual[str(h)] = {label: summarize(part.filter(pl.col("pandemic") == stress))
            for label, stress in (("normal", False), ("pandemic_stress", True))}
        print(f"Scored Year {h} including prospects", flush=True)
    path = path_table(f)
    cumulative = {label: paths_summary(path.filter(pl.col("pandemic") == stress))
                  for label, stress in (("normal", False), ("pandemic_stress", True))}
    cold_scores = {str(h): summarize(cold.filter(pl.col("horizon") == h), pa_forms=("candidate", "ensemble"), values=False)
                   for h in (1, 2, 3)}
    roster = pl.read_parquet(ROSTER).select("origin_year", "player_id",
        pl.col("prediction_roster_expected_pa").alias("legacy"), pl.col("prediction_roster_active_probability").alias("legacy_p"),
        pl.col("actual_pa").alias("legacy_actual"))
    common = f.filter((pl.col("horizon") == 1) & ~pl.col("pandemic")).join(roster,
        on=["origin_year", "player_id"], how="inner", validate="1:1")
    np.testing.assert_allclose(common["actual_pa"], common["legacy_actual"])
    legacy_scores = summarize(common, pa_forms=("candidate", "legacy"), values=False)
    report = {"status": "development_confirmation_complete_no_forecast_changes", "annual": annual,
        "cumulative": cumulative, "cold_start": cold_scores, "legacy_overlap": {"rows": common.height, "scores": legacy_scores},
        "arrival": arrival_descriptions(f, path), "league_ledger": league_ledger(f),
        "decision": decision(annual, cumulative), "calibration": manifest["calibration"],
        "protected_outcomes_used": False, "forecasts_changed": False,
        "limits": ["Exposed development evidence, not independent holdout", "Year 3 has only three normal origins",
            "Batting plus replacement, not full WAR", "Cold-start value anchor is not disjoint; value not scored there",
            "Minor-league roles not measured directly", "No joint career simulation or league capacity allocation",
            "Future-selected arrival paths descriptive only", "Missing debut row means no debut in certified MLB history through cutoff"]}
    PACKAGE.mkdir(parents=True, exist_ok=True)
    for name in ("predictions.parquet", "cold-start.parquet", "fit-manifest.json"):
        shutil.copyfile(OUT/name, PACKAGE/name)
    path.write_parquet(PACKAGE/"three-year-paths.parquet", compression="zstd", compression_level=10)
    save(PACKAGE/"report.json", report)
    files = ["predictions.parquet", "cold-start.parquet", "fit-manifest.json", "three-year-paths.parquet", "report.json"]
    save(PACKAGE/"manifest.json", {"files": {p: sha256_file(PACKAGE/p) for p in files},
        "scoring_sources": {str(p): sha256_file(p) for p in [Path(__file__).relative_to(Path.cwd()),
            Path("src/universal_baseball/multiyear_hitter_followup.py"),
            Path("tests/test_hitter_three_year_opportunity_scoring.py")]},
        "protected_outcomes_used": False, "forecasts_changed": False})
    print(json.dumps({"decision": report["decision"], "annual_pa": {h: r["normal"]["groups"]["overall"]["pa"] for h, r in annual.items()},
        "cumulative_value": cumulative["normal"]["groups"]["overall"]["value"]}, indent=2))
    verify()


def verify():
    manifest = json.loads((PACKAGE/"manifest.json").read_text())
    for p, digest in manifest["files"].items():
        assert sha256_file(PACKAGE/p) == digest, p
    for p, digest in manifest["scoring_sources"].items():
        assert sha256_file(Path(p)) == digest, p
    fits = json.loads((PACKAGE/"fit-manifest.json").read_text())
    for p, digest in fits["sources"].items():
        assert sha256_file(Path(p)) == digest, p
    assert all(n["last_target"] <= n["origin"] for n in fits["fits"])
    assert all(n["test_train_shared_players"] == 0 for n in fits["fits"] if n["cold_start"])
    assert all(n["latest_target"] is None or n["latest_target"] <= n["cutoff"] for n in fits["calibration"])
    f = pl.read_parquet(PACKAGE/"predictions.parquet").sort("origin_year", "player_id", "horizon")
    assert f.unique(["origin_year", "player_id", "horizon"]).height == f.height
    assert (f["origin_year"]+f["horizon"]).max() <= 2025
    assert f.group_by("origin_year", "player_id").len()["len"].unique().to_list() == [3]
    np.testing.assert_allclose(f["arrival_by_h"], monotone_arrival(f["arrival_raw"].to_numpy().reshape(-1, 3)).reshape(-1))
    np.testing.assert_allclose(f["replacement"], f["candidate"]*f["performance_anchor"]/600)
    np.testing.assert_allclose(f["reconciled"], f["delivered"]+f["beta"]*(f["candidate"]-f["accepted"])*f["performance_anchor"]/600)
    for col in (*PA_FORMS, *VALUE_FORMS, "arrival_by_h"):
        assert f[col].is_finite().all(), col
    path = pl.read_parquet(PACKAGE/"three-year-paths.parquet")
    for col in (*PA_FORMS, *VALUE_FORMS, "actual_pa", "actual_value"):
        np.testing.assert_allclose(path[col], sum(path[f"{col}_h{h}"] for h in (1, 2, 3)))
    print(json.dumps({"status": "verified", "player_origin_horizon_rows": f.height, "three_year_paths": path.height,
                      "protected_outcomes_used": False, "forecasts_changed": False}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    if parser.parse_args().verify:
        verify()
    else:
        main()
