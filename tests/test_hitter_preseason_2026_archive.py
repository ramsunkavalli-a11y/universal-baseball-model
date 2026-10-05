import json
from html import escape
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from capture_hitter_preseason_2026_archive import parse


def html(year='2026', duplicate_identity=False, missing=False):
    payload = {}
    entries = []
    for rank in range(1, 101):
        pid = 1 if duplicate_identity else rank
        ref = f'Person:{pid}'
        payload[ref] = dict(id=pid, useName='Example', useLastName=str(pid), liveStats='Must not retain')
        entries.append(dict(rank=rank, playerEntity=dict(player=dict(__ref=ref))))
    payload['ROOT_QUERY'] = {'getPlayerRankingsFromSelection({"limit":100,"slug":"sel-pr-2026-top100"})': entries[:-1] if missing else entries}
    state = dict(context=dict(year=year, list='top100'), payload=payload)
    return '<div data-init-state="'+escape(json.dumps(state), quote=True)+'"></div>'


def test_only_complete_preseason_ranks_and_identities_retained():
    rows = parse(html())
    assert len(rows) == 100 and rows[0]['rank'] == 1
    assert set(rows[0]) == {'season', 'player_id', 'rank', 'list_capacity', 'list_complete', 'player_name'}


def test_wrong_year_incomplete_and_duplicate_stop():
    for h in [html(year='2025'), html(missing=True), html(duplicate_identity=True)]:
        with pytest.raises(AssertionError):
            parse(h)


def test_multiple_states_rejected():
    with pytest.raises(ValueError):
        parse(html()+html())
