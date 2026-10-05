"""Independent checks for the completed dependency contrast, not promotion."""
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import numpy as np
import polars as pl

from run_hitter_employment_comparison import ROOT, GEN, OLD, FIX, read, verify
from finalize_hitter_employment_comparison import independent_score
from universal_baseball.employment_comparison import FLAGS
from universal_baseball.storage import sha256_file

FIRST = GEN / 'hitter-employment-comparison'
OUT = GEN / 'hitter-employment-comparison-v2'
ALLOWED = FLAGS + ['signed_first_team_work', 'employment_evidence_unknown',
                   'employment_evidence_age_years']


def independent_timing(now, latest):
    if latest is None:
        return 1., 0.
    elapsed = (date.fromisoformat(now) - date.fromisoformat(latest)).days
    assert elapsed >= 0
    return 0., min(elapsed, 3650) / 365.


def main():
    public = ROOT / 'reports/model-evidence/hitter-employment-comparison-v2/report.json'
    if (OUT / 'final-review.json').exists() or public.exists():
        raise ValueError('Preserve completed receipts')
    receipt = read(OUT / 'review-receipt.json')
    pre = read(OUT / 'preflight.json')
    verify(receipt['hashes'])
    verify(pre['hashes'])
    assert pre['allowed_changes'] == ALLOWED
    assert len(pre['checks']) == 140 and pre['baseline_heads_replayed'] == 70
    assert receipt['corrected_heads_replayed'] == 70

    # Reconstruct timing independently from actual old and corrected ledger dates.
    ledger = read(GEN / 'hitter-status-evidence-v2/status-ledger.json')['rows']
    deltas = {r['candidate_key']: r for r in read(FIX / 'employment-deltas.json')['rows']}
    timing_rows = {r['candidate_key']: r for r in pl.read_parquet(OUT / 'employment-timing.parquet').to_dicts()}
    assert len(ledger) == len(timing_rows) == 83300
    source_checks = 0
    for r in ledger:
        t = timing_rows[r['candidate_key']]
        assert (r['origin_year'], r['player_id'], r['information_date']) == (
            t['origin_year'], t['player_id'], t['information_date'])
        assert r['target_year'] == r['origin_year'] + 1 <= 2025
        old_latest = r['employment']['latest_date']
        new_latest = deltas.get(r['candidate_key'], r)['employment']['latest_date']
        for prefix, latest in [('old', old_latest), ('new', new_latest)]:
            assert t[prefix + '_latest_date'] == latest
            unknown, age = independent_timing(r['information_date'], latest)
            assert t[prefix + '_employment_evidence_unknown'] == unknown
            assert t[prefix + '_employment_evidence_age_years'] == age
            source_checks += 3
    del ledger, deltas, timing_rows

    timing = pl.read_parquet(OUT / 'employment-timing.parquet')
    indicators = pl.read_parquet(FIX / 'employment-indicators.parquet')
    matrix_checks = 0
    for k in range(5):
        a = pl.read_parquet(OLD / f'features-{k}.parquet').sort('row_id')
        b = pl.read_parquet(OUT / f'features-{k}.parquet').sort('row_id')
        assert a.height == b.height == 63314
        assert a.columns == b.columns and a.schema == b.schema
        unchanged = [n for n in a.columns if n not in ALLOWED]
        assert a.select(unchanged).equals(b.select(unchanged))
        idx = b.select('row_id', 'origin_year', 'player_id', 'ctx_information_date')
        expected = idx.join(indicators.select('origin_year', 'player_id', 'information_date', *FLAGS),
                            on=['origin_year', 'player_id'], validate='1:1').sort('row_id')
        assert expected.height == b.height and expected['information_date'].null_count() == 0
        assert expected['information_date'].equals(b['ctx_information_date'])
        assert np.array_equal(b.select(FLAGS).to_numpy(), expected.select(FLAGS).to_numpy())
        dates = idx.join(timing, on=['origin_year', 'player_id'], validate='1:1').sort('row_id')
        assert dates['information_date'].equals(b['ctx_information_date'])
        for prefix, frame in [('old', a), ('new', b)]:
            for n in ['employment_evidence_unknown', 'employment_evidence_age_years']:
                assert frame[n].equals(dates[prefix + '_' + n])
            signed = np.where((frame['status_major_link'].to_numpy() > 0) |
                              (frame['on_40man'].to_numpy() > 0) |
                              (frame['status_agreement_unspecified'].to_numpy() > 0),
                              frame['last_first_team_work'].to_numpy(), 0.)
            assert np.array_equal(signed, frame['signed_first_team_work'].to_numpy())
        if k == 0:
            changed = np.any(a.select(ALLOWED).to_numpy() != b.select(ALLOWED).to_numpy(), axis=1)
            marks = pl.read_parquet(OUT / 'source-changes.parquet').sort('row_id')
            assert a['row_id'].equals(marks['row_id'])
            assert np.array_equal(changed, marks['employment_input_changed'].to_numpy())
            assert int(changed.sum()) == 10276
            date_change = dates['old_latest_date'].fill_null('unknown') != dates['new_latest_date'].fill_null('unknown')
            assert int(date_change.sum()) == 10267
        matrix_checks += a.height * len(ALLOWED)

    q = pl.read_parquet(OUT / 'predictions.parquet').sort('row_id')
    old = pl.read_parquet(OLD / 'predictions.parquet').sort('row_id')
    assert q.height == 30519 and q.select(old.columns).equals(old)
    assert q['old_job_rate'].equals(q['corrected_job_rate'])
    assert q['target_year'].max() == 2025 and not q['next_pa'].is_null().any()
    fit = read(OUT / 'fit-report.json')
    assert len(fit['cells']) == 35 and sha256_file(OUT / 'predictions.parquet') == fit['predictions_sha256']
    for c in fit['cells']:
        assert len(c['heads']) == 2
        assert sha256_file(ROOT / c['predictions_path']) == c['predictions_sha256']
        for h in c['heads']:
            assert sha256_file(ROOT / h['path']) == h['sha256']

    original = q.filter(~pl.col('source_addition'))
    assert original.height == 30506 and q.filter(pl.col('source_addition')).height == 13
    assert original.filter(pl.col('employment_input_changed')).height == 7125
    foreign = b.filter(pl.col('evidence_foreign_source_present') > 0)['row_id'].to_list()
    from prepare_hitter_overseas_integration import ANCHOR
    public_ids = pl.read_parquet(ANCHOR, columns=['row_id', 'steamer_index', 'zips_index'])
    public_rows = original.join(public_ids, on='row_id', how='left', validate='1:1').filter(
        (pl.col('pa_0') > 0) & pl.col('steamer_index').is_not_null() & pl.col('zips_index').is_not_null())
    groups = {'original_all': original, 'additions': q.filter(pl.col('source_addition')),
              'public': public_rows, 'foreign': q.filter(pl.col('row_id').is_in(foreign)),
              'affected_original': original.filter(pl.col('employment_input_changed')),
              'unaffected_original': original.filter(~pl.col('employment_input_changed')),
              'current_regular': original.filter(pl.col('pa_0') >= 400),
              'current_partial': original.filter(pl.col('pa_0').is_between(1, 399)),
              'absent_prior_debut': original.filter((pl.col('pa_0') == 0) & (pl.col('prior_debut') > 0))}
    groups.update({'origin_' + str(y): original.filter(pl.col('origin_year') == y)
                   for y in original['origin_year'].unique()})
    groups.update({'stage_' + s: original.filter(pl.col('stage') == s)
                   for s in original['stage'].unique()})
    groups.update({'never_' + s: original.filter((pl.col('stage') == s) & (pl.col('prior_debut') == 0))
                   for s in ['Upper minors', 'Lower minors']})
    score_checks = 0
    scores = read(OUT / 'scores.json')
    for reported in scores['scopes']:
        g = groups[reported['scope']]
        assert reported['rows'] == g.height and reported['people'] == g['player_id'].n_unique()
        assert reported['actual_PA'] == g['next_pa'].sum()
        assert np.isclose(reported['actual_value'], g['actual_relative_value'].sum(), atol=1e-8)
        for arm, result in reported['scores'].items():
            for n, v in independent_score(g, arm).items():
                assert np.isclose(v, result[n], atol=1e-10, rtol=0), (reported['scope'], arm, n)
                score_checks += 1
            for name, col in [('expected_pa', '_pa'), ('expected_arrivals', '_p'), ('expected_value', '_value')]:
                assert np.isclose(g[arm + col].sum(), result[name], atol=1e-8, rtol=0)
                score_checks += 1
    cases = read(OUT / 'player-walks.json')['cases']
    retained = {c['origin']['row_id'] for c in read(FIRST / 'player-walks.json')['cases']}
    assert len(cases) == 125 and len(retained) == 113
    assert retained.issubset({c['origin']['row_id'] for c in cases})
    assert set(read(OUT / 'case-selection.json')['selected']) == {str(c['origin']['row_id']) for c in cases}
    product_checks = 0
    for c in cases:
        r, a, b = c['origin'], c['old_model_inputs'], c['corrected_model_inputs']
        for arm, inputs in [('old_job', a), ('corrected_job', b)]:
            t = c['head_mechanics'][arm + '_participation']
            u = c['head_mechanics'][arm + '_conditional_pa']
            probability = t['linked_probability']
            if inputs['status_hard_unavailable'] or inputs['status_retired']:
                probability = 0.
            assert np.isclose(probability, r[arm + '_p'], atol=1e-10)
            assert np.isclose(probability * np.clip(u['raw_prediction'], 1, 800), r[arm + '_pa'], atol=1e-8)
            assert np.isclose(r[arm + '_pa'] * (r[arm + '_rate'] / 600 + r['origin_replacement_rate']),
                              r[arm + '_value'], atol=1e-10)
            product_checks += 3
        assert c['input_changes'] == {n: [a[n], b[n]] for n in pre['job_features'] if a[n] != b[n]}
        assert not (set(c['input_changes']) - set(ALLOWED))

    tests = []
    for command in [[sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
                     'tests/test_employment_comparison.py', 'tests/test_employment_timing.py'],
                    [sys.executable, 'scripts/verify_hitter_selected_2026_freeze.py'],
                    [sys.executable, 'scripts/verify_hitter_full_2026_freeze.py']]:
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if completed.returncode:
            raise ValueError(completed.stdout + completed.stderr)
        tests.append(dict(command=command[1:], exit_code=0, output=completed.stdout))
    paths = [Path(__file__), ROOT / 'docs/hitter-employment-comparison-v2-result.md',
             ROOT / 'docs/hitter-employment-comparison-v2-player-review.md',
             OUT / 'review-receipt.json', OUT / 'scores.json', OUT / 'intervals.json',
             OUT / 'predictions.parquet', OUT / 'case-selection.json', OUT / 'player-walks.json']
    result = dict(status='review_complete_full_dependency_correction_no_promotion',
                  player_walkthrough_status='complete', machine_traces=125, retained_traces=113,
                  complete_employment_correction_tested=True, source_parser_correction_retained=True,
                  primary_PA_improvement_demonstrated=False, source_correction_contrast_closed=True,
                  further_source_correction_variants_authorized=False, deployment_approved=False,
                  new_heads=70, baseline_replayed=70, corrected_replayed=70, target_year_maximum=2025,
                  timing_source_checks=source_checks, employment_matrix_checks=matrix_checks,
                  independent_score_checks=score_checks, independent_case_product_checks=product_checks,
                  completed_2026_evaluation_unchanged=True,
                  next_action='Inventory prior availability work and cutoff-known restriction timing before any new fit',
                  tests_and_freezes=tests, hashes={str(p.relative_to(ROOT)): sha256_file(p) for p in paths})
    verify(receipt['hashes'])
    verify(pre['hashes'])
    (OUT / 'final-review.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf8', newline='\n')
    public.parent.mkdir(parents=True, exist_ok=True)
    public.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8', newline='\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ['hashes', 'tests_and_freezes']}), flush=True)


if __name__ == '__main__':
    main()
