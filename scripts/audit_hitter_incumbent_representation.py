"""Replay the actual incumbent branches before replacing their representation.

No fit, outcome-based feature selection, counterfactual promotion or 2026 access.
The readable review must accompany these mechanical receipts.
"""
from pathlib import Path
import json

import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

from prepare_practical_hitter_v33 import safe_matrix
from universal_baseball.storage import sha256_file

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / 'reports/generated'
OUT = GENERATED / 'hitter-incumbent-representation-audit'
BASE = GENERATED / 'practical-hitter-numeric-repair-v53'
BRIDGE = GENERATED / 'hitter-talent-bridge-v74'
TRACKING = GENERATED / 'hitter-statcast-next-year'
WORKLOAD = GENERATED / 'hitter-preseason-readiness-v68'
CURRENT = GENERATED / 'hitter-minor-statcast-precision/scored-predictions.parquet'
FAILED = GENERATED / 'hitter-overseas-integration'
CASES = [
    (670541, 2018), (643217, 2017), (660271, 2018), (808982, 2024),
    (807799, 2024), (592450, 2024), (592450, 2016), (701762, 2024),
    (665487, 2022), (656555, 2023), (474832, 2023), (673548, 2021),
    (660271, 2017), (807799, 2022), (808982, 2023), (541650, 2017),
    (527038, 2016), (460131, 2016),
]


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def save(path, value):
    assert not path.exists(), f'Preserve completed evidence: {path}'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False,
                              allow_nan=False, default=str) + '\n', encoding='utf8', newline='\n')


def load_head(directory, year, fold, field, value):
    receipt = read(directory / f'fit-{year}-{fold}.json')
    head = next(h for h in receipt['heads'] if h.get(field) == value)
    assert sha256_file(Path(head['path'])) == head['sha256'], head['path']
    return joblib.load(head['path']), head


def trace(model, row, names):
    x = safe_matrix(row, names)[0]
    effects = x * model.coef_
    prediction = float(model.intercept_ + effects.sum())
    assert np.isclose(prediction, model.predict(x[None, :])[0], atol=1e-10, rtol=0)
    terms = [dict(feature=n, raw_input=float(row[n][0]), fixed_scale_input=float(v),
                  coefficient=float(b), effect=float(e))
             for n, v, b, e in zip(names, x, model.coef_, effects, strict=True)]
    keep = sorted(terms, key=lambda t: abs(t['effect']), reverse=True)[:12]
    # Retain the specific features implicated in the failed fit, even if their
    # incumbent contribution is small. Selection is fixed before this replay.
    mandatory = {'pooled_DSL_BB', 'pooled_Aminus_BB', 'pooled_AAA_K',
                 'pooled_MLB_K', 'pooled_MLB_HR', 'sc_0_mean_ev', 'sc_0_ev95'}
    keep += [t for t in terms if t['feature'] in mandatory
             and t['feature'] not in {s['feature'] for s in keep}]
    return dict(prediction=prediction, intercept=float(model.intercept_),
                retained_terms=keep, omitted_terms_sum=float(effects.sum() - sum(t['effect'] for t in keep)),
                interpretation='Exact coefficient accounting, not causal importance')


def main():
    assert not OUT.exists(), 'Do not restart a completed audit'
    prior_review = read(FAILED / 'final-review.json')
    assert prior_review['player_walkthrough_status'] == 'complete'
    base_pre = read(BASE / 'preflight.json')
    bridge_pre = read(BRIDGE / 'preflight.json')
    tracking_pre = read(TRACKING / 'preflight.json')
    workload_pre = read(WORKLOAD / 'preflight.json')
    current = pl.read_parquet(CURRENT).sort('row_id')
    failed = pl.read_parquet(FAILED / 'predictions.parquet').sort('row_id')
    assert current.height == 30506 and current['target_year'].max() == 2025
    assert failed.filter(~pl.col('source_addition'))['row_id'].equals(current['row_id'])
    tracking = pl.read_parquet(TRACKING / 'features.parquet')
    workload = pl.read_parquet(WORKLOAD / 'features.parquet')
    bridge_predictions = pl.read_parquet(BRIDGE / 'scored-predictions.parquet').sort('row_id')
    counts = pl.read_parquet(GENERATED / 'practical-hitter-v31/counts.parquet')
    assert counts['season'].max() <= 2025
    base_names = base_pre['rate_features']
    bridge_names = bridge_pre['features']['translated_ridge']
    tracking_names = tracking_pre['arms']['ridge_measurements']
    workload_names = workload_pre['pa_features']
    assert (len(base_names), len(bridge_names), len(tracking_names), len(workload_names)) == (199, 220, 262, 251)
    checks, cases, seen, model_hashes = [], [], set(), {}
    with threadpool_limits(limits=2):
        for cell in workload_pre['cells']:
            y, k = cell['year'], cell['fold']
            q = current.filter(pl.col('row_id').is_in(cell['test_row_ids'])).sort('row_id')
            t = tracking.filter(pl.col('row_id').is_in(q['row_id'])).sort('row_id')
            b = pl.read_parquet(BRIDGE / f'features-{k}.parquet').filter(pl.col('row_id').is_in(q['row_id'])).sort('row_id')
            w = workload.filter(pl.col('row_id').is_in(q['row_id'])).sort('row_id')
            assert q['row_id'].equals(t['row_id']) and q['row_id'].equals(b['row_id']) and q['row_id'].equals(w['row_id'])
            specifications = [('base', BASE, 'head', 'rate', t, base_names),
                              ('prospect', BRIDGE, 'arm', 'translated_ridge', b, bridge_names),
                              ('tracking', TRACKING, 'arm', 'ridge_measurements', t, tracking_names)]
            raw, models = {}, {}
            for name, directory, field, value, frame, features in specifications:
                model, h = load_head(directory, y, k, field, value)
                assert model.__class__.__name__ == 'Ridge', 'Incumbent is not standardized Ridge'
                raw[name] = model.predict(safe_matrix(frame, features))
                models[name] = model
                model_hashes[h['path']] = h['sha256']
            assert np.allclose(raw['base'], q['preseason_rate'], atol=1e-10, rtol=0)
            bp = bridge_predictions.filter(pl.col('row_id').is_in(q['row_id'])).sort('row_id')
            assert np.allclose(raw['prospect'], bp['translated_ridge_all_rate'], atol=1e-10, rtol=0)
            assert np.allclose(raw['tracking'], q['ridge_measurements_raw_rate'], atol=1e-10, rtol=0)
            routed = np.where(q['prior_debut'].to_numpy() == 0, raw['prospect'],
                              np.where(t['sc_tracked'].to_numpy(), raw['tracking'], raw['base']))
            assert np.allclose(routed, q['combined_rate'], atol=1e-10, rtol=0)
            job = {}
            for head in ['participation', 'conditional_pa']:
                model, h = load_head(WORKLOAD, y, k, 'head', head)
                x = w.select(workload_names).to_numpy()
                p = model.predict_proba(x)[:, 1] if head == 'participation' else model.predict(x)
                expected = q['preseason_raw_p' if head == 'participation' else 'preseason_raw_conditional_pa']
                assert np.allclose(p, expected, atol=1e-10, rtol=0)
                job[head] = p
                model_hashes[h['path']] = h['sha256']
            assert np.allclose(q['preseason_pa'], q['preseason_p'] * q['preseason_conditional_pa'], atol=1e-10, rtol=0)
            assert np.allclose(q['combined_value'], q['preseason_pa'] * (routed / 600 + q['origin_replacement_rate']), atol=1e-10, rtol=0)
            checks.append(dict(origin=y, fold=k, rows=q.height, heads_replayed=5,
                               target_cutoff=y, future_MLB_labels_through=2025))
            for pid, origin in CASES:
                r = q.filter((pl.col('player_id') == pid) & (pl.col('origin_year') == origin))
                if r.is_empty():
                    continue
                a = r.row(0, named=True)
                seen.add((pid, origin))
                rid = a['row_id']
                route = 'prospect' if a['prior_debut'] == 0 else 'tracking' if a['sc_tracked'] else 'base'
                frame, names = (b, bridge_names) if route == 'prospect' else (t, tracking_names) if route == 'tracking' else (t, base_names)
                old = failed.filter(pl.col('row_id') == rid).row(0, named=True)
                cases.append(dict(player_id=pid, player_name=a['player_name'], origin_year=origin,
                    row_id=rid, outer_fold=k, information_date=cell['information_date'], branch=route,
                    age=a['age'], recent_MLB_PA=[a[f'pa_{lag}'] for lag in range(3)],
                    current=dict(rate=a['combined_rate'], probability=a['preseason_p'],
                                 conditional_PA=a['preseason_conditional_pa'], PA=a['preseason_pa'], value=a['combined_value']),
                    failed=dict(domestic_rate=old['domestic_rate'], overseas_rate=old['overseas_rate'],
                                domestic_PA=old['domestic_pa'], overseas_PA=old['overseas_pa']),
                    actual=dict(PA=a['next_pa'], rate=a['next_batting_rate'] if a['next_pa'] else None,
                                value=a['next_value']),
                    incumbent_trace=trace(models[route], frame.filter(pl.col('row_id') == rid), names),
                    history=counts.filter((pl.col('player_id') == pid) & pl.col('season').is_between(origin - 2, origin)).sort('season','bucket').to_dicts()))
            print(f'{y}/{k}: three talent and two job heads replayed, exact current routing.', flush=True)
    missing = [dict(player_id=pid, origin_year=y, reason='No incumbent forecast; old absence is not zero')
               for pid, y in CASES if (pid, y) not in seen]
    assert len(checks) == 35 and sum(c['rows'] for c in checks) == 30506
    inputs = [Path(__file__), CURRENT, FAILED/'final-review.json', FAILED/'predictions.parquet',
              BASE/'preflight.json', BRIDGE/'preflight.json', TRACKING/'preflight.json', WORKLOAD/'preflight.json',
              TRACKING/'features.parquet', WORKLOAD/'features.parquet', BRIDGE/'scored-predictions.parquet',
              ROOT/'scripts/prepare_practical_hitter_v33.py', ROOT/'scripts/fit_hitter_statcast_next_year.py',
              ROOT/'scripts/evaluate_hitter_talent_bridge_v74.py', ROOT/'scripts/fit_hitter_overseas_integration.py']
    inputs += [BRIDGE/f'features-{k}.parquet' for k in range(5)]
    report = dict(status='incumbent_replayed_representation_inventory', rows=30506,
        cells=checks, heads_replayed=175, case_selection='Fixed known design failures and ordinary/nonarrival controls; no new outcome ranking',
        cases=cases, missing_cases=missing, new_fits=0, protected_outcomes_used=False,
        frozen_forecast_changed=False, deployment_approved=False, broad_goal_achieved=False,
        target='Next calendar year MLB batting wins per 600 PA relative to future MLB environment; delivered batting plus replacement wins, not full WAR',
        routing='No prior MLB debut: translated prospect Ridge. Prior debut and any 3-year MLB tracking: MLB measurement Ridge. Otherwise numeric history Ridge.',
        representation=dict(original_rate_features=199, prospect_features=220, MLB_tracking_features=262,
                            job_features=251, scaler='Fixed physical units, no learned StandardScaler',
                            conditional_rate_weight='Origin row balancing times uncapped future PA, globally normalized',
                            failed_rate_weight='PA capped at 300; each origin gets equal total weight',
                            changes_not_isolated=['scaling','training weights','feature families','dated context','single integrated versus routed rate heads'],
                            raw_minor_rate_fields=105, positive_minor_tracking_in_current=False,
                            full_park_or_opponent_neutrality=False),
        input_hashes={str(p):sha256_file(p) for p in inputs}, saved_model_hashes=model_hashes,
        player_walkthrough_status='pending_readable_inventory_review')
    save(OUT/'inventory.json', report)
    print(f'Incumbent inventory saved: 175 heads, {len(cases)} available fixed cases, {len(missing)} absent cases; no fits.', flush=True)


if __name__ == '__main__':
    main()
