"""Read-only checks of the delivered repair, chronology, hashes and scope."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.multiyear_hitter_components import COMPONENTS
from universal_baseball.storage import sha256_file


def main():
    package = Path('model_artifacts/hitter-arrival-coherence-v1-2026-09-23')
    manifest = json.loads((package / 'manifest.json').read_text())
    fit = json.loads((package / 'fit-manifest.json').read_text())
    score = json.loads((package / 'score-report.json').read_text())
    for name, expected in manifest['files'].items():
        assert sha256_file(package / name) == expected, name
    for mapping in [manifest['build_code'], fit['source_hashes']]:
        for name, expected in mapping.items():
            assert sha256_file(Path(name)) == expected, name
    assert manifest['cutoff'] == '2025-12-31'
    assert score['selected_scope'] == 'C2'
    assert score['combined_update_allowed']
    assert not score['later_horizons_update_allowed']
    assert not score['protected_outcomes_used']
    for row in fit['fits']:
        assert row['latest_label'] <= row['origin'] <= 2025
        assert all(y + row['horizon'] <= row['origin'] for y in row['training_origins'])
        assert all(not (y < 2020 <= y + row['horizon']) for y in row['training_origins'])
        if row['cold']:
            assert row['shared_players'] == 0

    pred = pl.read_parquet(package / 'predictions.parquet')
    assert pred.select('origin_year', 'player_id', 'horizon', 'cold').is_duplicated().sum() == 0
    current = pred.filter(pl.col('origin_year') == 2025)
    assert current['actual_pa'].null_count() == current.height
    assert current['actual_value'].null_count() == current.height
    linked = pred.filter(pl.col('C2_affected'))
    assert linked.filter((pl.col('level') != 'RK') | pl.col('prior_debut')).height == 0
    np.testing.assert_allclose(linked['C2_pa'], linked['C2_p'] * linked['conditional_pa'])
    np.testing.assert_allclose(linked['C2_value'], linked['C2_pa'] * linked['rate'] / 600)

    delivered = pl.read_parquet(package / 'forecast-2026-2031.parquet').sort('player_id')
    old = pl.read_parquet('model_artifacts/six-year-hitter-v1-2026-09-22/forecast-2026-2031.parquet').sort('player_id')
    np.testing.assert_array_equal(delivered['player_id'], old['player_id'])
    assert delivered['player_id'].n_unique() == delivered.height == 3907
    counts = {}
    for h in range(1, 7):
        mask = delivered[f'arrival_repaired_h{h}'].to_numpy()
        counts[h] = int(mask.sum())
        if h > 3:
            assert not mask.any()
        else:
            assert counts[h] == 1093
            expected = current.filter(pl.col('horizon') == h).sort('player_id')
            np.testing.assert_array_equal(expected['player_id'], delivered['player_id'])
            np.testing.assert_array_equal(mask, expected['C2_affected'])
            for column, source in [(f'value_{2025+h}', 'C2_value'), (f'expected_pa_h{h}', 'C2_pa'), (f'activity_h{h}', 'C2_p')]:
                np.testing.assert_array_equal(delivered[column], expected[source])
        columns = [f'value_{2025+h}', f'expected_pa_h{h}', f'activity_h{h}', f'integrated_h{h}']
        columns += [f'{c}_runs_h{h}' for c in COMPONENTS]
        for column in columns:
            np.testing.assert_array_equal(delivered[column].to_numpy()[~mask], old[column].to_numpy()[~mask])
        if mask.any():
            ratio = delivered[f'expected_pa_h{h}'].to_numpy()[mask] / old[f'expected_pa_h{h}'].to_numpy()[mask]
            for c in COMPONENTS:
                np.testing.assert_allclose(delivered[f'{c}_runs_h{h}'].to_numpy()[mask], old[f'{c}_runs_h{h}'].to_numpy()[mask] * ratio)
            expected_value = delivered[f'value_{2025+h}'].to_numpy()[mask] + sum(delivered[f'{c}_runs_h{h}'].to_numpy()[mask] for c in COMPONENTS) / 10
            np.testing.assert_allclose(delivered[f'integrated_h{h}'].to_numpy()[mask], expected_value)
    assert delivered['full_control_value'].null_count() == delivered.height
    np.testing.assert_allclose(delivered['batting_c6'], sum(delivered[f'value_{2025+h}'] for h in range(1, 7)))
    np.testing.assert_allclose(delivered['integrated_c6'], sum(delivered[f'integrated_h{h}'] for h in range(1, 7)))
    print(json.dumps({'verified': True, 'fits': len(fit['fits']), 'prediction_rows': pred.height,
                      'players': delivered.height, 'repaired_by_horizon': counts,
                      'protected_outcomes_used': False, 'remaining_control_value': 'unavailable'}))


if __name__ == '__main__':
    main()
