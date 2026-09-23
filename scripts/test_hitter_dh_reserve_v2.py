"""Screen a fixed DH-aware reserve; reconstruct one additional accepted replay."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from evaluate_multiyear_hitter_followup_v2 import SOURCE, established_features, p_matrix
from evaluate_multiyear_hitter_v1 import opportunity
from test_hitter_league_allocation_v1 import summary, write_json
from universal_baseball.hitter_contract_reserve import dh_budget
from universal_baseball.hitter_horizon_consistency import fixed_groups
from universal_baseball.hitter_league_allocation import allocate, calibration, losses
from universal_baseball.multiyear_hitter_followup import compare_losses, opportunity_mask
from universal_baseball.storage import sha256_file

BASE = Path("reports/generated/multiyear-hitter-v1")
PREVIOUS = Path("model_artifacts/hitter-opportunity-calendar-v1-2026-09-22")
ANCHORS = Path("model_artifacts/hitter-anchored-development-v1-2026-09-22/historical-predictions.parquet")
CURRENT = Path("model_artifacts/multiyear-hitter-followup-v2-2026-09-22/forecast-2026-2028.parquet")
PITCH = SOURCE.with_name("mlb_pitching_2009_2025.parquet")
OUT = Path("model_artifacts/hitter-contract-reserve-v2-2026-09-22")
PLAN = Path("docs/hitter-contract-reserve-v2-plan.md")


def accepted_replay(panel, augmented, year):
    baseline = opportunity(panel, year, 2, False).select("player_id",
        pl.col("predicted_any_mlb_pa_probability").alias("base_p"),
        pl.col("predicted_positive_mlb_pa_mean").alias("old_q"))
    train = augmented.filter(pl.Series(opportunity_mask(augmented, year, 2)))
    test = augmented.filter((pl.col("origin_year") == year) & pl.col("established"))
    model = make_pipeline(StandardScaler(), LogisticRegression(C=1., max_iter=2000, random_state=417))
    model.fit(p_matrix(train, 2), train["pa_h2"].to_numpy() > 0)
    updated = test.select("player_id").with_columns(pl.Series("updated_p", model.predict_proba(p_matrix(test, 2))[:, 1]))
    result = baseline.join(updated, on="player_id", how="left", validate="1:1").with_columns(
        pl.coalesce("updated_p", "base_p").alias("old_p"), pl.lit(year).alias("origin_year"))
    result = result.with_columns((pl.col("old_p")*pl.col("old_q")).alias("pa_00"))
    return result.select("origin_year", "player_id", "old_p", "old_q", "pa_00"), {
        "origin": year, "established_train_rows": train.height, "established_test_rows": test.height,
        "latest_established_training_target": int(train["origin_year"].max())+2,
        "recipe": "unchanged PT_FORM_U plus accepted established P1 probability"}


def verify():
    manifest = json.loads((OUT/"reserve-manifest.json").read_text())
    for path, digest in manifest["sources"].items():
        assert sha256_file(Path(path)) == digest, path
    for name, digest in manifest["files"].items():
        assert sha256_file(OUT/name) == digest, name
    f = pl.read_parquet(OUT/"reserve-predictions.parquet")
    assert sorted(f["origin_year"].unique().to_list()) == [2022, 2023]
    assert f.unique(["origin_year", "player_id"]).height == f.height
    np.testing.assert_allclose(f["baseline_pa"], f["old_p"]*f["old_q"])
    np.testing.assert_allclose(f["candidate_value"], f["candidate_pa"]*f["performance_anchor"]/600)
    assert (f["candidate_pa"] >= 0).all() and (f["candidate_pa"] <= f["old_p"]*800+1e-8).all()
    report = json.loads((OUT/"reserve-report.json").read_text())
    for ledger in report["ledgers"]:
        y, b = ledger["origin"], ledger["budget"]
        assert max(b["pool_years"]) <= y and all(r["target"] <= y for r in b["reserve_support"])
        assert all(max(r["origins"])+2 <= y for r in ledger["calibration"])
        assert all(r["other_pa"]+r["pitcher_proxy_pa"] == r["outside_pa"] for r in b["reserve_support"])
        np.testing.assert_allclose(f.filter(pl.col("origin_year") == y)["candidate_pa"].sum()+ledger["slack"], b["named_budget"])
    assert report["replay_2022_validated"] and not report["forecast_changed"] and not report["protected_outcomes_used"]
    print(json.dumps({"status": "verified", "rows": f.height, "forecast_changed": False}))


def main():
    sources = [PLAN, Path(__file__).relative_to(Path.cwd()), SOURCE, PITCH, ANCHORS, CURRENT,
        PREVIOUS/"manifest.json", PREVIOUS/"scored-rows.parquet", BASE/"panel.parquet", BASE/"targets.parquet", BASE/"schedules.parquet",
        *[Path("scripts")/p for p in ("evaluate_multiyear_hitter_v1.py", "evaluate_multiyear_hitter_followup_v2.py", "audit_established_hitter_opportunity.py", "test_hitter_league_allocation_v1.py")],
        *[Path("src/universal_baseball")/p for p in ("hitter_contract_reserve.py", "hitter_league_allocation.py", "hitter_horizon_consistency.py", "hitter_opportunity_calendar.py", "multiyear_hitter_followup.py", "multiyear_hitter_value.py", "playing_time_model.py", "opportunity_model_v2.py")],
        Path("tests/test_hitter_contract_reserve.py")]
    hashes = {str(p): sha256_file(p) for p in sources}
    manifest = json.loads((PREVIOUS/"manifest.json").read_text())
    assert sha256_file(PREVIOUS/"scored-rows.parquet") == manifest["files"]["scored-rows.parquet"]
    panel, targets, schedules = [pl.read_parquet(BASE/(p+".parquet")) for p in ("panel", "targets", "schedules")]
    pitching = pl.read_parquet(PITCH)
    assert targets["season"].max() <= 2025 and pitching["season"].max() <= 2025
    history = pl.read_parquet(PREVIOUS/"scored-rows.parquet").select("origin_year", "player_id", "age", "stage", "pa_00", "old_p", "old_q", "performance_anchor", "pa_h2", "war_h2", "reference_h1", "reference_h2")
    augmented = established_features(panel)
    notes = []
    with threadpool_limits(limits=4):
        for y in [2022, 2023]:
            replay, note = accepted_replay(panel, augmented, y)
            notes.append(note)
            if y == 2022:
                check = replay.join(history.filter(pl.col("origin_year") == y), on=["origin_year", "player_id"], validate="1:1", suffix="_saved")
                assert check.height == replay.height
                for col in ("old_p", "old_q", "pa_00"):
                    np.testing.assert_allclose(check[col], check[col+"_saved"], rtol=1e-8, atol=1e-7)
            else:
                anchors = pl.read_parquet(ANCHORS).filter(pl.col("origin_year") == y)
                added = anchors.select("origin_year", "player_id", "age", "stage", "performance_anchor", "pa_h2", "war_h2", "reference_h1", "reference_h2").join(replay, on=["origin_year", "player_id"], validate="1:1")
                assert added.height == replay.height
                history = pl.concat([history, added.select(history.columns)], how="vertical_relaxed")
            print(f"Accepted opportunity replay complete: {y}", flush=True)
    history = history.sort(["origin_year", "player_id"])
    frames, ledgers = [], []
    for y in [2022, 2023]:
        budget = dh_budget(panel, targets, schedules, pitching, y)
        records = calibration(history, y)
        test = history.filter(pl.col("origin_year") == y)
        original = losses(allocate(test, records, budget["old_named_budget"]))
        corrected = losses(allocate(test, records, budget["named_budget"]))
        corrected = corrected.join(original.select("origin_year", "player_id", *[
            pl.col("candidate_"+c).alias("oldreserve_"+c) for c in ("pa", "value", "pa_loss", "value_loss")]),
            on=["origin_year", "player_id"], validate="1:1").sort(["origin_year", "player_id"])
        actual = targets.filter(pl.col("season") == y+2)
        outsider = actual.join(test.select("player_id"), on="player_id", how="anti")
        np.testing.assert_allclose(corrected["pa_h2"].sum()+outsider["mlb_pa"].sum(), actual["mlb_pa"].sum())
        ledgers.append({"origin": y, "target": y+2, "budget": budget, "calibration": records,
            "actual_outside_pa": int(outsider["mlb_pa"].sum()),
            "reserve_error": budget["reserve_pa"]-int(outsider["mlb_pa"].sum()),
            "actual_named_pa": int(corrected["pa_h2"].sum()),
            "baseline_named_pa": float(corrected["baseline_pa"].sum()),
            "corrected_named_pa": float(corrected["candidate_pa"].sum()),
            "slack": max(0., budget["named_budget"]-float(corrected["candidate_pa"].sum()))})
        frames.append(corrected)
    frame = pl.concat(frames).sort(["origin_year", "player_id"])
    groups = {"overall": np.ones(frame.height, bool), **fixed_groups(frame)}
    results = {}
    for name, mask in groups.items():
        f = frame.filter(mask)
        if f.is_empty():
            continue
        rec = summary(f, paired=name in ("overall", "Top50", "Top50 under26"))
        rec["versus_original_reserve"] = {t: compare_losses(f, "candidate_"+t+"_loss", "oldreserve_"+t+"_loss") for t in ("pa", "value")}
        rec["per_origin"] = {str(y): summary(f.filter(pl.col("origin_year") == y)) for y in [2022, 2023] if f.filter(pl.col("origin_year") == y).height}
        results[name] = rec
    paired = results["overall"]["paired"]
    gates = {"three_rule_known_origins": False,
        **{t+"_confident_improvement": paired[t]["interval95"][1] < 0 for t in ("pa", "value")},
        **{t+"_majority": paired[t]["improving_origins"] == 2 for t in ("pa", "value")},
        **{g+"_guard": all(results[g]["forms"]["candidate"][k] <= results[g]["forms"]["baseline"][k] for k in ("pa_rmse", "value_rmse")) for g in ("Top50", "Top50 under26")}}
    report = {"status": "screen_complete_not_promoted", "replay_2022_validated": True, "fit_notes": notes,
        "results": results, "ledgers": ledgers, "gates": gates, "forecast_changed": False, "protected_outcomes_used": False,
        "limits": ["Two rule-known development origins", "Approximate pitcher classification, not exact appearance role",
            "Fixed batting-plus-replacement anchor; not full WAR or delivered direct-value means",
            "Player-cluster intervals condition on seasons and fitted calibration", "No contract feature fit without source gate"]}
    assert all(sha256_file(Path(p)) == digest for p, digest in hashes.items())
    OUT.mkdir(parents=True, exist_ok=True)
    frame.write_parquet(OUT/"reserve-predictions.parquet")
    history.filter(pl.col("origin_year") == 2023).write_parquet(OUT/"accepted-opportunity-replay-2023.parquet")
    write_json(OUT/"reserve-report.json", report)
    write_json(OUT/"reserve-manifest.json", {"sources": hashes, "files": {name: sha256_file(OUT/name) for name in
        ("reserve-predictions.parquet", "accepted-opportunity-replay-2023.parquet", "reserve-report.json")}})
    print(json.dumps({"overall": results["overall"], "gates": gates}, indent=2))
    verify()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    if parser.parse_args().verify:
        verify()
    else:
        main()
