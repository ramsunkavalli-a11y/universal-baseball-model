"""Package verified research explorer evidence without forecast promotion."""
import json
import shutil
import subprocess
from pathlib import Path

import build_hitter_risk_research_explorer as b
from universal_baseball.storage import sha256_file


def main():
    assert not (b.OUT/'handoff-report.json').exists(), 'Preserve completed explorer evidence'
    build = b.e.read(b.OUT/'build-report.json')
    data = b.e.read(b.OUT/'data-verification.json')
    b.e.old.check_hashes(build['source_hashes'])
    b.e.old.check_hashes(data['source_hashes'])
    for rel, h in {**build['output_hashes'], **data['extra_artifact_hashes']}.items():
        assert sha256_file(b.DIST/rel) == h, rel
    review_path = b.e.ROOT/'config/hitter_research_explorer_browser_review.json'
    review = b.e.read(review_path)
    assert not review['pending'], 'Resolve required browser checks before handoff'
    assert review['no_new_models'] and review['research_only'] and not review['full_goal_complete']
    assert data['forecasts_verified'] == data['complete_input_files_verified'] == 30506
    node = subprocess.run(['node', '--check', str(b.TEMPLATE/'app.js')], text=True, capture_output=True)
    assert node.returncode == 0, node.stdout+node.stderr
    tests = subprocess.run([str(b.e.ROOT/'.venv/Scripts/python.exe'), '-X', 'utf8', '-m', 'pytest', '-q',
        '-p', 'no:cacheprovider', 'tests/test_hitter_risk_research_explorer.py'],
        cwd=b.e.ROOT, text=True, capture_output=True)
    assert tests.returncode == 0, tests.stdout+tests.stderr
    (b.OUT/'focused-tests.txt').write_text(tests.stdout+tests.stderr, encoding='utf8', newline='\n')
    b.e.write(b.OUT/'browser-review.json', review)
    b.e.write(b.OUT/'handoff-report.json', dict(url=review['url'], research_only=True,
        browser_verified_with_download_qualification=True, csv_browser_download_verified=review['download_verified'],
        player_forecasts=30506, complete_input_files=30506, completed_reviews=18,
        original_means_and_membership_unchanged=True, new_fits=0, protected_2026_opened=False,
        frozen_verification=data['frozen_verification'], published_explorer_changed=False,
        full_goal_complete=False, tests='9 focused tests pass; JavaScript syntax check passes',
        artifact_hashes={str(p): sha256_file(p) for p in [b.OUT/'build-report.json', b.OUT/'data-verification.json',
            b.OUT/'browser-review.json', b.OUT/'focused-tests.txt', review_path,
            b.e.ROOT/'docs/hitter-research-candidate-model-card.md', Path(__file__)]}))
    evidence = b.e.ROOT/'reports/model-evidence/hitter-risk-research-explorer'
    evidence.mkdir(parents=True, exist_ok=True)
    for name in ['build-report.json', 'data-verification.json', 'browser-review.json', 'focused-tests.txt', 'handoff-report.json']:
        assert not (evidence/name).exists(), 'Do not overwrite milestone evidence'
        shutil.copyfile(b.OUT/name, evidence/name)
        assert sha256_file(b.OUT/name) == sha256_file(evidence/name)
    print('Verified research explorer handed off at', review['url'], flush=True)
    print('Full model goal remains active; CSV download remains qualified.', flush=True)


if __name__ == '__main__':
    main()
