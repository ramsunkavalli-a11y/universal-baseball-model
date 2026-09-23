"""Read-only package, chronology, donor independence and sample-score verification."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

from fit_player_path_value_bridge_v1 import BASE, DEBUT, training
from report_player_path_value_bridge_v1 import PACKAGE
from universal_baseball.hitter_three_year_opportunity import attach_cohorts
from universal_baseball.player_path_distribution import summarize_draws
from universal_baseball.six_year_hitter import extend_labels
from universal_baseball.storage import sha256_file


def main():
    meta = json.loads((PACKAGE/'manifest.json').read_text())
    fit = json.loads((PACKAGE/'fit-manifest.json').read_text())
    decision = json.loads((PACKAGE/'score-report.json').read_text())
    for name, expected in meta['files'].items():
        assert sha256_file(PACKAGE/name) == expected, name
    for mapping in (meta['report_code'], fit['source_hashes']):
        for name, expected in mapping.items():
            assert sha256_file(Path(name)) == expected, name
    assert decision['status'] == 'reject_current_path_challenger'
    assert not decision['production_forecasts_changed']
    assert not decision['dollar_values_available']
    assert not decision['protected_outcomes_used']
    f = pl.read_parquet(PACKAGE/'predictions.parquet')
    assert f.select('origin_year', 'horizon', 'cold', 'method', 'player_id').is_duplicated().sum() == 0
    now = f.filter(pl.col('origin_year') == 2025)
    assert now['actual_batting'].null_count() == now.height
    targets = pl.read_parquet(BASE/'targets.parquet')
    panel = attach_cohorts(extend_labels(pl.read_parquet(BASE/'panel.parquet'), targets), pl.read_parquet(DEBUT), targets)
    rebuilt = {}
    for note in fit['fits']:
        year, h, cold, method = (note[k] for k in ('origin', 'horizon', 'cold', 'method'))
        assert note['latest_training_outcome'] <= year <= 2025
        assert note['self_donors'] == 0
        assert all(s['overlap'] == 0 for s in note['honest_splits'])
        if cold:
            assert note['query_players_in_training'] == 0
        assert all(y+h <= year and not y < 2020 <= y+h for y in note['training_origins'])
        path = Path(note['draw_path'])
        assert sha256_file(path) == note['draw_sha256']
        archive = np.load(path)
        assert not (archive['donor_player_id'][archive['donor_indices']] == archive['query_player_id'][:, None]).any()
        key = year, h, cold
        test = panel.filter(pl.col('origin_year') == year).sort('player_id')
        if key not in rebuilt:
            rebuilt[key] = training(panel, year, h, test['player_id'].to_list() if cold else ())
        train = rebuilt[key]
        np.testing.assert_array_equal(train['player_id'], archive['donor_player_id'])
        np.testing.assert_array_equal(train['origin_year'], archive['donor_origin'])
        np.testing.assert_array_equal(test['player_id'], archive['query_player_id'])
        # Exact recomputation for a fixed query verifies labels and joint path use.
        idx = archive['donor_indices'][0:1]
        wy = train.select([f'war_h{i}' for i in range(1, h+1)]).to_numpy()[idx]
        py = train.select([f'pa_h{i}' for i in range(1, h+1)]).to_numpy()[idx]
        ay = None if year == 2025 else test.head(1).select([f'war_h{i}' for i in range(1, h+1)]).to_numpy()
        ap = None if year == 2025 else test.head(1).select([f'pa_h{i}' for i in range(1, h+1)]).to_numpy()
        summary = summarize_draws(wy, py, ay, ap)
        row = f.filter((pl.col('origin_year') == year) & (pl.col('horizon') == h) & (pl.col('cold') == cold)
                       & (pl.col('method') == method) & (pl.col('player_id') == test['player_id'][0])).row(0, named=True)
        for name, expected in summary.items():
            np.testing.assert_allclose(row[name], expected[0], rtol=1e-12, atol=1e-12)
    print(json.dumps({'verified': True, 'runs': len(fit['fits']), 'rows': f.height,
                      'current_research_rows': now.height, 'decision': decision['status'],
                      'live_forecasts_changed': False, 'dollar_values_available': False}))


if __name__ == '__main__':
    main()
