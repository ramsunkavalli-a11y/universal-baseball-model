"""Audit loaded payroll evidence without publishing private player-level terms."""
import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.hitter_contract_reserve import contract_source_usable
from universal_baseball.storage import sha256_file

ROOT = Path("C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/universal-baseball-model/reports/generated")
OUT = Path("model_artifacts/hitter-contract-reserve-v2-2026-09-22/contract-source-audit.json")


def verify():
    report = json.loads(OUT.read_text())
    for name, digest in report["sources"].items():
        assert sha256_file(Path(name)) == digest, name
    assert report["contract_model_fitted"] is False
    assert report["eligible_historical_forecast_origins"] == []
    assert report["private_player_terms_published"] is False
    print(json.dumps({"status": "source_audit_verified", "contract_model_fitted": False}))


def main():
    bridge = ROOT/"historical-contract-bridge/2025"
    meta = json.loads((bridge/"report.json").read_text())
    paths = [bridge/"report.json", bridge/"valuation-ready-terms.parquet",
        ROOT/"league-control/2026-09-08/contract-year-liabilities.parquet",
        *[ROOT/f"fangraphs-opening-day-workbooks/{y}/opening-day-control-baseline.parquet" for y in [2023, 2024, 2025]],
        Path(__file__).relative_to(Path.cwd()), Path("src/universal_baseball/hitter_contract_reserve.py"),
        Path("docs/hitter-contract-reserve-v2-plan.md")]
    hashes = {str(p): sha256_file(p) for p in paths}
    # Contract data only. Never open current player forecasts, vesting outcomes or economics outputs.
    terms = pl.read_parquet(bridge/"valuation-ready-terms.parquet")
    counts = terms.group_by("payroll_year", "valuation_treatment").len().sort("payroll_year", "valuation_treatment").to_dicts()
    snapshot = meta["source_created_at"]
    loaded = [{"source": "2025 Cot's retrospective bridge", "snapshot_created": snapshot,
        "player_rows": meta["player_rows"], "accepted_identity_rows": meta["accepted_identity_rows"],
        "annual_term_rows": terms.height, "term_counts": counts,
        "has_signing_amendment_dates": False, "event_history_certified_for_opportunity": False,
        "reason": "2025-2029 payroll years from a post-2025 snapshot, not a historical salary training panel",
        "eligible_origins_2016_2023": [y for y in range(2016, 2024) if contract_source_usable(snapshot, y)]}]
    current = paths[2]
    # Aggregate/schema-only inspection of the already imported current workbooks.
    shape = pl.scan_parquet(current).select(pl.len().alias("rows"), pl.col("player_id").n_unique().alias("unique_ids"),
        pl.col("payroll_year").min().alias("first_payroll_year"), pl.col("payroll_year").max().alias("last_payroll_year")).collect().row(0, named=True)
    loaded.append({"source": "2026 FanGraphs imported payroll liabilities", "as_of": "2026-09-08", **shape,
        "has_signing_amendment_dates": False, "eligible_origins_2016_2023": [],
        "reason": "Current contract-cost inputs do not reconstruct what was known at older forecast cutoffs"})
    for y in [2023, 2024, 2025]:
        p = ROOT/f"fangraphs-opening-day-workbooks/{y}/opening-day-control-baseline.parquet"
        schema = pl.read_parquet_schema(p)
        loaded.append({"source": f"{y} Opening Day control", "rows": pl.scan_parquet(p).select(pl.len()).collect().item(),
            "columns": list(schema), "has_salary_or_guarantee": False,
            "reason": "Service/options/role information, not salaries or remaining guaranteed money"})
    report = {"status": "contract_test_blocked_historical_source_gap", "sources": hashes, "loaded_sources": loaded,
        "eligible_historical_forecast_origins": [], "contract_model_fitted": False,
        "private_player_terms_published": False, "protected_outcomes_used": False, "forecast_changed": False,
        "user_confirmation": "User confirmed no earlier payroll files are available locally",
        "not_a_negative_model_result": True,
        "needed": ["Stable player IDs plus salary amounts and effective/announcement dates for earlier cohorts",
            "Guaranteed versus option/opt-out years; all amendments and missing/unsigned states",
            "Retired/released/injured players retained, not a present-day survivor list",
            "At least one training origin preceding two completed chronological test origins"],
        "public_source_check": {"historical_payroll_url": "https://www.fangraphs.com/roster-resource/payroll/giants?season=2023",
            "result": "Web access returned HTTP 403; no download or bypass attempted",
            "documentation": "https://blogs.fangraphs.com/the-2025-rosterresource-payroll-pages-are-live/",
            "limitation": "A historical season view still requires event-date and cohort-coverage certification"}}
    assert all(sha256_file(Path(p)) == digest for p, digest in hashes.items())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, allow_nan=False)+"\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": report["status"], "loaded_sources": len(loaded), "contract_model_fitted": False}))
    verify()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    if parser.parse_args().verify:
        verify()
    else:
        main()
