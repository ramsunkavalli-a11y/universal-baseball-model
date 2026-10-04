from pathlib import Path
import sys
import numpy as np
import polars as pl
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from audit_hitter_detailed_contact_compatibility import reconstruct, peer_rows, memberships
from repair_hitter_contact_compatibility_pilot import overlay_selected_sequences


def fixture():
    return pl.DataFrame({'contact_events': [1], **{
        f'contact_cell_rate__{i}': [(1.5 if i == 0 else .5) / 46] for i in range(90)}})


def test_reconstruct_fixed_prior_and_denominator():
    names, counts = reconstruct(fixture())
    assert len(names) == 90 and counts.sum() == 1 and counts[0, 0] == 1


def test_noninteger_source_is_not_silently_rounded():
    f = fixture().with_columns(pl.lit(.02).alias('contact_cell_rate__0'))
    with pytest.raises(ValueError, match='integer'):
        reconstruct(f)


def test_peer_selection_does_not_use_future_outcomes():
    f = pl.DataFrame([dict(player_id=i, origin_year=2024, age=21. + i, stage='Upper minors',
                          prior_debut=0, pa_0=0, AAA_0_pa=0, AA_0_pa=100,
                          next_pa=100 * i) for i in range(6)])
    row = f.row(0, named=True)
    before = peer_rows(f, row)['player_id'].to_list()
    assert before == peer_rows(f.with_columns(pl.lit(-999).alias('next_pa')), row)['player_id'].to_list()


def test_fold_support_counts_shared_people_not_seasons():
    f = pl.DataFrame([dict(origin_year=y, target_season=y + 1, player_id=i)
                      for y in [2015, 2016, 2017] for i in [1, 2]])
    result = memberships(f)
    assert result[0]['train_rows'] == 4 and result[0]['shared_people'] == 2


def test_labels_must_mature_even_in_source_review():
    f = pl.DataFrame([dict(origin_year=y, target_season=y + 3, player_id=1)
                      for y in [2015, 2016, 2017]])
    with pytest.raises(ValueError, match='Unmatured'):
        memberships(f)


def test_official_identity_repair_preserves_physical_contact():
    source = pl.DataFrame({'game_pk': [1], 'at_bat_index': [74], 'player_id': [647228],
                           'core_bin': ['PULL_OFFB'], 'canonical_outcome': ['HR']})
    authority = pl.DataFrame({'game_pk': [1], 'at_bat_index': [74], 'official_batter_id': [676045]})
    r = overlay_selected_sequences(source, authority)
    assert r['player_id'][0] == 676045 and r['source_batter_id'][0] == 647228
    assert r['core_bin'][0] == 'PULL_OFFB' and r['canonical_outcome'][0] == 'HR'


def test_missing_official_identity_cannot_become_zero_or_inferred():
    source = pl.DataFrame({'game_pk': [1], 'at_bat_index': [74], 'player_id': [647228]})
    authority = pl.DataFrame({'game_pk': [1], 'at_bat_index': [75], 'official_batter_id': [676045]})
    with pytest.raises(ValueError, match='cover every'):
        overlay_selected_sequences(source, authority)
