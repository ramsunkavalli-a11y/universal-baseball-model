"""Lock the completed comparison only after actual player review and rechecks."""
from datetime import date
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import polars as pl

from run_hitter_nonmedical_opportunity import ROOT, GEN, BASE, SOURCE, OUT, read, verify
from universal_baseball.nonmedical_opportunity import FIELDS, OBS
from universal_baseball.storage import sha256_file
from finalize_hitter_employment_comparison import independent_score
from review_hitter_nonmedical_opportunity import groups


def main():
    public = ROOT / 'reports/model-evidence/hitter-nonmedical-opportunity/report.json'
    if (OUT / 'final-review.json').exists() or public.exists():
        raise ValueError('Preserve completed comparison')
    review, pre = read(OUT / 'review-receipt.json'), read(OUT / 'preflight.json')
    verify(review['hashes'])
    verify(pre['hashes'])
    assert review['heads_replayed'] == 140 and len(pre['checks']) == 140
    assert pre['baseline_heads_replayed'] == 70
    feature_use = read(OUT / 'feature-use-audit.json')
    feature_seal = read(OUT / 'feature-use-source-seal.json')
    assert feature_use['code_sha256'] == feature_seal['code_sha256'] == sha256_file(ROOT / 'scripts/audit_nonmedical_feature_use.py')
    assert feature_use['models_inspected'] == 140 and feature_use['tested_feature_splits'] == 0
    assert feature_use['paired_initial_prediction_matches'] == 70
    assert feature_use['paired_tree_node_array_matches'] == 17500
    assert feature_use['exact_prediction_field_checks'] == 213633
    assert all(sum(c['tested_feature_split_counts'].values()) == 0 for c in feature_use['cells'])
    ledger = read(GEN / 'hitter-status-evidence-v2/status-ledger.json')['rows']
    source = pl.read_parquet(OUT / 'source-inputs.parquet')
    source_rows = {(r['origin_year'], r['player_id']): r for r in source.to_dicts()}
    observed = {r['candidate_key']: r for r in pl.read_parquet(SOURCE / 'observations.parquet').to_dicts()}
    source_checks = 0
    for r in ledger:
        o, s, a = observed[r['candidate_key']], source_rows[r['origin_year'], r['player_id']], r['absence']
        now = date.fromisoformat(r['information_date'])
        assert s['information_date'] == o['information_date'] == r['information_date']
        assert s['captured_legal_class'] == a['state']
        assert s['observation_has_return'] == bool(o['observed_after_channel_names'])
        for prefix, flags, games, end, report in [
            ('legacy_', [r[n] for n in FIELDS[:2]], a['original_duration_games'], a['known_calendar_end'], a['reported_return_date']),
            ('obs_', [o['observation_finite_nonmedical'], o['observation_unresolved_nonmedical']],
             o['unresolved_original_duration_games'], o['unresolved_known_calendar_end'], o['current_return_date'])]:
            expected = [*map(float, flags), float(games is not None), min(games, 1000) / 100 if games is not None else 0.,
                float(end is not None), max(-365, min(365, (date.fromisoformat(end) - now).days)) / 365 if end else 0.,
                float(report is not None), max(-365, min(365, (date.fromisoformat(report) - now).days)) / 365 if report else 0.]
            for n, v in zip(FIELDS, expected, strict=True):
                assert s[prefix + n] == v
                source_checks += 1
    del ledger, observed
    matrix_checks = 0
    for k in range(5):
        old = pl.read_parquet(BASE / f'features-{k}.parquet').sort('row_id')
        new = pl.read_parquet(OUT / f'features-{k}.parquet').sort('row_id')
        assert old.height == new.height == 63314 and new.select(old.columns).equals(old)
        j = new.select('row_id', 'origin_year', 'player_id', 'ctx_information_date').join(
            source, on=['origin_year', 'player_id'], validate='1:1').sort('row_id')
        assert j['information_date'].equals(new['ctx_information_date'])
        assert np.array_equal(j.select(list(OBS.values())).to_numpy(), new.select(list(OBS.values())).to_numpy())
        assert np.array_equal(j.select(['legacy_' + n for n in FIELDS]).to_numpy(), new.select(FIELDS).to_numpy())
        matrix_checks += new.height * 16
        if k == 0:
            changed = np.any(new.select(FIELDS).to_numpy() != new.select(list(OBS.values())).to_numpy(), axis=1)
            marks = pl.read_parquet(OUT / 'source-changes.parquet').sort('row_id')
            assert new['row_id'].equals(marks['row_id'])
            assert np.array_equal(changed, marks['observation_input_changed'].to_numpy())
            assert int(changed.sum()) == 122
            context = new
    q = pl.read_parquet(OUT / 'predictions.parquet').sort('row_id')
    old = pl.read_parquet(BASE / 'predictions.parquet').sort('row_id')
    assert q.height == 30519 and q.select(old.columns).equals(old)
    assert q['target_year'].max() == 2025 and not q['next_pa'].is_null().any()
    assert q['corrected_job_rate'].equals(q['observation_rate'])
    exact_prediction_checks = 0
    for suffix in ['_raw_p', '_raw_conditional_pa', '_p', '_conditional_pa', '_pa', '_rate', '_value']:
        # Column names in the sealed forecast, not a rounded score comparison.
        assert q['corrected_job' + suffix].equals(q['observation' + suffix])
        exact_prediction_checks += q.height
    assert exact_prediction_checks == feature_use['exact_prediction_field_checks']
    assert feature_use['predictions_sha256'] == sha256_file(OUT / 'predictions.parquet')
    assert q.filter(pl.col('observation_input_changed')).height == 89
    fit = read(OUT / 'fit-report.json')
    assert len(fit['cells']) == 35 and sha256_file(OUT / 'predictions.parquet') == fit['predictions_sha256']
    for c in fit['cells']:
        assert sha256_file(ROOT / c['predictions_path']) == c['predictions_sha256']
        for h in c['heads']:
            assert sha256_file(ROOT / h['path']) == h['sha256']
    scopes = groups(q, context)
    scores = read(OUT / 'scores.json')
    score_checks = 0
    for recorded in scores['scopes']:
        g = scopes[recorded['scope']]
        assert recorded['rows'] == g.height and recorded['people'] == g['player_id'].n_unique()
        assert recorded['actual_PA'] == g['next_pa'].sum()
        assert recorded['actual_participants'] == (g['next_pa'] > 0).sum()
        assert np.isclose(recorded['actual_value'], g['actual_relative_value'].sum(), atol=1e-8, rtol=0)
        for arm, result in recorded['scores'].items():
            for n, v in independent_score(g, arm).items():
                assert np.isclose(v, result[n], atol=1e-10, rtol=0), (recorded['scope'], arm, n)
                score_checks += 1
            for n, suffix in [('expected_pa', '_pa'), ('expected_arrivals', '_p'), ('expected_value', '_value')]:
                assert np.isclose(result[n], g[arm + suffix].sum(), atol=1e-8, rtol=0)
            for subset, name in [(g.filter(pl.col('next_pa') > 0), 'PA_to_participants'),
                                 (g.filter(pl.col('next_pa') == 0), 'PA_to_nonparticipants')]:
                assert np.isclose(recorded['allocation'][arm][name], subset[arm + '_pa'].sum(), atol=1e-8, rtol=0)
    cases = read(OUT / 'player-walks.json')['cases']
    selection = read(OUT / 'case-selection.json')['selected']
    assert set(selection) == {str(c['origin']['row_id']) for c in cases}
    case_checks = 0
    for c in cases:
        r, inputs = c['origin'], c['model_inputs']
        assert q.filter(pl.col('row_id') == r['row_id']).row(0, named=True) == r
        assert c['input_changes'] == {n: [inputs[n], inputs[OBS[n]]] for n in FIELDS if inputs[n] != inputs[OBS[n]]}
        for arm in ['corrected_job', 'observation']:
            t, u = c['head_mechanics'][arm + '_participation'], c['head_mechanics'][arm + '_conditional_pa']
            p = t['linked_probability']
            if inputs['status_hard_unavailable'] or inputs['status_retired']:
                p = 0.
            cond = float(np.clip(u['raw_prediction'], 1, 800))
            assert np.isclose(p, r[arm + '_p'], atol=1e-10)
            assert np.isclose(cond, r[arm + '_conditional_pa'], atol=1e-8)
            assert np.isclose(p * cond, r[arm + '_pa'], atol=1e-8)
            assert np.isclose(p * cond * (r[arm + '_rate'] / 600 + r['origin_replacement_rate']),
                              r[arm + '_value'], atol=1e-8)
            case_checks += 4
    by_scope = {r['scope']: r for r in scores['scopes']}
    paired = next(r for r in read(OUT / 'intervals.json')['comparisons']
                  if r['scope'] == 'original_all' and r['baseline'] == 'corrected_job')
    primary = next(r for r in paired['intervals'] if r['metric'] == 'pa_mse')
    stage_warnings = [name for name, r in by_scope.items() if name.startswith('stage_') and r['rows'] >= 200
        and r['scores']['observation']['pa_rmse'] > 1.02 * r['scores']['corrected_job']['pa_rmse']]
    decision = dict(source_repair_retained=True, primary_improvement_interval_below_zero=primary['upper'] < 0,
        major_stage_deteriorations_over_two_percent=stage_warnings,
        predictive_improvement_not_established=True, rare_profile_certification=False,
        deployment_approved=False, disposition='retain_corrected_source_withhold_candidate_close_contrast',
        no_setting_or_feature_variants_authorized=True,
        exact_null_due_to_unused_tested_inputs=True, baseball_value_of_availability_rejected=False)
    # The conservative disposition must match the reviewed result, not a script default.
    assert primary['upper'] >= 0, 'Unexpected primary win requires a separately reviewed decision before closure'
    tests = []
    for command in [[sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
        'tests/test_nonmedical_observation.py', 'tests/test_nonmedical_opportunity.py'],
        [sys.executable, 'scripts/verify_hitter_selected_2026_freeze.py'],
        [sys.executable, 'scripts/verify_hitter_full_2026_freeze.py']]:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if result.returncode:
            raise ValueError(result.stdout + result.stderr)
        tests.append(dict(command=command[1:], exit_code=0, output=result.stdout))
    docs = [ROOT / 'docs/hitter-nonmedical-opportunity-result.md', ROOT / 'docs/hitter-nonmedical-opportunity-player-review.md']
    for path in docs:
        assert path.exists(), 'Human player/result review required'
    verify(review['hashes'])
    verify(pre['hashes'])
    paths = [Path(__file__), *docs, OUT / 'preflight.json', OUT / 'fit-report.json', OUT / 'predictions.parquet',
        OUT / 'review-receipt.json', OUT / 'scores.json', OUT / 'intervals.json',
        OUT / 'case-selection.json', OUT / 'player-walks.json',
        ROOT / 'scripts/audit_nonmedical_feature_use.py', ROOT / 'docs/source-correction-impact-gate.md',
        OUT / 'feature-use-audit.json', OUT / 'feature-use-source-seal.json']
    final = dict(status='historical_comparison_review_complete_no_promotion',
        player_walkthrough_status='complete', evaluation_rows=30519, original_rows=30506, additions=13,
        source_rows=63314, changed_source_input_rows=122, changed_evaluated_origins=89,
        source_numeric_checks=source_checks, matrix_numeric_checks=matrix_checks,
        independent_score_checks=score_checks, case_product_checks=case_checks,
        player_cases=len(cases), distinct_case_people=len({c['origin']['player_id'] for c in cases}),
        new_heads=70, replayed_heads=140, decision=decision, tests_and_freezes=tests,
        exact_prediction_field_checks=exact_prediction_checks, tested_feature_splits=0,
        paired_tree_node_array_matches=17500,
        talent_changed=False, selected_forecast_changed=False, completed_2026_evaluation_unchanged=True,
        hashes={str(p.relative_to(ROOT)): sha256_file(p) for p in paths})
    payload = json.dumps(final, indent=2) + '\n'
    (OUT / 'final-review.json').write_text(payload, encoding='utf8', newline='\n')
    public.parent.mkdir(parents=True, exist_ok=True)
    public.write_text(payload, encoding='utf8', newline='\n')
    print(json.dumps({k: v for k, v in final.items() if k not in {'hashes', 'tests_and_freezes'}}), flush=True)


if __name__ == '__main__':
    main()
