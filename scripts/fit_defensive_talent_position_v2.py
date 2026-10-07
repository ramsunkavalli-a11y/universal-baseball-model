"""One fixed component contrast; unknown talent remains unscored, not zero."""
import json
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from universal_baseball.defensive_talent_position import BASE_FEATURES, matrix, person_weights, preflight
from universal_baseball.storage import sha256_file
from audit_defensive_talent_support import verify
from run_hitter_finite_return_baseline import protections, save

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "reports/generated/defensive-talent-position-v2/qualified"
OUT = DATA / "comparison"
PUBLIC = ROOT / "reports/model-evidence/defensive-talent-position-v2/comparison"
ARMS = {"baseline": BASE_FEATURES, "raw_share": (*BASE_FEATURES, "raw_share"), "candidate": (*BASE_FEATURES, "complete_rate")}


def scores(rows):
    if not rows:
        return None
    y = np.array([r["quality_rate"] for r in rows])
    w = person_weights(rows)
    result = dict(rows=len(rows), people=len({r["player_id"] for r in rows}),
                  observed_mean=float(np.average(y, weights=w)),
                  sparse_profiles=sum(r["matching_training_people"] < 20 for r in rows),
                  rows_with_measurement_gaps=sum(r["unmeasured_official_outs"] > 0 for r in rows))
    for arm in (*ARMS, "zero"):
        prediction = np.array([r[arm] for r in rows])
        error = prediction - y
        result[arm] = dict(rmse=float(np.sqrt(np.average(error ** 2, weights=w))),
                           unweighted_rmse=float(np.sqrt(np.mean(error ** 2))),
                           mean_error=float(np.average(error, weights=w)), predicted_mean=float(np.average(prediction, weights=w)))
    grouped = {}
    for r in rows:
        grouped.setdefault(r["player_id"], []).append(r)
    losses = np.array([[np.mean([(r[a] - r["quality_rate"]) ** 2 for r in group]) for a in (*ARMS, "zero")] for group in grouped.values()])
    rng = np.random.default_rng(20261006)
    samples = rng.integers(0, len(grouped), size=(2000, len(grouped)))
    boot = np.sqrt(losses[samples].mean(axis=1))
    candidate = list(ARMS).index("candidate")
    result["candidate_paired_differences"] = {}
    for i, arm in enumerate((*ARMS, "zero")):
        if arm == "candidate":
            continue
        result["candidate_paired_differences"][arm] = dict(
            rmse_difference=result["candidate"]["rmse"] - result[arm]["rmse"],
            player_bootstrap_95=np.quantile(boot[:, candidate] - boot[:, i], [.025, .975]).tolist())
    return result


def main():
    protections()
    final_path = DATA / "source-final-review.json"
    final = json.loads(final_path.read_text(encoding="utf8"))
    assert final["player_walkthrough_status"] == "complete"
    verify(final["hashes"])
    assert not OUT.exists()
    OUT.mkdir(parents=True)
    PUBLIC.mkdir(parents=True)
    rows = pl.read_parquet(DATA / "labels.parquet").filter(pl.col("horizon") == 3).to_dicts()
    checks, work = [], []
    for year in sorted({r["origin_year"] for r in rows if r["window_mature"]}):
        for fold in range(5):
            train = [r for r in rows if r["quality_rate"] is not None and r["window_end"] <= year and r["origin_year"] < year and r["player_id"] % 5 != fold]
            test = [r for r in rows if r["origin_year"] == year and r["player_id"] % 5 == fold]
            check, support = preflight(train, test, year, fold, 3)
            checks.append(check)
            work.append((check, support, train, test))
    allowed_origins = {year for year in {c["origin"] for c in checks} if all(c["fit_allowed"] for c in checks if c["origin"] == year)}
    assert allowed_origins == {2021, 2022}, "Changed support requires a new review, not silent scope expansion"
    save(OUT / "fit-preflight.json", dict(folds=checks, allowed_origins=sorted(allowed_origins), arms=ARMS, alpha=100,
                                       training_weight="one_total_weight_per_training_person", scored_weight="one_per_measured_person_within_origin",
                                       unknown_quality="retained_predictions_not_scored_as_zero", feature_cutoff="origin_inclusive",
                                       hashes={str(p): sha256_file(p) for p in [Path(__file__), final_path, ROOT / "docs/defensive-talent-position-v2-contract.md", ROOT / "docs/defensive-talent-position-v2-exposure-amendment.md"]}))
    predictions, fits = [], []
    with threadpool_limits(limits=1):
        for check, support, train, test in work:
            if check["origin"] not in allowed_origins:
                continue
            w = person_weights(train)
            y = np.array([r["quality_rate"] for r in train])
            forecast = {a: None for a in ARMS}
            for arm, features in ARMS.items():
                x = matrix(train, features)
                scaler = StandardScaler().fit(x, sample_weight=w)
                fit = Ridge(alpha=100).fit(scaler.transform(x), y, sample_weight=w)
                forecast[arm] = fit.predict(scaler.transform(matrix(test, features)))
                coef = fit.coef_ / scaler.scale_
                intercept = float(fit.intercept_ - np.dot(coef, scaler.mean_))
                record = dict(origin=check["origin"], fold=check["fold"], arm=arm, features=list(features),
                              coefficient=coef.tolist(), intercept=intercept, alpha=100, training_people=check["training_people"],
                              training_keys=[(r["origin_year"], r["player_id"], r["position"]) for r in train],
                              scaler_mean=scaler.mean_.tolist(), scaler_scale=scaler.scale_.tolist())
                assert np.allclose(forecast[arm], matrix(test, features) @ coef + intercept, atol=1e-10)
                fits.append(record)
            for i, row in enumerate(test):
                predictions.append({**row, **{a: float(forecast[a][i]) for a in ARMS}, "zero": 0.,
                                    "fold": check["fold"], "matching_training_people": support[i], "training_people": check["training_people"]})
    expected = [r for r in rows if r["origin_year"] in allowed_origins]
    assert len(predictions) == len(expected)
    key = lambda r: (r["origin_year"], r["player_id"], r["position"])
    assert {key(r) for r in predictions} == {key(r) for r in expected}
    pl.DataFrame(predictions).write_parquet(OUT / "predictions.parquet")
    save(OUT / "fits.json", fits)
    aggregate = {str(year): scores([r for r in predictions if r["origin_year"] == year and r["quality_rate"] is not None]) for year in sorted(allowed_origins)}
    groups = []
    for year in sorted(allowed_origins):
        scored = [r for r in predictions if r["origin_year"] == year and r["quality_rate"] is not None]
        for field in ("position", "prior_mlb_defense", "fielding_level"):
            for value in sorted({r[field] for r in scored}):
                groups.append(dict(origin=year, field=field, value=value, score=scores([r for r in scored if r[field] == value])))
    report = dict(status="provisional_component_comparison_requires_player_review", fits=len(fits), origins=aggregate, groups=groups,
                  predictions=len(predictions), measured_rows=sum(r["quality_rate"] is not None for r in predictions),
                  long_window_fits=0, player_walkthrough_status="pending", production_changed=False, additional_2026_data_ingested_or_used=False,
                  hashes={str(p): sha256_file(p) for p in [Path(__file__), OUT / "fit-preflight.json", OUT / "fits.json", OUT / "predictions.parquet", DATA / "labels.parquet", final_path]})
    save(OUT / "report.json", report)
    save(PUBLIC / "report.json", report)
    protections()
    print(json.dumps(aggregate, indent=2))


if __name__ == "__main__":
    main()
