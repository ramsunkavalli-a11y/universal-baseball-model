"""Lock the corrected fixed-origin-weight cluster estimand."""
import importlib.util
from pathlib import Path
import sys

import numpy as np

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('foreign_borrowed_finalizer',
    SCRIPTS / 'finalize_foreign_borrowed_stability.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def row(pid, year, delta):
    return dict(player_id=pid, origin_year=year,
        **{arm+'_'+loss: (0 if arm=='affine' else delta)
           for arm in ['affine', 'borrowed'] for loss in ['logloss', 'brier', 'K_sq', 'HR_sq']})


def test_fixed_original_weights_and_repeated_people():
    rows = [row(1, 2016, -4), row(1, 2017, 2), row(2, 2017, 6)]
    output = module.fixed_cluster_intervals(rows, draws=2000)
    # Half of original mass is 2016, half 2017: (-4 + (2+6)/2)/2 = 0.
    assert output['intervals']['logloss']['delta'] == 0
    assert output['people'] == 2 and output['row_level_and_player_aggregate_resamples_agree']
    # Person 1 only: fixed masses 1/2 and 1/4 => -2, not year-renormalized -1.
    # Person 2 only: +6. All three possible cluster compositions occur.
    assert np.allclose(output['intervals']['logloss']['nominal_player_cluster_interval'], [-2, 6])


def test_reordering_rows_does_not_change_cluster_draws():
    rows = [row(1, 2016, -4), row(1, 2017, 2), row(2, 2017, 6)]
    a = module.fixed_cluster_intervals(rows)
    b = module.fixed_cluster_intervals(list(reversed(rows)))
    assert a['intervals'] == b['intervals']


def test_paired_constant_change_has_degenerate_interval():
    output = module.fixed_cluster_intervals([row(1, 2016, -.1), row(2, 2017, -.1)])
    assert np.allclose(output['intervals']['logloss']['nominal_player_cluster_interval'], [-.1, -.1])
