"""Independent replay and player traces before disposing of the fixed comparison."""

import argparse
from pathlib import Path

import joblib
import numpy as np
import polars as pl
from sklearn.metrics import mean_squared_error, brier_score_loss, log_loss
from threadpoolctl import threadpool_limits

import test_repaired_medical_opportunity as run
from universal_baseball.medical_opportunity_comparison import (
    OLD,
    NEW,
    RANGE,
    frame,
    support,
)
from universal_baseball.storage import sha256_file


def walk():
    target = run.PUBLIC / "player-walks.json"
    assert not target.exists()
    pre, fit = (
        run.read(run.OUT / "preflight.json"),
        run.read(run.OUT / "fit-report.json"),
    )
    report = run.read(run.PUBLIC / "report.json")
    run.verify(pre["hashes"])
    run.verify(fit["model_hashes"])
    run.verify(report["hashes"])
    run.protections()
    q = pl.read_parquet(run.OUT / "predictions.parquet").sort("row_id")
    anchor = pl.read_parquet(run.BASE / "predictions.parquet").sort("row_id")
    assert q.select(anchor.columns).equals(anchor)
    frames = {k: pl.read_parquet(run.OUT / f"features-{k}.parquet") for k in range(5)}
    models = {}
    replayed = 0
    with threadpool_limits(limits=2):
        for c in fit["cells"]:
            f = frames[c["fold"]]
            ids = next(
                p["test_row_ids"]
                for p in pre["cells"]
                if p["year"] == c["origin"] and p["fold"] == c["fold"]
            )
            te = f.filter(pl.col("row_id").is_in(ids) & pl.col("med_eligible")).sort(
                "row_id"
            )
            g = q.filter(pl.col("row_id").is_in(te["row_id"].to_list())).sort("row_id")
            for h in c["heads"]:
                m = joblib.load(h["path"])
                names = pre["features"][h["arm"]]
                x = te.select(names).to_numpy()
                v = (
                    m.predict_proba(x)[:, 1]
                    if h["head"] == "participation"
                    else m.predict(x)
                )
                col = h["arm"] + (
                    "_raw_p" if h["head"] == "participation" else "_raw_conditional_pa"
                )
                assert np.allclose(v, g[col].to_numpy(), atol=1e-10, rtol=0)
                models[(c["origin"], c["fold"], h["arm"], h["head"])] = m
                replayed += 1
    assert replayed == fit["new_heads"] == 120
    fallback = q.filter(~pl.col("medical_applied"))
    for arm in run.ARMS:
        for n in ["p", "conditional_pa", "pa", "value"]:
            assert np.array_equal(
                fallback[arm + "_" + n].to_numpy(),
                fallback["observation_" + n].to_numpy(),
            )
    eligible = q.filter(pl.col("med_eligible"))
    independent = {}
    for arm in ["observation", *run.ARMS]:
        mse = []
        brier = []
        ll = []
        vse = []
        for g in eligible.partition_by("origin_year"):
            mse.append(mean_squared_error(g["next_pa"], g[arm + "_pa"]))
            brier.append(brier_score_loss(g["next_pa"].to_numpy() > 0, g[arm + "_p"]))
            ll.append(
                log_loss(
                    g["next_pa"].to_numpy() > 0,
                    np.column_stack(
                        [1 - g[arm + "_p"].to_numpy(), g[arm + "_p"].to_numpy()]
                    ),
                    labels=[False, True],
                )
            )
            vse.append(
                mean_squared_error(g["actual_relative_value"], g[arm + "_value"])
            )
        independent[arm] = dict(
            pa_mse=float(np.mean(mse)),
            brier=float(np.mean(brier)),
            logloss=float(np.mean(ll)),
            value_mse=float(np.mean(vse)),
        )
        for metric, v in independent[arm].items():
            assert abs(v - report["scores"]["eligible"][arm][metric]) < 1e-9
    obs = pl.read_parquet(run.SOURCE / "model-observations.parquet")
    spells = run.read(run.SOURCE / "reconstructed-spells.json")["origins"]
    stats = pl.read_parquet(run.GEN / "practical-hitter-v31/dated-stints.parquet")
    walks = []
    for picked in run.read(run.PUBLIC / "case-selection.json")["cases"]:
        rid = picked["row_id"]
        r = q.filter(pl.col("row_id") == rid).row(0, named=True)
        y, k, pid = r["origin_year"], r["outer_fold"], r["player_id"]
        f = frames[k]
        actual = f.filter(pl.col("row_id") == rid)
        a = actual.row(0, named=True)
        old = pl.read_parquet(run.BASE / f"features-{k}.parquet").filter(
            pl.col("row_id") == rid
        )
        rebuilt = frame(old, obs.filter(pl.col("row_id") == rid)).select(actual.columns)
        # Polars SIMD batch division versus scalar replay can differ by one ULP.
        # Only this derived support scale gets tolerance; original data and the
        # source counts/states and actual modeled predictors remain exact.
        assert rebuilt.drop("med_best_recent_work").equals(
            actual.drop("med_best_recent_work")
        )
        assert np.allclose(
            rebuilt["med_best_recent_work"].to_numpy(),
            actual["med_best_recent_work"].to_numpy(),
            atol=1e-12,
            rtol=0,
        )
        cell = next(c for c in pre["cells"] if c["year"] == y and c["fold"] == k)
        tr = f.filter(
            pl.col("row_id").is_in(cell["training_row_ids"]) & pl.col("med_eligible")
        )
        changed = actual.with_columns((pl.col("next_pa") + 777).alias("next_pa"))
        assert support(tr, actual).equals(support(tr, changed))
        assert changed["med_eligible"].equals(actual["med_eligible"])
        for arm in run.ARMS:
            assert np.array_equal(
                changed.select(pre["features"][arm]).to_numpy(),
                actual.select(pre["features"][arm]).to_numpy(),
            )
        pool = f.filter(
            pl.col("row_id").is_in(q["row_id"].to_list())
            & (pl.col("origin_year") == y)
            & (pl.col("med_current") == a["med_current"])
            & (pl.col("player_id") != pid)
        )
        pool = pool.with_columns(
            (
                (pl.col("age") - a["age"]) ** 2 / 25
                + 4 * (pl.col("med_best_recent_work") - a["med_best_recent_work"]) ** 2
                + (pl.col("last_MLB_quality") - a["last_MLB_quality"]) ** 2
            ).alias("distance")
        )
        peers = pool.sort(["distance", "player_id"]).head(3)
        comparison = []
        for peer in peers.to_dicts():
            prediction = q.filter(pl.col("row_id") == peer["row_id"]).row(0, named=True)
            comparison.append(
                dict(
                    player_id=peer["player_id"],
                    name=prediction["player_name"],
                    row_id=peer["row_id"],
                    age=peer["age"],
                    last_MLB_quality=peer["last_MLB_quality"],
                    best_recent_normalized_MLB_PA=peer["med_best_recent_work"] * 600,
                    observation_state=peer["observation_state"],
                    medical_gate_reason=prediction["medical_gate_reason"],
                    anchor_pa=prediction["observation_pa"],
                    candidate_pa=prediction["repaired_pa"],
                    actual_pa=prediction["next_pa"],
                )
            )
        probes = []
        if cell["fit_allowed"] and a["med_eligible"]:
            borrowed = peers.row(0, named=True)
            source_swap = actual.with_columns(
                [pl.lit(borrowed[n]).alias(n) for n in NEW]
            )
            for head in ["participation", "conditional_pa"]:
                m = models[(y, k, "repaired", head)]
                names = pre["features"]["repaired"]
                x = actual.select(names).to_numpy()
                z = source_swap.select(names).to_numpy()

                def pred(t):
                    return float(
                        m.predict_proba(t)[0, 1]
                        if head == "participation"
                        else m.predict(t)[0]
                    )

                # Tree split counts identify usage, not causal importance or contribution.
                splits = {n: 0 for n in NEW}
                for trees in m._predictors:
                    for tree in trees:
                        for index in tree.nodes["feature_idx"][
                            ~tree.nodes["is_leaf"].astype(bool)
                        ]:
                            name = names[int(index)]
                            if name in splits:
                                splits[name] += 1
                probes.append(
                    dict(
                        head=head,
                        actual_raw_prediction=pred(x),
                        peer_medical_input_prediction=pred(z),
                        peer_id=borrowed["player_id"],
                        actual_medical_inputs={n: a[n] for n in NEW},
                        swapped_medical_inputs={n: borrowed[n] for n in NEW},
                        medical_feature_splits=splits,
                        diagnostic_only=True,
                        changes_common_history=False,
                        forecast_substituted=False,
                        clinical_or_causal_interpretation=False,
                    )
                )
        limits = []
        for head, sub in [
            ("participation", tr),
            ("conditional_pa", tr.filter(pl.col("next_pa") > 0)),
        ]:
            limits.append(
                dict(
                    head=head,
                    training_rows=len(sub),
                    training_people=sub["player_id"].n_unique(),
                    support=support(sub, actual).to_dicts(),
                    ranges={
                        n: dict(actual=a[n], min=sub[n].min(), max=sub[n].max())
                        for n in RANGE
                    },
                )
            )
        predictions = {
            arm: {n: r[arm + "_" + n] for n in ["p", "conditional_pa", "pa", "value"]}
            for arm in ["observation", *run.ARMS]
        }
        walks.append(
            dict(
                row_id=rid,
                player_id=pid,
                name=r["player_name"],
                origin=y,
                fold=k,
                selection_rules=picked["rules"],
                information_date=a["ctx_information_date"],
                age=a["age"],
                stage=a["stage"],
                source_addition=r["source_addition"],
                stats=stats.filter(
                    (pl.col("player_id") == pid) & pl.col("season").is_between(y - 2, y)
                )
                .select(
                    "season",
                    "bucket",
                    "plate_appearances",
                    "home_runs",
                    "strike_outs",
                    "base_on_balls",
                )
                .to_dicts(),
                source_summary=obs.filter(pl.col("row_id") == rid).to_dicts(),
                rebuilt_source=spells.get(f"{y}:{pid}"),
                original_medical_inputs={n: a[n] for n in OLD},
                new_medical_inputs={n: a[n] for n in NEW},
                job_inputs={
                    arm: {n: a[n] for n in pre["features"][arm]} for arm in run.ARMS
                },
                medically_eligible=a["med_eligible"],
                applied=r["medical_applied"],
                gate_reason=r["medical_gate_reason"],
                raw_model_available=r["raw_model_available"],
                raw_heads={
                    arm: dict(
                        p=r[arm + "_raw_p"],
                        conditional_pa=r[arm + "_raw_conditional_pa"],
                    )
                    for arm in run.ARMS
                },
                predictions=predictions,
                unchanged_batting_rate_per600=r["observation_rate"],
                origin_replacement_per_PA=r["origin_replacement_rate"],
                actual=dict(
                    PA=r["next_pa"], batting_plus_replacement=r["actual_relative_value"]
                ),
                support=limits,
                peers=comparison,
                peer_rule="same origin and current/gap; distance age/5, best recent PA/300, last MLB quality; no outcomes",
                fixed_model_probes=probes,
                future_outcome_mutation_invariant=True,
                input_reconstruction_verified=True,
                clinical_recovery_certified=False,
            )
        )
    run.save(
        target,
        dict(
            cases=walks,
            replayed_heads=replayed,
            independent_scores=independent,
            unchanged_anchor_all_rows=True,
            exact_fallback_verified=True,
            player_walkthrough_status="pending_judgment",
            hashes={
                str(p): sha256_file(p)
                for p in [
                    Path(__file__),
                    run.PUBLIC / "report.json",
                    run.PUBLIC / "case-selection.json",
                    run.OUT / "predictions.parquet",
                ]
            },
        ),
    )
    run.protections()
    print(
        f"All 120 heads replayed and {len(walks)} player histories traced; judgment pending",
        flush=True,
    )


def finalize():
    pre = run.read(run.OUT / "preflight.json")
    run.verify(pre["hashes"])
    report = run.read(run.PUBLIC / "report.json")
    run.verify(report["hashes"])
    walks = run.read(run.PUBLIC / "player-walks.json")
    run.verify(walks["hashes"])
    doc = run.ROOT / "docs/hitter-medical-opportunity-comparison-result.md"
    assert "Walkthrough status: complete" in doc.read_text(encoding="utf8")
    assert all(
        c["future_outcome_mutation_invariant"]
        and c["input_reconstruction_verified"]
        and len(c["peers"]) == 3
        and c["stats"]
        for c in walks["cases"]
    )
    run.protections()
    run.save(
        run.PUBLIC / "completion.json",
        dict(
            player_walkthrough_status="complete",
            execution_integrity_pass=True,
            predictive_gates_pass=report["predictive_gates_pass"],
            disposition="development_candidate_not_approved",
            deployment_approved=False,
            forecasts_promoted=False,
            clinical_recovery_validated=False,
            protected_2026_outcomes_used=False,
            hashes={
                str(p): sha256_file(p)
                for p in [
                    doc,
                    run.PUBLIC / "report.json",
                    run.PUBLIC / "player-walks.json",
                    Path(__file__),
                ]
            },
        ),
    )
    print(
        "Comparison reviewed; no promotion and no clinical probability claim",
        flush=True,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("phase", choices=["walk", "finalize"])
    {"walk": walk, "finalize": finalize}[p.parse_args().phase]()
