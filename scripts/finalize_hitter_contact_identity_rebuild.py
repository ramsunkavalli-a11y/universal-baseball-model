"""Seal the completed source review, without certifying projection merit."""
from pathlib import Path
import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
import polars as pl
from universal_baseball.storage import sha256_file
from universal_baseball.contact_identity_overlay import contact_identity_residuals
from rebuild_hitter_contact_identity import ROOT, OUT, WORK, YEARS, read, write


def main():
    target = OUT / 'final-report.json'
    if target.exists(): raise FileExistsError('Preserve completed source approval')
    assembly = read(OUT / 'assembly.json'); cases = read(OUT / 'fixed-cases.json')
    assert assembly['source_gate'] == 'pending_player_review'
    assert assembly['official_sha256'] == sha256_file(OUT / 'official.json')
    for p, h in cases['inputs'].items(): assert sha256_file(Path(p)) == h
    review_path = ROOT / 'config/hitter_contact_identity_source_review.json'
    review = read(review_path)
    ids = {(c['player_id'], c['origin_year']) for c in cases['cases']}
    assert ids == {(r['player_id'], r['origin_year']) for r in review['cases']}
    assert all(r['judgment'].strip() for r in review['cases']) and review['source_walkthrough_status'] == 'complete'
    assert review['new_predictive_gain_claimed'] is False and review['deployment_approved'] is False
    post = []
    for y in YEARS:
        r = next(r for r in assembly['years'] if r['year'] == y)
        assert r['unflagged_mismatch_contacts'] == 0
        for p, h in r['artifact_hashes'].items(): assert sha256_file(Path(p)) == h
        before = pl.read_parquet(WORK / f'residuals-{y}.parquet')
        games = before['game_id'].unique().to_list()
        repaired = pl.read_parquet(WORK / 'assembly' / f'repaired-{y}.parquet').filter(pl.col('game_pk').is_in(games))
        control_path = OUT / f'controls-{y}.parquet'
        after = contact_identity_residuals(repaired.drop('source_batter_id').rename({'batter_mlbam_id': 'source_batter_id'}), pl.read_parquet(control_path))
        after_path = WORK / 'assembly' / f'after-residuals-{y}.parquet'; after.write_parquet(after_path)
        post.append(dict(year=y, controlled_game_count=len(games),
            absolute_player_count_residual_before=before['contact_count_difference'].abs().sum(),
            absolute_player_count_residual_after=after['contact_count_difference'].abs().sum(),
            nonzero_player_rows_after=after.filter(pl.col('contact_count_difference') != 0).height,
            net_contact_difference_after=after['contact_count_difference'].sum(),
            before_path=str(WORK / f'residuals-{y}.parquet'), before_sha256=sha256_file(WORK / f'residuals-{y}.parquet'),
            after_path=str(after_path), after_sha256=sha256_file(after_path)))
    suites = ET.parse(OUT / 'unit-tests.xml').getroot().findall('testsuite')
    assert sum(int(s.attrib['tests']) for s in suites) == 34
    assert all(int(s.attrib['failures']) == int(s.attrib['errors']) == 0 for s in suites)
    freeze = json.loads(subprocess.check_output([str(ROOT / '.venv/Scripts/python.exe'), '-X', 'utf8',
        str(ROOT / 'scripts/verify_hitter_full_2026_freeze.py')], cwd=ROOT))
    assert freeze['status'] == 'verified' and freeze['protected_2026_opened'] is False
    doc = ROOT / 'docs/hitter-contact-identity-rebuild-result.md'
    final = dict(source_gate='accepted_for_raw_measurement_test', source_walkthrough_status='complete',
        cases=len(cases['cases']), repaired_contacts=sum(r['changed_participants'] for r in assembly['years']),
        retained_physical_contacts=sum(r['physical_contacts'] for r in assembly['years']),
        classified_contact_cells=sum(r['classified_contacts'] for r in assembly['years']),
        unflagged_identity_mismatches=0, remaining_count_residuals=post, freeze_verification=freeze,
        focused_tests=34, new_models_fitted=False, forecasts_changed=False, protected_outcomes_used=False,
        deployment_approved=False, whole_goal_complete=False, complete_schedule_coverage_claimed=False,
        park_neutral_measurements_claimed=False,
        source_vintage_limit='Current official matchup captures adjudicate historical identity; not certified original game-day vintages',
        next_step='One separately contracted, matched future-MLB information test with unchanged opportunity and preserved current/translated anchors',
        input_hashes={str(p): sha256_file(p) for p in [OUT / 'assembly.json', OUT / 'official.json', OUT / 'fixed-cases.json',
            OUT / 'selection.json', OUT / 'controls.json', OUT / 'unit-tests.xml', review_path, doc, Path(__file__)]})
    write(target, final)
    dest = ROOT / 'reports/model-evidence/hitter-contact-identity-rebuild'
    for name in ['assembly.json', 'official.json', 'fixed-cases.json', 'final-report.json']:
        assert not (dest / name).exists()
        shutil.copy2(OUT / name, dest / name)
        assert sha256_file(OUT / name) == sha256_file(dest / name)
    print(json.dumps({k: v for k, v in final.items() if k not in ['input_hashes', 'remaining_count_residuals']}, indent=2), flush=True)
    print('Remaining count checks:', [(r['year'], r['absolute_player_count_residual_before'], r['absolute_player_count_residual_after']) for r in post], flush=True)


if __name__ == '__main__': main()
