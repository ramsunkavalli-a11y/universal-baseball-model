"""Compare a sealed source-only departure correction and walk every changed row."""
import gzip
from datetime import date
from pathlib import Path

import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

import audit_hitter_big_miss_groups as a
from evaluate_hitter_retirement_v44 import sources
from run_hitter_finite_return_baseline import protections, save
from universal_baseball.hitter_miss_groups import summary
from universal_baseball.reported_career_departure import departure, forecast
from universal_baseball.retirement_availability import events
from universal_baseball.storage import sha256_file

PUBLIC = a.ROOT / "reports/model-evidence/hitter-reported-departure"
OUT = a.ROOT / "reports/generated/hitter-reported-departure"
CONTROLS = [(474832, 2023), (518626, 2023), (458015, 2023), (680757, 2021),
            (665487, 2022), (677551, 2023), (682882, 2024), (475253, 2018)]


def scored(g, arm):
    s = summary(g, arm)
    p = g[arm + "_p"].to_numpy()
    y = (g["next_pa"].to_numpy() > 0).astype(float)
    clipped = np.clip(p, 1e-6, 1 - 1e-6)
    return dict(s, brier=float(np.mean((p - y) ** 2)),
                log_loss=float(-np.mean(y * np.log(clipped) + (1-y) * np.log(1-clipped))),
                model_implied_group_conditional_pa=s["predicted_pa"] / s["predicted_active"] if s["predicted_active"] else None)


def main():
    assert not PUBLIC.exists() and not OUT.exists()
    protections()
    completed = a.read(a.PUBLIC / "audit-completion.json")
    assert completed["player_walkthrough_status"] == "complete"
    a.verify(completed["hashes"])
    a.verify(a.read(a.PUBLIC / "audit-seal.json")["hashes"])
    config = a.ROOT / "config/hitter_reported_career_departures.json"
    reports = a.read(config)["reports"]
    captures = sources()
    jan = a.ROOT / "reports/generated/hitter-availability-2025-source/captures/transactions-2025-01.json.gz"
    with gzip.open(jan, "rt", encoding="utf8") as handle:
        import json
        payload = json.load(handle)
    captures.append((2025, jan, payload))
    records = events(captures, date(2025, 1, 24))
    paths = [Path(__file__), config, a.ROOT / "docs/hitter-reported-departure-contract.md",
             a.ROOT / "src/universal_baseball/reported_career_departure.py",
             a.ROOT / "tests/test_reported_career_departure.py",
             a.ROOT / "src/universal_baseball/retirement_availability.py",
             a.OUT / "audit-rows.parquet", a.PUBLIC / "audit-completion.json",
             *[p for _, p, _ in captures]]
    PUBLIC.mkdir(parents=True)
    OUT.mkdir(parents=True)
    save(PUBLIC / "source-seal.json", dict(before_corrected_scoring=True, new_fits=0,
         reports=reports, coverage="partial manual supplement; original publication-time captures not archived",
         hashes={str(p): sha256_file(p) for p in paths}))
    original = pl.read_parquet(a.OUT / "audit-rows.parquet").sort("row_id")
    assert original.height == 30519 and original["target_year"].max() == 2025
    statuses, changed, values = {}, [], []
    for r in original.iter_rows(named=True):
        status = departure(reports, records, player_id=r["player_id"],
                           cutoff=date.fromisoformat(r["ctx_information_date"]))
        old = {k: r["observation_" + k] for k in ["p", "conditional_pa", "pa", "rate", "value"]}
        fixed = forecast(old, status)
        statuses[r["row_id"]] = status
        diff = old != fixed
        if diff:
            changed.append(r["row_id"])
        values.append(dict(row_id=r["row_id"], departure_changed=diff,
                           departure_reported=status["reported_departure"],
                           **{"departure_" + k: v for k, v in fixed.items()}))
    q = original.join(pl.DataFrame(values), on="row_id", validate="1:1").sort("row_id")
    assert q.select(original.columns).equals(original)
    assert q["departure_rate"].equals(q["observation_rate"])
    assert q["departure_conditional_pa"].equals(q["observation_conditional_pa"])
    for field in ["p", "conditional_pa", "pa", "rate", "value"]:
        unchanged = q.filter(~pl.col("departure_changed"))
        assert unchanged["departure_" + field].equals(unchanged["observation_" + field])
    q.write_parquet(OUT / "predictions.parquet")
    selected = set(changed)
    report_pids = {r["player_id"] for r in reports}
    selected.update(q.filter(pl.col("player_id").is_in(report_pids))["row_id"])
    for pid, origin in CONTROLS:
        row = q.filter((pl.col("player_id") == pid) & (pl.col("origin_year") == origin))
        assert row.height == 1
        selected.add(row["row_id"].item())
    save(PUBLIC / "case-selection.json", dict(
        rules="Every changed row, every unchanged source-player row, eight fixed controls; not outcome-selected gains only",
        row_ids=sorted(selected), changed_row_ids=changed, future_results_used_for_selection=False))
    frames = [pl.read_parquet(a.BASE / f"features-{k}.parquet") for k in range(5)]
    fits = {(c["origin"], c["fold"]): c for c in a.read(a.BASE / "fit-report.json")["cells"]}
    statpath = a.ROOT / "reports/generated/practical-hitter-v31/dated-stints.parquet"
    stats = pl.read_parquet(statpath)
    walks = []
    replay_paths = [statpath, a.BASE / "fit-report.json", *[a.BASE / f"features-{k}.parquet" for k in range(5)]]
    with threadpool_limits(limits=2):
        for r in q.filter(pl.col("row_id").is_in(selected)).iter_rows(named=True):
            x = frames[r["outer_fold"]].filter(pl.col("row_id") == r["row_id"])
            heads = []
            for h in fits[r["origin_year"], r["outer_fold"]]["heads"]:
                path = a.ROOT / h["path"]
                assert sha256_file(path) == h["sha256"]
                replay_paths.append(path)
                model = joblib.load(path)
                z = x.select(h["features"]).to_numpy()
                v = float(model.predict_proba(z)[0, 1] if h["head"] == "participation" else model.predict(z)[0])
                column = "observation_raw_p" if h["head"] == "participation" else "observation_raw_conditional_pa"
                assert abs(v-r[column]) < 1e-10
                heads.append(dict(head=h["head"], raw_prediction=v, model_sha256=h["sha256"], training_people=h["training_people"]))
            peers = q.filter((pl.col("origin_year") == r["origin_year"]) &
                             (pl.col("career_group") == r["career_group"]) &
                             (pl.col("player_id") != r["player_id"])).with_columns(
                (((pl.col("age")-r["age"])/5)**2 + ((pl.col("pa_0")-r["pa_0"])/300)**2 +
                 (pl.col("last_MLB_quality")-r["last_MLB_quality"])**2).alias("distance")).sort("distance", "row_id").head(3)
            walks.append(dict(
                origin={k:r[k] for k in ["row_id", "player_id", "player_name", "origin_year", "target_year", "ctx_information_date", "age", "career_group", "outer_fold"]},
                stats=stats.filter((pl.col("player_id") == r["player_id"]) & pl.col("season").is_between(r["origin_year"]-2, r["origin_year"])).select("season", "bucket", "plate_appearances", "home_runs", "strike_outs", "base_on_balls").sort("season", "bucket").to_dicts(),
                inputs=x.select(fits[r["origin_year"], r["outer_fold"]]["heads"][0]["features"]).row(0, named=True),
                replayed_heads=heads, dated_departure=statuses[r["row_id"]],
                forecast={k:r[k] for k in q.columns if k.startswith("observation_") or k.startswith("departure_")},
                actual=dict(pa=r["next_pa"], batting_plus_replacement_value=r["actual_relative_value"]),
                peers=peers.select("row_id", "player_name", "age", "pa_0", "observation_pa", "departure_pa", "next_pa").to_dicts(),
                peer_rule="Same origin/career group nearest age/5, current MLB PA/300, last MLB quality; origin-only, not necessarily minor talent matches"))
    save(PUBLIC / "player-walks.json", dict(cases=walks, replayed_heads=2*len(walks),
         player_walkthrough_status="pending_judgment",
         hashes={str(p):sha256_file(p) for p in replay_paths}))
    scopes = [("all", q), ("past_MLB", q.filter(pl.col("prior_debut") > 0)),
              ("no_debut", q.filter(pl.col("prior_debut") == 0)),
              ("changed", q.filter(pl.col("departure_changed"))), ("unchanged", q.filter(~pl.col("departure_changed")))]
    for key in ["origin_year", "career_group"]:
        scopes += [(key+"="+str(v), q.filter(pl.col(key) == v)) for v in sorted(q[key].unique().to_list())]
    scores = [dict(scope=name, anchor=scored(part, "observation"), correction=scored(part, "departure"),
                   earlier_selected_reference=scored(part, "repaired_domestic")) for name, part in scopes]
    by_origin = [s for s in scores if s["scope"].startswith("origin_year=")]
    equal_origin = {arm: {metric: float(np.mean([s[arm][metric]**2 for s in by_origin])**.5)
                         for metric in ["pa_rmse", "value_rmse"]} for arm in ["anchor", "correction"]}
    protections()
    save(PUBLIC / "report.json", dict(rows=q.height, changed_rows=len(changed), new_fits=0,
         changed_people=q.filter(pl.col("departure_changed"))["player_id"].n_unique(),
         positive_actual_PA_changed=q.filter(pl.col("departure_changed") & (pl.col("next_pa") > 0)).height,
         scores=scores, equal_origin_RMSE=equal_origin, original_columns_bit_exact=True,
         uncovered_rows_bit_exact=True, conditional_PA_and_talent_unchanged=True,
         public_projection_comparison="Not available in this saved cohort; not substituted from another target/vintage",
         protected_outcomes_accessed=False, frozen_forecast_changed=False,
         player_walkthrough_status="pending_judgment", development_selected_not_independent=True,
         hashes={str(p):sha256_file(p) for p in [OUT / "predictions.parquet", PUBLIC / "source-seal.json", PUBLIC / "case-selection.json", PUBLIC / "player-walks.json"]}))
    print(f"Corrected {len(changed)} forecasts; walked {len(walks)} rows / {2*len(walks)} heads; judgment pending")
    print(scores[0])


if __name__ == "__main__":
    main()
