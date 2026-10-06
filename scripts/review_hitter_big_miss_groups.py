"""Complete origin/stat/fit walks and correct group conditional-mean accounting."""

from pathlib import Path

import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

import audit_hitter_big_miss_groups as a
from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import save, protections

CASES = [(680574, 2023), (665487, 2022), (425902, 2016), (677551, 2023),
         (680757, 2021), (668804, 2018), (592450, 2016), (592450, 2024),
         (448801, 2017), (474832, 2023), (596748, 2021), (682882, 2024),
         (656555, 2023), (475253, 2018)]


def main():
    target = a.PUBLIC / "audit-player-walks.json"
    assert not target.exists()
    audit = a.read(a.PUBLIC / "group-audit.json")
    a.verify(audit["hashes"])
    a.verify(a.read(a.PUBLIC / "audit-seal.json")["hashes"])
    pre = a.read(a.BASE / "preflight.json")
    a.verify(pre["hashes"])
    g = pl.read_parquet(a.OUT / "audit-rows.parquet")
    frames = [pl.read_parquet(a.BASE / f"features-{k}.parquet") for k in range(5)]
    profiles = pl.read_parquet(a.BASE / "profile-support.parquet")
    history_path = a.ROOT / "reports/generated/practical-hitter-v31/dated-stints.parquet"
    stats = pl.read_parquet(history_path)
    fits = {(c["origin"], c["fold"]): c for c in a.read(a.BASE / "fit-report.json")["cells"]}
    selection = []
    for pid, origin in CASES:
        row = g.filter((pl.col("player_id") == pid) & (pl.col("origin_year") == origin))
        assert row.height == 1
        selection.append(dict(row_id=row["row_id"].item(), player_id=pid, origin=origin))
    save(a.PUBLIC / "audit-walk-selection.json", dict(
        cases=selection, rule="diagnostic miss-pattern cases plus ordinary Smoak and DSL control; not independent confirmation"))
    cases, paths = [], [Path(__file__), history_path, a.BASE / "profile-support.parquet"]
    with threadpool_limits(limits=2):
        for chosen in selection:
            r = g.filter(pl.col("row_id") == chosen["row_id"]).row(0, named=True)
            f = frames[r["outer_fold"]]
            x = f.filter(pl.col("row_id") == r["row_id"])
            cell = fits[r["origin_year"], r["outer_fold"]]
            heads = []
            for h in cell["heads"]:
                p = a.ROOT / h["path"]
                assert sha256_file(p) == h["sha256"]
                paths.append(p)
                m = joblib.load(p)
                z = x.select(h["features"]).to_numpy()
                pred = float(m.predict_proba(z)[0, 1] if h["head"] == "participation" else m.predict(z)[0])
                col = "observation_raw_p" if h["head"] == "participation" else "observation_raw_conditional_pa"
                assert abs(pred - r[col]) < 1e-10
                heads.append(dict(head=h["head"], prediction=pred,
                    training_rows=h["training_rows"], training_people=h["training_people"],
                    model_sha256=h["sha256"]))
            history = stats.filter((pl.col("player_id") == r["player_id"]) & pl.col("season").is_between(r["origin_year"] - 2, r["origin_year"]))
            peers = g.filter((pl.col("origin_year") == r["origin_year"]) & (pl.col("career_group") == r["career_group"]) & (pl.col("player_id") != r["player_id"])).with_columns(
                (((pl.col("age") - r["age"]) / 5) ** 2
                 + ((pl.col("pa_0") - r["pa_0"]) / 300) ** 2
                 + (pl.col("last_MLB_quality") - r["last_MLB_quality"]) ** 2).alias("distance")
            ).sort("distance", "row_id").head(3)
            source_fields = [n for n in a.FIELDS if n != "row_id"] + [n for n in pre["job_features"] if n not in a.FIELDS]
            cases.append(dict(
                origin={k: r[k] for k in ["row_id", "player_id", "player_name", "origin_year", "target_year", "outer_fold", "ctx_information_date", "age", "stage", "career_group", "opportunity_group", "observation_state"]},
                stats=history.select("season", "bucket", "plate_appearances", "home_runs", "strike_outs", "base_on_balls").sort("season", "bucket").to_dicts(),
                actual_inputs=x.select(source_fields).row(0, named=True),
                replayed_heads=heads,
                actual_profile_support=profiles.filter((pl.col("row_id") == r["row_id"]) & (pl.col("arm") == "observation")).to_dicts(),
                forecast={k: r[k] for k in ["observation_p", "observation_conditional_pa", "observation_pa", "observation_rate", "origin_replacement_rate", "observation_value"]},
                actual={k: r[k] for k in ["next_pa", "actual_relative_value"]},
                signed_error_accounting={k: r[k] for k in ["pa_error", "value_error", "value_PA_term", "value_rate_term"]},
                peers=peers.select("row_id", "player_id", "player_name", "age", "pa_0", "observation_p", "observation_conditional_pa", "observation_pa", "next_pa", "observation_value", "actual_relative_value").to_dicts(),
                peer_rule="same origin and career group, nearest age/5,current PA/300,last MLB quality; no outcomes",
                inferred_medical_clearance=False,
            ))
    # Unweighted conditional predictions across everyone do not describe actual arrivals.
    # Correct model-implied group conditional PA: sum(p*C) / sum(p).
    calibration = []
    for s in audit["scores"]:
        p = s["predicted_active"]
        predicted_c = s["predicted_pa"] / p if p else None
        actual_c = s["actual_pa"] / s["actual_active"] if s["actual_active"] else None
        difference = s["predicted_pa"] - s["actual_pa"]
        arrival_term = (p - s["actual_active"]) * actual_c if actual_c is not None else None
        conditional_term = p * (predicted_c - actual_c) if predicted_c is not None and actual_c is not None else None
        if arrival_term is not None and conditional_term is not None:
            assert abs(arrival_term + conditional_term - difference) < 1e-8
        calibration.append(dict(group=s["group"], predicted_conditional_group_PA=predicted_c,
            actual_conditional_group_PA=actual_c, predicted_active=p, actual_active=s["actual_active"],
            predicted_pa=s["predicted_pa"], actual_pa=s["actual_pa"],
            descriptive_PA_arrival_term=arrival_term, descriptive_PA_conditional_term=conditional_term,
            unweighted_all_player_conditional_mean_not_comparable=True, causal_attribution=False))
    save(a.PUBLIC / "group-calibration-accounting.json", dict(
        groups=calibration, no_forecasts_substituted=True,
        identity="P*C - A*M = (P-A)*M + P*(C-M); descriptive accounting only",
        hashes={str(a.PUBLIC / "group-audit.json"): sha256_file(a.PUBLIC / "group-audit.json")}))
    protections()
    save(target, dict(cases=cases, replayed_heads=sum(len(c["replayed_heads"]) for c in cases),
        new_fits=0, player_walkthrough_status="pending_judgment",
        hashes={str(p): sha256_file(p) for p in [*paths, a.PUBLIC / "group-audit.json", a.PUBLIC / "audit-walk-selection.json", a.PUBLIC / "group-calibration-accounting.json"]}))
    print(f"Replayed {len(cases) * 2} actual heads for {len(cases)} player-origin walks; group PA accounting verified")


if __name__ == "__main__":
    main()
