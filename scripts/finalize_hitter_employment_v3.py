"""Independent source/indicator accounting; no prediction or accuracy promotion."""
from pathlib import Path
import json
import re
import subprocess
import sys
import polars as pl
from audit_overseas_public_coverage import ROOT, GEN, read, verify
from universal_baseball.storage import sha256_file

OUT = GEN / 'hitter-employment-v3'
ROLE = GEN / 'overseas-role-sources'


def write_new(path, obj):
    if path.exists(): raise ValueError('Preserve completed source review')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n', encoding='utf8', newline='\n')


def main():
    if (OUT / 'final-review.json').exists(): raise ValueError('Review already completed')
    seals = [read(OUT / 'source-seal.json'), read(OUT / 'execution-recovery.json'),
             read(ROLE / 'source-seal.json')]
    for s in seals: verify(s['hashes'])
    old = {r['candidate_key']: r for r in read(GEN / 'hitter-status-evidence-v2/status-ledger.json')['rows']}
    pop = {r['candidate_key']: r for r in pl.read_parquet(
        GEN / 'hitter-preseason-population-source/population.parquet').to_dicts()}
    frame = pl.read_parquet(OUT / 'employment-indicators.parquet')
    rows = frame.to_dicts()
    delta_rows = read(OUT / 'employment-deltas.json')['rows']
    delta = {r['candidate_key']: r for r in delta_rows}
    assert len(rows) == len(old) == len(pop) == 83300
    assert len({r['candidate_key'] for r in rows}) == 83300
    assert {r['candidate_key'] for r in rows} == set(old) == set(pop)
    assert len(delta) == len(delta_rows) == 23172
    names = [c for c in frame.columns if c.startswith('status_')]
    assert len(names) == 9
    checks = 0
    context_checks = 0
    for r in rows:
        key = r['candidate_key']; previous = old[key]; p = pop[key]
        d = delta.get(key); e = d['employment'] if d else previous['employment']
        assert (r['player_id'], r['origin_year'], r['information_date']) == (
            previous['player_id'], previous['origin_year'], previous['information_date'])
        assert previous['target_year'] <= 2025
        listed = bool(p['returned_40man'])
        contradiction = bool(p['roster_cross_team_conflict'] or p['roster_status_conflict'] or e['same_date_conflict'])
        bad_positive = listed and e['state'] in ('reported_release', 'reported_retirement',
                                                'reserve_departure_organization_unconfirmed')
        oracle = {
            'status_major_link': (listed and not contradiction and not bad_positive) or
                                 (e['explicit_major_link'] and not contradiction),
            'status_minor_agreement': e['state'] == 'minor_agreement',
            'status_agreement_unspecified': e['state'] == 'agreement_unspecified',
            'status_acquisition_only': e['state'] == 'acquisition',
            'status_released': e['state'] == 'reported_release',
            'status_employment_unknown': e['state'] == 'unknown' and not listed,
            'status_employment_conflict': contradiction or bad_positive,
            'status_negative_listing_conflict': not listed and e['explicit_major_link'] and not contradiction,
            'status_positive_listing_conflict': bad_positive,
        }
        for n in names:
            assert r[n] == bool(oracle[n]), (key, n)
            checks += 1
        changes = {n: [previous[n], r[n]] for n in names if previous[n] != r[n]}
        assert changes == (d['changed_indicators'] if d else {})
        if d:
            assert previous['employment'] == d['old_employment']
            assert len(d['assignment_context']) == r['assignment_context_records']
            for c in d['assignment_context']:
                raw = c['raw']
                # Independent tokenization: reassigned/assigned cannot supply signed.
                tokens = re.findall(r'\w+', (raw.get('description') or '').lower())
                assert 'signed' not in tokens and raw.get('typeCode') != 'SFA'
                assert (raw.get('typeDesc') or '').lower() != 'signed as free agent'
                dates = [raw.get(n) for n in ('date', 'effectiveDate', 'resolutionDate') if raw.get(n)]
                assert max(dates) == c['known_date'] <= r['information_date']
                assert (raw.get('person') or {})['id'] == r['player_id']
                context_checks += 1
    numeric = [d for d in delta_rows if d['changed_indicators']]
    assert len(numeric) == 6941 and len({d['player_id'] for d in numeric}) == 3244
    walks = read(OUT / 'player-walks.json')['cases']
    assert len(walks) == len({r['row_id'] for r in walks}) == 59
    assert all(r['corrected_forecast'] is None and r['explanatory_inputs_only'] for r in walks)
    changed = [r for r in walks if r['old_job_evidence'] != r['corrected_job_evidence']]
    assert len(changed) == 1 and changed[0]['candidate_key'] == '2021:553988'
    assert changed[0]['corrected_job_evidence']['signed_first_team_work'] == 0
    ordinary = [delta['2016:400018'], delta['2017:430652']]
    assert all(r['employment']['state'] == 'minor_agreement' for r in ordinary)
    role = read(ROLE / 'ledger.json')['rows']
    reports = read(ROOT / 'config/hitter_overseas_role_source_review.json')['reports']
    role_checks = 0
    for r in role:
        expected = [v['report_id'] for v in reports if v['player_id'] == r['player_id']
                    and v['target_year'] == r['target_year'] and v['publication_day'] <= r['information_date']]
        assert expected == [v['report_id'] for v in r['reviewed_reports']['reports']]
        assert r['reviewed_reports']['role_coverage'] == ('observed_report' if any(
            v['reported_role'] for v in r['reviewed_reports']['reports']) else 'unknown')
        role_checks += 1
    assert sum(bool(r['reviewed_reports']['reports']) for r in role) == 8
    assert sum(r['reviewed_reports']['role_coverage'] == 'observed_report' for r in role) == 4
    commands = [[sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
                 'tests/test_hitter_employment_v3.py', 'tests/test_overseas_role_sources.py'],
                [sys.executable, 'scripts/verify_hitter_selected_2026_freeze.py'],
                [sys.executable, 'scripts/verify_hitter_full_2026_freeze.py']]
    outputs = []
    for command in commands:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if result.returncode: raise ValueError(result.stdout + result.stderr)
        outputs.append(dict(command=command[1:], exit_code=0, output=result.stdout))
    for s in seals: verify(s['hashes'])
    paths = [Path(__file__), ROOT / 'docs/hitter-overseas-role-source-result.md',
             OUT / 'employment-indicators.parquet', OUT / 'employment-deltas.json',
             OUT / 'player-walks.json', OUT / 'summary.json', ROLE / 'ledger.json', ROLE / 'player-walks.json']
    hashes = {str(p.relative_to(ROOT)): sha256_file(p) for p in paths}
    public = dict(source_origins=83300, employment_path_changed_origins=23172,
        numeric_indicator_changed_origins=6941, numeric_indicator_changed_people=3244,
        independent_indicator_checks=checks, assignment_context_checks=context_checks,
        independent_role_origin_checks=role_checks, retained_walks=59, ordinary_source_controls=2,
        official_report_origins=8, explicit_role_origins=4, new_fits=0, new_forecasts=0,
        source_review_status='complete', player_walkthrough_status='complete',
        predictive_improvement='not_tested', deployment_approved=False,
        completed_2026_evaluation_unchanged=True, tests_and_freezes=outputs, hashes=hashes)
    write_new(OUT / 'ordinary-source-walks.json', dict(
        selection='Stable player ID then earliest changed numeric origin in locked study; distinct people',
        cases=ordinary, new_forecasts=0))
    public['hashes'][str((OUT / 'ordinary-source-walks.json').relative_to(ROOT))] = sha256_file(OUT / 'ordinary-source-walks.json')
    write_new(OUT / 'final-review.json', public)
    write_new(ROLE / 'final-review.json', dict(source_review_status='complete', player_walkthrough_status='complete',
        pilot_not_population_complete=True, forecasting_approved=False, hashes=hashes))
    write_new(ROOT / 'reports/model-evidence/hitter-employment-v3/report.json', public)
    print(json.dumps({k: v for k, v in public.items() if k not in ('hashes', 'tests_and_freezes')}), flush=True)


if __name__ == '__main__': main()
