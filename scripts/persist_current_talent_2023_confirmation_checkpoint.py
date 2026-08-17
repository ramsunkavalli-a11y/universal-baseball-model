#!/usr/bin/env python3
"""Persist the preselected Current Talent candidate's 2023 confirmation result."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl


START_MARKER = "<!-- BEGIN AUTO CURRENT TALENT 2023 CONFIRMATION -->"
END_MARKER = "<!-- END AUTO CURRENT TALENT 2023 CONFIRMATION -->"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirmation-dir", type=Path, required=True)
    parser.add_argument("--docs-dir", type=Path, required=True)
    parser.add_argument("--project-status", type=Path, required=True)
    return parser.parse_args()


def _fmt(value: object, digits: int = 6) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def _checkpoint(report: dict[str, object], folds: pl.DataFrame) -> str:
    selected = dict(report["selected_candidate"])
    confirmed = bool(report["proper_score_confirmation"])
    lines = [
        "# Current Talent 2023 confirmation checkpoint",
        "",
        f"Status: **{'CONFIRMED' if confirmed else 'NOT CONFIRMED'} under the predeclared selection plan.**",
        "",
        "This gate evaluates only the candidate preselected from the 2021–2022 development grid, plus the existing 90/100/fitted reference. "
        "The 18-candidate alternative grid was **not** evaluated on 2023.",
        "",
        "## Preselected candidate",
        "",
        f"- Candidate: `{selected['candidate_id']}`",
        f"- Half-life: **{_fmt(selected['half_life_days'], 0)} days**",
        f"- Prior strength: **{_fmt(selected['prior_strength_core_events'], 0)} effective core events**",
        f"- Translation: **`{selected['translation_variant']}`**",
        "",
        "## 2023 confirmation folds",
        "",
        "| Cutoff | B1 log loss | B1 Brier | B1−B0 LL | B1−B0 Brier |",
        "|---|---:|---:|---:|---:|",
    ]
    selected_id = str(selected["candidate_id"])
    selected_folds = folds.filter(pl.col("candidate_id") == selected_id).sort("as_of_date")
    for row in selected_folds.iter_rows(named=True):
        lines.append(
            "| {date} | {ll:.6f} | {brier:.6f} | {dll:.6f} | {dbrier:.6f} |".format(
                date=row["as_of_date"],
                ll=float(row["baseline1_log_loss"]),
                brier=float(row["baseline1_brier"]),
                dll=float(row["baseline1_minus_baseline0_log_loss"]),
                dbrier=float(row["baseline1_minus_baseline0_brier"]),
            )
        )
    lines.extend(
        [
            "",
            "## Three-fold summary",
            "",
            f"- Mean B1 log loss: **{_fmt(report['selected_mean_baseline1_log_loss'])}**",
            f"- Mean B1 Brier: **{_fmt(report['selected_mean_baseline1_brier'])}**",
            f"- Mean B1−B0 log loss: **{_fmt(report['selected_mean_b1_minus_b0_log_loss'])}**",
            f"- Mean B1−B0 Brier: **{_fmt(report['selected_mean_b1_minus_b0_brier'])}**",
            f"- B1 log-loss wins vs B0: **{report['selected_b1_log_loss_win_vs_b0_fold_count']}/3**",
            f"- B1 Brier wins vs B0: **{report['selected_b1_brier_win_vs_b0_fold_count']}/3**",
            f"- Selected minus reference mean log loss: **{_fmt(report['selected_minus_reference_mean_log_loss'])}**",
            f"- Selected minus reference mean Brier: **{_fmt(report['selected_minus_reference_mean_brier'])}**",
            f"- Mean abs calibration-intercept error: **{_fmt(report['selected_mean_abs_calibration_intercept_error'])}**",
            f"- Mean abs calibration-slope error: **{_fmt(report['selected_mean_abs_calibration_slope_error'])}**",
            f"- Mean fixed-bin ECE: **{_fmt(report['selected_mean_ece'])}**",
            "",
            "## Breadth vs Baseline 0",
            "",
            f"- Component log-loss wins: **{report['selected_component_log_loss_win_vs_b0_count']}/{report['selected_component_comparison_count']}**",
            f"- Component Brier wins: **{report['selected_component_brier_win_vs_b0_count']}/{report['selected_component_comparison_count']}**",
            f"- Stratum log-loss wins: **{report['selected_stratum_log_loss_win_vs_b0_count']}/{report['selected_stratum_comparison_count']}**",
            f"- Stratum Brier wins: **{report['selected_stratum_brier_win_vs_b0_count']}/{report['selected_stratum_comparison_count']}**",
            "",
            "## Decision boundary",
            "",
        ]
    )
    if confirmed:
        lines.extend(
            [
                "The preselected candidate passes the proper-score confirmation rule: it remains better than its B0 comparator and does not reverse the development-grid log-loss advantage versus the fixed reference.",
                "",
                "This is sufficient to move to an explicit **simple-baseline freeze decision** using the already predeclared guardrails. It does not by itself authorize richer inputs or Projection.",
            ]
        )
    else:
        lines.extend(
            [
                "The preselected candidate fails the predeclared confirmation rule.",
                "",
                "**Do not reselect another candidate using 2023.** Record hyperparameter instability and keep the simple baseline unfrozen.",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def _status_section(report: dict[str, object]) -> str:
    selected = dict(report["selected_candidate"])
    confirmed = bool(report["proper_score_confirmation"])
    next_text = (
        "Make the documented simple-baseline freeze decision from the predeclared development + confirmation evidence; do not add richer inputs first."
        if confirmed
        else "Keep the simple baseline unfrozen and document hyperparameter instability; do not reselect using 2023."
    )
    return "\n".join(
        [
            START_MARKER,
            "## 2023 selected-candidate confirmation",
            "",
            f"Preselected candidate **`{selected['candidate_id']}`** is **{'CONFIRMED' if confirmed else 'NOT CONFIRMED'}** under the predeclared confirmation rule.",
            "",
            f"2023 equal-fold mean B1 log loss: **{_fmt(report['selected_mean_baseline1_log_loss'])}**; Brier: **{_fmt(report['selected_mean_baseline1_brier'])}**.",
            "",
            f"Mean B1−B0: **{_fmt(report['selected_mean_b1_minus_b0_log_loss'])} log loss / {_fmt(report['selected_mean_b1_minus_b0_brier'])} Brier**.",
            "",
            f"Selected minus fixed-reference mean: **{_fmt(report['selected_minus_reference_mean_log_loss'])} log loss / {_fmt(report['selected_minus_reference_mean_brier'])} Brier**.",
            "",
            "The full 18-candidate grid was **not** evaluated on 2023. Detailed checkpoint: `docs/current-talent-2023-confirmation-checkpoint.md`.",
            "",
            f"**Next gate:** {next_text}",
            END_MARKER,
        ]
    )


def _replace_or_append(text: str, section: str) -> str:
    if START_MARKER in text or END_MARKER in text:
        if START_MARKER not in text or END_MARKER not in text:
            raise ValueError("project-status confirmation markers are incomplete")
        before, remainder = text.split(START_MARKER, 1)
        _, after = remainder.split(END_MARKER, 1)
        return before.rstrip() + "\n\n" + section + after
    return text.rstrip() + "\n\n" + section + "\n"


def main() -> int:
    args = _parse_args()
    report_path = args.confirmation_dir / "report.json"
    folds_path = args.confirmation_dir / "confirmation_fold_metrics.csv"
    if not report_path.exists() or not folds_path.exists():
        raise FileNotFoundError("2023 confirmation checkpoint inputs are incomplete")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    folds = pl.read_csv(folds_path)
    if bool(report.get("full_grid_evaluated_on_2023")):
        raise ValueError("confirmation report says full grid was evaluated on 2023")
    if not bool(report.get("selection_uses_only_preselected_candidate_on_2023")):
        raise ValueError("confirmation report does not preserve selection boundary")

    args.docs_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = args.docs_dir / "current-talent-2023-confirmation-checkpoint.md"
    checkpoint.write_text(_checkpoint(report, folds), encoding="utf-8")
    (args.docs_dir / "current-talent-2023-confirmation-result.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    status_text = args.project_status.read_text(encoding="utf-8")
    args.project_status.write_text(
        _replace_or_append(status_text, _status_section(report)),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "candidate": report["selected_candidate"]["candidate_id"],
                "proper_score_confirmation": report["proper_score_confirmation"],
                "checkpoint": str(checkpoint),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
