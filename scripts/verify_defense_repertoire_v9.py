"""Independent source vectors, scalar-group sums and full-cohort forecast arithmetic."""

from collections import defaultdict
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections,save

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"reports/generated/defense-repertoire-v9"
PUBLIC=ROOT/"reports/model-evidence/defense-repertoire-v9"
OLD=ROOT/"reports/generated/defense-opportunity-v8"


def read(p):return json.loads(p.read_text(encoding="utf8"))


def norm(v):
    v=np.array(v,float);return v/v.sum() if v.sum() else v


def own_vectors(r,history):
    hist=[h for h in history if r["origin_year"]-2<=h["season"]<=r["origin_year"]]
    current=[h for h in hist if h["is_mlb"] and h["season"]==r["origin_year"]]
    fallback=[h for h in hist if not h["is_mlb"]]
    kind="latest_minor_season"
    if not fallback:
        fallback=[h for h in hist if h["is_mlb"] and h["season"]<r["origin_year"] and h["defensive_outs"]>0]
        kind="older_MLB_season" if fallback else "roster_or_unknown"
    latest=max((h["season"] for h in fallback),default=None)
    fallback=[h for h in fallback if h["season"]==latest]
    def vec(rows,field,positions):return np.array([sum(h[f"{field}_{p}"] for h in rows) for p in positions],float)
    co=vec(current,"outs",range(2,10));fo=vec(fallback,"outs",range(2,10))
    cs=vec(current,"starts",range(2,11));fs=vec(fallback,"starts",range(2,11))
    if not fallback:
        fo=np.array([str(p)==str(r["source_position"]) for p in range(2,10)],float)
        fs=np.array([str(p)==str(r["source_position"]) for p in range(2,11)],float)
    a=r["pa_0"]/(r["pa_0"]+100)
    weights=np.array([a,1-a])
    if co.sum()==0 and fo.sum()>0:weights=np.array([0.,1.])
    if fo.sum()==0 and co.sum()>0:weights=np.array([1.,0.])
    mix=norm(np.stack([norm(co),norm(fo)]).T@weights)
    cr=norm(cs) if cs.sum() else np.r_[norm(co),0]
    fr=norm(fs) if fs.sum() else np.r_[norm(fo),0]
    role=norm(a*cr+(1-a)*fr)
    if role.sum()==0 and mix.sum():role=np.r_[mix,0]
    primary=int(np.argmax(role))+2 if role.sum() else 0
    return dict(shares=mix,role=role,primary=primary,weight=a,current_outs=co,fallback_outs=fo,current_starts=cs,fallback_starts=fs,latest=latest,kind=kind)


def main():
    protections();assert not (OUT/"independent-verification.json").exists()
    pre,report=read(OUT/"preflight.json"),read(OUT/"fit-report.json")
    for p,h in {**pre["hashes"],**report["hashes"]}.items():assert sha256_file(Path(p))==h,p
    assert sha256_file(OUT/"features.parquet")==pre["features_sha256"]
    assert sha256_file(OUT/"profile-support.parquet")==pre["profile_sha256"]
    f=pl.read_parquet(OUT/"features.parquet");q=pl.read_parquet(OUT/"predictions.parquet")
    old=pl.read_parquet(OLD/"predictions.parquet").sort("row_id");q=q.sort("row_id")
    assert q["row_id"].equals(old["row_id"]) and q.height==12432
    anchors=[n for n in old.columns if n.startswith(("carry_","ratio_","pooled_","context_","actual_"))]
    for n in anchors:
        value = sum(q[f"actual_{p}"] for p in range(2,10)) if n=="actual_total_outs" else q[n]
        assert value.equals(old[n]),n
    hist=defaultdict(list)
    for r in pl.read_parquet(ROOT/"reports/generated/defense-position-opportunity-v7/annual-usage.parquet").to_dicts():hist[r["player_id"]].append(r)
    for r in f.to_dicts():
        v=own_vectors(r,hist[r["player_id"]])
        for field,key in [("shares","repertoire_shares"),("role","repertoire_role_shares"),("current_outs","repertoire_current_outs"),
            ("fallback_outs","repertoire_fallback_outs"),("current_starts","repertoire_current_starts"),("fallback_starts","repertoire_fallback_starts")]:
            assert np.allclose(v[field],r[key],atol=1e-14,rtol=0),key
        assert v["primary"]==r["repertoire_primary_role"] and v["weight"]==r["repertoire_weight"]
        assert v["latest"]==r["repertoire_fallback_season"] and v["kind"]==r["repertoire_fallback_kind"]
    means=forecasts=0;diagnostics=[];profiles=pl.read_parquet(OUT/"profile-support.parquet")
    for mnote in report["models"]:
        path=Path(mnote["path"]);assert sha256_file(path)==mnote["sha256"]
        m=read(path);y,k=m["origin"],m["fold"]
        tr=f.filter((pl.col("target_year")<=y) & (pl.col("outer_fold")!=k) & (pl.col("next_pa")>0))
        te=q.filter((pl.col("origin_year")==y) & (pl.col("outer_fold")==k))
        assert sorted(tr["row_id"])==sorted(m["training_row_ids"])
        assert sorted(te["row_id"])==sorted(m["test_row_ids"])
        assert not set(tr["player_id"]) & set(te["player_id"])
        tables={tuple(c["key"]):c for c in m["tables"]}
        for key,c in tables.items():
            group=tr
            if key[0] in ("role_stage","role"):group=group.filter(pl.col("repertoire_primary_role")==int(key[1]))
            if key[0] in ("family_stage","family"):group=group.filter(pl.col("repertoire_family")==key[1])
            if key[0].endswith("_stage"):group=group.filter(pl.col("stage")==key[2])
            masses=group.group_by("player_id").agg(pl.col("next_pa").sum())
            den=int(group["next_pa"].sum());num=sum(int(group[f"actual_{p}"].sum()) for p in range(2,10))
            dh=int(group["actual_10"].sum());eff=den**2/float((masses["next_pa"].cast(pl.Float64)**2).sum()) if den else 0.
            assert c["people"]==masses.height and c["rows"]==group.height
            assert c["denominator_PA"]==den and c["numerator_outs"]==num and c["numerator_DH_starts"]==dh
            assert np.isclose(c["effective_people"],eff,atol=1e-10,rtol=1e-12)
            assert c["outs_per_PA"]==(num/den if den else None) and c["DH_starts_per_PA"]==(dh/den if den else None)
            means+=1
        old_model=read(OLD/f"model-{y}-{k}.json")
        assert m["native_conversions"]==old_model["conversions"]
        for r in te.to_dicts():
            role=str(r["repertoire_primary_role"]);family=r["repertoire_family"];stage=r["stage"]
            candidates=[("role_stage",role,stage),("family_stage",family,stage),("role",role),("family",family),("all",)]
            c=next(tables[key] for key in candidates if tables[key]["people"]>=20 and tables[key]["effective_people"]>=10 and tables[key]["denominator_PA"]>0)
            assert c["key"]==json.loads(r["repair_prior_key"])
            a=r["pa_0"]/(r["pa_0"]+100);prior_outs=sum(r[f"carry_{p}"] for p in range(2,10))
            # Algebraically simplify a*(outs/PA): no accidental division by a
            # tiny or zero denominator, and independently equivalent arithmetic.
            rate=(prior_outs/(r["pa_0"]+100) if r["pa_0"] else 0.)+(1-a)*c["outs_per_PA"]
            total=r["preseason_pa"]*rate
            values=np.array(r["repertoire_shares"])*total
            dh=r["preseason_pa"]*((r["carry_10"]/(r["pa_0"]+100) if r["pa_0"] else 0.)+(1-a)*c["DH_starts_per_PA"])
            assert np.allclose(values,[r[f"repair_{p}"] for p in range(2,10)],atol=1e-9,rtol=1e-12),(r["player_id"],r["origin_year"],r["pa_0"])
            assert np.isclose(dh,r["repair_10"],atol=1e-10,rtol=0)
            assert np.isclose(total,r["repair_potential_outs"],atol=1e-9,rtol=0)
            assert all(v==0 for share,v in zip(r["repertoire_shares"],values) if share==0)
            assert np.isclose(values.sum(),r["repair_total_outs"],atol=1e-9,rtol=0)
            for channel,conv in m["native_conversions"].items():
                exposure=values[0] if channel in ("framing","throwing","blocking") else values[5:8].sum() if channel=="arm" else values[1]
                assert np.isclose(exposure*conv["rate"],r[f"repair_native_{channel}"],atol=1e-9,rtol=1e-12)
            forecasts+=1
        diagnostic=dict(origin=y,fold=k,test_rows=te.height,
            unknown_repertoire_rows=int(te["repertoire_unknown"].sum()),unallocated_potential_outs=float(te["repair_unallocated_outs"].sum()),
            coarse_group_rows=sum(json.loads(s)[0] in ("role","family","all") for s in te["repair_prior_key"]),
            large_training_range_rows=int((te["repair_total_outs"]>sum(tr[f"actual_{p}"] for p in range(2,10)).max()).sum()))
        diagnostics.append(diagnostic)
    coverage=[];groups=[]
    for y in (2022,2023,2024):
        te=q.filter(pl.col("origin_year")==y)
        current=sum(pl.col(f"carry_{p}") for p in range(2,10));future=sum(pl.col(f"actual_{p}") for p in range(2,10))
        filters={"continuing":(current>0)&(future>0),"new_or_returning":(current==0)&(future>0),
                 "exit":(current>0)&(future==0),"no_defense_before_or_after":(current==0)&(future==0)}
        for name,condition in filters.items():
            g=te.filter(condition)
            for a in ("ratio","repair"):
                v=g.select([f"{a}_{p}" for p in range(2,10)]).to_numpy();target=g.select([f"actual_{p}" for p in range(2,10)]).to_numpy()
                groups.append(dict(origin=y,cohort=name,arm=a,rows=g.height,rmse=float(np.sqrt(np.mean((v-target)**2))),
                    predicted_outs=float(v.sum()),actual_outs=float(target.sum())))
        for a in ("ratio","repair"):
            v=te.select([f"{a}_{p}" for p in range(2,10)]).to_numpy();target=te.select([f"actual_{p}" for p in range(2,10)]).to_numpy()
            rmse=float(np.sqrt(np.mean((v-target)**2)))
            saved=next(s for s in report["overall"] if s["origin"]==y and s["arm"]==a)
            assert np.isclose(rmse,saved["cell_rmse"],atol=1e-9,rtol=0)
        baseline_coverage=read(OLD/"independent-verification.json")["full_MLB_and_matched_totals"]
        for p in range(2,10):
            oldpos=next(s for s in baseline_coverage if s["origin"]==y and s["position"]==p)
            assert oldpos["matched_actual"]==te[f"actual_{p}"].sum()
            coverage.append(dict(origin=y,position=p,full_actual=oldpos["full_actual"],matched_actual=oldpos["matched_actual"],
                omitted_actual=oldpos["omitted_actual"],repair_outs=float(te[f"repair_{p}"].sum())))
    result=dict(integrity_pass=True,source_repertoires_replayed=f.height,scalar_tables_replayed=means,all_forecasts_replayed=forecasts,
        anchors_identical=True,unrelated_position_allocations=0,native_conversions_unchanged=True,
        profile_rows=profiles.height,sparse_profiles=int(profiles["sparse"].sum()),unseen_profiles=int((profiles["training_people"]==0).sum()),
        per_fold_diagnostics=diagnostics,exposure_cohorts=groups,matched_and_full_MLB=coverage,
        forecast_or_explorer_changed=False,protected_outcomes_used=False,player_walkthrough_status="baseball_judgment_pending",
        hashes={str(p):sha256_file(p) for p in [Path(__file__),OUT/"preflight.json",OUT/"fit-report.json",OUT/"predictions.parquet",OUT/"player-walkthrough.json"]})
    save(OUT/"independent-verification.json",result);save(PUBLIC/"independent-verification.json",result)
    protections();print(json.dumps({k:result[k] for k in ["integrity_pass","scalar_tables_replayed","all_forecasts_replayed","unrelated_position_allocations"]}))


if __name__=="__main__":main()
