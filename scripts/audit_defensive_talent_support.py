"""Fixed minor-origin/later-MLB coverage ledger, support audit and player traces."""

import json
from collections import defaultdict
from pathlib import Path

import polars as pl

from universal_baseball.defensive_talent_support import (
    POSITIONS, WINDOWS, age_band, profile, training_snapshot, window_label,
)
from universal_baseball.minor_infield_play_share import pooled
from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections, save

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "reports/generated/multiyear-hitter-components-v1"
OLD = ROOT / "reports/generated/minor-infield-play-share"
OUT = ROOT / "reports/generated/defensive-talent-support"
PUBLIC = ROOT / "reports/model-evidence/defensive-talent-support"
FIXED = [
    (677951, 2021), (683011, 2022), (665161, 2021), (682928, 2021),
    (691783, 2022), (691785, 2024), (669023, 2018), (622761, 2018),
    (678882, 2024), (669364, 2023), (682928, 2023), (678894, 2024), (692021, 2024),
]


def read(path):
    return json.loads(path.read_text(encoding="utf8"))


def verify(hashes):
    for path, digest in hashes.items():
        assert sha256_file(Path(path)) == digest, path


def indexed(frame, id_column="player_id", year_column="season"):
    result = defaultdict(dict)
    for row in frame.iter_rows(named=True):
        pid, year = row[id_column], row[year_column]
        assert year not in result[pid], (pid, year)
        result[pid][year] = row
    return result


def source_inventory(native, official, official_raw):
    pitcher = official_raw.filter(pl.col("position_abbreviation") == "P").group_by("player_id", "season").agg(pl.col("fielding_outs").sum())
    pitching = {(r["player_id"], r["season"]): r["fielding_outs"] for r in pitcher.iter_rows(named=True)}
    rows = []
    for pid, years in native.items():
        for year, r in years.items():
            total = r["outs_total"]
            vals = [r[f"outs_{p}"] for p in range(2, 10)]
            gap = total - sum(vals) if total is not None and all(v is not None for v in vals) else None
            p_outs = pitching.get((pid, year), 0)
            o = official.get(pid, {}).get(year)
            rows.append({"season": year, "player_id": pid, "native_outs": total,
                         "native_unmapped_outs": gap, "official_pitcher_outs": p_outs,
                         "gap_matches_pitcher_outs": gap == p_outs,
                         "official_outs": o["official_outs"] if o else None,
                         "native_official_outs_difference": total - o["official_outs"] if total is not None and o else None})
    f = pl.DataFrame(rows)
    return f, f.group_by("season").agg(
        pl.len().alias("native_rows"),
        (pl.col("native_unmapped_outs") != 0).sum().alias("nonzero_unmapped_rows"),
        ((pl.col("native_unmapped_outs") != 0) & pl.col("gap_matches_pitcher_outs")).sum().alias("unmapped_rows_matching_official_pitching"),
        pl.col("native_unmapped_outs").is_null().sum().alias("unknown_unmapped_rows"),
    ).sort("season").to_dicts()


def origins(annual, panel, official):
    metadata = {(r["origin_year"], r["player_id"]): r for r in panel.iter_rows(named=True)}
    records = []
    for year in sorted(annual["season"].unique().to_list()):
        pool = pooled(annual, year).filter(pl.col("ground_balls") >= 25)
        dsl = annual.filter(pl.col("season").is_between(year - 2, year) & (pl.col("league_id") == 130)).with_columns(
            (pl.col("ground_balls") * pl.lit(.5).pow(year - pl.col("season"))).alias("dsl_ground_balls")
        ).group_by("player_id", "position").agg(pl.col("dsl_ground_balls").sum())
        pool = pool.join(dsl, on=["player_id", "position"], how="left").with_columns(pl.col("dsl_ground_balls").fill_null(0))
        for row in pool.iter_rows(named=True):
            pid = row["player_id"]
            m = metadata.get((year, pid), {})
            role = [m.get("role_2B"), m.get("role_3B"), m.get("role_SS")]
            role_sum = sum(role) if all(v is not None for v in role) else None
            prior = any(y <= year and r["official_outs"] > 0 for y, r in official.get(pid, {}).items())
            records.append({**row, "origin_year": year, "player_name": m.get("player_name"),
                            "age": m.get("age"), "level": m.get("level"), "stage": m.get("stage"),
                            "metadata_present": bool(m), "prior_mlb_defense": prior,
                            "age_band": age_band(m.get("age")), "infield_role_share": role_sum,
                            "primary_infield_role": role_sum >= .5 if role_sum is not None else None,
                            "earliest_source_season": max(2016, year - 2),
                            "source_history_left_truncated": year - 2 < 2016})
    f = pl.DataFrame(records)
    assert f.select("origin_year", "player_id", "position").is_duplicated().sum() == 0
    return f


def group_report(labels):
    return labels.group_by("horizon", "origin_year", "level", "age_band", "position", "prior_mlb_defense").agg(
        pl.len().alias("player_position_rows"), pl.col("player_id").n_unique().alias("people"),
        pl.col("window_mature").sum().alias("mature_rows"),
        pl.col("quality_rate").is_not_null().sum().alias("same_position_quality_rows"),
        pl.col("infield_group_quality_available").sum().alias("infield_group_quality_rows"),
        (pl.col("future_official_outs") > 0).sum().alias("recorded_future_fielding_rows"),
        pl.col("age").mean().alias("mean_origin_age"),
        pl.col("ground_balls").mean().alias("mean_weighted_origin_ground_balls"),
        (pl.col("dsl_ground_balls") > 0).sum().alias("rows_with_dsl_source"),
    ).sort("horizon", "origin_year", "level", "age_band", "position", "prior_mlb_defense", nulls_last=True)


def peer_ids(focal, origin_records):
    # Rank only dated origin evidence; future results are not passed here.
    peers = [r for r in origin_records if r["origin_year"] == focal["origin_year"]
             and r["position"] == focal["position"] and r["player_id"] != focal["player_id"]
             and r["level"] == focal["level"] and r["prior_mlb_defense"] == focal["prior_mlb_defense"]]
    def distance(r):
        age_distance = abs(r["age"] - focal["age"]) if r["age"] is not None and focal["age"] is not None else 999
        return age_distance, abs(r["ground_balls"] - focal["ground_balls"]), r["player_id"]
    return sorted(peers, key=distance)[:3]


def main():
    protections()
    assert not OUT.exists() and not PUBLIC.exists(), "Preserve completed audit"
    pre = read(OLD / "preflight.json")
    cert = read(BASE / "native-source-certification.json")
    source = read(BASE / "source-audit.json")
    hashes = {path: digest for path, digest in pre["hashes"].items()
              if path.endswith(("annual.parquet", "component-panel.parquet", "official-position-history.parquet"))}
    hashes.update({str(ROOT / path): digest for path, digest in cert["raw_hashes"].items() if "fielding-" in path})
    hashes.update(cert["upstream_hashes"])
    old_inventory = Path(source["milb_origin_fielding"]["path"])
    hashes[str(old_inventory)] = source["milb_origin_fielding"]["sha256"]
    for path in [Path(__file__), ROOT / "src/universal_baseball/defensive_talent_support.py",
                 ROOT / "src/universal_baseball/minor_infield_play_share.py",
                 ROOT / "tests/test_defensive_talent_support.py",
                 ROOT / "docs/nonbatting-talent-support-contract.md", BASE / "native-source-certification.json"]:
        hashes[str(path)] = sha256_file(path)
    verify(hashes)
    annual = pl.read_parquet(OLD / "annual.parquet")
    panel = pl.read_parquet(BASE / "component-panel.parquet", columns=[
        "origin_year", "player_id", "player_name", "age", "level", "stage", "role_2B", "role_3B", "role_SS",
    ])
    official_frame = pl.read_parquet(BASE / "official-position-history.parquet")
    official = indexed(official_frame)
    raw = pl.concat([
        pl.read_parquet(BASE / f"native-source/fielding-{y}.parquet", columns=[
            "id", "name", "range_runs", "outs_total", *[f"outs_{p}" for p in range(2, 10)]
        ]).with_columns(pl.lit(y).alias("season")) for y in range(2016, 2026)
    ])
    native = indexed(raw, "id")
    assert raw["season"].max() == 2025
    official_raw = pl.read_parquet(source["mlb_fielding"]["path"])
    source_rows, source_checks = source_inventory(native, official, official_raw)
    origin_frame = origins(annual, panel, official)
    origin_records = origin_frame.to_dicts()
    labels = []
    for row in origin_records:
        for horizon in WINDOWS:
            label, _ = window_label(row, horizon, native, official)
            labels.append(label)
    label_frame = pl.DataFrame(labels, infer_schema_length=None)
    assert label_frame.height == 3 * origin_frame.height
    assert label_frame.filter(~pl.col("window_mature") & pl.col("quality_rate").is_not_null()).height == 0
    assert label_frame.filter((pl.col("quality_status") == "no_recorded_mlb_fielding") & pl.col("quality_rate").is_not_null()).height == 0
    support_rows, prediction_support, snapshots = [], [], {}
    for horizon in WINDOWS:
        for origin in sorted(origin_frame["origin_year"].unique().to_list()):
            for fold in range(5):
                for group in (False, True):
                    stats, counts = training_snapshot(labels, origin, fold, horizon, group)
                    target = stats["target"]
                    test = [r for r in labels if r["horizon"] == horizon and r["origin_year"] == origin and r["player_id"] % 5 == fold]
                    n = [len(counts.get(profile(r), set())) for r in test]
                    measured = [r for r in test if r["infield_group_quality_available"]] if group else [r for r in test if r["quality_rate"] is not None]
                    stats.update(test_rows=len(test), test_window_mature=origin + horizon <= 2025,
                                 measured_test_rows=len(measured), zero_profile_rows=sum(v == 0 for v in n),
                                 fewer_than_20_profile_rows=sum(v < 20 for v in n),
                                 measured_test_zero_profile_rows=sum(len(counts.get(profile(r), set())) == 0 for r in measured),
                                 measured_test_fewer_than_20_profile_rows=sum(len(counts.get(profile(r), set())) < 20 for r in measured))
                    support_rows.append(stats)
                    snapshots[(horizon, origin, fold, target)] = stats, counts
                    if not group:
                        for r, count in zip(test, n):
                            prediction_support.append({"horizon": horizon, "origin_year": origin,
                                                       "player_id": r["player_id"], "position": r["position"],
                                                       "fold": fold, "matching_training_people": count,
                                                       "training_people": stats["training_people"],
                                                       "training_origins_count": len(stats["training_origins"])})
    cases = []
    for pid, origin in FIXED:
        candidate = sorted([r for r in origin_records if r["player_id"] == pid and r["origin_year"] == origin], key=lambda r: (-r["ground_balls"], r["position"]))
        if not candidate:
            cases.append({"player_id": pid, "origin_year": origin, "eligible": False,
                          "reason": "No position with 25 weighted ground-ball exposures at this origin; not forced into cohort."})
            continue
        focal = candidate[0]
        rows = [focal] + peer_ids(focal, origin_records)
        traces = []
        for r in rows:
            windows = []
            for horizon in WINDOWS:
                result, path = window_label(r, horizon, native, official)
                stats, counts = snapshots[(horizon, origin, r["player_id"] % 5, "same_position")]
                windows.append({"label": result, "annual_path": path, "actual_fold_support": stats,
                                "matching_training_people": len(counts.get(profile(r), set()))})
            minor = annual.filter((pl.col("player_id") == r["player_id"]) & (pl.col("position") == r["position"]) & pl.col("season").is_between(origin - 2, origin)).sort("season", "level", "league_id").to_dicts()
            traces.append({"origin_inputs": r, "minor_annual_evidence": minor, "windows": windows})
        cases.append({"player_id": pid, "origin_year": origin, "eligible": True,
                      "selection": "fixed case at largest origin-known position exposure; three same-level/position/prior-MLB peers ranked by age then exposure then ID",
                      "focal_and_origin_known_peers": traces})
    old = pl.read_parquet(old_inventory)
    report = {
        "status": "support_inventory_requires_player_interpretation", "fits": 0,
        "player_walkthrough_status": "pending", "production_changed": False,
        "additional_2026_outcomes_accessed": False, "hashes": hashes,
        "origin_player_position_rows": origin_frame.height, "origin_people": origin_frame["player_id"].n_unique(),
        "origin_years": sorted(origin_frame["origin_year"].unique().to_list()),
        "metadata_missing_rows": origin_frame.filter(~pl.col("metadata_present")).height,
        "source_outs_checks": source_checks,
        "older_minor_inventory": {"years": sorted(old["season"].unique().to_list()), "columns": old.columns,
                                  "reconstructs_pre_2016_ground_ball_quality": False},
        "coverage_by_window_and_origin": label_frame.group_by("horizon", "origin_year").agg(
            pl.len().alias("rows"), pl.col("player_id").n_unique().alias("people"),
            pl.col("window_mature").sum().alias("mature_rows"),
            pl.col("quality_rate").is_not_null().sum().alias("same_position_quality_rows"),
            pl.col("player_id").filter(pl.col("quality_rate").is_not_null()).n_unique().alias("same_position_quality_people"),
            pl.col("infield_group_quality_available").sum().alias("infield_group_quality_rows"),
            pl.col("player_id").filter(pl.col("infield_group_quality_available")).n_unique().alias("infield_group_quality_people"),
        ).sort("horizon", "origin_year").to_dicts(),
        "selection_profiles": label_frame.filter(pl.col("window_mature")).with_columns(
            pl.col("quality_rate").is_not_null().alias("measured")
        ).group_by("horizon", "prior_mlb_defense", "measured").agg(
            pl.len().alias("rows"), pl.col("player_id").n_unique().alias("people"),
            pl.col("age").mean().alias("mean_age"), pl.col("ground_balls").mean().alias("mean_weighted_ground_balls"),
            (pl.col("level") == "RK").mean().alias("rookie_fraction"),
            (pl.col("level") == "AAA").mean().alias("aaa_fraction"),
            (pl.col("dsl_ground_balls") > 0).mean().alias("dsl_source_fraction"),
        ).sort("horizon", "prior_mlb_defense", "measured").to_dicts(),
        "quality_status_counts": label_frame.group_by("horizon", "quality_status").len().sort("horizon", "quality_status").to_dicts(),
        "support": support_rows,
    }
    OUT.mkdir(parents=True)
    PUBLIC.mkdir(parents=True)
    origin_frame.write_parquet(OUT / "origins.parquet")
    label_frame.write_parquet(OUT / "labels.parquet")
    group_report(label_frame).write_parquet(OUT / "coverage.parquet")
    source_rows.write_parquet(OUT / "native-outs-audit.parquet")
    pl.DataFrame(prediction_support).write_parquet(OUT / "forecast-time-support.parquet")
    artifacts = {str(path): sha256_file(path) for path in OUT.glob("*.parquet")}
    report["artifact_hashes"] = artifacts
    save(OUT / "report.json", report)
    save(PUBLIC / "report.json", report)
    walk = {"fixed_cases": FIXED, "cases": cases, "predictions_generated": False,
            "future_outcomes_not_used_to_choose_peers": True, "hashes": hashes, "artifact_hashes": artifacts}
    save(OUT / "player-traces.json", walk)
    save(PUBLIC / "player-traces.json", walk)
    verify(hashes)
    protections()
    print(json.dumps({"status": report["status"], "origin_rows": origin_frame.height,
                      "origin_people": report["origin_people"], "fits": 0,
                      "coverage": report["coverage_by_window_and_origin"]}, indent=2))


if __name__ == "__main__":
    main()
