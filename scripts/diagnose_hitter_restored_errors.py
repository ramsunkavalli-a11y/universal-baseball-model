"""Exact no-fit attribution of the sealed seven-input comparison."""
from pathlib import Path
import json

import numpy as np
import polars as pl

from universal_baseball.hitter_error_geometry import change, decompose
from universal_baseball.hitter_evidence_representation import RECENCY, foreign_precision, domestic_event_counts
from universal_baseball.hitter_compatible_value import labels
from universal_baseball.storage import sha256_file
from prepare_hitter_overseas_integration import annual_labels
from run_hitter_shared_production import ROOT, GEN, read, verify, source_data

PREVIOUS = GEN / 'hitter-mlb-events-restoration'
OUT = GEN / 'hitter-restored-error-diagnosis'
CONTRACT = ROOT / 'docs/hitter-restored-error-diagnosis-contract.md'
TERMS = ['delta', 'active_hitting_squared', 'active_interaction', 'nonarrival']
ARMS = ['current', 'restored', 'components']
EXPOSURES = ['none', 'positive_under600', '600plus']


def save(name, value):
    p = OUT / name
    assert not p.exists(), f'Preserve {p}'
    p.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf8', newline='\n')


def global_weights(q):
    y, n = q['origin_year'].to_numpy(), q['next_pa'].to_numpy()
    years = np.unique(y)
    value, rate = np.zeros(q.height), np.zeros(q.height)
    for origin in years:
        m = y == origin
        value[m] = 1 / (len(years) * m.sum())
        assert n[m].sum() > 0
        rate[m] = n[m] / (len(years) * n[m].sum())
    assert np.isclose(value.sum(), 1) and np.isclose(rate.sum(), 1)
    return value, rate


def independent_terms(q, anchor):
    n, pa, a, rep = [q[k].to_numpy() for k in ['next_pa', 'components_pa', 'actual_relative_rate', 'origin_replacement_rate']]
    active = n > 0
    old, new = [q[k + '_rate'].to_numpy() for k in [anchor, 'components']]
    t0, t1, o = np.zeros(q.height), np.zeros(q.height), np.zeros(q.height)
    t0[active] = pa[active] * (old[active] - a[active]) / 600
    t1[active] = pa[active] * (new[active] - a[active]) / 600
    o[active] = (pa[active] - n[active]) * (a[active] / 600 + rep[active])
    e0, e1 = [(q[k + '_value'] - q['actual_relative_value']).to_numpy() for k in [anchor, 'components']]
    assert np.allclose(t0[active] + o[active], e0[active], atol=1e-10)
    assert np.allclose(t1[active] + o[active], e1[active], atol=1e-10)
    terms = np.column_stack([e1**2 - e0**2, t1**2 - t0**2, 2 * o * (t1 - t0), np.where(active, 0, e1**2 - e0**2)])
    assert np.allclose(terms[:, 0], terms[:, 1:].sum(1), atol=1e-10)
    a = np.where(active, a, np.nan)
    helper = change(pa, n, old, new, a, rep)
    assert np.allclose(terms, np.column_stack([helper[k] for k in TERMS]), atol=1e-10)
    return terms, helper


def main():
    assert not OUT.exists(), 'Preserve completed or partial diagnosis'
    final = read(PREVIOUS / 'final-review.json'); verify(final['hashes'])
    assert final['player_walkthrough_status'] == 'complete'
    public_path = Path(final['public_report'])
    assert sha256_file(public_path) == final['public_report_sha256']
    public = read(public_path)
    pre = read(PREVIOUS / 'preflight.json'); verify(pre['source_hashes'])
    verify(read(PREVIOUS / 'source-review.json')['hashes'])
    fit = read(PREVIOUS / 'fit-report.json')
    for cell in fit['cells']:
        verify(cell['hashes'])
    q = pl.read_parquet(PREVIOUS / 'predictions.parquet').sort('row_id')
    assert q.height == 30519 and q['row_id'].n_unique() == 30519
    assert q['target_year'].max() == 2025 and q['horizon'].unique().to_list() == [1]
    assert q['components_pa'].equals(q['restored_pa'])
    original = q.filter(~pl.col('source_addition'))
    assert original.height == 30506 and original['components_pa'].equals(original['current_pa'])
    assert sorted(original['origin_year'].unique()) == [2016, 2017, 2018, 2021, 2022, 2023, 2024]
    assert q.filter(pl.col('source_addition'))['current_rate'].null_count() == 13
    actual, env = annual_labels(pl.read_parquet(GEN / 'practical-hitter-v31/dated-stints.parquet'))
    raw_counts = np.array([actual.get((r['target_year'], r['player_id']), np.zeros(8)) for r in q.iter_rows(named=True)])
    assert np.array_equal(raw_counts.sum(1), q['next_pa'].to_numpy())
    lab = labels(raw_counts, np.array([env[y] for y in q['origin_year']]), np.array([env[y] for y in q['target_year']]), q['origin_replacement_rate'].to_numpy())
    assert np.allclose(lab['relative_rate'], q['actual_relative_rate'], atol=1e-10)
    assert np.allclose(lab['relative_value'], q['actual_relative_value'], atol=1e-10)
    for arm in ARMS:
        m = ~q[arm + '_value'].is_null().to_numpy()
        assert np.allclose(q[arm + '_value'].to_numpy()[m], q[arm + '_pa'].to_numpy()[m] * (q[arm + '_rate'].to_numpy()[m] / 600 + q['origin_replacement_rate'].to_numpy()[m]), atol=1e-10)
    _, history, sources, _ = source_data()
    covered = set(read(GEN / 'hitter-mlb-events-source-audit/audit.json')['covered_source_seasons'])
    profiles = []
    for o in q.iter_rows(named=True):
        y, pid = o['origin_year'], o['player_id']
        assert set(range(y - 2, y + 1)) <= covered
        mlb = sum(RECENCY[y - r['season']] * domestic_event_counts(r).sum() for r in history[pid] if r['bucket'] == 'MLB' and 0 <= y - r['season'] < 3)
        foreign, by_league = foreign_precision(sources.get(f'{y}:{pid}'), origin=y)
        exposure = 'none' if mlb == 0 else 'positive_under600' if mlb < 600 else '600plus'
        overseas = 'both' if all(v > 0 for v in by_league.values()) else 'NPB' if by_league['NPB'] > 0 else 'KBO' if by_league['KBO'] > 0 else 'none'
        profiles.append(dict(row_id=o['row_id'], recent_observed_MLB_mass=float(mlb), recent_foreign_mass=float(foreign), overseas_source=overseas,
                             joint_profile=exposure + ('__foreign' if foreign > 0 else '__domestic')))
    q = q.join(pl.DataFrame(profiles), on='row_id', validate='1:1')
    old_profiles = pl.read_parquet(GEN / 'hitter-count-error-diagnosis/diagnostic-rows.parquet').sort('row_id')
    assert q['row_id'].equals(old_profiles['row_id'])
    assert np.allclose(q['recent_observed_MLB_mass'], old_profiles['recent_observed_MLB_mass'], atol=1e-10)
    assert q['overseas_source'].equals(old_profiles['overseas_source'])
    original = q.filter(~pl.col('source_addition'))
    w, rw = global_weights(original)
    n, a = original['next_pa'].to_numpy(), original['actual_relative_rate'].to_numpy()
    scores = {}
    for arm in ARMS:
        e = (original[arm + '_value'] - original['actual_relative_value']).to_numpy()
        re = original[arm + '_rate'].to_numpy() - a
        scores[arm] = dict(value_rmse=float(np.sqrt(w @ e**2)), value_mae=float(w @ abs(e)), rate_rmse=float(np.sqrt(rw @ re**2)),
                           expected_PA=float(original[arm + '_pa'].sum()), expected_value=float(original[arm + '_value'].sum()))
        for metric in ['value_rmse', 'value_mae', 'rate_rmse']:
            assert np.isclose(scores[arm][metric], public['scores']['scopes'][0]['scores'][arm][metric], atol=1e-12)
    rows = original.with_columns(pl.Series('global_value_weight', w), pl.Series('global_rate_weight', rw))
    contrasts = {}
    for anchor in ['current', 'restored']:
        terms, _ = independent_terms(original, anchor)
        rate_delta = (original['components_rate'].to_numpy() - a)**2 - (original[anchor + '_rate'].to_numpy() - a)**2
        contrasts[anchor] = dict(global_MSE_terms=dict(zip(TERMS, (w @ terms).tolist())), global_rate_MSE_change=float(rw @ rate_delta))
        rows = rows.with_columns(*[pl.Series(anchor + '_' + key, terms[:, j]) for j, key in enumerate(TERMS)], pl.Series(anchor + '_rate_MSE_delta', rate_delta))
        partitions = {
            'joint_profile': [(e + '__' + f, original['joint_profile'].to_numpy() == e + '__' + f) for e in EXPOSURES for f in ['domestic', 'foreign']],
            'origin': [(str(y), original['origin_year'].to_numpy() == y) for y in sorted(original['origin_year'].unique())],
            'participation': [('active', n > 0), ('nonarrival', n == 0)],
        }
        for family, groups in partitions.items():
            records = []
            assert np.array_equal(np.array([m for _, m in groups]).sum(0), np.ones(original.height))
            for name, m in groups:
                g = original.filter(pl.Series(m)); active = g.filter(pl.col('next_pa') > 0)
                records.append(dict(group=name, rows=g.height, people=g['player_id'].n_unique(), active_rows=active.height, active_people=active['player_id'].n_unique(),
                                    global_value_weight=float(w[m].sum()), global_rate_weight=float(rw[m].sum()),
                                    actual_PA=int(g['next_pa'].sum()), expected_PA=float(g['components_pa'].sum()), actual_value=float(g['actual_relative_value'].sum()),
                                    predicted_value={arm: float(g[arm + '_value'].sum()) for arm in ARMS},
                                    global_MSE_terms=dict(zip(TERMS, (w[m] @ terms[m]).tolist())), global_rate_MSE_change=float(rw[m] @ rate_delta[m])))
            for key in TERMS:
                assert np.isclose(sum(r['global_MSE_terms'][key] for r in records), contrasts[anchor]['global_MSE_terms'][key], atol=1e-12)
            assert np.isclose(sum(r['global_rate_MSE_change'] for r in records), contrasts[anchor]['global_rate_MSE_change'], atol=1e-12)
            contrasts[anchor][family] = records
        assert np.isclose(contrasts[anchor]['global_MSE_terms']['delta'], public['independent_paired_MSE_points'][anchor]['value'], atol=1e-12)
        assert np.isclose(contrasts[anchor]['global_rate_MSE_change'], public['independent_paired_MSE_points'][anchor]['rate'], atol=1e-12)
    all_forecasts = {r['row_id']: r for r in q.iter_rows(named=True)}
    walks = []
    for source_case in public['player_cases']:
        o = all_forecasts[source_case['row_id']]
        active = o['next_pa'] > 0
        arm_terms = {}
        for arm in ARMS:
            if o[arm + '_rate'] is None:
                continue
            d = decompose([o[arm + '_pa']], [o['next_pa']], [o[arm + '_rate']], [o['actual_relative_rate'] if active else np.nan], [o['origin_replacement_rate']])
            arm_terms[arm] = dict(rate=o[arm + '_rate'], value=o[arm + '_value'], delivered_error=float(d['error'][0]),
                                  hitting_error_at_expected_PA=float(d['hitting'][0]) if active else None,
                                  opportunity_error_at_observed_rate=float(d['opportunity'][0]) if active else None,
                                  opposing_errors=bool(d['hitting'][0] * d['opportunity'][0] < 0) if active else None)
        changes = {}
        for anchor in ['current', 'restored']:
            if anchor not in arm_terms:
                continue
            h = change([o['components_pa']], [o['next_pa']], [o[anchor + '_rate']], [o['components_rate']], [o['actual_relative_rate'] if active else np.nan], [o['origin_replacement_rate']])
            changes[anchor] = {key: float(h[key][0]) for key in TERMS}
        assert np.isclose(source_case['baseline_rate'] + source_case['fitted_residual'], o['components_rate'], atol=1e-10)
        assert np.isclose(source_case['fitted_intercept'] + sum(t['effect'] for t in source_case['feature_terms']), source_case['fitted_residual'], atol=1e-10)
        assert source_case['support'] and source_case['origin_selected_peers'] and source_case['information_date'] == o['ctx_information_date']
        walks.append(dict(row_id=o['row_id'], player_name=o['player_name'], player_id=o['player_id'], origin=o['origin_year'], target=o['target_year'],
                          information_date=o['ctx_information_date'], fold=o['outer_fold'], branch=o['count_branch'], why=source_case['why'],
                          joint_profile=o['joint_profile'], recent_MLB_mass=o['recent_observed_MLB_mass'], recent_foreign_mass=o['recent_foreign_mass'],
                          expected_PA=o['components_pa'], actual_PA=o['next_pa'], actual_rate=o['actual_relative_rate'] if active else None, actual_value=o['actual_relative_value'],
                          baseline=source_case['baseline_rate'], fitted_intercept=source_case['fitted_intercept'], fitted_residual=source_case['fitted_residual'],
                          added_component_effect=source_case['added_MLB_component_effect'], other_coefficient_change=source_case['other_coefficient_change'],
                          full_source_model_walk=dict(report=str(public_path.relative_to(ROOT)), sha256=sha256_file(public_path), case_row_id=o['row_id'],
                                                     fields=['raw_history', 'source', 'MLB_source', 'MLB_event_source', 'feature_terms', 'probes', 'support', 'origin_selected_peers']),
                          arms=arm_terms, contrasts=changes))
    assert len(walks) == 17 and {r['row_id'] for r in walks} == set(pre['fixed_case_row_ids'])
    additions = []
    for o in q.filter(pl.col('source_addition')).iter_rows(named=True):
        terms, _ = independent_terms(pl.DataFrame([o]), 'restored')
        additions.append(dict(row_id=o['row_id'], player_name=o['player_name'], origin=o['origin_year'], expected_PA=o['components_pa'], actual_PA=o['next_pa'],
                              actual_rate=o['actual_relative_rate'] if o['next_pa'] else None, actual_value=o['actual_relative_value'],
                              component_error=o['components_value'] - o['actual_relative_value'],
                              matched_restored_change=dict(zip(TERMS, terms[0].tolist())), incumbent_available=False))
    OUT.mkdir(parents=True)
    rows.write_parquet(OUT / 'diagnostic-rows.parquet')
    save('attribution.json', dict(scores=scores, original_rows=original.height, actual_PA=int(n.sum()), actual_value=float(original['actual_relative_value'].sum()), contrasts=contrasts,
                                  weights='Original global equal-origin weights; partitions sum to the same headline. Different partition families overlap and must not be added.',
                                  uncertainty='No new significance claim; existing player-bootstrap paired intervals remain nominal development evidence.'))
    save('player-decomposition.json', dict(cases=walks, additions=additions, full_source_walk_sha256=sha256_file(public_path), player_walkthrough_status='pending_readable_review'))
    paths = [Path(__file__), CONTRACT, PREVIOUS / 'final-review.json', public_path, GEN / 'hitter-count-error-diagnosis/diagnostic-rows.parquet',
             GEN / 'practical-hitter-v31/dated-stints.parquet', GEN / 'practical-hitter-v31/counts.parquet', GEN / 'foreign-origin-inputs/origin-inputs.json',
             ROOT / 'src/universal_baseball/hitter_error_geometry.py', ROOT / 'src/universal_baseball/hitter_evidence_representation.py',
             *[OUT / name for name in ['diagnostic-rows.parquet', 'attribution.json', 'player-decomposition.json']]]
    save('receipt.json', dict(new_fits=0, original_rows=30506, additions_separate=13, unchanged_PA=True, unchanged_forecasts=True,
                              source_profiles_independently_reconstructed=True, profiles_match_prior_source_only_diagnosis=True,
                              labels_independently_reconstructed=True, every_row_geometry_independently_verified=True, partition_identities_verified=True,
                              sealed_model_hashes_checked=fit['new_heads'], inherited_full_source_model_walks=17, protected_outcomes_used=False,
                              completed_2026_evaluation_unchanged=True, deployment_approved=False, player_walkthrough_status='pending_readable_review',
                              hashes={str(p): sha256_file(p) for p in paths}))
    print(json.dumps(dict(scores=scores, contrasts={a: contrasts[a]['global_MSE_terms'] for a in contrasts}), indent=2))
    print('No fits; 30,506 original forecasts and 13 additions preserved. Readable review pending.')


if __name__ == '__main__':
    main()
