import importlib.util
from pathlib import Path

import pytest


spec = importlib.util.spec_from_file_location('readiness', Path(__file__).resolve().parents[1] / 'scripts/audit_hitter_candidate_readiness.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_order_and_duplicates_are_not_hidden_by_feature_counts():
    assert module.ordered_feature_check(['a', 'b'], ['a', 'b'])['ordered_names_identical']
    with pytest.raises(ValueError):
        module.ordered_feature_check(['a', 'b'], ['b', 'a'])
    with pytest.raises(ValueError):
        module.ordered_feature_check(['a', 'a'], ['a', 'a'])


def completed():
    return {
        'scores': {'freeze_manifest_sha256': 'manifest', 'forecast_sha256': 'forecast',
                   'post_result_fit_or_tuning': False, 'scored_at_utc': '2026-10-05T09:00:00+00:00'},
        'review_completion': {'status': 'completed_single_frozen_evaluation_with_qualified_disposition',
                             'no_post_result_forecast_change': True, 'future_2026_retesting_forbidden': True,
                             'player_walkthrough_status': 'complete', 'predictive_superiority_established': False,
                             'public_matched_comparison_unavailable': True}}


def test_completion_does_not_inherit_old_pending_flags_or_claim_superiority():
    result = module.evaluation_completion({'frozen_at_utc': '2026-10-05T08:00:00+00:00'}, 'manifest', 'forecast', completed())
    assert result['status'] == 'already_evaluated_once'
    assert result['old_pending_flags_are_not_current_status']
    assert not result['predictive_superiority_established']
    assert not result['new_2026_scoring']


@pytest.mark.parametrize('change', ['forecast', 'tuning', 'time', 'walk', 'retest'])
def test_wrong_forecast_retuning_order_or_incomplete_review_cannot_pass(change):
    record = completed()
    if change == 'forecast': record['scores']['forecast_sha256'] = 'other'
    if change == 'tuning': record['scores']['post_result_fit_or_tuning'] = True
    if change == 'time': record['scores']['scored_at_utc'] = '2026-10-05T07:00:00+00:00'
    if change == 'walk': record['review_completion']['player_walkthrough_status'] = 'pending'
    if change == 'retest': record['review_completion']['future_2026_retesting_forbidden'] = False
    with pytest.raises(ValueError):
        module.evaluation_completion({'frozen_at_utc': '2026-10-05T08:00:00+00:00'}, 'manifest', 'forecast', record)
