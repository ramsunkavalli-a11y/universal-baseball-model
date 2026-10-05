"""Inventory previous work and source contradictions without another model fit."""
import json
from datetime import date
from pathlib import Path
import sys

import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from universal_baseball.availability_inventory import old_restriction_with_later_mlb_use
from universal_baseball.hitter_status_evidence_v2 import absence_state
from universal_baseball import availability_context_v29b as clinical
from universal_baseball.histogram_prediction_trace import trace
from universal_baseball.storage import sha256_file
from evaluate_hitter_readiness_v49 import logit_trace
from run_hitter_employment_comparison import read, verify

GEN = ROOT / 'reports/generated'
EXPERIMENT = GEN / 'hitter-employment-comparison-v2'
OUT = GEN / 'hitter-availability-inventory'
CASES = [(665487, 2022), (665487, 2023), (665487, 2024), (518735, 2016),
         (408314, 2017), (677551, 2023), (680776, 2024), (672779, 2024), (434563, 2017)]
PRIOR = ['hitter-offseason-injury-feature-result.md', 'hitter-availability-gap-v1-result.md',
         'availability-context-v29-result.md', 'practical-hitter-opportunity-status-v59-result.md',
         'hitter-observed-return-v60-result.md', 'hitter-status-evidence-result.md',
         'hitter-status-player-review.md', 'hitter-evidence-representation-result.md',
         'hitter-employment-comparison-v2-result.md']


def save(name, payload):
    (OUT / name).write_text(json.dumps(payload, indent=2, default=str) + '\n', encoding='utf8', newline='\n')


def main():
    if OUT.exists():
        raise ValueError('Inspect saved inventory instead of overwriting')
    final = read(EXPERIMENT / 'final-review.json')
    assert final['player_walkthrough_status'] == 'complete'
    verify(final['hashes'])
    pre = read(EXPERIMENT / 'preflight.json')
    verify(pre['hashes'])
    q = pl.read_parquet(EXPERIMENT / 'predictions.parquet')
    columns = ['row_id', 'origin_year', 'player_id', 'pa_0', 'ctx_information_date', *pre['job_features']]
    columns = list(dict.fromkeys(columns))
    features = {k: pl.read_parquet(EXPERIMENT / f'features-{k}.parquet', columns=columns) for k in range(5)}
    ledger = {r['candidate_key']: r for r in read(GEN / 'hitter-status-evidence-v2/status-ledger.json')['rows']}
    source_hashes = read(GEN / 'hitter-status-evidence-v2/source-seal.json')['source_hashes']
    paths = [Path(__file__), ROOT / 'src/universal_baseball/availability_inventory.py',
             ROOT / 'tests/test_availability_inventory.py', ROOT / 'docs/hitter-availability-inventory-contract.md',
             EXPERIMENT / 'final-review.json', EXPERIMENT / 'preflight.json', EXPERIMENT / 'predictions.parquet',
             GEN / 'hitter-status-evidence-v2/status-ledger.json',
             ROOT / 'src/universal_baseball/hitter_status_evidence_v2.py',
             ROOT / 'src/universal_baseball/availability_context_v29b.py',
             ROOT / 'src/universal_baseball/availability_context_v29.py',
             ROOT / 'config/hitter_status_return_reports.json', ROOT / 'config/availability_facts_v29.json',
             ROOT / 'config/availability_facts_v29b.json', *[ROOT / 'docs' / name for name in PRIOR]]
    paths += [EXPERIMENT / f'features-{k}.parquet' for k in range(5)]
    captured = [ROOT / p for p in source_hashes if Path(p).name.startswith('transactions-')
                and p.endswith('.json') and not p.endswith('.metadata.json')]
    assert len(captured) == 24
    paths += captured
    for path in captured:
        assert sha256_file(path) == source_hashes[str(path.relative_to(ROOT))]
    OUT.mkdir()
    save('source-seal.json', dict(before_audit=True, new_fits=0, forecasts_changed=False,
        hashes={str(p.relative_to(ROOT)): sha256_file(p) for p in paths}))
    warnings = []
    for r in features[0].to_dicts():
        status = ledger[f'{r["origin_year"]}:{r["player_id"]}']
        assert r['ctx_information_date'] == status['information_date']
        if old_restriction_with_later_mlb_use(r, status['absence']):
            warnings.append(dict(row_id=r['row_id'], player_id=r['player_id'], origin_year=r['origin_year'],
                cutoff=status['information_date'], origin_MLB_PA=r['pa_0'], absence=status['absence'],
                future_outcomes_not_used_in_warning=True, legal_reinstatement_not_certified=True))
    evaluated = {r['row_id']: r for r in q.to_dicts()}
    save('warnings.json', dict(source_rows=63314, warnings=warnings))
    people = {pid for pid, _ in CASES}
    captures = []
    raw = {pid: [] for pid in people}
    for path in captured:
        payload = read(path)
        selected = [r for r in payload['transactions'] if (r.get('person') or {}).get('id') in people]
        captures.append((int(path.stem.split('-')[-1]), dict(transactions=selected)))
        for r in selected:
            raw[r['person']['id']].append(dict(path=str(path.relative_to(ROOT)), record=r))
    teams = set()
    for y in range(2012, 2026):
        path = GEN / f'hitter-preseason-population-source/captures/teams-{y}.json'
        assert sha256_file(path) == source_hashes[str(path.relative_to(ROOT))]
        teams.update(r['id'] for r in read(path)['teams'])
    facts = [f for name in ['availability_facts_v29.json', 'availability_facts_v29b.json']
             for f in read(ROOT / 'config' / name)['events'] if f['player_id'] in people]
    records, _ = clinical.normalize(captures, teams, facts, maximum=date(2025, 1, 24))
    reports = read(ROOT / 'config/hitter_status_return_reports.json')['events']
    stints = pl.read_parquet(GEN / 'practical-hitter-v31/dated-stints.parquet')
    fit = read(EXPERIMENT / 'fit-report.json')
    cases = []
    with threadpool_limits(limits=2):
        for pid, y in CASES:
            rows = q.filter((pl.col('player_id') == pid) & (pl.col('origin_year') == y))
            assert rows.height == 1, (pid, y)
            r = rows.row(0, named=True)
            status = ledger[f'{y}:{pid}']
            eligible = [v for v in records if v['player_id'] == pid]
            replay = absence_state(eligible, date.fromisoformat(status['information_date']),
                                   [v for v in reports if v['player_id'] == pid])
            assert replay == status['absence'], (pid, y)
            f = features[r['outer_fold']].filter(pl.col('row_id') == r['row_id']).row(0, named=True)
            cell = next(c for c in fit['cells'] if (c['origin'], c['fold']) == (y, r['outer_fold']))
            heads = {}
            for h in cell['heads']:
                path = ROOT / h['path']
                assert sha256_file(path) == h['sha256']
                m = joblib.load(path)
                x = np.array([f[n] for n in h['features']])
                t = logit_trace(m, x, h['features']) if h['head'] == 'participation' else trace(m, x, h['features'])
                heads[h['head']] = t
                col = 'corrected_job_raw_p' if h['head'] == 'participation' else 'corrected_job_raw_conditional_pa'
                actual = t['linked_probability'] if h['head'] == 'participation' else t['raw_prediction']
                assert np.isclose(actual, r[col], atol=1e-8, rtol=0)
            cases.append(dict(origin=r, source_status=status, source_status_replayed=True,
                eligible_raw_records=[v for v in raw[pid] if max(str(v['record'].get(k) or '')[:10]
                    for k in ['date', 'effectiveDate', 'resolutionDate']) <= status['information_date']],
                normalized_absence_records=eligible, inputs=f, saved_head_mechanics=heads,
                stats=stints.filter((pl.col('player_id') == pid) & pl.col('season').is_between(y-2, y)).to_dicts(),
                warning=old_restriction_with_later_mlb_use(f, status['absence']),
                forecast_unchanged=True, no_new_gain_or_harm_forecast=True))
    save('player-walks.json', dict(cases=cases, player_walkthrough_status='machine_ready_manual_pending'))
    subset = [r for r in warnings if r['row_id'] in evaluated]
    summary = dict(status='inventory_built_manual_pending', new_fits=0, forecasts_changed=False,
        source_warning_origins=len(warnings), source_warning_people=len({r['player_id'] for r in warnings}),
        evaluated_warning_origins=len(subset), evaluated_warning_people=len({r['player_id'] for r in subset}),
        source_rows=63314, evaluation_rows=30519, player_cases=len(cases),
        availability_features_already_present=True, completed_2026_evaluation_unchanged=True,
        next_action='Repair source coverage and observation state before any further availability fit')
    assert (len(warnings), len(subset)) == (83, 54)
    save('summary.json', summary)
    save('audit-receipt.json', dict(hashes={str(p.relative_to(ROOT)): sha256_file(p)
        for p in [OUT/'source-seal.json', OUT/'warnings.json', OUT/'player-walks.json', OUT/'summary.json']}))
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
