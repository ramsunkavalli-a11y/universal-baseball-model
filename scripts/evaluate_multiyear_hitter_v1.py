"""Frozen, nested three-year hitter comparison; never reads 2026 outcomes."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import warnings

import numpy as np
import polars as pl
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from universal_baseball.multiyear_hitter_value import training_mask
from universal_baseball.hitter_model_tournament import make_engine_models, _fit_standard_two_part
from universal_baseball.hitter_target_architecture import feature_columns, matrix_from_panel, _lgbm_classifier, _lgbm_regressor
from universal_baseball.opportunity_model_v2 import OpportunityFold, fit_universal_hitter_opportunity_form
from universal_baseball.playing_time_model import PT_FORM_U, build_playing_time_design, predict_playing_time_hurdle
from universal_baseball.storage import sha256_file

ROOT = Path("reports/generated/multiyear-hitter-v1")
CONTRACT = Path("docs/multiyear-hitter-v1-contract.json")
RICH = Path("reports/generated/hitter-value-panel-v2/tables/modeling-panel.parquet")
CURRENT = Path("model_artifacts/hitter-full-2026-confirmation-forecast-2026-09-20/forecast-inputs-2025.parquet")
FORMS = ("B0", "D1", "D2", "D3")
SEED = 417


def ridge():
    return make_pipeline(SimpleImputer(strategy="median", keep_empty_features=True), StandardScaler(), Ridge(alpha=20.))


def groups(frame):
    age = frame["age"].to_numpy()
    pa = frame["pa_lag0"].fill_null(0).to_numpy()
    return {**{s: frame["stage"].to_numpy() == s for s in ("Current MLB", "Upper minors", "Lower minors", "Inactive / unknown")},
            "age_under_23": age < 23, "age_23_29": (age >= 23) & (age < 30), "age_30_plus": age >= 30,
            "current_PA_under_100": pa < 100, "current_PA_100_plus": pa >= 100}


def baseline(panel, manifest, origin, disjoint):
    test = panel.filter(pl.col("origin_year") == origin)
    ids = test["player_id"].to_numpy() if disjoint else []
    x = panel.select(manifest["base_features"]).to_numpy()
    tx = test.select(manifest["base_features"]).to_numpy()
    result = []
    for h in (1, 2, 3):
        mask = training_mask(panel, origin, h, ids)
        result.append(ridge().fit(x[mask], panel[f"war_h{h}"].to_numpy()[mask]).predict(tx))
    return np.column_stack(result)


def freeze(panel, manifest):
    if CONTRACT.exists():
        raise ValueError("Contract already exists; do not overwrite after scoring")
    folds = []
    for origin in range(2016, 2023):
        if origin == 2020:
            continue
        inner = [y for y in range(2012, origin - 2) if y != 2020]
        folds.append({"origin": origin, "inner_origins": inner,
                      "test_rows": panel.filter(pl.col("origin_year") == origin).height,
                      "pandemic_window": origin < 2020 <= origin + 3})
    # Freeze numerical margins using ONLY the earliest B0 development fold.
    pilot = panel.filter(pl.col("origin_year") == 2012)
    pred = baseline(panel, manifest, 2012, True).sum(axis=1)
    err = pred - pilot["war_c3"].to_numpy()
    guardrails = {}
    for name, mask in groups(pilot).items():
        e = err[mask]
        positives = int((pilot["pa_h1"].to_numpy()[mask] + pilot["pa_h2"].to_numpy()[mask] + pilot["pa_h3"].to_numpy()[mask] > 0).sum())
        if len(e) >= 200 and positives >= 30:
            guardrails[name] = {"pilot_rows": len(e), "pilot_active": positives,
                "mse_worsening_margin": float(.05 * np.mean(e ** 2)),
                "absolute_bias_worsening_margin": float(max(.05 * np.sqrt(np.mean(e ** 2)), 2 * np.std(e) / np.sqrt(len(e))))}
    artifacts = [ROOT / "panel.parquet", ROOT / "targets.parquet", ROOT / "schedules.parquet", RICH, CURRENT]
    support = []
    for year in range(2012, 2026):
        test = panel.filter(pl.col("origin_year") == year)
        if test.is_empty():
            continue
        support.append({"origin": year, "rows": test.height,
            "train_rows_h3_player_disjoint": int(training_mask(panel, year, 3, test["player_id"].to_numpy()).sum()),
            "train_rows_h3": int(training_mask(panel, year, 3).sum()),
            "active_h3": int((test["pa_h3"].fill_null(0) > 0).sum()) if year <= 2022 else None})
    contract = {"version": "multiyear_hitter_v1", "frozen_before_challenger_scores": True,
        "seed": SEED, "folds": folds, "support": support, "features": manifest["full_features"],
        "base_features": manifest["base_features"], "source_hashes": {str(p): sha256_file(p) for p in artifacts},
        "ridge_alpha": 20., "catboost": {"iterations": 400, "learning_rate": .03, "depth": 4, "l2_leaf_reg": 8., "thread_count": 4},
        "selection": "mean inner-origin cumulative-3 MSE, player-disjoint inner fit, mature labels; ties D1 then D2 then D3",
        "inner_minimum": 2, "primary": "equal-origin cumulative-3 MSE, selected procedure minus B0",
        "year1": "refit fixed five-member existing batting ensemble when at least two rich-panel training origins exist; B0 fallback otherwise or for unmatched players; same in every annual form; all inner fit IDs excluded",
        "target": manifest["target"], "cutoff": "Dec-31 reconstructed historical vintage; origin+h<=cutoff; fixed forecasts never receive intervening outcomes",
        "forms": [*FORMS, "C1_diagnostic_only"], "calibration": "delivered activity/workload is the SAME separately refit accepted PT_FORM_U for all forms; zero permissible difference. D3 internal probabilities reported separately, not delivered",
        "guardrails": guardrails, "guardrail_basis": "2012 disjoint B0 pilot only; 5% of reference MSE, bias max(5% reference RMSE, two reference standard errors). Practical exploratory tolerances, not established domain standards.",
        "annual_mse_worsening_relative_limit": .05,
        "decision": "favorable paired player-cluster 95% interval, majority improving origins, all supported subgroup/annual guards, nonpandemic and predeclared nonoverlap [2016,2019,2022] no reversal; otherwise B0 later years",
        "bootstrap_draws": 1000, "subgroup_min_rows": 200, "subgroup_min_active": 30,
        "intervals": "stage-specific prior eligible selected/B0 outer residuals, minimum 2 origins and 200 rows; literal 10th/90th quantiles; cumulative uses cumulative residuals, never sum annual quantiles; exploratory",
        "external_whole_WAR": "unavailable in recovered source inventory; no complete WAR claim",
        "no_2026_results": True, "coverage": manifest["coverage"], "calendar_2020": [r for r in manifest["annual_target_totals"] if r["season"] == 2020]}
    CONTRACT.write_text(json.dumps(contract, indent=2), encoding="utf-8")
    print(json.dumps({"contract": str(CONTRACT), "folds": folds, "guardrails": guardrails}, indent=2), flush=True)


def limit_model(model):
    p = model.get_params()
    if "n_jobs" in p:
        model.set_params(n_jobs=4)
    return model


def shared_year1(panel, origin, disjoint, fallback):
    rich = pl.read_parquet(RICH)
    scoring = pl.read_parquet(CURRENT) if origin == 2025 else rich.filter(pl.col("origin_year") == origin)
    train = rich.filter(pl.col("origin_year") < origin)
    cohort = panel.filter(pl.col("origin_year") == origin)
    if disjoint:
        train = train.filter(~pl.col("player_id").is_in(cohort["player_id"].to_list()))
    if train["origin_year"].n_unique() < 2 or scoring.is_empty():
        return fallback, np.full(cohort.height, "B0 historical fallback")
    # Replace only outcomes; preserve the existing cutoff-only rich predictors.
    train = train.drop("target_component_war", "target_conditional_component_war_per_600").join(
        panel.select("origin_year", "player_id", pl.col("war_h1").alias("target_component_war")),
        on=["origin_year", "player_id"], how="inner", validate="1:1").with_columns(
        pl.when(pl.col("target_mlb_pa") > 0).then(pl.col("target_component_war") * 600 / pl.col("target_mlb_pa")).otherwise(0).alias("target_conditional_component_war_per_600"))
    columns = feature_columns(rich)
    x, tx = matrix_from_panel(train, columns), matrix_from_panel(scoring, columns)
    y, active, pa = (train[c].to_numpy() for c in ("target_component_war", "target_mlb_active", "target_mlb_pa"))
    use = active == 1
    clf = limit_model(_lgbm_classifier(SEED)).fit(x, active)
    prob = clf.predict_proba(tx)[:, 1]
    direct = limit_model(_lgbm_regressor(SEED + 1)).fit(x, y).predict(tx)
    pt = limit_model(_lgbm_regressor(SEED + 3)).fit(x[use], pa[use]).predict(tx)
    rate = limit_model(_lgbm_regressor(SEED + 4)).fit(x[use], train["target_conditional_component_war_per_600"].to_numpy()[use], sample_weight=np.sqrt(np.maximum(pa[use], 1))).predict(tx)
    members = [direct, prob * np.clip(pt, 0, 750) * np.clip(rate, -5, 10) / 600]
    for engine in ("xgboost", "ebm", "ridge"):
        models = make_engine_models(engine, SEED, "balanced")
        limit_model(models.classifier); limit_model(models.regressor)
        p, conditional = _fit_standard_two_part(models, x, tx, active, y)
        members.append(p * conditional)
    lookup = dict(zip(scoring["player_id"].to_list(), np.mean(members, axis=0)))
    prediction = np.array([lookup.get(i, fallback[j]) for j, i in enumerate(cohort["player_id"])])
    labels = np.array(["refit existing five-model batting stack" if i in lookup else "B0 unmatched-player fallback" for i in cohort["player_id"]])
    return prediction, labels


def opportunity(panel, origin, h, disjoint):
    test = panel.filter(pl.col("origin_year") == origin)
    mask = training_mask(panel, origin, h, test["player_id"].to_numpy() if disjoint else [])
    train = panel.filter(pl.Series(mask))
    # Reuse the accepted model AND its no-pandemic-crossing training contract.
    train = train.filter(~((pl.col("origin_year") < 2020) & (pl.col("origin_year") + h >= 2020)))
    def predictors(f):
        return f.select("player_id", pl.col("age").alias("age_years"), "as_of_level_group", "on_40man",
            pl.col("mlb_pa_lag0").fill_null(0).alias("current_season_mlb_pa"),
            (pl.col("pa_lag0").fill_null(0) - pl.col("mlb_pa_lag0").fill_null(0)).alias("current_season_milb_pa"))
    folds = [OpportunityFold(y, y+h, predictors(f), f.select("player_id", pl.col(f"pa_h{h}").cast(pl.Int64).alias("next_year_mlb_pa")))
             for y in sorted(train["origin_year"].unique()) for f in [train.filter(pl.col("origin_year") == y)]]
    fit = fit_universal_hitter_opportunity_form(folds, form=PT_FORM_U)
    forecast = predict_playing_time_hurdle(fit, build_playing_time_design(predictors(test), form=PT_FORM_U))
    return test.select("player_id").join(forecast, on="player_id", validate="1:1")


def fit_origin(panel, manifest, contract, origin, disjoint):
    fingerprint = sha256_file(CONTRACT)[:12]
    path = ROOT / "fits" / f"{fingerprint}-{origin}-{'disjoint' if disjoint else 'returning'}.parquet"
    if path.exists():
        return pl.read_parquet(path)
    print(f"Fitting origin {origin}, player-disjoint={disjoint}", flush=True)
    test = panel.filter(pl.col("origin_year") == origin)
    ids = test["player_id"].to_numpy() if disjoint else []
    b = baseline(panel, manifest, origin, disjoint)
    shared, evidence = shared_year1(panel, origin, disjoint, b[:, 0])
    out = test.select("origin_year", "player_id", "age", "stage", "pa_lag0", "war_h1", "war_h2", "war_h3", "war_c3", "pa_h1", "pa_h2", "pa_h3")
    out = out.with_columns(pl.Series("year1", shared), pl.Series("year1_evidence", evidence), pl.Series("B0_raw_h1", b[:, 0]))
    x = panel.select(manifest["full_features"]).to_numpy()
    tx = test.select(manifest["full_features"]).to_numpy()
    for h in (2, 3):
        mask = training_mask(panel, origin, h, ids)
        y = panel[f"war_h{h}"].to_numpy()[mask]
        active = (panel[f"pa_h{h}"].to_numpy()[mask] > 0).astype(int)
        d1 = ridge().fit(x[mask], y).predict(tx)
        models = make_engine_models("catboost", SEED, "smooth")
        models.classifier.set_params(thread_count=4); models.regressor.set_params(thread_count=4)
        d2 = models.regressor.fit(x[mask], y).predict(tx)
        models = make_engine_models("catboost", SEED, "smooth")
        models.classifier.set_params(thread_count=4); models.regressor.set_params(thread_count=4)
        p, conditional = _fit_standard_two_part(models, x[mask], tx, active, y)
        out = out.with_columns(*[pl.Series(f"{k}_h{h}", v) for k, v in zip(FORMS, (b[:, h-1], d1, d2, p*conditional))], pl.Series(f"D3_probability_h{h}", p))
    mask = training_mask(panel, origin, 3, ids) & np.isfinite(panel["war_c3"].to_numpy())
    c1 = ridge().fit(x[mask], panel["war_c3"].to_numpy()[mask]).predict(tx)
    out = out.with_columns(pl.Series("C1_c3", c1), *[(pl.col("year1") + pl.col(f"{k}_h2") + pl.col(f"{k}_h3")).alias(f"{k}_c3") for k in FORMS])
    if not disjoint:
        for h in (1, 2, 3):
            pt = opportunity(panel, origin, h, False)
            out = out.with_columns(pl.Series(f"activity_h{h}", pt["predicted_any_mlb_pa_probability"]), pl.Series(f"expected_pa_h{h}", pt["predicted_expected_mlb_pa"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    out.write_parquet(path)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze", action="store_true")
    args = parser.parse_args()
    panel = pl.read_parquet(ROOT / "panel.parquet")
    manifest = json.loads((ROOT / "manifest.json").read_text())
    if args.freeze:
        freeze(panel, manifest)
        return
    contract = json.loads(CONTRACT.read_text())
    for path, expected in contract["source_hashes"].items():
        if sha256_file(Path(path)) != expected:
            raise ValueError(f"Frozen input changed: {path}")
    inners = sorted({y for f in contract["folds"] for y in f["inner_origins"]} | {y for y in range(2012, 2023) if y != 2020})
    fits = {y: fit_origin(panel, manifest, contract, y, True) for y in inners}
    def choice(years):
        losses = {k: float(np.mean([np.mean((fits[y][f"{k}_c3"].to_numpy() - fits[y]["war_c3"].to_numpy()) ** 2) for y in years])) for k in FORMS[1:]}
        return min(losses, key=losses.get), losses
    predictions, decisions = [], []
    for f in contract["folds"]:
        selected, losses = choice(f["inner_origins"])
        out = fit_origin(panel, manifest, contract, f["origin"], False)
        out = out.with_columns(pl.lit(selected).alias("selected_form"), *[pl.col(f"{selected}_{h}").alias(f"selected_{h}") for h in ("h2", "h3", "c3")])
        predictions.append(out)
        decisions.append({**f, "selected_form": selected, "inner_losses": losses})
    pl.concat(predictions).write_parquet(ROOT / "outer-predictions.parquet")
    current_choice, losses = choice(inners)
    current = fit_origin(panel, manifest, contract, 2025, False).with_columns(pl.lit(current_choice).alias("selected_form"), *[pl.col(f"{current_choice}_{h}").alias(f"selected_{h}") for h in ("h2", "h3", "c3")])
    current.write_parquet(ROOT / "current-candidates.parquet")
    (ROOT / "selection.json").write_text(json.dumps({"folds": decisions, "current": current_choice, "current_inner_losses": losses, "contract_sha256": sha256_file(CONTRACT)}, indent=2), encoding="utf-8")
    print("Fits complete. Decision and player report still require evaluation.", flush=True)


if __name__ == "__main__":
    warnings.filterwarnings("ignore", message="X does not have valid feature names")
    with threadpool_limits(limits=4):
        main()
