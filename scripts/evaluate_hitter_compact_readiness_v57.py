"""One reduced readiness representation; retain corrected baseline batting."""
from pathlib import Path
import sys
import warnings
import joblib
import numpy as np
import polars as pl
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.exceptions import ConvergenceWarning
from threadpoolctl import threadpool_limits
import evaluate_hitter_prospect_pooling_v54 as shared
import evaluate_hitter_numeric_repair_v53 as baseline
from fit_practical_hitter_v31 import weights
from universal_baseball.forecast_validation import preflight
from universal_baseball.storage import sha256_file
from universal_baseball.prospect_shared_history import materialize

ROOT=baseline.ROOT
OUT=ROOT/"reports/generated/practical-hitter-compact-readiness-v57"
read=baseline.read


def write(name,obj):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_text(baseline.json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf8")


def prepare():
    assert read(ROOT/"reports/generated/practical-hitter-head-assembly-v56/report.json")["player_walkthrough_status"]=="complete"
    assert not (OUT/"preflight.json").exists()
    source,full=materialize(pl.read_parquet(baseline.OUT/"features.parquet"))
    production=[f"pooled_{b}_{ev}" for b in ["AAA","AA"] for ev in ["K","BB","HR"]]
    names=[n for n in full if not n.startswith("pooled_") or n in production]
    assert len(names)==79 and len(full)-len(names)==92
    assert np.isfinite(source.select(names).to_numpy()).all()
    OUT.mkdir(parents=True,exist_ok=True); source.write_parquet(OUT/"features.parquet")
    prior=read(baseline.OUT/"preflight.json");cells=[];supports=[];profiles=[]
    keys=["stage","age_group","draft_known","thin_exposure","draft_age_group"]
    for c in prior["cells"]:
        tr=source.filter(pl.col("row_id").is_in(c["training_row_ids"])&(pl.col("prior_debut")==0)).sort("row_id")
        te=source.filter(pl.col("row_id").is_in(c["test_row_ids"])&(pl.col("prior_debut")==0)).sort("player_id")
        active=tr.filter(pl.col("next_pa")>0);checks={}
        assert len(active)>100 and set(tr["next_active"].unique())=={0,1}
        for head,rows in [("participation",tr),("conditional_pa",active)]:
            support,note=preflight(rows,te,cutoff=c["year"],fold=c["fold"],features=names,expected_keys=te.select("row_id","horizon").iter_rows())
            checks[head]=note; supports.append(support.with_columns(pl.lit(head).alias("head")))
            n=baseline.profile(rows).group_by(keys).agg(pl.col("player_id").n_unique().alias("profile_players"))
            profiles.append(baseline.profile(te).select("row_id",*keys).join(n,on=keys,how="left",validate="m:1").with_columns(pl.col("profile_players").fill_null(0),pl.lit(head).alias("head")))
        cells.append(dict(year=c["year"],fold=c["fold"],test_row_ids=c["test_row_ids"],prospect_test_ids=te["row_id"].to_list(),
            prospect_training_ids=tr["row_id"].to_list(),preflight=checks))
    pl.concat(supports).write_parquet(OUT/"support.parquet");pl.concat(profiles).write_parquet(OUT/"profile-support.parquet")
    paths=[baseline.OUT/"features.parquet",baseline.OUT/"scored-predictions.parquet",baseline.OUT/"preflight.json",
        ROOT/"reports/generated/practical-hitter-head-assembly-v56/report.json",
        OUT/"features.parquet",OUT/"support.parquet",OUT/"profile-support.parquet",Path(__file__),
        ROOT/"src/universal_baseball/prospect_shared_history.py",ROOT/"scripts/fit_practical_hitter_v31.py",
        ROOT/"docs/practical-hitter-compact-readiness-v57-contract.md"]
    write("preflight.json",dict(before_fitting=True,cells=cells,features=names,removed_features=[n for n in full if n not in names],
        input_hashes={str(p):sha256_file(p) for p in paths},settings=dict(logistic_C=.01,ridge_alpha=100,max_iter=1000,tol=1e-7),
        protected_outcomes_used=False,established_forecasts_unchanged=True,rate_unchanged=True))
    print("Actual subset preflights saved: 79 readiness features, 70 heads.",flush=True)


def fit():
    pre=read(OUT/"preflight.json")
    for p,h in pre["input_hashes"].items():assert sha256_file(Path(p))==h,p
    source=pl.read_parquet(OUT/"features.parquet");base=pl.read_parquet(baseline.OUT/"scored-predictions.parquet")
    names=pre["features"];fits=[];clips=[]
    with threadpool_limits(limits=2),warnings.catch_warnings():
        warnings.simplefilter("error",ConvergenceWarning)
        for c in pre["cells"]:
            y,k=c["year"],c["fold"];path=OUT/f"forecast-{y}-{k}.parquet"
            if path.exists():
                note=read(OUT/f"fit-{y}-{k}.json");assert sha256_file(path)==note["prediction_sha256"]
                for h in note["heads"]:assert sha256_file(Path(h["path"]))==h["sha256"]
                fits.append(note);clips.append(note["conditional_clipped"]);continue
            tr=source.filter(pl.col("row_id").is_in(c["prospect_training_ids"])).sort("row_id")
            active=tr.filter(pl.col("next_pa")>0)
            te=source.filter(pl.col("row_id").is_in(c["prospect_test_ids"])).sort("row_id")
            q=base.filter(pl.col("row_id").is_in(c["test_row_ids"])).sort("row_id")
            mask=q["prior_debut"].to_numpy()==0
            assert np.array_equal(q["row_id"].to_numpy()[mask],te["row_id"].to_numpy())
            heads=[];pred={}
            for head,rows in [("participation",tr),("conditional_pa",active)]:
                learner=LogisticRegression(C=.01,max_iter=1000,tol=1e-7,solver="lbfgs") if head=="participation" else Ridge(alpha=100)
                model=make_pipeline(StandardScaler(),learner)
                target="next_active" if head=="participation" else "next_pa"
                model.fit(rows.select(names).to_numpy(),rows[target].to_numpy(),
                    **{("logisticregression" if head=="participation" else "ridge")+"__sample_weight":weights(rows)})
                pred[head]=model.predict_proba(te.select(names).to_numpy())[:,1] if head=="participation" else model.predict(te.select(names).to_numpy())
                assert np.isfinite(pred[head]).all()
                mp=OUT/f"{head}-{y}-{k}.joblib";joblib.dump(model,mp,compress=3)
                heads.append(dict(head=head,path=str(mp),sha256=sha256_file(mp),training_rows=len(rows),training_players=rows["player_id"].n_unique(),
                    maximum_target_year=int(rows["target_year"].max()),iterations=int(learner.n_iter_[0]) if head=="participation" else None))
            p=q["repaired_p"].to_numpy().copy();cond=q["repaired_conditional_pa"].to_numpy().copy()
            p[mask]=pred["participation"];cond[mask]=np.clip(pred["conditional_pa"],1,800)
            p[q["hard_unavailable"].to_numpy()|q["reported_retired"].to_numpy()]=0
            pa=p*cond;rate=q["repaired_rate"].to_numpy()
            q=q.with_columns(pl.Series("shared_p",p),pl.Series("shared_conditional_pa",cond),pl.Series("shared_pa",pa),pl.Series("shared_rate",rate),
                pl.Series("prospect_pa_only_pa",pa),pl.Series("prospect_pa_only_rate",rate),
                pl.col("repaired_pa").alias("prospect_rate_only_pa"),pl.col("repaired_rate").alias("prospect_rate_only_rate"))
            for arm in ["shared","prospect_pa_only","prospect_rate_only"]:
                q=q.with_columns((pl.col(arm+"_pa")*(pl.col(arm+"_rate")/600+pl.col("origin_replacement_rate"))).alias(arm+"_value"))
            assert q.select(base.columns).equals(base.filter(pl.col("row_id").is_in(c["test_row_ids"])).sort("row_id"))
            nclip=int(((pred["conditional_pa"]<1)|(pred["conditional_pa"]>800)).sum());clips.append(nclip)
            q.write_parquet(path);note=dict(year=y,fold=k,heads=heads,conditional_clipped=nclip,prediction_sha256=sha256_file(path))
            write(f"fit-{y}-{k}.json",note);fits.append(note)
            print(f"Compact readiness {y}/{k}: two heads.",flush=True)
    q=pl.concat([pl.read_parquet(OUT/f"forecast-{c['year']}-{c['fold']}.parquet") for c in pre["cells"]]).sort("row_id")
    assert len(q)==30506 and q.select(base.columns).equals(base.sort("row_id"))
    assert q["shared_rate"].equals(q["repaired_rate"])
    q.write_parquet(OUT/"predictions.parquet");write("fits.json",fits)
    write("fit-report.json",dict(heads=70,all_original_columns_exact=True,all_logistic_fits_converged=True,
        conditional_clipped=sum(clips),rate_unchanged=True,player_walkthrough_status="pending",
        protected_outcomes_used=False,frozen_forecast_changed=False))


if __name__=="__main__":{"prepare":prepare,"fit":fit}[sys.argv[1]]()
