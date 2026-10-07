import json
from pathlib import Path
from audit_defensive_talent_support import verify
from run_hitter_finite_return_baseline import protections, save
from universal_baseball.storage import sha256_file

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/generated/defensive-talent-position-v2/qualified"
PUBLIC = ROOT / "reports/model-evidence/defensive-talent-position-v2/qualified"


def main():
    protections()
    pre = json.loads((OUT / "preflight.json").read_text(encoding="utf8"))
    cert = json.loads((OUT / "exposure-certification.json").read_text(encoding="utf8"))
    verify(pre["hashes"]); verify(cert["hashes"])
    doc = ROOT / "docs/defensive-talent-position-v2-source-review.md"
    assert doc.exists()
    final = dict(status="source_and_support_review_complete_one_bounded_three_year_fit_allowed", fits=0,
                 player_walkthrough_status="complete", predictive_accuracy_established=False,
                 review=str(doc.relative_to(ROOT)), production_changed=False, additional_2026_data_ingested_or_used=False,
                 hashes={**pre["hashes"], **cert["hashes"], **{str(p): sha256_file(p) for p in [doc, Path(__file__), OUT / "preflight.json", OUT / "exposure-certification.json"]}})
    save(OUT / "source-final-review.json", final)
    save(PUBLIC / "source-final-review.json", final)
    verify(final["hashes"])
    protections()
    print(final["status"])


if __name__ == "__main__":
    main()
