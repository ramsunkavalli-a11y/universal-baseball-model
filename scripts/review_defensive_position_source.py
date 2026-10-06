"""Explain source-pilot exposure gaps without inventing omitted skill measurements."""

import json
import sys
from pathlib import Path

import polars as pl

from audit_defensive_talent_support import ROOT, verify
from run_hitter_finite_return_baseline import protections, save
from universal_baseball.storage import sha256_file

OUT = ROOT / "reports/generated/defensive-position-source-pilot"
PUBLIC = ROOT / "reports/model-evidence/defensive-position-source-pilot"
YEARS = (2022, 2025)


def main():
    protections()
    report = json.loads((OUT / "report.json").read_text(encoding="utf8"))
    verify(report["hashes"])
    audit_path = ROOT / "reports/generated/multiyear-hitter-components-v1/source-audit.json"
    source = json.loads(audit_path.read_text(encoding="utf8"))["mlb_fielding"]
    official_path = Path(source["path"])
    assert sha256_file(official_path) == source["sha256"]
    official = pl.read_parquet(official_path).group_by("season", "player_id", "position_code").agg(pl.col("fielding_outs").sum())
    usage = {(r["season"], r["player_id"], int(r["position_code"])): r["fielding_outs"] for r in official.iter_rows(named=True) if r["position_code"].isdigit()}
    checks, missing, differences = [], [], []
    for year in YEARS:
        split = pl.read_parquet(OUT / f"position-{year}.parquet")
        aggregate = pl.read_parquet(OUT / f"aggregate-{year}.parquet")
        assert split["pos_id"].null_count() == 0
        rows = {(r["id"], r["pos_id"]): r for r in split.iter_rows(named=True)}
        unmapped = []
        for a in aggregate.iter_rows(named=True):
            pid = a["id"]
            present_outs = 0
            absent_outs = 0
            for pos in range(2, 10):
                n = a[f"outs_{pos}"]
                r = rows.get((pid, pos))
                if r:
                    assert r["outs_total"] == n
                    present_outs += n
                    official_n = usage.get((year, pid, pos))
                    if official_n is None or official_n != n:
                        differences.append({"season": year, "player_id": pid, "position": pos,
                                            "native_outs": n, "official_outs": official_n})
                elif n > 0:
                    absent_outs += n
                    missing.append({"season": year, "player_id": pid, "position": pos,
                                    "known_native_position_outs": n, "range_measurement": None})
            native_gap = a["outs_total"] - sum(a[f"outs_{p}"] for p in range(2, 10))
            official_p = usage.get((year, pid, 1), 0)
            if native_gap != 0:
                unmapped.append({"player_id": pid, "native_gap": native_gap,
                                 "official_pitcher_outs": official_p, "explained_by_pitching": native_gap == official_p})
            assert present_outs + absent_outs + native_gap == a["outs_total"]
        old = pl.read_parquet(ROOT / f"reports/generated/multiyear-hitter-components-v1/native-source/fielding-{year}.parquet")
        comparison = aggregate.select("id", "range_runs", "outs_total").join(old.select("id", "range_runs", "outs_total"), on="id", suffix="_old")
        year_missing = [r for r in missing if r["season"] == year]
        year_diffs = [r for r in differences if r["season"] == year]
        c = next(c for c in report["checks"] if c["season"] == year)
        range_differences = [abs((r["aggregate_range"] or 0) - r["split_range"]) for r in c["recomposition_mismatches"]]
        assert all(v < 1e-6 for v in range_differences)
        assert not c["exposure_mismatches"]
        # Also independently sum every non-null split run, not just mismatch rows.
        sums = split.group_by("id").agg(pl.col("range_runs").sum().alias("sum_range"))
        run_check = aggregate.select("id", "range_runs").join(sums, on="id")
        max_error = run_check.select((pl.col("range_runs") - pl.col("sum_range")).abs().max()).item()
        assert max_error < 1e-6
        checks.append({"season": year, "split_rows": split.height, "people": split["id"].n_unique(),
                       "max_run_recomposition_error": max_error, "native_position_exposure_mismatches": 0,
                       "missing_positive_position_rows": len(year_missing),
                       "missing_position_outs": sum(r["known_native_position_outs"] for r in year_missing),
                       "max_missing_position_outs": max((r["known_native_position_outs"] for r in year_missing), default=0),
                       "native_total_gap_rows": len(unmapped), "unexplained_total_gap_rows": sum(not r["explained_by_pitching"] for r in unmapped),
                       "official_native_position_out_differences": len(year_diffs),
                       "max_official_native_position_out_difference": max((abs(r["native_outs"] - r["official_outs"]) for r in year_diffs if r["official_outs"] is not None), default=0),
                       "old_new_range_revisions": comparison.filter((pl.col("range_runs") - pl.col("range_runs_old")).abs() > 1e-6).height,
                       "max_old_new_range_revision": comparison.select((pl.col("range_runs") - pl.col("range_runs_old")).abs().max()).item(),
                       "old_new_total_out_differences": comparison.filter(pl.col("outs_total") != pl.col("outs_total_old")).height})
        checks[-1]["null_infield_range_measurements"] = split.filter(pl.col("pos_id").is_in([4, 5, 6]) & pl.col("range_runs").is_null()).height
    if "--check-only" in sys.argv:
        print(json.dumps(checks, indent=2))
        return
    doc = ROOT / "docs/defensive-position-source-pilot-result.md"
    assert doc.exists(), "Complete the readable player interpretation first"
    final = {"status": "position_measurements_verified_for_observed_rows_with_explicit_exposure_gaps",
             "fits": 0, "player_walkthrough_status": "complete", "result": str(doc.relative_to(ROOT)),
             "checks": checks, "missing_positive_position_measurements": missing,
             "official_native_exposure_differences": differences, "fixed_player_walkthrough": report["walkthrough"],
             "production_changed": False, "additional_2026_data_ingested_or_used": False,
             "disposition": "Allow a dated historical position-source extension. Preserve missing split rows as unknown quality and use position-specific native outs. Recount support and repair origin metadata before fitting.",
             "hashes": {**report["hashes"], str(OUT / "report.json"): sha256_file(OUT / "report.json"),
                        str(Path(__file__)): sha256_file(Path(__file__)), str(doc): sha256_file(doc),
                        str(official_path): source["sha256"], str(audit_path): sha256_file(audit_path)}}
    save(OUT / "final-review.json", final)
    save(PUBLIC / "final-review.json", final)
    verify(final["hashes"])
    protections()
    print(json.dumps({k: v for k, v in final.items() if k not in ("hashes", "missing_positive_position_measurements", "official_native_exposure_differences", "fixed_player_walkthrough")}, indent=2))


if __name__ == "__main__":
    main()
