"""Independently count every completed case quantile, including the added case."""
from pathlib import Path
import numpy as np
from universal_baseball.hitter_workload_risk import mixture_pmf
from universal_baseball.storage import sha256_file
from score_hitter_offense_risk import scalar_quantiles
import evaluate_hitter_offense_risk as e


def main():
    assert not (e.OUT/'review-verification.json').exists(), 'Preserve verification'
    final = e.read(e.OUT/'final-report.json'); e.check_hashes(final['evidence_hashes']); e.check_hashes(final['local_fit_hashes'])
    fits = {(c['year'], c['fold']): c for c in e.read(e.OUT/'fit-report.json')['cells']}
    cases = e.read(e.OUT/'reviewed-cases.json'); checks = []
    for c in cases:
        r = c['origin']; cell = fits[r['origin_year'], r['outer_fold']]
        pars = cell['variance_parameters']; pmf = mixture_pmf([r['preseason_p']], [r['preseason_conditional_pa']], cell['workload_concentration'])[0]
        for arm, a, b in [('fixed', None, 0), ('constant', pars['constant_variance'], 0),
                          ('sample', pars['sample_dependent']['a'], pars['sample_dependent']['b'])]:
            fresh = scalar_quantiles(pmf, r['preseason_rate'], r['origin_replacement_rate'], a, b)
            assert np.allclose(fresh, [r[arm+'_q'+str(n)] for n in [10, 50, 90]], atol=1e-8, rtol=0)
            checks.append(dict(row_id=r['row_id'], arm=arm, quantiles=fresh))
    assert len(checks)*3 == 153
    note = dict(cases=17, independently_verified_scalar_quantiles=len(checks)*3, checks=checks,
        original_receipt_qualification='The finalizer initially counted nine checks for each of seventeen cases, although the separate physical case had then replayed only its three sample-dependent quantiles. This follow-up actually recomputes all three arms for all seventeen cases. The original receipts are preserved.',
        input_hashes={str(p): sha256_file(p) for p in [Path(__file__), e.OUT/'final-report.json', e.OUT/'reviewed-cases.json']},
        current_candidate_changed=False, protected_outcomes_used=False)
    e.write(e.OUT/'review-verification.json', note)
    dest = e.ROOT/'reports/model-evidence/hitter-offense-risk/review-verification.json'
    assert not dest.exists(); dest.write_bytes((e.OUT/'review-verification.json').read_bytes())
    print('153 actual scalar checks passed across seventeen reviewed players; receipt count qualification retained.', flush=True)


if __name__ == '__main__':
    main()
