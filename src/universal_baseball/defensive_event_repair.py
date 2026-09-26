"""Conservative event accounting; deliberately NOT a defensive skill model."""
from __future__ import annotations

from collections import Counter
import re


def family(event_type):
    if event_type.startswith('stolen_base_'):
        return 'SB'
    if event_type.startswith('pickoff_caught_stealing_'):
        return 'POCS'
    if event_type.startswith('caught_stealing_'):
        return 'CS'
    return {'wild_pitch':'WP', 'passed_ball':'PB'}.get(event_type)


def official_events(payload, expected_game, expected_year):
    """Keep individual steals; collapse multi-runner WP/PB to ONE pitch event.

    Identity is runner-event identity, not a terminal-PA battery assumption.
    Pitcher/catcher attribution intentionally remains uncertified.
    """
    gd = payload['gameData']
    if gd['game']['pk'] != expected_game or int(gd['datetime']['officialDate'][:4]) != expected_year:
        raise ValueError('Wrong historical game/year')
    if expected_year >= 2026 or gd['game']['type'] != 'R' or gd['status']['abstractGameState'] != 'Final':
        raise ValueError('Not a completed historical regular-season game')
    rows = {}
    coordinates = []
    for play in payload['liveData']['plays']['allPlays']:
        about = play['about']
        ab = about['atBatIndex']
        batting = 'away' if about['isTopInning'] else 'home'
        defense = 'home' if batting == 'away' else 'away'
        for runner in play.get('runners', []):
            d = runner.get('details', {})
            event_type = d.get('eventType', '')
            kind = family(event_type)
            if not kind:
                continue
            if kind in ('SB','CS','POCS'):
                reason = d.get('movementReason')
                # Other runners can advance ON a caught-stealing play. The play's
                # eventType is copied onto their movements; it is not their CS.
                # Do not require isOut: a scorer can charge CS with safe-on-error.
                if reason in ('r_adv_play','r_adv_throw'):
                    continue
                if reason != 'r_' + event_type:
                    raise ValueError(f'Uncertified steal movement reason: {reason}')
            index = d.get('playIndex')
            rid = d.get('runner', {}).get('id')
            if index is None or rid is None:
                raise ValueError('Runner event lacks unique event identity')
            row = {'game_pk':expected_game,'at_bat_index':ab,'event_index':index,
                   'family':kind,'event_type':event_type,'runner_id':rid if kind not in ('WP','PB') else None,
                   'batting_side':batting,'defense_side':defense,'source':'runner_movement',
                   'battery_attribution':'unresolved', 'catcher_id':None, 'pitcher_id':None}
            key = (ab,index,kind,row['runner_id'],event_type)
            rows.setdefault(key, row)
        for event in play.get('playEvents', []):
            event_type = event.get('details',{}).get('eventType','')
            kind = family(event_type)
            # Successful steals / CS stay runner based; do not double count actions.
            if kind in ('WP','PB'):
                key = (ab,event['index'],kind,None,event_type)
                rows.setdefault(key, {'game_pk':expected_game,'at_bat_index':ab,'event_index':event['index'],
                    'family':kind,'event_type':event_type,'runner_id':None,'batting_side':batting,
                    'defense_side':defense,'source':'play_event','battery_attribution':'unresolved',
                    'catcher_id':None,'pitcher_id':None})
            if event.get('hitData'):
                hit = event['hitData']
                xy = hit.get('coordinates',{})
                coordinates.append({'game_pk':expected_game,'at_bat_index':ab,
                    'official_x':xy.get('coordX'),'official_y':xy.get('coordY'),
                    'official_location':hit.get('location'),'official_trajectory':hit.get('trajectory'),
                    'official_result':play.get('result',{}).get('eventType')})
    return list(rows.values()), coordinates


def reconcile_box(payload, events):
    rows = []
    for side in ('home','away'):
        team = payload['liveData']['boxscore']['teams'][side]
        stats = team.get('teamStats',{})
        for kind, group, field in [('SB','batting','stolenBases'),('CS','batting','caughtStealing'),
                                    ('WP','pitching','wildPitches'),('PB','fielding','passedBall')]:
            value = stats.get(group,{}).get(field)
            if value is not None:
                if int(value) != float(value) or int(value) < 0:
                    raise ValueError('Invalid official box count')
                value = int(value)
            ledger_count = sum(e['family'] in ({'CS','POCS'} if kind == 'CS' else {kind})
                and e['batting_side' if kind in ('SB','CS') else 'defense_side'] == side for e in events)
            rows.append({'game_pk':payload['gameData']['game']['pk'],'side':side,'family':kind,
                'official':value,'ledger':ledger_count,'delta':None if value is None else ledger_count-value,
                'status':'unknown_box_count' if value is None else ('matched' if value == ledger_count else 'mismatch')})
    return rows


def narrative_capacity(text):
    """Old-style detection capacity, NOT identity-verified event recall.

    Even the maximum matched count per PA/family/base can overstate recall:
    terminal narratives do not identify the runner in the old numeric ledger.
    """
    text = str(text or '').lower()
    result = Counter()
    if not re.search(r'\b(?:pickoff|picked off)\b', text):
        kind = 'CS' if re.search(r'\bcaught stealing\b',text) else 'SB' if re.search(r'\b(?:steals|stolen base)\b',text) else None
        base = re.search(r'\b(2nd|3rd|home)\b',text)
        if kind and base:
            result[(kind, {'2nd':'2b','3rd':'3b','home':'home'}[base.group()])] = 1
    for pattern,kind in [('wild pitch','WP'),('passed ball','PB')]:
        if pattern in text:
            result[(kind,None)] = 1
    return result


def ground_ball_responsibility(row):
    """Conserved candidate allocation with explicit uncertainty, not range credit.

    All unknown/conflicting GBs stay in the ledger. Equal split of adjacent IFs
    is a declared benchmark only. Fully unassigned alternative is always kept.
    """
    if row.get('bb_type') != 'ground_ball':
        return []
    first = row.get('hit_location')
    outcome = row.get('terminal_outcome_group')
    if row.get('has_source_conflict'):
        positions, basis = [None], 'source_conflict'
    elif first in (7,8,9) and outcome in ('1B','2B','3B','ROE'):
        positions = {7:[5,6],8:[6,4],9:[4,3]}[first]
        basis = 'assumed_adjacent_infield_equal_share'
    elif first in (1,2,3,4,5,6):
        positions, basis = [first], 'observed_touch_not_ex_ante_responsibility'
    else:
        positions, basis = [None], 'unresolved'
    result = []
    for position in positions:
        pid = row.get('pitcher') if position == 1 else row.get(f'fielder_{position}') if position else None
        result.append({'game_pk':row['game_pk'],'at_bat_index':row['at_bat_index'],
            'first_touch_position':first,'candidate_position':position,'candidate_fielder_id':pid,
            'outcome':outcome,'share':1/len(positions),'basis':basis,
            'unknown_fielder':pid is None,'ex_ante_opportunity_certified':False,
            'all_unassigned_sensitivity_share':1/len(positions)})
    assert abs(sum(r['share'] for r in result)-1) < 1e-12
    return result
