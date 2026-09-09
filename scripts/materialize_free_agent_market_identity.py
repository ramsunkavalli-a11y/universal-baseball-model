#!/usr/bin/env python3
"""Attach pinned Chadwick MLBAM identities to free-agent market rows."""

from __future__ import annotations

import argparse
from datetime import date
from hashlib import sha256
import json
from pathlib import Path

import polars as pl
import requests

from universal_baseball.chadwick import (
    CHADWICK_ARCHIVE_URL,
    CHADWICK_SNAPSHOT_SHA,
    build_fangraphs_mlbam_crosswalk,
    read_chadwick_people_archive,
)
from universal_baseball.storage import write_canonical_parquet


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--source-root", type=Path,
        default=Path("reports/generated/free-agent-market-source"),
    )
    parser.add_argument("--chadwick-archive", type=Path)
    parser.add_argument(
        "--output-root", type=Path,
        default=Path("reports/generated/free-agent-market-identity"),
    )
    return parser.parse_args()


def _archive(args: argparse.Namespace, output_root: Path) -> Path:
    if args.chadwick_archive is not None:
        return args.chadwick_archive
    capture = output_root / "captures" / f"chadwick-{CHADWICK_SNAPSHOT_SHA}.zip"
    capture.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(
        CHADWICK_ARCHIVE_URL,
        headers={"User-Agent": "universal-baseball-model/1.0 public research"},
        timeout=60,
    )
    response.raise_for_status()
    capture.write_bytes(response.content)
    return capture


def main() -> int:
    args = _args()
    source = pl.read_parquet(
        args.source_root / args.as_of_date.isoformat()
        / "tables/fangraphs-free-agent-tracker.parquet"
    )
    output_root = args.output_root / args.as_of_date.isoformat()
    archive = _archive(args, output_root)
    archive_digest = sha256(archive.read_bytes()).hexdigest()
    people = read_chadwick_people_archive(archive)
    crosswalk = build_fangraphs_mlbam_crosswalk(
        people, source.get_column("fangraphs_id").to_list()
    )
    result = source.join(crosswalk, on="fangraphs_id", how="left", validate="m:1")
    if result.height != source.height:
        raise RuntimeError("free-agent identity join changed source row count")
    result = result.with_columns(
        pl.col("crosswalk_status").fill_null("missing_fangraphs_crosswalk").alias(
            "identity_status"
        )
    ).drop("crosswalk_status").sort(
        ["free_agent_year", "source_row_sequence"]
    )
    tables = output_root / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    storage = write_canonical_parquet(
        result,
        tables / "free-agent-market-identities.parquet",
        table_name="free_agent_market_identities",
    ).as_record()
    signed = result.filter(
        pl.col("contract_value_status") == "reported_guaranteed_terms"
    )
    one_year = signed.filter(pl.col("contract_years") == 1)
    report = {
        "report_schema_version": "0.1",
        "gate": "free_agent_market_identity_crosswalk",
        "as_of_date": args.as_of_date.isoformat(),
        "chadwick_commit": CHADWICK_SNAPSHOT_SHA,
        "chadwick_archive_sha256": archive_digest,
        "source_rows": source.height,
        "identity_status": result.group_by("identity_status").len().sort(
            "identity_status"
        ).to_dicts(),
        "signed_contract_rows": signed.height,
        "signed_contract_rows_with_mlbam": signed.filter(
            pl.col("player_id").is_not_null()
        ).height,
        "one_year_contract_rows": one_year.height,
        "one_year_contract_rows_with_mlbam": one_year.filter(
            pl.col("player_id").is_not_null()
        ).height,
        "name_matching_used": False,
        "storage": storage,
    }
    (output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
