"""Seal the explanatory diagnostic and genuinely ordinary thirteenth case."""
import shutil
from evaluate_hitter_prospect_workload_specialization import OUT, ROOT, read, write, verify
from universal_baseball.storage import sha256_file


def main():
    assert not (OUT/'completed-review.json').exists()
    primary = read(OUT/'final-report.json')
    assert primary['player_walkthrough_status']=='complete' and primary['reviewed_cases']==12
    verify(primary['source_hashes']); verify(primary['review_hashes']); verify(primary['model_hashes']); verify(primary['final_hashes'])
    supplemental = read(OUT/'ordinary-case-supplement.json')
    diagnostic = read(OUT/'allocation-diagnostic.json')
    verify(supplemental['hashes']); verify(diagnostic['hashes'])
    p = ROOT/'config/hitter_workload_specialization_supplement_review.json'
    notes = read(p)
    assert set(notes)=={str(supplemental['selection']['row_id'])}
    assert all(n['review_status']=='complete' and n['assessment'] for n in notes.values())
    paths = [OUT/'final-report.json',OUT/'ordinary-case-supplement.json',OUT/'allocation-diagnostic.json',p,
        ROOT/'scripts/diagnose_hitter_workload_specialization.py',ROOT/'scripts/review_hitter_workload_specialization_supplement.py',
        ROOT/'scripts/finish_hitter_workload_specialization_review.py',ROOT/'tests/test_hitter_workload_allocation_accounting.py',
        ROOT/'docs/hitter-prospect-workload-specialization-legacy-clarification.md',ROOT/'docs/hitter-prospect-workload-specialization-diagnostic.md',
        ROOT/'docs/hitter-prospect-workload-specialization-result.md']
    write('completed-review.json',dict(player_walkthrough_status='complete',primary_cases=12,supplementary_cases=1,total_cases=13,
        supplementary_assessments=notes,disposition='Do not adopt either specialized workload head; preserve current opportunity and translated hitting anchor.',
        checks_before_fits=140,new_heads_replayed=70,pooled_controls_replayed=70,
        arrival_and_rate_fixed=True,established_unchanged=True,
        protected_outcomes_used=False,frozen_forecast_changed=False,explorer_changed=False,deployment_approved=False,full_goal_complete=False,
        hashes={str(p):sha256_file(p) for p in paths}))
    evidence = ROOT/'reports/model-evidence/hitter-prospect-workload-specialization'
    for name in ['ordinary-case-supplement.json','allocation-diagnostic.json','completed-review.json']:
        shutil.copyfile(OUT/name,evidence/name)
        assert sha256_file(OUT/name)==sha256_file(evidence/name)
    print('Thirteen completed model walkthroughs and exact allocation diagnostics sealed; full goal active.',flush=True)


if __name__=='__main__':main()
