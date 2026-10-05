"""Seal the completed four-summary comparison without promoting a forecast."""
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.storage import sha256_file
from run_hitter_mlb_detail_restoration import ROOT, OUT, read, verify, save


def paired_points(q, candidate, anchor):
    """Independent equal-origin MSE contrasts, retaining inactive contribution."""
    rate, value = [], []
    for y in sorted(q['origin_year'].unique()):
        g = q.filter(pl.col('origin_year') == y)
        ce = (g[candidate + '_value'] - g['actual_relative_value']).to_numpy()
        ae = (g[anchor + '_value'] - g['actual_relative_value']).to_numpy()
        value.append(np.mean(ce * ce - ae * ae))
        g = g.filter(pl.col('next_pa') > 0)
        ce = (g[candidate + '_rate'] - g['actual_relative_rate']).to_numpy()
        ae = (g[anchor + '_rate'] - g['actual_relative_rate']).to_numpy()
        pa = g['next_pa'].to_numpy()
        rate.append(np.sum(pa * (ce * ce - ae * ae)) / pa.sum())
    return dict(rate=float(np.mean(rate)), value=float(np.mean(value)))


def main():
    public = ROOT / 'reports/model-evidence/hitter-mlb-detail-restoration/report.json'
    assert not (OUT / 'final-review.json').exists() and not public.exists()
    pre = read(OUT / 'preflight.json'); verify(pre['source_hashes'])
    source_review = read(OUT / 'source-review.json'); verify(source_review['hashes'])
    assert source_review['source_walkthrough_status'] == 'complete'
    receipt = read(OUT / 'review-receipt.json'); verify(receipt['hashes'])
    fit = read(OUT / 'fit-report.json')
    for cell in fit['cells']:
        verify(cell['hashes'])
    assert pre['checks_before_fits'] == receipt['heads_replayed'] == fit['new_heads'] == 105
    assert receipt['independent_headline_equations'] == 8
    assert receipt['original_columns_preserved'] and receipt['PA_exactly_fixed']
    assert receipt['labels_independently_reconstructed']
    walks = read(OUT / 'player-walks.json')['cases']
    assert len(walks) == len({r['row_id'] for r in walks}) == 17
    assert len(pre['fixed_case_row_ids']) == 16
    assert set(pre['fixed_case_row_ids']) <= {r['row_id'] for r in walks}
    docs = [ROOT / f'docs/hitter-mlb-detail-restoration-{n}.md'
            for n in ['result', 'player-review']]
    content = docs[1].read_text(encoding='utf8')
    for r in walks:
        o = r['forecast']
        assert o['player_name'].split()[-1] in content and str(r['row_id']) in content
        assert r['information_date'] in content
        assert np.isclose(r['past_baseline_rate'] + r['fitted_residual'], o['restored_rate'], atol=1e-10)
        assert np.isclose(r['fitted_intercept'] + sum(t['effect'] for t in r['feature_terms']), r['fitted_residual'], atol=1e-10)
        assert np.isclose(r['added_MLB_term_effect'] + r['other_coefficient_change'], o['restored_rate'] - o['scalar_rate'], atol=1e-10)
        assert r['origin_production_selected_comparisons'] and len(r['joint_MLB_quality_support']) == 2
    scores = read(OUT / 'scores.json'); overall = scores['scopes'][0]['scores']
    assert overall['restored']['value_rmse'] > overall['current']['value_rmse']
    assert overall['restored']['rate_rmse'] < overall['current']['rate_rmse']
    assert overall['restored']['value_rmse'] < overall['scalar']['value_rmse']
    q = pl.read_parquet(OUT / 'predictions.parquet').filter(~pl.col('source_addition'))
    assert q.height == 30506
    points = {}
    for anchor in ['current', 'count', 'scalar']:
        p = paired_points(q, 'restored', anchor)
        intervals = scores['matched_direct_interval'] if anchor == 'scalar' else scores['intervals'][anchor]
        for metric in ['rate', 'value']:
            assert np.isclose(p[metric], intervals[metric]['change'], atol=1e-12)
        points[anchor] = p
    paths = [Path(__file__), *docs, *[OUT / n for n in [
        'preflight.json', 'source-review.json', 'fit-seal.json', 'fit-report.json',
        'review-receipt.json', 'scores.json', 'player-walks.json', 'predictions.parquet']]]
    final = dict(
        player_walkthrough_status='complete', cases=17, fixed_cases_retained=16,
        new_heads=105, original_population=30506, source_additions_separate=13,
        integrity_status='Source reconstruction, hashes, preflight, replay and score arithmetic checked',
        independent_paired_MSE_points=points,
        physical_rate_envelope_pass=not scores['physical_envelope_violations'],
        profile_support_status='Qualified; joint full/active support remains sparse or absent in important foreign and lower-minor profiles',
        predictive_status='Fails declared incumbent delivered-value improvement requirement; partial recovery versus compressed direct/count arms',
        reasonability_status='Seventeen actual source/model walks reviewed; mature-MLB losses, breakout misses, foreign-transfer and rate/workload cancellations remain',
        disposition='Not adopted; retain incumbent, no cohort hybrid or forecast promotion',
        protected_outcomes_used=False, completed_2026_evaluation_unchanged=True,
        deployment_approved=False, research_goal_remains_active=True,
        hashes={str(p): sha256_file(p) for p in paths})
    cases = []
    for row in walks:
        o = row['forecast']
        cases.append(dict(
            row_id=row['row_id'], player_id=o['player_id'], player_name=o['player_name'],
            origin=o['origin_year'], target=o['target_year'], fold=o['outer_fold'],
            information_date=row['information_date'], age=row['age'], why=row['why'],
            branch=o['count_branch'], source=row['source'], raw_history=row['raw_history'],
            MLB_source=row['MLB_source'], baseline_rate=row['past_baseline_rate'],
            fitted_intercept=row['fitted_intercept'], fitted_residual=row['fitted_residual'],
            added_MLB_term_effect=row['added_MLB_term_effect'], other_coefficient_change=row['other_coefficient_change'],
            feature_terms=row['feature_terms'], probes=row['probes'],
            rates={a: o[a + '_rate'] for a in ['current', 'scalar', 'count', 'restored']},
            actual_rate=o['actual_relative_rate'] if o['next_pa'] else None,
            expected_PA=o['restored_pa'], actual_PA=o['next_pa'],
            values={a: o[a + '_value'] for a in ['current', 'scalar', 'count', 'restored']},
            actual_value=o['actual_relative_value'], actual_counts=row['actual_counts'],
            origin_selected_peers=row['origin_production_selected_comparisons'],
            support=row['joint_MLB_quality_support'], feature_extrapolations=row['added_feature_extrapolations']))
    public.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(final, scores=dict(scores, player_walkthrough_status='complete'),
                   raw_score_receipt_status='Preserved pre-readable-review artifact; completion is recorded in this final review',
                   player_cases=cases, readable_result='docs/hitter-mlb-detail-restoration-result.md',
                   readable_walks='docs/hitter-mlb-detail-restoration-player-review.md')
    public.write_text(json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf8', newline='\n')
    save('final-review.json', dict(final, public_report=str(public), public_report_sha256=sha256_file(public)))
    print('Four-summary comparison complete; 17 walks and three paired contrasts checked. Incumbent retained, frozen evaluation unchanged.')


if __name__ == '__main__':
    main()
