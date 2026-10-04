"""Complete human player review, preserve receipts, and leave promotion closed."""
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import polars as pl
from universal_baseball.storage import sha256_file
import evaluate_hitter_offense_risk as e


def main():
    assert not (e.OUT/'final-report.json').exists(), 'Preserve completed review'
    pre = e.read(e.OUT/'preflight.json'); e.check_hashes(pre['input_hashes'])
    verification = e.read(e.OUT/'verification.json'); e.check_hashes(verification['output_hashes'])
    assert verification['nested_heads_replayed'] == 50
    assert verification['variance_fits_replayed'] == 35 and verification['distribution_rows_replayed'] == 30506
    reviewed = e.read(e.ROOT/'config/hitter_offense_risk_review.json')
    cases = e.read(e.OUT/'cases.json')+[e.read(e.OUT/'physical-case.json')]
    assert set(reviewed['cases']) == {str(c['origin']['row_id']) for c in cases}
    assert len(cases) == 17
    for c in cases:
        text = reviewed['cases'][str(c['origin']['row_id'])]
        assert len(text) > 350
        c['baseball_review'] = text; c['player_walkthrough_status'] = 'complete'
    e.write(e.OUT/'reviewed-cases.json', cases)
    lines = ['# Player checks for next year offense ranges', '',
        'Seventeen historical player checks trace actual source statistics, current point forecasts,',
        'nested calibration and new offense ranges. These forecasts use information available at',
        'the end of the stated origin season plus the documented following preseason information',
        'date, and predict the following calendar year. No 2026 outcomes are used.', '',
        'All offense numbers below are custom fixed-event batting plus replacement wins, not full WAR.',
        'Hit/600 is the current hitting-rate forecast. For active observed players the actual rate',
        'uses the common-origin environment; an inactive player has no observed hitting rate.',
        'The three distributions have the same mean. The table shows their P10, median and P90.', '',
        'Cases include nine fixed players, score gains and harms, false highs/lows, an ordinary',
        'final-value case with compensating errors, and the largest physical-tail failure.',
        'Complete model inputs, additive Ridge contributions, opportunity tree paths, calibration',
        'paths, per-PA probability mass and independent scalar quantiles are saved in',
        '[the reviewed evidence](../reports/model-evidence/hitter-offense-risk/reviewed-cases.json).', '']
    for c in cases:
        r = c['origin']; pars = c['variance_parameters']; dep = pars['sample_dependent']
        lines += [f'## {r["player_name"]} after {r["origin_year"]}', '',
            'Selection: '+', '.join(c['selection'])+'.', '',
            '| Season | Level | PA | HR | Unintentional BB | K |',
            '| --- | --- | ---: | ---: | ---: | ---: |']
        for s in c['source_history']:
            lines.append(f'| {s["season"]} | {s["bucket"]} | {s["plate_appearances"]} | {s["home_runs"]} | {s["unintentional_walks"]} | {s["strike_outs"]} |')
        lines += ['', f'Current forecast: {r["preseason_p"]:.2%} chance of any MLB PA, '
            f'{r["preseason_conditional_pa"]:.2f} PA conditional on appearing, '
            f'{r["preseason_pa"]:.2f} expected PA, {r["preseason_rate"]:+.3f} Hit/600 '
            f'and {r["preseason_value"]:+.3f} expected offense.', '',
            '| Distribution | P10 | Median | P90 |', '| --- | ---: | ---: | ---: |']
        for arm, label in [('fixed', 'Workload only'), ('constant', 'Constant hitting spread'), ('sample', 'Sample dependent spread')]:
            lines.append(f'| {label} | {r[arm+"_q10"]:+.3f} | {r[arm+"_q50"]:+.3f} | {r[arm+"_q90"]:+.3f} |')
        observed_rate = f'{r["next_batting_rate"]:+.3f}' if r['next_pa'] > 0 else 'unobserved'
        lines += ['', f'Reality: {r["next_pa"]} MLB PA, {observed_rate} actual Hit/600 '
            f'and {r["next_value"]:+.3f} delivered offense.', '',
            f'Calibration: {c["calibration_people"]} distinct earlier active players; '
            f'{r["calibration_people"]} share the refined origin-known profile. '
            f'Rate variance is {dep["a"]:.4f} + {dep["b"]:.4f} times 600/PA; '
            f'the constant reference variance is {pars["constant_variance"]:.4f}. '
            f'The uncentered nested residual bias is {pars["residual_bias"]:+.3f}. '
            'These numbers do not identify pure talent variance.', '']
        top = sorted(c['rate_contributions'].items(), key=lambda t: abs(t[1]), reverse=True)[:6]
        lines += ['The saved rate fit has intercept '+f'{c["rate_intercept"]:+.3f}'+
            '; its largest signed input contributions are '+', '.join(f'{name} {value:+.3f}' for name, value in top)+
            '. All contributions, not only these six, reproduce the current rate exactly.', '',
            f'Negative-offense probability is {r["sample_p_negative"]:.2%}; probability of at least '
            f'two custom offense wins is {r["sample_p_two"]:.2%}. Impossible conditional PA/offense '
            f'probability is {r["sample_impossible_mass"]:.2%}.', '', c['baseball_review'], '',
            'Origin-selected comparisons: '+ '; '.join(f'{p["player_name"]}: {p["next_pa"]} subsequent PA, '
                f'{p["next_value"]:+.2f} offense' for p in c['peers'])+'.', '',
            'Comparison limit: '+c['peer_limit']+'.', '']
    lines += ['## Review decision', '', reviewed['disposition'], '',
        'The canceled 2020 MiLB season is not treated as failed production; target 2020 is excluded.',
        'Observed short-season MLB counts remain explicit. The mean and source limitations of the',
        'current model remain. None of these cases authorizes deployment or a claim of full player value.', '']
    walk = e.ROOT/'docs/hitter-offense-risk-walkthrough.md'
    walk.write_text('\n'.join(lines), encoding='utf8', newline='\n')
    python = str(e.ROOT/'.venv/Scripts/python.exe')
    test = subprocess.run([python, '-X', 'utf8', '-m', 'pytest', 'tests/test_hitter_offense_risk.py',
        'tests/test_hitter_workload_risk.py', '-q', '-p', 'no:cacheprovider'], cwd=e.ROOT, text=True, capture_output=True)
    assert test.returncode == 0, test.stdout+test.stderr
    (e.OUT/'focused-tests.txt').write_text(test.stdout+test.stderr, encoding='utf8', newline='\n')
    freeze = json.loads(subprocess.check_output([python, '-X', 'utf8', str(e.ROOT/'scripts/verify_hitter_full_2026_freeze.py')], cwd=e.ROOT))
    assert freeze['status'] == 'verified' and freeze['protected_2026_opened'] is False
    q = pl.read_parquet(e.WORK/'scored-predictions.parquet'); base = pl.read_parquet(e.current.OUT/'scored-predictions.parquet').sort('row_id')
    assert q.select(base.columns).sort('row_id').equals(base)
    for arm in ['fixed', 'constant', 'sample']:
        assert np.allclose(q[arm+'_expected_value'], q['preseason_value'], atol=1e-10, rtol=0)
    paths = [e.OUT/n for n in ['preflight.json', 'fit-report.json', 'verification.json', 'scores.json', 'intervals.json',
        'cases.json', 'physical-case.json', 'limits.json', 'reviewed-cases.json', 'focused-tests.txt',
        'nested-checks.json', 'outer-support.parquet', 'calibration-profile-support.parquet']]
    paths += [walk, e.ROOT/'config/hitter_offense_risk_review.json', Path(__file__),
              e.ROOT/'scripts/score_hitter_offense_risk.py', e.ROOT/'scripts/review_hitter_offense_risk_limits.py']
    head_hashes = {}
    for cell in e.read(e.OUT/'fit-report.json')['cells']:
        e.check_hashes(cell['output_hashes']); head_hashes.update(cell['output_hashes'])
        for h in cell['nested_heads']:
            e.check_hashes(h['output_hashes']); head_hashes.update(h['output_hashes'])
    report = dict(player_walkthrough_status='complete', reviewed_cases=17, actual_preflight_checks=130,
        nested_rate_heads_replayed=50, outer_rate_heads_replayed=35, variance_fits_replayed=35,
        distribution_rows_replayed=30506, independent_scalar_quantiles=153, focused_tests=12,
        original_mean_and_forecast_columns_exact=True, physical_distribution_gate='failed_at_low_PA',
        statistical_disposition='Improved proper offense-risk scores versus both declared references; development evidence',
        predictive_disposition=reviewed['disposition'], full_population_calibration=False,
        current_candidate_changed=False, deployed_explorer_changed=False, protected_outcomes_used=False,
        freeze_verification=freeze, full_goal_complete=False,
        next_step='Build a coherent event-count risk construction with unchanged anchors; address PA-dependent residual bias rather than tuning Normal widths. Preserve unresolved readiness and public workload gaps.',
        evidence_hashes={str(p): sha256_file(p) for p in paths}, local_fit_hashes=head_hashes)
    e.write(e.OUT/'final-report.json', report)
    evidence = e.ROOT/'reports/model-evidence/hitter-offense-risk'; evidence.mkdir(parents=True, exist_ok=True)
    for p in paths[:14]+[e.OUT/'final-report.json']:
        dest = evidence/p.name; assert not dest.exists(), 'Preserve evidence copies'
        shutil.copyfile(p, dest); assert sha256_file(dest) == sha256_file(p)
    print(json.dumps({k: report[k] for k in ['player_walkthrough_status', 'reviewed_cases', 'physical_distribution_gate',
        'current_candidate_changed', 'full_goal_complete']}, indent=2), flush=True)


if __name__ == '__main__':
    main()
