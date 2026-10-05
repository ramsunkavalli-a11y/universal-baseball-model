"""Independent replay and qualified disposition; never edits the fitted release."""

import json
from pathlib import Path

import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

from universal_baseball.finite_return_baseline import FEATURES, matrix, unrestricted
from universal_baseball.storage import sha256_file
from run_hitter_employment_comparison import ROOT, read, verify
from run_hitter_finite_return_baseline import (
    BASE,
    FIXED,
    OUT,
    PUBLIC,
    protections,
    save,
)


def recompute(g, arm):
    error = pl.col(arm + "_pa") - pl.col("next_pa")
    prob = pl.col(arm + "_p")
    actual = (pl.col("next_pa") > 0).cast(pl.Float64)
    logp = prob.clip(1e-12, 1 - 1e-12)
    expressions = [
        (error**2).mean().alias("pa_mse"),
        error.abs().mean().alias("pa_mae"),
        ((prob - actual) ** 2).mean().alias("brier"),
        (-actual * logp.log() - (1 - actual) * (1 - logp).log())
        .mean()
        .alias("logloss"),
    ]
    if arm + "_value" in g.columns:
        expressions.append(
            ((pl.col(arm + "_value") - pl.col("actual_relative_value")) ** 2)
            .mean()
            .alias("value_mse")
        )
    r = (
        g.group_by("origin_year")
        .agg(expressions)
        .select(pl.exclude("origin_year").mean())
        .row(0, named=True)
    )
    r["pa_rmse"] = np.sqrt(r["pa_mse"])
    if "value_mse" in r:
        r["value_rmse"] = np.sqrt(r["value_mse"])
    r.update(
        expected_pa=g[arm + "_pa"].sum(), actual_pa=g["next_pa"].sum(), rows=len(g)
    )
    return r


def main():
    assert not (PUBLIC / "completion.json").exists()
    pre, fit, report = (
        read(OUT / "preflight.json"),
        read(OUT / "fit-report.json"),
        read(PUBLIC / "report.json"),
    )
    verify(pre["hashes"])
    verify(report["hashes"])
    protections()
    q = pl.read_parquet(OUT / "predictions.parquet").sort("row_id")
    old = pl.read_parquet(BASE / "predictions.parquet").sort("row_id")
    assert q.select(old.columns).equals(old)
    assert q["finite_return_rate"].equals(q["observation_rate"])
    assert (
        q.filter(~pl.col("finite_return_changed"))
        .select("finite_return_p", "finite_return_conditional_pa", "finite_return_pa")
        .to_numpy()
        .tolist()
        == old.filter(~q["finite_return_changed"])
        .select("observation_p", "observation_conditional_pa", "observation_pa")
        .to_numpy()
        .tolist()
    )
    assert np.allclose(
        q["finite_return_p"] * q["finite_return_conditional_pa"],
        q["finite_return_pa"],
        rtol=0,
        atol=1e-10,
    )
    assert np.allclose(
        q["finite_return_pa"]
        * (q["finite_return_rate"] / 600 + q["origin_replacement_rate"]),
        q["finite_return_value"],
        rtol=0,
        atol=1e-10,
    )
    replayed, heads = 0, []
    with threadpool_limits(limits=2):
        for cell in fit["cells"]:
            y, k = cell["origin"], cell["fold"]
            f = pl.read_parquet(OUT / f"features-{k}.parquet")
            ids = next(
                c["test_row_ids"]
                for c in pre["cells"]
                if c["year"] == y and c["fold"] == k
            )
            te = f.filter(pl.col("row_id").is_in(ids)).sort("row_id")
            g = q.filter(pl.col("row_id").is_in(ids)).sort("row_id")
            assert te["row_id"].equals(g["row_id"])
            for h in cell["heads"]:
                assert sha256_file(Path(h["path"])) == h["sha256"]
                m = joblib.load(h["path"])
                for ready in [False, True]:
                    x = matrix(te, remove_explained_gap=ready)
                    if h["head"] == "participation":
                        v = m.predict_proba(x)[:, 1]
                        col = "ready_reference_p" if ready else "reference_p"
                    else:
                        v = np.clip(m.predict(x), 1, 800)
                        col = (
                            "ready_reference_conditional_pa"
                            if ready
                            else "reference_conditional_pa"
                        )
                    assert np.allclose(v, g[col], rtol=0, atol=1e-10)
                heads.append(h)
                replayed += 1
    original = q.filter(~pl.col("source_addition"))
    scopes = dict(
        all_original=original,
        finite_return=q.filter(pl.col("finite_return_changed")),
        nonarrivals=original.filter(pl.col("next_pa") == 0),
        current_regular=original.filter(pl.col("pa_0") >= 400),
        absent_former_regular=original.filter(
            (pl.col("pa_0") == 0) & pl.col("role_eligible")
        ),
    )
    scopes.update(
        {
            f"origin_{y}": original.filter(pl.col("origin_year") == y)
            for y in original["origin_year"].unique()
        }
    )
    scopes.update(
        {
            f"stage_{s}": original.filter(pl.col("stage") == s)
            for s in original["stage"].unique()
        }
    )
    checked = 0
    for scope, arms in report["scores"].items():
        for arm, saved in arms.items():
            for name, value in recompute(scopes[scope], arm).items():
                assert np.isclose(saved[name], value, rtol=1e-12, atol=1e-8), (
                    scope,
                    arm,
                    name,
                )
                checked += 1
    eligible = original.filter(
        pl.col("role_eligible") & pl.col("reference_unrestricted")
    )
    for arm, saved in report["reference_diagnostic"].items():
        for name, value in recompute(eligible, arm).items():
            assert np.isclose(saved[name], value, rtol=1e-12, atol=1e-8), (arm, name)
            checked += 1
    walks = read(PUBLIC / "player-walks.json")["cases"]
    assert {
        (r["forecast"]["player_id"], r["forecast"]["origin_year"]) for r in walks
    }.issuperset(FIXED)
    assert len(walks) == 15 and {n for r in walks for n in r["selection"]} == {
        "fixed diagnostic",
        "reference largest gain",
        "reference largest harm",
        "reference false high",
        "reference false low",
        "reference ordinary",
    }
    for r in walks:
        assert all(s["season"] <= r["forecast"]["origin_year"] for s in r["raw_stats"])
        for trace in r["head_coefficients"].values():
            assert np.isclose(
                trace["intercept"] + sum(trace["feature_effects"].values()),
                trace["linear_prediction"],
            )
        assert len(r["peers"]) == min(3, r["peer_count"])
    tatis = next(
        r
        for r in walks
        if r["forecast"]["player_id"] == 665487 and r["forecast"]["origin_year"] == 2022
    )
    o = tatis["forecast"]
    factor = tatis["finite_budget"]["known_suspension_fraction"]
    assert np.isclose(
        o["finite_return_pa"],
        o["ready_reference_p"] * o["ready_reference_conditional_pa"] * factor,
    )
    f = pl.read_parquet(OUT / "features-0.parquet")
    cell = next(c for c in pre["cells"] if c["year"] == 2022 and c["fold"] == 0)
    tr = unrestricted(f.filter(pl.col("row_id").is_in(cell["training_row_ids"])))
    comparable_medical = tr.filter(
        (pl.col("age") >= 20)
        & (pl.col("age") < 25)
        & (pl.col("last_MLB_work") >= 2 / 3)
        & (pl.col("status_major_link") == 1)
        & (pl.col("availability_annual_coverage") == 1)
        & (pl.col("role_gap") == 0)
        & (pl.col("role_surgery") == 1)
        & (pl.col("medical_recent_days") >= 0.25)
    )
    assert comparable_medical["player_id"].n_unique() == 0
    pool = f.filter(
        (pl.col("origin_year") == 2022)
        & pl.col("role_eligible")
        & (pl.col("status_major_link") == 1)
        & (pl.col("role_gap") == 0)
        & (pl.col("player_id") != 665487)
        & (pl.col("obs_status_finite_nonmedical") == 0)
        & (pl.col("obs_status_unresolved_nonmedical") == 0)
        & (pl.col("status_hard_unavailable") == 0)
    )
    pool = (
        pool.with_columns(
            (
                ((pl.col("age") - o["age"]) / 5) ** 2
                + (pl.col("last_MLB_work") - tatis["inputs"]["last_MLB_work"]) ** 2
                + (pl.col("last_MLB_quality") - tatis["inputs"]["last_MLB_quality"])
                ** 2
            ).alias("distance")
        )
        .sort(["distance", "player_id"])
        .head(3)
    )
    ordinary_peers = []
    for r in pool.to_dicts():
        observed = q.filter(pl.col("row_id") == r["row_id"]).row(0, named=True)
        ordinary_peers.append(
            dict(
                player_id=r["player_id"],
                name=r["player_name"],
                age=r["age"],
                last_role_PA=r["last_MLB_work"] * 600,
                last_quality=r["last_MLB_quality"],
                distance=r["distance"],
                reference_PA=observed["reference_pa"],
                benchmark_PA=observed["observation_pa"],
                actual_PA=observed["next_pa"],
                scope="ordinary role only; explicitly relaxed interruption category; not medical comparisons",
            )
        )
    diagnostics = []
    for r in walks:
        actual = r["forecast"]
        diagnostics.append(
            dict(
                row_id=r["row_id"],
                name=actual["player_name"],
                origin=actual["origin_year"],
                baseline_mechanism_exercised=bool(r["head_coefficients"]),
                candidate_changed=actual["finite_return_changed"],
                full_forecast_certified=False,
                review_status="complete",
            )
        )
    paths = [
        Path(__file__),
        PUBLIC / "report.json",
        PUBLIC / "player-walks.json",
        ROOT / "docs/hitter-finite-return-baseline-result.md",
        ROOT / "docs/hitter-finite-return-baseline-player-review.md",
    ]
    paths += [Path(h["path"]) for h in heads]
    save(
        PUBLIC / "completion.json",
        dict(
            player_walkthrough_status="complete",
            cases=diagnostics,
            source_to_forecast_mechanism_implemented=True,
            Tatis_full_unconditional_repair_complete=False,
            disposition="retain conditional finite-return reconstruction; reject broad role reference; no deployment",
            independent_head_replays=replayed,
            independent_score_equations=checked,
            tatis_ready_expected_PA=o["finite_return_pa"],
            tatis_gap_retained_expected_PA=tatis["delayed_recovery_sensitivity"][
                "expected_pa"
            ],
            exact_medical_transport_people=comparable_medical["player_id"].n_unique(),
            ordinary_role_comparisons=ordinary_peers,
            predictions_changed_rows=int(q["finite_return_changed"].sum()),
            public_comparison_unchanged=True,
            protected_2026_outcomes_used=False,
            forecasts_or_explorer_promoted=False,
            general_predictive_improvement_established=False,
            deployment_approved=False,
            hashes={str(p): sha256_file(p) for p in paths},
        ),
    )
    protections()
    print(
        json.dumps(
            dict(
                heads_replayed=replayed,
                score_equations=checked,
                walks=15,
                Tatis_unconditional_repair="still open",
                ordinary_comparisons=ordinary_peers,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
