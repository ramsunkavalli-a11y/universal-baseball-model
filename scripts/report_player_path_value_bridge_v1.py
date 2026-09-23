"""Archive the rejected experiment and explain the young-player failure mode."""
from __future__ import annotations

import json
from pathlib import Path
import shutil

import numpy as np
import polars as pl

from fit_hitter_arrival_coherence_v1 import save
from fit_player_path_value_bridge_v1 import OUT, BASE, DEBUT, training
from universal_baseball.hitter_three_year_opportunity import attach_cohorts
from universal_baseball.six_year_hitter import extend_labels
from universal_baseball.storage import sha256_file

PACKAGE = Path('model_artifacts/player-path-value-bridge-v1-2026-09-23')


def main():
    targets = pl.read_parquet(BASE/'targets.parquet')
    panel = attach_cohorts(extend_labels(pl.read_parquet(BASE/'panel.parquet'), targets), pl.read_parquet(DEBUT), targets)
    f = pl.read_parquet(OUT/'predictions.parquet')
    # This subset is a post-score diagnostic, not an additional selection gate.
    keys = panel.filter((pl.col('age') <= 23) & (pl.col('mlb_pa_lag0') > 0) & (pl.col('mlb_pa_lag0') < 100)).select('origin_year', 'player_id')
    recent = f.filter((pl.col('horizon') == 3) & ~pl.col('cold') & ~pl.col('pandemic') & (pl.col('origin_year') < 2025)).join(keys, on=['origin_year', 'player_id'], how='inner')
    young = recent.group_by('method').agg(pl.len().alias('player_origin_rows'),
        pl.col('actual_regular_workload').sum(), pl.col('p_regular_workload').sum().alias('expected_regular'),
        pl.col('actual_no_mlb').sum(), pl.col('p_no_mlb').sum().alias('expected_no_mlb'),
        pl.col('actual_batting').mean(), pl.col('mean_batting').mean(), pl.col('delivered_mean').mean())
    now = f.filter(pl.col('origin_year') == 2025)
    current_columns = ['player_id', 'player_name', 'age', 'stage', 'level', 'horizon', 'method',
        'mean_batting', 'batting_p10', 'batting_p50', 'batting_p90', 'mean_pa', 'p_no_mlb',
        'p_regular_workload', 'p_substantial_batting', 'p_sustained_high_batting', 'distinct_donors']
    now.select(current_columns).with_columns(pl.lit('rejected_research_not_player_forecast').alias('status')).write_parquet(OUT/'current-research-distributions.parquet')
    manifest = json.loads((OUT/'fit-manifest.json').read_text())
    donor_diagnostics = []
    for h in (3, 6):
        train = training(panel, 2025, h)
        note = next(n for n in manifest['fits'] if n['origin'] == 2025 and n['horizon'] == h and n['method'] == 'F1')
        archive = np.load(note['draw_path'])
        case = now.filter((pl.col('horizon') == h) & (pl.col('method') == 'F1') & (pl.col('player_name') == 'Bryce Eldridge'))
        pid = case['player_id'][0]
        index = np.flatnonzero(archive['query_player_id'] == pid)[0]
        donors = train[archive['donor_indices'][index].tolist()]
        donor_diagnostics.append({'horizon': h,
            'training_current_mlb_age19_22': train.filter((pl.col('stage') == 'Current MLB') & pl.col('age').is_between(19, 22)).height,
            'eldridge_sampled_donor_stages': donors.group_by('stage').len().sort('len', descending=True).to_dicts(),
            'eldridge_sampled_donor_age_mean': float(donors['age'].mean())})
    report = {'post_score_diagnostic_not_selection': True, 'young_brief_mlb_definition': 'age<=23 and current MLB PA in [1,99]',
              'young_brief_mlb': young.to_dicts(), 'donor_support': donor_diagnostics,
              'eldridge_rejected_research_only': now.filter(pl.col('player_name') == 'Bryce Eldridge').select(current_columns).to_dicts(),
              'interpretation': 'Sparse young-MLB donor support and broad-pool borrowing are hypotheses, not proven causes. Do not publish these probabilities as player forecasts.',
              'independent_horizon_warning': 'H3 and H6 are separate experiments, not a single coherent six-year distribution.',
              'next_candidate_requires_new_contract': True}
    save(OUT/'diagnosis.json', report)
    PACKAGE.mkdir(exist_ok=True, parents=True)
    for name in ('predictions.parquet', 'current-research-distributions.parquet', 'fit-manifest.json', 'score-report.json', 'diagnosis.json'):
        shutil.copyfile(OUT/name, PACKAGE/name)
    sources = [Path(__file__), Path('scripts/score_player_path_value_bridge_v1.py'),
               Path('src/universal_baseball/player_path_value.py'), Path('tests/test_player_path_value.py')]
    save(PACKAGE/'manifest.json', {'status': 'rejected_research', 'cutoff': '2025-12-31',
         'files': {n.name: sha256_file(n) for n in PACKAGE.iterdir() if n.name != 'manifest.json'},
         'report_code': {str(p): sha256_file(p) for p in sources},
         'draw_archives': 'Local fingerprinted cache; deterministic replay regenerates them. Not uploaded.',
         'live_forecasts_changed': False, 'dollar_values_available': False})
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
