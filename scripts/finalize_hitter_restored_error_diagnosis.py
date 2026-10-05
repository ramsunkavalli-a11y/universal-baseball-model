"""Close readable no-fit review, preserving incumbent and completed evaluation."""
from pathlib import Path
import json

import numpy as np

from universal_baseball.storage import sha256_file
from diagnose_hitter_restored_errors import ROOT, OUT, PREVIOUS, TERMS, read, verify, save


def main():
    assert not (OUT / 'final-review.json').exists()
    receipt = read(OUT / 'receipt.json'); verify(receipt['hashes'])
    assert receipt['new_fits'] == 0 and receipt['unchanged_forecasts'] and receipt['unchanged_PA']
    assert receipt['every_row_geometry_independently_verified'] and receipt['partition_identities_verified']
    assert receipt['source_profiles_independently_reconstructed'] and receipt['labels_independently_reconstructed']
    assert receipt['sealed_model_hashes_checked'] == 105 and not receipt['protected_outcomes_used']
    docs = [ROOT / f'docs/hitter-restored-error-diagnosis-{n}.md' for n in ['result', 'player-review']]
    content = docs[1].read_text(encoding='utf8')
    evidence = read(OUT / 'player-decomposition.json')
    cases = evidence['cases']; assert len(cases) == len({r['row_id'] for r in cases}) == 17
    for r in cases:
        assert str(r['row_id']) in content and r['information_date'] in content
        assert r['player_name'].split()[-1].rstrip('.') in content
        p = ROOT / r['full_source_model_walk']['report']
        assert sha256_file(p) == r['full_source_model_walk']['sha256']
        old = next(c for c in read(p)['player_cases'] if c['row_id'] == r['row_id'])
        assert old['raw_history'] or old['source']['contributions']
        assert old['feature_terms'] and old['support'] and old['origin_selected_peers']
        for arm in r['arms'].values():
            if r['actual_PA']:
                assert np.isclose(arm['hitting_error_at_expected_PA'] + arm['opportunity_error_at_observed_rate'], arm['delivered_error'], atol=1e-10)
            else:
                assert arm['hitting_error_at_expected_PA'] is None and arm['opportunity_error_at_observed_rate'] is None
        for contrast in r['contrasts'].values():
            assert np.isclose(contrast['delta'], sum(contrast[k] for k in TERMS[1:]), atol=1e-10)
        assert np.isclose(r['baseline'] + r['fitted_residual'], r['arms']['components']['rate'], atol=1e-10)
    additions = evidence['additions']; assert len(additions) == 13 and all(not r['incumbent_available'] for r in additions)
    a = read(OUT / 'attribution.json')
    for anchor, comparison in a['contrasts'].items():
        for family in ['joint_profile', 'origin', 'participation']:
            for key in TERMS:
                assert np.isclose(sum(r['global_MSE_terms'][key] for r in comparison[family]), comparison['global_MSE_terms'][key], atol=1e-12)
            assert sum(r['rows'] for r in comparison[family]) == 30506
        assert np.isclose(comparison['global_MSE_terms']['delta'], sum(comparison['global_MSE_terms'][k] for k in TERMS[1:]), atol=1e-12)
    previous = read(PREVIOUS / 'final-review.json'); verify(previous['hashes'])
    payload = dict(new_fits=0, original_rows=30506, additions_separate=13, inherited_actual_source_model_walks=17,
                   player_walkthrough_status='complete', diagnostic_not_forecast_improvement=True,
                   integrity_status='Immutable forecasts/models/sources and independently reconstructed labels, profiles, equations and partitions verified',
                   profile_status='Prior absent/sparse joint support remains qualified; six cells are descriptive, not deployment branches',
                   predictive_status='Nominal incumbent contrast remains uncertain near-tie; matched seven-input gain preserved',
                   reasonability_status='Actual player checks distinguish reinforcing errors, cancellation, missed opportunity and unobserved absent-player talent',
                   disposition='Retain incumbent; prospective same-input absolute-rate question requires a separate contract and prefit checks',
                   raw_internal_labels_qualification='Legacy inactive hitting labels and zero-weight internal rate deltas are not observed batting ability; public case labels are null and hitting contributions use active PA only',
                   protected_outcomes_used=False, completed_2026_evaluation_unchanged=True, deployment_approved=False, research_goal_remains_active=True,
                   readable_result='docs/hitter-restored-error-diagnosis-result.md', readable_walks='docs/hitter-restored-error-diagnosis-player-review.md',
                   attribution=a, cases=cases, additions=additions,
                   hashes={str(p): sha256_file(p) for p in [Path(__file__), *docs, OUT / 'receipt.json', ROOT / 'tests/test_hitter_restored_error_diagnosis.py']})
    public = ROOT / 'reports/model-evidence/hitter-restored-error-diagnosis/report.json'
    assert not public.exists()
    public.parent.mkdir(parents=True, exist_ok=True)
    public.write_text(json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf8', newline='\n')
    save('final-review.json', dict(payload, public_report=str(public), public_report_sha256=sha256_file(public)))
    print('No-fit diagnosis and 17 player checks complete. Incumbent and completed 2026 evaluation unchanged; long goal active.')


if __name__ == '__main__':
    main()
