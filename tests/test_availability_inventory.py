from universal_baseball.availability_inventory import old_restriction_with_later_mlb_use


def test_old_restriction_and_positive_later_year_is_warning():
    a = {'active_restrictions': {'suspended': {'kind': 'suspended_unspecified', 'event_date': '2022-08-12'}}}
    assert old_restriction_with_later_mlb_use({'origin_year': 2023, 'pa_0': 438}, a)


def test_same_year_use_does_not_clear_late_restriction():
    a = {'active_restrictions': {'restricted': {'kind': 'restricted', 'event_date': '2023-08-14'}}}
    assert not old_restriction_with_later_mlb_use({'origin_year': 2023, 'pa_0': 491}, a)


def test_missing_use_or_missing_restriction_is_not_proof():
    a = {'active_restrictions': {'suspended': {'kind': 'suspended_unspecified', 'event_date': '2022-08-12'}}}
    assert not old_restriction_with_later_mlb_use({'origin_year': 2023, 'pa_0': 0}, a)
    assert not old_restriction_with_later_mlb_use({'origin_year': 2023, 'pa_0': 438}, {'active_restrictions': {}})


def test_permanent_or_deceased_cannot_be_cleared_by_generic_use():
    for kind in ['permanent_ineligible', 'deceased']:
        a = {'active_restrictions': {'ineligible': {'kind': kind, 'event_date': '2022-06-01'}}}
        assert not old_restriction_with_later_mlb_use({'origin_year': 2023, 'pa_0': 438}, a)


def test_newer_parallel_channel_blocks_old_year_warning():
    a = {'active_restrictions': {
        'suspended': {'kind': 'suspended_unspecified', 'event_date': '2022-08-12'},
        'administrative': {'kind': 'administrative_leave', 'event_date': '2023-08-14'}}}
    assert not old_restriction_with_later_mlb_use({'origin_year': 2023, 'pa_0': 491}, a)
