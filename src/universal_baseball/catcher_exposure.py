"""Chronological source accounting; no fitted catcher skill or causal credit."""
from collections import Counter, defaultdict
import json
from universal_baseball.defensive_timeline import initial_defense, apply_substitution


class ExposureError(ValueError):
    pass


BASE={'1B':1,'2B':2,'3B':3}


def battery_timeline(payload):
    """Versioned C/P-only certification; never repair missing other fielders."""
    defense,membership,slots=initial_defense(payload)
    states={};pitches=[];credits=[];matchups=[]
    for play in sorted(payload['liveData']['plays']['allPlays'],key=lambda a:a['about']['atBatIndex']):
        ab=play['about']['atBatIndex'];side='home' if play['about']['isTopInning'] else 'away'
        last=None
        for event in sorted(play.get('playEvents',[]),key=lambda e:e['index']):
            key=(ab,event['index'])
            if key in states:raise ExposureError(f'Duplicate event {key}')
            apply_substitution(defense,membership,slots,event,side)
            state=defense[side].copy();states[key]=state
            if event.get('isPitch'):
                if state.get(1) is None or state.get(2) is None or state[1]==state[2]:
                    raise ExposureError(f'Unknown battery at pitch {key}')
                pitches.append({'at_bat_index':ab,'event_index':event['index'],
                    'pitcher_id':state[1],'catcher_id':state[2],'defense_side':side,
                    'full_lineup_known':set(state)==set(range(1,10)) and len(set(state.values()))==9,
                    'pitch_id':event.get('playId'),'pitch_number':event.get('pitchNumber'),
                    'call_code':event.get('details',{}).get('call',{}).get('code')})
                last=state[1]
        if last is not None:
            expected=play.get('matchup',{}).get('pitcher',{}).get('id')
            matchups.append({'at_bat_index':ab,'observed':last,'expected':expected,'match':last==expected})
        for runner in play.get('runners',[]):
            key=(ab,runner.get('details',{}).get('playIndex'));state=states.get(key,{})
            for credit in runner.get('credits',[]):
                code=credit.get('position',{}).get('code')
                if str(code) not in ['1','2']:continue
                pid=credit.get('player',{}).get('id');actual=state.get(int(code))
                credits.append({'at_bat_index':ab,'event_index':key[1],'position':int(code),
                    'observed':actual,'expected':pid,'match':actual is not None and actual==pid})
    return {'snapshots':states,'pitches':pitches,'credits':credits,'matchups':matchups}


def apply_movements(bases,outs,rows):
    """Move all runners simultaneously; duplicate movements are not extra outs."""
    grouped=defaultdict(list)
    for row in rows:
        m=row['movement'];rid=row.get('details',{}).get('runner',{}).get('id')
        if rid is None:raise ExposureError('Movement missing runner ID')
        # Explicit placeholder records contain no movement/out, not an extra PA.
        if all(m.get(c) is None for c in ['start','end','isOut','outNumber']):continue
        if m not in grouped[rid]:grouped[rid].append(m)
    outcomes={};out_numbers=[]
    for rid,moves in grouped.items():
        old=[b for b,p in bases.items() if p==rid]
        current=old[0] if old else None
        # Scoring can contain a return-to-base leg, e.g. 1B->2B->1B->score.
        # Require all recorded legs to form a complete path. Never select an
        # attractive final row or infer an intermediate exposure from that path.
        if len(moves)>8:raise ExposureError('Too many movement legs to certify')
        def paths(where,remaining,retired=False,scored=False,ordinals=()):
            if not remaining:return {(where,ordinals)}
            if retired or scored:return set()
            answers=set()
            for i,m in enumerate(remaining):
                if BASE.get(m.get('start'))!=where:continue
                rest=remaining[:i]+remaining[i+1:]
                if m.get('isOut'):
                    if m.get('outNumber') is None:continue
                    answers |= paths(None,rest,retired=True,ordinals=(*ordinals,int(m['outNumber'])))
                elif m.get('end')=='score':answers |= paths(None,rest,scored=True,ordinals=ordinals)
                elif m.get('end') in BASE:answers |= paths(BASE[m['end']],rest,ordinals=ordinals)
            return answers
        possible=paths(current,moves)
        if len(possible)!=1:raise ExposureError(f'Ambiguous/contradictory runner path id={rid} base={current} moves={moves}')
        end,ordinals=possible.pop();outcomes[rid]=end;out_numbers.extend(ordinals)
    expected=list(range(outs+1,outs+1+len(out_numbers)))
    if sorted(out_numbers)!=expected or outs+len(out_numbers)>3:
        raise ExposureError(f'Out sequence {out_numbers} does not follow {outs}')
    # On an inning-ending force the feed often omits irrelevant safe advances.
    # All recorded starts/outs were checked above; there is no post-third-out
    # live-base occupancy or another pitch opportunity to invent.
    if outs+len(out_numbers)==3:return {},3
    updated={b:r for b,r in bases.items() if r not in outcomes}
    for rid,end in outcomes.items():
        if end is None:continue
        if end in updated:raise ExposureError(f'Two runners occupy base {end}')
        updated[end]=rid
    return updated,outs+len(out_numbers)


def runner_timeline(payload):
    states={};checks=[];bases={};outs=0;half=None
    for play in sorted(payload['liveData']['plays']['allPlays'],key=lambda a:a['about']['atBatIndex']):
        about=play['about'];ab=about['atBatIndex'];newhalf=(about['inning'],about['isTopInning'])
        if newhalf!=half:bases={};outs=0;half=newhalf
        grouped=defaultdict(list)
        for row in play.get('runners',[]):grouped[row.get('details',{}).get('playIndex')].append(row)
        events=sorted(play.get('playEvents',[]),key=lambda e:e['index'])
        if set(grouped)-{e['index'] for e in events}:raise ExposureError(f'Runner movement without event at PA {ab}')
        balls=strikes=0
        for event in events:
            index=event['index'];key=(ab,index);kind=event.get('details',{}).get('eventType')
            if key in states:raise ExposureError('Duplicate event key')
            if kind=='runner_placed':
                base=event.get('base');rid=event.get('player',{}).get('id')
                if base not in [1,2,3] or rid is None or base in bases or rid in bases.values():
                    raise ExposureError('Conflicting/unknown placed runner')
                bases[base]=rid
            if kind=='offensive_substitution' and str(event.get('position',{}).get('code'))=='12':
                replaced=event.get('replacedPlayer',{}).get('id');rid=event.get('player',{}).get('id')
                where=[b for b,r in bases.items() if r==replaced]
                if len(where)!=1 or rid is None or rid in bases.values():raise ExposureError('Pinch runner not reconciled')
                bases[where[0]]=rid
            states[key]={'bases':bases.copy(),'outs':outs,'balls':balls,'strikes':strikes}
            try:bases,outs=apply_movements(bases,outs,grouped[index])
            except ExposureError as exc:raise ExposureError(f'PA {ab} event {index}: {exc}') from exc
            count=event.get('count',{})
            balls=count.get('balls',balls);strikes=count.get('strikes',strikes)
        expected={b:play.get('matchup',{}).get(name,{}).get('id') for b,name in
            [(1,'postOnFirst'),(2,'postOnSecond'),(3,'postOnThird')]}
        expected={b:r for b,r in expected.items() if r is not None}
        end={} if outs==3 else bases
        expected_outs=play.get('count',{}).get('outs')
        checks.append({'at_bat_index':ab,'bases':json.dumps(end,sort_keys=True),
            'expected_bases':json.dumps(expected,sort_keys=True),'outs':outs,'expected_outs':expected_outs,
            'match':end==expected and outs==expected_outs})
        if not checks[-1]['match']:
            raise ExposureError(f'Post-PA mismatch {checks[-1]}')
    return {'snapshots':states,'checks':checks}


def attach_exposures(payload,events,battery,runners):
    """Keep every numerator, even when no defensible physical pitch link exists."""
    state=runners['snapshots'] if runners else {}
    pitchrows=[];pitchmap={};idmap=defaultdict(list);eventmap={}
    for play in payload['liveData']['plays']['allPlays']:
        ab=play['about']['atBatIndex']
        for ev in play.get('playEvents',[]):
            key=(ab,ev['index']);eventmap[key]=ev
            if ev.get('isPitch') and ev.get('playId'):idmap[(ab,ev['playId'])].append(key)
    for p in battery['pitches']:
        key=(p['at_bat_index'],p['event_index']);s=state.get(key);bases=s['bases'] if s else {}
        row={**p,'runner_state_known':s is not None,
            **{f'runner_{b}':bases.get(b) for b in [1,2,3]},
            'pre_outs':s['outs'] if s else None,'pre_strikes':s['strikes'] if s else None,
            'pre_balls':s['balls'] if s else None,
            'blocking_at_risk':bool(bases) or (s['strikes']==2 and (1 not in bases or s['outs']==2)) if s else None}
        pitchrows.append(row);pitchmap[key]=row
    assigned=[]
    for e in events:
        key=(e['at_bat_index'],e['event_index']);ev=eventmap.get(key,{})
        possible=[key] if key in pitchmap else idmap.get((key[0],ev.get('actionPlayId')),[])
        linked=possible[0] if len(possible)==1 else None
        b=battery['snapshots'].get(key,{})
        cp=(b.get(1),b.get(2));cert=all(x is not None for x in cp) and cp[0]!=cp[1]
        s=state.get(key);pitch=pitchmap.get(linked,{})
        rid=e.get('runner_id');from_base=next((k for k,v in s['bases'].items() if v==rid),None) if s and rid else None
        assigned.append({**e,'pitcher_id':cp[0] if cert else None,'catcher_id':cp[1] if cert else None,
            'battery_attribution':'CP_timeline_v2' if cert else 'unresolved',
            'linked_pitch_index':linked[1] if linked else None,
            'pitch_link':'exact_event' if linked==key else 'exact_actionPlayId' if linked else 'unlinked',
            'link_battery_match':cp==(pitch.get('pitcher_id'),pitch.get('catcher_id')) if linked else None,
            'linked_blocking_at_risk':pitch.get('blocking_at_risk'),
            'runner_state_known':s is not None,'runner_from_base':from_base,
            'pre_runner_count':len(s['bases']) if s else None,'pre_outs':s['outs'] if s else None})
    risks=[]
    for p in pitchrows:
        if not p['runner_state_known']:continue
        for base in [1,2,3]:
            rid=p[f'runner_{base}']
            if rid is not None:
                risks.append({'at_bat_index':p['at_bat_index'],'event_index':p['event_index'],
                    'catcher_id':p['catcher_id'],'pitcher_id':p['pitcher_id'],'runner_id':rid,
                    'from_base':base,'next_base_occupied':base<3 and p[f'runner_{base+1}'] is not None})
    return {'pitches':pitchrows,'events':assigned,'runner_pitches':risks}


def pitch_box_checks(payload,pitches):
    counts=Counter((r['defense_side'],r['pitcher_id']) for r in pitches);result=[]
    for side,team in payload['liveData']['boxscore']['teams'].items():
        for player in team['players'].values():
            stats=player.get('stats',{}).get('pitching',{})
            if not stats:continue
            rid=player['person']['id'];official=stats.get('numberOfPitches')
            result.append({'side':side,'player_id':rid,'official':official,'observed':counts[(side,rid)],
                'status':'unknown' if official is None else 'match' if official==counts[(side,rid)] else 'mismatch'})
    return result
