#!/usr/bin/env python
"""Compare direct MiLB Performance-bin values with leakage-safe pooling.

Input is the JSON output of ``audit_milb_bin_value_stability.py``. This is a
statistical diagnostic only: it does not promote a player score or production
weight. Candidate split halves are training evidence; reference halves are held
out. For each target environment/bin, shrinkage priors exclude the target
environment and all reference halves.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

from universal_baseball.bin_value_pooling import (
    DEFAULT_PRIOR_STRENGTHS,
    evaluate_split_half_pooling,
)


POOL_GROUP_BY_LEAGUE = {
    112: "AAA",
    117: "AAA",
    121: "ROOKIE_COMPLEX",
    124: "ROOKIE_COMPLEX",
    130: "ROOKIE_COMPLEX",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=Path(
            "reports/generated/milb-bin-value-stability/"
            "milb_bin_value_stability.json"
        ),
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("reports/generated/milb-bin-value-pooling"),
    )
    return parser.parse_args()


def _read_json(path: Path) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("stability report must be a JSON object")
    return payload, sha256(raw).hexdigest()


def _group_rows(result: Mapping[str, Any], group: str) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in result["group_evaluations"]
        if row["pool_group"] == group
    ]


def _direct_row(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return next(row for row in rows if int(row["prior_strength"]) == 0)


def _robust_improvement_strengths(rows: list[dict[str, Any]]) -> list[int]:
    """Strengths that do not worsen MAE, RMSE, or occurrence-weighted MAE."""

    direct = _direct_row(rows)
    result: list[int] = []
    for row in rows:
        strength = int(row["prior_strength"])
        if strength == 0:
            continue
        if (
            float(row["mae"]) <= float(direct["mae"])
            and float(row["rmse"]) <= float(direct["rmse"])
            and float(row["occurrence_weighted_mae"])
            <= float(direct["occurrence_weighted_mae"])
        ):
            result.append(strength)
    return result


def _candidate_for_next_validation(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Choose a diagnostic candidate, never a production policy.

    A positive candidate must improve all three principal error summaries over
    direct means. Among those robust strengths, minimize unweighted MAE and use
    the smaller strength as a deterministic tie-breaker. If none qualify, keep
    the direct/unpooled baseline.
    """

    robust = set(_robust_improvement_strengths(rows))
    eligible = [
        row
        for row in rows
        if int(row["prior_strength"]) in robust
    ]
    if not eligible:
        direct = _direct_row(rows)
        return {
            "prior_strength": 0,
            "reason": "no positive strength improved MAE, RMSE, and occurrence-weighted MAE together",
            "metrics": {
                key: direct[key]
                for key in (
                    "mae",
                    "rmse",
                    "occurrence_weighted_mae",
                    "max_absolute_error",
                )
            },
        }
    best = min(
        eligible,
        key=lambda row: (float(row["mae"]), int(row["prior_strength"])),
    )
    return {
        "prior_strength": int(best["prior_strength"]),
        "reason": "diagnostic strength with lowest MAE among strengths that improve all three principal error summaries",
        "metrics": {
            key: best[key]
            for key in (
                "mae",
                "rmse",
                "occurrence_weighted_mae",
                "max_absolute_error",
            )
        },
    }


def main() -> int:
    args = parse_args()
    args.report_dir.mkdir(parents=True, exist_ok=True)
    stability, input_sha256 = _read_json(args.input)
    environment_reports = stability.get("environment_reports") or []
    if not environment_reports:
        raise ValueError("stability report contains no environment_reports")

    same_group = evaluate_split_half_pooling(
        environment_reports,
        pool_group_by_league=POOL_GROUP_BY_LEAGUE,
        prior_strengths=DEFAULT_PRIOR_STRENGTHS,
        scope="group",
    )
    all_milb = evaluate_split_half_pooling(
        environment_reports,
        pool_group_by_league=POOL_GROUP_BY_LEAGUE,
        prior_strengths=DEFAULT_PRIOR_STRENGTHS,
        scope="all",
    )

    decisions: dict[str, Any] = {}
    for group in same_group["pool_groups"]:
        rows = _group_rows(same_group, str(group))
        direct = _direct_row(rows)
        decisions[str(group)] = {
            "direct_metrics": {
                key: direct[key]
                for key in (
                    "mae",
                    "rmse",
                    "occurrence_weighted_mae",
                    "max_absolute_error",
                )
            },
            "robust_improvement_strengths": _robust_improvement_strengths(rows),
            "candidate_for_next_validation": _candidate_for_next_validation(rows),
            "best_strength_by_metric": same_group["best_strength_by_group"][str(group)],
        }

    payload = {
        "report_schema_version": 1,
        "status": "diagnostic_pooling_comparison_not_production_weights",
        "input_path": str(args.input),
        "input_sha256": input_sha256,
        "pool_group_by_league": {
            str(key): value for key, value in POOL_GROUP_BY_LEAGUE.items()
        },
        "prior_strength_interpretation": "prior-equivalent candidate occurrences",
        "same_group_leave_one_environment_out": same_group,
        "all_milb_leave_one_environment_out": all_milb,
        "diagnostic_decisions": decisions,
        "interpretation": (
            "The held-out reference half never contributes to a prior, and a target "
            "environment never contributes to its own prior. Positive shrinkage is "
            "not presumed beneficial. The candidate strength is only a next-validation "
            "candidate when it improves MAE, RMSE, and occurrence-weighted MAE together; "
            "otherwise the diagnostic retains direct means for that pool group."
        ),
    }
    (args.report_dir / "milb_bin_value_pooling.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        "# MiLB Performance-bin pooling diagnostic",
        "",
        "**Diagnostic only. No pooling rule or sampled bin value is promoted to production.**",
        "",
        f"- Stability input SHA-256: `{input_sha256}`",
        f"- Environments: {same_group['environment_count']}",
        f"- Environment-bin observations: {same_group['observation_count']}",
        f"- Prior strengths tested: {same_group['prior_strengths']}",
        "- Prior construction: candidate halves of other environments only; target environment and all held-out halves excluded",
        "",
        "## Same-group leave-one-environment-out results",
        "",
    ]
    for group in same_group["pool_groups"]:
        group = str(group)
        rows = _group_rows(same_group, group)
        direct = _direct_row(rows)
        decision = decisions[group]
        candidate_strength = decision["candidate_for_next_validation"]["prior_strength"]
        candidate = next(
            row for row in rows if int(row["prior_strength"]) == candidate_strength
        )
        lines.extend(
            [
                f"### {group}",
                "",
                f"- Direct: MAE={direct['mae']:.4f}, RMSE={direct['rmse']:.4f}, occurrence-weighted MAE={direct['occurrence_weighted_mae']:.4f}, max |error|={direct['max_absolute_error']:.4f}",
                f"- Robust positive strengths: {decision['robust_improvement_strengths']}",
                f"- Next-validation candidate strength: **{candidate_strength}** prior-equivalent occurrences",
                f"- Candidate: MAE={candidate['mae']:.4f}, RMSE={candidate['rmse']:.4f}, occurrence-weighted MAE={candidate['occurrence_weighted_mae']:.4f}, max |error|={candidate['max_absolute_error']:.4f}",
                f"- Reason: {decision['candidate_for_next_validation']['reason']}",
                "",
            ]
        )

    lines.extend(
        [
            "## Interpretation",
            "",
            "This comparison is intentionally capable of returning different answers by level. A universal MiLB shrinkage constant is not accepted merely because it improves an aggregate metric. The next gate should validate any positive level-specific candidate on an independent split/season or expand the official sample if the signal does not replicate.",
            "",
        ]
    )
    summary = "\n".join(lines)
    (args.report_dir / "milb_bin_value_pooling.md").write_text(
        summary, encoding="utf-8"
    )
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
