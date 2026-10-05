"""Seal readable no-fit diagnosis; export compact evidence without promotion."""
import json
from pathlib import Path

from universal_baseball.storage import sha256_file
from run_hitter_count_baseline import ROOT, OUT as COUNT, read, verify

OUT = ROOT / 'reports/generated/hitter-count-error-diagnosis'


def main():
    assert not (OUT / 'final-review.json').exists()
    receipt, qualification = [read(OUT / name) for name in ['receipt.json', 'qualification.json']]
    verify(receipt['hashes'])
    verify(qualification['hashes'])
    for name in ['final-review.json', 'review-receipt.json', 'review-qualification.json']:
        verify(read(COUNT / name)['hashes'])
    assert receipt['new_fits'] == qualification['new_fits'] == 0
    assert qualification['independent_formula_identity_pass'] and qualification['complete_partition_families'] == 12
    cases = read(OUT / 'player-decomposition.json')
    additions = read(OUT / 'addition-decomposition.json')
    assert len(cases) == len({r['row_id'] for r in cases}) == 13
    docs = [ROOT / f'docs/hitter-count-error-diagnosis-{name}.md' for name in ['result', 'player-review']]
    content = docs[1].read_text(encoding='utf8')
    assert all(r['player_name'].split()[-1] in content for r in cases)
    assert len(additions) == 13 and all(not r['incumbent_available'] for r in additions)
    paths = [Path(__file__), *docs, *[OUT / n for n in ['receipt.json', 'qualification.json', 'global-attribution.json', 'addition-decomposition.json']]]
    final = dict(new_fits=0, player_walkthrough_status='complete', cases=13,
                 original_rows=qualification['original_rows'], additions_separate=13,
                 disposition='No forecast change; retain incumbent; one matched direct-value learning contrast next',
                 diagnostic_not_accuracy_improvement=True, protected_outcomes_used=False,
                 completed_2026_evaluation_unchanged=True, deployment_approved=False,
                 reasonability_status='Error mechanisms reviewed, replacement remains rejected; root cause not causally isolated',
                 research_goal_remains_active=True, hashes={str(p): sha256_file(p) for p in paths})
    p = OUT / 'final-review.json'
    p.write_text(json.dumps(final, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf8', newline='\n')
    public = ROOT / 'reports/model-evidence/hitter-count-error-diagnosis/report.json'
    assert not public.exists()
    public.parent.mkdir(parents=True, exist_ok=True)
    compact = dict(final, qualification=qualification, global_attribution=read(OUT / 'global-attribution.json'),
                   player_decomposition=cases, addition_decomposition=additions,
                   foreign_penalty_diagnostic=read(OUT / 'foreign-penalty-diagnostic.json'),
                   readable_result='docs/hitter-count-error-diagnosis-result.md',
                   readable_player_review='docs/hitter-count-error-diagnosis-player-review.md',
                   original_source_model_walks='reports/model-evidence/hitter-count-baseline/report.json')
    public.write_text(json.dumps(compact, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf8', newline='\n')
    print('No-fit diagnosis complete: 13 retained walks, 12 exact global partitions, 13 separately explained additions. No promotion.')


if __name__ == '__main__':
    main()
