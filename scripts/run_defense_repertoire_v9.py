"""One sealed repertoire/exposure repair and complete saved calculation traces."""

from collections import defaultdict
import json
import math
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.defense_repertoire import POSITIONS,ROLES,PSEUDO_PA,make_repertoire,keys,mean_group,predict
from universal_baseball.defense_opportunity_bridge import CHANNELS,native_from_outs
from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections,save
from run_defense_opportunity_v8 import score,native_score

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/"reports/generated/defense-opportunity-v8"
SOURCE=ROOT/"reports/generated/defense-position-opportunity-v7"
OUT=ROOT/"reports/generated/defense-repertoire-v9"
PUBLIC=ROOT/"reports/model-evidence/defense-repertoire-v9"


def read(path):
    return json.loads(path.read_text(encoding="utf8"))


def write(name,data):
    save(OUT/name,data);save(PUBLIC/name,data)


def hashes(paths):
    return {str(p):sha256_file(p) for p in paths}


def check():
    pre=read(OUT/"preflight.json")
    for p,digest in pre["hashes"].items():
        assert sha256_file(Path(p))==digest,p
    assert sha256_file(OUT/"features.parquet")==pre["features_sha256"]
    protections()
    return pre


def prepare():
    protections();assert not (OUT/"preflight.json").exists()
    OUT.mkdir(parents=True,exist_ok=True);PUBLIC.mkdir(parents=True,exist_ok=True)
    final=read(OLD/"final-review.json")
    assert final["player_walkthrough_status"]=="complete" and not final["baseball_reasonability_pass"]
    for p,h in final["hashes"].items():
        assert sha256_file(Path(p))==h
    previous=read(OLD/"preflight.json")
    for p,h in previous["hash_inputs"].items():
        assert sha256_file(Path(p))==h
    annual=pl.read_parquet(SOURCE/"annual-usage.parquet")
    by_person=defaultdict(list)
    for r in annual.to_dicts():by_person[r["player_id"]].append(r)
    features=[]
    for r in pl.read_parquet(OLD/"features.parquet").to_dicts():
        r.update(make_repertoire(r,by_person[r["player_id"]]));features.append(r)
    frame=pl.DataFrame(features,infer_schema_length=None)
    assert frame["target_year"].max()<=2025 and frame.height==30506
    frame.write_parquet(OUT/"features.parquet")
    cells=[];profiles=[]
    for old in previous["role_cells"]:
        y,k=old["origin"],old["fold"]
        tr=frame.filter(pl.col("row_id").is_in(old["training_row_ids"]))
        te=frame.filter(pl.col("row_id").is_in(old["test_row_ids"]))
        assert tr["target_year"].max()<=y and not set(tr["player_id"]) & set(te["player_id"])
        required={key for r in te.to_dicts() for key in keys(r)}
        support=[mean_group(tr.to_dicts(),key) for key in sorted(required)]
        assert next(s for s in support if s["key"]==["all"])["people"]>=20
        cells.append(dict(origin=y,fold=k,training_row_ids=tr["row_id"].to_list(),test_row_ids=te["row_id"].to_list(),
            training_people=tr["player_id"].n_unique(),training_target_ceiling=int(tr["target_year"].max()),
            support=support,computed_before_outcome_numerators=True,player_disjoint=True))
        # Detailed origin support is diagnostic only. Retain every weak profile.
        def sample(r):
            p=r["pa_0"];return "0" if p==0 else "1-49" if p<50 else "50-199" if p<200 else "200+"
        bucket=defaultdict(set)
        for r in tr.to_dicts():bucket[r["stage"],r["age_band"],sample(r),r["repertoire_primary_role"]].add(r["player_id"])
        for r in te.to_dicts():
            key=(r["stage"],r["age_band"],sample(r),r["repertoire_primary_role"])
            profiles.append(dict(row_id=r["row_id"],player_id=r["player_id"],origin=y,fold=k,stage=key[0],age_band=key[1],
                current_MLB_sample=key[2],primary_role=key[3],training_people=len(bucket[key]),sparse=len(bucket[key])<20,
                unknown_repertoire=r["repertoire_unknown"]))
    pl.DataFrame(profiles).write_parquet(OUT/"profile-support.parquet")
    paths=[Path(__file__),ROOT/"docs/defense-repertoire-v9-contract.md",ROOT/"src/universal_baseball/defense_repertoire.py",
        ROOT/"tests/test_defense_repertoire.py",ROOT/"scripts/run_defense_opportunity_v8.py",
        ROOT/"src/universal_baseball/defense_opportunity_bridge.py",SOURCE/"annual-usage.parquet",OLD/"features.parquet",
        OLD/"predictions.parquet",OLD/"final-review.json",OLD/"fit-report.json",OLD/"player-walkthrough.json"]
    paths += [OLD/f"model-{c['origin']}-{c['fold']}.json" for c in cells]
    write("preflight.json",dict(before_fitting=True,cells=cells,pseudo_sample_PA=PSEUDO_PA,one_repair_no_tuning=True,
        profile_rows=len(profiles),unseen_profiles=sum(p["training_people"]==0 for p in profiles),sparse_profiles=sum(p["sparse"] for p in profiles),
        unknown_repertoires=sum(p["unknown_repertoire"] for p in profiles),fixed_upstream_PA=True,native_conversions_reused=True,
        protected_outcomes_used=False,hashes=hashes(paths),features_sha256=sha256_file(OUT/"features.parquet"),
        profile_sha256=sha256_file(OUT/"profile-support.parquet")))
    print(json.dumps(dict(status="ready_before_fitting",cells=len(cells),test_rows=len(profiles),unknown_repertoires=sum(p["unknown_repertoire"] for p in profiles))))


def interval(frame):
    people=frame["player_id"].unique().sort().to_list();index={p:i for i,p in enumerate(people)}
    present=np.zeros((len(people),3));loss=np.zeros((len(people),3,2))
    for r in frame.to_dicts():
        i,j=index[r["player_id"]],r["origin_year"]-2022;present[i,j]=1
        for a,arm in enumerate(("repair","ratio")):
            loss[i,j,a]=sum((r[f"{arm}_{p}"]-r[f"actual_{p}"])**2 for p in POSITIONS)/8
    rng=np.random.default_rng(708007);changes=[]
    for _ in range(2000):
        counts=rng.multinomial(len(people),np.full(len(people),1/len(people)))
        rmse=np.sqrt(np.einsum("i,ija->ja",counts,loss)/(counts@present)[:,None])
        changes.append(float((rmse[:,0]-rmse[:,1]).mean()))
    rmses=np.sqrt(loss.sum(axis=0)/present.sum(axis=0)[:,None])
    return dict(contrast="repair_minus_ratio",change=float((rmses[:,0]-rmses[:,1]).mean()),
        interval_95=np.quantile(changes,[.025,.975]).tolist(),people=len(people),seed=708007,draws=2000,
        whole_person_clustered=True,development_only=True)


def fit():
    pre=check();assert not (OUT/"fit-report.json").exists()
    frame=pl.read_parquet(OUT/"features.parquet");old=pl.read_parquet(OLD/"predictions.parquet")
    arms=[c for c in old.columns if c.startswith(("carry_","ratio_","pooled_","context_")) and c not in frame.columns]
    frame=frame.join(old.select("row_id",*arms),on="row_id",how="left",validate="1:1")
    rows=[];model_receipts=[]
    for c in pre["cells"]:
        y,k=c["origin"],c["fold"]
        tr=frame.filter(pl.col("row_id").is_in(c["training_row_ids"]));te=frame.filter(pl.col("row_id").is_in(c["test_row_ids"]))
        tables={tuple(s["key"]):mean_group(tr.to_dicts(),tuple(s["key"]),True) for s in c["support"]}
        for s in c["support"]:
            assert all(tables[tuple(s["key"])][p]==v for p,v in s.items())
        conv=read(OLD/f"model-{y}-{k}.json")["conversions"]
        model=dict(origin=y,fold=k,tables=list(tables.values()),native_conversions=conv,
                   training_row_ids=c["training_row_ids"],test_row_ids=c["test_row_ids"])
        path=OUT/f"model-{y}-{k}.json";save(path,model)
        model_receipts.append(dict(origin=y,fold=k,path=str(path),sha256=sha256_file(path)))
        for r in te.to_dicts():
            p=predict(r,tables)
            for pos,v in zip(ROLES,p["values"]):r[f"repair_{pos}"]=v
            for channel,v in native_from_outs(p["values"],conv).items():r[f"repair_native_{channel}"]=v
            r.update(repair_total_outs=sum(p["values"][:8]),repair_cell_squared_error=float(np.mean([(p["values"][j]-r[f"actual_{pos}"])**2 for j,pos in enumerate(POSITIONS)])),
                repair_potential_outs=p["potential_total_outs"],repair_unallocated_outs=max(0.,p["unallocated_outs"]),
                repair_prior_key=json.dumps(p["prior"]["key"]),repair_prior_people=p["prior"]["people"],
                repair_prior_effective_people=p["prior"]["effective_people"],repair_outs_per_PA=p["shrunk_outs_per_PA"])
            rows.append(r)
        print(f"Repertoire fold {y}/{k} saved",flush=True)
    result=pl.DataFrame(rows,infer_schema_length=None).sort("row_id")
    assert result.height==12432 and result["row_id"].n_unique()==12432
    assert result.select([f"repair_{p}" for p in ROLES]).to_numpy().min()>=0
    assert np.isfinite(result.select([f"repair_{p}" for p in ROLES]).to_numpy()).all()
    result.write_parquet(OUT/"predictions.parquet")
    overall=[];groups=[];native=[]
    for y in (2022,2023,2024):
        q=result.filter(pl.col("origin_year")==y)
        for a in ("carry","ratio","pooled","context","repair"):overall.append(dict(origin=y,arm=a,**score(q,a)))
        for field in ("stage","age_band"):
            for value in q[field].unique():
                g=q.filter(pl.col(field)==value)
                for a in ("ratio","repair"):groups.append(dict(origin=y,field=field,value=value,arm=a,**score(g,a)))
        for channel in CHANNELS:
            for a in ("ratio","context","repair"):
                for positive in (False,True):
                    native.append(dict(origin=y,channel=channel,arm=a,positive_only=positive,
                        unknown_rows=q[f"actual_native_{channel}"].null_count(),score=native_score(q,a,channel,positive)))
    write("fit-report.json",dict(models=model_receipts,overall=overall,groups=groups,native_scores=native,
        interval=interval(result),player_walkthrough_status="pending",disposition="pending_player_review",
        upstream_PA_and_quality_unchanged=True,protected_outcomes_used=False,
        hashes=hashes([OUT/"preflight.json",OUT/"predictions.parquet"])))
    protections();print(json.dumps(dict(rows=result.height,status="provisional_needs_walkthrough")))


def review():
    pre=check();assert not (OUT/"player-walkthrough.json").exists()
    report=read(OUT/"fit-report.json")
    for p,h in report["hashes"].items():assert sha256_file(Path(p))==h
    q=pl.read_parquet(OUT/"predictions.parquet");records=q.to_dicts();mapping={(r["player_id"],r["origin_year"]):r for r in records}
    source=pl.read_parquet(SOURCE/"source.parquet")
    previous=read(OLD/"player-walkthrough.json")
    selected={(c["player_id"],c["origin"]):["previous_focal",*c["reasons"]] for c in previous["cases"]}
    peers={(c["player_id"],c["origin"]):[mapping[(p["player_id"],p["origin"])] for p in c["records"][1:]] for c in previous["cases"]}
    dev=[r for r in records if r["origin_year"] in (2022,2023)]
    gain=lambda r:r["ratio_cell_squared_error"]-r["repair_cell_squared_error"]
    e=lambda r:r["repair_total_outs"]-sum(r[f"actual_{p}"] for p in POSITIONS)
    extra=[(max(dev,key=gain),"new_largest_gain"),(min(dev,key=gain),"new_largest_deterioration"),
           (max(dev,key=e),"new_largest_false_high"),(min(dev,key=e),"new_largest_false_low")]
    unknown=[r for r in records if r["repertoire_unknown"]]
    if unknown:extra.append((max(unknown,key=lambda r:r["repair_potential_outs"]),"unknown_repertoire"))
    for r,why in extra:
        key=(r["player_id"],r["origin_year"]);selected.setdefault(key,[]).append(why)
        if key not in peers:
            pool=[p for p in records if p["origin_year"]==r["origin_year"] and p["stage"]==r["stage"] and p["player_id"]!=r["player_id"]
                and p["repertoire_primary_role"]==r["repertoire_primary_role"]
                and (r["age"] is None or p["age"] is not None and abs(p["age"]-r["age"])<=3)]
            def distance(p):
                return (sum(abs(a-b) for a,b in zip(r["repertoire_shares"],p["repertoire_shares"]))+
                    .1*abs(math.log1p(r["role_defensive_sample"])-math.log1p(p["role_defensive_sample"]))+
                    (abs(p["age"]-r["age"])/3 if r["age"] is not None else 0),p["row_id"])
            peers[key]=sorted(pool,key=distance)[:3]
    walks=[]
    for key,reasons in sorted(selected.items()):
        main=mapping[key];traces=[]
        for r in [main,*peers[key]]:
            model=read(OUT/f"model-{r['origin_year']}-{r['outer_fold']}.json")
            p=predict(r,{tuple(t["key"]):t for t in model["tables"]})
            assert np.allclose(p["values"],[r[f"repair_{pos}"] for pos in ROLES],atol=1e-9,rtol=0)
            raw=source.filter((pl.col("player_id")==r["player_id"]) & pl.col("season").is_between(r["origin_year"]-2,r["origin_year"]))
            actual=source.filter((pl.col("player_id")==r["player_id"]) & (pl.col("season")==r["target_year"]) & pl.col("is_mlb"))
            traces.append(dict(player_id=r["player_id"],player_name=r["player_name"],origin=r["origin_year"],fold=r["outer_fold"],stage=r["stage"],age=r["age"],
                current_MLB_PA=r["pa_0"],expected_PA=r["preseason_pa"],actual_PA=r["next_pa"],
                repertoire={k:v for k,v in r.items() if k.startswith("repertoire_")},scalar_calculation=p,
                origin_source_rows=raw.to_dicts(),future_official_usage=actual.to_dicts(),
                position_forecasts={a:{str(pos):r[f"{a}_{pos}"] for pos in ROLES} for a in ("carry","ratio","pooled","context","repair")},
                actual_position_outs_and_DH_starts={str(pos):r[f"actual_{pos}"] for pos in ROLES},
                native_forecasts={a:{c:r[f"{a}_native_{c}"] for c in CHANNELS} for a in ("ratio","context","repair")},
                native_actuals={c:r[f"actual_native_{c}"] for c in CHANNELS},
                actual_PA_sensitivity_values=[v*r["next_pa"]/r["preseason_pa"] if r["preseason_pa"] else 0 for v in p["values"]],
                sensitivity_not_forecast=True,nonarrival_unknown_quality=True))
        walks.append(dict(player_id=main["player_id"],player_name=main["player_name"],origin=main["origin_year"],reasons=reasons,records=traces))
    write("player-walkthrough.json",dict(status="mechanics_complete_baseball_review_pending",cases=walks,
        peer_selection="Preserve previous origin-selected peers; additional cases use same origin/stage/dominant role/age within three years, role/exposure distance and no outcome filter.",
        protected_outcomes_used=False))
    print(json.dumps(dict(cases=len(walks),peers=sum(len(c["records"])-1 for c in walks),status="needs_baseball_judgment_and_independent_replay")))


if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("action",choices=["prepare","fit","review"])
    args=p.parse_args();{"prepare":prepare,"fit":fit,"review":review}[args.action]()
