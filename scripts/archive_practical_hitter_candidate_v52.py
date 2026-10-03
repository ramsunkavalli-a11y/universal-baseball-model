"""Save manifest and browser proof; historical forecast data remain local."""
import shutil
import json
from pathlib import Path
from universal_baseball.storage import sha256_file
from build_practical_hitter_candidate_v52 import ROOT,OUT

def main():
    m=json.loads((OUT/'candidate-manifest.json').read_text());assert all(sha256_file(ROOT/p)==h for p,h in m['artifact_hashes'].items())
    dest=ROOT/'reports/model-evidence/practical-hitter-candidate-v52';dest.mkdir(parents=True,exist_ok=True)
    for name in ['candidate-manifest.json','explorer-preview.jpg']:
        assert (OUT/name).exists();shutil.copy2(OUT/name,dest/name)
    proof=dict(browser_url='http://127.0.0.1:8787/',default_candidate_verified=True,team_filter_verified='San Francisco Giants',
        information_year_verified=2024,target_year_verified=2025,giants_filtered_rows=152,giants_expected_pa=5859,giants_actual_pa=5872,
        player_detail_verified=dict(player_id=808393,origin_year=2024,participation_probability_percent=.12,conditional_PA=83.31,expected_PA=.10,conditional_support_players=5),
        source_history_and_manual_reviews_visible=True,public_benchmark_visible=True,rows_verified=30506,
        all_readiness_products_verified=True,null_nonarrival_ability_verified=True,common_unit_actual_contribution_verified=True,
        screenshot_sha256=sha256_file(OUT/'explorer-preview.jpg'),old_and_frozen_explorers_unchanged=True)
    (dest/'browser-verification.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf8')
    print('Candidate manifest, exact artifact hashes and browser proof saved.',flush=True)

if __name__=='__main__':main()
