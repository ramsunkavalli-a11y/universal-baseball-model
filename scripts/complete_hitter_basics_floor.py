"""Append reviewed completion; preserve raw score receipt and frozen forecasts."""
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.storage import sha256_file

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/model-evidence/hitter-basics-floor'


def main():
    path = OUT / 'completion.json'
    assert not path.exists(), 'Do not overwrite completed evidence'
    report = json.loads((OUT / 'report.json').read_text(encoding='utf8'))
    for name, digest in report['source_hashes'].items():
        assert sha256_file(Path(name)) == digest, name
    assert report['new_fits'] == report['new_data_sources'] == 0
    assert not report['protected_2026_outcomes_used'] and not report['forecasts_changed']
    q = pl.read_parquet(ROOT / 'reports/generated/hitter-mlb-events-restoration/predictions.parquet').filter(
        ~pl.col('source_addition')).with_columns(pl.lit(0.).alias('mean_rate'))
    equations = 0
    for arm, col in [('incumbent', 'current_rate'), ('past_profile', 'scalar_baseline_rate'), ('league_mean', 'mean_rate')]:
        t = q.with_columns((pl.col('current_pa') * (pl.col(col) / 600 + pl.col('origin_replacement_rate')) -
            pl.col('actual_relative_value')).alias('error'))
        value_mse = t.group_by('origin_year').agg((pl.col('error') ** 2).mean().alias('mse'))['mse'].mean()
        rate_mse = t.filter(pl.col('next_pa') > 0).group_by('origin_year').agg(
            (((pl.col(col) - pl.col('actual_relative_rate')) ** 2 * pl.col('next_pa')).sum() /
             pl.col('next_pa').sum()).alias('mse'))['mse'].mean()
        s = report['scores']['all'][arm]
        assert np.isclose(np.sqrt(value_mse), s['value_rmse'], atol=1e-12)
        assert np.isclose(np.sqrt(rate_mse), s['rate_rmse'], atol=1e-12)
        equations += 2
    assert len(report['cases']) == report['source_cases_reconstructed'] == 10
    assert sum('largest floor gain' in c['reasons'] for c in report['cases']) == 1
    assert sum('largest floor harm' in c['reasons'] for c in report['cases']) == 1
    assert any(c['actual_rate'] is None for c in report['cases'])
    for case in report['cases']:
        o = case['forecast']
        assert np.isclose(o['current_p'] * o['current_conditional_pa'], o['current_pa'], atol=1e-9)
        assert case['source_pool']['cutoff'] == o['origin_year']
        assert o['outer_fold'] in case['source_pool']['excluded_folds']
        assert len(case['origin_selected_peers']) == 3
        assert all(p['player_id'] != o['player_id'] for p in case['origin_selected_peers'])
    selected = ROOT / 'model_artifacts/hitter-selected-2026-frozen-2026-10-05/freeze-manifest.json'
    frozen_hash = sha256_file(selected)
    assert frozen_hash == 'a1d819ffcdd98a9ee62feecf5637b5ebe1f93b6e931d77d2b7d692ed928da67a'
    final_2026 = ROOT / 'reports/model-evidence/hitter-final-2026/report.json'
    assert sha256_file(final_2026) == '8c2acfeb42ece7d109d3b35542a6b79ec372467d7027d5945a4ba800cde913bb'
    paths = [OUT / 'report.json', ROOT / 'docs/hitter-basics-reset-plan.md',
        ROOT / 'docs/hitter-basics-floor-result.md', ROOT / 'docs/hitter-basics-reset-assessment.md',
        ROOT / 'scripts/check_hitter_basics_floor.py', Path(__file__),
        ROOT / 'tests/test_hitter_basics_floor.py', selected, final_2026]
    receipt = dict(player_walkthrough_status='complete', cases=10, independent_headline_equations=equations,
        basic_competence='Overall and established hitting clear the limited past-profile floor; lower-minors not certified',
        peer_qualification='Origin-only peers retained; current-exposure matching is inadequate for established returns/elite pedigree',
        disposition='Keep hitting reference; prioritize opportunity mechanism, no forecast promotion',
        new_fits=0, forecasts_changed=False, deployment_approved=False,
        completed_2026_evaluation_unchanged=True,
        raw_receipt_pending_marker_preserved=True,
        hashes={str(p): sha256_file(p) for p in paths})
    path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf8', newline='\n')
    print('Ten walks and six independent equations complete; unchanged evaluated forecast retained.')


if __name__ == '__main__':
    main()
