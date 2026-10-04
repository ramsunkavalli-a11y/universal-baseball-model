"""Preserve compact evidence for a verified historical export, without fitting."""
import json
import shutil
from pathlib import Path

from universal_baseball.storage import sha256_file
import build_hitter_integrated_research_explorer as b

EVIDENCE = b.ROOT / 'reports/model-evidence/hitter-integrated-research-explorer'


def main():
    assert not (EVIDENCE / 'final-report.json').exists(), 'Preserve completed milestone'
    build = b.prep.read(b.OUT / 'build-report.json')
    verification = b.prep.read(b.OUT / 'verification.json')
    browser = b.prep.read(EVIDENCE / 'browser-review.json')
    assert verification['export_verification_status'] == 'complete'
    assert verification['all_exported_rows_checked'] == 30506
    assert verification['protected_freeze']['status'] == 'verified'
    assert browser['status'] == 'core_interactions_verified_with_download_limitation'
    b.prep.old.verify_hashes(build['source_hashes'])
    b.prep.old.verify_hashes(verification['source_hashes'])
    for name, digest in build['output_hashes'].items():
        assert sha256_file(b.DIST / name) == digest, name
    assert sha256_file(b.OUT / 'display-player-walks.json') == verification['player_walks_sha256']
    paths = [
        (b.OUT / 'build-report.json', EVIDENCE / 'build-report.json'),
        (b.OUT / 'verification.json', EVIDENCE / 'verification.json'),
        (b.OUT / 'display-player-walks.json', EVIDENCE / 'display-player-walks.json'),
        (b.DIST / 'metadata.json', EVIDENCE / 'metadata.json'),
        (b.DIST / 'heads.json', EVIDENCE / 'heads.json'),
        (b.DIST / 'mlb-review.json', EVIDENCE / 'mlb-review.json'),
    ]
    for path in sorted((b.DIST / 'reviews').glob('*.json')):
        paths.append((path, EVIDENCE / 'reviews' / path.name))
    for name in browser['screenshot_files']:
        paths.append((b.OUT / name, EVIDENCE / name))
    for source, target in paths:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            assert sha256_file(target) == sha256_file(source), target
        else:
            shutil.copyfile(source, target)
    # Preserve the complete fitted inputs for the eight fixed display walks.
    walks = b.prep.read(b.OUT / 'display-player-walks.json')['cases']
    selected = {}
    for case in walks:
        row = case['row']
        key = row['cell']
        data = b.prep.read(b.DIST / f'cells/{key}.json')['rows'][str(row['row_id'])]
        selected[str(row['row_id'])] = dict(cell=key, inputs=data)
    b.write(EVIDENCE / 'selected-exact-inputs.json', selected)
    artifacts = {str(p.relative_to(EVIDENCE)): sha256_file(p)
                 for p in sorted(EVIDENCE.rglob('*')) if p.is_file()}
    code = [
        b.ROOT / 'scripts/build_hitter_integrated_research_explorer.py',
        b.ROOT / 'scripts/verify_hitter_integrated_research_explorer.py',
        Path(__file__), b.ROOT / 'src/universal_baseball/hitter_research_export.py',
        b.ROOT / 'tests/test_hitter_research_export.py',
        b.ROOT / 'docs/hitter-integrated-research-explorer-contract.md',
        b.ROOT / 'docs/hitter-integrated-research-explorer-result.md',
    ] + sorted(b.TEMPLATE.glob('*'))
    b.write(EVIDENCE / 'final-report.json', dict(
        milestone='Historical reviewed hitter assembly and source-to-display explorer',
        export_verification_status='complete',
        browser_verification_status=browser['status'],
        csv_download_verified=False,
        forecasts=30506, people=build['people'],
        exact_row_inputs_verified=verification['exact_rate_and_opportunity_inputs_checked'],
        selected_branch_and_opportunity_replays=build['selected_branch_and_opportunity_replays'],
        fixed_display_walks=8, reviewed_origins=build['reviewed_origins'],
        endpoint_components_checked=verification['independent_endpoint_components'],
        new_models_fitted=0, predictions_unchanged=True,
        protected_freeze=verification['protected_freeze'],
        deployment_approved=False, full_goal_complete=False,
        artifact_hashes=artifacts, code_hashes={str(p): sha256_file(p) for p in code},
        local_url=browser['url'],
        full_data_directory=str(b.DIST),
        reproducibility_limit='Requires the reviewed local source panels and fitted heads recorded in the build manifest; the full generated display arrays are kept local, not recreated by fitting.',
    ))
    print('Saved compact verified historical explorer evidence:', EVIDENCE, flush=True)


if __name__ == '__main__':
    main()
