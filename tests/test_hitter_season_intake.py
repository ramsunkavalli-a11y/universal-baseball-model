import pytest

from universal_baseball.hitter_season_intake import COUNT_FIELDS, counts, project_page


def payload():
    stat = {k:0 for k in COUNT_FIELDS.values()}
    stat.update(plateAppearances=10, atBats=8, baseOnBalls=1, sacFlies=1,
                hits=3, doubles=1, strikeOuts=2, gamesPlayed=3)
    return {'stats':[{'type':{'displayName':'season'}, 'group':{'displayName':'hitting'},
                     'splits':[{'season':'2026','sport':{'id':16},'team':{'id':5},
                                'player':{'id':7,'fullName':'Example'},'numTeams':2,
                                'league':{'id':130},'stat':stat}]}]}


def test_aggregate_does_not_claim_stint_or_dsl_scope():
    row = project_page(payload(), season=2026, sport_id=16, kind='players')[0]
    assert row['needs_stint_resolution']
    assert row['singles'] == 2 and row['babip_opportunities'] == 7
    assert 'bucket' not in row


def test_missing_event_not_zero():
    data = payload()['stats'][0]['splits'][0]['stat']
    del data['caughtStealing']
    with pytest.raises(ValueError, match='unknown'):
        counts(data)


@pytest.mark.parametrize('key,value', [('plateAppearances',9), ('hits',9), ('baseOnBalls',-1), ('triples',float('nan'))])
def test_bad_arithmetic_rejected(key, value):
    data = payload()['stats'][0]['splits'][0]['stat']
    data[key] = value
    with pytest.raises(ValueError):
        counts(data)


def test_wrong_year_and_duplicate_identity():
    data = payload()
    with pytest.raises(ValueError, match='season'):
        project_page(data, season=2025, sport_id=16, kind='players')
    data['stats'][0]['splits'] *= 2
    with pytest.raises(ValueError, match='Duplicate'):
        project_page(data, season=2026, sport_id=16, kind='players')


def test_unclassified_pa_retained_without_inventing_event():
    data = payload()['stats'][0]['splits'][0]['stat']
    data['plateAppearances'] = 11
    row = counts(data)
    assert row['unclassified_pa'] == 1
    assert row['plate_appearances'] == 11 and row['at_bats'] == 8
