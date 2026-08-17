#!/usr/bin/env python3
"""Persist the predeclared 2021–2022 Current Talent selection result in repo docs.

This is intentionally a post-selection / pre-confirmation checkpoint. It reads the
already-ranked development-grid outputs and writes a compact Markdown checkpoint
plus machine-readable copies. It does not inspect or evaluate 2023 evidence.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl


START_MARKER = "<!-- BEGIN AUTO CURRENT TALENT DEVELOPMENT SELECTION -->"
END_MARKER = "<!-- END AUTO CURRENT TALENT DEVELOPMENT SELECTION -->"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selection-dir", type=Path, required=True)
    parser.add_argument("--docs-dir", type=Path, required=True)
    parser.add_argument("--project-status", type=Path, required=True)
    return parser.parse_args()


def _fmt(value: object, digits: int = 6) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def _checkpoint_markdown(selected: dict[str, object], ranked: pl.DataFrame) -> str:
    top = ranked.head(5).to_dicts()
    lines = [
        "# Current Talent development-grid selection checkpoint",
        "",
        "Status: **selected from the predeclared 2021–2022 grid; 2023 alternative-grid configurations have not been inspected.**",
        "",
        "Selection plan: `docs/current-talent-baseline-selection-plan.md`.",
        "",
        "## Preselected primary candidate",
        "",
        f"- Candidate: `{selected['candidate_id']}`",
        f"- Recency half-life: **{_fmt(selected['half_life_days'], 0)} days**",
        f"- EB prior strength: **{_fmt(selected['prior_strength_core_events'], 0)} effective core events**",
        f"- Translation variant: **`{selected['translation_variant']}`**",
        f"- 2021–2022 equal-fold mean log loss: **{_fmt(selected['mean_baseline1_log_loss'])}**",
        f"- 2021–2022 equal-fold mean Brier: **{_fmt(selected['mean_baseline1_brier'])}**",
        f"- Mean B1−B0 log-loss delta: **{_fmt(selected['mean_baseline1_minus_baseline0_log_loss'])}**",
        f"- Mean B1−B0 Brier delta: **{_fmt(selected['mean_baseline1_minus_baseline0_brier'])}**",
        f"- B1 log-loss fold wins vs B0: **{selected['baseline1_log_loss_win_fold_count']}/{selected['fold_count']}**",
        f"- B1 Brier fold wins vs B0: **{selected['baseline1_brier_win_fold_count']}/{selected['fold_count']}**",
        "",
        "### Versus existing 90/100/fitted reference",
        "",
        f"- Reference: `{selected['reference_candidate_id']}`",
        f"- Selected minus reference mean log loss: **{_fmt(selected['selected_minus_reference_mean_log_loss'])}**",
        f"- Selected minus reference mean Brier: **{_fmt(selected['selected_minus_reference_mean_brier'])}**",
        "",
        "### Calibration guardrails on development folds",
        "",
        f"- Mean absolute intercept error: **{_fmt(selected['mean_abs_calibration_intercept_error'])}**",
        f"- Mean absolute slope error: **{_fmt(selected['mean_abs_calibration_slope_error'])}**",
        f"- Mean fixed-bin ECE: **{_fmt(selected['mean_ece'])}**",
        "",
        "## Top five by the predeclared primary objective",
        "",
        "| Rank | Candidate | Half-life | Prior | Translation | Mean log loss | Mean Brier | Pareto |",
        "|---:|---|---:|---:|---|---:|---:|---|",
    ]
    for row in top:
        lines.append(
            "| {rank} | `{candidate}` | {half:.0f} | {prior:.0f} | `{translation}` | {ll:.6f} | {brier:.6f} | {pareto} |".format(
                rank=int(row["selection_order"]),
                candidate=row["candidate_id"],
                half=float(row["half_life_days"]),
                prior=float(row["prior_strength_core_events"]),
                translation=row["translation_variant"],
                ll=float(row["mean_baseline1_log_loss"]),
                brier=float(row["mean_baseline1_brier"]),
                pareto="yes" if bool(row["proper_score_pareto_frontier"]) else "no",
            )
        )
    lines.extend(
        [
            "",
            "## Confirmation boundary",
            "",
            "The primary candidate above was selected using **only the six 2021–2022 development folds**. "
            "Do not replace it after inspecting 2023. The next gate may evaluate this one preselected candidate "
            "on 2023 and compare it with Baseline 0 and the existing 90/100/fitted reference configuration.",
            "",
            "If 2023 confirmation fails, record hyperparameter instability; **do not reselect using 2023**.",
            "",
        ]
    )
    return "\n".join(lines)


def _project_status_section(selected: dict[str, object]) -> str:
    return "\n".join(
        [
            START_MARKER,
            "## Development-grid candidate selected — awaiting 2023 confirmation",
            "",
            "The predeclared 18-candidate simple-baseline grid has been evaluated on **2021–2022 only**. "
            "Alternative grid configurations have not been evaluated on 2023.",
            "",
            f"Preselected candidate: **`{selected['candidate_id']}`** — half-life **{_fmt(selected['half_life_days'], 0)} days**, "
            f"prior strength **{_fmt(selected['prior_strength_core_events'], 0)}**, translation **`{selected['translation_variant']}`**.",
            "",
            f"Development equal-fold mean B1 log loss: **{_fmt(selected['mean_baseline1_log_loss'])}**; "
            f"Brier: **{_fmt(selected['mean_baseline1_brier'])}**.",
            "",
            f"Versus the prior 90/100/fitted reference, selected-minus-reference mean log loss is "
            f"**{_fmt(selected['selected_minus_reference_mean_log_loss'])}** and Brier is "
            f"**{_fmt(selected['selected_minus_reference_mean_brier'])}**.",
            "",
            "Detailed checkpoint: `docs/current-talent-development-selection-checkpoint.md`.",
            "",
            "**Next gate:** evaluate this preselected candidate on the three 2023 folds only; compare to B0 and the "
            "existing 90/100/fitted reference. Do not run the full alternative grid on 2023 and do not reselect "
            "using 2023 if confirmation fails.",
            END_MARKER,
        ]
    )


def _replace_or_append(text: str, section: str) -> str:
    if START_MARKER in text or END_MARKER in text:
        if START_MARKER not in text or END_MARKER not in text:
            raise ValueError("project-status selection markers are incomplete")
        before, remainder = text.split(START_MARKER, 1)
        _, after = remainder.split(END_MARKER, 1)
        return before.rstrip() + "\n\n" + section + after
    return text.rstrip() + "\n\n" + section + "\n"


def main() -> int:
    args = _parse_args()
    selected_path = args.selection_dir / "selected_candidate.json"
    ranked_path = args.selection_dir / "ranked_candidates.csv"
    if not selected_path.exists() or not ranked_path.exists():
        raise FileNotFoundError("selection checkpoint inputs are incomplete")

    selected = json.loads(selected_path.read_text(encoding="utf-8"))
    ranked = pl.read_csv(ranked_path)
    if ranked.height != 18:
        raise ValueError(f"expected 18 ranked candidates, observed {ranked.height}")
    if str(ranked.row(0, named=True)["candidate_id"]) != str(selected["candidate_id"]):
        raise ValueError("selected candidate does not match ranked-candidate primary winner")

    args.docs_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = args.docs_dir / "current-talent-development-selection-checkpoint.md"
    checkpoint_path.write_text(
        _checkpoint_markdown(selected, ranked),
        encoding="utf-8",
    )
    (args.docs_dir / "current-talent-development-selected-candidate.json").write_text(
        json.dumps(selected, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    ranked.write_csv(args.docs_dir / "current-talent-development-ranked-candidates.csv")

    status_text = args.project_status.read_text(encoding="utf-8")
    args.project_status.write_text(
        _replace_or_append(status_text, _project_status_section(selected)),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "selected_candidate": selected["candidate_id"],
                "checkpoint": str(checkpoint_path),
                "project_status_updated": str(args.project_status),
                "confirmation_ready": True,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
