"""Seal the source review without recertifying old predictive model claims."""
from pathlib import Path
import json
import shutil
import xml.etree.ElementTree as ET
from universal_baseball.storage import sha256_file
from audit_hitter_detailed_contact_compatibility import ROOT, OUT


def read(path): return json.loads(path.read_text(encoding='utf8'))


def main():
    if (OUT / 'final-report.json').exists(): raise FileExistsError('Preserve first completion receipt')
    report = read(OUT / 'report.json')
    for name in ['report.json', 'event-provenance.json', 'official-adjudication.json', 'repair-pilot.json']:
        obj = read(OUT / name)
        for p, h in obj['input_hashes'].items():
            assert sha256_file(Path(p)) == h, p
    for p, h in report['output_hashes'].items(): assert sha256_file(Path(p)) == h, p
    adjudication = read(OUT / 'official-adjudication.json')
    for r in adjudication['rows']: assert sha256_file(Path(r['source_capture'])) == r['source_sha256']
    pilot = read(OUT / 'repair-pilot.json')
    assert sha256_file(OUT / 'repaired-selected-game-contacts.parquet') == pilot['repaired_artifact_sha256']
    assert pilot['selected_contacts'] == 501 and pilot['changed_participant_contacts'] == 3
    review_path = ROOT / 'config/hitter_detailed_contact_compatibility_review.json'
    document_path = ROOT / 'docs/hitter-detailed-contact-compatibility-result.md'
    review = read(review_path); cases = read(OUT / 'cases.json')
    assert review['new_predictive_gain_claimed'] is False and review['complete_season_repair_claimed'] is False
    ids = [(r['player_id'], r['origin_year']) for r in review['cases']]
    assert len(set(ids)) == len(ids) == len(cases)
    assert set(ids) == {(r['player_id'], r['origin_year']) for r in cases}
    text = document_path.read_text(encoding='utf8')
    assert all(r['judgment'].strip() for r in review['cases'])
    # Long-form doc uses surnames; the receipt still requires exact numeric identities.
    assert all(r['forecasts']['player_name'].removesuffix(' Jr.').split()[-1] in text for r in cases)
    actual_mismatches = {(r['source']['game_pk'], r['source']['at_bat_index'],
                         r['source']['player_id'], r['official_batter']['id'])
                        for r in adjudication['rows'] if r['participant_mismatch']}
    assert actual_mismatches == {(r['game_pk'], r['at_bat_index'], r['source_player_id'],
                                 r['correct_player_id']) for r in review['source_cases']}
    suites = ET.parse(OUT / 'unit-tests.xml').getroot().findall('testsuite')
    assert sum(int(s.attrib['tests']) for s in suites) == 7
    assert all(int(s.attrib['failures']) == int(s.attrib['errors']) == 0 for s in suites)
    final = dict(report, source_walkthrough_status='complete',
        model_predictive_walkthrough_status='not_replayed_no_new_model_test',
        complete_season_repair=False, deployment_approved=False,
        disposition='Source repair required before fair current-contact comparison; old forecasts remain qualified development evidence',
        next_action=review['next_action'],
        review_hashes={str(p): sha256_file(p) for p in [review_path, document_path, Path(__file__), OUT / 'unit-tests.xml']})
    (OUT / 'final-report.json').write_text(json.dumps(final, indent=2, allow_nan=False) + '\n', encoding='utf8')
    dest = ROOT / 'reports/model-evidence/hitter-detailed-contact-compatibility'; dest.mkdir(parents=True, exist_ok=True)
    for name in ['report.json', 'final-report.json', 'cases.json', 'selected-cases.json',
                 'event-provenance.json', 'official-adjudication.json', 'repair-pilot.json']:
        shutil.copy2(OUT / name, dest / name)
        assert sha256_file(OUT / name) == sha256_file(dest / name)
    print('Eleven source/output reviews and three official participant adjudications complete; seven checks pass. No forecast changed.')


if __name__ == '__main__': main()
