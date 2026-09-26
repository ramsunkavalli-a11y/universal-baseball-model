"""Reconstruct event-time defense independently of terminal-PA snapshots."""
from __future__ import annotations

from collections import Counter


class TimelineError(ValueError):
    pass


def initial_defense(payload):
    teams=payload['liveData']['boxscore']['teams']
    defense={};membership={};slots={}
    for side in ('home','away'):
        candidates={};order={}
        for player in teams[side]['players'].values():
            pid=player['person']['id']
            membership.setdefault(pid,set()).add(side)
            if player.get('stats',{}).get('fielding',{}).get('gamesStarted')==1:
                allpos=player.get('allPositions') or [player.get('position',{})]
                code=allpos[0].get('code')
                if str(code) not in {str(n) for n in range(1,10)}:
                    raise TimelineError('Starter position unavailable')
                position=int(code)
                candidates.setdefault(position,[]).append(pid)
            raw=player.get('battingOrder')
            if raw is not None and int(raw)%100==0:
                slot=int(raw)//100
                if slot in order:raise TimelineError('Duplicate starting batting slot')
                order[slot]=pid
        # Official gamesStarted can describe actual first defensive appearance,
        # while allPositions begins with a pregame role. Do not guess between
        # duplicate candidates; only explicit pre-first-pitch actions may resolve.
        positions={pos:ids[0] for pos,ids in candidates.items() if len(ids)==1}
        defense[side]=positions;slots[side]=order
    return defense,membership,slots


def apply_substitution(defense,membership,slots,event,defense_side):
    kind=event.get('details',{}).get('eventType')
    if kind not in ('pitching_substitution','defensive_substitution','defensive_switch','offensive_substitution'):
        return False
    pid=event.get('player',{}).get('id')
    if pid not in membership:raise TimelineError('Substitution has no known player/team')
    side=('away' if defense_side=='home' else 'home') if kind=='offensive_substitution' else defense_side
    if side not in membership[pid]:raise TimelineError('Substitution player not on acting team')
    state=defense[side]
    raw=event.get('battingOrder');slot=int(raw)//100 if raw is not None else None
    replaced=event.get('replacedPlayer',{}).get('id')
    if kind=='offensive_substitution' and replaced is None:
        replaced=slots[side].get(slot)
        if replaced is None:raise TimelineError('Offensive replacement not identified')
    if replaced is not None and side not in membership.get(replaced,set()):
        raise TimelineError('Replacement belongs to wrong/unknown team')
    # Clear old positions first. A group of switches may be temporarily incomplete
    # between actions but must be complete at every actual pitch/runner event.
    for pos,current in list(state.items()):
        if current==pid or (replaced is not None and current==replaced):
            del state[pos]
    if kind!='offensive_substitution':
        code=event.get('position',{}).get('code')
        if kind=='pitching_substitution' and code is None:code='1'
        if str(code) not in {str(n) for n in range(1,11)}:
            raise TimelineError('Unrecognized defensive assignment')
        if int(code)<=9:state[int(code)]=pid
    if slot is not None:slots[side][slot]=pid
    return True


def defensive_timeline(payload):
    defense,membership,slots=initial_defense(payload)
    snapshots={};terminals=[];credits=[];changes=[];pitch_counts=Counter();matchups=[]
    plays=payload['liveData']['plays']['allPlays']
    if len({a['about']['atBatIndex'] for a in plays})!=len(plays):raise TimelineError('Duplicate play index')
    for play in sorted(plays,key=lambda a:a['about']['atBatIndex']):
        ab=play['about']['atBatIndex'];side='home' if play['about']['isTopInning'] else 'away'
        events=play.get('playEvents',[])
        if len({e['index'] for e in events})!=len(events):raise TimelineError('Duplicate event index')
        last_pitch=None
        for event in sorted(events,key=lambda e:e['index']):
            index=event['index']
            if apply_substitution(defense,membership,slots,event,side):
                changes.append({'at_bat_index':ab,'event_index':index,'type':event['details']['eventType'],
                    'player_id':event['player']['id']})
            state=defense[side].copy()
            snapshots[(ab,index)]=state
            if event.get('isPitch'):
                if set(state)!=set(range(1,10)) or len(set(state.values()))!=9:
                    raise TimelineError(f'Incomplete defense at pitch {ab}/{index}')
                pitch_counts[state[1]]+=1
                last_pitch=(ab,index,state)
        if last_pitch is not None:
            _,index,state=last_pitch
            terminals.append({'at_bat_index':ab,'event_index':index,**{f'fielder_{k}':v for k,v in state.items()}})
            expected=play.get('matchup',{}).get('pitcher',{}).get('id')
            matchups.append({'at_bat_index':ab,'timeline_pitcher':state[1],'matchup_pitcher':expected,
                'match':state[1]==expected})
        for runner in play.get('runners',[]):
            d=runner.get('details',{});index=d.get('playIndex')
            state=snapshots.get((ab,index))
            for credit in runner.get('credits',[]):
                raw=credit.get('position',{}).get('code');pid=credit.get('player',{}).get('id')
                if str(raw) not in {str(n) for n in range(1,10)}:continue
                expected=state.get(int(raw)) if state else None
                credits.append({'at_bat_index':ab,'event_index':index,'position':int(raw),
                    'credited_id':pid,'timeline_id':expected,'credit':credit.get('credit'),
                    'match':expected is not None and expected==pid})
    return {'snapshots':snapshots,'terminal':terminals,'credits':credits,'changes':changes,
        'pitch_counts':dict(pitch_counts),'matchups':matchups}


def attach_battery(events,timeline):
    result=[]
    for row in events:
        state=timeline['snapshots'].get((row['at_bat_index'],row['event_index']))
        if state is None or set(state)!=set(range(1,10)):
            result.append({**row,'battery_attribution':'unresolved_timeline'})
        else:
            result.append({**row,'pitcher_id':state[1],'catcher_id':state[2],
                'battery_attribution':'chronological_lineup_and_actions'})
    return result


def player_box_checks(payload,events,timeline):
    checks=[]
    for side in ('home','away'):
        players=payload['liveData']['boxscore']['teams'][side]['players']
        for player in players.values():
            pid=player['person']['id'];stats=player.get('stats',{})
            specs=[]
            if stats.get('pitching'):
                specs += [('WP','pitching','wildPitches','pitcher_id',{'WP'}),
                    ('pitcher_SB','pitching','stolenBases','pitcher_id',{'SB'}),
                    ('pitcher_CS','pitching','caughtStealing','pitcher_id',{'CS','POCS'})]
            positions={str(p.get('code')) for p in player.get('allPositions',[])}|{str(player.get('position',{}).get('code'))}
            if '2' in positions and stats.get('fielding'):
                specs += [('PB','fielding','passedBall','catcher_id',{'PB'}),
                    ('catcher_SB','fielding','stolenBases','catcher_id',{'SB'}),
                    ('catcher_CS_presence','fielding','caughtStealing','catcher_id',{'CS','POCS'})]
            for name,group,key,identity,kinds in specs:
                value=stats.get(group,{}).get(key)
                count=sum(e.get(identity)==pid and e['defense_side']==side and e['family'] in kinds for e in events)
                checks.append({'side':side,'player_id':pid,'metric':name,'official':value,'ledger':count,
                    'status':'unknown' if value is None else 'match' if value==count else 'mismatch'})
    return checks
