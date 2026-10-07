"""Trace gains, losses, origin-only peers and exact component calculations."""
from collections import defaultdict
import json
import math

import numpy as np
import polars as pl

from build_defense_native_range_v3 import OUT, ROOT, write, FIXED_NAMES
from audit_defensive_talent_support import verify
from run_hitter_finite_return_baseline import protections
from universal_baseball.defense_native_range import FEATURES, history, features, predict, matrix, score, paired_interval
from universal_baseball.storage import sha256_file


def main():
    protections()
    report = json.loads((OUT / "report.json").read_text(encoding="utf8"))
    verify(report["hashes"])
    assert report["player_walkthrough_status"] == "pending"
    assert not (OUT / "player-walkthrough.json").exists()
    rows = pl.read_parquet(OUT / "predictions.parquet").to_dicts()
    ledger = pl.read_parquet(OUT / "component-ledger.parquet").to_dicts()
    native = defaultdict(list)
    for r in ledger:
        native[r["player_id"]].append(r)
    models = {(r["origin"],r["fold"]):r["model"] for r in json.loads((OUT / "models.json").read_text())["models"]}
    primary = [r for r in rows if r["origin_year"] >= 2022 and r["quality_rate"] is not None]
    selected = defaultdict(list)
    key = lambda r:(r["origin_year"],r["player_id"],r["position"])
    for token in FIXED_NAMES:
        matches = [r for r in rows if token.lower() in r["player_name"].lower() and r["origin_year"] == 2022]
        for pid in sorted({r["player_id"] for r in matches}):
            r = max([x for x in matches if x["player_id"] ==pid],key=lambda x:x["history_outs"])
            selected[key(r)].append("fixed: "+token)
    gain = lambda r:abs(r["history"]-r["quality_rate"]) - abs(r["calibrated"]-r["quality_rate"])
    for name,r in [("largest gain",max(primary,key=gain)), ("largest deterioration",min(primary,key=gain)),
                   ("false high",max(primary,key=lambda r:r["calibrated"]-r["quality_rate"])),
                   ("false low",min(primary,key=lambda r:r["calibrated"]-r["quality_rate"])),
                   ("ordinary median error",sorted(primary,key=lambda r:abs(r["calibrated"]-r["quality_rate"]))[len(primary)//2])]:
        selected[key(r)].append(name)
    cases = []
    for k,reasons in sorted(selected.items()):
        r = next(x for x in rows if key(x)==k)
        year,pid,pos = k
        h,past = history(native[pid],year,pos)
        assert all(math.isclose(h[c],r[c],abs_tol=1e-10) for c in h)
        weighted = [{**s,"recency_weight":.5**(year-s["season"]),
                     "weighted_outs":s["native_outs"]*.5**(year-s["season"]),
                     "weighted_range_runs":s["range_runs"]*.5**(year-s["season"])} for s in past]
        inputs = features(r)
        m = models[year,r["fold"]]
        if m:
            z = (matrix([r])[0]-m["mean"])/m["scale"]
            contributions = dict(zip(FEATURES,(z*np.array(m["coef"])).tolist()))
            assert math.isclose(m["intercept"]+sum(contributions.values()),r["calibrated"],abs_tol=1e-10)
            # Fixed-fit explanation only, not a causal/validated alternative.
            zero_history = {**r,"history_rate":0.}
            probe = float(predict(m,[zero_history])[0])
        else:
            contributions = {}
            probe = None
        path = [s for s in native[pid] if year<s["season"]<=r["window_end"]]
        same = [s for s in path if s["position"]==pos and s["range_valid"]]
        if r["quality_rate"] is not None:
            assert len(same)>=2 and sum(s["native_outs"] for s in same)>=1500
            assert math.isclose(1500*sum(s["range_runs"] for s in same)/sum(s["native_outs"] for s in same),r["quality_rate"],abs_tol=1e-10)
        peers = [s for s in rows if s["origin_year"]==year and s["position"]==pos and s["player_id"]!=pid]
        peers.sort(key=lambda s:(abs((s["age"] or 27)-(r["age"] or 27)),abs(s["history_outs"]-r["history_outs"]),s["player_id"]))
        peer_traces = []
        for p in peers[:3]:
            ph,pp = history(native[p["player_id"]],year,pos)
            peer_traces.append(dict(origin=p, history=ph, dated_sources=pp,
                                    future_path=[s for s in native[p["player_id"]] if year<s["season"]<=p["window_end"]]))
        cases.append(dict(selection=reasons, forecast=r, weighted_origin_history=weighted,
                          other_origin_positions=[s for s in native[pid] if year-2<=s["season"]<=year and s["position"]!=pos],
                          model_inputs=inputs, fitted_intercept=m["intercept"] if m else None,
                          fitted_contributions=contributions,
                          zero_history_fixed_fit_probe=probe,
                          probe_scope="sets history and derived history×reliability together; explanatory, artificial combination, not causal or an approved projection",
                          future_annual_path=path, peers=peer_traces))
    write("player-walkthrough.json",dict(selection="fixed named cases plus outcome-selected diagnostic extremes/median; exact manifest persisted; peers same origin/position, nearest age then exposure then ID without future selection",
                                          cases=cases, player_walkthrough_status="complete",
                                          units="native range runs per 500 defensive innings, fixed three-calendar-year future pool",
                                          no_downstream_war_or_arrival_forecast=True))
    # Review the actual mechanics and matched results; no automatic adoption.
    write("review-checks.json",dict(cases=len(cases), people=len({c["forecast"]["player_id"] for c in cases}),
                                    all_case_histories_reconstructed=True,
                                    all_case_predictions_replayed=True, future_paths_reconstructed=True,
                                    origin_only_peer_selection=True,
                                    unknown_quality_peers=sum(p["origin"]["quality_rate"] is None for c in cases for p in c["peers"]),
                                    primary_measured_people=report["primary"]["scores"]["history"]["people"],
                                    hash=sha256_file(OUT/"player-walkthrough.json")))
    for c in cases:
        r=c["forecast"]
        print(json.dumps(dict(name=r["player_name"],pid=r["player_id"],pos=r["position"],origin=r["origin_year"],
                              selections=c["selection"],history=r["history"],calibrated=r["calibrated"],actual=r["quality_rate"],
                              age=r["age"],exposure=r["history_outs"],support=r["profile_people"],
                              contributions=c["fitted_contributions"],probe=c["zero_history_fixed_fit_probe"])))


if __name__ == "__main__":
    main()
