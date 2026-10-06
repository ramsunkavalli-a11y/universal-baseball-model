"""Finalize reviewed saved-model diagnosis without fitting or changing forecasts."""
from pathlib import Path

import polars as pl

import audit_hitter_big_miss_groups as a
from audit_hitter_arrival_cohorts import OUT, PUBLIC
from run_hitter_finite_return_baseline import protections, save
from universal_baseball.storage import sha256_file


def main():
    completion = PUBLIC / "completion.json"
    assert not completion.exists(), "Preserve completed evidence"
    protections()
    report = a.read(PUBLIC / "report.json")
    a.verify(report["hashes"])
    seal = a.read(PUBLIC / "source-seal.json")
    a.verify(seal["hashes"])
    pre = a.read(a.BASE / "preflight.json")
    a.verify(pre["hashes"])
    fits = a.read(a.BASE / "fit-report.json")["cells"]
    assert len(fits) == len(pre["cells"]) == 35
    prepared = {(c["year"], c["fold"]): c for c in pre["cells"]}
    frames = [pl.read_parquet(a.BASE / f"features-{k}.parquet") for k in range(5)]
    verified_heads = 0
    for c in fits:
        y, k = c["origin"], c["fold"]
        p = prepared[y, k]
        f = frames[k]
        tr = f.filter(pl.col("row_id").is_in(p["training_row_ids"]))
        te = f.filter(pl.col("row_id").is_in(p["test_row_ids"]))
        assert tr["target_year"].max() <= y
        assert not (tr["target_year"] == 2020).any()
        assert not set(tr["player_id"]) & set(te["player_id"])
        assert {h["head"] for h in c["heads"]} == {"participation", "conditional_pa"}
        for h in c["heads"]:
            assert sha256_file(a.ROOT / h["path"]) == h["sha256"]
            assert h["features"] == pre["job_features"]
            sub = tr if h["head"] == "participation" else tr.filter(pl.col("next_pa") > 0)
            assert sub.height == h["training_rows"]
            assert sub["player_id"].n_unique() == h["training_people"]
            assert sub["target_year"].max() == h["maximum_training_target"]
            verified_heads += 1
    training = a.read(PUBLIC / "training-and-flag-use.json")
    a.verify(training["hashes"])
    assert len(training["flag_use"]) == 35
    profiles = pl.read_parquet(OUT / "profile-support.parquet")
    assert profiles.height == 2 * report["rows"] == 61038
    assert profiles.group_by("row_id", "head").len()["len"].max() == 1
    assert profiles.group_by("row_id").len()["len"].unique().to_list() == [2]
    warnings = []
    for y in sorted(profiles["origin"].unique().to_list()):
        for head in ["participation", "conditional_pa"]:
            part = profiles.filter((pl.col("origin") == y) & (pl.col("head") == head)
                                   & (pl.col("prior_debut") == 0))
            if y in [2021, 2022]:
                assert (part["calendar_readiness_people"] == 0).all()
            warnings.append(dict(origin=y, head=head, never_debut_rows=part.height,
                calendar_context_absent=part["calendar_context_absent"].sum(),
                calendar_under20_warning=part["calendar_context_under20_warning"].sum(),
                warning_not_proof_of_no_transfer=True))
    groups = a.read(PUBLIC / "cohort-calibration.json")["groups"]
    for g in groups:
        if g["descriptive_arrival_PA_term"] is not None:
            assert abs(g["descriptive_arrival_PA_term"] + g["descriptive_conditional_PA_term"]
                       - (g["predicted_pa"] - g["actual_pa"])) < 1e-8
    walks = a.read(PUBLIC / "player-walks.json")
    assert len(walks["cases"]) == report["cases"] == 12
    assert walks["replayed_heads"] == report["replayed_heads"] == 24
    for c in walks["cases"]:
        assert len(c["actual_inputs"]) == len(pre["job_features"]) == 293
        assert len(c["replayed_heads"]) == len(c["support"]) == 2
        assert c["stats"] and len(c["peers"]) == 3
        assert abs(c["forecast"]["observation_p"] * c["forecast"]["observation_conditional_pa"]
                   - c["forecast"]["observation_pa"]) < 1e-8
    review = a.ROOT / "docs/hitter-arrival-cohort-diagnosis-result.md"
    assert review.exists() and review.stat().st_size > 5000
    protections()
    save(completion, dict(player_walkthrough_status="complete", cases=12, replayed_heads=24,
        saved_heads_hash_verified=verified_heads, training_cells=35, historical_forecasts=30519,
        new_fits=0, forecast_changed=False, accuracy_gain_claimed=False,
        broader_hitter_goal_complete=False, protected_outcomes_read=False,
        disposition="Diagnosis and calendar-context reporting repair only; no new experiment or promotion",
        calendar_warnings=warnings,
        hashes={str(p): sha256_file(p) for p in [PUBLIC / "report.json", review, Path(__file__)]}))
    print("Review complete: 70 saved head hashes, 35 training cells, 12 walks; forecasts unchanged")


if __name__ == "__main__":
    main()
