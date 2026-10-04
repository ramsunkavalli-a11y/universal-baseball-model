import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location('qualified', Path(__file__).resolve().parents[1] / 'scripts/build_hitter_qualified_handoff.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def inputs():
    return (dict(on_40man=0, origin_evidence_bridge=True),
        dict(availability_state='unknown', latest_context_date=None, foreign_performance_missing=False),
        dict(medical_scope=False, recorded_unresolved=None, reported_roster_returns730=None, observed_return_intervals730=None, clinical_recovery_certified=False),
        dict(roster_event_sign='positive', roster_event_date='2023-01-01', roster_event_capture_scope=True, event_listing_conflict=True, date_conflict_count=0))


def test_unknown_is_not_healthy_or_known_roster_error():
    e = module.evidence_metadata(*inputs())
    assert e['recorded_unresolved'] is None
    assert any('not known healthy' in f for f in e['source_flags'])
    assert any('not a proven roster error' in f for f in e['source_flags'])


def test_future_outcomes_cannot_change_source_flags():
    f, c, m, r = inputs()
    before = module.evidence_metadata(f, c, m, r)
    f.update(next_pa=700, next_value=10)
    assert module.evidence_metadata(f, c, m, r) == before


def test_restricted_and_missing_foreign_are_not_automatic_zeros():
    f, c, m, r = inputs()
    c.update(availability_state='administrative_leave', foreign_performance_missing=True)
    e = module.evidence_metadata(f, c, m, r)
    assert any('not legal clearance' in s for s in e['source_flags'])
    assert any('not zero talent' in s for s in e['source_flags'])
    assert 'pa' not in e and not e['availability_states_used_as_predictors']


def test_ui_additions_keep_actuals_opt_in_and_use_existing_filters():
    template = (module.OLD / 'explorer/index.html').read_text(encoding='utf8')
    html = module.qualified_html(template)
    assert '<input id="actual" type="checkbox">' in html
    assert 'r.target_year===y&&sourceMatch(r)&&(!org' in html
    assert 'html+=sourcePanel(r)' in html
    assert 'no calibrated continuous prediction intervals' in html
