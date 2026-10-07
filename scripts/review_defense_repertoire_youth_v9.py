"""Append the young-profile failure trace without refitting or changing case seals."""

import json
import math

import numpy as np
import polars as pl

from universal_baseball.defense_repertoire import ROLES,predict
from run_defense_repertoire_v9 import ROOT,OUT,PUBLIC,SOURCE,check,read
from run_hitter_finite_return_baseline import save
from universal_baseball.storage import sha256_file


def main():
    check();assert not (OUT/"young-profile-diagnosis.json").exists()
    q=pl.read_parquet(OUT/"predictions.parquet").with_columns(
        (pl.col("repair_cell_squared_error")-pl.col("ratio_cell_squared_error")).alias("harm"))
    young=q.filter(pl.col("age_band")=="3").sort("harm",descending=True)
    source=pl.read_parquet(SOURCE/"source.parquet")
    records=q.to_dicts();walks=[]
    for focal in young.head(4).to_dicts():
        pool=[r for r in records if r["origin_year"]==focal["origin_year"] and r["stage"]==focal["stage"]
            and r["player_id"]!=focal["player_id"] and r["repertoire_primary_role"]==focal["repertoire_primary_role"]
            and r["age"] is not None and abs(r["age"]-focal["age"])<=3]
        def distance(r):
            return (sum(abs(x-y) for x,y in zip(r["repertoire_shares"],focal["repertoire_shares"]))+
                .1*abs(math.log1p(r["role_defensive_sample"])-math.log1p(focal["role_defensive_sample"]))+
                abs(r["age"]-focal["age"])/3,r["row_id"])
        chosen=sorted(pool,key=distance)[:3];traces=[]
        for r in [focal,*chosen]:
            model=read(OUT/f"model-{r['origin_year']}-{r['outer_fold']}.json")
            calculation=predict(r,{tuple(c["key"]):c for c in model["tables"]})
            assert np.allclose(calculation["values"],[r[f"repair_{p}"] for p in ROLES],atol=1e-9,rtol=0)
            known=source.filter((pl.col("player_id")==r["player_id"]) & pl.col("season").is_between(r["origin_year"]-2,r["origin_year"]))
            traces.append(dict(player_id=r["player_id"],name=r["player_name"],origin=r["origin_year"],age=r["age"],stage=r["stage"],
                current_MLB_PA=r["pa_0"],expected_PA=r["preseason_pa"],actual_PA=r["next_pa"],
                raw_origin_rows=known.to_dicts(),repertoire={k:v for k,v in r.items() if k.startswith("repertoire_")},
                scalar_calculation=calculation,forecasts={a:{str(p):r[f"{a}_{p}"] for p in ROLES} for a in ("ratio","repair")},
                actuals={str(p):r[f"actual_{p}"] for p in ROLES},native_actuals={c:r[f"actual_native_{c}"] for c in ("framing","throwing","blocking","arm","receiving")},
                future_nonarrival_not_zero_talent=True))
        walks.append(dict(player_id=focal["player_id"],name=focal["player_name"],origin=focal["origin_year"],
            harm=focal["harm"],eligible_origin_peers=len(pool),records=traces))
    result=dict(selection="Four largest increases in position-cell squared error among origin age 15–19; diagnostics, not independent confirmation.",
        total_young_harm=float(young["harm"].sum()),top_four_harm_share=float(young.head(4)["harm"].sum()/young["harm"].sum()),
        cases=walks,profile_issue="Concentrated minor-position allocation misses MLB role transitions; some misses also have PA overprojection.",
        no_rows_removed=True,no_refit=True,protected_outcomes_used=False,status="mechanics_traced_baseball_judgment_in_readable_review",
        hashes={str(p):sha256_file(p) for p in [ROOT/"scripts/review_defense_repertoire_youth_v9.py",OUT/"predictions.parquet",OUT/"preflight.json"]})
    save(OUT/"young-profile-diagnosis.json",result);save(PUBLIC/"young-profile-diagnosis.json",result)
    print(json.dumps(dict(cases=len(walks),top_four_harm_share=result["top_four_harm_share"])))


if __name__=="__main__":main()
