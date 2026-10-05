from datetime import date
from universal_baseball.hitter_status_evidence import employment_kind as old_kind
from universal_baseball.hitter_employment_v3 import employment_kind, events


def raw(text, code='ASG', day='2022-03-17', **extra):
    return dict(id=1, person={'id': 553988}, toTeam={'id': 112}, fromTeam={},
                description=text, typeCode=code, typeDesc='', date=day, **extra)


def test_actual_machado_failure_keeps_context_not_signing():
    r = raw('2B Dixon Machado and  assigned to Chicago Cubs.')
    assert old_kind(r, {112}) == 'agreement_unspecified'
    assert employment_kind(r, {112}) == 'assignment_context'
    assert events([r], {112}, date(2022, 3, 18))[0]['kind'] == 'assignment_context'


def test_actual_minor_signing_preserved():
    r = raw('Chicago Cubs signed free agent RF An Ordinary Player to a minor league contract.', 'SFA')
    assert employment_kind(r, {112}) == 'minor_agreement'


def test_signed_word_and_explicit_signing_code_preserved():
    assert employment_kind(raw('Chicago Cubs signed free agent OF Example.'), {112}) == 'agreement_unspecified'
    assert employment_kind(raw('Provider description unavailable.', 'SFA'), {112}) == 'agreement_unspecified'


def test_conservative_cutoff_keeps_resolution_date():
    r = raw('Chicago Cubs signed free agent OF Example.', 'SFA', resolutionDate='2022-03-19')
    assert events([r], {112}, date(2022, 3, 18)) == []


def test_future_assignment_does_not_change_eligible_events():
    r = raw('Chicago Cubs signed free agent OF Example.', 'SFA')
    later = raw('Example assigned to Chicago Cubs.', day='2022-03-19')
    assert events([r, later], {112}, date(2022, 3, 18)) == events([r], {112}, date(2022, 3, 18))
