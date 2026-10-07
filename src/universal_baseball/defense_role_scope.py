"""Team-aware annual role evidence with independently qualified period dates."""
from collections import defaultdict
from datetime import date

from universal_baseball.defense_role_logs import integer, parse_logs


def period(day):
    return 'before_August' if date.fromisoformat(day).month < 8 else 'August_onward'


def schedule_context(payload, *, season, sport_id):
    """No standings, biographies or future player outcomes are projected."""
    if season not in range(2021, 2025):
        raise ValueError('Historical role context restricted to 2021–2024')
    groups = defaultdict(list)
    count = 0
    for day in payload['dates']:
        for game in day['games']:
            count += 1
            if game['gameType'] != 'R' or int(game['season']) != season:
                raise ValueError('Schedule scope mismatch')
            if date.fromisoformat(day['date']).year != season:
                raise ValueError('Schedule date outside origin')
            teams = sorted(integer(game['teams'][s]['team']['id'], 'team id')
                           for s in ('home', 'away'))
            for side in ('home', 'away'):
                returned = game['teams'][side]['team'].get('sport', {}).get('id')
                if returned is not None and returned != sport_id:
                    raise ValueError('Schedule sport mismatch')
            groups[integer(game['gamePk'], 'game id')].append(dict(
                official_date=game['officialDate'], calendar_date=day['date'],
                teams=teams, resume_date=game.get('resumeGameDate'),
                resumed_from=game.get('resumedFromDate'),
                state=game['status']['abstractGameState'],
                resumed=bool(game.get('resumeDate') or game.get('resumedFrom'))))
    if count != integer(payload['totalGames'], 'total games'):
        raise ValueError('Truncated schedule')
    result = {}
    for pk, entries in groups.items():
        teams = {tuple(e['teams']) for e in entries}
        originals = {e['official_date'] for e in entries}
        dates = {e['calendar_date'] for e in entries}
        dates |= {e[k] for e in entries for k in ('resume_date', 'resumed_from') if e[k]}
        dates |= originals
        qualified = len(teams) == len(originals) == 1 and all(e['state'] == 'Final' for e in entries)
        periods = {period(d) for d in dates}
        result[pk] = dict(teams=list(next(iter(teams))) if len(teams) == 1 else None,
            official_date=next(iter(originals)) if len(originals) == 1 else None,
            dates=sorted(dates), qualified=qualified,
            resumed=any(e['resumed'] for e in entries),
            period=next(iter(periods)) if qualified and len(periods) == 1 else None)
    return result


def parse_team_logs(payload, *, player_id, season, sport_id, source_id, context):
    groups = payload.get('stats', [])
    if not groups:
        return []
    if len(groups) != 1:
        raise ValueError('Expected one fielding gameLog')
    group = groups[0]
    splits = group['splits']
    if 'totalSplits' in group and integer(group['totalSplits'], 'total splits') != len(splits):
        raise ValueError('Truncated source response')
    # Reuse the sealed strict scalar parser, changing only the record grain.
    rows = []
    seen = set()
    positions = defaultdict(set)
    for split in splits:
        singleton = dict(group, splits=[split], totalSplits=1)
        row = parse_logs(dict(stats=[singleton]), player_id=player_id,
            season=season, sport_id=sport_id, source_id=source_id)[0]
        key = (row['game_id'], row['team_id'], row['position_code'])
        if key in seen:
            raise ValueError('Duplicate player-game-team-position')
        seen.add(key)
        positions[row['game_id'], row['position_code']].add(row['team_id'])
        game = context.get(row['game_id'])
        qualified = bool(game and game['qualified'] and row['team_id'] in game['teams']
                         and row['date'] == game['official_date'])
        row['original_log_period'] = row['period']
        row['period'] = game['period'] if qualified else None
        row['date_status'] = ('unknown_schedule_context' if not qualified else
            'cross_period_resumption' if row['period'] is None else
            'same_period_resumption' if game['resumed'] else 'qualified_calendar_period')
        row['schedule_dates'] = game['dates'] if game else []
        rows.append(row)
    for (pk, _), teams in positions.items():
        if len(teams) > 1:
            game = context.get(pk)
            if not game or not game['qualified'] or not game['resumed'] or set(game['teams']) != teams:
                raise ValueError('Opposing-team position records lack resumed-game certification')
    return rows


def parse_people_isolated(payload, *, player_ids, season, sport_id, source_id, context):
    people = payload['people']
    if len(people) != len(player_ids) or {p['id'] for p in people} != set(player_ids):
        raise ValueError('Unexpected or missing people')
    parsed, errors = {}, {}
    for person in people:
        pid = person['id']
        try:
            parsed[pid] = parse_team_logs(dict(stats=person.get('stats', [])),
                player_id=pid, season=season, sport_id=sport_id,
                source_id=source_id, context=context)
        except (ValueError, KeyError, AssertionError) as exc:
            errors[pid] = str(exc)
    return parsed, errors


def certify_measurements(comparisons, rows):
    """Appearance disagreement must not null matching outs or starts."""
    mapping = {'fielding_outs': 'fielding_outs', 'reviewed_starts': 'raw_starts',
               'appearances': 'appearances'}
    result = {}
    for field, raw in mapping.items():
        annual = bool(rows and comparisons) and all(
            c['annual'][raw] == c['log'][raw] for c in comparisons)
        uncertain = [r for r in rows if r[field] > 0 and r['period'] is None]
        result[field] = dict(full_year=annual, periods=annual and not uncertain,
            uncertain_position_games=len(uncertain),
            uncertain_exposure=sum(r[field] for r in uncertain))
    return result
