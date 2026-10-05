import pytest

from universal_baseball.hitter_mlb_events import reconstruct, EVENTS


def row():
    return dict(plate_appearances=100, strike_outs=30, unintentional_walks=10,
                hit_by_pitch=2, home_runs=5, babip_hits=20,
                babip_opportunities=50, doubles=4, triples=1)


def test_babip_uses_ball_in_play_opportunities_not_plate_appearances():
    f, note = reconstruct(1, 2024, {(2024, 1): row()}, {2022, 2023, 2024})
    assert f['pooled_MLB_BABIP'] == (20 + 100 * .30) / (50 + 100)
    assert note['events']['BABIP']['observed_share'] == 50 / 150
    assert note['events']['HR']['observed_share'] == 100 / 200
    assert f['pooled_MLB_BB'] == (10 + 100 * .08) / 200


def test_unknown_coverage_is_not_a_measured_average_hitter():
    with pytest.raises(ValueError, match='Unknown MLB count coverage'):
        reconstruct(1, 2024, {}, {2023, 2024})
    f, note = reconstruct(1, 2024, {}, {2022, 2023, 2024})
    assert all(f[f'pooled_MLB_{e}'] == prior for e, (_, _, prior) in EVENTS.items())
    assert all(v['unshrunk_rate'] is None and v['model_coordinate'] == 0 for v in note['events'].values())


def test_reconstruct_once_prior_with_recency_and_ignore_future():
    raw = {(2024, 1): row(), (2023, 1): row()}
    f, note = reconstruct(1, 2024, raw, {2022, 2023, 2024})
    assert f['pooled_MLB_HR'] == (9 + 3) / 280
    assert note['events']['HR']['denominator'] == 180
    raw[(2025, 1)] = {k: 9999 for k in row()}
    assert reconstruct(1, 2024, raw, {2022, 2023, 2024, 2025}) == (f, note)


def test_invalid_event_count_raises():
    bad = row(); bad['babip_hits'] = 51
    with pytest.raises(ValueError, match='Invalid BABIP'):
        reconstruct(1, 2024, {(2024, 1): bad}, {2022, 2023, 2024})
