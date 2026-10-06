"""Locked outcome-complete minor ground-ball bridge; no forecast deployment."""

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import polars as pl
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from universal_baseball.minor_infield_play_share import annual, pooled, check_support, POSITIONS
from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections, save

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/generated/minor-infield-play-share"
PUBLIC = ROOT / "reports/model-evidence/minor-infield-play-share"
BASE = ROOT / "reports/generated/multiyear-hitter-components-v1"
ORIGINS = [2018, 2021, 2022, 2023, 2024]
FIXED = [(677951,2021),(683011,2022),(665161,2021),(682928,2021),
         (691783,2022),(691785,2024),(669023,2018),(622761,2018)]
BENCH = ["age_centered", "age_squared", "age_missing", "log_pa_lag0", "log_pa_lag1", "log_pa_lag2",
         "log_mlb_pa_lag0", "log_mlb_pa_lag1", "log_mlb_pa_lag2", "prior_range", "prior_range_known",
         "prior_mlb_defense", "log_gb"] + [f"level_{l}" for l in ["MLB","AAA","AA","A+","A","A-","RK","INACTIVE","UNKNOWN"]] + [f"role_{p}" for p in ["C","1B","2B","3B","SS","LF","CF","RF","DH","missing"]] + [f"share_{p}" for p in POSITIONS]
ARMS = {"benchmark": BENCH, "legacy": BENCH + [f"legacy_{p}" for p in POSITIONS],
        "complete": BENCH + [f"complete_{p}" for p in POSITIONS]}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf8"))


def hashes(paths):
    return {str(p): sha256_file(p) for p in paths}


def verify(mapping):
    for path, value in mapping.items():
        assert sha256_file(Path(path)) == value, path


def prepare():
    protections()
    assert not OUT.exists(), "Do not overwrite prepared evidence"
    OUT.mkdir(parents=True)
    PUBLIC.mkdir(parents=True, exist_ok=True)
    source_report = ROOT / "model_artifacts/ground-ball-ledger-v2-2026-09-26/report.json"
    paths = [Path(__file__), ROOT / "src/universal_baseball/minor_infield_play_share.py",
             ROOT / "tests/test_minor_infield_play_share.py", ROOT / "docs/minor-infield-play-share-contract.md", source_report]
    manifest = read(source_report)
    arrays, audits = [], []
    for path, meta in manifest["artifacts"].items():
        if Path(path).stem not in {str(y) for y in [2016,2017,2018,2019,2021,2022,2023,2024]}:
            continue
        path = ROOT / path
        assert sha256_file(path) == meta["sha256"]
        s = pl.read_parquet(path)
        assert s.height == meta["rows"]
        a, audit = annual(s)
        arrays.append(a)
        audit["season"] = int(path.stem)
        audit["levels"] = s.group_by("level", "league_id").len().sort("level", "league_id").to_dicts()
        audits.append(audit)
        paths.append(path)
    a = pl.concat(arrays).sort("season", "player_id", "position", "league_id")
    a.write_parquet(OUT / "annual.parquet")
    paths.append(OUT / "annual.parquet")
    certpath = BASE / "native-source-certification.json"
    cert = read(certpath)
    for path, value in cert["raw_hashes"].items():
        assert sha256_file(ROOT / path) == value
        paths.append(ROOT / path)
    for path, value in cert["upstream_hashes"].items():
        assert sha256_file(Path(path)) == value
        paths.append(Path(path))
    paths += [certpath, BASE / "native-fielding-history.parquet", BASE / "official-position-history.parquet", BASE / "component-panel.parquet"]
    n = pl.read_parquet(BASE / "native-fielding-history.parquet")
    o = pl.read_parquet(BASE / "official-position-history.parquet")
    panel_columns = ["player_id", "player_name", "origin_year", "age", "level", "stage"] + [c for c in BENCH if c not in {"prior_range", "prior_range_known", "prior_mlb_defense", "log_gb", "share_4", "share_5", "share_6"}]
    f = pl.read_parquet(BASE / "component-panel.parquet", columns=panel_columns).filter(pl.col("origin_year").is_in([2016,2017,2018,2021,2022,2023,2024])).with_columns(pl.col("age_centered").fill_null(0), pl.col("age_squared").fill_null(0))
    assert f.select("origin_year", "player_id").is_duplicated().sum() == 0
    assert n.select("season", "player_id").is_duplicated().sum() == 0
    assert o.select("season", "player_id").is_duplicated().sum() == 0
    panels = []
    for origin in sorted(f["origin_year"].unique()):
        q = f.filter(pl.col("origin_year") == origin)
        p = pooled(a, origin)
        wide = p.group_by("player_id").agg(pl.col("ground_balls").sum().alias("weighted_gb"))
        for pos in POSITIONS:
            z = p.filter(pl.col("position") == pos).select("player_id", pl.col("ground_balls").alias(f"gb_{pos}"), pl.col("credits").alias(f"credits_{pos}"), pl.col("expected_credits").alias(f"expected_{pos}"), pl.col("touches").alias(f"touches_{pos}"), pl.col("legacy_expected_credits").alias(f"legacy_expected_{pos}"), pl.col("complete_rate").alias(f"complete_{pos}"), pl.col("legacy_rate").alias(f"legacy_{pos}"))
            wide = wide.join(z, on="player_id", how="left")
        wide = wide.fill_null(0)
        q = q.join(wide, on="player_id", how="inner").filter(pl.col("weighted_gb") >= 25)
        past = n.filter(pl.col("season").is_between(origin-2,origin)).with_columns(pl.lit(.5).pow(origin-pl.col("season")).alias("w"))
        past = past.filter(pl.col("range_runs").is_not_null() & (pl.col("outs_total") > 0)).group_by("player_id").agg((pl.col("range_runs")*pl.col("w")).sum().alias("past_range"), (pl.col("outs_total")*pl.col("w")).sum().alias("past_outs"))
        prior = o.filter(pl.col("season") <= origin).group_by("player_id").agg(pl.col("official_outs").sum().alias("career_outs"))
        target_o = o.filter(pl.col("season") == origin+1).select("player_id", pl.col("official_outs").alias("future_official_outs"), (pl.col("outs_4")+pl.col("outs_5")+pl.col("outs_6")).alias("future_if_outs"))
        target_n = n.filter(pl.col("season") == origin+1).select("player_id", pl.col("range_runs").alias("native_range"), pl.col("outs_total").alias("future_native_outs"))
        q = q.join(past, on="player_id", how="left").join(prior, on="player_id", how="left").join(target_o,on="player_id",how="left").join(target_n,on="player_id",how="left")
        q = q.with_columns((pl.col("career_outs").fill_null(0)>0).cast(pl.Float64).alias("prior_mlb_defense"),
            pl.col("past_outs").is_not_null().cast(pl.Float64).alias("prior_range_known"),
            (1500*pl.col("past_range")/(pl.col("past_outs")+600)).fill_null(0).alias("prior_range"),
            pl.col("weighted_gb").log1p().alias("log_gb"), pl.lit(origin+1).alias("target_year"),
            pl.when(pl.col("future_official_outs").fill_null(0)==0).then(pl.lit(0.)).otherwise(pl.col("native_range")).alias("delivered"),
            pl.when((pl.col("future_native_outs")>=150) & (pl.col("future_if_outs")>=.5*pl.col("future_official_outs"))).then(1500*pl.col("native_range")/pl.col("future_native_outs")).otherwise(pl.lit(None)).alias("quality"),
        ).with_columns(*[(pl.col(f"gb_{pos}")/pl.col("weighted_gb")).alias(f"share_{pos}") for pos in POSITIONS])
        assert np.isfinite(q.select(ARMS["complete"]+ARMS["legacy"][-3:]).to_numpy()).all()
        panels.append(q.select("player_id","player_name","origin_year","target_year","age","level","stage","future_official_outs","future_native_outs","future_if_outs","delivered","quality","weighted_gb", *BENCH,*[c for pos in POSITIONS for c in [f"gb_{pos}",f"credits_{pos}",f"expected_{pos}",f"touches_{pos}",f"legacy_expected_{pos}",f"complete_{pos}",f"legacy_{pos}"]]))
    panel = pl.concat(panels).sort("origin_year","player_id").with_row_index("row_id")
    panel.write_parquet(OUT / "features.parquet")
    paths.append(OUT / "features.parquet")
    checks, cell_support = [], []
    for origin in ORIGINS:
        for fold in range(5):
            test = panel.filter((pl.col("origin_year")==origin)&(pl.col("player_id")%5==fold))
            for target in ["delivered","quality"]:
                train = panel.filter((pl.col("target_year")<=origin)&(pl.col("player_id")%5!=fold)&pl.col(target).is_not_null())
                check, support = check_support(train,test,ARMS["complete"]+ARMS["legacy"][-3:],origin,fold)
                check["target"] = target
                checks.append(check)
                cell_support += [dict(row_id=rowid, target=target, support=n) for rowid,n in zip(test["row_id"],support,strict=True)]
    save(OUT / "support.json", {"cells":checks,"rows":cell_support})
    paths.append(OUT / "support.json")
    prep = {"source_audit":audits,"population":panel.group_by("origin_year","level").agg(pl.len().alias("starting_players"),pl.col("quality").is_not_null().sum().alias("conditional_quality_labels"),pl.col("delivered").is_null().sum().alias("unknown_delivered_labels"), (pl.col("future_official_outs").fill_null(0)==0).sum().alias("no_MLB_defense")).sort("origin_year","level").to_dicts(),"checks":checks,"hashes":hashes(paths),"fits":0,"production_changed":False}
    save(OUT / "preflight.json", prep)
    save(PUBLIC / "preflight.json", prep)
    print(json.dumps({"rows":panel.height,"cells":len(checks),"blocked":sum(not c['fit_allowed'] for c in checks),"quality_cells": [c for c in checks if c['target']=='quality']},indent=2))


def scores(q, target):
    q = q.filter(pl.col(target).is_not_null())
    result = {"rows":q.height,"people":q["player_id"].n_unique(),"actual_sum":q[target].sum(),"arms":{}}
    y = q[target].to_numpy()
    w = np.minimum(q["future_native_outs"].fill_null(0).to_numpy()/1500,1) if target=="quality" else np.ones(len(y))
    for arm in ["neutral",*ARMS]:
        pred=q[f"{target}_{arm}"].to_numpy(); e=pred-y
        result["arms"][arm]={"rmse":float(np.sqrt(np.mean(e*e))),"mae":float(np.mean(abs(e))),"weighted_mse":float(np.average(e*e,weights=w)),"predicted_sum":float(pred.sum())} if len(y) else None
    return result


def fit():
    protections()
    prep=read(OUT / "preflight.json"); verify(prep["hashes"])
    assert not (OUT / "predictions.parquet").exists()
    f=pl.read_parquet(OUT / "features.parquet")
    checks=read(OUT / "support.json")
    lookup={(c['origin'],c['fold'],c['target']):c for c in checks['cells']}
    sup={(c['row_id'],c['target']):c['support'] for c in checks['rows']}
    output=[]; fits=[]
    for origin in ORIGINS:
        for fold in range(5):
            test=f.filter((pl.col("origin_year")==origin)&(pl.col("player_id")%5==fold))
            columns=[]
            for target in ["delivered","quality"]:
                train=f.filter((pl.col("target_year")<=origin)&(pl.col("player_id")%5!=fold)&pl.col(target).is_not_null())
                check, support=check_support(train,test,ARMS["complete"]+ARMS["legacy"][-3:],origin,fold)
                assert check["fit_allowed"]==lookup[origin,fold,target]["fit_allowed"]
                assert support==[sup[i,target] for i in test["row_id"]]
                columns += [pl.Series(f"{target}_support",support), pl.lit(0.).alias(f"{target}_neutral")]
                for arm, feats in ARMS.items():
                    pred=np.zeros(test.height)
                    if check["fit_allowed"]:
                        model=make_pipeline(StandardScaler(),Ridge(alpha=100))
                        weights=np.minimum(train["future_native_outs"].to_numpy()/1500,1) if target=="quality" else np.ones(train.height)
                        with threadpool_limits(limits=1):
                            model.fit(train.select(feats).to_numpy(), train[target].to_numpy(), ridge__sample_weight=weights)
                            pred=model.predict(test.select(feats).to_numpy())
                        path=OUT / f"{origin}-{fold}-{target}-{arm}.joblib"
                        joblib.dump(model,path)
                        fits.append(dict(origin=origin,fold=fold,target=target,arm=arm,path=str(path),sha256=sha256_file(path),features=feats,training_rows=train.height,training_people=train['player_id'].n_unique()))
                    columns.append(pl.Series(f"{target}_{arm}",pred))
            output.append(test.with_columns(columns))
    q=pl.concat(output).sort("row_id")
    assert q.height==f.filter(pl.col('origin_year').is_in(ORIGINS)).height
    q.write_parquet(OUT / "predictions.parquet")
    recent=q.filter(pl.col("origin_year")>=2022)
    rng=np.random.default_rng(2601005)
    z=recent.filter(pl.col('delivered').is_not_null()).with_columns(((pl.col('delivered_complete')-pl.col('delivered'))**2-(pl.col('delivered_benchmark')-pl.col('delivered'))**2).alias('difference')).group_by('player_id').agg(pl.col('difference').sum().alias('diff'),pl.len().alias('n'))
    diffs, ns=z['diff'].to_numpy(), z['n'].to_numpy()
    boots=[]
    for _ in range(1000):
        ix=rng.integers(0,len(z),len(z)); boots.append(float(diffs[ix].sum()/ns[ix].sum()))
    report={'recent_delivered':scores(recent,'delivered'),'recent_quality':scores(recent,'quality'), 'paired_recent_MSE_difference_complete_minus_benchmark':{'point':float(diffs.sum()/ns.sum()),'interval95':list(np.quantile(boots,[.025,.975]))},
        'by_origin':{str(o):{t:scores(q.filter(pl.col('origin_year')==o),t) for t in ['delivered','quality']} for o in ORIGINS},
        'by_recent_level':{l:{t:scores(recent.filter(pl.col('level')==l),t) for t in ['delivered','quality']} for l in sorted(recent['level'].unique())},
        'by_recent_prior_MLB':{str(v):{t:scores(recent.filter(pl.col('prior_mlb_defense')==v),t) for t in ['delivered','quality']} for v in [0,1]},
        'player_walkthrough_status':'pending','decision':'provisional_until_walkthrough','new_fits':len(fits),'production_changed':False,'protected_outcomes_used':False,
        'hashes':{**prep['hashes'],str(OUT/'predictions.parquet'):sha256_file(OUT/'predictions.parquet')},'fits':fits}
    save(OUT / 'fit-report.json',report)
    save(PUBLIC / 'fit-report.json',report)
    print(json.dumps({k:report[k] for k in ['recent_delivered','recent_quality','paired_recent_MSE_difference_complete_minus_benchmark','new_fits']},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('stage',choices=['prepare','fit']); args=parser.parse_args()
    prepare() if args.stage=='prepare' else fit()
