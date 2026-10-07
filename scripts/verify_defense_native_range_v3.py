"""Independently replay native histories, ridge solves, scores and review gates."""
from collections import Counter, defaultdict
import json
import math
from pathlib import Path

import numpy as np
import polars as pl

from build_defense_native_range_v3 import ROOT, OUT, SOURCE, write
from audit_defensive_talent_support import verify
from run_hitter_finite_return_baseline import protections
from source_defensive_positions_v2 import embedded
from universal_baseball.defense_native_range import FEATURES, matrix, profile, paired_interval
from universal_baseball.storage import sha256_file


def close(a,b):
    assert math.isclose(float(a),float(b),abs_tol=1e-9,rel_tol=1e-9), (a,b)


def main():
    protected = protections()
    source = json.loads((OUT/"source-review.json").read_text(encoding="utf8"))
    report = json.loads((OUT/"report.json").read_text(encoding="utf8"))
    pre = json.loads((OUT/"fit-preflight.json").read_text(encoding="utf8"))
    repair = json.loads((OUT/"execution-repair.json").read_text(encoding="utf8"))
    for hashes in (source["hashes"],report["hashes"]):
        verify(hashes)
    for p,h in pre["hashes"].items():
        if p.endswith("fit_defense_native_range_v3.py"):
            assert sha256_file(OUT/"fit-runner-initial.py")==h==repair["initial_runner_sha256"]
            assert sha256_file(Path(p))==repair["corrected_runner_sha256"]
        else:
            assert sha256_file(Path(p))==h
    assert pre["protections"]==report["protections"]==source["protections"]==protected
    rows = pl.read_parquet(OUT/"predictions.parquet").to_dicts()
    labels = pl.read_parquet(OUT/"labels.parquet").to_dicts()
    ledger = pl.read_parquet(OUT/"component-ledger.parquet").to_dicts()
    raw = {}
    for y in range(2016,2026):
        for r in embedded((SOURCE/f"position-{y}.response").read_text(encoding="utf8"),"data"):
            raw[y,r["id"],r["pos_id"]]=r
    native = defaultdict(list)
    for r in ledger:
        rr = raw[r["season"],r["player_id"],r["position"]]
        assert r["native_outs"]==rr["outs_total"] and r["range_runs"]==rr["range_runs"]
        native[r["player_id"]].append(r)
    for r in labels:
        n=runs=0.
        for s in native[r["player_id"]]:
            if r["origin_year"]-2<=s["season"]<=r["origin_year"] and s["position"]==r["position"] and s["range_valid"]:
                w=2**(s["season"]-r["origin_year"])
                n+=s["native_outs"]*w
                runs+=s["range_runs"]*w
        close(n,r["history_outs"]);close(runs,r["history_runs"])
        close(1500*runs/(3000+n),r["history_rate"])
        if r["quality_rate"] is not None:
            p=[s for s in native[r["player_id"]] if r["origin_year"]<s["season"]<=r["window_end"] and s["position"]==r["position"] and s["range_valid"]]
            assert len(p)>=2 and r["window_end"]<=2025 and r["unmeasured_official_outs"]==0
            close(sum(s["native_outs"] for s in p),r["future_outs"])
            close(sum(s["range_runs"] for s in p),r["future_runs"])
            close(1500*sum(s["range_runs"] for s in p)/sum(s["native_outs"] for s in p),r["quality_rate"])
    models = {(r["origin"],r["fold"]):r["model"] for r in json.loads((OUT/"models.json").read_text())["models"]}
    fitted_count=0
    for c in pre["checks"]:
        year,fold=c["origin"],c["fold"]
        train=[r for r in labels if r["quality_rate"] is not None and r["window_end"]<=year and r["origin_year"]<year and r["player_id"]%5!=fold]
        test=[r for r in rows if r["origin_year"]==year and r["fold"]==fold]
        assert c["train_keys"]==[[r["origin_year"],r["player_id"],r["position"]] for r in train]
        assert set(map(tuple,c["test_keys"]))=={(r["origin_year"],r["player_id"],r["position"]) for r in test}
        assert {r["player_id"] for r in train}.isdisjoint(r["player_id"] for r in test)
        assert c["training_people"]==len({r["player_id"] for r in train})
        support=defaultdict(set)
        for r in train:
            support[profile(r)].add(r["player_id"])
        for r in test:
            assert r["profile_people"]==len(support[profile(r)])
        m=models[year,fold]
        if m is None:
            assert not c["fit_allowed"]
            for r in test:
                close(r["calibrated"],r["history_rate"])
            continue
        assert c["fit_allowed"]
        x=matrix(train); y=np.array([r["quality_rate"] for r in train])
        counts=Counter(r["player_id"] for r in train)
        w=np.array([1/counts[r["player_id"]] for r in train])
        mean=np.average(x,axis=0,weights=w)
        sd=np.sqrt(np.average((x-mean)**2,axis=0,weights=w));sd[sd<1e-10]=1
        z=(x-mean)/sd; intercept=float(np.average(y,weights=w))
        # Independent augmented least-squares solve, not the runner normal equations.
        beta=np.linalg.lstsq(np.vstack([np.sqrt(w)[:,None]*z,np.sqrt(10)*np.eye(len(FEATURES))]),
                             np.concatenate([np.sqrt(w)*(y-intercept),np.zeros(len(FEATURES))]),rcond=None)[0]
        assert np.allclose(beta,m["coef"],atol=1e-10)
        assert np.allclose(mean,m["mean"]) and np.allclose(sd,m["scale"])
        pp=intercept+(matrix(test)-mean)/sd@beta
        for r,v in zip(test,pp):
            close(r["calibrated"],v)
        fitted_count+=1
    primary=[r for r in rows if r["origin_year"]>=2022 and r["quality_rate"] is not None]
    for name,subset in [("primary",primary),*[(str(y),[r for r in rows if r["origin_year"]==y and r["quality_rate"] is not None]) for y in range(2016,2023) if str(y) in report["by_origin"]]]:
        target=report["primary"] if name=="primary" else report["by_origin"][name]
        counts=Counter(r["player_id"] for r in subset)
        w=np.array([1/counts[r["player_id"]] for r in subset])
        for arm in ("neutral","history","calibrated"):
            error=np.array([r[arm]-r["quality_rate"] for r in subset])
            close(np.sqrt(np.average(error**2,weights=w)),target["scores"][arm]["rmse"])
            close(np.average(error,weights=w),target["scores"][arm]["bias"])
        for name_interval,left,right in [("calibrated_minus_history","calibrated","history"),("history_minus_neutral","history","neutral"),("calibrated_minus_neutral","calibrated","neutral")]:
            assert paired_interval(subset,left,right)==target[name_interval]
    walk=json.loads((OUT/"player-walkthrough.json").read_text(encoding="utf8"))
    review=json.loads((OUT/"review-checks.json").read_text(encoding="utf8"))
    assert walk["player_walkthrough_status"]=="complete" and review["hash"]==sha256_file(OUT/"player-walkthrough.json")
    # A pooled multi-year measurement can still be dominated by one season.
    concentrated=[]
    for r in primary:
        n=max(s["native_outs"] for s in native[r["player_id"]] if r["origin_year"]<s["season"]<=r["window_end"] and s["position"]==r["position"] and s["range_valid"])
        if n/r["future_outs"]>.8:
            concentrated.append(dict(player_id=r["player_id"],position=r["position"],share=n/r["future_outs"]))
    data=dict(execution_integrity="pass", predictions_replayed=len(rows), source_rows_replayed=len(ledger),
              quality_histories_replayed=len(labels), independent_ridge_solves=fitted_count,
              person_bootstrap_intervals_replayed=True, player_walkthrough_status="complete",
              primary_concentrated_measurements=concentrated,
              profile_support="qualified: 221/317 primary positions have fewer than 20 detailed-profile training people",
              predictive_result="MLB range history and calibrated history beat neutral; calibrated improves history in 2022, not every group",
              reasonability="qualified: sparse young/development and multi-position cases still missed",
              disposition="retain research range baselines; defense integration and other components remain open",
              deployment_approved=False, protections=protected,
              hashes={str(p):sha256_file(p) for p in [OUT/"player-walkthrough.json",OUT/"review-checks.json",
                                                     ROOT/"scripts/verify_defense_native_range_v3.py"]})
    assert not (OUT/"final-review.json").exists()
    write("final-review.json",data)
    print(json.dumps({k:v for k,v in data.items() if k not in ('hashes','protections','primary_concentrated_measurements')},indent=2))
    print('concentrated measurements',len(concentrated))


if __name__ == "__main__":
    main()
