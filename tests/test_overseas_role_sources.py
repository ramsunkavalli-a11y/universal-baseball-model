from universal_baseball.overseas_role_sources import reports_at_origin


def source(**extra):
    r = dict(player_id=1, target_year=2024, publication_day='2023-12-15',
             report_id='a', reported_role='camp_competition_depth', contract_form='major')
    r.update(extra)
    return r


def test_same_day_warning_and_not_certified_rights():
    r = reports_at_origin([source()], 1, 2024, '2023-12-15')
    assert r['reports'][0]['same_day_precision_warning']
    assert not r['current_rights_certified']
    assert r['source_pilot_not_population_complete']


def test_no_role_carry_forward_even_if_long_contract():
    r = reports_at_origin([source(contract_years=6)], 1, 2025, '2025-01-24')
    assert r['reports'] == [] and r['role_coverage'] == 'unknown'
    assert r['excluded'][0]['reason'] == 'different_target_season'


def test_future_report_cannot_change_eligible_information():
    old = reports_at_origin([source()], 1, 2024, '2024-01-26')
    new = reports_at_origin([source(), source(report_id='later', publication_day='2024-02-01',
                                            reported_role='everyday_center_field')], 1, 2024, '2024-01-26')
    assert old['reports'] == new['reports']
    assert old['role_coverage'] == new['role_coverage']
    assert new['excluded'][0]['reason'] == 'published_after_cutoff'


def test_no_report_is_unknown_not_no_job():
    r = reports_at_origin([source()], 2, 2024, '2024-01-26')
    assert r['role_coverage'] == 'unknown' and r['reports'] == []


def test_contract_does_not_impute_everyday_role():
    r = reports_at_origin([source(reported_role=None)], 1, 2024, '2024-01-26')
    assert r['role_coverage'] == 'unknown'
    assert r['reports'][0]['contract_form'] == 'major'
