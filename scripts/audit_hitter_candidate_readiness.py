"""Reconcile completed hitter evidence without fitting or rescoring outcomes.

This checks recipe and receipt provenance, not predictive certification.
The completed 2026 report is read only for completion/hash/date metadata.
"""
import json
from datetime import datetime
from pathlib import Path

import joblib

from universal_baseball.storage import sha256_file

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / 'reports/generated'
EVIDENCE = ROOT / 'reports/model-evidence'
FROZEN = ROOT / 'model_artifacts/hitter-selected-2026-frozen-2026-10-05'
OUT = EVIDENCE / 'hitter-candidate-readiness/report.json'


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def ordered_feature_check(historical, frozen):
    if historical != frozen:
        raise ValueError('Ordered features differ; names/counts alone do not reconcile recipes')
    if len(set(frozen)) != len(frozen):
        raise ValueError('Duplicate feature names')
    return {'count': len(frozen), 'ordered_names_identical': True}


def evaluation_completion(manifest, manifest_sha, forecast_sha, completed):
    """Final receipt controls current status, not an earlier pending flag."""
    score, review = completed['scores'], completed['review_completion']
    if score['freeze_manifest_sha256'] != manifest_sha or score['forecast_sha256'] != forecast_sha:
        raise ValueError('Final evaluation does not identify this unchanged frozen forecast')
    if score['post_result_fit_or_tuning'] or not review['no_post_result_forecast_change']:
        raise ValueError('A post-result changed candidate is not the single frozen evaluation')
    if review['status'] != 'completed_single_frozen_evaluation_with_qualified_disposition':
        raise ValueError('Final evaluation is not recorded complete')
    if not review['future_2026_retesting_forbidden'] or review['player_walkthrough_status'] != 'complete':
        raise ValueError('Missing completion/retesting guard')
    if datetime.fromisoformat(score['scored_at_utc']) <= datetime.fromisoformat(manifest['frozen_at_utc']):
        raise ValueError('Evaluation must follow freezing')
    return dict(status='already_evaluated_once', frozen_at_utc=manifest['frozen_at_utc'],
                scored_at_utc=score['scored_at_utc'], forecasts_changed=False,
                predictive_superiority_established=review['predictive_superiority_established'],
                matched_2026_public_comparison_available=not review['public_matched_comparison_unavailable'],
                new_2026_scoring=False, old_pending_flags_are_not_current_status=True)


def main():
    if OUT.exists():
        raise RuntimeError('Preserve completed readiness evidence')
    paths = [Path(__file__), ROOT / 'docs/hitter-candidate-readiness-review-contract.md']
    manifest_path = FROZEN / 'freeze-manifest.json'
    manifest = read(manifest_path)
    manifest_sha = sha256_file(manifest_path)
    assert manifest_sha == (FROZEN / 'freeze-manifest.sha256').read_text().strip()
    for f in manifest['files']:
        assert sha256_file(FROZEN / f['path']) == f['sha256'], f['path']
    paths += [manifest_path, FROZEN / 'preflight.json']
    frozen_pre = read(FROZEN / 'preflight.json')
    source_specs = {
        'rate_numeric': ('practical-hitter-numeric-repair-v53', lambda p: p['rate_features']),
        'rate_tracking': ('hitter-statcast-next-year', lambda p: p['arms']['ridge_measurements']),
        'rate_prospect': ('hitter-talent-bridge-v74', lambda p: p['features']['translated_ridge']),
        'participation': ('hitter-preseason-readiness-v68', lambda p: p['pa_features']),
        'conditional_pa': ('hitter-preseason-readiness-v68', lambda p: p['pa_features']),
    }
    recipes = {}
    for head, (directory, select) in source_specs.items():
        p = GEN / directory / 'preflight.json'; paths.append(p)
        recipes[head] = dict(ordered_feature_check(select(read(p)), frozen_pre['features'][head]),
                             historical_source=str(p.relative_to(ROOT)), saved_parameters_identical=True,
                             historical_heads_checked=0, frozen_heads_checked=0)
    inventory_path = GEN / 'hitter-incumbent-representation-audit/inventory.json'
    inventory = read(inventory_path); paths.append(inventory_path)
    assert inventory['heads_replayed'] == 175 and inventory['rows'] == 30506
    production_params = {}
    for h in manifest['models']:
        model = joblib.load(FROZEN / h['path'])
        params = model.get_params(deep=False)
        identity = (type(model).__name__, params)
        if h['head'] in production_params:
            assert production_params[h['head']] == identity
        production_params[h['head']] = identity
        assert h['features'] == frozen_pre['features'][h['head']]
        recipes[h['head']]['frozen_heads_checked'] += 1
    for raw_path, digest in inventory['saved_model_hashes'].items():
        p = Path(raw_path); assert sha256_file(p) == digest, p
        head = next((h for h, (d, _) in source_specs.items()
                     if p.parent.name == d and (h not in ['participation', 'conditional_pa'] or p.name.startswith(h + '-'))), None)
        assert head is not None, p
        model = joblib.load(p)
        assert (type(model).__name__, model.get_params(deep=False)) == production_params[head], p
        recipes[head]['historical_heads_checked'] += 1
    for h, note in recipes.items():
        assert note['historical_heads_checked'] == 35 and note['frozen_heads_checked'] == 5
        note['model_family'], note['parameters'] = production_params[h]
    print('All five ordered feature lists and 175 historical / 25 frozen model recipes agree.', flush=True)

    final_path = EVIDENCE / 'hitter-final-2026/report.json'; paths.append(final_path)
    completed = read(final_path)
    completion = evaluation_completion(manifest, manifest_sha, sha256_file(FROZEN / 'forecast.parquet'), completed)
    # No outcome arrays, group scores or player outcomes are extracted here.
    assert not completion['predictive_superiority_established']

    experiment_specs = [
        ('absolute_rate', 'hitter-absolute-rate/report.json'),
        ('workload_risk', 'hitter-workload-risk/final-report.json'),
        ('talent_to_opportunity', 'hitter-talent-opportunity/final-report.json'),
        ('deeper_conditional_workload', 'hitter-positive-workload-capacity/final-report.json'),
        ('separate_entrant_workload', 'hitter-prospect-workload-specialization/completed-review.json'),
        ('available_season_history', 'hitter-available-season-history/final-report.json'),
        ('smooth_rankings', 'hitter-smooth-preseason-v73/report.json'),
        ('corrected_employment', 'hitter-employment-comparison-v2/report.json'),
        ('nonmedical_observation', 'hitter-nonmedical-opportunity/report.json'),
        ('incumbent_representation', 'hitter-incumbent-representation/final-review.json'),
    ]
    experiments = []
    for name, rel in experiment_specs:
        p = EVIDENCE / rel; paths.append(p); r = read(p)
        assert r['player_walkthrough_status'] == 'complete', name
        assert not r.get('protected_outcomes_used', False), name
        assert not r.get('deployment_approved', False), name
        experiments.append(dict(name=name, evidence=str(p.relative_to(ROOT)),
                                player_walkthrough_status='complete', deployment_approved=False))
    absolute = read(EVIDENCE / 'hitter-absolute-rate/report.json')
    scores = absolute['scores']; overall = next(s for s in scores['scopes'] if s['scope'] == 'all')
    assert overall['rows'] == 30506 and overall['active_rows'] == 4538
    assert all(s['expected_PA'] == overall['scores']['current']['expected_PA'] for s in overall['scores'].values())
    representation_path = GEN / 'hitter-mlb-events-restoration/preflight.json'; paths.append(representation_path)
    challenger_counts = {k: len(v) for k, v in read(representation_path)['arms'].items()}
    assert challenger_counts == {'base': 123, 'prospect': 132, 'tracking': 186}
    pa_path = EVIDENCE / 'hitter-talent-opportunity/scores.json'; paths.append(pa_path)
    pa_scores = read(pa_path)
    public = next(s for s in pa_scores if s['scope'] == 'public')
    # These PA scores can be reconciled; their legacy offense reference cannot
    # be inserted into the compatible batting-contribution ledger above.
    assert public['rows'] == 2627
    workload_scopes = []
    for s in pa_scores:
        workload_scopes.append(dict(scope=s['scope'], rows=s['rows'],
                                    expected_PA=s['scores']['current']['expected_pa'], actual_PA=s['actual_pa'],
                                    expected_appearances=s['scores']['current']['expected_appearances'],
                                    actual_appearances=s['actual_appearances']))
    receipt = dict(
        status='completed_evidence_reconciliation_not_model_validation', new_fits=0, new_scores=0,
        raw_2026_outcomes_accessed=False, existing_final_evaluation_metadata_read=True,
        historical_recipe_matches_frozen=recipes, saved_recipe_models_checked=200,
        training_coefficients_identical_claim=False,
        training_qualification='Same recipes, different cutoffs and training sets; production source gates and origin-2020 membership repair remain in the frozen receipts.',
        frozen_manifest_sha256=manifest_sha, frozen_files_verified=len(manifest['files']),
        frozen_population=manifest['population'], evaluation_completion=completion,
        representation_challenger_feature_counts=challenger_counts,
        historical_original_population=overall['rows'], compatible_contribution_reference=overall,
        incumbent_workload_cohort_totals=workload_scopes,
        incumbent_public_workload=dict(rows=public['rows'], pa_rmse=public['scores']['current']['pa_rmse'],
                                       pa_mae=public['scores']['current']['pa_mae'],
                                       qualification='Compare only to the matched saved public export; PA is not a ZiPS talent-only workload claim.'),
        legacy_offense_scores_not_mixed_with_compatible_scores=True,
        completed_comparisons=experiments,
        decision='Keep the historical incumbent and unchanged evaluated frozen candidate as qualified references. No research-arm promotion or outcome-selected subgroup hybrid.',
        next_action='Historical source-to-fit exposure/support audit of thin high-pedigree and established upper-minors profiles, after mapping prior rich-feature tests; no new fit without a demonstrated nonduplicative gap.',
        remaining_requirements=['prospect readiness and allocation', 'public workload and comparable benchmark coverage',
                                'foreign/return entrant coverage', 'support for low-level ability claims',
                                'joint uncertainty and later horizons', 'nonbatting full value and control/contract valuation'],
        deployment_approved=False, full_war_or_control_value_claim=False, goal_complete=False,
        evidence_hashes={str(p.relative_to(ROOT)): sha256_file(p) for p in dict.fromkeys(paths)})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(receipt, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf8', newline='\n')
    print('Readiness record saved: no fits, no rescoring, no forecast/explorer change; goal remains active.', flush=True)


if __name__ == '__main__':
    main()
