"""Replay dated status independently, then attach source walks and unchanged outcomes."""
from collections import Counter,defaultdict
from datetime import date
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import polars as pl

from prepare_hitter_status_evidence import ROOT,sources,read,save,FIXED
from prepare_hitter_status_evidence_v2 import OUT,ORIGINAL
from recover_hitter_status_evidence import save_wire
from prepare_foreign_component_translation import verify
from universal_baseball.storage import sha256_file


def independent_events(raw, teams, cutoff):
    found={}
    for r in raw:
        dates=[str(r[k])[:10] for k in ['date','effectiveDate','resolutionDate'] if r.get(k)]
        if not r.get('date') or not dates or max(dates)>cutoff:continue
        a=(r.get('fromTeam') or {}).get('id');b=(r.get('toTeam') or {}).get('id')
        text=(r.get('description') or '').lower();typ=(r.get('typeDesc') or '').lower();code=r.get('typeCode')
        if a not in teams and b not in teams or any(w in text for w in ['rehab assignment','all-stars','all stars']):continue
        negative=typ in {'released','declared free agency','free agency'} or 'elected free agency' in text or ' released ' in text
        if negative:kind='release'
        elif code=='RET':kind='retirement'
        elif code in {'OUT','DES'} or 'outrighted' in text or ('designated' in text and 'assignment' in text):kind='reserve_departure'
        elif b in teams:
            if 'minor league contract' in text or 'minor-league contract' in text:kind='minor_agreement'
            elif code=='SFA' or typ=='signed as free agent' or 'signed ' in text:kind='agreement_unspecified'
            elif code in {'CU','SE'} or any(w in text for w in ['selected the contract','selected contract',' activated ','reinstated']):kind='major_activation'
            elif code in {'TR','CLW','R5','PUR','CP'} or typ in {'trade','claimed off waivers','selected off waivers','rule 5 draft','purchased'}:kind='acquisition'
            else:continue
        else:continue
        key=tuple(r.get(k) for k in ['id','typeCode','date','effectiveDate','resolutionDate'])+(r.get('person',{}).get('id'),a,b)
        obj=dict(known=max(dates),kind=kind,team=b if b in teams else a,raw=r)
        assert key not in found or found[key]==obj
        found[key]=obj
    return list(found.values())


def independent_employment(events):
    grouped=defaultdict(list)
    for r in events:grouped[r['known']].append(r)
    team=None;major=False;amb=False;status='unknown';trace=[]
    for day,rows in sorted(grouped.items()):
        add=[r for r in rows if r['kind'] in {'major_activation','minor_agreement','agreement_unspecified','acquisition'}]
        remove=[r for r in rows if r['kind'] in {'release','retirement'}]
        exit_=[r for r in rows if r['kind']=='reserve_departure']
        if add:
            clubs={r['team'] for r in add}
            if len(clubs)>1 or any(r['team'] in clubs for r in remove+exit_):
                status='ambiguous_same_date';team=None;major=False;amb=True
            else:
                club=next(iter(clubs));kinds={r['kind'] for r in add}
                major=('major_activation' in kinds) or (major and team==club)
                team=club;amb=False
                status=next(k for k in ['major_activation','minor_agreement','agreement_unspecified','acquisition'] if k in kinds)
        elif any(team is None or r['team']==team for r in remove):
            relevant=[r for r in remove if team is None or r['team']==team]
            status='reported_retirement' if any(r['kind']=='retirement' for r in relevant) else 'reported_release'
            team=None;major=False;amb=False
        elif exit_ and (team is None or any(r['team']==team for r in exit_)):
            status='reserve_departure_organization_unconfirmed';major=False
            clubs={r['team'] for r in exit_}
            if team is None and len(clubs)==1:team=next(iter(clubs))
        trace.append(dict(date=day,kinds=sorted({r['kind'] for r in rows}),state=status,
            team_id=team,explicit_major_link=major,same_date_conflict=amb))
    return dict(state=status,team_id=team,explicit_major_link=major,same_date_conflict=amb,
        latest_date=trace[-1]['date'] if trace else None,trace=trace)


def eligible_records(records, cutoff):
    versions={}
    for r in records:
        if r['available_date']>cutoff:continue
        key=(r['transaction_id'],r['player_id']);previous=versions.get(key)
        if previous and previous['available_date']==r['available_date']:
            assert (previous['description'],previous['event_date'])==(r['description'],r['event_date'])
        if previous is None or r['available_date']>previous['available_date']:versions[key]=r
    return list(versions.values())


def independent_absence(records, cutoff):
    mapping={'suspended_unspecified':'suspended','restricted':'restricted','administrative_leave':'administrative',
        'ineligible_unspecified':'ineligible','finite_ineligible':'ineligible','permanent_ineligible':'ineligible','deceased':'deceased'}
    byday=defaultdict(list)
    for r in eligible_records(records,cutoff):byday[r['event_date']].append(r)
    active={};retired=False;cleared_once=False
    for day,rows in sorted(byday.items()):
        restrictions=defaultdict(list);clears=defaultdict(list)
        for r in rows:
            text=r['description'].lower();kind=r['kind']
            if kind in mapping:restrictions[mapping[kind]].append(r)
            if kind in {'nonmedical_activation','reinstated'}:
                channels={name for words,name in [(['restricted'],'restricted'),(['administrative'],'administrative'),
                    (['suspended','suspension'],'suspended'),(['ineligible'],'ineligible')] if any(w in text for w in words)}
                if len(channels)==1:clears[next(iter(channels))].append(kind)
            if kind=='mlb_activation' and r.get('il_kind')!='activation' and not any(w in text for w in
                ['injured','disabled','paternity','bereavement','restricted','administrative']):clears['suspended'].append(kind)
        for channel in set(restrictions)|set(clears):
            incoming=restrictions[channel]
            if incoming:
                choice=max(incoming,key=lambda r:(r['kind']=='permanent_ineligible',r['kind']=='finite_ineligible',bool(r.get('duration_games'))))
                permanent=active.get(channel,{}).get('kind')=='permanent_ineligible'
                k='permanent_ineligible' if permanent else choice['kind']
                info=dict(kind=k,event_date=day.isoformat(),ambiguous=bool(clears[channel]) and channel!='deceased')
                if choice.get('duration_games'):info['duration_games']=choice['duration_games']
                if k=='finite_ineligible':
                    durations={int(r['duration_years']) for r in incoming if r['kind']=='finite_ineligible'};assert len(durations)==1
                    yy=day.year+next(iter(durations));dd=28 if day.month==2 and day.day==29 and yy%4!=0 else day.day
                    info['calendar_end']=date(yy,day.month,dd).isoformat()
                active[channel]=info
            elif channel in active and clears[channel] and channel!='deceased':
                if active[channel]['kind']!='permanent_ineligible' or 'reinstated' in clears[channel]:
                    del active[channel];cleared_once=True
        kinds={r['kind'] for r in rows}
        if 'retired' in kinds:retired=True
        elif kinds&{'org_acquisition','minor_contract','foreign_return_signing'}:retired=False
    expired=[k for k,r in active.items() if r.get('calendar_end') and r['calendar_end']<=cutoff.isoformat()]
    for k in expired:del active[k]
    hard='deceased' in active or any(r['kind']=='permanent_ineligible' for r in active.values())
    if 'deceased' in active:state='deceased'
    elif hard:state='permanent_ineligible'
    elif any(r['ambiguous'] for r in active.values()):state='ambiguous_same_date_restriction'
    elif any(r.get('duration_games') for r in active.values()):state='finite_game_suspension'
    elif any(r.get('calendar_end') for r in active.values()):state='finite_calendar_ineligibility'
    elif set(active)=={'suspended'}:state='suspension_unspecified'
    elif active:state='unresolved_nonmedical'
    elif expired:state='finite_end_elapsed_return_unconfirmed'
    else:state='reported_nonmedical_reinstatement' if cleared_once else 'no_captured_restriction'
    return dict(state=state,active=active,hard=hard,retired=retired)


def main():
    assert not (OUT/'independent-review.json').exists(),'Preserve completed review'
    receipt=read(OUT/'preparation-receipt.json');verify(receipt['source_hashes']);verify(receipt['artifact_hashes'])
    population,_,records,teams,reports,_,_=sources()
    raw=defaultdict(list)
    for path in receipt['source_hashes']:
        p=ROOT/path
        if p.name.startswith('transactions-') and p.suffix=='.json' and not p.name.endswith('.metadata.json'):
            for r in read(p)['transactions']:
                if (pid:=(r.get('person') or {}).get('id')):raw[pid].append(r)
    ledger=read(OUT/'status-ledger.json')['rows'];lookup={r['candidate_key']:r for r in ledger}
    assert len(lookup)==len(population)==83300 and set(lookup)=={p['candidate_key'] for p in population}
    ages=[];unscoped=Counter();multi=Counter();checked=0
    for p in population:
        r=lookup[p['candidate_key']];pid=p['player_id'];cutoff=date.fromisoformat(p['information_date'])
        assert all(r[k]==p[k] for k in ['candidate_key','player_id','origin_year','target_year','information_date'])
        employment=independent_employment(independent_events(raw[pid],teams,p['information_date']))
        assert employment==r['employment'],p['candidate_key']
        a=independent_absence(records[pid],cutoff)
        assert (a['state'],a['active'],a['hard'],a['retired'])==(r['absence']['state'],r['absence']['active_restrictions'],
            r['absence']['hard_unavailable'],r['absence']['retired_evidence']),p['candidate_key']
        games=[q['duration_games'] for q in a['active'].values() if q.get('duration_games')]
        ends=[q['calendar_end'] for q in a['active'].values() if q.get('calendar_end')]
        assert r['absence']['original_duration_games']==(games[0] if len(games)==1 else None)
        assert r['absence']['known_calendar_end']==(max(ends) if ends else None)
        eligible=[q for q in reports[pid] if q['known_date']<=p['information_date'] and q['event_date']<=p['information_date']
            and a['active'].get('suspended',{}).get('duration_games') and q['event_date']==a['active']['suspended']['event_date']]
        report=max(eligible,key=lambda q:q['known_date']) if eligible else None
        assert r['absence']['return_report']==report
        conflict=bool(p['roster_cross_team_conflict'] or p['roster_status_conflict'] or employment['same_date_conflict'])
        positive=p['returned_40man'] and employment['state'] in {'reported_release','reported_retirement','reserve_departure_organization_unconfirmed'}
        expected=dict(status_major_link=bool(p['returned_40man'] and not conflict and not positive or employment['explicit_major_link'] and not conflict),
            status_minor_agreement=employment['state']=='minor_agreement',status_agreement_unspecified=employment['state']=='agreement_unspecified',
            status_acquisition_only=employment['state']=='acquisition',status_released=employment['state']=='reported_release',
            status_employment_unknown=employment['state']=='unknown' and not p['returned_40man'],status_employment_conflict=bool(conflict or positive),
            status_negative_listing_conflict=bool(not p['returned_40man'] and employment['explicit_major_link'] and not conflict),
            status_positive_listing_conflict=bool(positive),status_hard_unavailable=a['hard'],
            status_finite_nonmedical=bool(games or ends),status_unresolved_nonmedical=any(q['ambiguous'] or q['kind'] in
                {'restricted','administrative_leave','ineligible_unspecified'} or q['kind']=='suspended_unspecified' and not q.get('duration_games')
                for q in a['active'].values()),status_medical_evidence_open=any(s['open'] for s in r['clinical_spells']),
            status_medical_scope_interrupted=any(s['closure_kind']=='observation_scope_exit' for s in r['clinical_spells']))
        assert all(r[k]==v for k,v in expected.items()),p['candidate_key']
        assert r['new_PA_forecast'] is None and not r['forecast_eligibility_approved'] and not r['current_rights_fully_certified']
        assert r['literal_returned_40man']==p['returned_40man'] and r['full_annual_availability_coverage']==(p['origin_year']>=2015)
        if employment['explicit_major_link'] and not p['returned_40man']:
            ages.append((cutoff-date.fromisoformat(employment['latest_date'])).days)
        if len(a['active'])>1:multi['multiple_active_restrictions']+=1
        unscoped['records']+=len(r['absence']['unscoped_return_evidence'])
        checked+=1
        if checked%15000==0:print(json.dumps(dict(independently_replayed=checked)),flush=True)
    # Peer membership is chosen exclusively from forecast-time information.
    foreign={r['candidate_key']:r for r in read(ROOT/'reports/generated/foreign-origin-inputs/origin-inputs.json')['rows']}
    fixed=list(FIXED);oldcases=read(ORIGINAL/'source-cases.json')['cases'];fixed.append((oldcases[-1]['name'],oldcases[-1]['player_id'],oldcases[-1]['origin_year']))
    poplookup={p['candidate_key']:p for p in population};peer_ids={}
    def foreign_flag(p):return bool(foreign.get(p['candidate_key'],{}).get('recent_foreign_pa',0))
    for name,pid,y in fixed:
        p=poplookup[f'{y}:{pid}'];s=lookup[p['candidate_key']];choices=[]
        for q in population:
            if q['origin_year']!=y or q['player_id']==pid or q['role_status']!=p['role_status'] or foreign_flag(q)!=foreign_flag(p):continue
            t=lookup[q['candidate_key']]
            if t['status_major_link']!=s['status_major_link']:continue
            d=abs(np.log1p(q['recent_mlb_pa'])-np.log1p(p['recent_mlb_pa']))+abs(np.log1p(q['recent_domestic_pa'])-np.log1p(p['recent_domestic_pa']))
            if foreign_flag(p):d+=abs(np.log1p(foreign[q['candidate_key']]['recent_foreign_pa'])-np.log1p(foreign[p['candidate_key']]['recent_foreign_pa']))
            choices.append(dict(candidate_key=q['candidate_key'],player_id=q['player_id'],distance=float(d)))
        peer_ids[p['candidate_key']]=sorted(choices,key=lambda q:(q['distance'],q['player_id']))[:3]
    save(OUT/'peer-membership-seal.json',dict(rule='same origin, source role status, observed recent foreign-history presence and positive major-link signal; nearest log recent MLB/domestic/foreign PA; stable ID ties; no outcome conditioning',rows=peer_ids,
        qualification='Exposure/status comparisons, not matched talent or guaranteed jobs; source role hints do not approve eligibility'))
    # Only after peer selection: historical outcomes through 2025, never 2026.
    path=ROOT/'reports/generated/practical-hitter-v31/dated-stints.parquet';stats=pl.read_parquet(path);assert stats['season'].max()==2025
    cols=['plate_appearances','hits','doubles','triples','home_runs','base_on_balls','intentional_walks','hit_by_pitch','strike_outs']
    annual=stats.filter(pl.col('sport_id')==1).group_by('player_id','season').agg(pl.col(cols).sum())
    actual={(r['player_id'],r['season']):r for r in annual.to_dicts()}
    anchor_path=ROOT/'reports/generated/hitter-minor-statcast-precision/scored-predictions.parquet'
    anchor=pl.read_parquet(anchor_path);assert anchor.height==30506
    for r in anchor.select('player_id','target_year','next_pa').to_dicts():
        assert r['next_pa']==actual.get((r['player_id'],r['target_year']),{}).get('plate_appearances',0)
    anchors={(r['player_id'],r['origin_year']):r for r in anchor.select('player_id','origin_year','preseason_p','preseason_conditional_pa','preseason_pa','combined_rate','combined_value','next_pa').to_dicts()}
    ctx_path=ROOT/'reports/generated/hitter-dated-context-integration/predictions.parquet'
    contexts={(r['player_id'],r['origin_year']):r for r in pl.read_parquet(ctx_path).select('player_id','origin_year','ctx_p','ctx_conditional_pa','ctx_pa').to_dicts()}
    cases=[]
    for name,pid,y in fixed:
        key=f'{y}:{pid}';p=poplookup[key];s=lookup[key]
        history=stats.filter((pl.col('player_id')==pid)&pl.col('season').is_between(y-2,y)).sort('season','sport_id','team_id').to_dicts()
        peers=[]
        for peer in peer_ids[key]:
            q=poplookup[peer['candidate_key']];peers.append(dict(peer,name=q['player_name'],source=q,status=lookup[q['candidate_key']],
                actual_next_MLB_PA=actual.get((q['player_id'],y+1),{}).get('plate_appearances',0),unchanged_forecast=anchors.get((q['player_id'],y))))
        cases.append(dict(name=name,player_id=pid,origin_year=y,source_population=p,actual_origin_domestic_stints=history,
            foreign_input=foreign.get(key),eligible_employment_events=sorted(independent_events(raw[pid],teams,p['information_date']),key=lambda r:r['known']),
            eligible_absence_records=eligible_records(records[pid],date.fromisoformat(p['information_date'])),
            first_status=next(c['status'] for c in oldcases if c['player_id']==pid and c['origin_year']==y),scoped_status=s,
            unchanged_forecast=anchors.get((pid,y)),previous_completed_context_forecast=contexts.get((pid,y)),
            actual_next_MLB_counts=actual.get((pid,y+1)),actual_next_MLB_PA=actual.get((pid,y+1),{}).get('plate_appearances',0),
            new_forecast=None,origin_only_peers=peers))
    save_wire(OUT/'reviewed-cases.json',dict(cases=cases,player_walkthrough_status='machine_traces_ready_manual_pending'))
    tests=subprocess.run([sys.executable,'-m','pytest','-p','no:cacheprovider','tests/test_hitter_status_evidence.py','tests/test_hitter_status_list_scopes.py','-q'],cwd=ROOT,capture_output=True,text=True)
    assert tests.returncode==0,tests.stdout+tests.stderr
    freeze=subprocess.run([sys.executable,'scripts/verify_hitter_full_2026_freeze.py'],cwd=ROOT,capture_output=True,text=True)
    assert freeze.returncode==0,freeze.stdout+freeze.stderr
    final=dict(status='full_replay_complete_manual_walk_pending',rows_replayed=checked,all_original_source_rows_retained=True,
        clinical_spells_unchanged_and_previously_reviewed_normalizer_reused=True,clinical_normalizer_newly_independently_reconstructed=False,
        changes=read(OUT/'changed-decisions.json'),summary=read(OUT/'summary.json'),multiple_restriction_rows=dict(multi),
        unscoped_return_evidence=dict(unscoped),negative_listing_explicit_major_event_age_days=dict(rows=len(ages),
            over_365_days=sum(a>365 for a in ages),over_730_days=sum(a>730 for a in ages),maximum=max(ages) if ages else None),
        historical_MLB_labels_reconstructed=30506,tests=tests.stdout,protected_freeze=json.loads(freeze.stdout),
        new_fits=0,forecasts_changed=False,deployment_approved=False,goal_achieved=False,
        hashes={**receipt['source_hashes'],**receipt['artifact_hashes'],str(Path(__file__).relative_to(ROOT)):sha256_file(Path(__file__)),
            str(path.relative_to(ROOT)):sha256_file(path),str(anchor_path.relative_to(ROOT)):sha256_file(anchor_path),
            str(ctx_path.relative_to(ROOT)):sha256_file(ctx_path),**{str(p.relative_to(ROOT)):sha256_file(p) for p in [OUT/'reviewed-cases.json',OUT/'peer-membership-seal.json']}})
    save(OUT/'independent-review.json',final)
    print(json.dumps({k:final[k] for k in ['status','rows_replayed','multiple_restriction_rows','negative_listing_explicit_major_event_age_days','unscoped_return_evidence','new_fits']}),flush=True)


if __name__=='__main__':main()
