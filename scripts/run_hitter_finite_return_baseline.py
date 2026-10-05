"""One career-role reference, a finite-return repair, and mandatory player walks."""

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import polars as pl
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from universal_baseball.finite_return_baseline import (
    FEATURES,
    coefficients,
    frame,
    matrix,
    support,
    transfer_allowed,
    unrestricted,
)
from universal_baseball.forecast_validation import preflight
from universal_baseball.known_suspension_budget import apply_to_role, budget
from universal_baseball.storage import sha256_file
from fit_practical_hitter_v31 import weights
from run_hitter_employment_comparison import ROOT, read, verify

BASE = ROOT / "reports/generated/hitter-nonmedical-opportunity"
OUT = ROOT / "reports/generated/hitter-finite-return-baseline"
PUBLIC = ROOT / "reports/model-evidence/hitter-finite-return-baseline"
FIXED = [
    (665487, 2022),
    (665487, 2023),
    (656555, 2023),
    (453056, 2018),
    (628356, 2017),
    (677551, 2023),
    (672779, 2024),
    (680776, 2024),
    (474832, 2023),
    (592450, 2024),
]


def save(path, data):
    assert not path.exists(), f"Preserve completed evidence: {path}"
    path.write_text(
        json.dumps(data, indent=2, allow_nan=False, default=str) + "\n",
        encoding="utf8",
        newline="\n",
    )


def protections():
    selected = (
        ROOT
        / "model_artifacts/hitter-selected-2026-frozen-2026-10-05/freeze-manifest.json"
    )
    final = ROOT / "reports/model-evidence/hitter-final-2026/report.json"
    assert (
        sha256_file(selected)
        == "a1d819ffcdd98a9ee62feecf5637b5ebe1f93b6e931d77d2b7d692ed928da67a"
    )
    assert (
        sha256_file(final)
        == "8c2acfeb42ece7d109d3b35542a6b79ec372467d7027d5945a4ba800cde913bb"
    )


def prepare():
    assert not OUT.exists(), "Preserve preparation; do not restart"
    protections()
    final = read(BASE / "final-review.json")
    assert final["player_walkthrough_status"] == "complete"
    verify(final["hashes"])
    pre = read(BASE / "preflight.json")
    verify(pre["hashes"])
    q = pl.read_parquet(BASE / "predictions.parquet").sort("row_id")
    assert q.height == 30519 and q["target_year"].max() == 2025
    reportpath = ROOT / "config/hitter_anticipated_medical_readiness.json"
    reports = read(reportpath)["reports"]
    paths = [
        Path(__file__),
        ROOT / "src/universal_baseball/finite_return_baseline.py",
        ROOT / "tests/test_finite_return_baseline.py",
        ROOT / "docs/hitter-finite-return-baseline-contract.md",
        ROOT / "src/universal_baseball/forecast_validation.py",
        ROOT / "src/universal_baseball/known_suspension_budget.py",
        reportpath,
        BASE / "preflight.json",
        BASE / "final-review.json",
        BASE / "predictions.parquet",
        ROOT / "reports/model-evidence/known-suspension-budget/report.json",
        ROOT / "config/reported_suspension_season_budgets.json",
        ROOT
        / "reports/generated/hitter-nonmedical-observation/active-origin-evidence.json",
    ]
    frames, checks, profiles = {}, [], []
    for k in range(5):
        path = BASE / f"features-{k}.parquet"
        f = pl.read_parquet(path).sort("row_id")
        frames[k] = frame(f, reports)
        assert frames[k].select(f.columns).equals(f)
        paths.append(path)
    oldcases = read(
        ROOT / "reports/model-evidence/known-suspension-budget/report.json"
    )["cases"]
    observations = read(
        ROOT
        / "reports/generated/hitter-nonmedical-observation/active-origin-evidence.json"
    )["origins"]
    budgets, transfer = {}, []
    facts = read(ROOT / "config/reported_suspension_season_budgets.json")["events"]
    for fact in facts:
        pid, y = fact["player_id"], fact["target_year"] - 1
        rows = frames[0].filter(
            (pl.col("player_id") == pid) & (pl.col("origin_year") == y)
        )
        assert rows.height == 1
        row = rows.row(0, named=True)
        # This release covers only the already captured 2023 season budget.
        assert fact["target_year"] == 2023
        ev = budget(
            observations[f"{y}:{pid}"],
            facts,
            player_id=pid,
            cutoff=row["ctx_information_date"],
            target_year=y + 1,
            season_games=162,
            season_start="2023-03-30",
        )
        assert ev == next(
            c["budget"] for c in oldcases if c["player_id"] == pid and c["origin"] == y
        )
        if transfer_allowed(row, ev):
            budgets[str(row["row_id"])] = ev
            transfer.append(row["row_id"])
    assert transfer, "No supported finite-return case; do not fit an unrelated model"
    for c in pre["cells"]:
        y, k = c["year"], c["fold"]
        f = frames[k]
        tr = unrestricted(f.filter(pl.col("row_id").is_in(c["training_row_ids"]))).sort(
            "row_id"
        )
        te = f.filter(
            pl.col("row_id").is_in(c["test_row_ids"]) & pl.col("role_eligible")
        ).sort("row_id")
        for name, sub in [
            ("participation", tr),
            ("conditional_pa", tr.filter(pl.col("next_pa") > 0)),
        ]:
            _, note = preflight(
                sub,
                te,
                cutoff=y,
                fold=k,
                features=FEATURES,
                expected_keys=te.select("row_id", "horizon").iter_rows(),
            )
            assert sub["ctx_information_date"].max() < te["ctx_information_date"].min()
            assert sub.height >= 200 and sub["player_id"].n_unique() >= 100
            s = support(sub, te).with_columns(
                pl.lit(y).alias("origin"),
                pl.lit(k).alias("fold"),
                pl.lit(name).alias("head"),
                pl.lit("actual_gap").alias("scope"),
            )
            profiles.append(s)
            transferred = te.filter(pl.col("row_id").is_in(transfer))
            counterfactual = []
            if transferred.height:
                s2 = support(
                    sub, transferred.with_columns(pl.lit(0.0).alias("role_gap"))
                ).with_columns(
                    pl.lit(y).alias("origin"),
                    pl.lit(k).alias("fold"),
                    pl.lit(name).alias("head"),
                    pl.lit("anticipated_recovery_transport").alias("scope"),
                )
                profiles.append(s2)
                counterfactual = s2.to_dicts()
            checks.append(
                dict(
                    origin=y,
                    fold=k,
                    head=name,
                    **note,
                    reference_profile_zero=int((s["role_profile_people"] == 0).sum()),
                    transport_profiles=counterfactual,
                )
            )
    OUT.mkdir()
    for k, f in frames.items():
        p = OUT / f"features-{k}.parquet"
        f.write_parquet(p)
        paths.append(p)
    p = OUT / "profile-support.parquet"
    pl.concat(profiles).write_parquet(p)
    paths.append(p)
    save(
        OUT / "preflight.json",
        dict(
            before_fitting=True,
            cells=pre["cells"],
            checks=checks,
            features=FEATURES,
            transfer_row_ids=transfer,
            budgets=budgets,
            settings=dict(C=1.0, alpha=100.0),
            original_rows=30506,
            additions=13,
            new_fits=0,
            scope="one known finite-return transport; broad reference diagnostic",
            protected_2026_outcomes_used=False,
            deployment_approved=False,
            hashes={str(p): sha256_file(p) for p in paths},
        ),
    )
    print(
        f"70 full/active checks complete; finite-return gate rows: {transfer}",
        flush=True,
    )


def fit():
    pre = read(OUT / "preflight.json")
    verify(pre["hashes"])
    protections()
    assert len(pre["checks"]) == 70 and not (OUT / "fit-report.json").exists()
    assert not list(OUT.glob("model-*.joblib")), "Do not overwrite partial execution"
    save(
        OUT / "fit-seal.json",
        dict(
            preflight_sha256=sha256_file(OUT / "preflight.json"),
            runner_sha256=sha256_file(Path(__file__)),
        ),
    )
    q = pl.read_parquet(BASE / "predictions.parquet").sort("row_id")
    parts, cells = [], []
    with threadpool_limits(limits=2):
        for c in pre["cells"]:
            y, k = c["year"], c["fold"]
            f = pl.read_parquet(OUT / f"features-{k}.parquet")
            tr = unrestricted(
                f.filter(pl.col("row_id").is_in(c["training_row_ids"]))
            ).sort("row_id")
            te = f.filter(pl.col("row_id").is_in(c["test_row_ids"])).sort("row_id")
            g = q.filter(pl.col("row_id").is_in(c["test_row_ids"])).sort("row_id")
            assert g["row_id"].equals(te["row_id"])
            heads, models = [], {}
            for name, sub, cls, target in [
                (
                    "participation",
                    tr,
                    LogisticRegression(C=1.0, max_iter=2000),
                    "next_active",
                ),
                (
                    "conditional_pa",
                    tr.filter(pl.col("next_pa") > 0),
                    Ridge(alpha=100.0),
                    "next_pa",
                ),
            ]:
                m = make_pipeline(StandardScaler(), cls)
                m.fit(
                    matrix(sub),
                    sub[target].to_numpy(),
                    **{m.steps[-1][0] + "__sample_weight": weights(sub)},
                )
                path = OUT / f"model-{name}-{y}-{k}.joblib"
                joblib.dump(m, path, compress=3)
                models[name] = m
                heads.append(
                    dict(
                        head=name,
                        path=str(path),
                        sha256=sha256_file(path),
                        training_rows=sub.height,
                        training_people=sub["player_id"].n_unique(),
                        latest_training_target=int(sub["target_year"].max()),
                    )
                )
            refp = models["participation"].predict_proba(matrix(te))[:, 1]
            refc = np.clip(models["conditional_pa"].predict(matrix(te)), 1, 800)
            reference = refp * refc
            ready_p = models["participation"].predict_proba(
                matrix(te, remove_explained_gap=True)
            )[:, 1]
            ready_c = np.clip(
                models["conditional_pa"].predict(matrix(te, remove_explained_gap=True)),
                1,
                800,
            )
            probability, conditional = (
                g["observation_p"].to_numpy().copy(),
                g["observation_conditional_pa"].to_numpy().copy(),
            )
            is_transfer = te["row_id"].is_in(pre["transfer_row_ids"]).to_numpy()
            for i in np.flatnonzero(is_transfer):
                ev = pre["budgets"][str(te["row_id"][int(i)])]
                r = apply_to_role(
                    ready_p[i],
                    ready_c[i],
                    g["observation_rate"][int(i)],
                    ev,
                    excludes_known_suspension=True,
                )
                probability[i], conditional[i] = r["probability"], r["conditional_pa"]
            pa = probability * conditional
            rate = g["observation_rate"].to_numpy()
            g = g.with_columns(
                pl.Series("reference_p", refp),
                pl.Series("reference_conditional_pa", refc),
                pl.Series("reference_pa", reference),
                pl.Series("ready_reference_p", ready_p),
                pl.Series("ready_reference_conditional_pa", ready_c),
                pl.Series("finite_return_p", probability),
                pl.Series("finite_return_conditional_pa", conditional),
                pl.Series("finite_return_pa", pa),
                pl.Series("finite_return_rate", rate),
                pl.Series(
                    "finite_return_value",
                    pa * (rate / 600 + g["origin_replacement_rate"].to_numpy()),
                ),
                pl.Series("finite_return_changed", is_transfer),
                te["role_eligible"],
                (
                    (te["obs_status_finite_nonmedical"] == 0)
                    & (te["obs_status_unresolved_nonmedical"] == 0)
                    & (te["status_hard_unavailable"] == 0)
                    & (te["status_retired"] == 0)
                ).alias("reference_unrestricted"),
            )
            assert g.select(q.columns).equals(
                q.filter(pl.col("row_id").is_in(c["test_row_ids"])).sort("row_id")
            )
            parts.append(g)
            cells.append(dict(origin=y, fold=k, heads=heads))
            print(f"Career-role heads complete {y}/{k}", flush=True)
    result = pl.concat(parts).sort("row_id")
    assert result.height == 30519 and result["finite_return_changed"].sum() == len(
        pre["transfer_row_ids"]
    )
    result.write_parquet(OUT / "predictions.parquet")
    save(
        OUT / "fit-report.json",
        dict(
            new_heads=70,
            cells=cells,
            predictions_sha256=sha256_file(OUT / "predictions.parquet"),
            player_walkthrough_status="pending",
            protected_2026_outcomes_used=False,
            deployment_approved=False,
        ),
    )
    verify(pre["hashes"])
    protections()


def metrics(g, arm):
    y, p = g["next_pa"].to_numpy(), g[arm + "_p"].to_numpy()
    pred = g[arm + "_pa"].to_numpy()
    years = g["origin_year"].to_numpy()
    losses = dict(
        pa_mse=(pred - y) ** 2,
        pa_mae=abs(pred - y),
        brier=(p - (y > 0)) ** 2,
        logloss=-np.log(
            np.where(
                y > 0, np.clip(p, 1e-12, 1 - 1e-12), np.clip(1 - p, 1e-12, 1 - 1e-12)
            )
        ),
    )
    if arm + "_value" in g.columns:
        losses["value_mse"] = (
            g[arm + "_value"].to_numpy() - g["actual_relative_value"].to_numpy()
        ) ** 2
    r = {
        n: float(np.mean([v[years == a].mean() for a in np.unique(years)]))
        for n, v in losses.items()
    }
    r.update(expected_pa=float(pred.sum()), actual_pa=float(y.sum()), rows=len(g))
    r["pa_rmse"] = float(np.sqrt(r["pa_mse"]))
    if "value_mse" in r:
        r["value_rmse"] = float(np.sqrt(r["value_mse"]))
    return r


def review():
    assert not PUBLIC.exists()
    pre, fit = read(OUT / "preflight.json"), read(OUT / "fit-report.json")
    verify(pre["hashes"])
    protections()
    assert sha256_file(OUT / "predictions.parquet") == fit["predictions_sha256"]
    q = pl.read_parquet(OUT / "predictions.parquet").sort("row_id")
    original = q.filter(~pl.col("source_addition"))
    scopes = dict(
        all_original=original,
        finite_return=q.filter(pl.col("finite_return_changed")),
        nonarrivals=original.filter(pl.col("next_pa") == 0),
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
    scopes["current_regular"] = original.filter(pl.col("pa_0") >= 400)
    scopes["absent_former_regular"] = original.filter(
        (pl.col("pa_0") == 0) & pl.col("role_eligible")
    )
    scores = {
        n: {a: metrics(g, a) for a in ["observation", "current", "finite_return"]}
        for n, g in scopes.items()
        if len(g)
    }
    eligible = original.filter(
        pl.col("role_eligible") & pl.col("reference_unrestricted")
    )
    refscore = {a: metrics(eligible, a) for a in ["observation", "reference"]}
    publicpath = (
        ROOT
        / "reports/generated/hitter-minor-statcast-precision/scored-predictions.parquet"
    )
    public = original.join(
        pl.read_parquet(
            publicpath, columns=["row_id", "steamer_pa", "steamer_index", "zips_index"]
        ),
        on="row_id",
        how="left",
        validate="1:1",
    ).filter(
        (pl.col("pa_0") > 0)
        & pl.col("steamer_index").is_not_null()
        & pl.col("zips_index").is_not_null()
    )
    publicscores = dict(
        rows=len(public),
        vintage_unknown=True,
        steamer_mae=float((public["steamer_pa"] - public["next_pa"]).abs().mean()),
        **{
            a + "_mae": float((public[a + "_pa"] - public["next_pa"]).abs().mean())
            for a in ["observation", "finite_return"]
        },
    )
    chosen = {}
    for pid, y in FIXED:
        row = q.filter((pl.col("player_id") == pid) & (pl.col("origin_year") == y)).row(
            0, named=True
        )
        chosen[row["row_id"]] = ["fixed diagnostic"]
    d = eligible.with_columns(
        (
            (pl.col("reference_pa") - pl.col("next_pa")) ** 2
            - (pl.col("observation_pa") - pl.col("next_pa")) ** 2
        ).alias("delta"),
        (pl.col("reference_pa") - pl.col("next_pa")).alias("error"),
    )
    for label, col, descending in [
        ("reference largest gain", "delta", False),
        ("reference largest harm", "delta", True),
        ("reference false high", "error", True),
        ("reference false low", "error", False),
    ]:
        rid = d.sort([col, "row_id"], descending=[descending, False])["row_id"][0]
        chosen.setdefault(rid, []).append(label)
    ordinary = (
        d.filter(pl.col("next_pa") > 0)
        .with_columns(pl.col("error").abs().alias("absolute"))
        .sort("absolute")
    )
    chosen.setdefault(ordinary["row_id"][0], []).append("reference ordinary")
    rawpath = ROOT / "reports/generated/practical-hitter-v31/dated-stints.parquet"
    raw = pl.read_parquet(rawpath)
    contextpath = (
        ROOT / "reports/generated/hitter-status-evidence-v2/status-ledger.json"
    )
    contexts = {r["candidate_key"]: r for r in read(contextpath)["rows"]}
    walks, replayed = [], 0
    frames = {k: pl.read_parquet(OUT / f"features-{k}.parquet") for k in range(5)}
    for rid, why in chosen.items():
        o = q.filter(pl.col("row_id") == rid).row(0, named=True)
        y, k, pid = o["origin_year"], o["outer_fold"], o["player_id"]
        cell = next(c for c in fit["cells"] if c["origin"] == y and c["fold"] == k)
        f = frames[k]
        one = f.filter(pl.col("row_id") == rid)
        r = one.row(0, named=True)
        paths = {}
        if r["role_eligible"]:
            for h in cell["heads"]:
                assert sha256_file(Path(h["path"])) == h["sha256"]
                m = joblib.load(h["path"])
                paths[h["head"]] = coefficients(m, matrix(one))
                paths[h["head"] + "_anticipated_ready"] = coefficients(
                    m, matrix(one, remove_explained_gap=True)
                )
                if h["head"] == "participation":
                    assert np.isclose(
                        m.predict_proba(matrix(one))[0, 1], o["reference_p"]
                    )
                    assert np.isclose(
                        1 / (1 + np.exp(-paths[h["head"]]["linear_prediction"])),
                        o["reference_p"],
                    )
                else:
                    assert np.isclose(
                        np.clip(m.predict(matrix(one))[0], 1, 800),
                        o["reference_conditional_pa"],
                    )
                replayed += 1
        pool = f.filter(
            (pl.col("origin_year") == y)
            & (pl.col("player_id") != pid)
            & (pl.col("role_eligible") == r["role_eligible"])
            & (pl.col("status_major_link") == r["status_major_link"])
            & ((pl.col("role_gap") > 0) == (r["role_gap"] > 0))
        )
        count = len(pool)
        pool = (
            pool.with_columns(
                (
                    (pl.col("age") - r["age"]) ** 2 / 25
                    + (pl.col("last_MLB_work") - r["last_MLB_work"]) ** 2
                    + (pl.col("last_MLB_quality") - r["last_MLB_quality"]) ** 2
                ).alias("distance")
            )
            .sort(["distance", "player_id"])
            .head(3)
        )
        peers = []
        for pr in pool.to_dicts():
            pq = q.filter(pl.col("row_id") == pr["row_id"])
            if len(pq):
                peers.append(
                    dict(
                        player_id=pr["player_id"],
                        name=pr["player_name"],
                        distance=pr["distance"],
                        age=pr["age"],
                        last_role_pa=pr["last_MLB_work"] * 600,
                        forecast=pq.select(
                            "observation_pa",
                            "reference_pa",
                            "finite_return_pa",
                            "next_pa",
                        ).row(0, named=True),
                    )
                )
        stats = (
            raw.filter(
                (pl.col("player_id") == pid)
                & (pl.col("season") <= y)
                & (pl.col("season") >= y - 2)
            )
            .select(
                "season",
                "bucket",
                "plate_appearances",
                "home_runs",
                "strike_outs",
                "base_on_balls",
                "hits",
                "at_bats",
            )
            .to_dicts()
        )
        ctx = contexts[f"{y}:{pid}"]
        budget_ev = pre["budgets"].get(str(rid))
        delayed = None
        if budget_ev:
            delayed = apply_to_role(
                o["reference_p"],
                o["reference_conditional_pa"],
                o["observation_rate"],
                budget_ev,
                excludes_known_suspension=True,
            )
        tr = unrestricted(
            f.filter(
                pl.col("row_id").is_in(
                    next(c for c in pre["cells"] if c["year"] == y and c["fold"] == k)[
                        "training_row_ids"
                    ]
                )
            )
        )
        walks.append(
            dict(
                row_id=rid,
                selection=why,
                forecast=o,
                raw_stats=stats,
                inputs={
                    n: r[n]
                    for n in FEATURES
                    + ["anticipated_preseason_readiness", "role_eligible"]
                },
                context=dict(
                    clinical_spells=ctx["clinical_spells"],
                    absence=ctx["absence"],
                    employment=ctx["employment"],
                    medical_recovery_certified=False,
                ),
                head_coefficients=paths,
                actual_gap_support=support(tr, one).to_dicts(),
                ready_transport_support=support(
                    tr, one.with_columns(pl.lit(0.0).alias("role_gap"))
                ).to_dicts(),
                finite_budget=budget_ev,
                delayed_recovery_sensitivity=delayed,
                peer_selection="same origin, role eligibility, reported MLB link and actual gap category; nearest age/last role/quality; no outcomes",
                peer_count=count,
                peers=peers,
            )
        )
    PUBLIC.mkdir(parents=True)
    save(
        PUBLIC / "player-walks.json",
        dict(cases=walks, player_walkthrough_status="pending_judgment"),
    )
    report = dict(
        scores=scores,
        reference_diagnostic=refscore,
        public_comparison=publicscores,
        changed_rows=q.filter(pl.col("finite_return_changed"))
        .select(
            "player_name",
            "origin_year",
            "observation_pa",
            "reference_p",
            "reference_conditional_pa",
            "ready_reference_p",
            "ready_reference_conditional_pa",
            "finite_return_p",
            "finite_return_conditional_pa",
            "finite_return_pa",
            "next_pa",
        )
        .to_dicts(),
        model_count=70,
        walk_count=len(walks),
        walk_heads_replayed=replayed,
        player_walkthrough_status="pending_judgment",
        deployment_approved=False,
        forecasts_or_explorer_promoted=False,
        protected_2026_outcomes_used=False,
        general_predictive_improvement_established=False,
        hashes={
            str(p): sha256_file(p)
            for p in [
                OUT / "preflight.json",
                OUT / "fit-seal.json",
                OUT / "fit-report.json",
                OUT / "predictions.parquet",
                PUBLIC / "player-walks.json",
                rawpath,
                contextpath,
                publicpath,
            ]
        },
    )
    save(PUBLIC / "report.json", report)
    protections()
    print(
        json.dumps(
            dict(changed=report["changed_rows"], reference=refscore, walks=len(walks)),
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["prepare", "fit", "review"])
    dict(prepare=prepare, fit=fit, review=review)[parser.parse_args().phase]()
