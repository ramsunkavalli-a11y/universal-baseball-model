"""Run the single predeclared league PA allocation screen; no forecast writes."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.hitter_horizon_consistency import fixed_groups
from universal_baseball.hitter_league_allocation import (
    allocate, budget_at_cutoff, calibration, losses,
)
from universal_baseball.hitter_opportunity_calendar import mean_origin
from universal_baseball.multiyear_hitter_followup import compare_losses
from universal_baseball.storage import sha256_file

BASE = Path("reports/generated/multiyear-hitter-v1")
PREVIOUS = Path("model_artifacts/hitter-opportunity-calendar-v1-2026-09-22")
CURRENT = Path("model_artifacts/multiyear-hitter-followup-v2-2026-09-22/forecast-2026-2028.parquet")
PLAN = Path("docs/hitter-league-allocation-v1-plan.md")
OUT = Path("model_artifacts/hitter-league-allocation-v1-2026-09-22")
ORIGINS = [2018, 2019, 2021, 2022]


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+"\n", encoding="utf-8", newline="\n")


def summary(frame, paired=False):
    result = {"rows": frame.height, "origins": sorted(frame["origin_year"].unique().to_list()),
              "actual_mean_pa": mean_origin(frame, "pa_h2"), "forms": {}}
    for form in ("baseline", "uniform", "candidate"):
        result["forms"][form] = {"pa_rmse": float(np.sqrt(mean_origin(frame, form+"_pa_loss"))),
            "pa_mae": mean_origin(frame, form+"_pa_mae"), "pa_bias": mean_origin(frame, form+"_error"),
            "value_rmse": float(np.sqrt(mean_origin(frame, form+"_value_loss")))}
    result["delivered_direct_value_rmse"] = float(np.sqrt(mean_origin(frame, "direct_value_loss")))
    if paired:
        result["paired"] = {target: compare_losses(frame, "candidate_"+target+"_loss", "baseline_"+target+"_loss")
                            for target in ("pa", "value")}
    return result


def evaluate(frame):
    groups = {"overall": np.ones(frame.height, dtype=bool), **fixed_groups(frame)}
    output = {}
    for scope, mask in (("all", np.ones(frame.height, dtype=bool)),
                        ("ordinary", frame["origin_year"].is_in([2021, 2022]).to_numpy()),
                        *[(str(y), (frame["origin_year"] == y).to_numpy()) for y in ORIGINS]):
        output[scope] = {name: summary(frame.filter(mask & group),
            paired=scope in ("all", "ordinary") and name in ("overall", "Top50", "Top50 under26"))
            for name, group in groups.items() if (mask & group).any()}
    return output


def verify():
    manifest = json.loads((OUT/"manifest.json").read_text())
    for name, digest in manifest["sources"].items():
        assert sha256_file(Path(name)) == digest, name
    for name, digest in manifest["files"].items():
        assert sha256_file(OUT/name) == digest, name
    f = pl.read_parquet(OUT/"predictions.parquet")
    assert f.unique(["origin_year", "player_id"]).height == f.height
    assert sorted(f["origin_year"].unique().to_list()) == ORIGINS
    assert (f["candidate_pa"] >= 0).all()
    assert (f["candidate_pa"] <= f["old_p"]*800+1e-8).all()
    np.testing.assert_allclose(f["baseline_pa"], f["old_p"]*f["old_q"])
    np.testing.assert_allclose(f["candidate_value"], f["candidate_pa"]*f["performance_anchor"]/600)
    report = json.loads((OUT/"report.json").read_text())
    for ledger in report["ledgers"]:
        y = ledger["origin"]
        assert max(ledger["budget"]["pool_years"]) <= y
        assert all(r["target"] <= y for r in ledger["budget"]["reserve_support"])
        assert all(max(r["origins"])+2 <= y for r in ledger["calibration"])
        g = f.filter(pl.col("origin_year") == y)
        np.testing.assert_allclose(g["candidate_pa"].sum()+ledger["slack"], ledger["budget"]["named_budget"])
    assert not report["forecast_changed"] and not report["protected_outcomes_used"]
    print(json.dumps({"status": "verified", "rows": f.height, "forecast_changed": False}))


def main():
    prior = json.loads((PREVIOUS/"manifest.json").read_text())
    for name, digest in prior["files"].items():
        assert sha256_file(PREVIOUS/name) == digest, name
    sources = [PLAN, Path(__file__).relative_to(Path.cwd()), Path("tests/test_hitter_league_allocation.py"),
        *[Path("src/universal_baseball")/name for name in ("hitter_league_allocation.py",
            "hitter_horizon_consistency.py", "hitter_opportunity_calendar.py", "multiyear_hitter_followup.py")],
        BASE/"panel.parquet", BASE/"targets.parquet", BASE/"schedules.parquet",
        PREVIOUS/"manifest.json", PREVIOUS/"scored-rows.parquet", CURRENT]
    hashes = {str(p): sha256_file(p) for p in sources}
    history = pl.read_parquet(PREVIOUS/"scored-rows.parquet").select(
        "origin_year", "player_id", "stage", "age", "pa_00", "old_p", "old_q",
        "performance_anchor", "pa_h2", "war_h2", "reference_h1", "reference_h2"
    ).sort(["origin_year", "player_id"])
    panel, targets, schedules = [pl.read_parquet(BASE/(name+".parquet")) for name in ("panel", "targets", "schedules")]
    assert targets["season"].max() <= 2025 and schedules["season"].max() <= 2025
    assert targets.unique(["season", "player_id"]).height == targets.height
    frames, ledgers = [], []
    for y in ORIGINS:
        records = calibration(history, y)
        budget = budget_at_cutoff(panel, targets, schedules, y)
        test = history.filter(pl.col("origin_year") == y)
        cohort = panel.filter(pl.col("origin_year") == y)
        assert set(test["player_id"]) == set(cohort["player_id"])
        g = losses(allocate(test, records, budget["named_budget"]))
        actual = targets.filter(pl.col("season") == y+2)
        outside = actual.join(test.select("player_id"), on="player_id", how="anti")
        np.testing.assert_allclose(g["pa_h2"].sum()+outside["mlb_pa"].sum(), actual["mlb_pa"].sum())
        np.testing.assert_allclose(g["war_h2"].sum()+outside["component_war"].sum(), actual["component_war"].sum())
        # Future outcomes are used only below for evaluation, never allocation.
        ledger = {"origin": y, "target": y+2, "budget": budget, "calibration": records,
            "actual_league_pa": float(actual["mlb_pa"].sum()), "actual_named_pa": float(g["pa_h2"].sum()),
            "actual_outside_pa": float(outside["mlb_pa"].sum()),
            "actual_outside_partial_value": float(outside["component_war"].sum()),
            "reserve_error": budget["reserve_pa"]-float(outside["mlb_pa"].sum()),
            "predicted_named_pa": {form: float(g[form+"_pa"].sum()) for form in ("baseline", "uniform", "candidate")},
            "slack": max(0., budget["named_budget"]-float(g["candidate_pa"].sum())),
            "capped_players": int((g["candidate_pa"] >= g["old_p"]*800-1e-8).sum()),
            "by_allocation_group": {name: summary(g.filter(pl.col("allocation_group") == name))
                                    for name in sorted(g["allocation_group"].unique())}}
        ledgers.append(ledger)
        frames.append(g)
        print(f"Completed fixed allocation: origin {y}, calibration {sorted({v for r in records for v in r['origins']})}", flush=True)
    scored = pl.concat(frames).sort(["origin_year", "player_id"])
    results = evaluate(scored)
    ordinary = results["ordinary"]["overall"]["paired"]
    guards = {name: results["ordinary"][name]["forms"]["candidate"]["pa_rmse"]
              <= results["ordinary"][name]["forms"]["baseline"]["pa_rmse"]
              and results["ordinary"][name]["forms"]["candidate"]["value_rmse"]
              <= results["ordinary"][name]["forms"]["baseline"]["value_rmse"]
              for name in ("Top50", "Top50 under26")}
    gates = {"three_ordinary_origins": len(results["ordinary"]["overall"]["origins"]) >= 3,
             "pa_confident_improvement": ordinary["pa"]["interval95"][1] < 0,
             "value_confident_improvement": ordinary["value"]["interval95"][1] < 0,
             "pa_majority": ordinary["pa"]["improving_origins"] > len(ordinary["pa"]["folds"])/2,
             "value_majority": ordinary["value"]["improving_origins"] > len(ordinary["value"]["folds"])/2,
             **guards}
    report = {"status": "screen_complete_no_promotion", "forecast_changed": False,
        "protected_outcomes_used": False, "results": results, "ledgers": ledgers, "gates": gates,
        "limits": ["Two ordinary evaluation years; exposed development evidence",
            "Player bootstrap conditions on seasons and fitted calibration", "Batting plus replacement, not full WAR",
            "Fixed-anchor opportunity comparison is not the delivered direct-value model",
            "No current forecast generated; no allocation or batting rate changed in explorer",
            "Stage and expected-PA groups do not identify a causal source of errors"]}
    assert all(sha256_file(Path(name)) == digest for name, digest in hashes.items())
    OUT.mkdir(parents=True, exist_ok=True)
    scored.write_parquet(OUT/"predictions.parquet")
    write_json(OUT/"report.json", report)
    write_json(OUT/"manifest.json", {"sources": hashes, "files": {name: sha256_file(OUT/name)
        for name in ("predictions.parquet", "report.json")}, "forecast_changed": False, "protected_outcomes_used": False})
    print(json.dumps({"ordinary": results["ordinary"]["overall"], "gates": gates}, indent=2))
    verify()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    if parser.parse_args().verify:
        verify()
    else:
        main()
