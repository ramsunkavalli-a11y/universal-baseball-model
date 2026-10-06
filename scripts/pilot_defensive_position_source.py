"""Historical position-split source pilot with same-vintage aggregate checks."""

import json
import math
import re
from pathlib import Path

import polars as pl
import requests
from sportsdataverse.mlb.mlb_statcast import parse_mlb_statcast_html_leaderboard

from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections, save

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/generated/defensive-position-source-pilot"
PUBLIC = ROOT / "reports/model-evidence/defensive-position-source-pilot"
YEARS = (2022, 2025)
FIXED = (677951, 622761, 669364, 678882)


def capture(year, split):
    assert year in YEARS
    params = {"type": "fielder", "seasonStart": year, "seasonEnd": year,
              "minInnings": 0, "minResults": 0}
    if split:
        params["groupBy"] = "position"
    stem = f"{'position' if split else 'aggregate'}-{year}"
    path = OUT / f"{stem}.response"
    if not path.exists():
        r = requests.get("https://baseballsavant.mlb.com/leaderboard/fielding-run-value",
                         params=params, timeout=45)
        r.raise_for_status()
        path.write_bytes(r.content)
    content = path.read_text(encoding="utf8")
    matches = re.findall(r"(?:const|var|let)\s+serverParams\s*=\s*(\{.*?\});", content)
    assert len(matches) == 1, "Need embedded query/year provenance"
    observed = json.loads(matches[0])
    assert int(observed["seasonStart"]) == int(observed["seasonEnd"]) == year
    assert ("position" in observed["secondaryGroupBy"]) == split
    frame = parse_mlb_statcast_html_leaderboard(content)
    assert isinstance(frame, pl.DataFrame) and frame.height > 0
    frame.write_parquet(OUT / f"{stem}.parquet")
    return frame, {"requested_year": year, "split": split, "params": params,
                   "observed_year_start": observed["seasonStart"], "observed_year_end": observed["seasonEnd"],
                   "observed_grouping": observed["secondaryGroupBy"], "rows": frame.height,
                   "response_sha256": sha256_file(path), "columns": frame.columns}


def main():
    protections()
    prior = ROOT / "reports/generated/defensive-talent-support/final-review.json"
    assert json.loads(prior.read_text(encoding="utf8"))["player_walkthrough_status"] == "complete"
    assert not (OUT / "report.json").exists(), "Preserve completed pilot"
    OUT.mkdir(parents=True, exist_ok=True)
    captures, checks, walks = [], [], []
    for year in YEARS:
        split, note = capture(year, True)
        captures.append(note)
        agg, note = capture(year, False)
        captures.append(note)
        assert "pos_id" in split.columns, "Primary-position labels do not certify splits"
        assert split.select("id", "pos_id").is_duplicated().sum() == 0
        assert agg["id"].n_unique() == agg.height
        assert set(split["pos_id"].drop_nulls().unique()).issubset(set(range(1, 10)))
        aggregates = {r["id"]: r for r in agg.iter_rows(named=True)}
        by_player = {}
        for row in split.iter_rows(named=True):
            by_player.setdefault(row["id"], []).append(row)
        exposure_mismatches, recompose_mismatches, null_range = [], [], []
        for pid, rows in by_player.items():
            a = aggregates.get(pid)
            assert a is not None, pid
            for r in rows:
                pos = r["pos_id"]
                if pos in range(2, 10) and r["outs_total"] != a[f"outs_{pos}"]:
                    exposure_mismatches.append({"player_id": pid, "position": pos,
                                                "split_outs": r["outs_total"], "aggregate_position_outs": a[f"outs_{pos}"]})
                if r["range_runs"] is None:
                    null_range.append({"player_id": pid, "position": pos, "outs": r["outs_total"]})
            sum_outs = sum(r["outs_total"] or 0 for r in rows)
            sum_range = sum(r["range_runs"] for r in rows if r["range_runs"] is not None)
            range_ok = a["range_runs"] is None or math.isclose(sum_range, a["range_runs"], abs_tol=1e-6, rel_tol=0)
            if sum_outs != a["outs_total"] or not range_ok:
                recompose_mismatches.append({"player_id": pid, "split_outs": sum_outs,
                                            "aggregate_outs": a["outs_total"], "split_range": sum_range,
                                            "aggregate_range": a["range_runs"]})
        old = pl.read_parquet(ROOT / f"reports/generated/multiyear-hitter-components-v1/native-source/fielding-{year}.parquet")
        older = {r["id"]: r for r in old.iter_rows(named=True)}
        for pid in FIXED:
            rows = by_player.get(pid, [])
            a = aggregates.get(pid)
            prior_row = older.get(pid)
            walks.append({"season": year, "player_id": pid,
                          "aggregate": {k: a[k] for k in ("name", "range_runs", "outs_total")} if a else None,
                          "positions": [{"position": r["pos_id"], "range_runs": r["range_runs"], "outs": r["outs_total"]} for r in rows],
                          "old_aggregate_range": prior_row["range_runs"] if prior_row else None,
                          "old_aggregate_outs": prior_row["outs_total"] if prior_row else None})
        checks.append({"season": year, "split_rows": split.height, "split_people": split["id"].n_unique(),
                       "aggregate_people": agg.height, "exposure_mismatches": exposure_mismatches,
                       "recomposition_mismatches": recompose_mismatches, "null_range_positions": null_range})
    report = {"status": "source_pilot_requires_player_interpretation", "fits": 0,
              "checks": checks, "captures": captures, "walkthrough": walks,
              "player_walkthrough_status": "pending", "production_changed": False,
              "additional_2026_data_ingested_or_used": False,
              "hashes": {str(p): sha256_file(p) for p in list(OUT.glob("*.parquet")) + list(OUT.glob("*.response")) + [
                  Path(__file__), ROOT / "docs/defensive-position-source-pilot-contract.md", prior,
              ]}}
    PUBLIC.mkdir(parents=True, exist_ok=True)
    save(OUT / "report.json", report)
    save(PUBLIC / "report.json", report)
    protections()
    print(json.dumps({"status": report["status"], "checks": [{k: v for k, v in c.items() if k != "null_range_positions"} for c in checks], "walkthrough": walks}, indent=2))


if __name__ == "__main__":
    main()
