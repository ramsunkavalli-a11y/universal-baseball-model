import polars as pl
import pytest
from universal_baseball.hitter_contact_identity_rebuild import (
    FIELDS, reconcile_contacts, select_authority_games, overlay_authority, contact_cells, measurement_changes,
)


def contact(game=1, player=10, seq=0, league=130):
    return dict(game_pk=game, at_bat_index=seq, source_batter_id=player, pitch_number=4,
                season=2024, level='rk', league_id=league, hc_x=123., hc_y=88.)


def control(game=1, player=10, count=1, league=130, conflict=False):
    return dict(game_id=game, player_id=player, expected_contact_count=count, league_id=league,
                game_type='R', blocking_metadata_conflict=False, nonblocking_metadata_conflict=conflict)


def empty_quarantine(): return pl.DataFrame(schema={'game_pk': pl.Int64})


def test_missing_control_is_unknown_not_zero():
    c = pl.DataFrame([contact(), contact(2)])
    m, residuals = select_authority_games(c, pl.DataFrame([control()]), empty_quarantine())
    row = m.filter(pl.col('game_pk') == 2).to_dicts()[0]
    assert row['trigger_reasons'] == ['missing_game_controls']
    assert 2 not in residuals['game_id']


def test_unresolved_and_metadata_controls_trigger():
    c = pl.DataFrame([contact(), contact(2)])
    controls = pl.DataFrame([control(count=None), control(2, conflict=True)], schema_overrides={'expected_contact_count': pl.Int64})
    m, r = select_authority_games(c, controls, empty_quarantine())
    assert m['triggered'].all() and len(r) == 0


def test_league_mismatch_not_folded_into_aaa():
    m, _ = select_authority_games(pl.DataFrame([contact(league=125)]), pl.DataFrame([control(league=112)]), empty_quarantine())
    assert m['league_id'][0] == 125
    assert 'control_source_league_disagreement' in m['trigger_reasons'][0]


def test_residuals_trigger_both_sides_of_identity_swap():
    c = pl.DataFrame([contact()]); controls = pl.DataFrame([control(count=0), control(player=11, count=1)])
    m, r = select_authority_games(c, controls, empty_quarantine())
    assert m['triggered'][0] and sorted(r['contact_count_difference']) == [-1, 1]
    a = pl.DataFrame([dict(game_pk=1, at_bat_index=0, official_batter_id=11)])
    repaired, failures = overlay_authority(c, m, a)
    assert repaired['batter_mlbam_id'][0] == 11 and len(failures) == 0
    assert repaired.select(c.columns).equals(c)


def test_unflagged_mismatch_is_not_silently_repaired():
    c = pl.DataFrame([contact()]); m, _ = select_authority_games(c, pl.DataFrame([control()]), empty_quarantine())
    a = pl.DataFrame([dict(game_pk=1, at_bat_index=0, official_batter_id=11)])
    repaired, failures = overlay_authority(c, m, a)
    assert len(failures) == 1 and repaired['batter_mlbam_id'][0] == 10


def test_missing_sequence_and_duplicate_authority_fail():
    c = pl.DataFrame([contact()]); m, _ = select_authority_games(c, pl.DataFrame([control()]), empty_quarantine())
    a = pl.DataFrame([dict(game_pk=1, at_bat_index=1, official_batter_id=11)])
    with pytest.raises(ValueError, match='missing'): overlay_authority(c, m, a)
    with pytest.raises(ValueError, match='unique'): overlay_authority(c, m, pl.concat([a, a]))


def test_sample_is_deterministic_and_separate_by_league():
    c = pl.DataFrame([contact(g, league=125 if g < 6 else 130) for g in range(1, 11)])
    controls = pl.DataFrame([control(g, league=125 if g < 6 else 130) for g in range(1, 11)])
    m, _ = select_authority_games(c, controls, empty_quarantine(), sample_size=2)
    m2, _ = select_authority_games(c.reverse(), controls.reverse(), empty_quarantine(), sample_size=2)
    assert m.equals(m2) and m.filter(pl.col('unflagged_sample')).height == 4
    assert m.filter(pl.col('unflagged_sample')).group_by('league_id').len()['len'].to_list() == [2, 2]


def test_contact_union_and_nonnull_consensus():
    row = {c: None for c in FIELDS}
    row.update(game_pk=1, at_bat_index=0, season=2024, level='rk', league_id=130,
               game_type='R', batter=10, type='X', terminal_pitch_number=4, source_asset='a')
    other = dict(row, source_asset='b', hc_x=100.)
    c, q = reconcile_contacts([pl.DataFrame([row]), pl.DataFrame([other])])
    assert len(c) == 1 and c['hc_x'][0] == 100. and len(q) == 0
    other['type'] = 'S'
    c, q = reconcile_contacts([pl.DataFrame([row]), pl.DataFrame([other])])
    assert len(c) == 0 and len(q) == 1 and 'type' in q['conflicting_fields'][0]


def test_cells_preserve_bunts_and_unknowns_outside_feature_denominator():
    rows = [dict(contact(seq=i), batter_mlbam_id=10, participant_authority='source_default',
                 stand='R', bb_type='fly_ball', pa_description='Player homers.', terminal_outcome_group='HR') for i in range(3)]
    rows[1].update(bb_type='bunt_grounder', pa_description='Player bunts.', terminal_outcome_group=None)
    rows[2].update(bb_type=None, terminal_outcome_group=None)
    events, counts, wide = contact_cells(pl.DataFrame(rows))
    assert len(events) == 3 and wide['physical_contacts'][0] == 3
    assert wide['classified_contacts'][0] == 1 and counts['count'].sum() == 1
    rates = [c for c in wide.columns if c.startswith('rate_')]
    assert len(rates) == 90 and abs(wide.select(pl.sum_horizontal(rates)) [0, 0] - 1) < 1e-12


def test_foul_air_is_not_fair_contact_and_mexico_remains_distinct():
    rows = [dict(contact(seq=i, league=125), level='aaa', batter_mlbam_id=10,
        participant_authority='source_default', stand='R', bb_type='fly_ball',
        pa_description='Player flies out in foul territory.', terminal_outcome_group='OUT') for i in range(2)]
    rows[1]['pa_description'] = 'Player flies out.'
    events, counts, wide = contact_cells(pl.DataFrame(rows))
    assert wide['bucket'][0] == 'MEX' and wide['physical_contacts'][0] == 2
    assert counts['count'].sum() == 1
    assert events['contact_profile_status'].to_list()[0] == 'foul_air_excluded'


def test_measurement_loss_cannot_underflow_unsigned_counts():
    row = dict(season=2016, league_id=117, bucket='AAA', player_id=10,
               physical_contacts=37, classified_contacts=33, raw_narrative_hr=1)
    before = pl.DataFrame([row], schema_overrides={c: pl.UInt32 for c in ['physical_contacts', 'classified_contacts', 'raw_narrative_hr']})
    after = pl.DataFrame([dict(row, physical_contacts=36, classified_contacts=32, raw_narrative_hr=0)])
    delta = measurement_changes(before, after)
    assert delta['delta_physical_contacts'][0] == -1
    assert delta['delta_raw_narrative_hr'][0] == -1
