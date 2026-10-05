"""Append completion evidence without replacing sealed source/review receipts."""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/generated/international-hitter-source-2025'
RAW = ROOT / 'data/quarantine/international-hitter-source-2025'
PUBLIC = ROOT / 'reports/model-evidence/international-hitter-source-2025/report.json'
FIELDS = ('pa', 'ab', 'hits', 'doubles', 'triples', 'hr', 'bb', 'ibb', 'hbp', 'so', 'sh', 'sf')
DOCS = ('docs/hitter-international-source-2025-result.md',
        'docs/hitter-international-source-2025-player-review.md')
TESTS = ('tests/test_international_hitter_source_2025.py',
         'tests/test_npb_hitter_2025_layout.py', 'tests/test_kbo_english_annual_counts.py',
         'tests/test_npb_history.py', 'tests/test_npb_identity_overlay.py',
         'tests/test_kbo_history.py', 'tests/test_kbo_source_review.py',
         'tests/test_kbo_identity.py', 'tests/test_kbo_history_inputs.py',
         'tests/test_international_hitter_2025_completion.py')


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_hashes(mapping, root=ROOT):
    for raw_path, expected in mapping.items():
        path = Path(raw_path)
        if not path.is_absolute():
            path = root / path
        if digest(path) != expected:
            raise ValueError(f'Changed sealed input: {path}')


def exclusive_events(counts):
    events = dict(K=counts['so'], UBB=counts['bb'] - counts['ibb'], HBP=counts['hbp'],
                  **{'1B': counts['hits'] - counts['doubles'] - counts['triples'] - counts['hr'],
                     '2B': counts['doubles'], '3B': counts['triples'], 'HR': counts['hr']})
    events['other'] = counts['pa'] - sum(events.values())
    if any(v < 0 for v in events.values()):
        raise ValueError('Invalid exclusive event counts')
    return events


def verify_subtotal(annual, summary, last_year):
    eligible = [r for r in annual if 2023 <= r['season'] <= last_year]
    counts = {k: sum(r[k] for r in eligible) for k in FIELDS}
    events = exclusive_events(counts)
    if summary['origin'] != last_year or summary['counts'] != counts or summary['events'] != events:
        raise ValueError('Changed annual/subtotal calculation')
    if summary['selected_source_rows'] != len(eligible) or summary['mlb_translation_fitted']:
        raise ValueError('Invalid source-only subtotal')
    if summary['observed_positive_seasons'] != sorted({r['season'] for r in eligible if r['pa'] > 0}):
        raise ValueError('Invalid observed-season membership')
    if set(summary['event_rates']) != set(events):
        raise ValueError('Missing event rate')
    for event, value in events.items():
        observed = summary['event_rates'][event]
        if not counts['pa']:
            if observed is not None:
                raise ValueError('Unobserved rate represented as zero')
        elif observed is None or not math.isclose(observed, value / counts['pa'], rel_tol=0, abs_tol=1e-14):
            raise ValueError('Rate differs from actual counts')


def verify_case(case, selection, history, current):
    key = 'npb_id' if case['league'] == 'NPB' else 'kbo_id'
    for field in ('league', 'source_id', 'player_id', 'rule'):
        if case[field] != selection[field]:
            raise ValueError('Changed case selection')
    rows = [r for r in history + current if r[key] == case['source_id'] and 2023 <= r['season'] <= 2025]
    expected = sorted([{k: r[k] for k in ('season', *FIELDS)} for r in rows],
                      key=lambda r: (r['season'], *(r[k] for k in FIELDS)))
    actual = sorted([{k: r[k] for k in ('season', *FIELDS)} for r in case['annual_counts']],
                    key=lambda r: (r['season'], *(r[k] for k in FIELDS)))
    if actual != expected:
        raise ValueError('Walk does not reconstruct exact source-key history')
    verify_subtotal(actual, case['before_last_season'], 2024)
    verify_subtotal(actual, case['with_last_season'], 2025)
    if not case['future_mutation_invariance'] or case['new_projection'] is not None:
        raise ValueError('Source review cannot approve new forecasts')
    matches = [r for r in current if r[key] == case['source_id']]
    if len(matches) != 1 or matches[0] != case['source_2025']:
        raise ValueError('Changed current source record')


def command(args):
    result = subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return result.stdout


def save_new(path, value):
    if path.exists():
        raise ValueError(f'Completion output already exists; inspect, do not overwrite: {path}')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n',
                    encoding='utf8', newline='\n')


def main():
    if PUBLIC.exists() or (OUT / 'review-completion.json').exists():
        raise ValueError('Inspect completed receipts rather than rerunning finalization')
    names = ('npb-collection.json', 'kbo-collection.json', 'kbo-identity-collection.json',
             'independent-review.json', 'completed-walk-execution.json')
    receipts = {name: read(OUT / name) for name in names}
    for receipt in receipts.values():
        verify_hashes(receipt.get('source_hashes', {}))
        verify_hashes(receipt.get('hashes', {}))
    old_reviews = ('reports/generated/npb-hitting-history/review.json',
                   'reports/generated/kbo-hitting-history/review.json',
                   'reports/generated/kbo-identity-overlay/review.json')
    for name in old_reviews:
        verify_hashes(read(ROOT / name)['hashes'])
    # Include request bodies in verification, not just the rendered source bytes.
    capture_count = 0
    for meta_path in RAW.rglob('*.json'):
        if meta_path.name.endswith('.request.json'):
            continue
        meta = read(meta_path)
        if 'url' not in meta:
            continue
        html = Path(str(meta_path).removesuffix('.metadata.json')) if meta_path.name.endswith('.metadata.json') else meta_path.with_suffix('.html')
        if digest(html) != meta['sha256'] or meta['url'] != meta['returned_url']:
            raise ValueError('Changed or redirected raw source')
        if 'request_sha256' in meta:
            request_path = meta_path.with_name(meta_path.stem + '.request.json')
            payload = read(request_path) if meta['method'] == 'POST' else None
            request_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
            if request_hash != meta['request_sha256'] or meta['http_status'] != 200:
                raise ValueError('Changed request or failed source response')
        capture_count += 1
    current = {'NPB': pl.read_parquet(OUT / 'npb-2025.parquet'),
               'KBO': pl.read_parquet(OUT / 'kbo-2025-identities.parquet')}
    history = {'NPB': pl.read_parquet(ROOT / 'reports/generated/npb-hitting-history/reviewed-batting.parquet'),
               'KBO': pl.read_parquet(ROOT / 'reports/generated/kbo-identity-overlay/reviewed-batting.parquet')}
    selection = read(OUT / 'walk-selection.json')
    walks = read(OUT / 'player-walks.json')
    if len(walks['cases']) != 8 or len(selection['cases']) != 8 or selection['future_outcomes_used']:
        raise ValueError('Wrong source-review population')
    checked = 0
    narrative = (ROOT / DOCS[1]).read_text(encoding='utf8')
    for case, selected in zip(walks['cases'], selection['cases'], strict=True):
        verify_case(case, selected, history[case['league']].to_dicts(), current[case['league']].to_dicts())
        if case['source_id'] not in narrative:
            raise ValueError('Missing narrated source case')
        for check in case['english_count_checks']:
            checked += check.get('count_fields', check.get('english_origin_count_fields_checked', 0))
    if checked != 115 or receipts['independent-review.json']['raw_count_fields_reconstructed'] != 20541:
        raise ValueError('Incomplete source reconstruction')
    # Pytest may clear its basetemp. Allocate and validate a new empty directory
    # inside this output workspace, never the user's shared temporary tree.
    scratch = Path(tempfile.mkdtemp(prefix='completion-tests-', dir=OUT)).resolve()
    if scratch.parent != OUT.resolve() or any(scratch.iterdir()):
        raise ValueError('Unsafe test scratch directory')
    tests = command(['-m', 'pytest', '-q', '--basetemp', str(scratch), *TESTS])
    selected_freeze = json.loads(command(['scripts/verify_hitter_selected_2026_freeze.py']))
    legacy_freeze = json.loads(command(['scripts/verify_hitter_full_2026_freeze.py']))
    if selected_freeze['status'] != 'verified' or legacy_freeze['status'] != 'verified':
        raise ValueError('Changed forecast freeze')
    provenance = [OUT / n for n in (*names, 'walk-selection.json', 'player-walks.json')]
    provenance += [ROOT / n for n in (*old_reviews, *DOCS, *TESTS)] + [Path(__file__)]
    hashes = {p.relative_to(ROOT).as_posix(): digest(p) for p in provenance}
    aggregates = {}
    for league, frame in current.items():
        aggregates[league] = dict(source_rows=len(frame), pa=frame['pa'].sum(),
            zero_pa_rows=frame.filter(pl.col('pa') == 0).height,
            no_MLBAM_rows=frame.filter(pl.col('player_id').is_null()).height,
            positive_pa_no_MLBAM_rows=frame.filter(pl.col('player_id').is_null() & (pl.col('pa') > 0)).height)
    report = dict(status='qualified_2025_batting_source_complete',
        source_player_walkthrough_status='complete', cutoff='2025-12-31',
        source_season=2025, source_aggregates=aggregates,
        raw_count_fields_reconstructed=20541, english_count_fields_checked=checked,
        raw_captures_and_request_bodies_verified=capture_count,
        kbo_team_fields_reconciled=16, new_static_KBO_profiles=29,
        npb_unresolved_source_keys=1, kbo_residual_PA=1,
        selected_source_cases=[{k: c[k] for k in ('league', 'source_id', 'rule', 'player_id',
            'age_at_origin', 'annual_counts', 'before_last_season', 'with_last_season',
            'peers', 'future_mutation_invariance', 'new_projection', 'scope')} for c in walks['cases']],
        tests=tests, selected_freeze_verification=selected_freeze, legacy_freeze_verification=legacy_freeze,
        verifier_phase_flags_are_not_new_final_evaluation_claims=True,
        new_fits=0, forecast_changes=0, predictive_improvement_established=False,
        historical_roles_qualified=False, historical_park_exposure_qualified=False,
        all_source_MLBAM_crosswalk_qualified=False, deployment_approved=False,
        bulk_provider_rows_published=False, hashes=hashes,
        claim='Last overseas batting season available; no revised 2026 predictions or accuracy claim')
    save_new(PUBLIC, report)
    save_new(OUT / 'review-completion.json', dict(completed_utc=datetime.now(timezone.utc).isoformat(),
        source_player_walkthrough_status='complete', earlier_pending_receipts_preserved=True,
        supersedes_review_pending_fields_only=list(names), public_report_sha256=digest(PUBLIC),
        new_fits=0, forecast_changes=0, predictive_improvement_established=False, hashes=hashes))
    print(json.dumps(dict(status=report['status'], walks=8, captures=capture_count,
                         raw_count_fields=20541, english_count_fields=checked,
                         forecast_changes=0, tests=tests)))


if __name__ == '__main__':
    main()
