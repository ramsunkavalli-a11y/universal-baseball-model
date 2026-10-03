from universal_baseball.cached_school_background import DatedSchoolBackground


def pick(year=2009,pid=1,name='Florida',grade='JR'):
    return dict(draft_year=year,player_id=pid,school_name=name,school_class=grade)


def test_existing_dated_institution_recovers_background_not_class():
    own=pick(2012,2,' Florida  ','')
    r=DatedSchoolBackground([pick()]).resolve(own,2012)
    assert r['background']=='college' and r['evidence'][0]['year']==2009
    assert own['school_class']==''


def test_future_evidence_cannot_fill_old_forecast():
    r=DatedSchoolBackground([pick(2018)]).resolve(pick(2012,2,grade=''),2012)
    assert r['background']=='unknown' and not r['evidence']


def test_institution_conflict_stays_unknown_and_aliases_not_guessed():
    resolver=DatedSchoolBackground([pick(),pick(2010,3,grade='HS SR')])
    assert resolver.resolve(pick(2012,2,grade=''),2012)['background']=='unknown'
    assert DatedSchoolBackground([pick(name='LSU')]).resolve(pick(2012,2,'Louisiana State',''),2012)['background']=='unknown'


def test_explicit_own_background_and_missing_pick():
    r=DatedSchoolBackground([])
    assert r.resolve(pick(name='Some HS',grade=''),2012)['background']=='hs'
    assert r.resolve(pick(name='Some CC',grade=''),2012)['background']=='jc'
    assert r.resolve(None,2012)['background']=='unknown'
