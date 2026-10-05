import copy
import pytest

from universal_baseball.international_snapshot_completion import aligned_peers, validate_claims


def row(key, pa, season=2026):
    counts = dict(pa=pa, ab=pa, hits=0, doubles=0, triples=0, hr=0, bb=0,
                  ibb=0, hbp=0, so=0, sh=0, sf=0)
    return dict(counts, id=key, season=season, player_name_ko=key, birth_date=None)


def test_peers_use_same_multi_year_denominator():
    focal = row('focal', 10)
    current = [focal, row('near', 1), row('snapshot-only', 30), row('third', 100), row('fourth', 200)]
    history = current + [row('focal', 20, 2025), row('near', 29, 2025), row('snapshot-only', 1000, 2025)]
    peers = aligned_peers(history, current, 'id', focal)
    assert peers[0]['source_key'] == 'near' and peers[0]['window_pa'] == 30
    assert peers[0]['snapshot_pa'] == 1
    assert 'focal' not in [p['source_key'] for p in peers]


def test_unknown_source_identity_cannot_be_joined_by_name():
    focal = row(None, 0)
    peers = aligned_peers([focal, row('other', 0)], [focal, row('other', 0)], 'id', focal)
    assert len(peers) == 1 and peers[0]['window_source_rows'] == 1


def test_conflicting_peer_birth_dates_rejected():
    current = [row('peer', 1), dict(row('peer', 2), birth_date='2000-01-01')]
    with pytest.raises(ValueError, match='birth dates'):
        aligned_peers(current, current, 'id', row('focal', 0))


def valid():
    return dict(new_fits=0, forecasts_changed=False, raw_2026_MLB_outcomes_read=False,
        independent_reconstruction_pass=True, future_mutation_checks=6,
        source_cases=[dict(MLB_talent_forecast=None, MLB_opportunity_forecast=None,
                           predictive_outcome=None) for _ in range(6)],
        source_checks={league: dict(season_complete=False) for league in ['npb', 'kbo']})


def test_valid_source_review_is_not_predictive_validation():
    validate_claims(valid())


@pytest.mark.parametrize('field,value', [('new_fits', 1), ('forecasts_changed', True),
    ('raw_2026_MLB_outcomes_read', True), ('independent_reconstruction_pass', False),
    ('future_mutation_checks', 5)])
def test_unsafe_claims_fail(field, value):
    r = valid(); r[field] = value
    with pytest.raises(ValueError): validate_claims(r)


def test_no_invented_forecast_or_season_completion():
    r = valid(); bad = copy.deepcopy(r); bad['source_cases'][0]['MLB_talent_forecast'] = 1
    with pytest.raises(ValueError): validate_claims(bad)
    r['source_checks']['npb']['season_complete'] = True
    with pytest.raises(ValueError): validate_claims(r)
