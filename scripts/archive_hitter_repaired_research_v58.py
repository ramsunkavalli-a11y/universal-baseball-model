"""Preserve reviewed research export and observed browser proof, not raw data."""
import json
import shutil
from pathlib import Path
from build_hitter_repaired_research_v58 import ROOT, OUT
from universal_baseball.storage import sha256_file


def main():
    m=json.loads((OUT/"candidate-manifest.json").read_text())
    assert all(sha256_file(ROOT/p)==h for p,h in m["artifact_hashes"].items())
    assert all(sha256_file(Path(p))==h for p,h in m["source_hashes"].items())
    assert (OUT/"explorer-preview.jpg").exists()
    proof=dict(
        browser_url="http://127.0.0.1:8788/",
        default_corrected_baseline_verified=True,
        team_filter_verified="San Francisco Giants",
        information_year_verified=2024,target_year_verified=2025,
        giants_filtered_rows=152,giants_expected_pa_rounded=5842,
        giants_actual_pa=5872,giants_expected_offense_rounded=15.2,
        giants_actual_offense_rounded=13.5,
        player_search_and_details_verified=dict(player_id=808393,
            origin_year=2024,appearance_probability_percent_rounded=.12,
            conditional_pa_rounded=83.08,expected_pa_rounded=.10,
            history_years=[2023,2024],source_buckets=["DSL"],
            actual_pa=0,actual_rate_unobserved=True),
        alternative_comparison_rows_visible=True,
        historical_reviews_version_labeled=True,
        public_benchmark_and_timing_qualifications_visible=True,
        screenshot_sha256=sha256_file(OUT/"explorer-preview.jpg"),
        old_explorers_and_frozen_2026_unchanged=True,
    )
    m["browser_visual_verification"]="complete"
    m["browser_verification"]=proof
    (OUT/"candidate-manifest.json").write_text(json.dumps(m,indent=2)+"\n",encoding="utf8")
    dest=ROOT/"reports/model-evidence/practical-hitter-repaired-research-v58"
    dest.mkdir(parents=True,exist_ok=True)
    for name in ["candidate-manifest.json","explorer-preview.jpg"]:
        shutil.copy2(OUT/name,dest/name)
    (dest/"browser-verification.json").write_text(json.dumps(proof,indent=2)+"\n",encoding="utf8")
    print("Corrected research export and observed browser proof saved.",flush=True)


if __name__=="__main__":main()
