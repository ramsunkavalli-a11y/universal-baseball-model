"""Project only publisher-selected historical ranks, never live biography fields."""
import json
from html.parser import HTMLParser


class _State(HTMLParser):
    def __init__(self):
        super().__init__()
        self.states = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key == 'data-init-state':
                self.states.append(json.loads(value))


def project(html, year, *, allow_2025=False):
    if not 2011 <= year <= (2025 if allow_2025 else 2024):
        raise ValueError('Only declared historical development years are allowed')
    parser = _State(); parser.feed(html)
    if len(parser.states) != 1:
        raise ValueError('Missing or ambiguous publisher state')
    state = parser.states[0]
    if state['context']['year'] != str(year) or state['context']['list'] != 'top100':
        raise ValueError('Wrong report year or list')
    key = f'getPlayerRankingsFromSelection({{"limit":100,"slug":"sel-pr-{year}-top100"}})'
    entries = state['payload']['ROOT_QUERY'][key]
    capacity = 50 if year == 2011 else 100
    complete = True
    if year in [2020,2021] and sorted(x['rank'] for x in entries)==list(range(1,100)):
        # The saved publisher response lacks rank 100. Observed ranks remain
        # usable, but no absent player can be labeled unranked from this list.
        capacity = 99
        complete = False
    if sorted(x['rank'] for x in entries) != list(range(1, capacity+1)):
        raise ValueError(f'Incomplete or duplicate ranks in {year}: expected {capacity}, received {len(entries)}; ranks {[x["rank"] for x in entries]}')
    result = []
    for entry in entries:
        reference = entry['playerEntity']['player']['__ref']
        if not reference.startswith('Person:') or not reference[7:].isdigit():
            raise ValueError('Unresolved prospect identity')
        pid = int(reference[7:])
        person = state['payload'][reference]
        if int(person['id']) != pid:
            raise ValueError('Identity reference disagreement')
        result.append(dict(season=year, player_id=pid, rank=int(entry['rank']),
                           list_capacity=capacity, list_complete=complete,
                           player_name=person['useName']+' '+person['useLastName']))
    if len({x['player_id'] for x in result}) != capacity:
        raise ValueError('Duplicate prospect identity')
    # Position, organization, age, ETA, tool grades and biographies are intentionally
    # omitted. They are not established as field-matched vintage in these pages.
    return sorted(result, key=lambda x:x['rank'])


def features(player_id, origin_year, lookup, complete_years):
    out = {}
    for lag in range(3):
        year = origin_year-lag; available = year in complete_years
        rank = lookup.get((year, player_id))
        if rank is not None and not available:
            raise ValueError('Rank from uncertified list')
        out[f'scout_list_available_{lag}'] = float(available)
        out[f'scout_list_capacity_{lag}'] = float(complete_years[year]) if available else 0.
        certified_absence = available and complete_years[year] in [50,100]
        out[f'scout_listed_{lag}'] = 1. if rank is not None else (0. if certified_absence else None)
        out[f'scout_rank_score_{lag}'] = (101-rank)/100 if rank is not None else (0. if certified_absence else None)
    return out
