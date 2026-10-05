"""Completion gates test actual arithmetic and immutable membership, not scores."""
import copy
import importlib.util
from pathlib import Path

import pytest

path = Path(__file__).resolve().parents[1] / 'scripts/finalize_international_hitter_2025.py'
spec = importlib.util.spec_from_file_location('international_completion', path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def row(season=2025, pa=10, key='a'):
    return dict(season=season, npb_id=key, pa=pa, ab=pa, hits=1, doubles=0,
                triples=0, hr=1, bb=0, ibb=0, hbp=0, so=2 if pa else 0,
                sh=0, sf=0, player_id=None)


def subtotal(rows, year):
    selected = [r for r in rows if 2023 <= r['season'] <= year]
    counts = {k: sum(r[k] for r in selected) for k in m.FIELDS}
    events = m.exclusive_events(counts)
    return dict(origin=year, counts=counts, events=events,
                event_rates={k: v / counts['pa'] if counts['pa'] else None for k, v in events.items()},
                selected_source_rows=len(selected), mlb_translation_fitted=False,
                observed_positive_seasons=sorted({r['season'] for r in selected if r['pa'] > 0}))


def test_unobserved_rate_is_not_zero():
    s = subtotal([], 2024)
    m.verify_subtotal([], s, 2024)
    s['event_rates']['K'] = 0
    with pytest.raises(ValueError, match='Unobserved'):
        m.verify_subtotal([], s, 2024)


def test_future_rows_do_not_enter_subtotal():
    rows = [row(), row(2026, 100)]
    s = subtotal(rows, 2025)
    m.verify_subtotal(rows, s, 2025)
    assert s['counts']['pa'] == 10


def test_changed_rate_fails():
    rows = [row()]
    s = subtotal(rows, 2025)
    s['event_rates']['K'] = .3
    with pytest.raises(ValueError, match='Rate differs'):
        m.verify_subtotal(rows, s, 2025)


def test_source_keys_separate_unmapped_players():
    current = [row(key='a'), row(pa=100, key='b')]
    chosen = dict(league='NPB', source_id='a', player_id=None, rule='ordinary')
    case = dict(chosen, source_2025=current[0], annual_counts=[current[0]],
                before_last_season=subtotal([], 2024), with_last_season=subtotal([current[0]], 2025),
                future_mutation_invariance=True, new_projection=None)
    m.verify_case(case, chosen, [], current)
    bad = copy.deepcopy(case)
    bad['annual_counts'].append(current[1])
    with pytest.raises(ValueError, match='source-key'):
        m.verify_case(bad, chosen, [], current)


def test_case_cannot_be_replaced():
    with pytest.raises(ValueError, match='selection'):
        m.verify_case(dict(league='NPB', source_id='b'), dict(league='NPB', source_id='a'), [], [])


def test_changed_seal_fails(tmp_path):
    p = tmp_path / 'input'
    p.write_text('original')
    sha = m.digest(p)
    m.verify_hashes({'input': sha}, tmp_path)
    p.write_text('changed')
    with pytest.raises(ValueError, match='Changed sealed'):
        m.verify_hashes({'input': sha}, tmp_path)


def test_completion_cannot_overwrite(tmp_path):
    p = tmp_path / 'completed.json'
    m.save_new(p, {'status': 'complete'})
    with pytest.raises(ValueError, match='already exists'):
        m.save_new(p, {'status': 'different'})
