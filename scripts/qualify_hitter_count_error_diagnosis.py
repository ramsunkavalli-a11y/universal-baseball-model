"""Independent arithmetic and global-weight qualifications; no fits or selection."""
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.storage import sha256_file
from run_hitter_count_baseline import ROOT, OUT as COUNT, EVENTS, read, verify

OUT = ROOT / 'reports/generated/hitter-count-error-diagnosis'
TERMS = ['delivered_delta', 'active_hitting_squared', 'active_interaction', 'nonarrival']


def save(name, value):
    p = OUT / name
    assert not p.exists(), f'Preserve {p}'
    p.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf8', newline='\n')


def main():
    receipt = read(OUT / 'receipt.json')
    verify(receipt['hashes'])
    f = pl.read_parquet(OUT / 'diagnostic-rows.parquet').sort('row_id')
    original = f.filter(~pl.col('source_addition'))
    years = original['origin_year'].to_numpy()
    w = np.zeros(original.height)
    for y in np.unique(years):
        m = years == y
        w[m] = 1 / (m.sum() * len(np.unique(years)))
    assert np.isclose(w.sum(), 1)
    n = original['next_pa'].to_numpy()
    pa = original['count_pa'].to_numpy()
    assert original['current_pa'].equals(original['count_pa'])
    a = original['actual_relative_rate'].to_numpy()
    rep = original['origin_replacement_rate'].to_numpy()
    active = n > 0
    old_rate, new_rate = [original[k + '_rate'].to_numpy() for k in ['current', 'count']]
    old_t, new_t, o = [np.zeros(original.height) for _ in range(3)]
    old_t[active] = pa[active] * (old_rate[active] - a[active]) / 600
    new_t[active] = pa[active] * (new_rate[active] - a[active]) / 600
    o[active] = (pa[active] - n[active]) * (a[active] / 600 + rep[active])
    old_error, new_error = [(original[k + '_value'] - original['actual_relative_value']).to_numpy() for k in ['current', 'count']]
    assert np.allclose(old_t[active] + o[active], old_error[active], atol=1e-10)
    assert np.allclose(new_t[active] + o[active], new_error[active], atol=1e-10)
    expected = np.column_stack([new_error**2 - old_error**2, new_t**2 - old_t**2, 2 * o * (new_t - old_t), np.where(active, 0, new_error**2 - old_error**2)])
    assert np.allclose(expected, original.select(TERMS).to_numpy(), atol=1e-10)
    assert np.allclose(expected[:, 0], expected[:, 1:].sum(1), atol=1e-10)
    assert np.allclose(original.filter(pl.col('next_pa') > 0).select([f'error_term_{e}' for e in EVENTS]).to_numpy().sum(1), (new_rate - a)[active], atol=1e-10)
    scores = {}
    for name, e in [('current', old_error), ('count', new_error)]:
        rate_mse = []
        for y in np.unique(years):
            m = (years == y) & active
            r = old_rate if name == 'current' else new_rate
            rate_mse.append(np.sum(n[m] * (r[m] - a[m])**2) / n[m].sum())
        scores[name] = dict(value_rmse=float(np.sqrt(w @ (e * e))), rate_rmse=float(np.sqrt(np.mean(rate_mse))))
    groups = read(OUT / 'groups.json')
    for name in scores:
        for metric in scores[name]:
            assert np.isclose(scores[name][metric], groups[0]['scores'][name][metric], atol=1e-12)
    families = sorted({r['family'] for r in groups} - {'all', 'additions'})
    contributions = []
    global_terms = dict(zip(TERMS, (w @ expected).tolist()))
    for family in families:
        values = original[family].to_numpy()
        family_rows = []
        for value in sorted(set(values)):
            m = values == value
            term = dict(zip(TERMS, (w[m] @ expected[m]).tolist()))
            family_rows.append(dict(family=family, group=value, rows=int(m.sum()), active_rows=int((m & active).sum()), global_weight=float(w[m].sum()), global_MSE_contribution=term))
        for key in TERMS:
            assert np.isclose(sum(r['global_MSE_contribution'][key] for r in family_rows), global_terms[key], atol=1e-12)
        contributions.extend(family_rows)
    # Additions have no incumbent. Show their count-only errors, never a fake delta.
    additions = []
    for row in f.filter(pl.col('source_addition')).iter_rows(named=True):
        assert row['current_rate'] is None and row['delivered_delta'] is None
        n, pa, r, rep = [row[k] for k in ['next_pa', 'count_pa', 'count_rate', 'origin_replacement_rate']]
        error = row['count_value'] - row['actual_relative_value']
        t = pa * (r - row['actual_relative_rate']) / 600 if n > 0 else None
        o = (pa - n) * (row['actual_relative_rate'] / 600 + rep) if n > 0 else None
        assert n == 0 or np.isclose(t + o, error, atol=1e-10)
        additions.append(dict(row_id=row['row_id'], player_name=row['player_name'], origin_year=row['origin_year'], actual_PA=n, expected_PA=pa, hitting_error_at_expected_PA=t, opportunity_error_at_observed_hitting=o, count_value_error=error, incumbent_available=False))
    # Qualify metadata discarded by the sealed diagnostic join; it is not a fitted input.
    differences = []
    for k in range(5):
        source = pl.read_parquet(COUNT / f'features-{k}.parquet').select('row_id', pl.col('origin_replacement_rate').alias('feature_replacement'))
        joined = original.filter(pl.col('outer_fold') == k).select('row_id', 'origin_year', 'origin_replacement_rate').join(source, on='row_id', validate='1:1')
        for y in sorted(joined['origin_year'].unique()):
            h = joined.filter(pl.col('origin_year') == y)
            d = (h['feature_replacement'] - h['origin_replacement_rate']).to_numpy()
            differences.append(dict(fold=k, origin=y, rows=h.height, max_absolute_replacement_difference=float(abs(d).max())))
    save('global-attribution.json', dict(weighting='Original equal-origin row weights, unchanged across all groups; each family partitions the same global delta. Different families overlap and must not be added to each other.', global_terms=global_terms, groups=contributions))
    save('addition-decomposition.json', additions)
    paths = [Path(__file__), OUT / 'receipt.json', OUT / 'global-attribution.json', OUT / 'addition-decomposition.json']
    save('qualification.json', dict(new_fits=0, independent_formula_identity_pass=True, independently_replayed_overall_scores=scores, original_rows=original.height, active_original_rows=int(active.sum()), addition_rows=len(additions), complete_partition_families=len(families), metadata_differences=differences, metadata_qualification='Forecast replacement references are authoritative; feature-matrix replacement metadata were excluded at join. No talent feature or forecast was changed.', protected_outcomes_used=False, hashes={str(p): sha256_file(p) for p in paths}))
    print(json.dumps(dict(scores=scores, global_terms=global_terms, partition_families=len(families), additions=len(additions))))


if __name__ == '__main__':
    main()
