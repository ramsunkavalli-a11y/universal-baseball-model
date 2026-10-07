"""Only completed detailed schedule states describe played role segments."""
from universal_baseball.defense_role_logs import integer
from universal_baseball.defense_role_scope import schedule_context


def completed_schedule_context(payload, *, season, sport_id):
    count=sum(len(day['games']) for day in payload['dates'])
    if count!=integer(payload['totalGames'],'total games'):
        raise ValueError('Truncated schedule')
    dates=[]
    for day in payload['dates']:
        games=[]
        for g in day['games']:
            if g['gameType']!='R' or int(g['season'])!=season:
                raise ValueError('Schedule scope mismatch')
            detail=g['status']['detailedState']
            if detail.startswith('Final') or detail.startswith('Completed Early'):
                games.append(g)
        if games:dates.append(dict(day,games=games))
    filtered=dict(payload,dates=dates,totalGames=sum(len(d['games']) for d in dates))
    return schedule_context(filtered,season=season,sport_id=sport_id)
