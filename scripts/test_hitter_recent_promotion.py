"""One matched training-era contrast, separate preflight and fit phases."""
import argparse
from pathlib import Path

import joblib
import numpy as np
import polars as pl
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits

import audit_hitter_big_miss_groups as a
from fit_practical_hitter_v31 import weights as old_weights
from run_hitter_finite_return_baseline import protections, save
from universal_baseball.forecast_validation import preflight
from universal_baseball.hitter_recent_promotion import profile, support, weights
from universal_baseball.storage import sha256_file

PUBLIC = a.ROOT / "reports/model-evidence/hitter-recent-promotion"
OUT = a.ROOT / "reports/generated/hitter-recent-promotion"
REFERENCE = a.ROOT / "reports/generated/hitter-reported-departure/predictions.parquet"


def prepare():
    assert not PUBLIC.exists() and not OUT.exists()
    protections()
    for p in ["hitter-arrival-cohort-diagnosis", "hitter-reported-departure"]:
        review = a.read(a.ROOT / "reports/model-evidence" / p / "completion.json")
        assert review["player_walkthrough_status"] == "complete"
        a.verify(review["hashes"])
    pre = a.read(a.BASE / "preflight.json")
    a.verify(pre["hashes"])
    fit = a.read(a.BASE / "fit-report.json")
    fitcells = {(c["origin"], c["fold"]): c for c in fit["cells"]}
    q = pl.read_parquet(REFERENCE).sort("row_id")
    assert q.height == 30519 and q["target_year"].max() == 2025
    frames = [pl.read_parquet(a.BASE / f"features-{k}.parquet") for k in range(5)]
    checks, supports, masses, replayed = [], [], [], 0
    with threadpool_limits(limits=2):
        for c in pre["cells"]:
            y, k = c["year"], c["fold"]
            f = frames[k]
            tr = f.filter(pl.col("row_id").is_in(c["training_row_ids"])).sort("row_id")
            te = f.filter(pl.col("row_id").is_in(c["test_row_ids"])).sort("row_id")
            observed = q.filter(pl.col("row_id").is_in(c["test_row_ids"])).sort("row_id")
            assert te["row_id"].equals(observed["row_id"])
            for head, sub in [("participation", tr), ("conditional_pa", tr.filter(pl.col("next_pa") > 0))]:
                assert np.array_equal(weights(sub), old_weights(sub))
                _, note = preflight(sub, te, cutoff=y, fold=k, features=pre["job_features"],
                    expected_keys=te.select("row_id", "horizon").iter_rows())
                checks.append(dict(origin=y, fold=k, head=head, **note))
                supports.append(support(sub, te).with_columns(pl.lit(y).alias("origin"), pl.lit(k).alias("fold"), pl.lit(head).alias("head")))
                weighted = sub.with_columns(pl.Series("recent_weight", weights(sub, recent=True)))
                masses.extend(dict(origin=y, fold=k, head=head, **r) for r in weighted.group_by("origin_year").agg(
                    pl.len().alias("rows"), pl.col("player_id").n_unique().alias("people"),
                    pl.col("recent_weight").sum().alias("recent_mass")).sort("origin_year").to_dicts())
                h = next(h for h in fitcells[y, k]["heads"] if h["head"] == head)
                assert h["features"] == pre["job_features"]
                path = a.ROOT / h["path"]
                assert sha256_file(path) == h["sha256"]
                m = joblib.load(path)
                cls = HistGradientBoostingClassifier if head == "participation" else HistGradientBoostingRegressor
                assert m.get_params() == cls(**pre["settings"]).get_params()
                pred = m.predict_proba(te.select(h["features"]).to_numpy())[:, 1] if head == "participation" else m.predict(te.select(h["features"]).to_numpy())
                col = "observation_raw_p" if head == "participation" else "observation_raw_conditional_pa"
                assert np.allclose(pred, observed[col], rtol=0, atol=1e-10)
                replayed += 1
    assert len(checks) == replayed == 70
    paths = [Path(__file__), a.ROOT / "docs/hitter-recent-promotion-contract.md",
        a.ROOT / "src/universal_baseball/hitter_recent_promotion.py", a.ROOT / "tests/test_hitter_recent_promotion.py",
        a.ROOT / "src/universal_baseball/hitter_arrival_cohort_review.py",
        a.ROOT / "src/universal_baseball/forecast_validation.py", a.ROOT / "scripts/fit_practical_hitter_v31.py",
        a.BASE / "preflight.json", a.BASE / "fit-report.json", REFERENCE,
        *[a.BASE / f"features-{k}.parquet" for k in range(5)],
        *[a.ROOT / h["path"] for c in fit["cells"] for h in c["heads"]]]
    PUBLIC.mkdir(parents=True)
    OUT.mkdir(parents=True)
    save(PUBLIC / "source-seal.json", dict(before_fitting=True, hashes={str(p):sha256_file(p) for p in paths}))
    pl.concat(supports).write_parquet(OUT / "profile-support.parquet")
    save(PUBLIC / "training-weights.json", dict(masses=masses, checks=checks, support_warning_not_certification=True,
        hashes={str(OUT / "profile-support.parquet"):sha256_file(OUT / "profile-support.parquet")}))
    f = profile(frames[0])
    cohorts = []
    for y in sorted(f["origin_year"].unique().to_list()):
        for name, sub in [("all_observed_draft_year", f.filter((pl.col("origin_year") == y) & (pl.col("draft_time") == "draft_year"))),
                          ("thin_advanced_top_pick", f.filter((pl.col("origin_year") == y) & pl.col("thin_advanced_top_pick")))]:
            never = sub.filter(pl.col("prior_debut") == 0)
            cohorts.append(dict(origin=y, group=name, observed_players=sub.height,
                already_MLB_at_origin=sub.filter(pl.col("prior_debut") > 0).height,
                never_debut_at_origin=never.height, next_year_arrivals=never.filter(pl.col("next_pa") > 0).height,
                next_year_PA=int(never["next_pa"].sum()), school_unknown=int(sub["draft_class_unknown"].sum()),
                canceled_origin=y == 2020, short_MLB_target=y == 2019))
    save(PUBLIC / "draft-cohorts.json", dict(cohorts=cohorts, observed_population_not_whole_draft=True,
        describes_actual_origins_not_future_eligibility=True))
    save(OUT / "preflight.json", dict(cells=pre["cells"], settings=pre["settings"], features=pre["job_features"],
        head_checks=70, benchmark_heads_replayed=70, before_fitting=True,
        hashes={str(p):sha256_file(p) for p in [PUBLIC / "source-seal.json", PUBLIC / "training-weights.json", PUBLIC / "draft-cohorts.json"]}))
    protections()
    print("Preflight complete: 70 source/head checks and reference replays; no fits", flush=True)


def fit():
    pre = a.read(OUT / "preflight.json")
    a.verify(pre["hashes"])
    a.verify(a.read(PUBLIC / "source-seal.json")["hashes"])
    assert not (OUT / "fit-report.json").exists() and not list(OUT.glob("model-*.joblib"))
    save(PUBLIC / "fit-seal.json", dict(before_fitting=True, preflight_sha256=sha256_file(OUT / "preflight.json")))
    q = pl.read_parquet(REFERENCE).sort("row_id")
    parts, cells = [], []
    with threadpool_limits(limits=2):
        for c in pre["cells"]:
            y, k = c["year"], c["fold"]
            f = pl.read_parquet(a.BASE / f"features-{k}.parquet")
            tr = f.filter(pl.col("row_id").is_in(c["training_row_ids"])).sort("row_id")
            te = f.filter(pl.col("row_id").is_in(c["test_row_ids"])).sort("row_id")
            g = q.filter(pl.col("row_id").is_in(c["test_row_ids"])).sort("row_id")
            assert g["row_id"].equals(te["row_id"])
            pred, heads = {}, []
            for head, sub, cls, target in [("participation", tr, HistGradientBoostingClassifier, "next_active"),
                ("conditional_pa", tr.filter(pl.col("next_pa") > 0), HistGradientBoostingRegressor, "next_pa")]:
                w = weights(sub, recent=True)
                m = cls(**pre["settings"])
                m.fit(sub.select(pre["features"]).to_numpy(), sub[target].to_numpy(), sample_weight=w)
                path = OUT / f"model-{head}-{y}-{k}.joblib"
                joblib.dump(m, path, compress=3)
                heads.append(dict(head=head, path=str(path.relative_to(a.ROOT)), sha256=sha256_file(path),
                    features=pre["features"], training_rows=sub.height, training_people=sub["player_id"].n_unique(),
                    weight_sum=float(w.sum()), latest_training_origin=int(sub["origin_year"].max())))
                x = te.select(pre["features"]).to_numpy()
                pred[head] = m.predict_proba(x)[:, 1] if head == "participation" else m.predict(x)
            p = pred["participation"].copy()
            p[(te["status_hard_unavailable"].to_numpy() > 0) | (te["status_retired"].to_numpy() > 0) | g["departure_reported"].to_numpy()] = 0
            conditional = np.clip(pred["conditional_pa"], 1, 800)
            never = g["prior_debut"].to_numpy() == 0
            p = np.where(never, p, g["departure_p"].to_numpy())
            conditional = np.where(never, conditional, g["departure_conditional_pa"].to_numpy())
            pa = p * conditional
            g = g.with_columns(pl.Series("recent_raw_p", pred["participation"]),
                pl.Series("recent_raw_conditional_pa", pred["conditional_pa"]),
                pl.Series("recent_p", p), pl.Series("recent_conditional_pa", conditional),
                pl.Series("recent_pa", pa), pl.col("departure_rate").alias("recent_rate"),
                pl.Series("recent_value", pa * (g["departure_rate"].to_numpy()/600 + g["origin_replacement_rate"].to_numpy())))
            assert g.select(q.columns).equals(q.filter(pl.col("row_id").is_in(c["test_row_ids"])).sort("row_id"))
            for n in ["p", "conditional_pa", "pa", "rate", "value"]:
                assert g.filter(pl.col("prior_debut") > 0)["recent_"+n].equals(g.filter(pl.col("prior_debut") > 0)["departure_"+n])
            path = OUT / f"forecast-{y}-{k}.parquet"
            g.write_parquet(path)
            cells.append(dict(origin=y, fold=k, heads=heads, path=str(path), sha256=sha256_file(path)))
            parts.append(g)
            print(f"Fitted origin {y}, fold {k}; two heads; previously debuted forecasts unchanged", flush=True)
    result = pl.concat(parts).sort("row_id")
    assert result.height == q.height and result.select(q.columns).equals(q)
    path = OUT / "predictions.parquet"
    result.write_parquet(path)
    save(OUT / "fit-report.json", dict(cells=cells, new_fits=70, predictions_sha256=sha256_file(path),
        player_walkthrough_status="pending", deployment_approved=False))
    protections()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["prepare", "fit"])
    {"prepare":prepare, "fit":fit}[parser.parse_args().phase]()
