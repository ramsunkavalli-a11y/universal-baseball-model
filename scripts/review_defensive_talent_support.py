"""Complete the coverage audit with arithmetic replay and extra origin-selected DSL cases."""

from math import isclose
from pathlib import Path

import polars as pl

from audit_defensive_talent_support import (
    BASE, OLD, OUT, PUBLIC, ROOT, indexed, peer_ids, read, verify,
)
from run_hitter_finite_return_baseline import protections, save
from universal_baseball.defensive_talent_support import profile, training_snapshot, window_label
from universal_baseball.storage import sha256_file


def main():
    protections()
    report = read(OUT / "report.json")
    verify(report["hashes"])
    verify(report["artifact_hashes"])
    labels = pl.read_parquet(OUT / "labels.parquet")
    origins = pl.read_parquet(OUT / "origins.parquet")
    annual = pl.read_parquet(OLD / "annual.parquet")
    official = indexed(pl.read_parquet(BASE / "official-position-history.parquet"))
    raw = pl.concat([
        pl.read_parquet(BASE / f"native-source/fielding-{y}.parquet", columns=[
            "id", "name", "range_runs", "outs_total", *[f"outs_{p}" for p in range(2, 10)]
        ]).with_columns(pl.lit(y).alias("season")) for y in range(2016, 2026)
    ])
    native = indexed(raw, "id")
    walk = read(OUT / "player-traces.json")
    origin_rows = origins.to_dicts()
    label_rows = labels.to_dicts()
    # This supplementary sample uses only 2016 source exposure, not later outcomes.
    dsl = origins.filter(
        (pl.col("origin_year") == 2016) & (pl.col("position") == 6)
        & (pl.col("dsl_ground_balls") >= 100)
        & (pl.col("dsl_ground_balls") / pl.col("ground_balls") >= .8)
    ).sort(["dsl_ground_balls", "player_id"], descending=[True, False]).head(3).to_dicts()
    supplemental = []
    for row in dsl:
        traces = []
        for peer in [row] + peer_ids(row, origin_rows):
            windows = []
            for horizon in (3, 5, 7):
                label, path = window_label(peer, horizon, native, official)
                stats, counts = training_snapshot(label_rows, peer["origin_year"], peer["player_id"] % 5, horizon)
                windows.append({"label": label, "annual_path": path, "actual_fold_support": stats,
                                "matching_training_people": len(counts.get(profile(peer), set()))})
            minor = annual.filter((pl.col("player_id") == peer["player_id"]) & (pl.col("position") == peer["position"]) & pl.col("season").is_between(peer["origin_year"] - 2, peer["origin_year"])).sort("season", "level", "league_id").to_dicts()
            traces.append({"origin_inputs": peer, "minor_annual_evidence": minor, "windows": windows})
        supplemental.append({"player_id": row["player_id"], "origin_year": 2016,
                             "focal_and_origin_known_peers": traces})
    walk["supplemental_dsl_selection"] = "Three largest 2016 SS DSL weighted exposures, minimum 100 and at least 80% DSL; ties by ID. Diagnostic selection after aggregate coverage, without future player quality. Peers use the original age/level/position/exposure rule."
    walk["supplemental_dsl_cases"] = supplemental
    # Replay all origin inputs using annual rows, independently of the pooling helper.
    evidence = {}
    for r in annual.iter_rows(named=True):
        evidence.setdefault((r["player_id"], r["position"]), []).append(r)
    for r in origin_rows:
        history = [a for a in evidence[(r["player_id"], r["position"])] if r["origin_year"] - 2 <= a["season"] <= r["origin_year"]]
        for col in ("ground_balls", "credits", "touches", "expected_credits", "legacy_expected_credits"):
            expected = sum(a[col] * .5 ** (r["origin_year"] - a["season"]) for a in history)
            assert isclose(r[col], expected, rel_tol=1e-10, abs_tol=1e-10), (r["player_id"], col)
        residual = (r["credits"] - r["expected_credits"]) / (r["ground_balls"] + 600)
        assert isclose(residual, r["complete_rate"], rel_tol=1e-10, abs_tol=1e-10)
    # Replay every label, including censoring, against unchanged raw sources.
    for r in label_rows:
        replay, _ = window_label(r, r["horizon"], native, official)
        for key in ("quality_rate", "quality_status", "same_position_seasons", "same_position_outs",
                    "window_mature", "future_official_outs", "infield_group_quality_available"):
            assert replay[key] == r[key], (r["player_id"], r["origin_year"], r["horizon"], key)
    profiles = labels.filter(pl.col("window_mature") & ~pl.col("prior_mlb_defense")).group_by("horizon", "level").agg(
        pl.len().alias("player_position_rows"), pl.col("player_id").n_unique().alias("people"),
        pl.col("player_id").filter(pl.col("quality_rate").is_not_null()).n_unique().alias("same_position_quality_people"),
        pl.col("player_id").filter(pl.col("infield_group_quality_available")).n_unique().alias("infield_group_quality_people"),
    ).sort("horizon", "level", nulls_last=True).to_dicts()
    dsl_coverage = labels.filter(pl.col("window_mature") & (pl.col("dsl_ground_balls") > 0) & ~pl.col("prior_mlb_defense")).group_by("horizon").agg(
        pl.len().alias("player_position_rows"), pl.col("player_id").n_unique().alias("people"),
        pl.col("player_id").filter(pl.col("quality_rate").is_not_null()).n_unique().alias("same_position_quality_people"),
        pl.col("player_id").filter(pl.col("infield_group_quality_available")).n_unique().alias("infield_group_quality_people"),
    ).sort("horizon").to_dicts()
    final = {
        "status": "measurement_and_support_audit_complete_not_model_validation",
        "fits": 0, "accuracy_improvement_established": False,
        "player_walkthrough_status": "complete",
        "player_walkthrough": "docs/defensive-talent-support-player-walkthrough.md",
        "result": "docs/defensive-talent-support-result.md",
        "origin_inputs_replayed": origins.height, "window_labels_replayed": labels.height,
        "fixed_player_origins_reviewed": len(walk["cases"]), "supplemental_dsl_origins_reviewed": len(supplemental),
        "no_prior_mlb_defense_by_level": profiles, "dsl_source_coverage": dsl_coverage,
        "hashes": {**report["hashes"], **report["artifact_hashes"],
                   str(Path(__file__)): sha256_file(Path(__file__)),
                   str(OUT / "report.json"): sha256_file(OUT / "report.json"),
                   str(OUT / "player-traces.json"): sha256_file(OUT / "player-traces.json")},
        "disposition": "Do not fit or reject minor defensive talent from these sparse same-position labels. Repair position-resolved MLB measurements and historical input support before the next talent comparison.",
        "production_changed": False, "additional_2026_model_outcomes_ingested_or_used": False,
        "incidental_current_leaderboard_excerpt_in_source_search": True,
    }
    for path in (ROOT / final["player_walkthrough"], ROOT / final["result"]):
        assert path.exists(), f"Write the interpretation before completion: {path}"
        final["hashes"][str(path)] = sha256_file(path)
    save(OUT / "reviewed-player-traces.json", walk)
    save(PUBLIC / "reviewed-player-traces.json", walk)
    final["hashes"][str(OUT / "reviewed-player-traces.json")] = sha256_file(OUT / "reviewed-player-traces.json")
    save(OUT / "final-review.json", final)
    save(PUBLIC / "final-review.json", final)
    verify(final["hashes"])
    protections()
    print({k: v for k, v in final.items() if k not in ("hashes", "no_prior_mlb_defense_by_level")})


if __name__ == "__main__":
    main()
