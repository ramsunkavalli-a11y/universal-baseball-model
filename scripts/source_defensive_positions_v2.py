"""Extend certified position measurements without importing unrelated sports models."""
import json
import math
import re
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import polars as pl
import requests

from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections, save
from audit_defensive_talent_support import verify

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/generated/defensive-talent-position-v2"
PUBLIC = ROOT / "reports/model-evidence/defensive-talent-position-v2"
PILOT = ROOT / "reports/generated/defensive-position-source-pilot"


def embedded(content, variable):
    matches = []
    pattern = rf"(?<![\w$.])(?:const|var|let)\s+{variable}\s*=\s*"
    for match in re.finditer(pattern, content):
        try:
            value, _ = json.JSONDecoder().raw_decode(content, match.end())
            matches.append(value)
        except json.JSONDecodeError:
            continue
    assert len(matches) == 1, (variable, len(matches))
    return matches[0]


def decode(content, year, split):
    params = embedded(content, "serverParams")
    assert int(params["seasonStart"]) == int(params["seasonEnd"]) == year
    assert ("position" in params["secondaryGroupBy"]) == split
    rows = embedded(content, "data")
    assert isinstance(rows, list) and rows
    # These leaderboard rows are flat JSON; do not execute embedded JavaScript.
    assert all(not isinstance(v, (dict, list)) for row in rows for v in row.values())
    frame = pl.DataFrame(rows, infer_schema_length=None)
    required = ["id", "name", "outs_total", "range_runs"]
    if split:
        required += ["pos_id"]
    else:
        required += [f"outs_{p}" for p in range(2, 10)]
    assert set(required).issubset(frame.columns)
    return frame.select(required), params


def capture(task):
    year, split = task
    assert 2016 <= year <= 2025
    stem = f"{'position' if split else 'aggregate'}-{year}"
    path = OUT / f"{stem}.response"
    query = dict(type="fielder", seasonStart=year, seasonEnd=year, minInnings=0, minResults=0)
    if split:
        query["groupBy"] = "position"
    if not path.exists():
        if year in (2022, 2025):
            shutil.copyfile(PILOT / path.name, path)
        else:
            response = requests.get("https://baseballsavant.mlb.com/leaderboard/fielding-run-value", params=query, timeout=45)
            response.raise_for_status()
            path.write_bytes(response.content)
    frame, observed = decode(path.read_text(encoding="utf8"), year, split)
    if year in (2022, 2025):
        reference = pl.read_parquet(PILOT / f"{stem}.parquet").select(frame.columns)
        assert frame.equals(reference), "Lightweight parser must replay certified pilot"
    target = OUT / f"{stem}.parquet"
    if target.exists():
        assert frame.equals(pl.read_parquet(target))
    else:
        frame.write_parquet(target)
    return dict(year=year, split=split, requested=query, observed=observed,
                response_sha256=sha256_file(path), parsed_sha256=sha256_file(target),
                reused_pilot=year in (2022, 2025), rows=frame.height)


def main():
    protections()
    pilot = json.loads((PILOT / "final-review.json").read_text(encoding="utf8"))
    verify(pilot["hashes"])
    assert pilot["player_walkthrough_status"] == "complete"
    assert not (OUT / "source-report.json").exists()
    OUT.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        captures = list(pool.map(capture, [(y, s) for y in range(2016, 2026) for s in (True, False)]))
    audit = ROOT / "reports/generated/multiyear-hitter-components-v1/source-audit.json"
    source = json.loads(audit.read_text(encoding="utf8"))["mlb_fielding"]
    official_path = Path(source["path"])
    assert sha256_file(official_path) == source["sha256"]
    official = pl.read_parquet(official_path).group_by("season", "player_id", "position_code").agg(pl.col("fielding_outs").sum())
    usage = {(r["season"], r["player_id"], int(r["position_code"])): r["fielding_outs"] for r in official.iter_rows(named=True) if r["position_code"].isdigit()}
    checks, annual, gaps = [], [], []
    for year in range(2016, 2026):
        split = pl.read_parquet(OUT / f"position-{year}.parquet")
        agg = pl.read_parquet(OUT / f"aggregate-{year}.parquet")
        assert split.select("id", "pos_id").is_duplicated().sum() == 0
        assert agg["id"].n_unique() == agg.height
        rows = {(r["id"], r["pos_id"]): r for r in split.iter_rows(named=True)}
        assert set(split["pos_id"].drop_nulls()).issubset(range(1, 10))
        # Older seasons retain a few pitcher rows with no range measurement.
        pitcher_rows = split.filter(pl.col("pos_id") == 1)
        assert pitcher_rows["range_runs"].null_count() == pitcher_rows.height
        max_recomposition = 0
        mismatches, missing, nulls, pitcher_gaps = 0, 0, 0, 0
        for a in agg.iter_rows(named=True):
            pid = a["id"]
            values = []
            for pos in range(2, 10):
                row = rows.get((pid, pos))
                native_outs = a[f"outs_{pos}"]
                official_outs = usage.get((year, pid, pos), 0)
                if row is not None:
                    assert row["outs_total"] == native_outs, "Split must agree with same-vintage total"
                    valid = native_outs > 0 and official_outs == native_outs and row["range_runs"] is not None and math.isfinite(row["range_runs"])
                    mismatches += official_outs != native_outs
                    nulls += row["range_runs"] is None
                    if row["range_runs"] is not None:
                        values.append(row["range_runs"])
                    annual.append(dict(season=year, player_id=pid, player_name=row["name"], position=pos,
                                       native_outs=native_outs, official_outs=official_outs,
                                       range_runs=row["range_runs"], measurement_valid=valid))
                elif native_outs > 0 or official_outs > 0:
                    missing += 1
                    gaps.append(dict(season=year, player_id=pid, position=pos, native_outs=native_outs, official_outs=official_outs, reason="missing_split_row"))
            if a["range_runs"] is not None:
                delta = abs(sum(values) - a["range_runs"])
                max_recomposition = max(max_recomposition, delta)
                assert delta < 1e-6
            native_gap = a["outs_total"] - sum(a[f"outs_{p}"] for p in range(2, 10))
            official_pitcher = usage.get((year, pid, 1), 0)
            if native_gap != official_pitcher:
                pitcher_gaps += 1
                gaps.append(dict(season=year, player_id=pid, position=1, native_outs=native_gap, official_outs=official_pitcher, reason="unresolved_aggregate_pitcher_gap"))
        aggregate_ids = set(agg["id"])
        assert all(pid in aggregate_ids for pid, pos in rows)
        for (y, pid, pos), outs in usage.items():
            if y == year and pos in range(2, 10) and outs > 0 and pid not in aggregate_ids:
                gaps.append(dict(season=y, player_id=pid, position=pos, native_outs=None, official_outs=outs, reason="missing_aggregate_player"))
        checks.append(dict(season=year, position_rows=split.height, pitcher_rows_without_range=pitcher_rows.height, people=split["id"].n_unique(), official_mismatches=mismatches, missing_positive_positions=missing, null_ranges=nulls, unresolved_pitcher_gaps=pitcher_gaps, max_recomposition_error=max_recomposition))
    pl.DataFrame(annual).write_parquet(OUT / "annual.parquet")
    pl.DataFrame(gaps).write_parquet(OUT / "measurement-gaps.parquet")
    report = dict(status="source_certified_observed_position_rows_individual_exclusions_preserved", checks=checks, captures=captures,
                  fits=0, player_walkthrough_status="pending", production_changed=False, additional_2026_data_ingested_or_used=False,
                  hashes={str(p): sha256_file(p) for p in [Path(__file__), ROOT / "docs/defensive-talent-position-v2-contract.md", official_path, audit, PILOT / "final-review.json", *OUT.glob("*.response"), *OUT.glob("*.parquet")]})
    PUBLIC.mkdir(parents=True, exist_ok=True)
    save(OUT / "source-report.json", report)
    save(PUBLIC / "source-report.json", report)
    protections()
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
