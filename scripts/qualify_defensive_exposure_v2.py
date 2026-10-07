"""Pre-fit bounded exposure certification; strict source evidence stays intact."""
import json
import shutil
from pathlib import Path

import polars as pl

from audit_defensive_talent_support import verify
from run_hitter_finite_return_baseline import protections, save
from universal_baseball.storage import sha256_file
import prepare_defensive_talent_position_v2 as prepare

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "reports/generated/defensive-talent-position-v2"
OUT = BASE / "qualified"


def main():
    protections()
    verify(json.loads((BASE / "source-report.json").read_text(encoding="utf8"))["hashes"])
    assert not OUT.exists()
    OUT.mkdir()
    frame = pl.read_parquet(BASE / "annual.parquet")
    delta = (pl.col("native_outs") - pl.col("official_outs")).abs()
    maximum = pl.max_horizontal("native_outs", "official_outs")
    frame = frame.with_columns(pl.col("measurement_valid").alias("strict_measurement_valid"),
                              delta.alias("exposure_difference"))
    frame = frame.with_columns(((delta <= 5) & (delta <= .01 * maximum)
                                & (pl.col("native_outs") > 0) & (pl.col("official_outs") > 0)
                                & pl.col("range_runs").is_not_null() & pl.col("range_runs").is_finite()).alias("measurement_valid"))
    frame.write_parquet(OUT / "annual.parquet")
    for name in ("identity.parquet", "identity-report.json", "source-report.json"):
        shutil.copyfile(BASE / name, OUT / name)
    checks = frame.filter(pl.col("position").is_in([4, 5, 6])).group_by("season").agg(
        pl.col("strict_measurement_valid").sum().alias("strict_rows"),
        pl.col("measurement_valid").sum().alias("qualified_rows"),
        pl.col("exposure_difference").max().alias("maximum_discrepancy")).sort("season").to_dicts()
    report = dict(status="bounded_exposure_certification_before_any_fit", fits=0, checks=checks,
                  hashes={str(p): sha256_file(p) for p in [Path(__file__), BASE / "annual.parquet", OUT / "annual.parquet", ROOT / "docs/defensive-talent-position-v2-exposure-amendment.md"]})
    save(OUT / "exposure-certification.json", report)
    prepare.OUT = OUT
    prepare.PUBLIC = ROOT / "reports/model-evidence/defensive-talent-position-v2/qualified"
    prepare.PUBLIC.mkdir(parents=True)
    prepare.main()
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
