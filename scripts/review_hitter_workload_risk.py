"""Attribution and manual-review closeout without changing sealed fits or scores."""
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

from universal_baseball.storage import sha256_file
import fit_hitter_workload_risk as fit
from score_hitter_workload_risk import equal_year, paired

ROOT, OUT = fit.ROOT, fit.OUT
EVIDENCE = ROOT / 'reports/model-evidence/hitter-workload-risk'


def verify(paths):
    for path, digest in paths.items():
        assert sha256_file(Path(path)) == digest, path


def attribution():
    assert not (OUT / 'attribution.json').exists(), 'Preserve attribution receipt'
    verification = fit.read(OUT / 'verification.json')
    verify(verification['source_hashes'])
    verify(fit.read(OUT / 'fit-seal.json'))
    q = pl.read_parquet(OUT / 'scored-predictions.parquet')
    rule = (pl.col('reported_retired') == 1) | (pl.col('hard_unavailable') == 1)
    affected = q.filter(rule)
    # Check the policy relationship, not future outcomes; no outcome filters.
    assert (affected['preseason_p'] == 0).all()
    changed = q.with_columns(
        pl.when(rule).then(0).otherwise(pl.col('forest_q' + str(a)))
        .alias('attribution_q' + str(a)) for a in [10, 50, 90])
    quantiles = changed.select('attribution_q10', 'attribution_q50', 'attribution_q90').to_numpy()
    actual = changed['next_pa'].to_numpy()
    residual = actual[:, None] - quantiles
    alpha = np.array([.1, .5, .9])
    changed = changed.with_columns(pl.Series('attribution_pinball',
        np.maximum(residual * alpha, residual * (alpha - 1)).mean(axis=1)))
    assert changed.filter(~rule)['attribution_pinball'].equals(q.filter(~rule)['forest_pinball'])
    original = equal_year(q, 'risk_pinball') - equal_year(q, 'forest_pinball')
    adjusted = equal_year(changed, 'risk_pinball') - equal_year(changed, 'attribution_pinball')
    with threadpool_limits(limits=2):
        intervals = [dict(scope='all_reference_same_rule', **paired(changed, 'attribution', 'pinball')),
                     dict(scope='outside_rule_rows_diagnostic', **paired(q.filter(~rule), 'forest', 'pinball'))]
    paths = [OUT / 'verification.json', OUT / 'scored-predictions.parquet',
             ROOT / 'docs/hitter-workload-risk-attribution-check.md', Path(__file__)]
    note = dict(post_result_diagnostic=True, primary_unchanged=True,
        evaluation_rows=len(q), rule_rows=len(affected), rule_people=affected['player_id'].n_unique(),
        original_difference=original, same_rule_reference_difference=adjusted,
        rule_contribution=original-adjusted, share_of_original_gain=(original-adjusted)/original,
        outside_rule_rows=len(q.filter(~rule)),
        outside_rule_risk_pinball=equal_year(q.filter(~rule), 'risk_pinball'),
        outside_rule_forest_pinball=equal_year(q.filter(~rule), 'forest_pinball'),
        intervals=intervals,
        affected=affected.select('row_id', 'player_id', 'player_name', 'origin_year',
            'reported_retired', 'hard_unavailable', 'preseason_p', 'next_pa',
            'risk_pinball', 'forest_pinball').to_dicts(),
        source_hashes={str(p): sha256_file(p) for p in paths},
        limitations='Other mean, feature and participation differences remain; not a spread-only contrast')
    fit.write('attribution.json', note)
    print(json.dumps({k: v for k, v in note.items() if k not in ['affected', 'source_hashes']}, indent=2))


def finalize():
    verification = fit.read(OUT / 'verification.json')
    verify(verification['source_hashes'])
    verify(fit.read(OUT / 'fit-seal.json'))
    attribution = fit.read(OUT / 'attribution.json')
    verify(attribution['source_hashes'])
    cases = fit.read(OUT / 'cases.json')
    review_path = ROOT / 'config/hitter_workload_risk_review.json'
    notes = fit.read(review_path)
    assert set(notes['players']) == {str(c['origin']['row_id']) for c in cases}
    assert all(len(v) > 160 for v in notes['players'].values())
    assert notes['current_candidate_changed'] is False
    assert notes['deployment_approved'] is False
    assert notes['full_goal_complete'] is False
    assert len(cases) == 14 and verification['all_current_columns_exact']
    doc = ROOT / 'docs/hitter-workload-risk-player-walkthrough.md'
    text = doc.read_text(encoding='utf8')
    assert all(c['origin']['player_name'] in text and str(c['origin']['row_id']) in text for c in cases)
    complete = [dict(row_id=c['origin']['row_id'], player_id=c['origin']['player_id'],
        player_name=c['origin']['player_name'], origin_year=c['origin']['origin_year'],
        selection=c['selection'], baseball_review=notes['players'][str(c['origin']['row_id'])]) for c in cases]
    fit.write('reviewed-cases.json', complete)
    review_paths = [review_path, doc, ROOT / 'docs/hitter-workload-risk-result.md',
                   OUT / 'reviewed-cases.json', OUT / 'attribution.json',
                   OUT / 'concentrations.json', Path(__file__)]
    final = dict(execution_integrity=True, evaluation_rows=30506,
        nested_contexts=verification['nested_contexts'],
        unique_nested_heads_replayed=verification['nested_heads_replayed'],
        concentration_fits_replayed=verification['concentrations_replayed'],
        point_heads_replayed=verification['case_point_heads_replayed'],
        independent_scalar_quantiles=verification['independent_case_quantiles'],
        player_walkthrough_status='complete', reviewed_cases=len(complete),
        walkthrough_path=str(doc), predictive_disposition=notes['disposition'],
        support_claim=notes['support_claim'], baseball_limits=notes['baseball_limits'],
        current_candidate_changed=False, deployment_approved=False, full_goal_complete=False,
        protected_outcomes_used=False, frozen_forecast_changed=False,
        all_current_forecasts_exact=True, distribution_is_workload_only=True,
        source_and_execution_hashes=verification['source_hashes'],
        review_hashes={str(p): sha256_file(p) for p in review_paths})
    final_path = OUT / 'final-report.json'
    if final_path.exists():
        assert fit.read(final_path) == final, 'Do not overwrite a different completed review'
    else:
        fit.write('final-report.json', final)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    filenames = ['preflight.json', 'fit-seal.json', 'scores.json', 'intervals.json',
                 'concentrations.json', 'verification.json', 'attribution.json',
                 'cases.json', 'reviewed-cases.json', 'final-report.json']
    for filename in filenames:
        source, target = OUT / filename, EVIDENCE / filename
        if target.exists():
            assert sha256_file(target) == sha256_file(source), target
        else:
            shutil.copyfile(source, target)
    # Receipts are separate from the original fit and verification files, which
    # truthfully record that review was pending when those steps completed.
    print('Fourteen player reviews complete; research-only result; current forecasts unchanged.')


if __name__ == '__main__':
    {'attribution': attribution, 'finalize': finalize}[sys.argv[1]]()
