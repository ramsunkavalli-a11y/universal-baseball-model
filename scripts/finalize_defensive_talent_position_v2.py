"""Separate completed review from positive prediction or deployment."""
import json
from pathlib import Path
from audit_defensive_talent_support import verify
from run_hitter_finite_return_baseline import protections, save
from universal_baseball.storage import sha256_file

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/generated/defensive-talent-position-v2/qualified/comparison"
PUBLIC = ROOT / "reports/model-evidence/defensive-talent-position-v2/comparison"


def main():
    protections()
    report = json.loads((OUT / "report.json").read_text(encoding="utf8"))
    checks = json.loads((OUT / "review-checks.json").read_text(encoding="utf8"))
    source = json.loads((OUT.parent / "source-final-review.json").read_text(encoding="utf8"))
    verify(report["hashes"]); verify(checks["hashes"]); verify(source["hashes"])
    assert checks["origin_replays"] == 31563 and checks["label_replays"] == 94689
    assert checks["prediction_replays"] == report["predictions"] * 3
    assert checks["independent_ridge_replays"] == report["fits"] == 30
    assert checks["reviewed_focal_cases"] == 25
    doc = ROOT / "docs/defensive-talent-position-v2-result.md"
    assert doc.exists()
    decision = dict(status="infield_source_and_fixed_comparison_milestone_complete",
                    player_walkthrough_status="complete", result=str(doc.relative_to(ROOT)),
                    integrity="pass_with_disclosed_bounded_exposure_discrepancies",
                    support="selected_observed_defenders_only_lower_minors_and_long_windows_not_validated",
                    predictive_improvement="not_demonstrated", baseball_reasonability="review_complete_gains_and_major_misses_disclosed",
                    deployment_approved=False, production_changed=False, additional_2026_data_ingested_or_used=False,
                    disposition="Keep repaired data. Do not deploy or retune this adjusted play-share addition. Next source feasibility is individual opportunity and position retention, not another algorithm search.",
                    hashes={**source["hashes"], **report["hashes"], **checks["hashes"], **{str(p): sha256_file(p) for p in [Path(__file__), doc, OUT / "review-checks.json", ROOT / "tests/test_defensive_talent_position.py"]}})
    save(OUT / "final-review.json", decision)
    save(PUBLIC / "final-review.json", decision)
    verify(decision["hashes"])
    protections()
    print(json.dumps({k: v for k, v in decision.items() if k != "hashes"}, indent=2))


if __name__ == "__main__":
    main()
