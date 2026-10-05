"""Seal completed seven-component evidence without upgrading forecasts."""
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.storage import sha256_file
from run_hitter_mlb_events_restoration import ROOT, OUT, read, verify, save
from finalize_hitter_mlb_detail_restoration import paired_points


def main():
    public = ROOT / 'reports/model-evidence/hitter-mlb-events-restoration/report.json'
    assert not public.exists() and not (OUT / 'final-review.json').exists()
    pre = read(OUT / 'preflight.json'); verify(pre['source_hashes'])
    source = read(OUT / 'source-review.json'); verify(source['hashes'])
    assert source['source_walkthrough_status'] == 'complete'
    receipt = read(OUT / 'review-receipt.json'); verify(receipt['hashes'])
    fit = read(OUT / 'fit-report.json')
    for c in fit['cells']:
        verify(c['hashes'])
    assert pre['checks_before_fits'] == receipt['heads_replayed'] == fit['new_heads'] == 105
    assert receipt['independent_headline_equations'] == 10
    assert receipt['original_columns_preserved'] and receipt['PA_exactly_fixed']
    assert receipt['labels_independently_reconstructed']
    walks = read(OUT / 'player-walks.json')['cases']
    assert len(walks) == len({r['row_id'] for r in walks}) == 17
    assert len(pre['fixed_case_row_ids']) == 17
    assert set(pre['fixed_case_row_ids']) == {r['row_id'] for r in walks}
    docs = [ROOT / f'docs/hitter-mlb-events-restoration-{n}.md' for n in ['result', 'player-review']]
    content = docs[1].read_text(encoding='utf8')
    for r in walks:
        o = r['forecast']
        assert o['player_name'].split()[-1] in content and str(r['row_id']) in content
        assert r['information_date'] in content
        assert np.isclose(r['past_baseline_rate'] + r['fitted_residual'], o['components_rate'], atol=1e-10)
        assert np.isclose(r['fitted_intercept'] + sum(t['effect'] for t in r['feature_terms']), r['fitted_residual'], atol=1e-10)
        assert np.isclose(r['added_MLB_component_effect'] + r['other_coefficient_change'], o['components_rate'] - o['restored_rate'], atol=1e-10)
        assert len(r['joint_MLB_component_support']) == 2 and r['origin_production_selected_comparisons']
    scores = read(OUT / 'scores.json'); overall = scores['scopes'][0]['scores']
    assert overall['components']['value_rmse'] > overall['current']['value_rmse']
    assert overall['components']['rate_rmse'] < overall['current']['rate_rmse']
    assert all(scores['intervals']['restored'][m]['upper'] < 0 for m in ['rate', 'value'])
    q = pl.read_parquet(OUT / 'predictions.parquet').filter(~pl.col('source_addition'))
    assert q.height == 30506
    points = {}
    for anchor in ['current', 'scalar', 'count', 'restored']:
        p = paired_points(q, 'components', anchor)
        for metric in ['rate', 'value']:
            assert np.isclose(p[metric], scores['intervals'][anchor][metric]['change'], atol=1e-12)
        points[anchor] = p
    paths = [Path(__file__), ROOT / 'scripts/finalize_hitter_mlb_detail_restoration.py', *docs,
             *[OUT / n for n in ['preflight.json', 'source-review.json', 'fit-seal.json', 'fit-report.json',
                                 'review-receipt.json', 'scores.json', 'player-walks.json', 'predictions.parquet']]]
    final = dict(player_walkthrough_status='complete', cases=17, fixed_cases_retained=17, new_heads=105,
                 original_population=30506, source_additions_separate=13,
                 integrity_status='Sources, preflight, hashes, replay, labels and score arithmetic checked',
                 independent_paired_MSE_points=points,
                 profile_support_status='Qualified; absent/sparse joint profiles retained, not certified by coordinate ranges',
                 physical_rate_envelope_pass=not scores['physical_envelope_violations'],
                 predictive_status='Both matched improvements supported by nominal development intervals; incumbent delivered requirement fails narrowly',
                 reasonability_status='Seventeen actual walks complete; mature-MLB, foreign transfer, breakout and workload/talent cancellation gaps remain',
                 disposition='Retain incumbent and preserve useful component evidence; no favorable-cohort blend or automatic forecast promotion',
                 protected_outcomes_used=False, completed_2026_evaluation_unchanged=True, deployment_approved=False,
                 research_goal_remains_active=True, hashes={str(p): sha256_file(p) for p in paths})
    cases = []
    for r in walks:
        o = r['forecast']
        cases.append(dict(row_id=r['row_id'], player_id=o['player_id'], player_name=o['player_name'],
                          origin=o['origin_year'], target=o['target_year'], fold=o['outer_fold'], branch=o['count_branch'],
                          information_date=r['information_date'], age=r['age'], why=r['why'], source=r['source'],
                          raw_history=r['raw_history'], MLB_source=r['MLB_source'], MLB_event_source=r['MLB_event_source'],
                          baseline_rate=r['past_baseline_rate'], fitted_intercept=r['fitted_intercept'], fitted_residual=r['fitted_residual'],
                          added_MLB_component_effect=r['added_MLB_component_effect'], other_coefficient_change=r['other_coefficient_change'],
                          feature_terms=r['feature_terms'], probes=r['probes'],
                          rates={a: o[a + '_rate'] for a in ['current', 'scalar', 'count', 'restored', 'components']},
                          actual_rate=o['actual_relative_rate'] if o['next_pa'] else None,
                          expected_PA=o['components_pa'], actual_PA=o['next_pa'],
                          values={a: o[a + '_value'] for a in ['current', 'scalar', 'count', 'restored', 'components']},
                          actual_value=o['actual_relative_value'], actual_counts=r['actual_counts'],
                          support=r['joint_MLB_component_support'], feature_extrapolations=r['added_feature_extrapolations'],
                          origin_selected_peers=[dict(p, actual_relative_rate=p['actual_relative_rate'] if p['next_pa'] else None)
                                                 for p in r['origin_production_selected_comparisons']]))
    public.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(final, scores=dict(scores, player_walkthrough_status='complete'), player_cases=cases,
                   raw_score_receipt_status='Pending marker in sealed intermediate receipt preserved; this final review records completion',
                   readable_result='docs/hitter-mlb-events-restoration-result.md', readable_walks='docs/hitter-mlb-events-restoration-player-review.md')
    public.write_text(json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf8', newline='\n')
    save('final-review.json', dict(final, public_report=str(public), public_report_sha256=sha256_file(public)))
    print('Seven-component comparison complete: 17 actual walks and four paired contrasts verified. Useful matched improvement, incumbent retained.')


if __name__ == '__main__':
    main()
