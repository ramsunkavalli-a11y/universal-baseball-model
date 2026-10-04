"""Require actual human case review before a count-risk disposition receipt."""
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.mlb_event_logit import EVENTS, VALUES
from universal_baseball.hitter_compatible_value import UNIT
from universal_baseball.storage import sha256_file
import evaluate_hitter_event_count_risk as e


def main():
    assert not (e.OUT/'final-report.json').exists(), 'Preserve completed evidence'
    preparation = e.read(e.OUT/'preparation-verification.json')
    e.old.check_hashes(preparation['source_hashes']); e.old.check_hashes(preparation['audit_hashes'])
    scored = e.read(e.OUT/'scoring-verification.json'); e.old.check_hashes(scored['artifact_hashes'])
    mc = e.read(e.OUT/'monte-carlo-audit.json'); e.old.check_hashes(mc['source_hashes'])
    limits = e.read(e.OUT/'limits.json'); e.old.check_hashes(limits['source_hashes'])
    assert sha256_file(e.WORK/'monte-carlo-audit.parquet') == mc['artifact_sha256']
    replay = e.read(e.OUT/'case-replay-verification.json')
    assert sha256_file(e.OUT/'cases.json') == replay['evidence_sha256']
    reviewed = e.read(e.ROOT/'config/hitter_event_count_risk_review.json')
    cases = e.read(e.OUT/'cases.json')
    assert set(reviewed['cases']) == {str(c['origin']['row_id']) for c in cases}
    assert reviewed['selected_law'] in ['none', 'independent', 'associated']
    if reviewed['selected_law'] != 'none':
        assert limits['numerical_ranking_stable'], 'Do not select a numerically unstable research law'
    assert len(reviewed['disposition']) > 250
    quantiles_verified = 0; exact_draws_verified = 0
    for case in cases:
        r = case['origin']; text = reviewed['cases'][str(r['row_id'])]
        assert len(text) > 350, ('Insufficient player judgment', r['row_id'])
        e.old.check_hashes(case['draw_artifact_hashes'])
        for arm in ['independent', 'associated']:
            p = e.WORK/f'case-{r["row_id"]}-{arm}-draws.parquet'
            draw = pl.read_parquet(p); counts = draw.select(['count_'+v for v in EVENTS]).to_numpy()
            n = draw['pa'].to_numpy(); value = draw['value'].to_numpy()
            assert counts.shape == (4096, 8) and (counts >= 0).all()
            assert np.issubdtype(counts.dtype, np.integer) and np.array_equal(counts.sum(1), n)
            fresh = (counts @ VALUES-n*r['origin_index'])*UNIT/600+n*r['origin_replacement_rate']
            assert np.array_equal(fresh, value)
            # Independent explicit weighted-support crossing, not mixture_terms.
            pairs = sorted([(float(v), r['preseason_p']/len(value)) for v in value]+[(0., 1-r['preseason_p'])])
            for alpha, name in [(.1, 'q10'), (.5, 'q50'), (.9, 'q90')]:
                mass = 0.; answer = None
                for v, w in pairs:
                    mass += w
                    if mass >= alpha:
                        answer = v; break
                assert answer is not None and np.isclose(answer, r[arm+'_'+name], atol=1e-12, rtol=0)
                quantiles_verified += 1
            exact_draws_verified += len(draw)
        case['baseball_review'] = text; case['player_walkthrough_status'] = 'complete'
    e.write(e.OUT/'reviewed-cases.json', cases)
    lines = ['# Player checks for integer hitting outcome ranges', '',
        'Historical forecasts use the documented season-end plus following preseason information',
        'date and predict the following calendar year. Every mean stays fixed. Offense is custom',
        'fixed-event batting plus replacement, not full WAR or six years of club control.', '',
        'The count distributions generate actual integer events. Their reference profile is a',
        'working distribution shape, not a player-specific K, BB or HR projection. The associated',
        'version links possible workload and hitting while preserving total expected offense.', '',
        'Case selection includes thirteen fixed player-origin cases, largest score gains and harms,',
        'false high and low mean forecasts, and an ordinary active result. Player judgments below',
        'are reviewed separately from the mechanical replay. Full input and saved-model traces are',
        '[in the evidence](../reports/model-evidence/hitter-event-count-risk/reviewed-cases.json).', '']
    for case in cases:
        r = case['origin']; parameters = case['count_parameters']
        lines += [f'## {r["player_name"]} after {r["origin_year"]}', '',
            'Selection: '+', '.join(case['selection'])+'.', '',
            '| Season | Level | PA | HR | Unintentional BB | K |',
            '| --- | --- | ---: | ---: | ---: | ---: |']
        for s in case['source_history']:
            lines.append(f'| {s["season"]} | {s["bucket"]} | {s["plate_appearances"]} | {s["home_runs"]} | {s["unintentional_walks"]} | {s["strike_outs"]} |')
        lines += ['', f'Current forecast: {r["preseason_p"]:.2%} chance of MLB PA, '
            f'{r["preseason_conditional_pa"]:.2f} PA conditional on appearing, '
            f'{r["preseason_pa"]:.2f} expected PA, {r["preseason_rate"]:+.3f} Hit/600 '
            f'and {r["preseason_value"]:+.3f} expected offense.', '',
            '| Distribution | P10 | Median | P90 |', '| --- | ---: | ---: | ---: |']
        for arm, label in [('fixed', 'Workload only'), ('normal', 'Prior Normal law'),
                           ('independent', 'Independent counts'), ('associated', 'Associated counts')]:
            lines.append(f'| {label} | {r[arm+"_q10"]:+.3f} | {r[arm+"_q50"]:+.3f} | {r[arm+"_q90"]:+.3f} |')
        actual_rate = f'{r["next_batting_rate"]:+.3f}' if r['next_pa'] > 0 else 'unobserved'
        lines += ['', f'Reality: {r["next_pa"]} MLB PA, {actual_rate} actual Hit/600 and '
            f'{r["next_value"]:+.3f} delivered offense.', '',
            f'The independent concentration is {parameters["independent"]["phi"]:.2f}. '
            f'The associated concentration is {parameters["associated"]["phi"]:.2f} and '
            f'slope {parameters["associated"]["beta"]:+.4f}, within the predeclared [-1,1] interval. '
            f'The positive-workload log center is {case["verified_draws"]["associated"]["workload_log_center"]:.4f}. '
            f'The refined calibration intersection contains {r["calibration_people"]} earlier people. '
            'Sparse or missing intersections borrow from the global calibration.', '',
            f'The prior Normal impossible-outcome probability is {r["normal_impossible_mass"]:.2%}; '
            'integer count support permits none. Each saved arm has 4,096 verified positive draws; '
            'non-arrival is retained as a separate exact mass at zero. Sample means are not recentered.', '']
        top = sorted(case['rate_contributions'].items(), key=lambda t: abs(t[1]), reverse=True)[:6]
        lines += [f'The saved rate intercept is {case["rate_intercept"]:+.3f}; largest signed '
            'input contributions are '+', '.join(f'{name} {v:+.3f}' for name, v in top)+
            '. All saved contributions together reproduce the unchanged point rate.', '',
            case['baseball_review'], '', 'Origin-selected comparisons: '+
            '; '.join(f'{p["player_name"]}: {p["next_pa"]} subsequent PA, {p["next_value"]:+.2f} offense' for p in case['peers'])+'.', '',
            'Comparison limit: '+case['peer_limit']+'.', '']
    lines += ['## Decision and remaining limits', '', reviewed['disposition'], '',
        'No protected 2026 outcomes are read. The frozen forecast and deployed explorer remain',
        'unchanged. This review does not certify public workload, elite readiness, defense,',
        'long-term control or the complete player-value system.', '']
    walk = e.ROOT/'docs/hitter-event-count-risk-walkthrough.md'
    walk.write_text('\n'.join(lines), encoding='utf8', newline='\n')
    python = str(e.ROOT/'.venv/Scripts/python.exe')
    test = subprocess.run([python, '-X', 'utf8', '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
        'tests/test_hitter_event_count_risk.py', 'tests/test_hitter_event_count_risk_review.py'],
        cwd=e.ROOT, text=True, capture_output=True)
    assert test.returncode == 0, test.stdout+test.stderr
    (e.OUT/'focused-tests.txt').write_text(test.stdout+test.stderr, encoding='utf8', newline='\n')
    freeze = json.loads(subprocess.check_output([python, '-X', 'utf8',
        str(e.ROOT/'scripts/verify_hitter_full_2026_freeze.py')], cwd=e.ROOT))
    assert freeze['status'] == 'verified' and freeze['protected_2026_opened'] is False
    q = pl.read_parquet(e.WORK/'scored-predictions.parquet').sort('row_id')
    base = pl.read_parquet(e.old.current.OUT/'scored-predictions.parquet').sort('row_id')
    assert q.select(base.columns).equals(base)
    for arm in ['independent', 'associated']:
        assert np.allclose(q[arm+'_expected_value'], q['preseason_value'], atol=1e-10, rtol=0)
    files = ['preflight.json', 'fit-report.json', 'outer-support.parquet', 'calibration-profile-support.parquet',
        'preparation-verification.json', 'preparation-tests.txt', 'scores.json', 'intervals.json', 'case-selection.json',
        'scoring-verification.json', 'monte-carlo-audit.json', 'limits.json', 'cases.json', 'case-replay-verification.json',
        'reviewed-cases.json', 'focused-tests.txt']
    paths = [e.OUT/name for name in files]+[Path(__file__), walk, e.ROOT/'config/hitter_event_count_risk_review.json']
    output_hashes = {}
    for cell in e.read(e.OUT/'fit-report.json')['cells']:
        e.old.check_hashes(cell['output_hashes']); output_hashes.update(cell['output_hashes'])
    for case in cases: output_hashes.update(case['draw_artifact_hashes'])
    for name in ['predictions.parquet', 'scored-predictions.parquet', 'monte-carlo-audit.parquet']:
        output_hashes[str(e.WORK/name)] = sha256_file(e.WORK/name)
    e.write(e.OUT/'final-report.json', dict(player_walkthrough_status='complete', reviewed_cases=len(cases),
        actual_independent_quantile_checks=quantiles_verified, integer_draws_independently_verified=exact_draws_verified,
        calibration_replays=70, all_row_count_assertions_during_fit=True,
        all_row_distribution_replay=False, numerical_ranking_stable=limits['numerical_ranking_stable'],
        selected_research_law=reviewed['selected_law'], disposition=reviewed['disposition'],
        current_means_unchanged=True, deployed_forecast_changed=False, protected_outcomes_used=False,
        goal_complete=False, frozen_verification=freeze,
        evidence_hashes={str(p): sha256_file(p) for p in paths}, local_output_hashes=output_hashes))
    evidence = e.ROOT/'reports/model-evidence/hitter-event-count-risk'; evidence.mkdir(parents=True, exist_ok=True)
    for name in files+['final-report.json']:
        target = evidence/name
        if target.exists():
            assert sha256_file(target) == sha256_file(e.OUT/name), ('Never overwrite changed prior evidence', name)
        else:
            shutil.copyfile(e.OUT/name, target)
        assert sha256_file(target) == sha256_file(e.OUT/name)
    print('Completed player review:', len(cases), 'cases;', quantiles_verified, 'independent quantile checks', flush=True)


if __name__ == '__main__':
    main()
