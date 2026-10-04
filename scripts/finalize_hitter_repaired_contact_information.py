"""Complete actual walks and independently recompute scores before disposition."""
import json
import shutil
import subprocess
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.storage import sha256_file
import evaluate_hitter_repaired_contact_information as e


def same(expected, actual):
    for key, value in expected.items():
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            assert np.isclose(value, actual[key], atol=1e-10, rtol=0), (key, value, actual[key])
        elif value is None:
            assert actual[key] is None


def main():
    assert not (e.OUT / 'report.json').exists(), 'Preserve completed review'
    pre = e.read(e.OUT / 'preflight.json'); e.verify_inputs(pre)
    notes_path = e.ROOT / 'config/hitter_repaired_contact_information_review.json'
    notes = e.read(notes_path)
    case_files = [e.OUT / 'cases.json', e.OUT / 'sensitivity-cases.json']
    cases = []
    for p in case_files:
        artifact = e.read(p)
        for src, h in artifact['input_hashes'].items(): assert sha256_file(e.Path(src)) == h, src
        cases += artifact['cases']
    assert len(cases) == 19 and len({c['row_id'] for c in cases}) == 19
    assert {str(c['row_id']) for c in cases} == set(notes) - {'review_limits'}
    assert all(len(notes[str(c['row_id'])]) > 200 for c in cases)
    verification = e.read(e.OUT / 'verification.json')
    assert sha256_file(e.Path(verification['scored_path'])) == verification['scored_sha256']
    q = pl.read_parquet(verification['scored_path'])
    sources = dict(e.scope(q)); scores = e.read(e.OUT / 'scores.json'); intervals = e.read(e.OUT / 'intervals.json')
    with threadpool_limits(limits=2):
        for s in scores:
            g = sources[s['scope']]
            assert len(g) == s['rows'] and int((g['next_pa'] > 0).sum()) == s['active_rows']
            assert np.isclose(g['next_value'].sum(), s['actual_value'], atol=1e-10, rtol=0)
            rel = g.drop('next_batting_rate').rename({'next_relative_rate': 'next_batting_rate'})
            for a, expected in s['scores'].items(): same(expected, e.score(g, a))
            for a, expected in s['rate'].items(): same(expected, e.rate_score(rel, a + '_rate'))
            for a, expected in s['rate_equal_player'].items(): same(expected, e.rate_score(rel, a + '_rate', False))
            for a, expected in s['common_origin_rate_sensitivity'].items(): same(expected, e.rate_score(g, a + '_rate'))
        for expected in intervals:
            g = sources[expected['scope']]
            if expected['metric'] == 'value_mse':
                actual = e.paired(g, expected['candidate'], expected['benchmark'])
            else:
                rel = g.drop('next_batting_rate').rename({'next_relative_rate': 'next_batting_rate'})
                actual = e.rate_interval(rel, expected['arm'], expected['reference'])
            same(expected, actual)
        for c in cases:
            assert c['actual']['rate'] is None or c['actual']['pa'] > 0
            for t in c['linear_traces'].values():
                total = t['intercept'] + sum(v['effect'] for v in t['effects'])
                assert np.isclose(total, t['raw_prediction'], atol=1e-10, rtol=0)
                assert np.isclose(total - t['block_contributions']['detail'], t['neutral_detail_probe'], atol=1e-10, rtol=0)
            r = q.filter(pl.col('row_id') == c['row_id']).row(0, named=True)
            assert r['player_id'] == c['player_id'] and r['origin_year'] == c['origin_year']
            assert all(np.isclose(r[a + '_' + field], value, atol=1e-10, rtol=0)
                       for a, values in c['forecasts'].items() for field, value in values.items())
    text = ['# Player review of repaired contact information', '',
        'All nineteen selected cases remain. Rates are fixed-event batting wins per 600 PA relative to future MLB average; actual rates are unobserved for non-arrivals. Delivered value uses the separate common-origin batting plus replacement reference, not full WAR. Playing time does not change. The added contact measurements are minor-only and not park-neutral.', '',
        notes['review_limits'], '']
    for c in cases:
        text += [f"## {c['player_name']} before {c['target_year']}", '',
                 f"Selection: {', '.join(c['selection'])}. Age {c['age']:.0f}; {c['stage']}; information date {c['information_date']}.", '',
                 'Known production is shown as PA / strikeouts / unintentional walks / HR. Source years and level identities are kept separate.', '']
        text += [f"- {s['season']} {s['bucket']}: {s['plate_appearances']} / {s['strike_outs']} / {s['unintentional_walks']} / {s['home_runs']}." for s in c['source_history']]
        text += ['', 'Measured physical contacts / classified contacts / narrative HR:', '']
        text += [f"- {s['season']} {s['bucket']}, actual league {s['league_id']}: {s['physical_contacts']} / {s['classified_contacts']} / {s['raw_narrative_hr']}." for s in c['contact_history']]
        if not c['contact_history']: text += ['- No own minor contact in the window.']
        text += ['', '| Forecast | Hitting rate | Expected PA | Delivered offense |', '| --- | ---: | ---: | ---: |']
        for a, label in [('preseason', 'Current count model'), ('translated_ridge', 'Translated anchor'),
                         ('coverage', 'Coverage control'), ('mix', 'Contact mix'), ('joint', 'Joint contact detail'),
                         ('joint_all', 'All-player sensitivity')]:
            v = c['forecasts'][a]
            text += [f"| {label} | {v['rate']:+.3f} | {v['pa']:.1f} | {v['value']:+.3f} |"]
        actual = c['actual']; rate = 'Unobserved' if actual['rate'] is None else f"{actual['rate']:+.3f}"
        text += [f"| Actual | {rate} | {actual['pa']} | {actual['value']:+.3f} |", '',
                 f"Unchanged appearance probability {c['arrival_probability']:.4f}; conditional PA {c['conditional_pa']:.1f}. Broad/refined active support: " +
                 '/'.join(str(s['active_profile_people']) for s in c['active_profile_support']) + ' distinct people.', '', notes[str(c['row_id'])], '']
        if c['linear_traces']:
            t = c['linear_traces']['joint']; b = t['block_contributions']
            text += [f"Exact joint fitted sum: intercept {t['intercept']:+.3f}; coverage {b['coverage']:+.3f}, mix {b['mix']:+.3f}, detail {b['detail']:+.3f}, with original-input terms completing raw hitting {t['raw_prediction']:+.3f}. Neutral detail at the same exposure gives {t['neutral_detail_probe']:+.3f}. This potentially artificial within-fit probe is mechanics, not an independently validated forecast. All actual inputs, scales and coefficients are saved.", '']
        text += ['Origin-selected peers and following-year MLB PA: ' + ', '.join(f"{p['player_name']} {p['next_pa']}" for p in c['peers']['cases']) + '.', '']
    doc = e.ROOT / 'docs/hitter-repaired-contact-information-walkthrough.md'
    assert not doc.exists(); doc.write_text('\n'.join(text) + '\n', encoding='utf8')
    e.write('reviewed-cases.json', dict(player_walkthrough_status='complete', cases=[dict(c, judgment=notes[str(c['row_id'])]) for c in cases],
            review_limits=notes['review_limits'], scoring_recomputed=True, no_refits_or_tuning=True))
    freeze = json.loads(subprocess.check_output([str(e.ROOT / '.venv/Scripts/python.exe'), '-X', 'utf8',
                        str(e.ROOT / 'scripts/verify_hitter_full_2026_freeze.py')], cwd=e.ROOT))
    assert freeze['status'] == 'verified' and freeze['protected_2026_opened'] is False
    fits = [e.OUT / f"fit-{c['year']}-{c['fold']}.json" for c in pre['cells']]
    model_hashes = {h['path']: h['sha256'] for p in fits for h in e.read(p)['heads']}
    for p, h in model_hashes.items(): assert sha256_file(e.Path(p)) == h
    tests = subprocess.run([str(e.ROOT / '.venv/Scripts/python.exe'), '-X', 'utf8', '-m', 'pytest',
        'tests/test_hitter_repaired_contact_information.py', '-q', '-p', 'no:cacheprovider'], cwd=e.ROOT, capture_output=True, text=True)
    assert tests.returncode == 0, tests.stdout + tests.stderr
    report = dict(player_walkthrough_status='complete', cases=19, new_heads=len(model_hashes),
        actual_preflight_checks=210, original_anchor_replays=35, candidate_head_replays=verification['replayed_heads'],
        unsupported_2016_cells=verification['fallback_cells'], scores_recomputed=True, intervals_recomputed=True,
        mathematical_rate_violations=verification['mathematical_rate_violations'], focused_tests=11, test_output=tests.stdout,
        predictive_disposition='Do not replace translated anchor with raw contact; retain all-player sensitivity as qualified research, not adoption',
        negative_claim_limit='Does not reject park-neutral, opponent-adjusted or nonlinear contact models; no own MLB contact is supplied',
        opportunity_changed=False, deployed_explorer_changed=False, current_candidate_changed=False, goal_complete=False,
        full_population_support=False, protected_outcomes_used=False, freeze_verification=freeze,
        next_step='Finish candidate integration and uncertainty under the practical plan; contact adjustment extension requires outer-fold-clean source proof, not automatic promotion',
        input_hashes={str(p): sha256_file(p) for p in [notes_path, doc, e.Path(__file__),
            e.ROOT / 'scripts/review_hitter_repaired_contact_information.py',
            e.ROOT / 'scripts/review_hitter_repaired_contact_sensitivities.py', e.OUT / 'preflight.json',
            e.OUT / 'scores.json', e.OUT / 'intervals.json', e.OUT / 'verification.json', *case_files, e.OUT / 'reviewed-cases.json', *fits]},
        fitted_model_hashes=model_hashes)
    e.write('report.json', report)
    dest = e.ROOT / 'reports/model-evidence/hitter-repaired-contact-information'; dest.mkdir(parents=True, exist_ok=True)
    for name in ['preflight.json', 'scores.json', 'intervals.json', 'verification.json', 'cases.json', 'sensitivity-cases.json', 'reviewed-cases.json', 'report.json']:
        assert not (dest / name).exists(); shutil.copy2(e.OUT / name, dest / name)
        assert sha256_file(dest / name) == sha256_file(e.OUT / name)
    print(json.dumps({k: v for k, v in report.items() if k not in ['input_hashes', 'fitted_model_hashes']}, indent=2), flush=True)


if __name__ == '__main__': main()
