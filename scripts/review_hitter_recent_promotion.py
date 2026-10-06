"""Replay, paired scoring and fixed player traces; final judgment stays separate."""
from pathlib import Path

import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

import audit_hitter_big_miss_groups as a
from audit_hitter_arrival_cohorts import PEER_FIELDS
from evaluate_hitter_readiness_v49 import logit_trace
from evaluate_hitter_reported_departures import scored
from prepare_hitter_overseas_integration import ANCHOR, annual_labels
from run_hitter_finite_return_baseline import protections, save
from test_hitter_recent_promotion import OUT, PUBLIC, REFERENCE
from universal_baseball.hitter_recent_promotion import profile, MINOR_BUCKETS
from universal_baseball.histogram_prediction_trace import trace
from universal_baseball.hitter_compatible_value import labels
from universal_baseball.storage import sha256_file

FIXED = [(694671,2023), (701762,2024), (682616,2022), (701350,2024),
         (640457,2016), (668804,2018), (664848,2021)]
ARMS = ["departure", "recent"]


def losses(g, arm):
    p = g[arm+"_p"].to_numpy()
    active = (g["next_pa"].to_numpy() > 0).astype(float)
    cp = np.clip(p, 1e-6, 1-1e-6)
    return dict(pa_mse=(g[arm+"_pa"].to_numpy()-g["next_pa"].to_numpy())**2,
        pa_mae=abs(g[arm+"_pa"].to_numpy()-g["next_pa"].to_numpy()),
        value_mse=(g[arm+"_value"].to_numpy()-g["actual_relative_value"].to_numpy())**2,
        brier=(p-active)**2, log_loss=-(active*np.log(cp)+(1-active)*np.log(1-cp)))


def balanced(g, arm):
    year = g["origin_year"].to_numpy()
    result = scored(g, arm)
    for name, v in losses(g, arm).items():
        result["equal_origin_"+name] = float(np.mean([v[year == y].mean() for y in np.unique(year)]))
    return result


def paired(g, reference, metric):
    delta = losses(g,"recent")[metric] - losses(g,reference)[metric]
    people, pi = np.unique(g["player_id"].to_numpy(), return_inverse=True)
    _, yi = np.unique(g["origin_year"].to_numpy(), return_inverse=True)
    den = np.zeros((len(people), int(yi.max())+1))
    num = den.copy()
    np.add.at(den, (pi,yi), 1)
    np.add.at(num, (pi,yi), delta)
    rng, draws = np.random.default_rng(105), []
    for _ in range(2000):
        w = np.bincount(rng.integers(0,len(people),len(people)), minlength=len(people))
        d = w@den
        if (d > 0).all():
            draws.append(float(np.mean((w@num)/d)))
    assert len(draws) > 1900
    return dict(reference=reference, metric=metric,
        difference=float(np.mean(num.sum(0)/den.sum(0))),
        lower=float(np.quantile(draws,.025)), upper=float(np.quantile(draws,.975)),
        replicates=len(draws), qualification="Nominal whole-player/equal-origin development interval; not fresh confirmation or season-shock protection")


def main():
    assert not (PUBLIC/"scores.json").exists() and not (PUBLIC/"player-walks.json").exists()
    protections()
    pre = a.read(OUT/"preflight.json")
    a.verify(pre["hashes"])
    a.verify(a.read(PUBLIC/"source-seal.json")["hashes"])
    fit = a.read(OUT/"fit-report.json")
    assert sha256_file(OUT/"predictions.parquet") == fit["predictions_sha256"]
    q = pl.read_parquet(OUT/"predictions.parquet").sort("row_id")
    old = pl.read_parquet(REFERENCE).sort("row_id")
    assert q.select(old.columns).equals(old)
    assert q["recent_rate"].equals(q["departure_rate"])
    for arm in ["recent", "departure"]:
        assert np.allclose(q[arm+"_pa"], q[arm+"_p"]*q[arm+"_conditional_pa"], rtol=0, atol=1e-10)
        assert np.allclose(q[arm+"_value"], q[arm+"_pa"]*(q[arm+"_rate"]/600+q["origin_replacement_rate"]), rtol=0, atol=1e-10)
    fits = {(c["origin"],c["fold"]): c for c in fit["cells"]}
    anchors = {(c["origin"],c["fold"]): c for c in a.read(a.BASE/"fit-report.json")["cells"]}
    frames = [pl.read_parquet(a.BASE/f"features-{k}.parquet") for k in range(5)]
    replays = 0
    with threadpool_limits(limits=2):
        for c in fit["cells"]:
            y,k = c["origin"], c["fold"]
            part = q.filter((pl.col("origin_year") == y) & (pl.col("outer_fold") == k)).sort("row_id")
            x = frames[k].filter(pl.col("row_id").is_in(part["row_id"].to_list())).sort("row_id").select(pre["features"]).to_numpy()
            for arm, cell in [("recent",c), ("observation",anchors[y,k])]:
                for h in cell["heads"]:
                    assert sha256_file(a.ROOT/h["path"]) == h["sha256"]
                    assert h["features"] == pre["features"]
                    m = joblib.load(a.ROOT/h["path"])
                    v = m.predict_proba(x)[:,1] if h["head"] == "participation" else m.predict(x)
                    col = arm+("_raw_p" if h["head"] == "participation" else "_raw_conditional_pa")
                    assert np.allclose(v,part[col],rtol=0,atol=1e-10)
                    replays += 1
    assert replays == 140
    stats_path = a.ROOT/"reports/generated/practical-hitter-v31/dated-stints.parquet"
    stats = pl.read_parquet(stats_path)
    counts_by_player, env = annual_labels(stats)
    counts = np.array([counts_by_player.get((r["target_year"],r["player_id"]),np.zeros(8)) for r in q.iter_rows(named=True)])
    actual = labels(counts, np.array([env[y] for y in q["origin_year"]]),
                    np.array([env[y] for y in q["target_year"]]),q["origin_replacement_rate"].to_numpy())
    assert np.array_equal(actual["pa"],q["next_pa"])
    assert np.allclose(actual["relative_value"],q["actual_relative_value"],rtol=0,atol=1e-10)
    raw = ["age", "prior_debut", "draft_known", "draft_elapsed", "draft_rank", "draft_class_unknown", "on_40man", "scout_rank_score_0",
           "milb_canceled_0", "milb_canceled_1", "milb_canceled_2",
           *[b+"_"+str(k)+"_pa" for b in MINOR_BUCKETS for k in range(3)], *PEER_FIELDS]
    raw = list(dict.fromkeys(raw))
    g = profile(q.drop([n for n in raw if n in q.columns]).join(frames[0].select("row_id",*raw),on="row_id",validate="1:1"))
    never = g.filter(pl.col("prior_debut") == 0)
    public = g.filter(~pl.col("source_addition")).join(pl.read_parquet(ANCHOR,
        columns=["row_id","steamer_index","zips_index"]),on="row_id",how="left",validate="1:1").filter(
            (pl.col("pa_0") > 0) & pl.col("steamer_index").is_not_null() & pl.col("zips_index").is_not_null())
    assert public.height == 2627 and (public["prior_debut"] > 0).all()
    for n in ["p","conditional_pa","pa","rate","value"]:
        assert public["recent_"+n].equals(public["departure_"+n])
    scopes = [("all",g), ("never_all",never), ("never_recent",never.filter(pl.col("origin_year") >= 2022)),
              ("never_six_non2021",never.filter(pl.col("origin_year") != 2021)),
              ("never_2021_stress",never.filter(pl.col("origin_year") == 2021)),
              ("past_MLB_unchanged",g.filter(pl.col("prior_debut") > 0)), ("public_unchanged",public)]
    for y in sorted(never["origin_year"].unique().to_list()):
        sub = never.filter(pl.col("origin_year") == y)
        scopes += [("never_origin="+str(y),sub), ("upper_origin="+str(y),sub.filter(pl.col("upper_now"))),
                   ("lower_origin="+str(y),sub.filter(~pl.col("upper_now")))]
    for name, sub in [("recent",never.filter(pl.col("origin_year") >= 2022)), ("all",never)]:
        scopes += [(name+"_upper",sub.filter(pl.col("upper_now"))), (name+"_lower",sub.filter(~pl.col("upper_now"))),
                   (name+"_thin_advanced_top_pick",sub.filter(pl.col("thin_advanced_top_pick"))),
                   (name+"_nonarrival",sub.filter(pl.col("next_pa") == 0)), (name+"_actual_regular",sub.filter(pl.col("next_pa") >= 400))]
    scores = []
    for name,sub in scopes:
        if not sub.height:
            continue
        original = sub.filter(~pl.col("source_addition"))
        scores.append(dict(scope=name, **{arm:balanced(sub,arm) for arm in ARMS},
            selected_original_only={arm:balanced(original,arm) for arm in ["current",*ARMS]} if original.height else None,
            selected_anchor_missing_additions=sub.filter(pl.col("source_addition")).height))
    with threadpool_limits(limits=2):
        intervals = [dict(scope=name, **paired(sub if ref == "departure" else sub.filter(~pl.col("source_addition")),ref,metric))
                     for name,sub in scopes if name in ["never_recent","never_six_non2021"]
                     for ref in ["departure","current"] for metric in ["pa_mse","value_mse"]]
    save(PUBLIC/"scores.json",dict(scores=scores, intervals=intervals, independent_head_replays=replays,
        player_walkthrough_status="pending_judgment", all_original_columns_unchanged=True,
        previously_debuted_outputs_bit_exact=True, fixed_hitting=True, protected_outcomes_read=False,
        hashes={str(OUT/"predictions.parquet"):sha256_file(OUT/"predictions.parquet"), str(OUT/"fit-report.json"):sha256_file(OUT/"fit-report.json"), str(Path(__file__)):sha256_file(Path(__file__)), str(ANCHOR):sha256_file(ANCHOR)}))
    recent = never.filter(pl.col("origin_year") >= 2022).with_columns(
        (((pl.col("recent_pa")-pl.col("next_pa"))**2)-((pl.col("departure_pa")-pl.col("next_pa"))**2)).alias("PA_loss_difference"),
        (pl.col("recent_pa")-pl.col("next_pa")).alias("candidate_error"))
    selected = []
    for pid,y in FIXED:
        r = g.filter((pl.col("player_id") == pid) & (pl.col("origin_year") == y))
        assert r.height == 1
        selected.append(dict(row_id=r["row_id"].item(), reason="fixed"))
    for col,descending,name in [("PA_loss_difference",False,"largest_recent_PA_gain"), ("PA_loss_difference",True,"largest_recent_PA_harm"),
        ("candidate_error",True,"largest_recent_false_high"), ("candidate_error",False,"largest_recent_false_low")]:
        r = recent.sort([col,"row_id"],descending=[descending,False]).head(1)
        selected.append(dict(row_id=r["row_id"].item(),reason=name))
    ordinary = recent.filter(pl.col("next_pa") > 0).with_columns(pl.col("candidate_error").abs().alias("size")).sort("size","row_id").head(1)
    selected.append(dict(row_id=ordinary["row_id"].item(),reason="ordinary_recent_positive_PA"))
    save(PUBLIC/"case-selection.json",dict(cases=selected, diagnostic_not_independent=True))
    sup = pl.read_parquet(OUT/"profile-support.parquet")
    walks = []
    with threadpool_limits(limits=2):
        for r in g.filter(pl.col("row_id").is_in([s["row_id"] for s in selected])).iter_rows(named=True):
            y,k = r["origin_year"],r["outer_fold"]
            f = frames[k].filter(pl.col("row_id") == r["row_id"])
            x = f.select(pre["features"]).to_numpy()[0]
            heads = []
            for arm, cell in [("recent",fits[y,k]), ("observation",anchors[y,k])]:
                for h in cell["heads"]:
                    m = joblib.load(a.ROOT/h["path"])
                    t = logit_trace(m,x,pre["features"]) if h["head"] == "participation" else trace(m,x,pre["features"])
                    heads.append(dict(arm=arm,head=h["head"],model_sha256=h["sha256"],
                        reference=t["reference"],raw_prediction=t["raw_prediction"],
                        linked_probability=t.get("linked_probability"), feature_effects=t["feature_effects"][:8],
                        path_accounting_not_causal=True))
            distance = ((pl.col("age")-r["age"])/5)**2
            for key in PEER_FIELDS:
                scale = 300 if key.endswith("_pa") else 1 if key in ["draft_rank","scout_rank_score_0"] else .1 if key.endswith("_K") else .05
                distance += ((pl.col(key)-r[key])/scale)**2
            peers = never.filter((pl.col("origin_year") == y) & (pl.col("draft_time") == r["draft_time"]) &
                (pl.col("upper_level") == r["upper_level"]) & (pl.col("protected_listing") == r["protected_listing"]) &
                (pl.col("player_id") != r["player_id"])).with_columns(distance.alias("distance")).sort("distance","row_id").head(3)
            walks.append(dict(origin={n:r[n] for n in ["row_id","player_id","player_name","origin_year","ctx_information_date","outer_fold","age","draft_time","upper_level","thin_advanced_top_pick"]},
                stats=stats.filter((pl.col("player_id") == r["player_id"]) & pl.col("season").is_between(y-2,y)).select("season","bucket","plate_appearances","home_runs","strike_outs","base_on_balls").sort("season","bucket").to_dicts(),
                actual_inputs=f.select(pre["features"]).row(0,named=True), saved_head_traces=heads,
                status={n:r[n] for n in ["status_hard_unavailable","status_retired","departure_reported"] if n in r},
                forecasts={arm:{n:r[arm+"_"+n] for n in ["p","conditional_pa","pa","rate","value"]} for arm in ARMS+([] if r["source_addition"] else ["current"])},
                actual=dict(PA=r["next_pa"],value=r["actual_relative_value"]),
                support=sup.filter(pl.col("row_id") == r["row_id"]).to_dicts(),
                peer_rule="Same origin, draft-time, upper-level category and listing; age/5, level PA/300, K/.1, BB+HR/.05, draft+rank/1; no outcomes",
                fewer_than_three_exact_peers=peers.height < 3,
                peers=peers.select("row_id","player_name","age",*PEER_FIELDS,"departure_pa","recent_pa","next_pa").to_dicts()))
    protections()
    save(PUBLIC/"player-walks.json",dict(cases=walks, cases_replayed_heads=4*len(walks),
        player_walkthrough_status="pending_judgment", hashes={str(stats_path):sha256_file(stats_path),str(OUT/"profile-support.parquet"):sha256_file(OUT/"profile-support.parquet")}))
    print(f"140 complete-cohort heads replayed; {len(walks)} player walks awaiting judgment",flush=True)


if __name__ == "__main__":
    main()
