"""Fit the fixed confirmation recipes on identical historical cohorts."""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
from pathlib import Path
import warnings

import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

from universal_baseball.hitter_three_year_opportunity import (
    ORIGINS, arrival_probability, attach_cohorts, fit_benchmark, monotone_arrival,
    reconciliation_beta, training_rows, value_versions,
)
from universal_baseball.storage import sha256_file

BASE = Path("reports/generated/multiyear-hitter-v1")
PREVIOUS = Path("model_artifacts/hitter-role-workload-v1-2026-09-22")
V2 = Path("model_artifacts/multiyear-hitter-followup-v2-2026-09-22")
ANCHOR = Path("model_artifacts/hitter-anchored-development-v1-2026-09-22/historical-anchors.parquet")
OLD = Path("C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/universal-baseball-model/reports/generated")
DEBUT = OLD/"career-mlb-outcome-inventory-2009-2025/tables/people-debut-dates.parquet"
ROSTER = Path("reports/generated/hitter-roster-feature-challenger-v2/chronological-predictions.parquet")
OUT = Path("reports/generated/hitter-three-year-opportunity-v1")
PACKAGE = Path("model_artifacts/hitter-three-year-opportunity-v1-2026-09-22")
PLAN = Path("docs/hitter-three-year-opportunity-confirmation-v1-plan.md")


def save(path, obj):
    path.write_text(json.dumps(obj, indent=2, allow_nan=False)+"\n", encoding="utf-8", newline="\n")


def main():
    sources = [PLAN, Path(__file__).relative_to(Path.cwd()), BASE/"panel.parquet", BASE/"manifest.json",
        BASE/"outer-predictions.parquet", BASE/"targets.parquet", V2/"opportunity-predictions.parquet",
        V2/"forecast-2026-2028.parquet", ANCHOR, DEBUT, ROSTER, PREVIOUS/"predictions.parquet",
        Path("src/universal_baseball/hitter_three_year_opportunity.py"),
        Path("src/universal_baseball/hitter_model_tournament.py"),
        Path("src/universal_baseball/hitter_horizon_consistency.py"),
        Path("tests/test_hitter_three_year_opportunity.py")]
    hashes = {str(p): sha256_file(p) for p in sources}
    key = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()[:16]
    cache = OUT/"cache"/key
    cache.mkdir(parents=True, exist_ok=True)
    panel = attach_cohorts(pl.read_parquet(BASE/"panel.parquet").filter(pl.col("origin_year") <= 2022),
                          pl.read_parquet(DEBUT), pl.read_parquet(BASE/"targets.parquet"))
    features = json.loads((BASE/"manifest.json").read_text())["full_features"]
    assert len(features) == 77 and not set(features) & {"player_id", "origin_year", "prospect", "prior_debut"}
    history = pl.read_parquet(BASE/"outer-predictions.parquet")
    updates = pl.read_parquet(V2/"opportunity-predictions.parquet")
    anchors = pl.read_parquet(ANCHOR)
    earlier = pl.read_parquet(PREVIOUS/"predictions.parquet")
    fits, cold, notes = [], [], []
    keep = ["origin_year", "player_id", "age", "stage", "prior_debut", "prospect", "minor_returner", "recent_debut"]
    for cold_start, years in ((False, ORIGINS), (True, (2022,))):
        for year in years:
            for h in (1, 2, 3):
                path = cache/f"{year}-h{h}-{'cold' if cold_start else 'normal'}.parquet"
                note_path = path.with_suffix(".json")
                if path.exists() and note_path.exists():
                    result, note = pl.read_parquet(path), json.loads(note_path.read_text())
                else:
                    test = panel.filter(pl.col("origin_year") == year).sort("player_id")
                    excluded = test["player_id"].to_list() if cold_start else []
                    train = training_rows(panel, year, h, excluded)
                    assert train.height and train["origin_year"].max()+h <= year
                    if cold_start:
                        assert not set(train["player_id"]) & set(excluded)
                    print(f"Fitting {year} Year {h}, {'cold-start' if cold_start else 'usual history'}, {train.height} training rows", flush=True)
                    x, tx = train.select(features).to_numpy(), test.select(features).to_numpy()
                    fitted = fit_benchmark(x, train[f"pa_h{h}"].to_numpy(), tx)
                    labels = np.column_stack([train[f"pa_h{k}"].to_numpy() for k in range(1, h+1)]).sum(axis=1) > 0
                    arrival = fitted["candidate_p"] if h == 1 else arrival_probability(x, labels, tx)
                    result = test.select(*keep, pl.col(f"pa_h{h}").alias("actual_pa"),
                        pl.col(f"war_h{h}").alias("actual_value"))
                    result = result.with_columns(pl.lit(h).alias("horizon"),
                        pl.lit(year < 2020 <= year+h).alias("pandemic"),
                        pl.Series("arrival_raw", arrival),
                        *[pl.Series(k, v) for k, v in fitted.items()])
                    value_col = "year1" if h == 1 else f"selected_h{h}"
                    ref = history.filter(pl.col("origin_year") == year).select("player_id",
                        pl.col(f"activity_h{h}").alias("p0"), pl.col(f"expected_pa_h{h}").alias("pa0"),
                        pl.col(value_col).alias("delivered"), pl.col("year1").alias("reference_h1"))
                    update = updates.filter((pl.col("origin_year") == year) & (pl.col("horizon") == h)).select("player_id", "p1")
                    ref = ref.join(update, on="player_id", how="left", validate="1:1").with_columns(
                        pl.coalesce("p1", "p0").alias("accepted_p")).with_columns(
                        (pl.col("accepted_p")*pl.col("pa0")/pl.col("p0")).alias("accepted"))
                    result = result.join(ref.select("player_id", "accepted", "accepted_p", "delivered", "reference_h1"),
                        on="player_id", validate="1:1", maintain_order="left")
                    result = result.join(anchors, on=["origin_year", "player_id"], validate="1:1", maintain_order="left")
                    assert result["performance_anchor"].null_count() == 0
                    assert (result["latest_anchor_target"] <= year).all()
                    if h < 3 and not cold_start:
                        check = result.join(earlier.filter((pl.col("origin_year") == year) & (pl.col("horizon") == h)).select(
                            "player_id", "base", "base_p", pl.col("accepted").alias("previous_accepted")), on="player_id", validate="1:1")
                        assert check.height == result.height
                        for a, b in (("candidate", "base"), ("candidate_p", "base_p"), ("accepted", "previous_accepted")):
                            np.testing.assert_allclose(check[a], check[b], rtol=1e-10, atol=1e-9)
                    note = {"origin": year, "horizon": h, "cold_start": cold_start, "train_rows": train.height,
                        "train_origins": sorted(train["origin_year"].unique().to_list()), "last_target": int(train["origin_year"].max())+h,
                        "evaluation_rows": test.height, "train_players": train["player_id"].n_unique(),
                        "test_train_shared_players": len(set(train["player_id"]) & set(test["player_id"])),
                        "prior_screen_reproduced": h < 3 and not cold_start}
                    result.write_parquet(path)
                    save(note_path, note)
                (cold if cold_start else fits).append(result)
                notes.append(note)
                print(f"Ready: {year} Year {h} {'cold' if cold_start else 'normal'}", flush=True)
    frame = pl.concat(fits).sort("horizon", "origin_year", "player_id")
    reconciled, calibration = [], []
    for h in (1, 2, 3):
        pool = frame.filter(pl.col("horizon") == h)
        for year in ORIGINS:
            note = reconciliation_beta(pool, year, h)
            calibration.append(note)
            reconciled.append(value_versions(pool.filter(pl.col("origin_year") == year), note["beta"]))
    frame = pl.concat(reconciled).sort("origin_year", "player_id", "horizon")
    # Every player has the same three horizons, verified before grouping arrays.
    assert frame.group_by("origin_year", "player_id").len()["len"].min() == 3
    raw = frame["arrival_raw"].to_numpy().reshape(-1, 3)
    cumulative = monotone_arrival(raw).reshape(-1)
    actual_pa = frame["actual_pa"].to_numpy().reshape(-1, 3)
    arrived = np.maximum.accumulate(actual_pa > 0, axis=1).reshape(-1)
    frame = frame.with_columns(pl.Series("arrival_by_h", cumulative), pl.Series("actual_arrival_by_h", arrived))
    assert all(sha256_file(Path(p)) == digest for p, digest in hashes.items())
    OUT.mkdir(parents=True, exist_ok=True)
    frame.write_parquet(OUT/"predictions.parquet", compression="zstd", compression_level=10)
    pl.concat(cold).write_parquet(OUT/"cold-start.parquet", compression="zstd", compression_level=10)
    save(OUT/"fit-manifest.json", {"sources": hashes, "fingerprint": key, "fits": notes, "calibration": calibration,
        "versions": {n: importlib.metadata.version(n) for n in ("numpy", "polars", "scikit-learn", "lightgbm", "xgboost", "interpret")},
        "files": {n: sha256_file(OUT/n) for n in ("predictions.parquet", "cold-start.parquet")},
        "protected_outcomes_used": False, "forecasts_changed": False})
    print(json.dumps({"status": "fit_complete", "rows": frame.height, "fingerprint": key}), flush=True)


if __name__ == "__main__":
    warnings.filterwarnings("ignore", message="X does not have valid feature names")
    with threadpool_limits(limits=4):
        main()
