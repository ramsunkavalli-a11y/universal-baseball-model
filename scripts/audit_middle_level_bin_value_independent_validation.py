#!/usr/bin/env python
"""Independent 2024 confirmation of pre-specified middle-level bin pooling.

The candidate strengths in this file were selected from the 2025 primary gate
*before* this script was run against 2024:

- AA: 75 prior-equivalent occurrences
- High-A: 150 prior-equivalent occurrences
- Single-A: 25 prior-equivalent occurrences

The independent season uses final foul-air-screened Performance bins, 45 games
per actual league, same-level peer priors only, and the existing leakage-safe
five-fold validator. Production promotion requires the pre-specified strength
to improve or tie direct estimation on all four held-out summaries: cell MAE,
cell RMSE, event MAE, and event RMSE. The full strength grid is retained only as
secondary diagnostics and must not be used to change the pre-specified choice.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import audit_middle_level_bin_value_validation as primary
import audit_milb_bin_value_cross_validation as cv
import audit_screened_bin_value_confirmation as screened


ASSET_GROUP = {
    "2024_6_aa_pbp.csv": "AA",
    "2024_6_a+_pbp.csv": "HIGH_A",
    "2024_6_a_pbp.csv": "SINGLE_A",
}
PRE_SPECIFIED_STRENGTH = {
    "AA": 75,
    "HIGH_A": 150,
    "SINGLE_A": 25,
}
GAMES_PER_ENVIRONMENT = 45
METRICS = ("cell_mae", "cell_rmse", "event_mae", "event_rmse")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("data/quarantine/middle-level-bin-value-independent-validation"),
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("reports/generated/middle-level-bin-value-independent-validation"),
    )
    return parser.parse_args()


def _comparison(evaluations: list[dict[str, Any]], strength: int) -> dict[str, Any]:
    direct = next(row for row in evaluations if int(row["prior_strength"]) == 0)
    candidate = next(
        row for row in evaluations if int(row["prior_strength"]) == int(strength)
    )
    metrics = {
        metric: {
            "direct": float(direct[metric]),
            "candidate": float(candidate[metric]),
            "delta": float(candidate[metric]) - float(direct[metric]),
            "improved_or_tied": float(candidate[metric]) <= float(direct[metric]),
        }
        for metric in METRICS
    }
    return {
        "pre_specified_strength": int(strength),
        "metrics": metrics,
        "pass": all(row["improved_or_tied"] for row in metrics.values()),
        "secondary_robust_strengths": cv._robust_strengths(evaluations),
    }


def main() -> int:
    args = parse_args()
    args.work_dir.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)

    # Reuse the primary gate's tested discovery/cache path, changing only the
    # independent-season asset set. No 2024 metric is consulted when choosing
    # PRE_SPECIFIED_STRENGTH above.
    original_assets = primary.ASSET_GROUP
    primary.ASSET_GROUP = dict(ASSET_GROUP)
    try:
        group_by_league, cached_metadata = primary._discover_groups(args.work_dir)
    finally:
        primary.ASSET_GROUP = original_assets

    if set(group_by_league.values()) != set(PRE_SPECIFIED_STRENGTH):
        raise RuntimeError(f"not all independent target levels were discovered: {group_by_league}")

    original_download = screened.download_file

    def cached_download(url: str, destination: Path, **_: Any) -> dict[str, Any]:
        key = str(destination)
        if key not in cached_metadata or not destination.exists():
            return original_download(url, destination, timeout_seconds=240)
        return cached_metadata[key]

    original_pool_map = screened.POOL_GROUP_BY_LEAGUE
    screened.download_file = cached_download
    screened.POOL_GROUP_BY_LEAGUE = dict(group_by_league)
    try:
        frames, meta = screened._load_environment_frames(
            assets=tuple(ASSET_GROUP),
            work_dir=args.work_dir,
        )
        fivefold = screened._fivefold(frames, meta)
    finally:
        screened.download_file = original_download
        screened.POOL_GROUP_BY_LEAGUE = original_pool_map

    discovered_groups = {str(row["pool_group"]) for row in meta.values()}
    if discovered_groups != set(PRE_SPECIFIED_STRENGTH):
        raise RuntimeError(f"unexpected independent pool groups: {sorted(discovered_groups)}")

    confirmations: dict[str, Any] = {}
    for group, strength in PRE_SPECIFIED_STRENGTH.items():
        confirmations[group] = _comparison(
            fivefold["group_evaluations"][group], strength
        )

    overall_pass = all(row["pass"] for row in confirmations.values())
    payload = {
        "report_schema_version": 1,
        "status": "independent_2024_middle_level_screened_bin_value_confirmation",
        "assets": ASSET_GROUP,
        "games_per_environment": GAMES_PER_ENVIRONMENT,
        "pre_specified_strengths": PRE_SPECIFIED_STRENGTH,
        "pool_group_by_league": group_by_league,
        "environment_meta": meta,
        "confirmations": confirmations,
        "overall_pass": overall_pass,
        "fivefold": fivefold,
        "interpretation": (
            "Only each group's pre-specified 2025-selected strength controls promotion. "
            "The 2024 full strength grid is secondary evidence and cannot be used to "
            "replace a failed pre-specified candidate."
        ),
    }
    (args.report_dir / "middle_level_bin_value_independent_validation.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        "# Independent 2024 middle-level screened-bin confirmation",
        "",
        f"- Games per actual league environment: {GAMES_PER_ENVIRONMENT}",
        f"- Environments: {len(meta)}",
        "- Candidate strengths were frozen from the 2025 primary gate before this run",
        "- Final foul-air-screened Performance bins only",
        "- Same-level peer priors only",
        "",
    ]
    for group in sorted(confirmations):
        result = confirmations[group]
        lines.extend(
            [
                f"## {group}",
                "",
                f"- Pre-specified strength: **{result['pre_specified_strength']}**",
                f"- Independent pass: **{result['pass']}**",
                f"- Secondary robust strengths: {result['secondary_robust_strengths']}",
            ]
        )
        for metric, values in result["metrics"].items():
            lines.append(
                f"- {metric}: direct={values['direct']:.6f}, candidate={values['candidate']:.6f}, "
                f"delta={values['delta']:+.6f}, improved_or_tied={values['improved_or_tied']}"
            )
        lines.append("")
    lines.extend(
        [
            f"Overall all-level confirmation pass: **{overall_pass}**",
            "",
            "A failed level remains direct/unpooled unless a new pre-registered validation cycle is designed; this independent season is not used to tune a replacement strength.",
            "",
        ]
    )
    summary = "\n".join(lines)
    (args.report_dir / "middle_level_bin_value_independent_validation.md").write_text(
        summary, encoding="utf-8"
    )
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
