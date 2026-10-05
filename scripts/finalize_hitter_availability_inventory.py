"""Verify read-only inventory membership and source/forecast walks."""
import json
from datetime import date
from pathlib import Path
import subprocess
import sys

import numpy as np
import polars as pl
from audit_hitter_availability_inventory import ROOT, GEN, OUT, EXPERIMENT, read, verify
from universal_baseball.storage import sha256_file


def main():
    public = ROOT / 'reports/model-evidence/hitter-availability-inventory/report.json'
    if (OUT / 'final-review.json').exists() or public.exists():
        raise ValueError('Preserve completed inventory')
    audit = read(OUT / 'audit-receipt.json')
    seal = read(OUT / 'source-seal.json')
    verify(audit['hashes'])
    verify(seal['hashes'])
    features = pl.read_parquet(EXPERIMENT / 'features-0.parquet',
        columns=['row_id', 'origin_year', 'player_id', 'pa_0', 'ctx_information_date'])
    ledger = {r['candidate_key']: r for r in read(GEN / 'hitter-status-evidence-v2/status-ledger.json')['rows']}
    independently_flagged = set()
    for r in features.to_dicts():
        a = ledger[f'{r["origin_year"]}:{r["player_id"]}']['absence']
        channels = list(a['active_restrictions'].values())
        if a['hard_unavailable'] or any(v['kind'] in ['deceased', 'permanent_ineligible'] for v in channels):
            continue
        if r['pa_0'] > 0 and channels and all(date.fromisoformat(v['event_date']).year < r['origin_year'] for v in channels):
            independently_flagged.add(r['row_id'])
    warnings = read(OUT / 'warnings.json')['warnings']
    assert independently_flagged == {r['row_id'] for r in warnings}
    q = pl.read_parquet(EXPERIMENT / 'predictions.parquet')
    in_test = q.filter(pl.col('row_id').is_in(list(independently_flagged)))
    assert len(independently_flagged) == 83 and in_test.height == 54
    assert len({r['player_id'] for r in warnings}) == 27 and in_test['player_id'].n_unique() == 23
    cases = read(OUT / 'player-walks.json')['cases']
    assert len(cases) == 9 and len({c['origin']['player_id'] for c in cases}) == 7
    for c in cases:
        r = c['origin']
        assert q.filter(pl.col('row_id') == r['row_id']).row(0, named=True) == r
        assert c['source_status']['absence'] == ledger[f'{r["origin_year"]}:{r["player_id"]}']['absence']
        assert c['warning'] == (r['row_id'] in independently_flagged)
        m = c['saved_head_mechanics']
        p = m['participation']['linked_probability']
        if c['inputs']['status_retired'] or c['inputs']['status_hard_unavailable']:
            p = 0.
        assert np.isclose(p * np.clip(m['conditional_pa']['raw_prediction'], 1, 800), r['corrected_job_pa'], atol=1e-8)
        assert c['source_status_replayed'] and c['forecast_unchanged']
    tests = []
    for command in [[sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', 'tests/test_availability_inventory.py'],
                    [sys.executable, 'scripts/verify_hitter_selected_2026_freeze.py'],
                    [sys.executable, 'scripts/verify_hitter_full_2026_freeze.py']]:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if result.returncode:
            raise ValueError(result.stdout + result.stderr)
        tests.append(dict(command=command[1:], exit_code=0, output=result.stdout))
    paths = [Path(__file__), ROOT / 'docs/hitter-availability-inventory-result.md',
             OUT / 'audit-receipt.json', OUT / 'source-seal.json', OUT / 'warnings.json',
             OUT / 'player-walks.json', OUT / 'summary.json']
    final = dict(status='read_only_inventory_review_complete_source_gap',
        player_walkthrough_status='complete', new_fits=0, forecasts_changed=False,
        source_warning_origins=83, source_warning_people=27, evaluated_warning_origins=54,
        evaluated_warning_people=23, source_rows=63314, evaluation_rows=30519,
        player_cases=9, distinct_case_people=7, source_case_replays=9, saved_heads_replayed=18,
        independently_reconstructed_warning_membership=True,
        legal_reinstatement_or_medical_recovery_certified=False, predictive_improvement_tested=False,
        deployment_approved=False, completed_2026_evaluation_unchanged=True,
        next_action='Repair systematic nonmedical return coverage and separate history, observed activity and current uncertainty before any fit',
        tests_and_freezes=tests, hashes={str(p.relative_to(ROOT)): sha256_file(p) for p in paths})
    verify(audit['hashes'])
    verify(seal['hashes'])
    (OUT / 'final-review.json').write_text(json.dumps(final, indent=2) + '\n', encoding='utf8', newline='\n')
    public.parent.mkdir(parents=True, exist_ok=True)
    public.write_text(json.dumps(final, indent=2) + '\n', encoding='utf8', newline='\n')
    print(json.dumps({k: v for k, v in final.items() if k not in ['hashes', 'tests_and_freezes']}), flush=True)


if __name__ == '__main__':
    main()
