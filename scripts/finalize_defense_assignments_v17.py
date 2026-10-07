"""Finalize one reviewed assignment experiment without refitting or deployment."""
import argparse
from pathlib import Path
import subprocess
import sys

import numpy as np
import polars as pl

from run_defense_assignments_v17 import ROOT, OUT, PUBLIC, check, read, write, hashes, verify
from run_hitter_finite_return_baseline import protections


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manual-review-complete', action='store_true')
    assert parser.parse_args().manual_review_complete, 'Main-agent stats/input/mechanics/reality review is required'
    check()
    assert not (OUT/'final-review.json').exists()
    report = read(OUT/'report.json')
    walk = read(OUT/'player-walkthrough.json')
    diagnosis = read(OUT/'diagnostic-review.json')
    assert read(OUT/'independent-verification.json')['status'] == 'passed'
    verify(diagnosis['hashes'])
    assert diagnosis['status'] == 'passed' and diagnosis['support_profiles_replayed'] == 12432
    assert walk['focal_cases'] == 23 and walk['records'] == 92
    assert all(c['peer_shortfall'] == 0 for c in walk['cases'])
    previous = read(ROOT/'reports/generated/defense-role-v15/player-walkthrough.json')['cases']
    for a, b in zip(previous, walk['cases'][:19]):
        assert [(r['player_id'],r['origin']) for r in a['records']] == [(r['player_id'],r['origin']) for r in b['records']]
    rows = pl.read_parquet(OUT/'predictions.parquet').to_dicts()
    interval_replay = []
    # Independent squared-error bootstrap reconstruction, not the score helper.
    for saved in report['intervals']:
        rs = [r for r in rows if r[saved['target']] is not None]
        people = sorted({r['player_id'] for r in rs})
        pi = {pid:i for i,pid in enumerate(people)}
        loss = np.zeros((len(people),3,2)); count = np.zeros((len(people),3))
        for r in rs:
            i,j = pi[r['player_id']], r['origin_year']-2022
            assert count[i,j] == 0
            count[i,j] = 1
            loss[i,j] = [(r[a]-r[saved['target']])**2 for a in (saved['left'],saved['right'])]
        rng = np.random.default_rng(saved['seed']); draws = []
        for _ in range(saved['draws']):
            sample = rng.integers(len(people), size=len(people))
            roots = np.sqrt(loss[sample].sum(axis=0)/count[sample].sum(axis=0)[:,None]).mean(axis=0)
            draws.append(float(roots[0]-roots[1]))
        limits = np.quantile(draws,[.025,.975])
        assert np.allclose(limits,saved['interval_95'],atol=1e-12,rtol=0)
        interval_replay.append(dict(target=saved['target'],anchor=saved['right'],people=len(people),
            draws=saved['draws'],interval_95=limits.tolist(),replayed=True))
    write('interval-verification.json',dict(status='passed',intervals=interval_replay,no_refits=True,no_2026_outcomes=True))
    paths = [ROOT/'tests'/n for n in ('test_defense_assignments.py','test_defense_jobs.py',
        'test_defense_role_logs.py','test_defense_role_scope.py','test_defense_role_calendar.py')]
    test = subprocess.run([sys.executable,'-X','utf8','-m','pytest','-p','no:cacheprovider',
        *map(str,paths),'-q'],cwd=ROOT,capture_output=True,text=True,encoding='utf8')
    write('test-review.json',dict(pytest_exit_code=test.returncode,tests=[str(p) for p in paths],
        stdout=test.stdout,stderr=test.stderr,qualification='Focused execution regression tests, not predictive validation.'))
    print(test.stdout,flush=True)
    assert test.returncode == 0, test.stderr
    owned = [ROOT/'docs/defense-assignments-v17-contract.md',ROOT/'docs/defense-assignments-v17-result.md',
        ROOT/'src/universal_baseball/defense_assignments.py',ROOT/'tests/test_defense_assignments.py']
    owned += [ROOT/'scripts'/n for n in ('run_defense_assignments_v17.py','verify_defense_assignments_v17.py',
        'review_defense_assignments_v17.py','inspect_defense_assignments_v17.py',
        'diagnose_defense_assignments_v17.py','finalize_defense_assignments_v17.py')]
    names = ('preflight.json','fit-report.json','report.json','independent-verification.json',
        'player-walkthrough.json','player-walkthrough.md','diagnostic-review.json','interval-verification.json','test-review.json')
    for name in names:
        assert (OUT/name).read_bytes() == (PUBLIC/name).read_bytes(), name
    owned += [OUT/n for n in names]
    protections()
    write('final-review.json',dict(status='reviewed_assignment_not_promoted',execution_integrity='passed',
        training_support='qualified_sparse_joint_profiles_and_unseen_groups_retained',
        predictive_improvement='combined_value_uncertain_native_defense_worse',
        baseball_reasonability='failed_current_specialist_role_and_component_cancellation_checks',
        player_walkthrough_status='complete',manual_reviewer='main agent; compact source/input/logit/allocation/quality/reality traces for all 23 focal cases and 69 peers, with detailed focal mechanism review',
        focal_cases=23,walked_records=92,preserved_focal_cases=19,preserved_original_peers=57,
        sparse_joint_profiles=11364,unseen_stage_role_fallbacks=1620,
        primary_value_RMSE_change=report['intervals'][0]['mean_origin_RMSE_difference'],
        primary_value_interval=report['intervals'][0]['interval_95'],
        disposition='Retain certified current/late/older evidence and capacity checks, not this individual assignment replacement. Existing practical native quality baselines remain available.',
        remaining=['Later-MLB minor defensive talent identification with joint input/target support',
            'Practical position-development and multi-year opportunity/value integration',
            'Cutoff-known upcoming assignments omitted from historical role model',
            'Separate Lovich batting small-sample defect remains open'],
        no_2026_outcomes_used=True,frozen_forecast_and_explorer_unchanged=True,full_defense_goal_complete=False,
        supersedes_pending_review_status_in_preserved_artifacts=True,hashes=hashes(owned)))
    protections()
    print('Assignment review complete; no promotion. Defense goal remains active.',flush=True)


if __name__ == '__main__':
    main()
