"""Strict dated role evidence. Assignment is not defensive quality or health."""
from datetime import date

from universal_baseball.position_role_source import (
    POSITION_CODE_ABBREVIATION, baseball_innings_to_outs,
)


def integer(value, field):
    if isinstance(value, bool) or value is None:
        raise ValueError(f'Missing or invalid {field}')
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f'Invalid {field}') from exc
    if not number.is_integer() or number < 0:
        raise ValueError(f'Invalid {field}')
    return int(number)


def parse_logs(payload, *, player_id, season, sport_id, source_id):
    """Parse one explicit sport; an empty result is unknown, not certified zero."""
    if season > 2024:
        raise ValueError('Role-source inputs are restricted to 2024 or earlier')
    groups = payload.get('stats', [])
    if not groups:
        return []
    if len(groups) != 1 or groups[0].get('type', {}).get('displayName') != 'gameLog' \
            or groups[0].get('group', {}).get('displayName') != 'fielding':
        raise ValueError('Expected exactly one fielding gameLog group')
    group = groups[0]
    splits = group.get('splits')
    if not isinstance(splits, list):
        raise ValueError('Missing splits')
    if 'totalSplits' in group and integer(group['totalSplits'], 'totalSplits') != len(splits):
        raise ValueError('Truncated source response')
    rows = []
    seen = set()
    for split in splits:
        stat = split['stat']
        pid = integer(split['player']['id'], 'player id')
        year = integer(split['season'], 'season')
        sport = integer(split['sport']['id'], 'sport id')
        day = date.fromisoformat(split['date'])
        if pid != player_id or year != season or sport != sport_id or day.year != season:
            raise ValueError('Player, season, date or sport scope mismatch')
        if split.get('gameType') != 'R':
            raise ValueError('Not a regular-season game')
        position = split['position']
        code = str(position['code'])
        if POSITION_CODE_ABBREVIATION.get(code) != position.get('abbreviation'):
            raise ValueError('Invalid position code or abbreviation')
        if stat.get('position') != position:
            raise ValueError('Split and stat positions disagree')
        games = integer(stat['games'], 'games')
        played = integer(stat['gamesPlayed'], 'games played')
        started = integer(stat['gamesStarted'], 'games started')
        if games != 1 or played != 1 or started > played:
            raise ValueError('Invalid position-game exposure')
        outs = baseball_innings_to_outs(stat['innings'])
        if code == '10' and outs != 0:
            raise ValueError('DH cannot have fielding outs')
        game = integer(split['game']['gamePk'], 'game id')
        if not game:
            raise ValueError('Missing game id')
        key = (pid, game, code)
        if key in seen:
            raise ValueError('Duplicate player-game-position')
        seen.add(key)
        rows.append(dict(player_id=pid, season=year, sport_id=sport,
            league_id=integer(split['league']['id'], 'league id'),
            team_id=integer(split['team']['id'], 'team id'), game_id=game,
            date=day.isoformat(), period='before_August' if day.month < 8 else 'August_onward',
            position_code=int(code), position=position['abbreviation'], fielding_outs=outs,
            appearances=played, raw_starts=started, reviewed_starts=started,
            certified_dual_DH_addition=0, source_id=source_id, correction_source=None))
    return sorted(rows, key=lambda r: (r['date'], r['game_id'], r['position_code']))


def apply_dual_dh(rows, corrections):
    """Apply dated, already certified P/DH additions once, never invent DH innings."""
    result = [dict(r) for r in rows]
    seen = set()
    for correction in corrections:
        if not correction['certified']:
            continue
        pid, year, game = correction['player_id'], correction['season'], correction['game_id']
        key = (pid, game)
        if key in seen:
            raise ValueError('Duplicate certified correction')
        seen.add(key)
        matches = [r for r in result if r['player_id'] == pid and r['game_id'] == game]
        pitching = [r for r in matches if r['position_code'] == 1 and r['raw_starts'] == 1]
        if len(pitching) != 1 or pitching[0]['date'] != correction['date'] or pitching[0]['season'] != year:
            raise ValueError('Certified correction lacks its exact dated pitching start')
        dh = [r for r in matches if r['position_code'] == 10]
        if not dh:
            # The two rule-certified P-only boxes legitimately omit a DH appearance.
            if correction.get('DH_evidence_basis') != 'rule_5_11b_starting_pitcher_in_lineup':
                raise ValueError('Missing DH appearance without rule certification')
            row = dict(pitching[0], position_code=10, position='DH', fielding_outs=0,
                       appearances=0, raw_starts=0, reviewed_starts=0,
                       source_id=correction['source_id'])
            result.append(row)
        elif len(dh) != 1:
            raise ValueError('Duplicate DH evidence')
        else:
            row = dh[0]
        if row['raw_starts'] != 0 or row['reviewed_starts'] != 0 or row['certified_dual_DH_addition']:
            raise ValueError('DH start would be double counted')
        row['reviewed_starts'] = 1
        row['certified_dual_DH_addition'] = 1
        row['correction_source'] = correction['source_id']
    return sorted(result, key=lambda r: (r['date'], r['game_id'], r['position_code']))


def position_totals(rows):
    totals = {}
    for r in rows:
        key = (r['sport_id'], r['league_id'], r['position_code'])
        values = totals.setdefault(key, dict(fielding_outs=0, raw_starts=0,
            reviewed_starts=0, appearances=0, certified_dual_DH_addition=0))
        for field in values:
            values[field] += r[field]
    return totals
