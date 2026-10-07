"""Immutable cohort, repaired context, fixed labels and actual fold support."""
import json
from collections import defaultdict
from pathlib import Path

import polars as pl

from universal_baseball.defensive_talent_position import origin_context, label, preflight
from universal_baseball.storage import sha256_file
from audit_defensive_talent_support import verify, FIXED
from run_hitter_finite_return_baseline import protections, save

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/generated/defensive-talent-position-v2"
PUBLIC = ROOT / "reports/model-evidence/defensive-talent-position-v2"


def main():
    protections()
    assert not (OUT / "preflight.json").exists()
    paths = [ROOT / "reports/generated/defensive-talent-support/origins.parquet",
             ROOT / "reports/generated/minor-infield-play-share/annual.parquet", OUT / "identity.parquet", OUT / "annual.parquet"]
    for filename in ("source-report.json", "identity-report.json"):
        verify(json.loads((OUT / filename).read_text(encoding="utf8"))["hashes"])
    original, minor_frame, bio_frame, native_frame = [pl.read_parquet(p) for p in paths]
    source_path = ROOT / "reports/generated/multiyear-hitter-components-v1/source-audit.json"
    source = json.loads(source_path.read_text(encoding="utf8"))["mlb_fielding"]
    official_path = Path(source["path"])
    assert sha256_file(official_path) == source["sha256"]
    paths += [source_path, official_path]
    official_frame = pl.read_parquet(official_path).group_by("season", "player_id", "position_code").agg(pl.col("fielding_outs").sum())
    official = {(r["season"], r["player_id"], int(r["position_code"])): r["fielding_outs"] for r in official_frame.iter_rows(named=True) if r["position_code"].isdigit()}
    minor, native = defaultdict(list), defaultdict(dict)
    for r in minor_frame.iter_rows(named=True):
        minor[r["player_id"], r["position"]].append(r)
    for r in native_frame.iter_rows(named=True):
        native[r["player_id"], r["position"]][r["season"]] = r
    bio = {r["player_id"]: r for r in bio_frame.iter_rows(named=True)}
    origins = [origin_context(r, minor, bio, native, official) for r in original.iter_rows(named=True)]
    prepared = pl.DataFrame(origins)
    assert prepared.height == original.height == 31563
    assert prepared.select("origin_year", "player_id", "position").equals(original.select("origin_year", "player_id", "position"))
    prepared.write_parquet(OUT / "origins.parquet")
    labels, fixed = [], []
    fixed_keys = set(FIXED + [(678662, 2019), (678662, 2021)])
    for row in origins:
        for horizon in (3, 5, 7):
            record, path = label(row, horizon, native, official)
            labels.append(record)
            if (row["player_id"], row["origin_year"]) in fixed_keys:
                fixed.append(dict(inputs=row, horizon=horizon, label=record, future_path=path,
                                  minor_source=minor[row["player_id"], row["position"]],
                                  past_native=[r for r in native[row["player_id"], row["position"]].values() if r["season"] <= row["origin_year"]]))
    frame = pl.DataFrame(labels)
    frame.write_parquet(OUT / "labels.parquet")
    checks = []
    for horizon in (3, 5, 7):
        for year in sorted({r["origin_year"] for r in origins if r["origin_year"] + horizon <= 2025}):
            for fold in range(5):
                train = [r for r in labels if r["horizon"] == horizon and r["window_end"] <= year and r["origin_year"] < year and r["player_id"] % 5 != fold and r["quality_rate"] is not None]
                test = [r for r in labels if r["horizon"] == horizon and r["origin_year"] == year and r["player_id"] % 5 == fold]
                c, support = preflight(train, test, year, fold, horizon)
                checks.append(c)
    coverage = frame.group_by("horizon", "origin_year", "fielding_level", "prior_mlb_defense").agg(
        pl.len().alias("origin_positions"), pl.col("player_id").n_unique().alias("people"),
        pl.col("quality_rate").is_not_null().sum().alias("measured_rows"),
        pl.col("player_id").filter(pl.col("quality_rate").is_not_null()).n_unique().alias("measured_people"))
    coverage.write_parquet(OUT / "coverage.parquet")
    counts = []
    for horizon in (3, 5, 7):
        f = frame.filter((pl.col("horizon") == horizon) & pl.col("quality_rate").is_not_null())
        novel = f.filter(~pl.col("prior_mlb_defense"))
        counts.append(dict(horizon=horizon, measured_rows=f.height, people=f["player_id"].n_unique(),
                           no_prior_mlb_people=novel["player_id"].n_unique(),
                           rookie_origin_people=novel.filter(pl.col("fielding_level") == "rk")["player_id"].n_unique(),
                           dsl_origin_people=novel.filter(pl.col("dsl_share") >= .8)["player_id"].n_unique()))
    report = dict(status="prepared_requires_source_player_review_before_fit", fits=0, coverage=counts, folds=checks,
                  age_missing_before=original["age"].null_count(), age_missing_after=prepared["age"].null_count(),
                  name_missing_before=original["player_name"].null_count(), name_missing_after=prepared["player_name"].null_count(),
                  changed_age_rows=prepared.filter(pl.col("original_age").is_not_null() & (pl.col("age") != pl.col("original_age"))).height,
                  fixed_traces=fixed, player_walkthrough_status="pending", production_changed=False, additional_2026_data_ingested_or_used=False,
                  hashes={str(p): sha256_file(p) for p in [*paths, Path(__file__), ROOT / "src/universal_baseball/defensive_talent_position.py", *[OUT / n for n in ("origins.parquet", "labels.parquet", "coverage.parquet", "source-report.json", "identity-report.json")]]})
    save(OUT / "preflight.json", report)
    save(PUBLIC / "preflight.json", {k: v for k, v in report.items() if k != "fixed_traces"})
    save(OUT / "source-player-traces.json", fixed)
    print(json.dumps({k: v for k, v in report.items() if k not in ("fixed_traces", "hashes", "folds")}, indent=2))
    print(json.dumps([c for c in checks if c["origin"] in (2021, 2022) and c["horizon"] == 3], indent=2))
    protections()


if __name__ == "__main__":
    main()
