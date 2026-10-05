"""One defect repair, sealed folds, retained player walks and independent replay."""

import argparse
from pathlib import Path

import joblib
import numpy as np
import polars as pl
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from universal_baseball.finite_return_baseline import unrestricted
from universal_baseball.forecast_validation import preflight
from universal_baseball.known_suspension_budget import apply_to_role
from universal_baseball.role_health_separation import (
    FEATURES,
    OMITTED_CLINICAL,
    coefficients,
    matrix,
    medical_span_audit,
    support,
)
from universal_baseball.storage import sha256_file
from fit_practical_hitter_v31 import weights
from run_hitter_employment_comparison import ROOT, read, verify
from run_hitter_finite_return_baseline import metrics, protections, save

OLD = ROOT / "reports/generated/hitter-finite-return-baseline"
PRIOR = ROOT / "reports/model-evidence/hitter-finite-return-baseline"
OUT = ROOT / "reports/generated/hitter-role-health-separation"
PUBLIC = ROOT / "reports/model-evidence/hitter-role-health-separation"


def train_test(c):
    f = pl.read_parquet(OLD / f"features-{c['fold']}.parquet")
    tr = unrestricted(f.filter(pl.col("row_id").is_in(c["training_row_ids"])))
    te = f.filter(pl.col("row_id").is_in(c["test_row_ids"]))
    return f, tr.sort("row_id"), te.sort("row_id")


def prepare():
    assert not OUT.exists(), "Preserve existing preparation"
    protections()
    old = read(OLD / "preflight.json")
    verify(old["hashes"])
    complete = read(PRIOR / "completion.json")
    assert complete["player_walkthrough_status"] == "complete"
    q = pl.read_parquet(OLD / "predictions.parquet")
    assert q.height == 30519 and q["target_year"].max() == 2025
    paths = [
        Path(__file__),
        ROOT / "src/universal_baseball/role_health_separation.py",
        ROOT / "tests/test_role_health_separation.py",
        ROOT / "docs/hitter-role-health-separation-contract.md",
        OLD / "preflight.json",
        OLD / "predictions.parquet",
        PRIOR / "player-walks.json",
        PRIOR / "completion.json",
        ROOT / "src/universal_baseball/forecast_validation.py",
        ROOT / "src/universal_baseball/finite_return_baseline.py",
        ROOT / "src/universal_baseball/known_suspension_budget.py",
        ROOT / "scripts/fit_practical_hitter_v31.py",
        ROOT / "scripts/run_hitter_finite_return_baseline.py",
        ROOT / "scripts/run_hitter_employment_comparison.py",
    ]
    checks = []
    for c in old["cells"]:
        _, tr, te = train_test(c)
        eligible = te.filter(pl.col("role_eligible"))
        for head, sub in [
            ("participation", tr),
            ("conditional_pa", tr.filter(pl.col("next_pa") > 0)),
        ]:
            _, note = preflight(
                sub,
                eligible,
                cutoff=c["year"],
                fold=c["fold"],
                features=FEATURES,
                expected_keys=eligible.select("row_id", "horizon").iter_rows(),
            )
            assert (
                sub["ctx_information_date"].max()
                < eligible["ctx_information_date"].min()
            )
            checks.append(
                dict(
                    origin=c["year"],
                    fold=c["fold"],
                    head=head,
                    **note,
                    actual_support=support(sub, eligible).to_dicts(),
                    ready_support=support(
                        sub,
                        eligible.filter(
                            pl.col("row_id").is_in(old["transfer_row_ids"])
                        ).with_columns(pl.lit(0.0).alias("role_gap")),
                    ).to_dicts(),
                )
            )
    paths.extend(OLD / f"features-{k}.parquet" for k in range(5))
    paths.extend(
        Path(h["path"])
        for c in read(OLD / "fit-report.json")["cells"]
        for h in c["heads"]
    )
    OUT.mkdir()
    save(
        OUT / "preflight.json",
        dict(
            cells=old["cells"],
            checks=checks,
            features=FEATURES,
            omitted=OMITTED_CLINICAL,
            new_fits=0,
            before_fitting=True,
            transfer_row_ids=old["transfer_row_ids"],
            budgets=old["budgets"],
            hashes={str(p): sha256_file(p) for p in paths},
            protected_2026_outcomes_used=False,
            deployment_approved=False,
        ),
    )
    print("All 70 training checks completed before fitting", flush=True)


def fit():
    pre = read(OUT / "preflight.json")
    verify(pre["hashes"])
    protections()
    assert len(pre["checks"]) == 70
    assert (
        not list(OUT.glob("model-*.joblib"))
        and not (OUT / "predictions.parquet").exists()
    )
    save(
        OUT / "fit-seal.json",
        dict(preflight_sha256=sha256_file(OUT / "preflight.json")),
    )
    original = pl.read_parquet(OLD / "predictions.parquet").sort("row_id")
    parts, receipts = [], []
    with threadpool_limits(limits=2):
        for c in pre["cells"]:
            _, tr, te = train_test(c)
            g = original.filter(pl.col("row_id").is_in(c["test_row_ids"])).sort(
                "row_id"
            )
            assert g["row_id"].equals(te["row_id"])
            models, heads = {}, []
            for head, sub, estimator, target in [
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
                m = make_pipeline(StandardScaler(), estimator)
                m.fit(
                    matrix(sub),
                    sub[target].to_numpy(),
                    **{m.steps[-1][0] + "__sample_weight": weights(sub)},
                )
                path = OUT / f"model-{head}-{c['year']}-{c['fold']}.joblib"
                joblib.dump(m, path, compress=3)
                models[head] = m
                heads.append(
                    dict(
                        head=head,
                        path=str(path),
                        sha256=sha256_file(path),
                        training_rows=len(sub),
                        training_people=sub["player_id"].n_unique(),
                    )
                )
            p = models["participation"].predict_proba(matrix(te))[:, 1]
            raw = models["conditional_pa"].predict(matrix(te))
            cond = np.clip(raw, 1, 800)
            rp = models["participation"].predict_proba(matrix(te, reported_ready=True))[
                :, 1
            ]
            rc = np.clip(
                models["conditional_pa"].predict(matrix(te, reported_ready=True)),
                1,
                800,
            )
            ep, ec = (
                g["observation_p"].to_numpy().copy(),
                g["observation_conditional_pa"].to_numpy().copy(),
            )
            changed = te["row_id"].is_in(pre["transfer_row_ids"]).to_numpy()
            for i in np.flatnonzero(changed):
                r = apply_to_role(
                    rp[i],
                    rc[i],
                    g["observation_rate"][int(i)],
                    pre["budgets"][str(te["row_id"][int(i)])],
                    excludes_known_suspension=True,
                )
                ep[i], ec[i] = r["probability"], r["conditional_pa"]
            rate = g["observation_rate"].to_numpy()
            unit = rate / 600 + g["origin_replacement_rate"].to_numpy()
            parts.append(
                g.with_columns(
                    pl.Series("separated_p", p),
                    pl.Series("separated_raw_conditional_pa", raw),
                    pl.Series("separated_conditional_pa", cond),
                    pl.Series("separated_pa", p * cond),
                    pl.Series("separated_value", p * cond * unit),
                    pl.Series("ready_separated_p", rp),
                    pl.Series("ready_separated_conditional_pa", rc),
                    pl.Series("repair_p", ep),
                    pl.Series("repair_conditional_pa", ec),
                    pl.Series("repair_pa", ep * ec),
                    pl.Series("repair_value", ep * ec * unit),
                )
            )
            receipts.append(dict(origin=c["year"], fold=c["fold"], heads=heads))
            print(f"Role-only reference {c['year']}/{c['fold']}", flush=True)
    q = pl.concat(parts).sort("row_id")
    assert q.height == original.height and q.select(original.columns).equals(original)
    q.write_parquet(OUT / "predictions.parquet")
    save(
        OUT / "fit-report.json",
        dict(
            cells=receipts,
            new_heads=70,
            prediction_sha256=sha256_file(OUT / "predictions.parquet"),
            player_walkthrough_status="pending",
            protected_2026_outcomes_used=False,
        ),
    )
    verify(pre["hashes"])
    protections()


def paired_interval(g, arm, anchor):
    delta = (g[arm + "_pa"].to_numpy() - g["next_pa"].to_numpy()) ** 2
    delta -= (g[anchor + "_pa"].to_numpy() - g["next_pa"].to_numpy()) ** 2
    people, inverse = np.unique(g["player_id"].to_numpy(), return_inverse=True)
    years = g["origin_year"].to_numpy()
    rng = np.random.default_rng(314)
    samples = []
    for _ in range(500):
        counts = np.bincount(
            rng.integers(0, len(people), len(people)), minlength=len(people)
        )
        w = counts[inverse]
        if all(w[years == y].sum() > 0 for y in np.unique(years)):
            samples.append(
                np.mean(
                    [
                        np.average(delta[years == y], weights=w[years == y])
                        for y in np.unique(years)
                    ]
                )
            )
    return dict(
        loss="equal-origin PA MSE difference",
        candidate=arm,
        benchmark=anchor,
        point=float(np.mean([delta[years == y].mean() for y in np.unique(years)])),
        interval_95=np.quantile(samples, [0.025, 0.975]).tolist(),
        draws=len(samples),
    )


def review():
    assert not PUBLIC.exists()
    pre, fitreport = read(OUT / "preflight.json"), read(OUT / "fit-report.json")
    verify(pre["hashes"])
    assert sha256_file(OUT / "predictions.parquet") == fitreport["prediction_sha256"]
    q = pl.read_parquet(OUT / "predictions.parquet")
    broad = q.filter(
        ~pl.col("source_addition")
        & pl.col("role_eligible")
        & pl.col("reference_unrestricted")
    )
    assert len(broad) == 1988
    broad = broad.with_columns(
        (
            pl.col("reference_pa")
            * (pl.col("observation_rate") / 600 + pl.col("origin_replacement_rate"))
        ).alias("reference_value")
    )
    arms = ["observation", "reference", "separated"]
    scores = {a: metrics(broad, a) for a in arms}
    origin = {
        str(y): {a: metrics(broad.filter(pl.col("origin_year") == y), a) for a in arms}
        for y in sorted(broad["origin_year"].unique())
    }
    exits = {a: metrics(broad.filter(pl.col("next_pa") == 0), a) for a in arms}
    gates = dict(
        primary_no_worse=scores["separated"]["pa_mse"]
        <= scores["observation"]["pa_mse"],
        brier_no_worse=scores["separated"]["brier"] <= scores["observation"]["brier"],
        logloss_no_worse=scores["separated"]["logloss"]
        <= scores["observation"]["logloss"],
        total_within_5pct=abs(
            scores["separated"]["expected_pa"] / scores["separated"]["actual_pa"] - 1
        )
        <= 0.05,
        each_origin_mse_within_2pct=all(
            v["separated"]["pa_mse"] <= 1.02 * v["observation"]["pa_mse"]
            for v in origin.values()
        ),
    )
    retained = read(PRIOR / "player-walks.json")["cases"]
    chosen = {r["row_id"]: ["retained preceding case"] for r in retained}
    d = broad.with_columns(
        (
            (pl.col("separated_pa") - pl.col("next_pa")) ** 2
            - (pl.col("observation_pa") - pl.col("next_pa")) ** 2
        ).alias("delta"),
        (pl.col("separated_pa") - pl.col("next_pa")).alias("error"),
    )
    for label, col, descending in [
        ("largest gain", "delta", False),
        ("largest harm", "delta", True),
        ("false high", "error", True),
        ("false low", "error", False),
    ]:
        rid = d.sort([col, "row_id"], descending=[descending, False])["row_id"][0]
        chosen.setdefault(rid, []).append(label)
    ordinary = d.filter(pl.col("next_pa") > 0).with_columns(
        pl.col("error").abs().alias("abs")
    )
    rid = ordinary.sort(["abs", "row_id"])["row_id"][0]
    chosen.setdefault(rid, []).append("ordinary")
    rawpath = ROOT / "reports/generated/practical-hitter-v31/dated-stints.parquet"
    ledgerpath = ROOT / "reports/generated/hitter-status-evidence-v2/status-ledger.json"
    winpath = (
        ROOT / "reports/generated/practical-hitter-late-role-v46/source-manifest.json"
    )
    raw = pl.read_parquet(rawpath)
    ledger = {r["candidate_key"]: r for r in read(ledgerpath)["rows"]}
    windows = {}
    for capture in read(winpath)["sources"]:
        path = Path(capture["path"])
        assert sha256_file(path) == capture["sha256"]
        for s in read(path)["stats"][0]["splits"]:
            windows.setdefault(s["player"]["id"], []).append(
                dict(
                    start=capture["start"],
                    end=capture["end"],
                    pa=s["stat"]["plateAppearances"],
                    source_path=str(path),
                    source_sha256=capture["sha256"],
                )
            )
    walks = []
    frames = {k: pl.read_parquet(OLD / f"features-{k}.parquet") for k in range(5)}
    for rid, selection in chosen.items():
        o = q.filter(pl.col("row_id") == rid).row(0, named=True)
        y, k, pid = o["origin_year"], o["outer_fold"], o["player_id"]
        f = frames[k]
        one = f.filter(pl.col("row_id") == rid)
        r = one.row(0, named=True)
        c = next(c for c in pre["cells"] if c["year"] == y and c["fold"] == k)
        tr = unrestricted(f.filter(pl.col("row_id").is_in(c["training_row_ids"])))
        headpaths, clinicaldiagnosis = {}, []
        if r["role_eligible"]:
            for head in ["participation", "conditional_pa"]:
                m = joblib.load(OUT / f"model-{head}-{y}-{k}.joblib")
                headpaths[head] = coefficients(m, matrix(one))
                headpaths[head + "_reported_ready"] = coefficients(
                    m, matrix(one, reported_ready=True)
                )
            oldmodel = joblib.load(OLD / f"model-conditional_pa-{y}-{k}.joblib")
            from universal_baseball.finite_return_baseline import (
                coefficients as oldcoef,
                matrix as oldmatrix,
            )

            oldeffects = oldcoef(oldmodel, oldmatrix(one))["feature_effects"]
            sub = tr.filter(pl.col("next_pa") > 0)
            for n in OMITTED_CLINICAL:
                clinicaldiagnosis.append(
                    dict(
                        feature=n,
                        supplied=r[n],
                        min=float(sub[n].min()),
                        max=float(sub[n].max()),
                        people_nonzero=sub.filter(pl.col(n) > 0)[
                            "player_id"
                        ].n_unique(),
                        old_conditional_effect=oldeffects[n],
                        omitted_from_repaired_heads=True,
                    )
                )
        pool = f.filter(
            (pl.col("origin_year") == y)
            & (pl.col("player_id") != pid)
            & (pl.col("role_eligible") == r["role_eligible"])
            & (pl.col("status_major_link") == r["status_major_link"])
            & ((pl.col("role_gap") > 0) == (r["role_gap"] > 0))
        )
        peers = pool.with_columns(
            (
                (pl.col("age") - r["age"]) ** 2 / 25
                + (pl.col("last_MLB_work") - r["last_MLB_work"]) ** 2
                + (pl.col("last_MLB_quality") - r["last_MLB_quality"]) ** 2
            ).alias("distance")
        )
        peers = (
            peers.sort(["distance", "player_id"])
            .head(3)
            .select("row_id", "age", "last_MLB_work", "distance")
        )
        peers = peers.join(
            q.select(
                "row_id",
                "player_name",
                "observation_pa",
                "reference_pa",
                "separated_pa",
                "next_pa",
            ),
            on="row_id",
            how="left",
            validate="1:1",
        )
        ctx = ledger[f"{y}:{pid}"]
        walks.append(
            dict(
                row_id=rid,
                selection=selection,
                forecast=o,
                known_stats=raw.filter(
                    (pl.col("player_id") == pid) & pl.col("season").is_between(y - 2, y)
                )
                .select(
                    "season",
                    "bucket",
                    "plate_appearances",
                    "home_runs",
                    "base_on_balls",
                    "strike_outs",
                    "hits",
                    "at_bats",
                )
                .to_dicts(),
                role_inputs={n: r[n] for n in FEATURES},
                clinical_input_diagnosis=clinicaldiagnosis,
                context=ctx,
                medical_span_audit=medical_span_audit(
                    ctx["clinical_spells"],
                    windows.get(pid, []),
                    r["ctx_information_date"],
                ),
                coefficients=headpaths,
                actual_gap_support=support(tr, one).to_dicts(),
                reported_ready_support=support(
                    tr, one.with_columns(pl.lit(0.0).alias("role_gap"))
                ).to_dicts(),
                peer_rule="Same origin, eligibility, MLB link and actual-gap category, nearest age/prior workload/quality; no outcomes",
                peer_pool_count=len(pool),
                peers=peers.to_dicts(),
                clinical_recovery_probability_estimated=False,
            )
        )
    PUBLIC.mkdir(parents=True)
    save(
        PUBLIC / "player-walks.json",
        dict(cases=walks, player_walkthrough_status="pending_judgment"),
    )
    report = dict(
        scores=scores,
        per_origin=origin,
        exits=exits,
        gates=gates,
        paired_uncertainty=[
            paired_interval(broad, "separated", a) for a in ["observation", "reference"]
        ],
        limited_reconstruction=q.filter(pl.col("finite_return_changed")).to_dicts(),
        changed_historical_research_rows=1,
        walkthrough_cases=len(walks),
        player_walkthrough_status="pending_judgment",
        deployment_approved=False,
        clinical_availability_repair_complete=False,
        protected_2026_outcomes_used=False,
        hashes={
            str(p): sha256_file(p)
            for p in [
                OUT / "preflight.json",
                OUT / "fit-report.json",
                OUT / "predictions.parquet",
                PUBLIC / "player-walks.json",
                rawpath,
                ledgerpath,
                winpath,
            ]
        },
    )
    save(PUBLIC / "report.json", report)
    protections()
    print(dict(scores=scores, gates=gates, walks=len(walks)), flush=True)


def finalize():
    report = read(PUBLIC / "report.json")
    verify(report["hashes"])
    pre, fitreport = read(OUT / "preflight.json"), read(OUT / "fit-report.json")
    verify(pre["hashes"])
    q = pl.read_parquet(OUT / "predictions.parquet").sort("row_id")
    old = pl.read_parquet(OLD / "predictions.parquet").sort("row_id")
    assert q.select(old.columns).equals(old)
    assert (
        q.filter(~pl.col("finite_return_changed"))
        .select(pl.col("repair_pa") == pl.col("observation_pa"))
        .to_series()
        .all()
    )
    replayed = 0
    for c, receipt in zip(pre["cells"], fitreport["cells"], strict=True):
        _, _, te = train_test(c)
        g = q.filter(pl.col("row_id").is_in(c["test_row_ids"])).sort("row_id")
        for h in receipt["heads"]:
            assert sha256_file(Path(h["path"])) == h["sha256"]
            m = joblib.load(h["path"])
            for ready in [False, True]:
                prefix = "ready_separated" if ready else "separated"
                if h["head"] == "participation":
                    result, name = (
                        m.predict_proba(matrix(te, reported_ready=ready))[:, 1],
                        prefix + "_p",
                    )
                else:
                    result, name = (
                        np.clip(m.predict(matrix(te, reported_ready=ready)), 1, 800),
                        prefix + "_conditional_pa",
                    )
                assert np.allclose(result, g[name].to_numpy(), rtol=1e-12, atol=1e-10)
            replayed += 1
    broad = q.filter(
        ~pl.col("source_addition")
        & pl.col("role_eligible")
        & pl.col("reference_unrestricted")
    )
    for a in ["observation", "reference", "separated"]:
        g = broad.to_pandas()
        # Independently group the raw row losses, rather than call metrics again.
        actual, pred, p = (
            g.next_pa.to_numpy(),
            g[a + "_pa"].to_numpy(),
            g[a + "_p"].to_numpy(),
        )
        raw = dict(
            pa_mse=(pred - actual) ** 2,
            pa_mae=abs(pred - actual),
            brier=(p - (actual > 0)) ** 2,
            logloss=-np.log(
                np.where(
                    actual > 0,
                    np.clip(p, 1e-12, 1 - 1e-12),
                    np.clip(1 - p, 1e-12, 1 - 1e-12),
                )
            ),
        )
        for n, v in raw.items():
            g["loss"] = v
            assert np.isclose(
                g.groupby("origin_year").loss.mean().mean(), report["scores"][a][n]
            )
    walks = read(PUBLIC / "player-walks.json")["cases"]
    assert all(w["known_stats"] and w["role_inputs"] and w["peer_rule"] for w in walks)
    doc = ROOT / "docs/hitter-role-health-separation-result.md"
    assert doc.exists() and "Walkthrough status: complete" in doc.read_text(
        encoding="utf8"
    )
    protections()
    save(
        PUBLIC / "completion.json",
        dict(
            player_walkthrough_status="complete",
            replayed_heads=replayed,
            previous_forecasts_preserved=True,
            deployment_approved=False,
            clinical_availability_repair_complete=False,
            protected_2026_outcomes_used=False,
            disposition="repair role representation; clinical risk remains unsupported",
            hashes={
                str(p): sha256_file(p)
                for p in [
                    doc,
                    PUBLIC / "report.json",
                    PUBLIC / "player-walks.json",
                    Path(__file__),
                ]
            },
        ),
    )
    print(
        f"{replayed} heads replayed; scores independently reconstructed; no deployment",
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["prepare", "fit", "review", "finalize"])
    {"prepare": prepare, "fit": fit, "review": review, "finalize": finalize}[
        parser.parse_args().phase
    ]()
