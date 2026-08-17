#!/usr/bin/env python3
"""Render durable checkpoint files from one richer 2022 development report.

This renderer is deterministic and performs no model fitting or source I/O. The
result remains an artifact until explicitly reviewed/committed; a generated PASS
is not itself authorization to inspect 2023 before the checkpoint is persisted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


EXPECTED_GATE = "current_talent_batted_ball_quality_2022_development"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def _fmt(value: object, digits: int = 6) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, bool):
        return "PASS" if value else "FAIL"
    if isinstance(value, (int, str)):
        return str(value)
    return f"{float(value):.{digits}f}"


def render_checkpoint(report: dict[str, object], *, report_sha256: str) -> tuple[str, dict[str, object]]:
    if report.get("gate") != EXPECTED_GATE:
        raise ValueError("unexpected richer development report gate")
    if report.get("confirmation_data_present") is not False:
        raise ValueError("development checkpoint cannot contain confirmation data")
    if report.get("development_cutoffs") != ["2022-07-15", "2022-08-01", "2022-09-01"]:
        raise ValueError("development cutoff contract changed")

    eligible = bool(report["eligible_for_fixed_2023_confirmation"])
    status = "DEVELOPMENT PASSED" if eligible else "DEVELOPMENT FAILED"
    scores = dict(report["proper_score_summary"])
    calibration = dict(report["calibration_summary"])
    non_mlb = dict(report["non_mlb_transport"])
    checks = dict(report["promotion_checks"])
    fit = dict(report["residual_fit_metrics"])

    lines = [
        "# Current Talent batted-ball richer development checkpoint",
        "",
        f"Status: **{status}**",
        "",
        "This checkpoint summarizes the fixed 2022 development gate for the first richer Current Talent challenger. It does not contain 2023 confirmation data and does not permit 2023 reselection.",
        "",
        "## Frozen candidate",
        "",
        "- Comparator: Baseline 2 `translated_multiseason_recency_empirical_bayes_v1`",
        "- Challenger: `baseline2_plus_ev_sweet_spot_contact_residual_v1`",
        "- Features: 180-day weighted mean EV + 8–32° sweet-spot share",
        "- Model BBE: result-producing, non-bunt, complete EV+LA, pitch-grain",
        "- Primary richer eligibility: >=20 complete tracked BBE",
        "- Residual L2: 0.01; no penalty search",
        "- Training snapshot: 2021-07-15 only",
        "- Development folds: 2022-07-15 / 2022-08-01 / 2022-09-01",
        "",
        "## Proper scores — equal-fold mean",
        "",
        f"- B2 log loss: **{_fmt(scores.get('baseline2_equal_fold_mean_log_loss'), 9)}**",
        f"- Richer log loss: **{_fmt(scores.get('richer_equal_fold_mean_log_loss'), 9)}**",
        f"- Richer − B2 log loss: **{_fmt(scores.get('richer_minus_baseline2_equal_fold_mean_log_loss'), 9)}**",
        f"- B2 Brier: **{_fmt(scores.get('baseline2_equal_fold_mean_brier'), 9)}**",
        f"- Richer Brier: **{_fmt(scores.get('richer_equal_fold_mean_brier'), 9)}**",
        f"- Richer − B2 Brier: **{_fmt(scores.get('richer_minus_baseline2_equal_fold_mean_brier'), 9)}**",
        f"- Richer log-loss fold wins: **{_fmt(scores.get('richer_log_loss_fold_wins'))}/3**",
        "",
        "## Calibration guardrail",
        "",
        f"- B2 mean absolute intercept error: {_fmt(calibration.get('baseline2_mean_abs_intercept_error'), 6)}",
        f"- Richer mean absolute intercept error: {_fmt(calibration.get('richer_mean_abs_intercept_error'), 6)}",
        f"- B2 mean absolute slope error: {_fmt(calibration.get('baseline2_mean_abs_slope_error'), 6)}",
        f"- Richer mean absolute slope error: {_fmt(calibration.get('richer_mean_abs_slope_error'), 6)}",
        "",
        "## Non-MLB transport",
        "",
        f"- Any-MiLB-evidence future core events: **{_fmt(non_mlb.get('combined_any_milb_evidence_future_core_events'))}**",
        f"- Any-MiLB-evidence equal-fold mean log-loss delta: **{_fmt(non_mlb.get('combined_any_milb_evidence_equal_fold_mean_log_loss_delta'), 9)}**",
        f"- Supported and improves: **{_fmt(non_mlb.get('combined_any_milb_evidence_supported_and_improves'))}**",
        f"- Failed meaningful capability tiers: **{len(non_mlb.get('failed_capability_tiers', []))}**",
        "",
        "## Promotion checks",
        "",
    ]
    for key, value in checks.items():
        lines.append(f"- `{key}`: **{_fmt(value)}**")
    lines.extend(
        [
            "",
            "## Training fit",
            "",
            f"- Training players: {_fmt(fit.get('training_player_count'))}",
            f"- Training future contact events: {_fmt(fit.get('training_future_contact_events'))}",
            f"- Initial mean contact log loss: {_fmt(fit.get('initial_mean_contact_log_loss'), 9)}",
            f"- Final mean contact log loss: {_fmt(fit.get('final_mean_contact_log_loss'), 9)}",
            f"- Optimizer iterations: {_fmt(fit.get('iterations'))}",
            f"- Converged: {_fmt(fit.get('converged'))}",
            "",
            "## Decision",
            "",
        ]
    )
    if eligible:
        lines.append(
            "All frozen development checks passed. After this checkpoint and its result JSON are reviewed and committed, the project may implement/run only the already-fixed 2023 confirmation protocol. No feature, BBE, threshold, penalty, date, or model-form search is authorized."
        )
    else:
        lines.append(
            "At least one frozen development check failed. Retain Baseline 2. Do not inspect 2023 richer performance to rescue this candidate; any alternative richer model requires a new predeclared challenger."
        )
    lines.extend(
        [
            "",
            f"Source report SHA-256: `{report_sha256}`",
            "",
        ]
    )

    result = {
        "result_schema_version": "0.1",
        "gate": EXPECTED_GATE,
        "source_report_sha256": report_sha256,
        "training_cutoff": report["training_cutoff"],
        "development_cutoffs": report["development_cutoffs"],
        "comparator": report["comparator"],
        "challenger": report["challenger"],
        "tracked_bbe_definition": report["tracked_bbe_definition"],
        "primary_min_complete_tracked_bbe": report["primary_min_complete_tracked_bbe"],
        "fixed_l2_penalty": report["fixed_l2_penalty"],
        "proper_score_summary": scores,
        "calibration_summary": calibration,
        "non_mlb_transport": non_mlb,
        "promotion_checks": checks,
        "eligible_for_fixed_2023_confirmation": eligible,
        "confirmation_data_present": False,
    }
    return "\n".join(lines), result


def main() -> int:
    args = _parse_args()
    content = args.report.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    report = json.loads(content)
    markdown, result = render_checkpoint(report, report_sha256=digest)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = args.output_dir / "current-talent-batted-ball-development-checkpoint.md"
    result_path = args.output_dir / "current-talent-batted-ball-development-result.json"
    markdown_path.write_text(markdown)
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
