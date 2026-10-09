"""Strict season-count intake; aggregate team labels are not stint evidence."""
from math import isfinite

COUNT_FIELDS = {
    'plate_appearances': 'plateAppearances', 'at_bats': 'atBats', 'hits': 'hits',
    'doubles': 'doubles', 'triples': 'triples', 'home_runs': 'homeRuns',
    'base_on_balls': 'baseOnBalls', 'intentional_walks': 'intentionalWalks',
    'hit_by_pitch': 'hitByPitch', 'strike_outs': 'strikeOuts',
    'sac_bunts': 'sacBunts', 'sac_flies': 'sacFlies', 'stolen_bases': 'stolenBases',
    'caught_stealing': 'caughtStealing', 'ground_into_double_play': 'groundIntoDoublePlay',
    'games_played': 'gamesPlayed', 'runs': 'runs', 'catchers_interference': 'catchersInterference',
}
SPORTS = {1: 'MLB', 11: 'AAA', 12: 'AA', 13: 'HIGH_A', 14: 'SINGLE_A', 16: 'ROOKIE_COMPLEX'}


def counts(stat):
    missing = set(COUNT_FIELDS.values())-stat.keys()
    if missing:
        raise ValueError(f'Missing counts are unknown: {sorted(missing)}')
    out = {}
    for name, key in COUNT_FIELDS.items():
        value = stat[key]
        if isinstance(value, bool) or not isinstance(value, (float, int)) or not isfinite(value) or value < 0 or int(value) != value:
            raise ValueError(f'Invalid {key}')
        out[name] = int(value)
    out['unclassified_pa'] = out['plate_appearances'] - sum(out[n] for n in (
        'at_bats', 'base_on_balls', 'hit_by_pitch', 'sac_bunts', 'sac_flies', 'catchers_interference'))
    # An obstruction/other administrative PA can lack a named source field.
    # Retain it explicitly, without asserting a cause or inventing an AB/event.
    if out['unclassified_pa'] < 0:
        raise ValueError('Named events exceed PA')
    out.update(singles=out['hits']-out['doubles']-out['triples']-out['home_runs'],
               unintentional_walks=out['base_on_balls']-out['intentional_walks'],
               babip_hits=out['hits']-out['home_runs'],
               babip_opportunities=out['at_bats']-out['strike_outs']-out['home_runs']+out['sac_flies'])
    if min(out.values()) < 0 or out['hits'] > out['at_bats'] or out['strike_outs'] > out['at_bats']:
        raise ValueError('Impossible event counts')
    return out


def project_page(payload, *, season, sport_id, kind):
    if sport_id not in SPORTS or kind not in {'players', 'teams'}:
        raise ValueError('Unsupported source scope')
    blocks = payload.get('stats', [])
    if len(blocks) != 1 or blocks[0].get('type', {}).get('displayName') != 'season' or blocks[0].get('group', {}).get('displayName') != 'hitting':
        raise ValueError('Wrong season-stat response')
    rows = []
    for split in blocks[0]['splits']:
        if int(split['season']) != season:
            raise ValueError('Wrong season')
        if split.get('sport', {}).get('id', sport_id) != sport_id:
            raise ValueError('Wrong level')
        try:
            projected_counts = counts(split['stat'])
        except ValueError as exc:
            raise ValueError(f"{split.get('player', split.get('team'))}: {exc}") from exc
        row = dict(season=season, sport_id=sport_id, **projected_counts)
        row['team_id'] = split.get('team', {}).get('id')
        if kind == 'teams':
            if row['team_id'] is None:
                raise ValueError('Missing team identity')
        else:
            row.update(player_id=int(split['player']['id']), player_name=split['player']['fullName'],
                       league_id=split.get('league', {}).get('id'),
                       position=split.get('position', {}).get('code', 'UNKNOWN'),
                       reported_age=split['stat'].get('age'),
                       number_of_teams=split.get('numTeams'),
                       source_scope='player_sport_season_aggregate')
            # Multiple rookie leagues share sport 16. Do not pretend an aggregate
            # row's one displayed league/team locates every plate appearance.
            row['needs_stint_resolution'] = row['number_of_teams'] != 1 or row['team_id'] is None
        rows.append(row)
    key = 'player_id' if kind == 'players' else 'team_id'
    if len({r[key] for r in rows}) != len(rows):
        raise ValueError(f'Duplicate {kind} identity within source page')
    return rows
