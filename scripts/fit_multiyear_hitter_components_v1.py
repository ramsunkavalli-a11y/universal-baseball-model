"""Run the frozen small component comparison; no protected outcomes."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
import json
from pathlib import Path

import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

from audit_multiyear_hitter_components_v1 import OUT, OLD, SOURCES
from universal_baseball.multiyear_hitter_components import (
    COMPONENTS, START, attach_labels, choose_component, component_ridge, historical_rate, mature_mask, pandemic)
from universal_baseball.player_value_baserunning_runs import build_baserunning_reference, project_baserunning_runs
from universal_baseball.current_baserunning import ATTEMPT_CANDIDATE, SUCCESS_CANDIDATE, ADVANCEMENT_CANDIDATE
from universal_baseball.player_value_steal_data import StealStint, build_loo_player_season_summaries
from universal_baseball.player_value_steal_projection import PlayerSeasonStealSummary, attempt_multiplier, success_log_odds_residual
from universal_baseball.player_value_advancement_projection import PlayerSeasonAdvancementSummary, projected_advancement_rate
from universal_baseball.position_role_profile import build_batting_role_profiles, BATTING_ROLE_POSITIONS
from universal_baseball.position_role_transition import transition_smoothed_prediction
from universal_baseball.player_value_positional_adjustment import POSITIONAL_RUNS_PER_162
from universal_baseball.storage import sha256_file

PLAN = Path("docs/multiyear-hitter-components-v1-plan.md")
PA = Path("model_artifacts/hitter-three-year-opportunity-v1-2026-09-22/predictions.parquet")
CURRENT = Path("model_artifacts/multiyear-hitter-followup-v2-2026-09-22/forecast-2026-2028.parquet")
KEY = ["origin_year", "player_id"]
YEARS = [2016,2017,2018,2019,2021,2022,2023,2024,2025]
ROLE = ["role_"+p for p in BATTING_ROLE_POSITIONS]


def save(path, obj):
    path.write_text(json.dumps(obj, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def load_sources():
    frames, hashes = [], {}
    specs = [("affiliated-skill-source-2008-2017",2008,2017),
             ("affiliated-skill-source-2018-2022",2018,2022), ("affiliated-skill-source",2023,2025)]
    for directory, lo, hi in specs:
        path = OLD/directory/"tables/affiliated_hitting_components.parquet"
        frames.append(pl.read_parquet(path).filter(pl.col("season").is_between(lo,hi)))
        hashes[str(path)] = sha256_file(path)
    stats = pl.concat(frames, how="diagonal_relaxed")
    if stats.unique(["season","player_id","sport_id","team_id"]).height != stats.height:
        raise ValueError("Overlapping batting history")
    fielding = []
    for k in ("mlb_fielding", "milb_origin_fielding", "affiliated_fielding", "affiliated_fielding_2025"):
        path = SOURCES[k]; f = pl.read_parquet(path)
        if k != "mlb_fielding":
            f = f.filter(pl.col("level_group") != "MLB")
        if k == "milb_origin_fielding":
            f = f.filter(pl.col("season") < 2021)
        fielding.append(f.select("season","player_id","position_abbreviation","games_played","games_started","fielding_outs"))
        hashes[str(path)] = sha256_file(path)
    roles = build_batting_role_profiles(pl.concat(fielding,how="vertical_relaxed")).profile
    roles = roles.group_by("season","player_id").agg(*[
        pl.col("role_probability").filter(pl.col("position_abbreviation")==p).sum().alias("role_"+p)
        for p in BATTING_ROLE_POSITIONS])
    return stats, roles, hashes


def annual_labels():
    batting = pl.read_parquet(SOURCES["mlb_batting"])
    official = pl.read_parquet(OUT/"official-position-history.parquet")
    native = pl.read_parquet(OUT/"native-fielding-history.parquet")
    advancement = pl.read_parquet(OUT/"native-advancement-history.parquet")
    # Fixed transparent run conversion, centered within the observed target year.
    # The season's centering is label construction, never an input at an earlier cutoff.
    steal = batting.with_columns((pl.col("batting_hits")-pl.col("batting_doubles")-pl.col("batting_triples")
        -pl.col("batting_home_runs")+pl.col("batting_base_on_balls")-pl.col("batting_intentional_walks")
        +pl.col("batting_hit_by_pitch")).alias("op"),
        (pl.col("batting_stolen_bases")*.2-pl.col("batting_caught_stealing")*.4).alias("raw_steal"))
    steal = steal.with_columns((pl.col("raw_steal")-pl.col("op")*pl.col("raw_steal").sum().over("season")/
        pl.col("op").sum().over("season")).alias("steals"))
    keys = pl.concat([f.select("season","player_id") for f in (batting,official,native)],how="vertical_relaxed").unique()
    f = keys.join(steal.select("season","player_id","steals",pl.col("batting_plate_appearances").alias("label_pa")),on=["season","player_id"],how="left")
    f = f.join(official,on=["season","player_id"],how="left").join(native,on=["season","player_id"],how="left")
    f = f.join(advancement,on=["season","player_id"],how="left")
    f = f.with_columns(pl.col("label_pa").fill_null(0),pl.col("steals").fill_null(0),
        pl.col("position_runs").fill_null(0).alias("position"),
        # Leaderboard n=1 omits players with no eligible running opportunity.
        pl.when(pl.col("season")>=2016).then(pl.col("advancement_runs").fill_null(0)).alias("advancement"))
    native_fields = {"general":pl.col("range_runs")+pl.col("arm_runs")+pl.col("dp_runs"),
                     "framing":pl.col("framing_runs"),"throwing":pl.col("throwing_runs"),"blocking":pl.col("blocking_runs")}
    for c, expr in native_fields.items():
        f = f.with_columns(pl.when(pl.col("season")<START[c]).then(None)
            .when((pl.col("official_outs").fill_null(0)==0)&pl.col("outs_total").is_null()).then(0.)
            .otherwise(expr).alias(c))
    return f.select("season","player_id","label_pa",*COMPONENTS).filter(pl.col("season").is_between(2009,2025))


def feature_panel(annual, roles):
    panel = pl.read_parquet(SOURCES["panel"])
    features = [c for c in panel.columns if c.startswith(("age_","level_","log_","share_"))]
    features += [f"{c}_rate_lag{lag}" for lag in range(3) for c in ("ubb","strikeout","single","double","triple","home_run","hbp","stolen_base")]
    panel = panel.join(roles.rename({"season":"origin_year"}),on=KEY,how="left",validate="1:1",maintain_order="left")
    panel = panel.with_columns(pl.col(ROLE[0]).is_null().cast(pl.Int8).alias("role_missing"), *[pl.col(c).fill_null(0) for c in ROLE])
    features += ROLE+["role_missing"]
    for lag in range(3):
        right = annual.select((pl.col("season")+lag).alias("origin_year"),"player_id",pl.col("label_pa").alias(f"label_pa_lag{lag}"),
                              *[pl.col(c).alias(f"{c}_lag{lag}") for c in COMPONENTS])
        panel = panel.join(right,on=KEY,how="left",validate="1:1",maintain_order="left")
        for c in COMPONENTS:
            # Availability is player-specific and era-specific; a zero prediction
            # for missing history is not labeled measured average defense.
            name = f"{c}_lag{lag}"
            panel = panel.with_columns(pl.col(name).is_not_null().cast(pl.Int8).alias(name+"_available"),
                (600*pl.col(name)/(600+pl.col(f"label_pa_lag{lag}"))).alias(name+"_rate"))
            features += [name,name+"_available",name+"_rate"]
    return attach_labels(panel,annual), features


def running_history(stats, advancement):
    stints = []
    for r in stats.iter_rows(named=True):
        level = r["level_group"]
        stints.append(StealStint(r["season"],"MLB" if level=="MLB" else "MiLB",str(r["sport_id"]),level,r["player_id"],r["player_name"],
            *[float(r[c] or 0) for c in ("plate_appearances","hits","doubles","triples","home_runs","base_on_balls",
                                       "intentional_walks","hit_by_pitch","stolen_bases","caught_stealing")]))
    history, audit = build_loo_player_season_summaries(stints)
    steals, advances = defaultdict(list),defaultdict(list)
    for r in history: steals[r.player_id].append(r)
    for r in advancement.iter_rows(named=True):
        advances[r["player_id"]].append(PlayerSeasonAdvancementSummary(r["player_id"],r["season"],r["advancement_runs"],r["advancement_opportunities"]))
    return steals,advances,asdict(audit)


def reference(stats, advancement, year):
    f = stats.filter((pl.col("season")==year)&(pl.col("level_group")=="MLB"))
    op = float((f["hits"]-f["doubles"]-f["triples"]-f["home_runs"]+f["base_on_balls"]-f["intentional_walks"]+f["hit_by_pitch"]).sum())
    # Fixed .2/- .4 conversion matches the common label, not a later MLB environment.
    return build_baserunning_reference(season=year,plate_appearances=float(f["plate_appearances"].sum()),runs=.1625,outs=1.,
        steal_opportunity_proxy=op,steal_attempts=float((f["stolen_bases"]+f["caught_stealing"]).sum()),stolen_bases=float(f["stolen_bases"].sum()),
        advancement_opportunities=float(advancement.filter(pl.col("season")==year)["advancement_opportunities"].sum()))


def benchmark_rates(test, roles, cutoff, h, steals, advances, ref):
    earlier = roles.filter(pl.col("season")+h<=cutoff).join(roles.rename({"season":"target_year",**{c:c+"_future" for c in ROLE}}),
        left_on=[pl.col("season")+h,"player_id"],right_on=["target_year","player_id"],how="inner")
    if earlier.height:
        earlier = earlier.filter(~pl.Series(pandemic(earlier["season"].to_numpy(),h)))
    source = earlier.select(ROLE).to_numpy(); dest = earlier.select([c+"_future" for c in ROLE]).to_numpy()
    primary = source.argmax(axis=1) if len(source) else np.array([],int)
    means = {i:dest[primary==i].mean(axis=0) for i in range(9) if np.any(primary==i)}
    values = np.array([POSITIONAL_RUNS_PER_162[p] for p in BATTING_ROLE_POSITIONS])
    result = {c:[] for c in COMPONENTS}
    for row in test.iter_rows(named=True):
        pid = row["player_id"]; current = np.array([row[c] for c in ROLE]); i=current.argmax(); share=current[i]
        predicted = transition_smoothed_prediction(current,primary_share=share,destination_mean=means[i]) if share>=.65 and i in means else current
        result["position"].append(float(predicted@values))
        # No future history is allowed even when target season is two/three years away.
        sh = [x for x in steals[pid] if x.season<=cutoff]
        ah = [x for x in advances[pid] if x.season<=cutoff]
        st = PlayerSeasonStealSummary(pid,cutoff+h,"MLB",0,0,0,0,0)
        at = PlayerSeasonAdvancementSummary(pid,cutoff+h,0,0)
        v = project_baserunning_runs(projected_mlb_pa=600,attempt_multiplier=attempt_multiplier(st,sh,ATTEMPT_CANDIDATE),
            success_logodds_residual=success_log_odds_residual(st,sh,SUCCESS_CANDIDATE),
            advancement_rate=projected_advancement_rate(at,ah,ADVANCEMENT_CANDIDATE),reference=ref)
        result["steals"].append(v.steal_runs); result["advancement"].append(v.advancement_runs)
        for c in ("general","framing","throwing","blocking"):
            result[c].append(float(historical_rate([row[f"{c}_lag{l}"] or 0. for l in range(3)],
                [row[f"label_pa_lag{l}"] or 0. for l in range(3)],[row[f"{c}_lag{l}_available"] for l in range(3)])))
    return {k:np.array(v) for k,v in result.items()}


def main():
    OUT.mkdir(exist_ok=True,parents=True)
    stats,roles,hashes = load_sources(); annual=annual_labels(); panel,features=feature_panel(annual,roles)
    annual.write_parquet(OUT/"annual-component-labels.parquet")
    roles.write_parquet(OUT/"position-profiles.parquet")
    panel.write_parquet(OUT/"component-panel.parquet")
    advancement=pl.read_parquet(OUT/"native-advancement-history.parquet")
    steals,advances,audit=running_history(stats,advancement)
    historical=pl.read_parquet(PA); current=pl.read_parquet(CURRENT)
    x=panel.select(features).to_numpy(); predictions=[]; notes=[]
    for year in YEARS:
        test=panel.filter(pl.col("origin_year")==year); tx=test.select(features).to_numpy()
        ref=reference(stats,advancement,year)
        for h in (1,2,3):
            if year!=2025 and year+h>2025: continue
            past=pl.concat(predictions,how="vertical_relaxed") if predictions else pl.DataFrame()
            rates=benchmark_rates(test,roles,year,h,steals,advances,ref)
            if year==2025:
                opportunity=current.select("player_id",pl.col(f"expected_pa_h{h}").alias("expected_pa"),pl.col(f"value_{2025+h}").alias("batting"))
            else:
                opportunity=historical.filter((pl.col("origin_year")==year)&(pl.col("horizon")==h)).select("player_id",pl.col("accepted").alias("expected_pa"),pl.col("delivered").alias("batting"))
            # Later folds are component-only. Direct value still has a valid out-of-time
            # forecast; carry-rate scoring needs PA, so fit a fixed Ridge workload proxy
            # using the identical dated all-player panel, explicitly not delivered PA.
            if opportunity.is_empty():
                m=(panel["origin_year"].to_numpy()+h<=year)&~pandemic(panel["origin_year"].to_numpy(),h)&np.isfinite(panel[f"pa_h{h}"].to_numpy())
                pa_model=component_ridge().fit(x[m],panel[f"pa_h{h}"].to_numpy()[m])
                opportunity=test.select("player_id").with_columns(pl.Series("expected_pa",np.clip(pa_model.predict(tx),0,750)),pl.lit(None,dtype=pl.Float64).alias("batting"))
            base=test.select(*KEY,"age","stage",pl.col(f"war_h{h}").alias("actual_batting")).join(opportunity,on="player_id",how="left",validate="1:1",maintain_order="left")
            for c in COMPONENTS:
                m=mature_mask(panel,year,h,c); train=panel.filter(pl.Series(m)); y=panel[f"{c}_h{h}"].to_numpy()
                benchmark=rates[c]*base["expected_pa"].to_numpy()/600
                direct=benchmark.copy(); fitted=train.height>=100 and train["origin_year"].n_unique()>=2
                if fitted:
                    counts=train.group_by("origin_year").len(); countmap=dict(counts.iter_rows())
                    weight=np.array([train.height/(len(countmap)*countmap[v]) for v in train["origin_year"]])
                    model=component_ridge().fit(x[m],y[m],ridge__sample_weight=weight)
                    direct=model.predict(tx)
                chosen, selection=choose_component(past,year,h,c)
                row=base.with_columns(pl.lit(h).alias("horizon"),pl.lit(c).alias("component"),pl.lit(bool(pandemic(year,h))).alias("pandemic"),
                    pl.Series("actual",test[f"{c}_h{h}"]),pl.lit(0.).alias("neutral"),pl.Series("benchmark",benchmark),pl.Series("direct",direct),
                    pl.Series("benchmark_rate",rates[c]),pl.lit(chosen).alias("selected_model"))
                row=row.with_columns(pl.col(chosen).alias("selected")); predictions.append(row)
                notes.append({"origin":year,"horizon":h,"component":c,"fitted":fitted,"training_rows":train.height,
                    "latest_label_year":int(train["origin_year"].max()+h) if train.height else None,
                    "training_origins":sorted(train["origin_year"].unique().to_list()),"selection":selection,"selected":chosen,
                    "pa_source":"delivered" if year not in (2023,2024) else "component_only_ridge_proxy"})
            print(f"Component fits {year} H{h}",flush=True)
        pl.concat(predictions,how="vertical_relaxed").write_parquet(OUT/"component-predictions.parquet")
    for p in [PLAN,PA,CURRENT,SOURCES["panel"],SOURCES["mlb_batting"],OUT/"native-fielding-history.parquet",OUT/"native-advancement-history.parquet",OUT/"official-position-history.parquet"]:
        hashes[str(p)]=sha256_file(p)
    save(OUT/"fit-manifest.json",{"plan_sha256":sha256_file(PLAN),"source_hashes":hashes,"features":features,"fits":notes,
        "steal_environment_audit":audit,"code_hashes":{p:sha256_file(Path(p)) for p in [__file__,"src/universal_baseball/multiyear_hitter_components.py"]},
        "label_note":"steals fixed .2/- .4, season-centered; zero advancement when absent from unqualified n=1 export; missing active fielding preserved",
        "caveat":"2023/24 component-only PA proxy is not the delivered workload model; score/selection must distinguish this"})


if __name__=="__main__":
    with threadpool_limits(limits=4): main()
