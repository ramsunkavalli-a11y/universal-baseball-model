"""Mandatory fitted player and peer review of the related-position contrast."""
from collections import defaultdict
import math

import numpy as np
import polars as pl

from run_defense_position_transfer_v4 import ROOT, SOURCE, OUT, FIXED, read, write, key, peers
from universal_baseball import defense_position_transfer as transfer
from universal_baseball.storage import sha256_file
from audit_defensive_talent_support import verify
from run_hitter_finite_return_baseline import protections


def main():
    report=read(OUT/"report.json")
    verify(report["hashes"])
    assert report["player_walkthrough_status"]=="pending" and report["protections"]==protections()
    rows=pl.read_parquet(OUT/"predictions.parquet").to_dicts()
    native=defaultdict(list)
    for r in pl.read_parquet(SOURCE/"component-ledger.parquet").to_dicts():
        native[r["player_id"]].append(r)
    models={(m["origin"],m["fold"]):m["model"] for m in read(OUT/"models.json")["models"]}
    selected=defaultdict(list)
    for pid,pos in FIXED:
        r=next((s for s in rows if key(s)==(2022,pid,pos)),None)
        if r:
            selected[key(r)].append("fixed diagnostic")
    primary=[r for r in rows if r["origin_year"]==2022 and r["quality_rate"] is not None]
    gain=lambda r:abs(r["calibrated"]-r["quality_rate"])-abs(r["transfer"]-r["quality_rate"])
    chosen=[("largest gain",max(primary,key=gain)),("largest deterioration",min(primary,key=gain)),
            ("false high",max(primary,key=lambda r:r["transfer"]-r["quality_rate"])),
            ("false low",min(primary,key=lambda r:r["transfer"]-r["quality_rate"])),
            ("ordinary median error",sorted(primary,key=lambda r:abs(r["transfer"]-r["quality_rate"]))[len(primary)//2])]
    for reason,r in chosen:
        selected[key(r)].append(reason)

    def describe(r):
        year,pid,pos=key(r)
        m=models[year,r["fold"]]
        inputs=transfer.features(r)
        if m:
            z=(transfer.matrix([r],m["disabled"])[0]-m["mean"])/m["scale"]
            terms=dict(zip(transfer.FEATURES,(z*np.array(m["coef"])).tolist()))
            assert math.isclose(m["intercept"]+sum(terms.values()),r["transfer"],abs_tol=1e-10)
            blank={**r,"other_rate":0.,"other_reliability":0.,"other_pivot_share":0.,
                   "other_outs":0.,"other_runs":0.,"other_positions":0}
            probe=float(transfer.predict(m,[blank])[0])
        else:
            terms={};probe=None
        past=[s for s in native[pid] if year-2<=s["season"]<=year]
        weighted=[{**s,"recency_weight":.5**(year-s["season"]),
                   "weighted_outs":s["native_outs"]*.5**(year-s["season"]),
                   "weighted_runs":None if s["range_runs"] is None else s["range_runs"]*.5**(year-s["season"])} for s in past]
        h,_=transfer.other_history(native[pid],year,pos)
        assert all(math.isclose(h[c],r[c],abs_tol=1e-10) for c in h)
        future=[s for s in native[pid] if year<s["season"]<=r["window_end"]]
        same=[s for s in future if s["position"]==pos and s["range_valid"]]
        if r["quality_rate"] is not None:
            assert math.isclose(1500*sum(s["range_runs"] for s in same)/sum(s["native_outs"] for s in same),r["quality_rate"],abs_tol=1e-10)
        return dict(forecast=r,origin_sources=weighted,actual_inputs=inputs,
                    fitted_intercept=None if m is None else m["intercept"],fitted_terms=terms,
                    disabled_features=[] if m is None else m["disabled"],
                    zero_other_fixed_fit_probe=probe,
                    direct_other_effect=None if probe is None else r["transfer"]-probe,
                    probe_scope="Other-history signal/exposure/share all zeroed together with original coefficients; explanatory, not a causal effect or approved replacement prediction.",
                    future_annual_path=future)
    cases=[]
    for k,reasons in sorted(selected.items()):
        r=next(s for s in rows if key(s)==k)
        cases.append(dict(selection=reasons,primary=describe(r),peers=[describe(p) for p in peers(rows,r)]))
    path=write("player-walkthrough.json",dict(cases=cases,player_walkthrough_status="complete",
          selection="Fixed player/positions plus biggest absolute-error gain/loss, signed errors and median; peers use only origin information",
          units="range runs per 500 defensive innings; later three-calendar-year pooled same-position MLB quality",
          full_value_forecast=False,no_2026_outcomes=True))
    write("walk-review.json",dict(cases=len(cases),people=len({c["primary"]["forecast"]["player_id"] for c in cases}),
          fully_replayed_peers=sum(len(c["peers"]) for c in cases),unknown_quality_peers=sum(p["forecast"]["quality_rate"] is None for c in cases for p in c["peers"]),
          source_arithmetic_and_predictions_verified=True,hash=sha256_file(path)))
    for c in cases:
        p=c["primary"];r=p["forecast"]
        print(dict(name=r["player_name"],pos=r["position"],selection=c["selection"],old=r["calibrated"],
                   new=r["transfer"],actual=r["quality_rate"],other_rate=r["other_rate"],
                   own_outs=r["history_outs"],other_outs=r["other_outs"],direct_other_effect=p["direct_other_effect"],
                   support=r["transfer_profile_people"]))


if __name__=="__main__":
    main()
