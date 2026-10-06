"""No-fit readiness, calendar support and calibration diagnosis with saved walks."""
from pathlib import Path

import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

import audit_hitter_big_miss_groups as a
from evaluate_hitter_reported_departures import scored
from run_hitter_finite_return_baseline import protections, save
from universal_baseball.hitter_arrival_cohort_review import FIELDS, profiles, support, probability_bands
from universal_baseball.storage import sha256_file

PUBLIC = a.ROOT / "reports/model-evidence/hitter-arrival-cohort-diagnosis"
OUT = a.ROOT / "reports/generated/hitter-arrival-cohort-diagnosis"
CASES = [(680757, 2021), (665161, 2021), (677594, 2021), (677951, 2021),
         (680977, 2021), (664848, 2021), (640902, 2021), (668804, 2018),
         (682616, 2022), (694671, 2023), (701762, 2024)]
PEER_FIELDS = ["AAA_0_pa", "AA_0_pa", "Aplus_0_pa", "A_0_pa", "scout_rank_score_0", "draft_rank",
               *["pooled_"+b+"_"+ev for b in ["AAA", "AA", "Aplus", "A"] for ev in ["K", "BB", "HR"]]]


def describe(g):
    s = scored(g, "observation")
    p, active = s["predicted_active"], s["actual_active"]
    actual_c = s["actual_pa"] / active if active else None
    pred_c = s["model_implied_group_conditional_pa"]
    return dict(s, descriptive_arrival_PA_term=(p-active)*actual_c if actual_c is not None else None,
                descriptive_conditional_PA_term=p*(pred_c-actual_c) if pred_c is not None and actual_c is not None else None,
                causal_attribution=False)


def main():
    assert not PUBLIC.exists() and not OUT.exists()
    protections()
    a.verify(a.read(a.PUBLIC / "audit-completion.json")["hashes"])
    a.verify(a.read(a.ROOT / "reports/model-evidence/hitter-reported-departure/completion.json")["hashes"])
    pre = a.read(a.BASE / "preflight.json")
    a.verify(pre["hashes"])
    frames = [pl.read_parquet(a.BASE / f"features-{k}.parquet").sort("row_id") for k in range(5)]
    actual_fields = [n for n in [*FIELDS, *PEER_FIELDS] if n != "row_id"]
    actual_fields = list(dict.fromkeys(actual_fields))
    for f in frames[1:]:
        assert f.select("row_id", *actual_fields).equals(frames[0].select("row_id", *actual_fields))
    original = pl.read_parquet(a.OUT / "audit-rows.parquet").sort("row_id")
    assert original.height == 30519 and original["target_year"].max() == 2025
    source = frames[0]
    for key in ["age", "prior_debut", "origin_year", "player_id"]:
        assert original[key].equals(original.select("row_id").join(source.select("row_id", key), on="row_id", validate="1:1")[key])
    g = original.drop([n for n in actual_fields if n in original.columns]).join(
        source.select("row_id", *actual_fields), on="row_id", validate="1:1")
    g = probability_bands(profiles(g))
    assert g.select([n for n in original.columns if n not in actual_fields]).equals(original.select([n for n in original.columns if n not in actual_fields]))
    fits = {(c["origin"], c["fold"]): c for c in a.read(a.BASE / "fit-report.json")["cells"]}
    statpath = a.ROOT / "reports/generated/practical-hitter-v31/dated-stints.parquet"
    paths = [Path(__file__), a.ROOT / "docs/hitter-arrival-cohort-diagnosis-contract.md",
             a.ROOT / "src/universal_baseball/hitter_arrival_cohort_review.py",
             a.ROOT / "tests/test_hitter_arrival_cohort_review.py", statpath,
             a.BASE / "preflight.json", a.BASE / "fit-report.json", a.OUT / "audit-rows.parquet",
             *[a.BASE / f"features-{k}.parquet" for k in range(5)],
             *[a.ROOT / h["path"] for c in fits.values() for h in c["heads"]]]
    PUBLIC.mkdir(parents=True)
    OUT.mkdir(parents=True)
    save(PUBLIC / "source-seal.json", dict(new_fits=0, hashes={str(p):sha256_file(p) for p in paths}))
    supports, training, usage = [], [], []
    with threadpool_limits(limits=2):
        for c in pre["cells"]:
            y, k = c["year"], c["fold"]
            f = frames[k]
            tr = f.filter(pl.col("row_id").is_in(c["training_row_ids"])).sort("row_id")
            te = f.filter(pl.col("row_id").is_in(c["test_row_ids"])).sort("row_id")
            assert tr["target_year"].max() <= y and not (tr["target_year"] == 2020).any()
            assert not set(tr["player_id"]) & set(te["player_id"])
            for lag in range(3):
                assert tr["milb_canceled_"+str(lag)].equals((tr["origin_year"]-lag == 2020).cast(tr["milb_canceled_"+str(lag)].dtype))
            for head, sub in [("participation", tr), ("conditional_pa", tr.filter(pl.col("next_pa") > 0))]:
                sup = support(sub, te).with_columns(pl.lit(y).alias("origin"), pl.lit(k).alias("fold"), pl.lit(head).alias("head"))
                supports.append(sup)
                part = profiles(sub).filter(pl.col("prior_debut") == 0)
                training.extend(dict(origin=y, fold=k, head=head, **r) for r in part.group_by("origin_year", "calendar_context", "upper_now", "protected_listing").agg(
                    pl.len().alias("rows"), pl.col("player_id").n_unique().alias("people"),
                    (pl.col("next_pa") > 0).sum().alias("arrivals")).sort("origin_year", "upper_now", "protected_listing").to_dicts())
            h = next(h for h in fits[y, k]["heads"] if h["head"] == "participation")
            m = joblib.load(a.ROOT / h["path"])
            counts = np.zeros(len(h["features"]), dtype=int)
            for iteration in m._predictors:
                for tree in iteration:
                    for node in tree.nodes[tree.nodes["is_leaf"] == 0]:
                        counts[int(node["feature_idx"])] += 1
            notes = []
            for name in ["reorganized", "milb_canceled_0", "milb_canceled_1", "milb_canceled_2"]:
                j = h["features"].index(name)
                notes.append(dict(feature=name, training_unique=sorted(sub_value for sub_value in tr[name].unique().to_list()),
                                  test_unique=sorted(te[name].unique().to_list()), splits=int(counts[j])))
            usage.append(dict(origin=y, fold=k, flags=notes, causal_importance=False))
    all_support = pl.concat(supports)
    all_support.write_parquet(OUT / "profile-support.parquet")
    save(PUBLIC / "training-and-flag-use.json", dict(training=training, flag_use=usage,
          original_training_membership_preserved=True, no_target_2020=True,
          repaired_origin_2020_kept=True, hashes={str(OUT / "profile-support.parquet"):sha256_file(OUT / "profile-support.parquet")}))
    grouped = []
    never = g.filter(pl.col("prior_debut") == 0)
    for y in sorted(g["origin_year"].unique().to_list()):
        cohort = never.filter(pl.col("origin_year") == y)
        scopes = [("all_never_debut", cohort), ("upper", cohort.filter(pl.col("upper_now"))),
                  ("lower_or_other", cohort.filter(~pl.col("upper_now")))]
        upper = cohort.filter(pl.col("upper_now"))
        for key in ["upper_exposure", "upper_level", "protected_listing", "fresh_rank_positive", "probability_band"]:
            scopes += [(key+"="+str(v), upper.filter(pl.col(key) == v)) for v in sorted(upper[key].unique().to_list())]
        for label, piece in scopes:
            if piece.height:
                grouped.append(dict(origin=y, scope=label, **describe(piece)))
    save(PUBLIC / "cohort-calibration.json", dict(groups=grouped, new_fits=0,
         probabilities_known_at_origin=True, pooled_row_weighted_diagnostics=True))
    selected = []
    for pid, y in CASES:
        r = g.filter((pl.col("player_id") == pid) & (pl.col("origin_year") == y))
        assert r.height == 1 and r["prior_debut"].item() == 0
        selected.append(dict(row_id=r["row_id"].item(), reason="fixed_diagnostic"))
    upper = never.filter(pl.col("upper_now"))
    for sign, label in [(True, "largest_false_high"), (False, "largest_false_low")]:
        r = upper.sort(["pa_error", "row_id"], descending=[sign, False]).head(1)
        selected.append(dict(row_id=r["row_id"].item(), reason=label))
    save(PUBLIC / "case-selection.json", dict(cases=selected, diagnostic_not_independent=True))
    stats = pl.read_parquet(statpath)
    walks = []
    with threadpool_limits(limits=2):
        for r in g.filter(pl.col("row_id").is_in([x["row_id"] for x in selected])).iter_rows(named=True):
            x = frames[r["outer_fold"]].filter(pl.col("row_id") == r["row_id"])
            heads = []
            for h in fits[r["origin_year"], r["outer_fold"]]["heads"]:
                m = joblib.load(a.ROOT / h["path"])
                z = x.select(h["features"]).to_numpy()
                v = float(m.predict_proba(z)[0, 1] if h["head"] == "participation" else m.predict(z)[0])
                col = "observation_raw_p" if h["head"] == "participation" else "observation_raw_conditional_pa"
                assert abs(v-r[col]) < 1e-10
                heads.append(dict(head=h["head"], raw_prediction=v, model_sha256=h["sha256"], training_people=h["training_people"]))
            distance = ((pl.col("age")-r["age"])/5)**2
            for key in PEER_FIELDS:
                scale = 300 if key.endswith("_pa") else 1 if key in ["draft_rank", "scout_rank_score_0"] else .1 if key.endswith("_K") else .05
                distance += ((pl.col(key)-r[key])/scale)**2
            peers = never.filter((pl.col("origin_year") == r["origin_year"]) & (pl.col("upper_level") == r["upper_level"]) &
                                 (pl.col("protected_listing") == r["protected_listing"]) & (pl.col("player_id") != r["player_id"])).with_columns(
                                     distance.alias("distance")).sort("distance", "row_id").head(3)
            walks.append(dict(origin={n:r[n] for n in ["row_id", "player_id", "player_name", "origin_year", "ctx_information_date", "age", "stage", "upper_level", "upper_exposure", "protected_listing", "fresh_rank_positive", "calendar_context", "probability_band", "outer_fold"]},
                 stats=stats.filter((pl.col("player_id") == r["player_id"]) & pl.col("season").is_between(r["origin_year"]-2, r["origin_year"])).select("season", "bucket", "plate_appearances", "home_runs", "strike_outs", "base_on_balls").sort("season", "bucket").to_dicts(),
                 actual_inputs=x.select(pre["job_features"]).row(0, named=True), replayed_heads=heads,
                 support=all_support.filter(pl.col("row_id") == r["row_id"]).to_dicts(),
                 forecast={n:r[n] for n in ["observation_p", "observation_conditional_pa", "observation_pa", "observation_rate", "observation_value"]},
                 actual={n:r[n] for n in ["next_pa", "actual_relative_value"]},
                 error={n:r[n] for n in ["pa_error", "value_error", "value_PA_term", "value_rate_term"]},
                 peers=peers.select("row_id", "player_name", "age", *PEER_FIELDS, "observation_p", "observation_conditional_pa", "observation_pa", "next_pa").to_dicts(),
                 peer_rule="Same origin, current affiliated upper-level category, 40-man listing; nearest age/5, level PA/300, K/.1, BB+HR/.05, draft+rank/1; no outcomes"))
    save(PUBLIC / "player-walks.json", dict(cases=walks, replayed_heads=2*len(walks), player_walkthrough_status="pending_judgment"))
    protections()
    save(PUBLIC / "report.json", dict(rows=g.height, cases=len(walks), replayed_heads=2*len(walks), new_fits=0,
         forecast_changed=False, player_walkthrough_status="pending_judgment", protected_outcomes_read=False,
         hashes={str(p):sha256_file(p) for p in [PUBLIC / "source-seal.json", PUBLIC / "training-and-flag-use.json",
                 PUBLIC / "cohort-calibration.json", PUBLIC / "case-selection.json", PUBLIC / "player-walks.json"]}))
    print(f"Audited 35 unchanged training cells and {len(walks)} player-origins; no fits or forecasts changed")


if __name__ == "__main__":
    main()
