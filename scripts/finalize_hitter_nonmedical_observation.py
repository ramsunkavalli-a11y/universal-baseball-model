"""Independently verify source repair and lock the performed player review."""
from collections import defaultdict
from datetime import date
import json
from pathlib import Path
import subprocess
import sys

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from universal_baseball.storage import sha256_file

GEN = ROOT / 'reports/generated'
OUT = GEN / 'hitter-nonmedical-observation'
PUBLIC = ROOT / 'reports/model-evidence/hitter-nonmedical-observation/report.json'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def verify(hashes):
    for path, digest in hashes.items():
        assert sha256_file(ROOT / path) == digest, path


def main():
    if (OUT / 'final-review.json').exists() or PUBLIC.exists():
        raise ValueError('Preserve completed source review')
    receipt = read(OUT / 'preparation-receipt.json')
    verify(receipt['hashes'])
    verify(receipt['output_hashes'])
    ledger = {r['candidate_key']: r for r in read(GEN / 'hitter-status-evidence-v2/status-ledger.json')['rows']}
    p = pl.read_parquet(GEN / 'hitter-preseason-population-source/population.parquet')
    frame = pl.read_parquet(OUT / 'observations.parquet')
    detail = read(OUT / 'active-origin-evidence.json')['origins']
    assert frame.select('candidate_key', 'player_id', 'origin_year', 'information_date').equals(
        p.select('candidate_key', 'player_id', 'origin_year', 'information_date'))
    manifest = read(GEN / 'practical-hitter-late-role-v46/source-manifest.json')
    raw = defaultdict(list)
    for capture in manifest['sources']:
        path = Path(capture['path'])
        assert sha256_file(path) == capture['sha256']
        for s in read(path)['stats'][0]['splits']:
            if s['stat']['plateAppearances'] > 0:
                raw[s['player']['id']].append(dict(player_id=s['player']['id'], season=capture['season'],
                    label=capture['window'], start=capture['start'], end=capture['end'],
                    available_date=capture['end'], pa=s['stat']['plateAppearances'],
                    source_path=str(path.relative_to(ROOT)), source_sha256=capture['sha256']))
    observed_keys, observed_people, active_keys = set(), set(), set()
    checks = 0
    for r in frame.to_dicts():
        key, cutoff = r['candidate_key'], date.fromisoformat(r['information_date'])
        a = ledger[key]['absence']
        active = a['active_restrictions']
        resolved, conflicts = {}, {}
        for channel, v in active.items():
            possible = [w for w in raw[r['player_id']] if date.fromisoformat(w['end']) <= cutoff
                        and date.fromisoformat(w['start']) > date.fromisoformat(v['event_date'])]
            if possible:
                first = sorted(possible, key=lambda w: (w['end'],
                    (date.fromisoformat(w['end']) - date.fromisoformat(w['start'])).days, w['label']))[0]
                target = conflicts if v['kind'] in {'permanent_ineligible', 'deceased'} else resolved
                target[channel] = dict(restriction=v, window=first, observed_return_upper=first['end'],
                    exact_return_date_known=False, legal_reinstatement_certified=False,
                    medical_recovery_certified=False)
        unresolved = {k: v for k, v in active.items() if k not in resolved}
        games = [v['duration_games'] for v in unresolved.values() if v.get('duration_games')]
        ends = [v['calendar_end'] for v in unresolved.values() if v.get('calendar_end')]
        assert r['captured_legal_state'] == a['state']
        assert r['hard_unavailable'] == a['hard_unavailable']
        assert r['observed_after_channel_names'] == sorted(resolved)
        assert r['observation_unresolved_channel_names'] == sorted(unresolved)
        assert r['hard_status_activity_conflict'] == bool(conflicts)
        assert r['observation_finite_nonmedical'] == bool(games or ends)
        assert r['observation_unresolved_nonmedical'] == any(v.get('ambiguous') or v['kind'] in
            {'restricted', 'administrative_leave', 'ineligible_unspecified'} or
            v['kind'] == 'suspended_unspecified' and not v.get('duration_games') for v in unresolved.values())
        assert r['unresolved_original_duration_games'] == (games[0] if len(games) == 1 else None)
        assert r['unresolved_known_calendar_end'] == (max(ends) if ends else None)
        report = a.get('return_report') if 'suspended' in unresolved else None
        assert r['current_return_date'] == (a.get('reported_return_date') if report else None)
        assert not r['legal_reinstatement_certified'] and not r['medical_recovery_certified']
        assert not r['absence_continuity_certified']
        checks += 13
        if active:
            active_keys.add(key)
            e = detail[key]
            assert e['captured_active_restrictions'] == active
            assert e['observation_unresolved_channels'] == unresolved
            assert e['channels_with_subsequent_observed_MLB_use'] == resolved
            assert e['hard_status_activity_conflicts'] == conflicts
            assert e['unresolved_return_report'] == report
            checks += 5
        if resolved:
            observed_keys.add(key)
            observed_people.add(r['player_id'])
    assert active_keys == set(detail)
    assert len(active_keys) == 485 and len(observed_keys) == 155 and len(observed_people) == 38
    q = pl.read_parquet(GEN / 'hitter-employment-comparison-v2/predictions.parquet')
    saved = {(r['player_id'], r['origin_year']): r for r in q.to_dicts()}
    evaluated = {f'{y}:{pid}' for pid, y in saved} & observed_keys
    features = pl.read_parquet(GEN / 'hitter-employment-comparison-v2/features-0.parquet',
                               columns=['player_id', 'origin_year'])
    modeled = {f'{r["origin_year"]}:{r["player_id"]}' for r in features.to_dicts()} & observed_keys
    assert len(modeled) == 122 and len(evaluated) == 89
    assert len({ledger[k]['player_id'] for k in evaluated}) == 28
    warnings = read(GEN / 'hitter-availability-inventory/warnings.json')['warnings']
    assert {f'{r["origin_year"]}:{r["player_id"]}' for r in warnings} <= observed_keys
    cases = read(OUT / 'player-walks.json')['cases']
    assert len(cases) == 11 and len({c['player_id'] for c in cases}) == 9
    for c in cases:
        key = f'{c["origin_year"]}:{c["player_id"]}'
        assert c['captured_legal_absence'] == ledger[key]['absence']
        if key in detail:
            assert c['new_observation'] == detail[key]
        assert c['unchanged_forecast'] == saved.get((c['player_id'], c['origin_year']))
        assert c['new_forecast'] is None
        if c['prior_inventory_trace']:
            assert c['prior_inventory_trace']['source_status_replayed']
            assert c['prior_inventory_trace']['forecast_unchanged']
        for peer in c['peers']:
            assert peer['unchanged_forecast'] == saved.get((peer['population']['player_id'], c['origin_year']))
    test_receipts = []
    commands = [[sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
        'tests/test_nonmedical_observation.py', 'tests/test_availability_inventory.py'],
        [sys.executable, 'scripts/verify_hitter_selected_2026_freeze.py'],
        [sys.executable, 'scripts/verify_hitter_full_2026_freeze.py']]
    for command in commands:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if result.returncode:
            raise ValueError(result.stdout + result.stderr)
        test_receipts.append(dict(command=command[1:], exit_code=0, output=result.stdout))
    verify(receipt['hashes'])
    verify(receipt['output_hashes'])
    paths = [Path(__file__), ROOT / 'docs/hitter-nonmedical-observation-result.md',
        ROOT / 'docs/hitter-nonmedical-observation-player-review.md', OUT / 'preparation-receipt.json',
        OUT / 'source-seal.json', OUT / 'observations.parquet', OUT / 'active-origin-evidence.json',
        OUT / 'player-walks.json', OUT / 'summary.json']
    final = dict(status='source_repair_review_complete_not_prediction_validation',
        player_walkthrough_status='complete', source_rows=83300, active_origins=485,
        changed_population_origins=155, changed_population_people=38,
        changed_model_source_origins=122, changed_evaluated_origins=89, changed_evaluated_people=28,
        independent_source_field_checks=checks, raw_window_PA_checks=49542,
        player_cases=11, distinct_case_people=9, saved_heads_previously_replayed=18,
        new_fits=0, forecasts_changed=False, legal_history_changed=False,
        legal_reinstatement_or_medical_recovery_certified=False,
        predictive_improvement_tested=False, deployment_approved=False,
        completed_2026_evaluation_unchanged=True, tests_and_freezes=test_receipts,
        hashes={str(path.relative_to(ROOT)): sha256_file(path) for path in paths},
        next_action='Predeclare one coherent matched historical opportunity comparison with fixed hitting and corrected observation/timing semantics')
    payload = json.dumps(final, indent=2) + '\n'
    (OUT / 'final-review.json').write_text(payload, encoding='utf8', newline='\n')
    PUBLIC.parent.mkdir(parents=True, exist_ok=True)
    PUBLIC.write_text(payload, encoding='utf8', newline='\n')
    print(json.dumps({k: v for k, v in final.items() if k not in {'hashes', 'tests_and_freezes'}}), flush=True)


if __name__ == '__main__':
    main()
