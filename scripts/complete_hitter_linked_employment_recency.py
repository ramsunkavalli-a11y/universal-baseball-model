"""Append a reviewed negative disposition, without changing fits or forecasts."""
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.linked_employment_recency import profiles
from universal_baseball.storage import sha256_file
from prepare_hitter_overseas_integration import ANCHOR
from run_hitter_linked_employment_recency import ROOT, OUT, read, verify

PUBLIC = ROOT / 'reports/model-evidence/hitter-linked-employment-recency'
JUDGMENTS = {
    47261: 'Tatis: useful directional repair but still implausibly near exit. Career talent is retained; appearance probability, not hitting, limits PA. One training peer cannot certify return behavior.',
    51083: 'Hoskins: the stronger existing employment model already recognized his return. This change worsens PA and must not receive credit for the old 26-to-367 correction.',
    29177: 'Kang: removing staleness raises a historical organizational link despite unresolved nonmedical evidence. No matching training person supports this intersection. This is the opposite-risk failure, not grounds for a named-player exemption.',
    32183: 'Ellsbury: a 40-man/activation record is not evidence of medical recovery. Both models allocate substantial PA despite a missed season; removing staleness does not repair the availability distinction.',
    51341: 'Lux: existing employment already gives high participation; conditional workload remains below the later 487 PA. The replacement changes little and does not establish a new recovery model.',
    50571: 'Belt: known recent production supports some chance of returning despite a recorded release. His zero outcome is not a reason to force every unsigned productive veteran to zero. Raw input is unchanged; retraining nevertheless increases PA.',
    44435: 'Kwan: 341 upper-minor PA and 31 strikeouts are known, but this employment change barely affects his forecast. Conditional PA and fixed hitting remain misses. Peers match MLB experience/link but not minor quality; they cannot certify a contact-profile comparison.',
    54849: 'Judge before 2025: established hitting survives and participation is almost certain. Conditional PA increases eleven, improving this case; it is not evidence of a solved star/workload forecast.',
    42839: 'Albies: largest contribution harm. A high-PA young regular reasonably has substantial expected work; the new probability rises from 90% to 96% and worsens his later low-workload outcome. Do not use later events to force a low preseason forecast.',
    23934: 'Judge before 2017: largest false low remains. The model knows 410 AAA PA/19 HR and a poor 95-PA debut; the new job-age input does not solve either conditional workload or fixed hitting. MLB-only peer distance is inadequate for prospect hitting comparisons.',
    51153: 'Acuna: largest false high. His 735-PA/41-HR season supports substantial preseason opportunity, not foreknowledge of a later interruption. The two forecasts are almost the same; this is not evidence that removing staleness caused the whole miss.',
    46577: 'Slater: an ordinary contribution match conceals opposing errors. Candidate predicts 301 PA versus 207 actual, while fixed batting rate is too low. An almost exact contribution is not accurate opportunity and talent estimation.',
}


def reconstruct_scores(g, arm):
    # Group-first aggregation, separate from the row-weight helper used to score.
    pa = pl.col(arm + '_pa') - pl.col('next_pa')
    value = pl.col(arm + '_value') - pl.col('actual_relative_value')
    prob = pl.col(arm + '_p')
    yes = (pl.col('next_pa') > 0).cast(pl.Float64)
    clipped = prob.clip(1e-12, 1 - 1e-12)
    expressions = [(pa ** 2).mean().alias('pa_mse'), pa.abs().mean().alias('pa_mae'),
        pa.mean().alias('pa_bias'), (value ** 2).mean().alias('value_mse'),
        value.abs().mean().alias('value_mae'), value.mean().alias('value_bias'),
        ((prob - yes) ** 2).mean().alias('brier'),
        (-yes * clipped.log() - (1 - yes) * (1 - clipped).log()).mean().alias('logloss')]
    r = g.group_by('origin_year').agg(expressions).select(pl.exclude('origin_year').mean()).row(0, named=True)
    r['pa_rmse'] = np.sqrt(r.pop('pa_mse'))
    r['value_rmse'] = np.sqrt(r.pop('value_mse'))
    r.update(expected_pa=g[arm + '_pa'].sum(), expected_arrivals=g[arm + '_p'].sum(),
             expected_value=g[arm + '_value'].sum())
    return r


def main():
    assert not PUBLIC.exists(), 'Preserve completed evidence'
    receipt = read(OUT / 'review-receipt.json')
    verify(receipt['hashes'])
    pre, fit, scores = read(OUT / 'preflight.json'), read(OUT / 'fit-report.json'), read(OUT / 'scores.json')
    verify(pre['hashes'])
    for c in fit['cells']:
        verify(c['hashes'])
    assert receipt['heads_replayed'] == 140 and receipt['hitting_exactly_fixed']
    q = pl.read_parquet(OUT / 'predictions.parquet')
    context = profiles(pl.read_parquet(OUT / 'features-0.parquet')).select('row_id',
        'prior_regular_evidence', 'current_MLB_present', 'status_major_link',
        'employment_evidence_age_years', 'unlinked_employment_age_years')
    q = q.join(context, on='row_id', validate='1:1')
    original = q.filter(~pl.col('source_addition'))
    public = original.join(pl.read_parquet(ANCHOR, columns=['row_id', 'steamer_pa', 'steamer_index', 'zips_index']),
        on='row_id', how='left', validate='1:1').filter((pl.col('pa_0') > 0) &
        pl.col('steamer_index').is_not_null() & pl.col('zips_index').is_not_null())
    absent = original.filter(~pl.col('current_MLB_present') & pl.col('prior_regular_evidence'))
    scopes = dict(original_all=original, public=public, additions=q.filter(pl.col('source_addition')),
        current_regular=original.filter(pl.col('pa_0') >= 400), absent_former_regular=absent,
        absent_linked=absent.filter(pl.col('status_major_link') > 0),
        absent_unlinked=absent.filter(pl.col('status_major_link') == 0),
        input_changed=original.filter(pl.col('employment_evidence_age_years') != pl.col('unlinked_employment_age_years')),
        nonparticipants=original.filter(pl.col('next_pa') == 0))
    scopes.update({f'origin_{y}': original.filter(pl.col('origin_year') == y) for y in original['origin_year'].unique()})
    scopes.update({f'stage_{s}': original.filter(pl.col('stage') == s) for s in original['stage'].unique()})
    scopes.update({f'never_{s}': original.filter((pl.col('stage') == s) & (pl.col('prior_debut') == 0))
                   for s in ['Upper minors', 'Lower minors']})
    equations = 0
    for s in scores['scopes']:
        g = scopes[s['scope']]
        assert g.height == s['rows'] and g['next_pa'].sum() == s['actual_PA']
        for arm, saved in s['scores'].items():
            for metric, actual in reconstruct_scores(g, arm).items():
                assert np.isclose(actual, saved[metric], atol=1e-10, rtol=1e-12), (s['scope'], arm, metric)
                equations += 1
            for active, field in [(True, 'PA_to_participants'), (False, 'PA_to_nonparticipants')]:
                total = g.filter((pl.col('next_pa') > 0) == active)[arm + '_pa'].sum()
                assert np.isclose(total, s['allocations'][arm][field], atol=1e-8)
    walks = read(OUT / 'player-walks.json')['cases']
    assert set(JUDGMENTS) == {c['row_id'] for c in walks}
    assert set(pre['fixed_cases']).issubset(JUDGMENTS)
    reviewed = []
    for c in walks:
        o = c['forecast']
        assert o['target_year'] == o['origin_year'] + 1 and o['target_year'] <= 2025
        for arm in ['observation', 'recency']:
            assert np.isclose(o[arm + '_pa'], o[arm + '_p'] * o[arm + '_conditional_pa'], atol=1e-9)
            assert np.isclose(o[arm + '_value'], o[arm + '_pa'] * (o[arm + '_rate'] / 600 + o['origin_replacement_rate']), atol=1e-9)
            for head in ['participation', 'conditional_pa']:
                t = c['head_paths'][arm + '_' + head]
                assert np.isclose(t['reference'] + sum(e['path_effect'] for e in t['feature_effects']),
                                  t['raw_prediction'], atol=1e-8)
        for lag in range(3):
            known = sum(s['plate_appearances'] for s in c['raw_three_year_stints']
                        if s['season'] == o['origin_year'] - lag and s['bucket'] == 'MLB')
            assert np.isclose(known, c['model_inputs'][f'MLB_{lag}_pa'], atol=1e-8)
        assert len(c['peers']) == min(3, c['peer_exact_count_before_limit'])
        assert all(p['forecast']['player_id'] != o['player_id'] and
                   p['forecast']['origin_year'] == o['origin_year'] for p in c['peers'])
        reviewed.append(dict(row_id=c['row_id'], player_id=o['player_id'], player_name=o['player_name'],
            origin=o['origin_year'], target=o['target_year'], fold=o['outer_fold'], cutoff=o['ctx_information_date'],
            selection=c['selection'], judgment=JUDGMENTS[c['row_id']],
            stats=c['raw_three_year_stints'],
            employment=dict(date=c['timing']['new_latest_date'], state=c['raw_employment']['state'],
                raw_age=c['raw_age'], transformed_age=c['transformed_age'], reported_major_link=c['reported_major_link'],
                on_40man=c['model_inputs']['on_40man']),
            fixed_rate=o['recency_rate'], actual_rate=c['actual_rate'], actual_pa=o['next_pa'],
            actual_value=o['actual_relative_value'],
            predictions={a: {n: o[a + '_' + n] for n in ['p', 'conditional_pa', 'pa', 'value']}
                         for a in ['current', 'observation', 'recency']},
            support=c['training_support'],
            head_accounting={name: dict(reference=t['reference'], prediction=t.get('linked_probability', t['raw_prediction']),
                largest_path_effects=t['feature_effects'][:5], interpretation=t['interpretation'])
                for name, t in c['head_paths'].items()},
            peers=[dict(player_id=p['forecast']['player_id'], player_name=p['forecast']['player_name'],
                distance=p['forecast']['origin_distance'], expected_pa=p['forecast']['recency_pa'],
                actual_pa=p['forecast']['next_pa'], raw_history=p['raw_three_year_stints']) for p in c['peers']],
            eligible_peer_count=c['peer_exact_count_before_limit']))
    by_scope = {s['scope']: s for s in scores['scopes']}
    allscores = by_scope['original_all']['scores']
    guardrails = {s['scope']: (s['scores']['recency']['pa_rmse'] / s['scores']['observation']['pa_rmse']) ** 2 - 1
                  for s in scores['scopes'] if s['scope'].startswith('stage_') or s['scope'] == 'current_regular'}
    gates = dict(primary_pa_improves=allscores['recency']['pa_rmse'] < allscores['observation']['pa_rmse'],
        contribution_nonworsening_both=all(allscores['recency']['value_rmse'] <= allscores[a]['value_rmse']
                                         for a in ['observation', 'current']),
        public_pa_mae_nonworsening=by_scope['public']['scores']['recency']['pa_mae'] <= by_scope['public']['scores']['observation']['pa_mae'],
        stage_regular_within_two_percent=all(d <= .02 for d in guardrails.values()),
        nominal_primary_interval_favors_improvement=next(r for r in scores['intervals']['original_all:observation']
                                                        if r['metric'] == 'pa_mse')['upper'] < 0)
    assert not gates['primary_pa_improves'] and not gates['stage_regular_within_two_percent']
    assert not gates['nominal_primary_interval_favors_improvement']
    selected = ROOT / 'model_artifacts/hitter-selected-2026-frozen-2026-10-05/freeze-manifest.json'
    final = ROOT / 'reports/model-evidence/hitter-final-2026/report.json'
    assert sha256_file(selected) == 'a1d819ffcdd98a9ee62feecf5637b5ebe1f93b6e931d77d2b7d692ed928da67a'
    assert sha256_file(final) == '8c2acfeb42ece7d109d3b35542a6b79ec372467d7027d5945a4ba800cde913bb'
    paths = [OUT / 'review-receipt.json', OUT / 'preflight.json', OUT / 'fit-report.json',
        OUT / 'scores.json', OUT / 'player-walks.json', OUT / 'predictions.parquet', OUT / 'support.parquet',
        ROOT / 'docs/hitter-linked-employment-recency-contract.md',
        ROOT / 'docs/hitter-linked-employment-recency-result.md',
        ROOT / 'docs/hitter-linked-employment-recency-player-review.md', Path(__file__), selected, final]
    report = dict(disposition='Reject this exact encoding; retain selected forecast and corrected employment facts',
        player_walkthrough_status='complete', deployment_approved=False, protected_2026_outcomes_used=False,
        forecasts_changed=False, new_heads=70, benchmark_and_candidate_replayed_heads=140,
        gates=gates, guardrail_PA_MSE_changes=guardrails, scopes=scores['scopes'], intervals=scores['intervals'],
        public_steamer=scores['public_steamer'], cases=reviewed,
        hitting='Exactly unchanged. The raw conditional rate metric is equally weighted within origin, unlike the previous PA-weighted hitting competence check; do not compare those numbers.',
        support_warning='Sparse comeback intersections remain: Tatis one full/active person, Kang zero, Ellsbury three. No universal comeback certification.',
        peer_warning='Predeclared peers fit the employment/career question, not minor hitting quality. Kwan/Judge debut peers omit minor talent and cannot validate those skill profiles.',
        independent_equations=equations, raw_pending_receipts_preserved=True,
        hashes={str(p): sha256_file(p) for p in paths})
    PUBLIC.mkdir(parents=True)
    (PUBLIC / 'report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf8', newline='\n')
    print(f'{len(reviewed)} walks complete; {equations} independent score/total equations. Exact encoding rejected; forecasts unchanged.')


if __name__ == '__main__':
    main()
