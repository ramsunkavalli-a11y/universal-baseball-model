"""Append the reviewed disposition; never rewrite fitted/scored evidence."""
from pathlib import Path

import numpy as np
import polars as pl

import audit_hitter_big_miss_groups as a
from run_hitter_finite_return_baseline import protections, save
from test_hitter_recent_promotion import OUT, PUBLIC, REFERENCE
from universal_baseball.storage import sha256_file


def decision(scores, intervals):
    groups = {g["scope"]: g for g in scores}

    def change(scope, metric):
        g = groups[scope]
        key = "equal_origin_" + metric
        return g["recent"][key] / g["departure"][key] - 1

    recent_interval = next(i for i in intervals if i["scope"] == "never_recent"
                           and i["reference"] == "departure" and i["metric"] == "pa_mse")
    checks = dict(
        primary_PA_point_improves=change("never_recent", "pa_mse") < 0,
        recent_value_within_2pct=change("never_recent", "value_mse") <= .02,
        recent_Brier_within_2pct=change("never_recent", "brier") <= .02,
        recent_log_loss_within_2pct=change("never_recent", "log_loss") <= .02,
        recent_upper_PA_within_2pct=change("recent_upper", "pa_mse") <= .02,
        recent_lower_PA_within_2pct=change("recent_lower", "pa_mse") <= .02,
        six_non2021_PA_within_2pct=change("never_six_non2021", "pa_mse") <= .02,
        all_recent_origins_PA_within_10pct=all(change("never_origin="+str(y), "pa_mse") <= .10
                                             for y in [2022, 2023, 2024]),
        nominal_primary_interval_favors_improvement=recent_interval["upper"] < 0,
    )
    return checks


def main():
    assert not (PUBLIC / "completion.json").exists(), "Preserve completed evidence"
    protections()
    records = [OUT / "preflight.json", PUBLIC / "source-seal.json",
               PUBLIC / "training-weights.json", PUBLIC / "scores.json",
               PUBLIC / "player-walks.json"]
    for path in records:
        a.verify(a.read(path)["hashes"])
    pre = a.read(OUT / "preflight.json")
    fit = a.read(OUT / "fit-report.json")
    assert pre["before_fitting"] and pre["benchmark_heads_replayed"] == 70
    assert len(pre["cells"]) == len(fit["cells"]) == 35
    assert pre["head_checks"] == fit["new_fits"] == 70
    assert len(a.read(PUBLIC / "training-weights.json")["checks"]) == 70
    assert len(pre["features"]) == 293
    verified = 0
    for c in fit["cells"]:
        assert sha256_file(Path(c["path"])) == c["sha256"]
        assert {h["head"] for h in c["heads"]} == {"participation", "conditional_pa"}
        for h in c["heads"]:
            assert sha256_file(a.ROOT / h["path"]) == h["sha256"]
            assert h["features"] == pre["features"]
            assert abs(h["weight_sum"] - h["training_rows"]) < 1e-7
            assert h["latest_training_origin"] < c["origin"]
            verified += 1
    assert verified == 70
    q = pl.read_parquet(OUT / "predictions.parquet").sort("row_id")
    old = pl.read_parquet(REFERENCE).sort("row_id")
    assert sha256_file(OUT / "predictions.parquet") == fit["predictions_sha256"]
    assert q.height == q["row_id"].n_unique() == 30519 and q["target_year"].max() == 2025
    assert q.select(old.columns).equals(old)
    known = q.filter(pl.col("prior_debut") > 0)
    for n in ["p", "conditional_pa", "pa", "rate", "value"]:
        assert known["recent_"+n].equals(known["departure_"+n])
    assert q["recent_rate"].equals(q["departure_rate"])
    assert np.allclose(q["recent_pa"], q["recent_p"] * q["recent_conditional_pa"], rtol=0, atol=1e-10)
    assert np.allclose(q["recent_value"], q["recent_pa"] *
                       (q["recent_rate"] / 600 + q["origin_replacement_rate"]), rtol=0, atol=1e-10)
    profiles = pl.read_parquet(OUT / "profile-support.parquet")
    assert profiles.height == 61038
    assert profiles.group_by("row_id", "head").len()["len"].max() == 1
    scores = a.read(PUBLIC / "scores.json")
    assert scores["independent_head_replays"] == 140
    assert len(scores["intervals"]) == 8
    assert all(i["replicates"] == 2000 for i in scores["intervals"])
    checks = decision(scores["scores"], scores["intervals"])
    assert not checks["recent_lower_PA_within_2pct"]
    assert not checks["nominal_primary_interval_favors_improvement"]
    assert all(v for k, v in checks.items() if k not in ["recent_lower_PA_within_2pct",
                                                     "nominal_primary_interval_favors_improvement"])
    walks = a.read(PUBLIC / "player-walks.json")
    selected = a.read(PUBLIC / "case-selection.json")["cases"]
    assert len(walks["cases"]) == len(selected) == 12
    assert {c["origin"]["row_id"] for c in walks["cases"]} == {s["row_id"] for s in selected}
    assert walks["cases_replayed_heads"] == 48
    for c in walks["cases"]:
        assert len(c["actual_inputs"]) == 293
        assert len(c["saved_head_traces"]) == 4 and len(c["support"]) == 2 and c["stats"]
        assert len(c["peers"]) == (1 if c["origin"]["player_id"] == 694671 else 3)
        assert c["fewer_than_three_exact_peers"] == (len(c["peers"]) < 3)
        for arm in ["recent", "departure"]:
            r = c["forecasts"][arm]
            assert abs(r["pa"] - r["p"] * r["conditional_pa"]) < 1e-8
    review = a.ROOT / "docs/hitter-recent-promotion-result.md"
    assert review.exists() and review.stat().st_size > 10000
    protections()
    save(PUBLIC / "completion.json", dict(
        player_walkthrough_status="complete", reviewed_cases=12, cases_replayed_heads=48,
        all_cohort_head_replays=140, candidate_heads_hash_verified=70, forecast_rows=30519,
        statistical_checks=checks, statistical_replacement_pass=False,
        reasonability="Mixed: Chourio improves; thin advanced entrants and Quero remain/worsen; value not improved",
        disposition="Do not adopt; close exact four-year training decay, retain current forecast",
        deployment_approved=False, explorer_changed=False, selected_forecast_changed=False,
        broader_hitter_goal_complete=False, protected_outcomes_read=False,
        hashes={str(p): sha256_file(p) for p in [*records, PUBLIC / "case-selection.json",
            PUBLIC / "draft-cohorts.json", PUBLIC / "fit-seal.json", OUT / "fit-report.json",
            review, Path(__file__)]},
    ))
    print("Review complete: 12 walks/48 case heads, 140 cohort replays; candidate not adopted")


if __name__ == "__main__":
    main()
