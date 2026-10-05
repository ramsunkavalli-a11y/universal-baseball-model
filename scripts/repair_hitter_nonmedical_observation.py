"""Reconstruct observation evidence without replacing legal records or forecasts."""
from collections import Counter, defaultdict
from datetime import date
import json
from pathlib import Path
import sys
from urllib.parse import parse_qs, urlparse

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from universal_baseball.nonmedical_observation import continuing_absence
from universal_baseball.storage import sha256_file

GEN = ROOT / 'reports/generated'
OUT = GEN / 'hitter-nonmedical-observation'
WIN = GEN / 'practical-hitter-late-role-v46'
OLD = GEN / 'hitter-status-evidence-v2'
JOB = GEN / 'hitter-employment-comparison-v2'
FIXED = [(665487, 2022), (665487, 2023), (665487, 2024), (518735, 2016),
         (408314, 2017), (677551, 2023), (680776, 2024), (672779, 2024), (434563, 2017)]


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def save(name, payload):
    (OUT / name).write_text(json.dumps(payload, indent=2, default=str, allow_nan=False) + '\n',
                           encoding='utf8', newline='\n')


def verified_windows(manifest):
    """Rebuild positive-only evidence from archived raw all-MLB requests."""
    byperson = defaultdict(list)
    expected = pl.read_parquet(WIN / 'windows.parquet')
    lut = {(r['player_id'], r['season']): r for r in expected.to_dicts()}
    checks = 0
    for capture in manifest['sources']:
        y, label = capture['season'], capture['window']
        path = Path(capture['path'])
        assert sha256_file(path) == capture['sha256']
        request = read(path.with_name(path.stem + '-request.json'))
        assert request['sha256'] == capture['sha256'] and request['url'] == capture['url']
        query = parse_qs(urlparse(capture['url']).query)
        assert query['stats'] == ['byDateRange'] and query['group'] == ['hitting']
        assert query['sportIds'] == ['1'] and query['gameType'] == ['R']
        assert date.fromisoformat(capture['start']).strftime('%m/%d/%Y') == query['startDate'][0]
        assert date.fromisoformat(capture['end']).strftime('%m/%d/%Y') == query['endDate'][0]
        payload = read(path)
        assert len(payload['stats']) == 1
        block = payload['stats'][0]
        assert block['type']['displayName'] == 'byDateRange' and block['group']['displayName'] == 'hitting'
        assert len(block['splits']) == capture['rows'] < int(query['limit'][0])
        seen = set()
        for split in block['splits']:
            assert split['season'] == str(y) and split['sport']['id'] == 1
            pid = split['player']['id']
            assert pid not in seen
            seen.add(pid)
            pa = split['stat']['plateAppearances']
            assert pa >= 0 and int(pa) == pa
            assert lut[pid, y][label + '_pa'] == pa
            checks += 1
            if pa > 0:
                byperson[pid].append(dict(player_id=pid, season=y, label=label,
                    start=capture['start'], end=capture['end'], available_date=capture['end'],
                    pa=pa, source_path=str(path.relative_to(ROOT)), source_sha256=capture['sha256']))
        for (pid, season), row in lut.items():
            if season == y and pid not in seen:
                assert row[label + '_pa'] == 0
                checks += 1
    return byperson, checks


def main():
    if OUT.exists():
        raise ValueError('Preserve existing execution; inspect or use a recovery contract')
    population_path = GEN / 'hitter-preseason-population-source/population.parquet'
    manifest = read(WIN / 'source-manifest.json')
    assert manifest['years'] == list(range(2010, 2025)) and len(manifest['sources']) == 45
    prior_final = read(GEN / 'hitter-availability-inventory/final-review.json')
    assert prior_final['player_walkthrough_status'] == 'complete'
    for name, digest in prior_final['hashes'].items():
        assert sha256_file(ROOT / name) == digest
    paths = [Path(__file__), ROOT / 'src/universal_baseball/nonmedical_observation.py',
        ROOT / 'tests/test_nonmedical_observation.py', ROOT / 'docs/hitter-nonmedical-observation-contract.md',
        population_path, OLD / 'status-ledger.json', OLD / 'source-seal.json',
        WIN / 'source-manifest.json', WIN / 'windows.parquet', JOB / 'features-0.parquet',
        JOB / 'predictions.parquet', GEN / 'practical-hitter-v31/counts.parquet',
        GEN / 'hitter-availability-inventory/player-walks.json',
        GEN / 'hitter-availability-inventory/warnings.json',
        GEN / 'hitter-availability-inventory/final-review.json']
    for capture in manifest['sources']:
        path = Path(capture['path'])
        paths.extend([path, path.with_name(path.stem + '-request.json')])
    old_hashes = read(OLD / 'source-seal.json')['source_hashes']
    assert sha256_file(population_path) == old_hashes[str(population_path.relative_to(ROOT))]
    OUT.mkdir()
    before = {str(p.relative_to(ROOT)): sha256_file(p) for p in paths}
    save('source-seal.json', dict(before_reconstruction=True, hashes=before,
        population_rows=83300, new_fits=0, completed_2026_evaluation_unchanged=True))
    windows, checks = verified_windows(manifest)
    population = pl.read_parquet(population_path)
    ledger = {r['candidate_key']: r for r in read(OLD / 'status-ledger.json')['rows']}
    assert population.height == len(ledger) == 83300
    q = pl.read_parquet(JOB / 'predictions.parquet')
    saved = {(r['player_id'], r['origin_year']): r for r in q.to_dicts()}
    features = pl.read_parquet(JOB / 'features-0.parquet', columns=['row_id', 'origin_year',
        'player_id', 'age', 'pa_0', 'snapshot_level', 'ctx_information_date'])
    inputs = {(r['player_id'], r['origin_year']): r for r in features.to_dicts()}
    rows, details = [], {}
    pops = {r['candidate_key']: r for r in population.to_dicts()}
    for p in population.to_dicts():
        key, pid = p['candidate_key'], p['player_id']
        old = ledger[key]
        assert old['information_date'] == p['information_date']
        evidence = continuing_absence(pid, old['absence'], windows.get(pid, []),
                                      p['information_date'], manifest['years'])
        r = dict(candidate_key=key, player_id=pid, origin_year=p['origin_year'],
            information_date=p['information_date'],
            captured_legal_state=evidence['captured_legal_state'],
            observed_after_channel_names=sorted(evidence['channels_with_subsequent_observed_MLB_use']),
            observation_unresolved_channel_names=sorted(evidence['observation_unresolved_channels']),
            hard_status_activity_conflict=bool(evidence['hard_status_activity_conflicts']),
            observation_finite_nonmedical=evidence['observation_finite_nonmedical'],
            observation_unresolved_nonmedical=evidence['observation_unresolved_nonmedical'],
            hard_unavailable=evidence['hard_unavailable'],
            unresolved_original_duration_games=evidence['unresolved_original_duration_games'],
            unresolved_known_calendar_end=evidence['unresolved_known_calendar_end'],
            current_return_date=evidence['current_return_date'],
            legal_reinstatement_certified=False, medical_recovery_certified=False,
            absence_continuity_certified=False)
        rows.append(r)
        if old['absence']['active_restrictions']:
            details[key] = evidence
    frame = pl.DataFrame(rows, schema_overrides={'unresolved_original_duration_games': pl.Int64,
        'unresolved_known_calendar_end': pl.String, 'current_return_date': pl.String}, infer_schema_length=None)
    assert frame.height == frame['candidate_key'].n_unique() == 83300
    frame.write_parquet(OUT / 'observations.parquet')
    changed = frame.filter(pl.col('observed_after_channel_names').list.len() > 0)
    save('active-origin-evidence.json', dict(origins=details))
    annual_warning_keys = {f'{r["origin_year"]}:{r["player_id"]}' for r in
        read(GEN / 'hitter-availability-inventory/warnings.json')['warnings']}
    changed_keys = set(changed['candidate_key'])
    additional = sorted(changed_keys - annual_warning_keys,
                        key=lambda k: (pops[k]['origin_year'], pops[k]['player_id']))
    selected = list(FIXED)
    if additional:
        p = pops[additional[0]]
        selected.append((p['player_id'], p['origin_year']))
    unresolved_minor = sorted([k for k, e in details.items() if e['observation_unresolved_channels']
        and not e['hard_unavailable'] and (pops[k]['player_id'], pops[k]['origin_year']) in inputs
        and inputs[pops[k]['player_id'], pops[k]['origin_year']]['pa_0'] == 0
        and inputs[pops[k]['player_id'], pops[k]['origin_year']]['snapshot_level'] in
            {'AAA', 'AA', 'HIGH_A', 'SINGLE_A', 'A-', 'ROOKIE_COMPLEX'}],
        key=lambda k: (pops[k]['origin_year'], pops[k]['player_id']))
    if unresolved_minor:
        p = pops[unresolved_minor[0]]
        selected.append((p['player_id'], p['origin_year']))
    selected = list(dict.fromkeys(selected))
    counts = pl.read_parquet(GEN / 'practical-hitter-v31/counts.parquet')
    old_cases = {(c['origin']['player_id'], c['origin']['origin_year']): c for c in
        read(GEN / 'hitter-availability-inventory/player-walks.json')['cases']}
    cases = []
    for pid, y in selected:
        key = f'{y}:{pid}'
        p = pops[key]
        e = details[key] if key in details else continuing_absence(pid,
            ledger[key]['absence'], windows.get(pid, []), p['information_date'], manifest['years'])
        source_input = inputs.get((pid, y))
        peers = []
        if source_input is not None:
            channels = set(ledger[key]['absence']['active_restrictions'])
            possible = [v for (other, year), v in inputs.items() if year == y and other != pid
                and set(ledger[f'{year}:{other}']['absence']['active_restrictions']) == channels]
            possible.sort(key=lambda v: (((v['age'] - source_input['age']) / 3) ** 2 +
                ((v['pa_0'] - source_input['pa_0']) / 200) ** 2, v['player_id']))
            for v in possible[:3]:
                pk = f'{y}:{v["player_id"]}'
                peers.append(dict(origin_input=v, population=pops[pk],
                    source_observation=details.get(pk), unchanged_forecast=saved.get((v['player_id'], y))))
        cutoff = date.fromisoformat(p['information_date'])
        prior = old_cases.get((pid, y))
        cases.append(dict(player_id=pid, origin_year=y, name=p['player_name'], population=p,
            actual_origin_inputs=source_input, captured_legal_absence=ledger[key]['absence'],
            new_observation=e, appearance_windows=[w for w in windows.get(pid, [])
                if date.fromisoformat(w['end']) <= cutoff],
            origin_known_counts=counts.filter((pl.col('player_id') == pid) &
                pl.col('season').is_between(y - 2, y)).sort('season', 'bucket').to_dicts(),
            unchanged_forecast=saved.get((pid, y)), prior_inventory_trace=prior,
            origin_known_peer_rule='Same origin and captured channel set; nearest age/3 and MLB PA/200; no outcomes used',
            peers=peers, new_forecast=None))
    save('player-walks.json', dict(cases=cases, additional_source_case=additional[:1],
        unresolved_minor_case=unresolved_minor[:1], player_walkthrough_status='pending'))
    source_keyset = set(features.select(pl.concat_str(pl.col('origin_year'), pl.lit(':'),
                                                     pl.col('player_id')).alias('key'))['key'])
    eval_keyset = {f'{r["origin_year"]}:{r["player_id"]}' for r in q.to_dicts()}
    affected = changed_keys & source_keyset
    evaluated = changed_keys & eval_keyset
    summary = dict(population_rows=83300, captured_active_origins=len(details),
        captured_active_people=len({pops[k]['player_id'] for k in details}),
        observation_changed_population_origins=len(changed_keys),
        observation_changed_population_people=changed['player_id'].n_unique(),
        observation_changed_model_source_origins=len(affected),
        observation_changed_evaluated_origins=len(evaluated),
        observation_changed_evaluated_people=len({pops[k]['player_id'] for k in evaluated}),
        conservative_annual_warnings_covered=len(annual_warning_keys & changed_keys),
        additional_population_origins=len(additional),
        hard_status_activity_conflicts=frame['hard_status_activity_conflict'].sum(),
        changed_legal_states=dict(Counter(ledger[k]['absence']['state'] for k in changed_keys)),
        raw_window_PA_checks=checks, raw_captures_verified=45,
        player_cases=len(cases), distinct_case_people=len({pid for pid, _ in selected}),
        source_repair_only=True, new_fits=0, forecasts_changed=False,
        legal_history_changed=False, medical_or_employment_evidence_changed=False,
        predictive_improvement_tested=False, player_walkthrough_status='pending')
    save('summary.json', summary)
    for name, digest in before.items():
        assert sha256_file(ROOT / name) == digest
    save('preparation-receipt.json', dict(status='source_built_review_pending', hashes=before,
        output_hashes={str((OUT / name).relative_to(ROOT)): sha256_file(OUT / name) for name in
            ['source-seal.json', 'observations.parquet', 'active-origin-evidence.json', 'player-walks.json', 'summary.json']}))
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
