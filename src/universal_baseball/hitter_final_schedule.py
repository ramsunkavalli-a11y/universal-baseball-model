"""Count completed regular-season games, not postponed schedule appearances."""
from collections import Counter,defaultdict


def completed_schedule(payload,season):
    groups=defaultdict(list)
    for d in payload.get('dates',[]):
        for g in d.get('games',[]):
            if g['gameType']!='R' or not str(g['officialDate']).startswith(f'{season}-'):
                raise ValueError('Unexpected target game season/type')
            groups[g['gamePk']].append(dict(listing_date=d['date'],**g))
    final=[];reschedules=[];unresolved=[]
    for pk,versions in groups.items():
        participants={tuple(v['teams'][side]['team']['id'] for side in ['away','home']) for v in versions}
        if len(participants)!=1:raise ValueError('Conflicting game participants')
        played=[v for v in versions if v['status']['codedGameState'] in ['F','O'] and v['status']['abstractGameState']=='Final']
        if played:
            if len({v['officialDate'] for v in played})!=1:raise ValueError('Ambiguous played game dates')
            chosen=next((v for v in played if v['status']['codedGameState']=='F'),played[0])
            final.append(chosen)
            if len(versions)>1:reschedules.append(dict(game_pk=pk,versions=versions,completed_listing=chosen['listing_date']))
        elif not all(v['status']['detailedState']=='Cancelled' for v in versions):
            unresolved.append(dict(game_pk=pk,versions=versions))
    counts=Counter(v['teams'][side]['team']['id'] for v in final for side in ['away','home'])
    return dict(schedule_entries=sum(map(len,groups.values())),unique_regular_games=len(groups),completed_games=len(final),
        team_game_counts=dict(counts),resolved_multiple_listing_games=reschedules,unresolved_games=unresolved,
        complete_regular_season_coverage=len(final)>=2400 and len(counts)==30 and min(counts.values(),default=0)>=160 and not unresolved)
