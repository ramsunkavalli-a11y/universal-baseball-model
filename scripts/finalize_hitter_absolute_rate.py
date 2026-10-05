"""Seal absolute-rate result after twenty actual source/model reviews."""
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.storage import sha256_file
from run_hitter_absolute_rate import ROOT, GEN, OUT, PREVIOUS, read, verify, save
from finalize_hitter_mlb_detail_restoration import paired_points


def main():
    public = ROOT / 'reports/model-evidence/hitter-absolute-rate/report.json'
    assert not public.exists() and not (OUT / 'final-review.json').exists()
    pre = read(OUT / 'preflight.json'); verify(pre['source_hashes'])
    source = read(OUT / 'source-review.json'); verify(source['hashes']); assert source['source_walkthrough_status'] == 'complete'
    receipt = read(OUT / 'review-receipt.json'); verify(receipt['hashes'])
    fit = read(OUT / 'fit-report.json')
    for c in fit['cells']:
        verify(c['hashes'])
    verify(read(GEN / 'hitter-count-error-diagnosis/receipt.json')['hashes'])
    assert pre['checks_before_fits'] == fit['new_heads'] == receipt['heads_replayed'] == 105
    assert receipt['independent_headline_equations'] == 12
    assert receipt['original_columns_preserved'] and receipt['PA_exactly_fixed'] and receipt['labels_independently_reconstructed']
    walks = read(OUT / 'player-walks.json')['cases']; assert len(walks) == len({r['row_id'] for r in walks}) == 20
    assert set(pre['fixed_case_row_ids']) <= {r['row_id'] for r in walks} and len(pre['fixed_case_row_ids']) == 17
    docs = [ROOT / f'docs/hitter-absolute-rate-{n}.md' for n in ['result', 'player-review']]
    content = docs[1].read_text(encoding='utf8')
    cases = []
    for r in walks:
        o = r['forecast']
        assert str(r['row_id']) in content and r['information_date'] in content and o['player_name'].split()[-1].rstrip('.') in content
        assert np.isclose(r['fitted_intercept'] + sum(t['effect'] for t in r['feature_terms']), o['absolute_rate'], atol=1e-10)
        assert r['new_offset'] == 0 and np.isclose(r['removed_baseline_effect'], -r['previous_baseline'], atol=1e-10)
        assert np.isclose(r['removed_baseline_effect'] + r['relearned_coefficient_change'], o['absolute_rate'] - o['components_rate'], atol=1e-10)
        assert r['origin_production_selected_comparisons'] and len(r['joint_support']) == 2
        assert r['raw_history'] or r['source']['contributions']
        for arm, g in r['geometry'].items():
            if o['next_pa']:
                assert np.isclose(g['hitting'] + g['opportunity'], g['error'], atol=1e-10)
            else:
                assert g['hitting'] is None and g['opportunity'] is None
        # Public inactive rate is unobserved, unlike the legacy internal zero label.
        forecast = dict(o)
        if not o['next_pa']:
            forecast['actual_relative_rate'] = forecast['actual_common_rate'] = None
        cases.append(dict(r, forecast=forecast))
    scores = read(OUT / 'scores.json'); overall = scores['scopes'][0]['scores']; points = {}
    for anchor in ['current', 'components']:
        assert all(overall['absolute'][metric] > overall[anchor][metric] for metric in ['rate_rmse', 'value_rmse'])
    q = pl.read_parquet(OUT / 'predictions.parquet').sort('row_id')
    previous = pl.read_parquet(PREVIOUS / 'predictions.parquet').sort('row_id'); assert q.select(previous.columns).equals(previous)
    original = q.filter(~pl.col('source_addition')); assert original.height == 30506
    assert q['absolute_pa'].equals(q['components_pa']) and q.filter(pl.col('source_addition')).height == 13
    for anchor in ['current', 'scalar', 'count', 'restored', 'components']:
        p = paired_points(original, 'absolute', anchor)
        for metric in ['rate', 'value']:
            assert np.isclose(p[metric], scores['intervals'][anchor][metric]['change'], atol=1e-12)
        points[anchor] = p
    paths = [Path(__file__), ROOT / 'scripts/finalize_hitter_mlb_detail_restoration.py', *docs,
             GEN / 'hitter-count-error-diagnosis/diagnostic-rows.parquet', PREVIOUS / 'profile-support.parquet', PREVIOUS / 'feature-ranges.json',
             *[OUT / n for n in ['preflight.json', 'source-review.json', 'fit-seal.json', 'fit-report.json', 'review-receipt.json', 'scores.json', 'player-walks.json', 'predictions.parquet']]]
    final = dict(player_walkthrough_status='complete', cases=20, fixed_cases_retained=17, new_heads=105, original_population=30506, source_additions_separate=13,
                 integrity_status='105 preflights and replays, original forecasts, source labels and twelve headline equations checked',
                 independent_paired_MSE_points=points, profile_support_status='Qualified; unchanged joint support gaps and ranges are retained',
                 physical_rate_envelope_pass=not scores['physical_envelope_violations'],
                 predictive_status='Both primary replacement requirements fail; nominal exposed-development intervals remain uncertain',
                 reasonability_status='Twenty full source/model walks completed; mature and foreign gains trade against prospect/recent-arrival losses and PA compensation',
                 disposition='Retain incumbent; close offset comparison without a prior/offset sweep or favorable-cohort hybrid',
                 protected_outcomes_used=False, completed_2026_evaluation_unchanged=True, deployment_approved=False, research_goal_remains_active=True,
                 hashes={str(p): sha256_file(p) for p in paths})
    public.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(final, scores=dict(scores, player_walkthrough_status='complete'), player_cases=cases,
                   readable_result='docs/hitter-absolute-rate-result.md', readable_walks='docs/hitter-absolute-rate-player-review.md',
                   raw_intermediate_status='Pending markers in sealed intermediate receipts retained; this final review records completion')
    public.write_text(json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf8', newline='\n')
    save('final-review.json', dict(final, public_report=str(public), public_report_sha256=sha256_file(public)))
    print('Absolute-rate comparison complete: 105 replays, 20 actual walks, five paired contrasts. Incumbent and 2026 evaluation unchanged.')


if __name__ == '__main__':
    main()
