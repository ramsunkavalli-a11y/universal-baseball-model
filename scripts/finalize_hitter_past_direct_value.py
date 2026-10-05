"""Complete the fixed comparison after readable walks; never promote forecasts."""
import json
from pathlib import Path

from universal_baseball.storage import sha256_file
from run_hitter_past_direct_value import ROOT, OUT, read, verify, save


def main():
    assert not (OUT / 'final-review.json').exists()
    pre = read(OUT / 'preflight.json'); verify(pre['source_hashes'])
    review = read(OUT / 'review-receipt.json'); verify(review['hashes'])
    fit = read(OUT / 'fit-report.json')
    for cell in fit['cells']: verify(cell['hashes'])
    assert review['heads_replayed'] == fit['new_heads'] == 105 and review['independent_headline_equations'] == 6
    walks = read(OUT / 'player-walks.json')['cases']; assert len(walks) == len({r['row_id'] for r in walks}) == 16
    assert set(pre['fixed_case_row_ids']) <= {r['row_id'] for r in walks}
    docs = [ROOT / f'docs/hitter-past-direct-value-{name}.md' for name in ['result', 'player-review']]
    content = docs[1].read_text(encoding='utf8'); assert all(r['forecast']['player_name'].split()[-1] in content for r in walks)
    scores = read(OUT / 'scores.json'); overall = scores['scopes'][0]['scores']
    assert overall['scalar']['value_rmse'] > overall['current']['value_rmse']
    assert overall['scalar']['rate_rmse'] < overall['count']['rate_rmse']
    paths = [Path(__file__), *docs, *[OUT / n for n in ['preflight.json', 'fit-seal.json', 'fit-report.json', 'review-receipt.json', 'scores.json', 'player-walks.json', 'predictions.parquet']]]
    final = dict(player_walkthrough_status='complete', cases=16, fixed_cases_retained=13, new_heads=105,
        disposition='Not adopted; retain incumbent. Same-input direct rate recovers count hitting loss but does not beat incumbent delivered value.',
        original_population=30506, source_additions_separate=13, physical_rate_envelope_pass=not scores['physical_envelope_violations'],
        reasonability_status='Reviewed; mature-MLB loss, sparse foreign context and component cancellations remain',
        protected_outcomes_used=False, completed_2026_evaluation_unchanged=True, deployment_approved=False, research_goal_remains_active=True,
        hashes={str(p): sha256_file(p) for p in paths})
    save('final-review.json', final)
    public = ROOT / 'reports/model-evidence/hitter-past-direct-value/report.json'; assert not public.exists(); public.parent.mkdir(parents=True)
    cases = []
    for row in walks:
        o = row['forecast']
        cases.append(dict(row_id=row['row_id'], player_id=o['player_id'], player_name=o['player_name'], origin=o['origin_year'], fold=o['outer_fold'], why=row['why'],
            branch=o['count_branch'], source=row['source'], raw_history=row['raw_history'], baseline_rate=row['past_baseline_rate'],
            fitted_intercept=row['fitted_scalar_intercept'], fitted_residual=row['fitted_scalar_residual'], feature_terms=row['feature_terms'], probes=row['probes'],
            rates={a: o[a + '_rate'] for a in ['current', 'count', 'scalar']}, actual_rate=o['actual_relative_rate'] if o['next_pa'] else None,
            expected_PA=o['scalar_pa'], actual_PA=o['next_pa'], values={a: o[a + '_value'] for a in ['current', 'count', 'scalar']}, actual_value=o['actual_relative_value'],
            actual_counts=row['actual_counts'], origin_selected_peers=row['origin_production_selected_comparisons'], support=row['support'], feature_extrapolations=row['feature_extrapolations']))
    public.write_text(json.dumps(dict(final, scores=scores, player_cases=cases, readable_result='docs/hitter-past-direct-value-result.md', readable_walks='docs/hitter-past-direct-value-player-review.md'), indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf8', newline='\n')
    print('Matched direct-rate comparison complete, 16 walks reviewed; incumbent retained and no forecast promotion.')


if __name__ == '__main__':
    main()
