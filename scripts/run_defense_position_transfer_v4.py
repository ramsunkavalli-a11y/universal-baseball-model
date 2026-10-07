"""Prepare a locked related-position comparison; fit only after source preflight."""
from collections import defaultdict
import argparse
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball import defense_native_range as base
from universal_baseball import defense_position_transfer as transfer
from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections
from audit_defensive_talent_support import verify

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reports/generated/defense-native-range-v3"
OUT = ROOT / "reports/generated/defense-position-transfer-v4"
PUBLIC = ROOT / "reports/model-evidence/defense-position-transfer-v4"
FIXED = ((608671,7), (608701,7), (571771,6), (622761,4), (605141,4),
         (677951,6), (595281,8))


def read(p):
    return json.loads(p.read_text(encoding="utf8"))


def write(name, value):
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / name
    assert not p.exists(), f"Preserve existing evidence: {p}"
    p.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf8", newline="\n")
    return p


def key(r):
    return r["origin_year"], r["player_id"], r["position"]


def peers(rows, r):
    pool = [p for p in rows if p["origin_year"] == r["origin_year"]
            and p["position"] == r["position"] and p["player_id"] != r["player_id"]]
    pool.sort(key=lambda p:(abs((p["age"] or 27) - (r["age"] or 27)),
                            abs(p["history_outs"] - r["history_outs"]),
                            abs(p["other_outs"] - r["other_outs"]),p["player_id"]))
    return pool[:3]


def prepare():
    protected = protections()
    anchor_review = read(SOURCE / "final-review.json")
    assert anchor_review["player_walkthrough_status"] == "complete"
    verify(read(SOURCE / "source-review.json")["hashes"])
    verify(read(SOURCE / "report.json")["hashes"])
    ledger = pl.read_parquet(SOURCE / "component-ledger.parquet").to_dicts()
    native = defaultdict(list)
    for r in ledger:
        native[r["player_id"]].append(r)
    rows = []
    for r in pl.read_parquet(SOURCE / "predictions.parquet").to_dicts():
        h, _ = transfer.other_history(native[r["player_id"]],r["origin_year"],r["position"])
        rows.append({**r, **h})
    assert len(rows) == 13402 and len({key(r) for r in rows}) == len(rows)
    OUT.mkdir(parents=True,exist_ok=True)
    assert not (OUT / "features.parquet").exists()
    pl.DataFrame(rows,infer_schema_length=None).write_parquet(OUT / "features.parquet")
    walks = []
    missing = []
    def describe(r):
        history = [s for s in native[r["player_id"]]
                   if r["origin_year"] - 2 <= s["season"] <= r["origin_year"]]
        # Source-stage artifact deliberately omits future quality/outcome paths.
        return dict(identity=list(key(r)), name=r["player_name"], age=r["age"],
                    same_history={c:r[c] for c in ("history_outs","history_runs","history_rate","reliability")},
                    other_history={c:r[c] for c in ("other_outs","other_runs","other_rate","other_reliability","other_pivot_share","other_invalid_outs")},
                    dated_sources=history, actual_inputs=transfer.features(r))
    for pid,pos in FIXED:
        r = next((s for s in rows if key(s) == (2022,pid,pos)),None)
        if r is None:
            missing.append(dict(player_id=pid,position=pos,origin=2022))
            continue
        walks.append(dict(primary=describe(r),peers=[describe(p) for p in peers(rows,r)]))
    walk_path = write("source-player-walkthrough.json",dict(cases=walks,missing_fixed_cases=missing,
                      selection="Fixed cases; peers same origin/position, nearest age then own/other sample and ID; no future selection",
                      source_only=True,player_walkthrough_status="complete"))
    checks = []
    for origin in sorted({r["origin_year"] for r in rows}):
        for fold in range(5):
            tr = [r for r in rows if r["quality_rate"] is not None and r["window_end"] <= origin
                  and r["origin_year"] < origin and r["player_id"] % 5 != fold]
            te = [r for r in rows if r["origin_year"] == origin and r["player_id"] % 5 == fold]
            check, _ = transfer.preflight(tr,te,origin,fold)
            checks.append(check)
    files = [SOURCE / "predictions.parquet",SOURCE / "component-ledger.parquet",SOURCE / "final-review.json",
             OUT / "features.parquet",walk_path,ROOT / "docs/defense-position-transfer-v4-contract.md",
             ROOT / "src/universal_baseball/defense_position_transfer.py",Path(__file__)]
    write("preflight.json",dict(before_fitting=True,source_walkthrough_status="complete",checks=checks,
          all_predictions_retained=len(rows),no_2026_outcomes=True,protections=protected,
          feature_names=list(transfer.FEATURES),hashes={str(p):sha256_file(p) for p in files}))
    for c in walks:
        p=c["primary"]
        print(json.dumps(dict(name=p["name"],identity=p["identity"],same=p["same_history"],other=p["other_history"])))
    print("Prepared all source walks and 40 chronological support checks; no fits.")


def group(rows):
    return dict(scores={a:base.score(rows,a) for a in ("neutral","history","calibrated","transfer")},
                transfer_minus_calibrated=base.paired_interval(rows,"transfer","calibrated"),
                sparse_transfer_rows=sum(r["transfer_profile_people"] < 20 for r in rows),
                sparse_own_rows=sum(r["profile_people"] < 20 for r in rows))


def run():
    pre = read(OUT / "preflight.json")
    assert pre["before_fitting"] and pre["source_walkthrough_status"] == "complete"
    verify(pre["hashes"])
    assert pre["protections"] == protections() and not (OUT / "report.json").exists()
    rows = pl.read_parquet(OUT / "features.parquet").to_dicts()
    models, predictions = [], []
    for check in pre["checks"]:
        year,fold = check["origin"],check["fold"]
        tr = [r for r in rows if r["quality_rate"] is not None and r["window_end"] <= year
              and r["origin_year"] < year and r["player_id"] % 5 != fold]
        te = [r for r in rows if r["origin_year"] == year and r["player_id"] % 5 == fold]
        replay,counts = transfer.preflight(tr,te,year,fold)
        assert replay == check
        m = transfer.fit(tr,check["disabled_features"]) if check["fit_allowed"] else None
        pred = transfer.predict(m,te) if m else np.array([r["history_rate"] for r in te])
        outside = ((transfer.matrix(te,m["disabled"]) < transfer.matrix(tr,m["disabled"]).min(0)) |
                   (transfer.matrix(te,m["disabled"]) > transfer.matrix(tr,m["disabled"]).max(0))).sum(1) if m else [None]*len(te)
        models.append(dict(origin=year,fold=fold,model=m))
        for r,p,n,e in zip(te,pred,counts,outside):
            predictions.append({**r,"transfer":float(p),"transfer_profile_people":n,
                                "transfer_features_outside_range":None if e is None else int(e)})
    assert len(predictions) == len(rows) and {key(r) for r in predictions} == {key(r) for r in rows}
    assert not (OUT / "predictions.parquet").exists()
    pl.DataFrame(predictions,infer_schema_length=None).write_parquet(OUT / "predictions.parquet")
    write("models.json",dict(models=models))
    measured = [r for r in predictions if r["quality_rate"] is not None]
    primary = [r for r in measured if r["origin_year"] >= 2022]
    result = dict(disposition="provisional until player walkthrough",player_walkthrough_status="pending",
                  primary=group(primary),by_origin={str(y):group([r for r in measured if r["origin_year"]==y])
                    for y in sorted({r["origin_year"] for r in measured})},
                  by_position={str(p):group([r for r in primary if r["position"]==p]) for p in range(3,10)},
                  by_profile={},all_predicted_rows=len(predictions),protections=pre["protections"],
                  full_value_forecast=False,deployment_approved=False,
                  hashes={str(p):sha256_file(p) for p in (OUT/"predictions.parquet",OUT/"models.json",OUT/"preflight.json")})
    profiles = dict(thin_target_other_sample=lambda r:r["history_outs"] <1500 and r["other_outs"]>=300,
                    no_related_history=lambda r:r["other_outs"]==0,
                    strong_target_history=lambda r:r["history_outs"]>=4500,
                    young=lambda r:r["age"] is not None and r["age"]<=24,
                    age30plus=lambda r:r["age"] is not None and r["age"]>=30)
    for name,predicate in profiles.items():
        result["by_profile"][name] = group([r for r in primary if predicate(r)])
    write("report.json",result)
    print(json.dumps(dict(primary=result["primary"],profiles=result["by_profile"]),indent=2))


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("stage",choices=("prepare","fit"))
    args=parser.parse_args()
    prepare() if args.stage=="prepare" else run()
