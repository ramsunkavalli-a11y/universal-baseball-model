"""Finalize the source repair only after unchanged-cohort and walk checks."""
from pathlib import Path

import polars as pl

import audit_hitter_big_miss_groups as a
from evaluate_hitter_reported_departures import PUBLIC, OUT, scored
from run_hitter_finite_return_baseline import protections, save
from universal_baseball.storage import sha256_file


def main():
    assert not (PUBLIC / "completion.json").exists()
    report = a.read(PUBLIC / "report.json")
    a.verify(report["hashes"])
    walks = a.read(PUBLIC / "player-walks.json")
    a.verify(walks["hashes"])
    a.verify(a.read(PUBLIC / "source-seal.json")["hashes"])
    q = pl.read_parquet(OUT / "predictions.parquet")
    old = pl.read_parquet(a.OUT / "audit-rows.parquet").sort("row_id")
    assert q.select(old.columns).equals(old)
    assert q.height == report["rows"] == 30519
    changed = q.filter(pl.col("departure_changed"))
    assert changed.height == report["changed_rows"] == 7
    assert changed["next_pa"].sum() == 0
    assert set(changed["row_id"]) <= {c["origin"]["row_id"] for c in walks["cases"]}
    assert len(walks["cases"]) == 24 and walks["replayed_heads"] == 48
    for c in walks["cases"]:
        if c["forecast"]["departure_changed"]:
            s = c["dated_departure"]
            assert s["reported_departure"] and s["evidence"]
            assert s["evidence"]["known_date"] <= c["origin"]["ctx_information_date"]
            assert s["evidence"]["event_date"] <= c["origin"]["ctx_information_date"]
            assert c["stats"] and len(c["inputs"]) == 293
        assert len(c["replayed_heads"]) == 2
    for field in ["p", "conditional_pa", "pa", "rate", "value"]:
        untouched = q.filter(~pl.col("departure_changed"))
        assert untouched["observation_"+field].equals(untouched["departure_"+field])
    no_debut = q.filter(pl.col("prior_debut") == 0)
    assert no_debut.height == 24207 and not no_debut["departure_changed"].any()
    for arm in ["observation", "departure"]:
        assert abs(scored(q, arm)["pa_rmse"] - report["scores"][0]["anchor" if arm == "observation" else "correction"]["pa_rmse"]) < 1e-12
    cross = []
    for y in sorted(q["origin_year"].unique().to_list()):
        g = q.filter((pl.col("origin_year") == y) & (pl.col("career_group") == "no_debut_upper_minors"))
        cross.append(dict(origin=y, **scored(g, "observation")))
    save(PUBLIC / "upper-minor-origin-diagnosis.json", dict(groups=cross,
         same_fixed_cohort=True, pooled_shortfall_not_uniform_across_origins=True,
         causal_COVID_claim=False, new_fits=0))
    protections()
    paths = [Path(__file__), PUBLIC / "report.json", PUBLIC / "player-walks.json",
             PUBLIC / "upper-minor-origin-diagnosis.json",
             a.ROOT / "docs/hitter-reported-departure-result.md",
             a.ROOT / "docs/hitter-big-miss-group-origin-follow-up.md"]
    save(PUBLIC / "completion.json", dict(player_walkthrough_status="complete",
         execution_integrity="pass", source_coverage="partial primary-report supplement",
         baseball_reasonability="pass for seven dated affirmative departures; major other misses unresolved",
         predictive_evidence="small matched development improvement, not independent validation",
         disposition="retain source/status repair in research recipe; no deployment approval",
         milestone_complete=True, full_hitter_goal_complete=False,
         protected_outcomes_accessed=False, frozen_forecast_changed=False,
         hashes={str(p):sha256_file(p) for p in paths}))
    print("Departure checkpoint completed: seven corrected forecasts; 24 walks / 48 heads; frozen artifacts unchanged")


if __name__ == "__main__":
    main()
