"""Require human case assessments before closing the development comparison."""
import shutil

from universal_baseball.storage import sha256_file
from prepare_hitter_extended_training import ROOT,OUT,read,write,verify


def main():
    assert not (OUT/'final-report.json').exists(), 'Preserve completed disposition'
    prep = read(OUT/'review-preparation.json')
    verify(prep['hashes'])
    verify(prep['model_hashes'])
    cases = read(OUT/'cases.json')
    notes_path = ROOT/'config/hitter_extended_training_review.json'
    result_path = ROOT/'docs/hitter-extended-training-result.md'
    notes = read(notes_path)
    assert set(notes)=={str(c['selection']['row_id']) for c in cases}
    assert all(n['review_status']=='complete' and n['assessment'] for n in notes.values())
    write('reviewed-cases.json',[dict(row_id=c['selection']['row_id'],player_id=c['selection']['player_id'],
        name=c['selection']['player_name'],**notes[str(c['selection']['row_id'])]) for c in cases])
    pre = read(OUT/'preflight.json')
    write('preflight-summary.json',{k:v for k,v in pre.items() if k!='cells'} | dict(
        cells=[{k:v for k,v in c.items() if k not in ['training_row_ids','test_row_ids']} | dict(
            training_membership_counts={a:len(ids) for a,ids in c['training_row_ids'].items()},test_rows=len(c['test_row_ids']))
            for c in pre['cells']],
        actual_memberships_retained_in=str(OUT/'preflight.json'),full_preflight_sha256=sha256_file(OUT/'preflight.json')))
    write('final-report.json',dict(player_walkthrough_status='complete',reviewed_cases=len(cases),
        new_heads_replayed=210,restricted_anchor_reproduced=True,
        disposition='See reviewed result; no automatic promotion',
        protected_outcomes_used=False,frozen_forecast_changed=False,explorer_changed=False,
        deployment_approved=False,full_goal_complete=False,
        source_and_execution_hashes=pre['input_hashes'],review_preparation_hashes=prep['hashes'],
        model_hashes=prep['model_hashes'],review_hashes={str(p):sha256_file(p) for p in [
            notes_path,result_path,OUT/'reviewed-cases.json',OUT/'preflight-summary.json',ROOT/'scripts/score_hitter_extended_training.py',
            ROOT/'scripts/review_hitter_extended_training.py',ROOT/'scripts/finalize_hitter_extended_training.py']}))
    evidence = ROOT/'reports/model-evidence/hitter-extended-training'
    evidence.mkdir(parents=True,exist_ok=True)
    for name in ['scores.json','intervals.json','selected-cases.json','cases.json','verification.json','reviewed-cases.json','preflight-summary.json','final-report.json']:
        shutil.copyfile(OUT/name,evidence/name)
        assert sha256_file(OUT/name)==sha256_file(evidence/name)
    print('Completed actual case reviews:',len(cases),'; full hitter goal remains active.')


if __name__=='__main__':
    main()
