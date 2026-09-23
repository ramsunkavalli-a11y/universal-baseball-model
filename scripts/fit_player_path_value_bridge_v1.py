"""Fixed empirical-path distribution experiment, not production forecast replacement."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

from universal_baseball.player_path_distribution import coarse_draws, forest_draws, summarize_draws
from universal_baseball.hitter_three_year_opportunity import attach_cohorts
from universal_baseball.six_year_hitter import extend_labels
from universal_baseball.storage import sha256_file
from fit_hitter_arrival_coherence_v1 import BASE, DEBUT, save

OUT = Path('reports/generated/player-path-value-bridge-v1')
PLAN = Path('docs/player-path-value-bridge-v1-plan.md')
REFERENCE = Path('model_artifacts/hitter-arrival-coherence-v1-2026-09-23/predictions.parquet')


def training(panel, cutoff, horizon, excluded=()):
    valid = ((pl.col('origin_year')+horizon <= cutoff)
             & ~((pl.col('origin_year') < 2020) & (pl.col('origin_year')+horizon >= 2020))
             & ~pl.col('player_id').is_in(list(excluded)))
    for h in range(1, horizon+1):
        valid &= pl.col(f'war_h{h}').is_not_null() & pl.col(f'pa_h{h}').is_not_null()
    return panel.filter(valid).sort('origin_year', 'player_id').unique('player_id', keep='last').sort('player_id')


def references(horizon):
    p = pl.read_parquet(REFERENCE).filter(~pl.col('cold') & (pl.col('horizon') <= horizon))
    return p.with_columns(pl.when(pl.col('horizon') <= 3).then(pl.col('C2_value'))
        .otherwise(pl.col('old_value')).alias('delivered')).group_by('origin_year', 'player_id').agg(
            pl.col('delivered').sum().alias('delivered_mean'), pl.col('horizon').n_unique().alias('n_horizons')
        ).filter(pl.col('n_horizons') == horizon).drop('n_horizons')


def main():
    OUT.mkdir(exist_ok=True, parents=True)
    paths = [PLAN, Path(__file__), Path('src/universal_baseball/player_path_distribution.py'),
             BASE/'panel.parquet', BASE/'targets.parquet', BASE/'manifest.json', DEBUT, REFERENCE]
    hashes = {str(p): sha256_file(p) for p in paths}
    fingerprint = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()[:16]
    cache = OUT/'cache'/fingerprint
    cache.mkdir(exist_ok=True, parents=True)
    targets = pl.read_parquet(BASE/'targets.parquet')
    panel = attach_cohorts(extend_labels(pl.read_parquet(BASE/'panel.parquet'), targets), pl.read_parquet(DEBUT), targets)
    full = json.loads((BASE/'manifest.json').read_text())['full_features']
    core = [c for c in full if c in ['age_centered', 'age_squared', 'age_missing', 'reorganization_era']
            or c.startswith(('level_', 'missing_lag', 'log_pa_lag', 'log_mlb_pa_lag'))]
    folds = [(y, 3, False) for y in (2016, 2019, 2021, 2022, 2025)]
    folds += [(y, 6, False) for y in (2016, 2017, 2018, 2019, 2025)] + [(2022, 3, True)]
    all_results, notes = [], []
    for year, horizon, cold in folds:
        test = panel.filter(pl.col('origin_year') == year).sort('player_id')
        train = training(panel, year, horizon, test['player_id'].to_list() if cold else ())
        wy = train.select([f'war_h{h}' for h in range(1, horizon+1)]).to_numpy()
        py = train.select([f'pa_h{h}' for h in range(1, horizon+1)]).to_numpy()
        is_future = year == 2025
        ay = None if is_future else test.select([f'war_h{h}' for h in range(1, horizon+1)]).to_numpy()
        ap = None if is_future else test.select([f'pa_h{h}' for h in range(1, horizon+1)]).to_numpy()
        if not is_future and (not np.isfinite(ay).all() or not np.isfinite(ap).all()):
            raise ValueError('Missing test outcomes')
        for method in ('B0', 'F0', 'F1'):
            dest = cache/f'{year}-h{horizon}-cold{int(cold)}-{method}'
            if dest.with_suffix('.parquet').exists():
                result = pl.read_parquet(dest.with_suffix('.parquet'))
                note = json.loads(dest.with_suffix('.json').read_text())
            else:
                print(f'Fit {year} H{horizon} cold={cold} {method}: {train.height} donors', flush=True)
                if method == 'B0':
                    draws, structure = coarse_draws(train, test), []
                else:
                    draws, structure = forest_draws(train, test, core if method == 'F0' else full, horizon)
                summary = summarize_draws(wy[draws], py[draws], ay, ap)
                result = test.select('origin_year', 'player_id', 'player_name', 'age', 'level', 'stage', 'prospect', 'recent_debut').with_columns(
                    pl.lit(horizon).alias('horizon'), pl.lit(cold).alias('cold'), pl.lit(method).alias('method'),
                    pl.lit(year < 2020 <= year+horizon).alias('pandemic'),
                    *[pl.Series(k, v) for k, v in summary.items()],
                    pl.Series('distinct_donors', [len(np.unique(d)) for d in draws]))
                result = result.join(references(horizon), on=['origin_year', 'player_id'], how='left', validate='1:1', maintain_order='left')
                if not is_future:
                    result = result.with_columns(((pl.col('delivered_mean')-pl.col('actual_batting'))**2).alias('delivered_mse'))
                result.write_parquet(dest.with_suffix('.parquet'))
                np.savez_compressed(dest.with_suffix('.npz'), donor_indices=draws,
                    donor_player_id=train['player_id'].to_numpy(), donor_origin=train['origin_year'].to_numpy(),
                    query_player_id=test['player_id'].to_numpy())
                note = {'origin': year, 'horizon': horizon, 'cold': cold, 'method': method,
                    'train_rows': train.height, 'training_origins': sorted(train['origin_year'].unique().to_list()),
                    'latest_training_outcome': int(train['origin_year'].max())+horizon,
                    'query_players_in_training': len(set(train['player_id']) & set(test['player_id'])),
                    'self_donors': int((train['player_id'].to_numpy()[draws] == test['player_id'].to_numpy()[:, None]).sum()),
                    'honest_splits': structure, 'draw_path': str(dest.with_suffix('.npz')),
                    'draw_sha256': sha256_file(dest.with_suffix('.npz'))}
                save(dest.with_suffix('.json'), note)
            all_results.append(result)
            notes.append(note)
            print(f'Ready {year} H{horizon} cold={cold} {method}', flush=True)
    pl.concat(all_results, how='diagonal_relaxed').write_parquet(OUT/'predictions.parquet')
    assert all(sha256_file(Path(p)) == v for p, v in hashes.items())
    save(OUT/'fit-manifest.json', {'source_hashes': hashes, 'fingerprint': fingerprint,
        'core_features': core, 'full_features': full, 'fits': notes, 'protected_outcomes_used': False,
        'current_forecasts_changed': False, 'target': 'batting_plus_replacement_not_whole_war'})


if __name__ == '__main__':
    with threadpool_limits(limits=4):
        main()
