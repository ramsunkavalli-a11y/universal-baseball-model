from universal_baseball.npb_identity_overlay import reviewed_id


def row(name='レアード', identity=None):
    return dict(name_key=name, npb_id=identity,
                npb_identity_status='exact_season_team_name' if identity else 'missing_listing_name')


def test_published_single_initial_recovered():
    assert reviewed_id(row(), {'Ｂ．レアード': {'23525130'}}) == ('23525130', 'unique_same_team_published_initial_alias')
    assert reviewed_id(row(), {'B.レアード': {'23525130'}})[0] == '23525130'


def test_ambiguous_surname_remains_unknown():
    assert reviewed_id(row(), {'Ｂ．レアード': {'001'}, 'Ｃ．レアード': {'002'}}) == (None, 'ambiguous_published_initial_alias')


def test_no_fuzzy_partial_or_transliteration():
    assert reviewed_id(row(), {'Ｂ．レアード改名': {'001'}})[0] is None
    assert reviewed_id(row(), {'Brandon Laird': {'001'}})[0] is None


def test_preserve_exact_identity():
    assert reviewed_id(row(identity='001'), {'Ｂ．レアード': {'002'}}) == ('001', 'exact_season_team_name')
