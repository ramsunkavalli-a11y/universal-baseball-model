"""Reparse captured identity and position data; verify sealed final evidence."""
import json
from pathlib import Path

import polars as pl
from audit_defensive_talent_support import verify
from run_hitter_finite_return_baseline import protections, save
from source_defensive_positions_v2 import decode
from universal_baseball.storage import sha256_file

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "reports/generated/defensive-talent-position-v2"
PUBLIC = ROOT / "reports/model-evidence/defensive-talent-position-v2"


def main():
    protections()
    final_path = BASE / "qualified/comparison/final-review.json"
    final = json.loads(final_path.read_text(encoding="utf8"))
    verify(final["hashes"])
    assert final["player_walkthrough_status"] == "complete" and not final["deployment_approved"]
    identities = json.loads((BASE / "identity-report.json").read_text(encoding="utf8"))
    actual, hashes = {}, {}
    for capture in identities["captures"]:
        path = Path(capture["response_path"])
        assert sha256_file(path) == capture["sha256"]
        hashes[str(path)] = capture["sha256"]
        for person in json.loads(path.read_text(encoding="utf8"))["people"]:
            assert person["id"] not in actual
            actual[person["id"]] = (person.get("birthDate"), person.get("fullName"))
    materialized = {r["player_id"]: (r["birth_date"], r["captured_name"]) for r in pl.read_parquet(BASE / "identity.parquet").to_dicts()}
    assert actual == materialized and len(actual) == 4529
    source = json.loads((BASE / "source-report.json").read_text(encoding="utf8"))
    for capture in source["captures"]:
        year, split = capture["year"], capture["split"]
        path = BASE / f"{'position' if split else 'aggregate'}-{year}.response"
        frame, params = decode(path.read_text(encoding="utf8"), year, split)
        assert frame.equals(pl.read_parquet(path.with_suffix(".parquet")))
        assert params == capture["observed"] and sha256_file(path) == capture["response_sha256"]
    qualified = pl.read_parquet(BASE / "qualified/annual.parquet")
    for row in qualified.to_dicts():
        delta = abs(row["native_outs"] - row["official_outs"])
        valid = (row["native_outs"] > 0 and row["official_outs"] > 0
                 and delta <= 5 and delta <= .01 * max(row["native_outs"], row["official_outs"])
                 and row["range_runs"] is not None)
        assert valid == row["measurement_valid"]
    output = dict(status="verified_completed_milestone_not_a_predictive_win", identities_reparsed=4529,
                  leaderboard_captures_reparsed=len(source["captures"]), qualified_annual_rows=qualified.height,
                  final_review_sha256=sha256_file(final_path), production_changed=False,
                  additional_2026_data_ingested_or_used=False,
                  hashes={**hashes, str(Path(__file__)): sha256_file(Path(__file__)), str(final_path): sha256_file(final_path)})
    path = BASE / "milestone-verification.json"
    if path.exists():
        assert json.loads(path.read_text(encoding="utf8")) == output
    else:
        save(path, output); save(PUBLIC / path.name, output)
    protections()
    print(json.dumps({k: v for k, v in output.items() if k != "hashes"}, indent=2))


if __name__ == "__main__":
    main()
