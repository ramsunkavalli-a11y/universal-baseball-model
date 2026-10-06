"""One matched medical-input contrast with stronger anchor and fixed fallback."""

import argparse
from pathlib import Path

import joblib
import numpy as np
import polars as pl
from sklearn.ensemble import (
    HistGradientBoostingClassifier,
    HistGradientBoostingRegressor,
)
from threadpoolctl import threadpool_limits

from universal_baseball.forecast_validation import preflight
from universal_baseball.medical_opportunity_comparison import (
    OLD,
    NEW,
    frame,
    support,
    apply,
)
from universal_baseball.storage import sha256_file
from fit_practical_hitter_v31 import weights
from run_hitter_employment_comparison import ROOT, read, verify
from run_hitter_finite_return_baseline import metrics, protections, save

GEN = ROOT / "reports/generated"
BASE = GEN / "hitter-nonmedical-opportunity"
SOURCE = GEN / "hitter-medical-timeline-repair"
PRIOR = ROOT / "reports/model-evidence/hitter-medical-timeline-repair"
OUT = GEN / "hitter-medical-opportunity-comparison"
PUBLIC = ROOT / "reports/model-evidence/hitter-medical-opportunity-comparison"
ARMS = ["legacy_refit", "repaired"]
FIXED = [
    (581527, 2016, "Devon Travis"),
    (665487, 2022, "Fernando Tatis Jr."),
    (656555, 2023, "Rhys Hoskins"),
    (453056, 2018, "Jacoby Ellsbury"),
    (670541, 2022, "Yordan Alvarez"),
    (596748, 2017, "Maikel Franco"),
    (592450, 2024, "Aaron Judge"),
    (592192, 2016, "Mark Canha"),
]


def validate_sources():
    protections()
    for receipt in [
        PRIOR / "completion.json",
        PRIOR / "identity-review.json",
        SOURCE / "source-seal.json",
        SOURCE / "build-receipt.json",
    ]:
        verify(read(receipt)["hashes"])
    assert read(PRIOR / "completion.json")["player_walkthrough_status"] == "complete"
    assert read(PRIOR / "identity-review.json")["fixed_contract_names_complete"]
    oldpre = read(BASE / "preflight.json")
    verify({str(ROOT / p): h for p, h in oldpre["hashes"].items()})
    verify(read(BASE / "final-review.json")["hashes"])
    fit = read(BASE / "fit-report.json")
    assert sha256_file(BASE / "predictions.parquet") == fit["predictions_sha256"]
    return oldpre, fit


def prepare():
    assert not OUT.exists(), "Preserve completed or partial experiment"
    oldpre, oldfit = validate_sources()
    q = pl.read_parquet(BASE / "predictions.parquet").sort("row_id")
    assert len(q) == 30519 and q["target_year"].max() == 2025
    obs = pl.read_parquet(SOURCE / "model-observations.parquet")
    names = {
        "legacy_refit": oldpre["job_features"],
        "repaired": [n for n in oldpre["job_features"] if n not in OLD] + NEW,
    }
    assert len(names["legacy_refit"]) == 293 and set(OLD) <= set(names["legacy_refit"])
    assert len(names["repaired"]) == 296 and not set(OLD) & set(names["repaired"])
    paths = [
        Path(__file__),
        ROOT / "src/universal_baseball/medical_opportunity_comparison.py",
        ROOT / "tests/test_medical_opportunity_comparison.py",
        ROOT / "docs/hitter-medical-opportunity-comparison-contract.md",
        ROOT / "src/universal_baseball/forecast_validation.py",
        ROOT / "scripts/fit_practical_hitter_v31.py",
        ROOT / "src/universal_baseball/hitter_evidence_representation.py",
        SOURCE / "model-observations.parquet",
        SOURCE / "source-seal.json",
        SOURCE / "build-receipt.json",
        PRIOR / "completion.json",
        PRIOR / "identity-review.json",
        BASE / "preflight.json",
        BASE / "fit-report.json",
        BASE / "predictions.parquet",
        BASE / "final-review.json",
        GEN / "practical-hitter-v31/dated-stints.parquet",
    ]
    paths += [BASE / f"features-{k}.parquet" for k in range(5)]
    paths += [ROOT / h["path"] for c in oldfit["cells"] for h in c["heads"]]
    frames = {
        k: frame(pl.read_parquet(BASE / f"features-{k}.parquet").sort("row_id"), obs)
        for k in range(5)
    }
    for pid, y, name in FIXED:
        actual = q.filter((pl.col("player_id") == pid) & (pl.col("origin_year") == y))
        assert len(actual) == 1 and actual["player_name"].item() == name
    checks, cells, gates = [], [], []
    for c in oldpre["cells"]:
        y, k = c["year"], c["fold"]
        f = frames[k]
        train = f.filter(
            pl.col("row_id").is_in(c["training_row_ids"]) & pl.col("med_eligible")
        ).sort("row_id")
        te = f.filter(pl.col("row_id").is_in(c["test_row_ids"])).sort("row_id")
        assert te["row_id"].equals(
            q.filter(pl.col("row_id").is_in(c["test_row_ids"]))["row_id"]
        )
        eligible = te.filter(pl.col("med_eligible"))
        active = train.filter(pl.col("next_pa") > 0)
        fit_allowed = (
            len(eligible) > 0
            and len(train) >= 200
            and train["player_id"].n_unique() >= 100
            and len(active) >= 200
            and active["player_id"].n_unique() >= 100
            and train["next_active"].n_unique() == 2
        )
        flags = te.select("row_id", "med_eligible")
        for head, sub in [("participation", train), ("conditional_pa", active)]:
            s = support(sub, te).select(
                "row_id",
                pl.col("medical_profile_people").alias(head + "_people"),
                pl.col("medical_range_outside").alias(head + "_outside"),
            )
            flags = flags.join(s, on="row_id", validate="1:1")
            note = dict(
                origin=y,
                fold=k,
                head=head,
                training_rows=len(sub),
                training_people=sub["player_id"].n_unique(),
                fit_allowed=fit_allowed,
            )
            if fit_allowed:
                assert (
                    sub["ctx_information_date"].max()
                    < eligible["ctx_information_date"].min()
                )
                for arm in ARMS:
                    _, details = preflight(
                        sub,
                        eligible,
                        cutoff=y,
                        fold=k,
                        features=names[arm],
                        expected_keys=eligible.select("row_id", "horizon").iter_rows(),
                    )
                    checks.append(dict(arm=arm, **note, preflight=details))
            else:
                checks.append(dict(arm="both_fallback", **note))
        flags = flags.with_columns(
            (
                pl.col("med_eligible")
                & pl.lit(fit_allowed)
                & (pl.col("participation_people") >= 20)
                & (pl.col("conditional_pa_people") >= 20)
                & ~pl.col("participation_outside")
                & ~pl.col("conditional_pa_outside")
            ).alias("medical_applied"),
            (pl.col("med_eligible") & pl.lit(fit_allowed)).alias("raw_model_available"),
        ).with_columns(
            pl.when(~pl.col("med_eligible"))
            .then(pl.lit("medical_ineligible"))
            .when(~pl.lit(fit_allowed))
            .then(pl.lit("training_unavailable"))
            .when(
                (pl.col("participation_people") < 20)
                | (pl.col("conditional_pa_people") < 20)
            )
            .then(pl.lit("sparse_medical_profile"))
            .when(pl.col("participation_outside") | pl.col("conditional_pa_outside"))
            .then(pl.lit("outside_medical_support"))
            .otherwise(pl.lit("applied"))
            .alias("medical_gate_reason")
        )
        gates.append(flags)
        cells.append(
            dict(
                **c,
                fit_allowed=fit_allowed,
                eligible_test_rows=len(eligible),
                applied_rows=int(flags["medical_applied"].sum()),
            )
        )
    # Replay the stronger historical forecast, never use it to train either new head.
    replayed = 0
    with threadpool_limits(limits=2):
        for c in oldfit["cells"]:
            f = (
                frames[c["fold"]]
                .filter(pl.col("row_id").is_in(c["test_row_ids"]))
                .sort("row_id")
            )
            g = q.filter(pl.col("row_id").is_in(c["test_row_ids"]))
            for h in c["heads"]:
                path = ROOT / h["path"]
                assert sha256_file(path) == h["sha256"]
                m = joblib.load(path)
                assert h["features"] == oldpre["job_features"]
                x = f.select(h["features"]).to_numpy()
                v = (
                    m.predict_proba(x)[:, 1]
                    if h["head"] == "participation"
                    else m.predict(x)
                )
                col = (
                    "observation_raw_p"
                    if h["head"] == "participation"
                    else "observation_raw_conditional_pa"
                )
                assert np.allclose(v, g[col].to_numpy(), atol=1e-10, rtol=0)
                replayed += 1
    assert replayed == 70
    OUT.mkdir()
    save(
        OUT / "source-seal.json",
        dict(before_fitting=True, hashes={str(p): sha256_file(p) for p in paths}),
    )
    for k, f in frames.items():
        f.write_parquet(OUT / f"features-{k}.parquet")
    pl.concat(gates).sort("row_id").write_parquet(OUT / "support-gates.parquet")
    paths += [OUT / f"features-{k}.parquet" for k in range(5)] + [
        OUT / "support-gates.parquet",
        OUT / "source-seal.json",
    ]
    save(
        OUT / "preflight.json",
        dict(
            before_fitting=True,
            cells=cells,
            checks=checks,
            features=names,
            settings=oldpre["settings"],
            baseline_heads_replayed=replayed,
            new_fits=0,
            eligible_rows=sum(c["eligible_test_rows"] for c in cells),
            applied_rows=sum(c["applied_rows"] for c in cells),
            hashes={str(p): sha256_file(p) for p in paths},
        ),
    )
    protections()
    print(
        f"Preflight complete: {sum(c['applied_rows'] for c in cells)} applied, {sum(c['eligible_test_rows'] for c in cells)} eligible; anchor heads replayed 70",
        flush=True,
    )


def fit():
    pre = read(OUT / "preflight.json")
    verify(pre["hashes"])
    protections()
    assert (
        not list(OUT.glob("model-*.joblib"))
        and not (OUT / "predictions.parquet").exists()
    )
    save(
        OUT / "fit-seal.json",
        dict(before_fitting=True, preflight_sha256=sha256_file(OUT / "preflight.json")),
    )
    q = pl.read_parquet(BASE / "predictions.parquet").sort("row_id")
    flags = pl.read_parquet(OUT / "support-gates.parquet")
    results, notes = [], []
    with threadpool_limits(limits=2):
        for c in pre["cells"]:
            y, k = c["year"], c["fold"]
            f = pl.read_parquet(OUT / f"features-{k}.parquet")
            tr = f.filter(
                pl.col("row_id").is_in(c["training_row_ids"]) & pl.col("med_eligible")
            ).sort("row_id")
            te = f.filter(pl.col("row_id").is_in(c["test_row_ids"])).sort("row_id")
            g = (
                q.filter(pl.col("row_id").is_in(c["test_row_ids"]))
                .join(flags, on="row_id", validate="1:1")
                .sort("row_id")
            )
            unit = (
                g["observation_rate"].to_numpy() / 600
                + g["origin_replacement_rate"].to_numpy()
            )
            eligible = te["med_eligible"].to_numpy()
            heads = []
            for arm in ARMS:
                raw_p = g["observation_p"].to_numpy().copy()
                raw_c = g["observation_conditional_pa"].to_numpy().copy()
                if c["fit_allowed"]:
                    for head, sub, cls, target in [
                        (
                            "participation",
                            tr,
                            HistGradientBoostingClassifier,
                            "next_active",
                        ),
                        (
                            "conditional_pa",
                            tr.filter(pl.col("next_pa") > 0),
                            HistGradientBoostingRegressor,
                            "next_pa",
                        ),
                    ]:
                        m = cls(**pre["settings"])
                        m.fit(
                            sub.select(pre["features"][arm]).to_numpy(),
                            sub[target].to_numpy(),
                            sample_weight=weights(sub),
                        )
                        path = OUT / f"model-{arm}-{head}-{y}-{k}.joblib"
                        joblib.dump(m, path, compress=3)
                        x = (
                            te.filter(pl.col("med_eligible"))
                            .select(pre["features"][arm])
                            .to_numpy()
                        )
                        v = (
                            m.predict_proba(x)[:, 1]
                            if head == "participation"
                            else m.predict(x)
                        )
                        if head == "participation":
                            raw_p[eligible] = v
                        else:
                            raw_c[eligible] = v
                        heads.append(
                            dict(
                                arm=arm,
                                head=head,
                                path=str(path),
                                sha256=sha256_file(path),
                                training_rows=len(sub),
                                training_people=sub["player_id"].n_unique(),
                            )
                        )
                p, cond = apply(
                    g["observation_p"].to_numpy(),
                    g["observation_conditional_pa"].to_numpy(),
                    raw_p,
                    raw_c,
                    g["medical_applied"].to_numpy(),
                )
                rawcond = np.clip(raw_c, 1, 800)
                g = g.with_columns(
                    pl.Series(arm + "_raw_p", raw_p),
                    pl.Series(arm + "_raw_conditional_pa", raw_c),
                    pl.Series(arm + "_diagnostic_p", raw_p),
                    pl.Series(arm + "_diagnostic_conditional_pa", rawcond),
                    pl.Series(arm + "_diagnostic_pa", raw_p * rawcond),
                    pl.Series(arm + "_diagnostic_value", raw_p * rawcond * unit),
                    pl.Series(arm + "_p", p),
                    pl.Series(arm + "_conditional_pa", cond),
                    pl.Series(arm + "_pa", p * cond),
                    pl.Series(arm + "_value", p * cond * unit),
                )
                fallback = ~g["medical_applied"].to_numpy()
                assert np.array_equal(
                    p[fallback], g["observation_p"].to_numpy()[fallback]
                )
                assert np.array_equal(
                    cond[fallback], g["observation_conditional_pa"].to_numpy()[fallback]
                )
            assert g.select(q.columns).equals(
                q.filter(pl.col("row_id").is_in(c["test_row_ids"]))
            )
            g.write_parquet(OUT / f"forecast-{y}-{k}.parquet")
            notes.append(
                dict(origin=y, fold=k, heads=heads, fit_allowed=c["fit_allowed"])
            )
            results.append(g)
            print(
                f"Matched medical heads {y}/{k}: {len(heads)} fits, {c['applied_rows']} applied",
                flush=True,
            )
    result = pl.concat(results).sort("row_id")
    assert len(result) == 30519 and result.select(q.columns).equals(q)
    result.write_parquet(OUT / "predictions.parquet")
    save(
        OUT / "fit-report.json",
        dict(
            cells=notes,
            new_heads=sum(len(c["heads"]) for c in notes),
            predictions_sha256=sha256_file(OUT / "predictions.parquet"),
            model_hashes={h["path"]: h["sha256"] for c in notes for h in c["heads"]},
            player_walkthrough_status="pending",
            deployment_approved=False,
            protected_2026_outcomes_used=False,
        ),
    )
    verify(pre["hashes"])
    protections()


def interval(g, arm, anchor):
    years = g["origin_year"].to_numpy()
    y = g["next_pa"].to_numpy()
    loss = (g[arm + "_pa"].to_numpy() - y) ** 2 - (
        g[anchor + "_pa"].to_numpy() - y
    ) ** 2
    people, ix = np.unique(g["player_id"].to_numpy(), return_inverse=True)
    rng = np.random.default_rng(314)
    values = []
    for _ in range(1000):
        w = np.bincount(
            rng.integers(len(people), size=len(people)), minlength=len(people)
        )[ix]
        if all(w[years == a].sum() > 0 for a in np.unique(years)):
            values.append(
                np.mean(
                    [
                        np.average(loss[years == a], weights=w[years == a])
                        for a in np.unique(years)
                    ]
                )
            )
    return dict(
        loss="equal-origin PA MSE difference",
        candidate=arm,
        anchor=anchor,
        point=float(np.mean([loss[years == a].mean() for a in np.unique(years)])),
        interval_95=np.quantile(values, [0.025, 0.975]).tolist(),
        draws=len(values),
    )


def score():
    assert not PUBLIC.exists()
    pre = read(OUT / "preflight.json")
    verify(pre["hashes"])
    fit = read(OUT / "fit-report.json")
    verify(fit["model_hashes"])
    assert sha256_file(OUT / "predictions.parquet") == fit["predictions_sha256"]
    q = pl.read_parquet(OUT / "predictions.parquet")
    arms = ["observation", *ARMS]
    eligible = q.filter(pl.col("med_eligible"))
    scopes = dict(
        full_population=q,
        eligible=eligible,
        applied=q.filter(pl.col("medical_applied")),
        eligible_exits=eligible.filter(pl.col("next_pa") == 0),
    )
    scores = {
        key: {arm: metrics(g, arm) for arm in arms}
        for key, g in scopes.items()
        if len(g)
    }
    raw = q.filter(pl.col("raw_model_available"))
    scores["raw_model_available"] = {
        a: metrics(raw, a)
        for a in ["observation", "legacy_refit_diagnostic", "repaired_diagnostic"]
    }
    for arm in arms:
        active = eligible.filter(pl.col("next_pa") > 0)
        scores["eligible"][arm]["active_conditional_pa_rmse"] = float(
            np.sqrt(
                np.mean(
                    [
                        (
                            (
                                g[arm + "_conditional_pa"].to_numpy()
                                - g["next_pa"].to_numpy()
                            )
                            ** 2
                        ).mean()
                        for g in active.partition_by("origin_year")
                    ]
                )
            )
        )
        scores["eligible"][arm]["expected_value"] = float(
            eligible[arm + "_value"].sum()
        )
        scores["eligible"][arm]["actual_value"] = float(
            eligible["actual_relative_value"].sum()
        )
    origins = {
        str(y): {
            a: metrics(eligible.filter(pl.col("origin_year") == y), a) for a in arms
        }
        for y in sorted(eligible["origin_year"].unique())
    }
    f = pl.read_parquet(OUT / "features-0.parquet")
    groups = q.join(
        f.select("row_id", "observation_state", "med_current"),
        on="row_id",
        validate="1:1",
    )
    group_scores = {}
    for col in ["stage", "observation_state", "med_current", "medical_gate_reason"]:
        group_scores[col] = [
            {"group": g[col][0], "scores": {a: metrics(g, a) for a in arms}}
            for g in groups.partition_by(col)
            if len(g)
        ]
    paired = [
        interval(eligible, "repaired", a) for a in ["observation", "legacy_refit"]
    ]
    candidate, anchor = (
        scores["eligible"]["repaired"],
        scores["eligible"]["observation"],
    )
    gates = dict(
        primary_improves=candidate["pa_mse"] < anchor["pa_mse"],
        paired_interval_negative=paired[0]["interval_95"][1] < 0,
        delivered_value_no_worse=candidate["value_mse"] <= anchor["value_mse"],
        brier_no_worse=candidate["brier"] <= anchor["brier"],
        logloss_no_worse=candidate["logloss"] <= anchor["logloss"],
        aggregate_pa_bias_no_worse=abs(
            candidate["expected_pa"] - candidate["actual_pa"]
        )
        <= abs(anchor["expected_pa"] - anchor["actual_pa"]),
        every_origin_rmse_within_2pct=all(
            v["repaired"]["pa_rmse"] <= 1.02 * v["observation"]["pa_rmse"]
            for v in origins.values()
        ),
    )
    chosen = {}
    for pid, y, name in FIXED:
        r = q.filter((pl.col("player_id") == pid) & (pl.col("origin_year") == y)).row(
            0, named=True
        )
        assert r["player_name"] == name
        chosen[r["row_id"]] = ["fixed before fitting"]
    diagnosis = eligible.with_columns(
        (
            (pl.col("observation_pa") - pl.col("next_pa")).abs()
            - (pl.col("repaired_pa") - pl.col("next_pa")).abs()
        ).alias("improvement"),
        (pl.col("repaired_pa") - pl.col("next_pa")).alias("signed_error"),
    )
    for label, col, descending in [
        ("largest improvement", "improvement", True),
        ("largest deterioration", "improvement", False),
        ("largest false high", "signed_error", True),
        ("largest false low", "signed_error", False),
    ]:
        rid = diagnosis.sort([col, "row_id"], descending=[descending, False])["row_id"][
            0
        ]
        chosen.setdefault(rid, []).append(label)
    normal = diagnosis.filter(pl.col("medical_applied")).with_columns(
        pl.col("signed_error").abs().alias("absolute_error")
    )
    rid = normal.sort(["absolute_error", "row_id"])["row_id"][0]
    chosen.setdefault(rid, []).append("ordinary applied case")
    minor = q.filter(
        (pl.col("origin_year") == 2024) & (pl.col("stage") == "Lower minors")
    ).sort("row_id")
    assert len(minor)
    chosen.setdefault(minor["row_id"][0], []).append(
        "outcome-blind lower-minor fallback control"
    )
    PUBLIC.mkdir(parents=True)
    save(
        PUBLIC / "case-selection.json",
        dict(
            cases=[dict(row_id=k, rules=v) for k, v in chosen.items()],
            profile_peers="same origin, current/gap; nearest age/5, best recent workload and last quality; no future outcomes",
        ),
    )
    save(
        PUBLIC / "report.json",
        dict(
            scores=scores,
            origins=origins,
            group_scores=group_scores,
            paired_intervals=paired,
            predictive_gates=gates,
            predictive_gates_pass=all(gates.values()),
            applied_rows=int(q["medical_applied"].sum()),
            eligible_rows=len(eligible),
            total_rows=len(q),
            new_heads=fit["new_heads"],
            player_walkthrough_status="pending",
            deployment_approved=False,
            protected_2026_outcomes_used=False,
            hashes={
                str(p): sha256_file(p)
                for p in [
                    OUT / "fit-report.json",
                    OUT / "preflight.json",
                    OUT / "predictions.parquet",
                    PUBLIC / "case-selection.json",
                ]
            },
        ),
    )
    protections()
    print(
        f"Scores provisional: eligible PA RMSE {anchor['pa_rmse']:.3f} -> {candidate['pa_rmse']:.3f}; walkthrough required",
        flush=True,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("phase", choices=["prepare", "fit", "score"])
    {"prepare": prepare, "fit": fit, "score": score}[p.parse_args().phase]()
