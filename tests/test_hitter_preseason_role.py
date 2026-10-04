from universal_baseball.hitter_preseason_role import role_from_position, role_from_transaction, reconcile_hints


def test_generic_outfield_and_infield_are_hitter_hints():
    assert role_from_position({'code':'O','abbreviation':'OF'})=='hitter_hint'
    assert role_from_position({'code':'I','abbreviation':'IF'})=='hitter_hint'


def test_pitcher_metadata_cannot_erase_two_way_hint():
    assert reconcile_hints(['pitcher_hint','two_way_hint'])=='two_way_or_conflicting_hints'
    assert role_from_position({'code':'Y'})=='two_way_hint'


def test_shared_trade_description_matches_the_person():
    row=dict(person=dict(fullName='Melky Cabrera'),description='Team traded LF Melky Cabrera for LHP Jonathan Sanchez.')
    assert role_from_transaction(row)=='hitter_hint'
    row['person']['fullName']='Jonathan Sanchez'
    assert role_from_transaction(row)=='pitcher_hint'


def test_missing_name_and_unrecognized_role_stay_unknown():
    assert role_from_transaction({'description':'Team signed RF Player.'})=='unknown'
    assert role_from_position({'code':'UNKNOWN'})=='unknown'


def test_two_way_transaction_and_conflict_are_visible():
    assert role_from_transaction(dict(person=dict(fullName='Player'),description='Team signed RHP/DH Player.'))=='two_way_hint'
    assert reconcile_hints(['hitter_hint','pitcher_hint'])=='two_way_or_conflicting_hints'
