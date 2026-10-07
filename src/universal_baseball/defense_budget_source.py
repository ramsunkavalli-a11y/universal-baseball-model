"""Explicit overlapping pitcher/DH starts, not a name-based player override."""


def dual_start(boxscore, player_id, season):
    if season < 2022:
        return dict(status='outside_rule_scope', certified=False)
    found = []
    for side in ('away', 'home'):
        team = boxscore.get('teams', {}).get(side, {})
        for player in team.get('players', {}).values():
            if player.get('person', {}).get('id') == player_id:
                found.append((side, player))
    if len(found) != 1:
        return dict(status='unresolved_identity', certified=False, records=len(found))
    side, player = found[0]
    pitching = player.get('stats', {}).get('pitching', {})
    order = player.get('battingOrder')
    roles = sorted({str(p.get('code')) for p in player.get('allPositions', [])})
    result = dict(side=side, batting_order=order, roles=roles,
                  pitching_starts=pitching.get('gamesStarted'), certified=False)
    if pitching.get('gamesStarted') != 1:
        return dict(**result, status='not_a_pitching_start')
    if order is None or not str(order).isdigit() or not str(order).endswith('00'):
        return dict(**result, status='not_a_batting_start')
    if '1' not in roles:
        return dict(**result, status='unresolved_dual_role')
    return dict(**{**result, 'certified': True}, status='certified_dual_start',
                DH_evidence_basis='boxscore_dual_appearance' if '10' in roles else
                'rule_5_11b_starting_pitcher_in_lineup')


def reviewed_dh_starts(raw_starts, game_records):
    """No silent gap fill and no duplicates, even when both endpoints repeat a game."""
    ids = [r['game_id'] for r in game_records]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate game evidence')
    if any(r['status'].startswith('unresolved') for r in game_records):
        raise ValueError('Unresolved dual-role evidence')
    additions = sum(r['certified'] for r in game_records)
    return dict(raw_starts=raw_starts, certified_dual_starts=additions,
                reviewed_starts=raw_starts + additions,
                game_ids=[r['game_id'] for r in game_records if r['certified']])
