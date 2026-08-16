#!/usr/bin/env python
"""Primary screened-bin value validation for AA, High-A, and Single-A.

The audit deliberately reuses the already-tested final-screen environment loader,
split-half evaluator, and five-fold predictive validator. It changes only the
source assets and pool grouping: peers may contribute priors only within the
same affiliated level. Direct estimates are a valid outcome.

This is a primary 2025 gate. A positive shrinkage rule is not promoted from this
script alone; it merely nominates a pre-specified strength for an independent
season confirmation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import audit_milb_bin_value_cross_validation as cv
import audit_milb_bin_value_stability as stability
import audit_screened_bin_value_confirmation as screened
from universal_baseball.certification import read_quarantined_csv


ASSET_GROUP = {
    "2025_5_aa_pbp.csv": "AA",
    "2025_5_a+_pbp.csv": "HIGH_A",
    "2025_5_a_pbp.csv": "SINGLE_A",
}
GAMES_PER_ENVIRONMENT = 45


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("data/quarantine/middle-level-bin-value-validation"),
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("reports/generated/middle-level-bin-value-validation"),
    )
    return parser.parse_args()


def _discover_groups(work_dir: Path) -> tuple[dict[int, str], dict[str, dict[str, Any]]]:
    """Download each asset once and derive actual league IDs from its certified inventory."""

    mapping: dict[int, str] = {}
    metadata_by_path: dict[str, dict[str, Any]] = {}
    for asset, group in ASSET_GROUP.items():
        path = work_dir / asset
        metadata = screened.download_file(
            f"{screened.base.BASE_URL}/{asset}", path, timeout_seconds=240
        )
        metadata_by_path[str(path)] = metadata
        frame = read_quarantined_csv(path)
        if frame.is_empty():
            raise RuntimeError(f"source asset is empty: {asset}")
        orders = stability._inventory_orders(
            frame, asset, max_games=GAMES_PER_ENVIRONMENT
        )
        if not orders:
            raise RuntimeError(f"source asset has no game inventory: {asset}")
        for (_, league_id, _), games in orders.items():
            league_id = int(league_id)
            previous = mapping.get(league_id)
            if previous is not None and previous != group:
                raise RuntimeError(
                    f"league_id={league_id} appears in both {previous} and {group} assets"
                )
            mapping[league_id] = group
            if len(games) < GAMES_PER_ENVIRONMENT:
                raise RuntimeError(
                    f"{asset} league_id={league_id} has only {len(games)} sampled games; "
                    f"expected {GAMES_PER_ENVIRONMENT}"
                )
    return mapping, metadata_by_path


def _split_robust_strengths(split_pooling: dict[str, Any], group: str) -> list[int]:
    return [
        int(row["prior_strength"])
        for row in split_pooling["group_evaluations"]
        if row["pool_group"] == group
        and int(row["prior_strength"]) > 0
        and float(row["mae_delta_vs_direct"]) <= 0
        and float(row["rmse_delta_vs_direct"]) <= 0
        and float(row["occurrence_weighted_mae_delta_vs_direct"]) <= 0
    ]


def _candidate_for_confirmation(
    fivefold: dict[str, Any],
    group: str,
    shared_robust: list[int],
) -> dict[str, Any]:
    if not shared_robust:
        return {
            "prior_strength": 0,
            "reason": "no positive strength is robust in both split-half and five-fold validation",
        }
    evaluations = fivefold["group_evaluations"][group]
    eligible = [
        row for row in evaluations if int(row["prior_strength"]) in set(shared_robust)
    ]
    best = min(
        eligible,
        key=lambda row: (float(row["cell_mae"]), int(row["prior_strength"])),
    )
    return {
        "prior_strength": int(best["prior_strength"]),
        "reason": "lowest five-fold cell MAE among strengths robust in both primary diagnostics; requires independent-season confirmation",
        "metrics": {
            key: float(best[key])
            for key in ("cell_mae", "cell_rmse", "event_mae", "event_rmse")
        },
    }


def main() -> int:
    args = parse_args()
    args.work_dir.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)

    group_by_league, cached_metadata = _discover_groups(args.work_dir)
    if set(group_by_league.values()) != set(ASSET_GROUP.values()):
        raise RuntimeError(f"not all target levels were discovered: {group_by_league}")

    # _load_environment_frames normally downloads the asset itself. The discovery
    # pass above already captured the exact bytes, so reuse those files rather than
    # paying for a second network transfer.
    original_download = screened.download_file

    def cached_download(url: str, destination: Path, **_: Any) -> dict[str, Any]:
        key = str(destination)
        if key not in cached_metadata or not destination.exists():
            return original_download(url, destination, timeout_seconds=240)
        return cached_metadata[key]

    screened.download_file = cached_download
    screened.POOL_GROUP_BY_LEAGUE = dict(group_by_league)
    try:
        frames, meta = screened._load_environment_frames(
            assets=tuple(ASSET_GROUP),
            work_dir=args.work_dir,
        )
    finally:
        screened.download_file = original_download

    discovered_groups = {str(row["pool_group"]) for row in meta.values()}
    if discovered_groups != set(ASSET_GROUP.values()):
        raise RuntimeError(f"unexpected pool groups: {sorted(discovered_groups)}")

    split_reports, split_pooling = screened._split_half_reports(frames, meta)
    fivefold = screened._fivefold(frames, meta)

    decisions: dict[str, Any] = {}
    for group in sorted(discovered_groups):
        split_robust = _split_robust_strengths(split_pooling, group)
        fivefold_robust = cv._robust_strengths(fivefold["group_evaluations"][group])
        shared = sorted(set(split_robust) & set(fivefold_robust))
        decisions[group] = {
            "split_half_robust_positive_strengths": split_robust,
            "fivefold_robust_positive_strengths": fivefold_robust,
            "shared_robust_positive_strengths": shared,
            "candidate_for_independent_confirmation": _candidate_for_confirmation(
                fivefold, group, shared
            ),
        }

    payload = {
        "report_schema_version": 1,
        "status": "primary_2025_middle_level_screened_bin_value_validation",
        "assets": ASSET_GROUP,
        "games_per_environment": GAMES_PER_ENVIRONMENT,
        "pool_group_by_league": group_by_league,
        "environment_meta": meta,
        "split_half_reports": split_reports,
        "split_half_pooling": split_pooling,
        "fivefold": fivefold,
        "decisions": decisions,
        "interpretation": (
            "Positive pooling is only a nomination from this 2025 primary gate. "
            "A level must have a strength robust in both split-half and five-fold "
            "validation, and that pre-specified strength must then survive a separate "
            "season before production promotion. Direct/unpooled is an accepted result."
        ),
    }
    (args.report_dir / "middle_level_bin_value_validation.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        "# 2025 middle-level screened-bin value validation",
        "",
        f"- Games per actual league environment: {GAMES_PER_ENVIRONMENT}",
        f"- Environments: {len(meta)}",
        "- Final foul-air-screened Performance bins only",
        "- Priors are same-level peers only; no AAA/universal-MiLB transfer",
        "",
    ]
    for group in sorted(decisions):
        result = decisions[group]
        lines.extend(
            [
                f"## {group}",
                "",
                f"- Split-half robust strengths: {result['split_half_robust_positive_strengths']}",
                f"- Five-fold robust strengths: {result['fivefold_robust_positive_strengths']}",
                f"- Shared robust strengths: {result['shared_robust_positive_strengths']}",
                f"- Candidate for independent confirmation: `{result['candidate_for_independent_confirmation']}`",
                "",
            ]
        )
    lines.append(
        "No positive strength is production-approved by this report alone."
    )
    summary = "\n".join(lines) + "\n"
    (args.report_dir / "middle_level_bin_value_validation.md").write_text(
        summary, encoding="utf-8"
    )
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
