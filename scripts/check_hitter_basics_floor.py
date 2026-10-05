"""No-fit competence check; historical artifacts only, no 2026 reuse."""
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.hitter_count_baseline import FEATURES, past_profile
from universal_baseball.hitter_past_direct_value import baseline
from universal_baseball.storage import sha256_file

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / 'reports/generated'
OUTPUT = ROOT / 'reports/model-evidence/hitter-basics-floor'
FIXED = [23934, 35088, 57052, 58061, 47261, 51083, 50571, 23483]


def validate(q):
    if q.is_empty() or q['target_year'].max() > 2025:
        raise ValueError('Historical targets ending in 2025 required')
    if q['row_id'].n_unique() != q.height:
        raise ValueError('Duplicate forecast rows')
    if not (q['target_year'] == q['origin_year'] + 1).all():
        raise ValueError('Only next-calendar-year forecasts')
    if q['source_addition'].any():
        raise ValueError('Additions lack the matched incumbent')
    if (q['next_pa'] < 0).any():
        raise ValueError('Invalid outcome exposure')
    for name in ['current_rate', 'scalar_baseline_rate', 'current_pa',
                 'actual_relative_rate', 'actual_relative_value', 'origin_replacement_rate']:
        if not np.isfinite(q[name].to_numpy()).all():
            raise ValueError(f'Nonfinite {name}')
    if (q['current_pa'] < 0).any() or (q['origin_replacement_rate'] <= 0).any():
        raise ValueError('Invalid forecast exposure/replacement')


def score(q, rate_column):
    """Equal origin contributions; PA-weighted and equal-player conditional rates."""
    parts = []
    for year in sorted(q['origin_year'].unique()):
        g = q.filter(pl.col('origin_year') == year)
        rate = g[rate_column].to_numpy()
        value = g['current_pa'].to_numpy() * (rate / 600 + g['origin_replacement_rate'].to_numpy())
        error = value - g['actual_relative_value'].to_numpy()
        active = g['next_pa'].to_numpy() > 0
        e = (rate - g['actual_relative_rate'].to_numpy())[active]
        n = g['next_pa'].to_numpy()[active]
        parts.append(dict(value_mse=float(np.mean(error ** 2)), value_mae=float(np.mean(abs(error))),
                          rate_mse=float(np.average(e ** 2, weights=n)) if len(e) else None,
                          equal_player_rate_mse=float(np.mean(e ** 2)) if len(e) else None,
                          value_total=float(value.sum())))
    return dict(rows=q.height, active_rows=int((q['next_pa'] > 0).sum()),
                value_rmse=float(np.sqrt(np.mean([p['value_mse'] for p in parts]))),
                value_mae=float(np.mean([p['value_mae'] for p in parts])),
                rate_rmse=float(np.sqrt(np.mean([p['rate_mse'] for p in parts if p['rate_mse'] is not None])))
                if any(p['rate_mse'] is not None for p in parts) else None,
                equal_player_rate_rmse=float(np.sqrt(np.mean([p['equal_player_rate_mse'] for p in parts
                    if p['equal_player_rate_mse'] is not None]))) if any(p['rate_mse'] is not None for p in parts) else None,
                expected_value=sum(p['value_total'] for p in parts),
                actual_value=float(q['actual_relative_value'].sum()),
                expected_PA=float(q['current_pa'].sum()), actual_PA=int(q['next_pa'].sum()))


def main():
    # Imports here do not run their fitting entry points.
    from run_hitter_count_baseline import REF, source_data, read, verify
    from prepare_hitter_overseas_integration import annual_labels
    from universal_baseball.hitter_compatible_value import labels

    if OUTPUT.exists():
        raise FileExistsError('Preserve the existing evidence; do not overwrite')
    evidence = read(ROOT / 'reports/model-evidence/hitter-mlb-events-restoration/report.json')
    assert evidence['player_walkthrough_status'] == 'complete'
    verify(evidence['hashes'])
    prediction_path = GEN / 'hitter-mlb-events-restoration/predictions.parquet'
    q = pl.read_parquet(prediction_path).filter(~pl.col('source_addition')).sort('row_id')
    validate(q)
    assert q.height == 30506 and set(q['origin_year']) == {2016, 2017, 2018, 2021, 2022, 2023, 2024}
    feature_paths = [GEN / f'hitter-count-baseline/features-{k}.parquet' for k in range(5)]
    graphs_paths = [GEN / f'hitter-shared-production/graphs-{k}.json' for k in range(5)]
    frames = {k: pl.read_parquet(p) for k, p in enumerate(feature_paths)}
    inputs = pl.concat([f.filter(pl.col('outer_fold') == k).select(
        'row_id', 'prior_debut', 'sc_tracked', 'minor_pa_0', *FEATURES, *REF)
        for k, f in frames.items()])
    inputs = inputs.filter(pl.col('row_id').is_in(q['row_id'])).sort('row_id')
    assert inputs['row_id'].equals(q['row_id'])
    reconstructed = baseline(inputs.select(FEATURES[:8]).to_numpy(), inputs.select(REF).to_numpy())
    assert np.allclose(reconstructed, q['scalar_baseline_rate'], atol=1e-10)
    assert np.allclose(q['current_value'], q['current_pa'] *
        (q['current_rate'] / 600 + q['origin_replacement_rate']), atol=1e-10)
    # Independently pair every actual label using the existing complete annual source.
    annual_path = GEN / 'practical-hitter-v31/dated-stints.parquet'
    counts, env = annual_labels(pl.read_parquet(annual_path))
    raw = np.array([counts.get((r['target_year'], r['player_id']), np.zeros(8)) for r in q.iter_rows(named=True)])
    lab = labels(raw, np.array([env[y] for y in q['origin_year']]), np.array([env[y] for y in q['target_year']]),
                 q['origin_replacement_rate'].to_numpy())
    assert np.array_equal(lab['pa'], q['next_pa'])
    assert np.allclose(lab['relative_rate'], q['actual_relative_rate'], atol=1e-10)
    assert np.allclose(lab['relative_value'], q['actual_relative_value'], atol=1e-10)
    q = q.with_columns(pl.lit(0.).alias('mean_rate'))
    arms = {'incumbent': 'current_rate', 'past_profile': 'scalar_baseline_rate', 'league_mean': 'mean_rate'}
    scopes = {'all': q, 'current_MLB': q.filter(pl.col('pa_0') > 0),
              'upper_never_debut': q.filter((pl.col('prior_debut') == 0) & (pl.col('stage') == 'Upper minors')),
              'lower_never_debut': q.filter((pl.col('prior_debut') == 0) & (pl.col('stage') == 'Lower minors')),
              'no_arrivals': q.filter(pl.col('next_pa') == 0)}
    scopes.update({f'origin_{y}': q.filter(pl.col('origin_year') == y) for y in sorted(q['origin_year'].unique())})
    scores = {name: {arm: score(g, col) for arm, col in arms.items()} for name, g in scopes.items()}
    floor_value = q['current_pa'] * (q['scalar_baseline_rate'] / 600 + q['origin_replacement_rate'])
    ranked = q.with_columns(((floor_value - q['actual_relative_value']) ** 2 -
        (q['current_value'] - q['actual_relative_value']) ** 2).alias('floor_minus_incumbent_squared_error'))
    chosen = {rid: ['fixed before scoring'] for rid in FIXED}
    for rid, why in [(ranked.sort('floor_minus_incumbent_squared_error')['row_id'][0], 'largest floor gain'),
                     (ranked.sort('floor_minus_incumbent_squared_error', descending=True)['row_id'][0], 'largest floor harm')]:
        chosen.setdefault(rid, []).append(why)
    _, history, sources, foreign = source_data()
    graphs = {k: read(p) for k, p in enumerate(graphs_paths)}
    saved = {r['row_id']: r for r in evidence['player_cases']}
    audited = read(GEN / 'hitter-incumbent-representation-audit/inventory.json')
    traces = {r['row_id']: r for r in audited['cases']}
    walks = []
    for rid, reasons in chosen.items():
        o = q.filter(pl.col('row_id') == rid).row(0, named=True)
        f = inputs.filter(pl.col('row_id') == rid).row(0, named=True)
        y, pid, k = o['origin_year'], o['player_id'], o['outer_fold']
        key = f'{y}:{pid}'
        values, source = past_profile(history[pid], graphs[k][f'{y}:{k}'], sources.get(key), foreign.get((key, k)),
                                      origin=y, outer_fold=k, own_fold=k)
        assert np.allclose([values[n] for n in FEATURES], [f[n] for n in FEATURES], atol=1e-10)
        rebuilt = baseline(np.array([[values[n] for n in FEATURES[:8]]]), np.array([source['reference']]))[0]
        assert np.isclose(rebuilt, o['scalar_baseline_rate'], atol=1e-10)
        peers = q.filter((pl.col('origin_year') == y) & (pl.col('player_id') != pid) &
                         (pl.col('prior_debut') == o['prior_debut']) & (pl.col('stage') == o['stage']))
        peers = peers.join(inputs.select('row_id', 'minor_pa_0'), on='row_id', validate='1:1')
        peers = peers.with_columns((((pl.col('age') - o['age']) / 5) ** 2 +
            ((pl.col('pa_0') - o['pa_0']) / 600) ** 2 +
            ((pl.col('minor_pa_0') - f['minor_pa_0']) / 600) ** 2).alias('origin_distance')).sort(
                ['origin_distance', 'player_id']).head(3)
        # Peer outcomes are revealed only AFTER selection by origin-known fields.
        branch = 'prospect' if not o['prior_debut'] else 'MLB_tracking' if f['sc_tracked'] else 'MLB_numeric'
        walks.append(dict(row_id=rid, reasons=reasons, forecast=o, incumbent_branch=branch,
            raw_history=[r for r in history[pid] if y - 2 <= r['season'] <= y], source_pool=source,
            baseline_features=values, baseline_rate=float(rebuilt), baseline_value=float(
                o['current_pa'] * (rebuilt / 600 + o['origin_replacement_rate'])),
            actual_rate=o['actual_relative_rate'] if o['next_pa'] > 0 else None,
            incumbent_coefficient_walk=traces.get(rid), prior_restoration_walk=saved.get(rid),
            origin_selected_peers=peers.select('row_id', 'player_id', 'player_name', 'age', 'pa_0', 'minor_pa_0',
                'origin_distance', 'current_rate', 'scalar_baseline_rate', 'current_pa', 'next_pa',
                'actual_relative_rate').to_dicts()))
    paths = [Path(__file__), ROOT / 'docs/hitter-basics-reset-plan.md', prediction_path, annual_path,
             ROOT / 'reports/model-evidence/hitter-mlb-events-restoration/report.json',
             GEN / 'hitter-incumbent-representation-audit/inventory.json',
             ROOT / 'src/universal_baseball/hitter_count_baseline.py',
             ROOT / 'src/universal_baseball/hitter_past_direct_value.py', *feature_paths, *graphs_paths]
    report = dict(target='next calendar year MLB batting rate and batting-plus-replacement, not full WAR',
        scores=scores, cases=walks, rows_reconstructed=q.height, source_cases_reconstructed=len(walks),
        peer_rule='same origin/stage/prior debut; squared scaled age/current MLB PA/minor PA distance; player-ID tie break',
        new_fits=0, new_data_sources=0, protected_2026_outcomes_used=False, forecasts_changed=False,
        deployment_approved=False, player_walkthrough_status='pending',
        source_hashes={str(p): sha256_file(p) for p in paths})
    OUTPUT.mkdir(parents=True)
    (OUTPUT / 'report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + '\n',
                                      encoding='utf8', newline='\n')
    print(json.dumps(scores['all'], indent=2))
    print('Cases:', [(r['forecast']['player_name'], r['forecast']['origin_year'], r['reasons']) for r in walks])


if __name__ == '__main__':
    main()
