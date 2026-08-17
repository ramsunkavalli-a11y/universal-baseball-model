#!/usr/bin/env python3
"""Capture tracked-only Minor Savant history for the richer Current Talent gate.

This is explicit live-source I/O and is intended for a manual workflow only *after*
the tiny tracked-only source probe passes under the corrected BBE contract.

The date range is derived from already-certified MiLB player-game evidence and may
be truncated with ``--end-date`` for a development-only capture. Requests are split
into small deterministic chunks; exact response bytes, URLs, hashes, and status
metadata are retained before the common raw->canonical->reconciliation and broad
source-completeness paths run.

Transient HTTP/network failures receive a small bounded retry/backoff. A chunk is
never accepted unless its final successful response passes the exact CSV/schema
contract; schema drift, empty content, and other semantic failures fail closed.
"""

from __future__ import annotations

import argparse
from datetime import date
import hashlib
import io
import json
from pathlib import Path
import time
from typing import Callable

import polars as pl
import requests

from universal_baseball.current_talent_batted_ball_materialization import (
    RAW_SAVANT_BBE_FIELDS,
    build_tracking_environment_completeness,
    load_certified_player_game_environments,
    materialize_reconciled_tracked_bbe,
    read_retained_savant_csv_tree,
)
from universal_baseball.current_talent_savant_minors import (
    DEFAULT_TRACKED_MINOR_CHUNK_DAYS,
    plan_tracked_minor_savant_requests,
)


USER_AGENT = (
    "universal-baseball-model/0.1 "
    "(public baseball research; tracked Minor Savant historical materialization)"
)
TRANSIENT_HTTP_STATUS = frozenset({429, 500, 502, 503, 504})
DEFAULT_MAX_FETCH_ATTEMPTS = 4
DEFAULT_RETRY_BACKOFF_SECONDS = 2.0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--certified-milb-root", type=Path, required=True)
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--end-date", type=date.fromisoformat)
    parser.add_argument("--chunk-days", type=int, default=DEFAULT_TRACKED_MINOR_CHUNK_DAYS)
    return parser.parse_args()


def _certified_date_bounds(root: Path, season: int) -> tuple[date, date]:
    paths = sorted(root.rglob(f"current_talent_game_summary_{season}_*.parquet"))
    if not paths:
        raise ValueError(f"no certified {season} MiLB game summaries under {root}")
    dates: list[date] = []
    for path in paths:
        frame = pl.read_parquet(path).select(
            pl.col("game_date").cast(pl.String).str.to_date(strict=False).alias("game_date")
        )
        if frame.filter(pl.col("game_date").is_null()).height:
            raise ValueError(f"certified MiLB summary contains invalid game_date: {path}")
        minimum = frame.get_column("game_date").min()
        maximum = frame.get_column("game_date").max()
        if minimum is not None:
            dates.append(minimum)
        if maximum is not None:
            dates.append(maximum)
    if not dates:
        raise ValueError(f"certified {season} MiLB summaries contain no game dates")
    return min(dates), max(dates)


def _validate_response_csv(content: bytes, *, request_url: str) -> tuple[int, int]:
    if not content.strip():
        raise ValueError(f"tracked Minor Savant returned empty bytes: {request_url}")
    try:
        frame = pl.read_csv(
            io.BytesIO(content),
            infer_schema=False,
            null_values=["", "null", "NA"],
            ignore_errors=False,
        )
    except Exception as exc:
        preview = content[:300].decode("utf-8", errors="replace")
        raise ValueError(
            f"tracked Minor Savant response is not readable CSV for {request_url}: {preview!r}"
        ) from exc
    missing = sorted(set(RAW_SAVANT_BBE_FIELDS) - set(frame.columns))
    if missing:
        raise ValueError(
            f"tracked Minor Savant response missing fields for {request_url}: {missing}"
        )
    return int(frame.height), len(frame.columns)


def _fetch_with_retry(
    session: requests.Session,
    url: str,
    *,
    timeout_seconds: int = 120,
    max_attempts: int = DEFAULT_MAX_FETCH_ATTEMPTS,
    base_backoff_seconds: float = DEFAULT_RETRY_BACKOFF_SECONDS,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> tuple[requests.Response, int]:
    """Fetch one chunk with bounded retry only for transient transport failures."""

    if max_attempts < 1:
        raise ValueError("max_attempts must be at least one")
    if base_backoff_seconds < 0:
        raise ValueError("base_backoff_seconds must be nonnegative")

    last_exception: requests.RequestException | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            response = session.get(url, timeout=timeout_seconds)
        except requests.RequestException as exc:
            last_exception = exc
            if attempt == max_attempts:
                raise
        else:
            if response.status_code not in TRANSIENT_HTTP_STATUS:
                response.raise_for_status()
                return response, attempt
            if attempt == max_attempts:
                response.raise_for_status()

        if attempt < max_attempts:
            sleep_fn(base_backoff_seconds * (2 ** (attempt - 1)))

    if last_exception is not None:  # pragma: no cover - loop always raises first
        raise last_exception
    raise RuntimeError("tracked Minor Savant retry loop ended unexpectedly")


def main() -> int:
    args = _parse_args()
    if args.chunk_days < 1:
        raise ValueError("chunk_days must be positive")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw_root = args.output_dir / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)

    certified_start, certified_end = _certified_date_bounds(args.certified_milb_root, args.season)
    capture_end = certified_end if args.end_date is None else min(certified_end, args.end_date)
    if capture_end < certified_start:
        raise ValueError(
            f"requested capture end {capture_end} precedes certified season start {certified_start}"
        )
    plan = plan_tracked_minor_savant_requests(
        certified_start,
        capture_end,
        chunk_days=args.chunk_days,
    )

    manifest_rows: list[dict[str, object]] = []
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    try:
        for request in plan:
            response, fetch_attempts = _fetch_with_retry(session, request.request_url)
            content = response.content
            row_count, column_count = _validate_response_csv(
                content, request_url=request.request_url
            )
            path = raw_root / request.raw_filename
            path.write_bytes(content)
            manifest_rows.append(
                {
                    "start_date": request.start_date,
                    "end_date": request.end_date,
                    "request_url": request.request_url,
                    "retrieved_url": response.url,
                    "status_code": int(response.status_code),
                    "fetch_attempts": fetch_attempts,
                    "content_type": response.headers.get("content-type", ""),
                    "response_sha256": hashlib.sha256(content).hexdigest(),
                    "response_bytes": len(content),
                    "row_count": row_count,
                    "column_count": column_count,
                    "raw_file": str(path),
                }
            )
    finally:
        session.close()

    request_manifest = pl.DataFrame(manifest_rows).sort("start_date")
    request_manifest_path = args.output_dir / "request_manifest.csv"
    request_manifest.write_csv(request_manifest_path)

    raw, raw_file_manifest = read_retained_savant_csv_tree(raw_root)
    certified = load_certified_player_game_environments(
        args.certified_milb_root,
        season=args.season,
        source_family="MILB_SAVANT_TRACKED",
    )
    completeness, completeness_metrics = build_tracking_environment_completeness(
        raw,
        certified,
        source_family="MILB_SAVANT_TRACKED",
    )
    reconciled = materialize_reconciled_tracked_bbe(
        raw,
        certified,
        source_family="MILB_SAVANT_TRACKED",
    )
    if reconciled.is_empty():
        raise ValueError("historical tracked Minor Savant capture produced zero canonical model BBE")

    reconciled_path = args.output_dir / (
        f"reconciled_tracked_bbe_{args.season}_milb_savant_tracked.parquet"
    )
    reconciled_csv = args.output_dir / (
        f"reconciled_tracked_bbe_{args.season}_milb_savant_tracked.csv"
    )
    raw_file_manifest_path = args.output_dir / "raw_file_manifest.csv"
    completeness_path = args.output_dir / "tracking_completeness_by_environment.csv"
    reconciled.write_parquet(reconciled_path, compression="zstd")
    reconciled.write_csv(reconciled_csv)
    raw_file_manifest.write_csv(raw_file_manifest_path)
    completeness.write_csv(completeness_path)

    by_tier = (
        reconciled.group_by(["source_capability_tier", "level_group", "league_id"])
        .agg(
            pl.len().cast(pl.Int64).alias("model_bbe"),
            pl.col("game_pk").n_unique().cast(pl.Int64).alias("game_count"),
            pl.col("player_id").n_unique().cast(pl.Int64).alias("player_count"),
            pl.col("game_date").min().alias("first_game_date"),
            pl.col("game_date").max().alias("last_game_date"),
            pl.col("launch_speed").mean().alias("mean_exit_velocity"),
            pl.col("sweet_spot").mean().alias("sweet_spot_share"),
        )
        .sort(["level_group", "league_id", "source_capability_tier"])
    )
    by_tier_path = args.output_dir / "capability_summary.csv"
    by_tier.write_csv(by_tier_path)

    report = {
        "report_schema_version": "0.3",
        "scope": "manual_tracked_minor_savant_historical_capture",
        "live_source_io": True,
        "season": args.season,
        "certified_game_date_start": certified_start.isoformat(),
        "certified_game_date_end": certified_end.isoformat(),
        "capture_end_date": capture_end.isoformat(),
        "chunk_days": args.chunk_days,
        "request_chunk_count": len(plan),
        "request_semantics": "tracked_only_helper_v1",
        "transient_retry_policy": {
            "max_attempts": DEFAULT_MAX_FETCH_ATTEMPTS,
            "base_backoff_seconds": DEFAULT_RETRY_BACKOFF_SECONDS,
            "status_codes": sorted(TRANSIENT_HTTP_STATUS),
        },
        "max_fetch_attempts_observed": int(request_manifest.get_column("fetch_attempts").max()),
        "canonical_model_bbe_contract": "result_producing_non_bunt_pitch_grain_v1",
        "raw_response_bytes": int(request_manifest.get_column("response_bytes").sum()),
        "raw_response_rows": int(request_manifest.get_column("row_count").sum()),
        "broad_tracking_completeness": completeness_metrics,
        "broad_tracking_completeness_by_environment": completeness.to_dicts(),
        "canonical_model_bbe_count": int(reconciled.height),
        "canonical_game_count": int(reconciled.get_column("game_pk").n_unique()),
        "canonical_player_count": int(reconciled.get_column("player_id").n_unique()),
        "source_capability_tiers": by_tier.to_dicts(),
        "outputs": {
            "request_manifest": str(request_manifest_path),
            "raw_file_manifest": str(raw_file_manifest_path),
            "raw_root": str(raw_root),
            "tracking_completeness_by_environment": str(completeness_path),
            "reconciled_parquet": str(reconciled_path),
            "reconciled_csv": str(reconciled_csv),
            "capability_summary": str(by_tier_path),
        },
        "decision_boundary": (
            "This capture provides observed tracked MiLB evidence only for returned tracked source "
            "rows. Capability labels must not be generalized to unobserved games at the same level."
        ),
    }
    report_path = args.output_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
