"""Execute the frozen role/mixture screen; no protected-season results."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import warnings

import numpy as np
import polars as pl
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from evaluate_multiyear_hitter_followup_v2 import SOURCE, established_features, p_matrix
from evaluate_multiyear_hitter_v1 import opportunity
from universal_baseball.hitter_horizon_consistency import fixed_groups
from universal_baseball.hitter_role_workload import (
    ROLE_COLUMNS, fit_hurdle, fit_mixture, mature_mask, projection_vintage_audit,
    role_features, workload_states,
)
from universal_baseball.multiyear_hitter_followup import compare_losses, opportunity_mask
from universal_baseball.storage import sha256_file

ROOT = Path("reports/generated/multiyear-hitter-v1")
OUT = Path("model_artifacts/hitter-role-workload-v1-2026-09-22")
OLD = SOURCE.parents[2]
FIELDING = OLD / "mlb-fielding-outcome-inventory-2004-2025/tables/mlb_fielding_usage_2004_2025.parquet"
ANCHOR = Path("model_artifacts/hitter-anchored-development-v1-2026-09-22/historical-anchors.parquet")
REFERENCE = Path("model_artifacts/hitter-anchored-development-v1-2026-09-22/historical-predictions.parquet")
UPDATE = Path("model_artifacts/multiyear-hitter-followup-v2-2026-09-22/opportunity-predictions.parquet")
ROSTER = Path("reports/generated/hitter-roster-feature-challenger-v2/chronological-predictions.parquet")
CURRENT = Path("model_artifacts/multiyear-hitter-followup-v2-2026-09-22/forecast-2026-2028.parquet")
PLAN = Path("docs/hitter-role-workload-v1-plan.md")
YEARS = (2016, 2017, 2018, 2019, 2021, 2022, 2023)
FORMS = ("accepted", "base", "role", "mixture")


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def accepted(panel, augmented, history, updates, year, horizon):
    if year < 2023:
        base = history.filter(pl.col("origin_year") == year).select("player_id",
            pl.col(f"activity_h{horizon}").alias("p0"), pl.col(f"expected_pa_h{horizon}").alias("pa0"))
        changed = updates.filter((pl.col("origin_year") == year) & (pl.col("horizon") == horizon)).select("player_id", "p1")
    else:
        base = opportunity(panel, year, horizon, False).select("player_id",
            pl.col("predicted_any_mlb_pa_probability").alias("p0"),
            pl.col("predicted_expected_mlb_pa").alias("pa0"))
        train = augmented.filter(pl.Series(opportunity_mask(augmented, year, horizon)))
        test = augmented.filter((pl.col("origin_year") == year) & pl.col("established"))
        model = make_pipeline(StandardScaler(), LogisticRegression(C=1., max_iter=2000, random_state=417))
        model.fit(p_matrix(train, horizon), train[f"pa_h{horizon}"].to_numpy() > 0)
        changed = test.select("player_id").with_columns(pl.Series("p1", model.predict_proba(p_matrix(test, horizon))[:, 1]))
    return base.join(changed, on="player_id", how="left", validate="1:1").with_columns(
        pl.coalesce("p1", "p0").alias("accepted_p")).with_columns(
        (pl.col("accepted_p") * pl.col("pa0") / pl.col("p0")).alias("accepted"))


def add_losses(frame, forms):
    y, value = frame["actual_pa"].to_numpy(), frame["actual_value"].to_numpy()
    a = frame["performance_anchor"].to_numpy() / 600
    fields = []
    for name in forms:
        pred = frame[name].to_numpy()
        fields += [pl.Series(name+"_pa_loss", (pred-y)**2), pl.Series(name+"_pa_abs", abs(pred-y)),
                   pl.Series(name+"_pa_bias", pred-y), pl.Series(name+"_value_loss", (pred*a-value)**2)]
        if name+"_p" in frame.columns:
            p = np.clip(frame[name+"_p"].to_numpy(), 1e-8, 1-1e-8)
            active = (y > 0).astype(float)
            fields += [pl.Series(name+"_brier", (p-active)**2),
                       pl.Series(name+"_log", -active*np.log(p)-(1-active)*np.log1p(-p))]
    return frame.with_columns(fields)


def metrics(frame, forms):
    out = {}
    for name in forms:
        result = {}
        for col, key in (("pa_loss", "pa_rmse"), ("value_loss", "value_rmse"),
                         ("pa_abs", "pa_mae"), ("pa_bias", "pa_bias"), ("brier", "brier"), ("log", "log_loss")):
            if name+"_"+col not in frame.columns:
                continue
            mean = float(frame.group_by("origin_year").agg(pl.col(name+"_"+col).mean())[name+"_"+col].mean())
            result[key] = mean**.5 if col.endswith("loss") else mean
        out[name] = result
    return out


def summarize(frame, forms=FORMS):
    groups = {"overall": np.ones(frame.height, bool), **fixed_groups(frame)}
    result = {}
    pairs = [(c, "accepted") for c in ("base", "role", "mixture")] + [("role", "base"), ("mixture", "role")]
    if "roster" in forms:
        pairs += [(c, "roster") for c in ("base", "role", "mixture")]
    for group, mask in groups.items():
        sub = frame.filter(mask)
        if not sub.height:
            continue
        rec = {"rows": sub.height, "active": int((sub["actual_pa"] > 0).sum()), "metrics": metrics(sub, forms)}
        if group in ("overall", "Top50", "Top50 under26"):
            rec["paired"] = {c+"_minus_"+b: {target: compare_losses(sub, c+"_"+target+"_loss", b+"_"+target+"_loss")
                             for target in ("pa", "value")} for c, b in pairs}
        result[group] = rec
    return {"groups": result, "by_origin": {str(y): metrics(frame.filter(pl.col("origin_year") == y), forms)
                                          for y in sorted(frame["origin_year"].unique())}}


def human_audit():
    output, sources, tables = [], [], {}
    for year in (2023, 2024, 2025):
        path = OLD / f"fangraphs-opening-day-workbooks/{year}/opening-day-projections.parquet"
        sources.append(path)
        rows = pl.read_parquet(path)
        tables[year] = rows
        assert rows["season"].unique().to_list() == [year]
        assert rows.unique(["season", "player_id"]).height == rows.height
        selected = rows.filter(pl.col("projected_pa").is_not_null())
        if selected.filter((pl.col("projected_pa") < 0) | (pl.col("projected_pa") > 800)).height:
            raise ValueError("Invalid human workload projection")
        output.append({"season": year, "tracker_rows": rows.height, "projected_pa_rows": selected.height,
            "projected_ip_rows": rows.filter(pl.col("projected_ip").is_not_null()).height})
    return {"vintage": "PA/IP identical across archive years; historical workload vintage rejected",
        "vintage_audit": projection_vintage_audit(tables), "forecast_accuracy_scoring_withheld": True,
        "matched_date_comparison_supported": False, "used_as_predictor": False,
        "missing_projections_treated_as_zero": False, "rows": output}, sources


def main():
    sources = [PLAN, Path(__file__).relative_to(Path.cwd()), Path("src/universal_baseball/hitter_role_workload.py"),
        Path("tests/test_hitter_role_workload.py"), ROOT/"panel.parquet", ROOT/"manifest.json", ROOT/"targets.parquet",
        ROOT/"schedules.parquet", ROOT/"outer-predictions.parquet", SOURCE, FIELDING, ANCHOR, REFERENCE, UPDATE, ROSTER, CURRENT,
        *[Path("scripts")/p for p in ("evaluate_multiyear_hitter_v1.py", "evaluate_multiyear_hitter_followup_v2.py")],
        *[Path("src/universal_baseball")/p for p in ("hitter_model_tournament.py", "multiyear_hitter_followup.py",
            "multiyear_hitter_value.py", "hitter_horizon_consistency.py", "playing_time_model.py", "opportunity_model_v2.py")]]
    panel = pl.read_parquet(ROOT/"panel.parquet").filter(pl.col("origin_year") <= 2023)
    targets = pl.read_parquet(ROOT/"targets.parquet")
    assert targets["season"].max() <= 2025
    audit, human_sources = human_audit()
    sources += human_sources
    hashes = {str(p): sha256_file(p) for p in sources}
    fractions = dict(targets.select("season", "schedule_fraction").unique().iter_rows())
    roles, role_audit = role_features(panel, pl.read_parquet(FIELDING), fractions)
    panel = panel.join(roles, on=["origin_year", "player_id"], validate="1:1", maintain_order="left")
    features = json.loads((ROOT/"manifest.json").read_text())["full_features"]
    assert len(features) == 77 and not any(c.startswith(("war_", "complete_")) or c in ("player_id", "origin_year") for c in features)
    augmented = established_features(panel)
    anchors = pl.read_parquet(ANCHOR)
    refs = pl.read_parquet(REFERENCE).select("origin_year", "player_id", "reference_h1")
    history, updates = pl.read_parquet(ROOT/"outer-predictions.parquet"), pl.read_parquet(UPDATE)
    frames, fit_notes = [], []
    OUT.mkdir(parents=True, exist_ok=True)
    for horizon in (1, 2):
        for year in YEARS:
            train = panel.filter(pl.Series(mature_mask(panel, year, horizon)))
            test = panel.filter(pl.col("origin_year") == year).sort("player_id")
            fit_notes.append({"horizon": horizon, "origin": year, "train_rows": train.height,
                "last_training_target": int(train["origin_year"].max())+horizon, "test_rows": test.height})
            result = test.select("origin_year", "player_id", "age", "stage",
                pl.col(f"pa_h{horizon}").alias("actual_pa"), pl.col(f"war_h{horizon}").alias("actual_value"))
            result = result.with_columns(pl.lit(horizon).alias("horizon"),
                pl.lit(year < 2020 <= year+horizon).alias("pandemic_crossing"))
            y = train[f"pa_h{horizon}"].to_numpy()
            for name, columns in (("base", features), ("role", features+ROLE_COLUMNS)):
                pred, prob = fit_hurdle(train.select(columns).to_numpy(), y, test.select(columns).to_numpy())
                result = result.with_columns(pl.Series(name, pred), pl.Series(name+"_p", prob))
            pred, prob, means = fit_mixture(train.select(features+ROLE_COLUMNS).to_numpy(), y, test.select(features+ROLE_COLUMNS).to_numpy())
            result = result.with_columns(pl.Series("mixture", pred), pl.Series("mixture_p", 1-prob[:, 0]),
                *[pl.Series(f"state_probability_{k}", prob[:, k]) for k in range(4)],
                *[pl.Series(f"state_mean_{k}", means[:, k]) for k in range(4)])
            result = result.join(accepted(panel, augmented, history, updates, year, horizon).select("player_id", "accepted", "accepted_p"),
                on="player_id", validate="1:1", maintain_order="left").join(anchors, on=["origin_year", "player_id"], validate="1:1", maintain_order="left")
            result = result.join(refs, on=["origin_year", "player_id"], validate="1:1", maintain_order="left")
            if result.select("accepted", "performance_anchor", "reference_h1").null_count().to_numpy().sum():
                raise ValueError("Missing baseline or independent rate anchor")
            assert (result["latest_anchor_target"] <= year).all()
            labels = workload_states(result["actual_pa"].to_numpy())
            result = result.with_columns(pl.Series("state_log_loss", -np.log(np.clip(prob[np.arange(len(labels)), labels], 1e-8, 1))),
                pl.Series("state_brier", ((prob-np.eye(4)[labels])**2).sum(axis=1)))
            frames.append(add_losses(result, FORMS))
            print(f"Role/mixture fits complete: origin {year}, horizon {horizon}, {test.height} players", flush=True)
    frame = pl.concat(frames).sort("horizon", "origin_year", "player_id")
    roster = pl.read_parquet(ROSTER).select("origin_year", "player_id", pl.col("prediction_roster_expected_pa").alias("roster"),
        pl.col("prediction_roster_active_probability").alias("roster_p"), pl.col("actual_pa").alias("roster_actual_pa"))
    results = {}
    for horizon in (1, 2):
        part = frame.filter(pl.col("horizon") == horizon)
        normal = part.filter(~pl.col("pandemic_crossing"))
        stress = part.filter(pl.col("pandemic_crossing"))
        rec = {"normal": summarize(normal), "pandemic_stress": summarize(stress),
               "state_scores": {"brier": float(normal.group_by("origin_year").agg(pl.col("state_brier").mean())["state_brier"].mean()),
                                "log_loss": float(normal.group_by("origin_year").agg(pl.col("state_log_loss").mean())["state_log_loss"].mean())}}
        if horizon == 1:
            common = normal.join(roster, on=["origin_year", "player_id"], how="inner", validate="1:1")
            np.testing.assert_allclose(common["actual_pa"], common["roster_actual_pa"])
            common = add_losses(common, ["roster"])
            rec["roster_overlap"] = {"matched_rows": common.height, "screen_rows_without_roster_match": normal.height-common.height,
                "roster_rows_outside_screen": roster.height-common.height, "scores": summarize(common, (*FORMS, "roster"))}
        results[str(horizon)] = rec
    gates = {}
    for h, rec in results.items():
        normal = rec["normal"]["groups"]
        for name in ("base", "role", "mixture"):
            paired = normal["overall"]["paired"][name+"_minus_accepted"]
            gate = {"both_confident": all(paired[t]["interval95"][1] < 0 for t in ("pa", "value")),
                "majority_both": all(paired[t]["improving_origins"] > len(paired[t]["folds"])/2 for t in ("pa", "value")),
                "star_guards": all(normal[g]["metrics"][name][m] <= normal[g]["metrics"]["accepted"][m]
                                   for g in ("Top50", "Top50 under26") for m in ("pa_rmse", "value_rmse"))}
            if h == "1":
                overlap = rec["roster_overlap"]["scores"]["groups"]["overall"]["metrics"]
                gate["strong_benchmark_no_reversal"] = all(overlap[name][m] <= overlap["roster"][m] for m in ("pa_rmse", "value_rmse"))
            gates[h+"_"+name] = gate
    report = {"status": "development_screen_complete_no_automatic_promotion", "forecast_changed": False,
        "protected_outcomes_used": False, "role_audit": role_audit, "human_archive": audit, "fits": fit_notes,
        "results": results, "gates": gates, "limitations": ["Partial value means batting plus replacement only",
            "No immutable matched-date human benchmark", "MLB usage only; no minor-league starts inferred",
            "Intervals condition on fitted models and observed seasons", "Workload states are not injury states",
            "Known-player historical evaluation, not cold-start player-disjoint validation"]}
    assert all(sha256_file(Path(p)) == digest for p, digest in hashes.items())
    # Losses are reproducible from keyed predictions; avoid publishing redundant arrays.
    compact = frame.drop([c for c in frame.columns if c.endswith(("_loss", "_abs", "_bias", "_brier", "_log"))])
    compact.write_parquet(OUT/"predictions.parquet", compression="zstd", compression_level=12)
    save(OUT/"report.json", report)
    save(OUT/"manifest.json", {"sources": hashes, "files": {p: sha256_file(OUT/p) for p in ("predictions.parquet", "report.json")}})
    print(json.dumps({"gates": gates, "overall": {h: r["normal"]["groups"]["overall"]["metrics"] for h, r in results.items()}}, indent=2))


def verify():
    manifest = json.loads((OUT/"manifest.json").read_text())
    for p, digest in manifest["sources"].items():
        assert sha256_file(Path(p)) == digest, p
    for p, digest in manifest["files"].items():
        assert sha256_file(OUT/p) == digest, p
    f = pl.read_parquet(OUT/"predictions.parquet")
    assert f.unique(["horizon", "origin_year", "player_id"]).height == f.height
    assert (f["origin_year"]+f["horizon"]).max() <= 2025
    assert (f["latest_anchor_target"] <= f["origin_year"]).all()
    p = f.select([f"state_probability_{k}" for k in range(4)]).to_numpy()
    q = f.select([f"state_mean_{k}" for k in range(4)]).to_numpy()
    np.testing.assert_allclose(p.sum(axis=1), 1)
    np.testing.assert_allclose(f["mixture"], (p*q).sum(axis=1))
    report = json.loads((OUT/"report.json").read_text())
    assert all(r["last_training_target"] <= r["origin"] for r in report["fits"])
    for name in FORMS:
        assert f[name].is_finite().all() and (f[name] >= 0).all()
    print(json.dumps({"status": "verified", "rows": f.height, "forecast_changed": False}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    warnings.filterwarnings("ignore", message="X does not have valid feature names")
    with threadpool_limits(limits=4):
        if parser.parse_args().verify:
            verify()
        else:
            main()
            verify()
