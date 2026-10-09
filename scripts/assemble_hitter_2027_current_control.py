"""Dated current owners and reviewed service estimates from existing sources."""
from collections import Counter,defaultdict
from datetime import date
from pathlib import Path
import gzip,json,sys
import polars as pl
from capture_hitter_2027_origin_counts import ROOT,write_once
from capture_hitter_2027_membership import ASOF,OUT as SOURCE,capture
from universal_baseball.organization_rights import resolve_current_organizations
from universal_baseball.playing_time_roster_source import project_team_full_roster_candidates_payload
from universal_baseball.roster_entry_source import build_opening_control_states
from universal_baseball.control_season_source import project_season_window
from universal_baseball.control_events import materialize_control_stints,OPENING_CONTROL_STATE_SCHEMA
from universal_baseball.hitter_current_control import service_events,service_openings,service_bounds,resolve_selection_option_pairs
from universal_baseball.team_control import calculate_control_years
from universal_baseball.storage import sha256_file

OUT=ROOT/'reports/generated/hitter-2027-base/current-control'
PUBLIC=ROOT/'reports/model-evidence/hitter-2027-v1'
OLD=Path('C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/universal-baseball-model/reports/generated/league-control-chronology-safe-release/2026-09-08')


def main():
    reviewed_mode='--reviewed' in sys.argv
    destination=OUT/'reviewed-v2' if reviewed_mode else OUT
    receipt_prefix='current-control-reviewed-v2' if reviewed_mode else 'current-control'
    assert not (destination/'current-control.parquet').exists()
    destination.mkdir(parents=True,exist_ok=True)
    members=pl.read_parquet(ROOT/'reports/generated/hitter-2027-batting-refresh/forecast.parquet')
    bios=pl.read_parquet(SOURCE/'bios.parquet');names=dict(bios.select('player_id','player_name').iter_rows())
    names={pid:names[pid] for pid in members['player_id']}
    teams=capture('teams','/teams',dict(sportId=1,season=2026))['teams'];mlb={r['id'] for r in teams}
    affiliates=capture('control-affiliate-teams','/teams',dict(sportIds='11,12,13,14,16',season=2026))['teams']
    parents={r['id']:r['parentOrgId'] for r in affiliates if r.get('parentOrgId') in mlb and r['id'] not in mlb}
    candidates=[]
    for team in sorted(mlb):
        payload=capture(f'roster-{team}-fullRoster',f'/teams/{team}/roster',dict(rosterType='fullRoster',season=2026,date=str(ASOF)))
        candidates.append(project_team_full_roster_candidates_payload(payload,team_id=team,season=2026,as_of_date=ASOF))
    forty=pl.read_parquet(SOURCE/'forty-man.parquet')
    tx=pl.read_parquet(SOURCE/'transactions.parquet');entries=pl.read_parquet(SOURCE/'roster-entries.parquet')
    owners=resolve_current_organizations(pl.concat(candidates),forty,tx,as_of_date=ASOF,
        mlb_team_ids=mlb,affiliate_parent_organization_ids=parents,player_names=names).filter(pl.col('player_id').is_in(list(names)))
    assert len(owners)==len(names)==4851
    window=project_season_window(capture('control-season-2026','/seasons/2026',dict(sportId=1)),season=2026)
    start=window['start_date'][0];end=window['end_date'][0];assert end<ASOF
    opening=build_opening_control_states(entries,window,mlb_team_ids=mlb)
    events=service_events(tx,mlb)
    if reviewed_mode:events=resolve_selection_option_pairs(events,tx)
    openings,trace=service_openings(opening.opening_states,events,entries,2026,start)
    active_opening={}
    if reviewed_mode:
        for tid in sorted(mlb):
            payload=capture('control-opening-active-'+str(tid),f'/teams/{tid}/roster',dict(rosterType='active',season=2026,date=str(start)))
            for r in payload['roster']:
                if r.get('status',{}).get('code')!='A':continue
                pid=r['person']['id']
                assert pid not in active_opening or active_opening[pid]['source_snapshot_id']==f'official-active:{tid}:{start}'
                active_opening[pid]=dict(player_id=pid,season=2026,roster_state='mlb_active',source_snapshot_id=f'official-active:{tid}:{start}')
        merged={r['player_id']:r for r in openings.to_dicts()};merged.update(active_opening)
        openings=pl.DataFrame(list(merged.values()),schema=OPENING_CONTROL_STATE_SCHEMA)
    year_events=events.filter(pl.col('season')==2026)
    materialized=materialize_control_stints(openings,year_events,window,as_of_date=ASOF)
    years=calculate_control_years(materialized.stints,window,as_of_date=ASOF)
    annual={r['player_id']:r for r in years.to_dicts()}
    previous={r['player_id']:r for r in pl.read_parquet(OLD/'league-control-snapshot.parquet').to_dicts()}
    people={r['player_id']:r for r in pl.read_parquet(SOURCE/'people-control.parquet').to_dicts()}
    histories=defaultdict(list);event_by=defaultdict(list);entry_by=defaultdict(list);interval_by=defaultdict(list)
    for r in tx.to_dicts():histories[r['player_id']].append(r)
    for r in events.to_dicts():event_by[r['player_id']].append(r)
    for r in entries.to_dicts():entry_by[r['player_id']].append(r)
    for r in materialized.stints.to_dicts():interval_by[r['player_id']].append(r)
    opening_by={r['player_id']:r for r in openings.to_dicts()};trace_by={r['player_id']:r for r in trace}
    counts=pl.read_parquet(ROOT/'reports/generated/hitter-2027-base/stints.parquet').filter((pl.col('season')==2026)&(pl.col('level_group')=='MLB')).group_by('player_id').agg(pl.col('plate_appearances').sum())
    pa=dict(counts.iter_rows());active40=set(forty.filter(pl.col('on_40man'))['player_id'])
    result=[];review_details={}
    for owner in owners.to_dicts():
        pid=owner['player_id'];old=previous.get(pid,{});person=people[pid];yr=annual.get(pid,{})
        debut=person['mlb_debut_date'];baseline=old.get('baseline_service_days') if old.get('baseline_status')=='available' else None
        basis='accepted_FG_opening_2026_balance'
        if baseline is None and (debut is None or debut.year>=2026):baseline=0;basis='official_no_prior_MLB_debut'
        service=int(yr.get('service_days',0));problems=[]
        if baseline is None:problems.append('missing_prior_service_balance')
        if pid not in opening_by and debut is not None and debut<start:problems.append('missing_opening_state')
        if pa.get(pid,0)>0 and service==0:problems.append('MLB_PA_without_reconstructed_service')
        anchor=trace_by.get(pid,{}).get('event_date')
        if anchor is None:
            covers=[r['start_date'] for r in entry_by[pid] if r['start_date']<=start and (r['end_date'] is None or r['end_date']>=start)]
            anchor=max(covers) if covers else start
        if pid in active_opening:anchor=start
        critical=[r for r in event_by[pid] if anchor<=r['event_date']<=end and r['action']=='review']
        if critical:problems.append('ambiguous_service_events')
        # Different service states on one day are not resolved by arbitrary IDs.
        by_day=defaultdict(set)
        for r in event_by[pid]:
            if start<=r['event_date']<=end and r['action']=='set_state':
                by_day[r['event_date']].add(r['target_state'] in ('mlb_active','mlb_injured','mlb_service_list'))
        if any(len(v)>1 for v in by_day.values()):problems.append('same_day_service_conflict')
        bounds=None
        if reviewed_mode:
            known_opening=(pid in opening_by and not any(r['event_date']<start for r in critical)) or debut is None or (debut is not None and debut>=start)
            lower,upper,uncertain=service_bounds(interval_by[pid],event_by[pid],start,end,known_opening)
            bounds=dict(lower=lower,upper=upper,uncertain_calendar_days=uncertain)
            if lower==upper:
                service=lower
                problems=[p for p in problems if p not in ('ambiguous_service_events','same_day_service_conflict','missing_opening_state')]
            elif 'uncertain_service_balance' not in problems:problems.append('uncertain_service_balance')
        estimate=None if baseline is None else baseline+service
        resolved_service=estimate if not problems else None
        row=dict(**owner,as_of_date=ASOF,on_40man=pid in active40,mlb_debut_date=debut,
            opening_service_days=baseline,opening_service_basis=basis if baseline is not None else 'unresolved',
            current_service_days=service,service_days_estimate=estimate,service_days=resolved_service,
            service_time=None if resolved_service is None else f'{resolved_service//172}.{resolved_service%172:03d}',
            service_status='estimated_from_dated_sources' if not problems else 'review_required',
            review_reasons=';'.join(problems),current_option_year_used=yr.get('option_year_used',False),
            baseline_options_remaining=old.get('baseline_options_remaining'),
            old_snapshot_service_days=old.get('service_days'),old_snapshot_current_service_days=old.get('current_service_days'),
            current_service_lower=None if bounds is None else bounds['lower'],
            current_service_upper=None if bounds is None else bounds['upper'],
            official_service_register=False)
        result.append(row)
        review_details[pid]=dict(opening=opening_by.get(pid),opening_transaction=trace_by.get(pid),
            critical_events=critical,intervals=interval_by[pid],service_bounds=bounds,
            transactions_2026=[r for r in histories[pid] if r['effective_date'].year==2026],
            legacy_opening_source=old.get('baseline_source_snapshot_ids'))
    frame=pl.DataFrame(result,infer_schema_length=None)
    if reviewed_mode:
        assert frame['current_service_lower'].null_count()==frame['current_service_upper'].null_count()==0
        assert frame.filter((pl.col('service_days').is_not_null())&(pl.col('current_service_lower')!=pl.col('current_service_upper'))).is_empty()
    frame.write_parquet(destination/'current-control.parquet')
    for name,table in [('service-events',year_events),('service-intervals',materialized.stints),('opening-states',openings),('service-years',years)]:
        table.write_parquet(destination/f'{name}.parquet')
    focal=[592450,660271,672275,805811,665487,804944,808393,682643,624413,671732,689414,606466,691740,806198]
    focal += [r['player_id'] for r in result if r['organization_status']=='resolved_official_release_no_rights'][:3]
    focal += [r['player_id'] for r in result if r['review_reasons']][:3]
    cases=[dict(current=next(r for r in result if r['player_id']==pid),detail=review_details[pid]) for pid in dict.fromkeys(focal)]
    walk=PUBLIC/f'{receipt_prefix}-player-walks.json.gz';assert not walk.exists()
    walk.write_bytes(gzip.compress(json.dumps(cases,default=str,allow_nan=False).encode(),mtime=0))
    write_once(PUBLIC/f'{receipt_prefix}-assembly.json',dict(as_of=str(ASOF),season_start=str(start),season_end=str(end),rows=len(frame),
        dated_active_opening_members=len(active_opening),
        owner_status=dict(Counter(r['organization_status'] for r in result)),
        service_status=dict(Counter(r['service_status'] for r in result)),
        review_reasons=dict(Counter(p for r in result for p in r['review_reasons'].split(';') if p)),
        reviewed_service_expected_PA=float(members.join(frame.select('player_id','service_days'),on='player_id').filter(pl.col('service_days').is_not_null())['expected_pa'].sum()) if 'expected_pa' in members.columns else None,
        official_service_register=False,player_walkthrough_status='pending',future_control_or_salary_forecast=False,
        output_hashes={str(p):sha256_file(p) for p in [destination/'current-control.parquet',walk]}))
    print(frame.group_by('service_status').len())
    print(json.dumps([{k:r['current'][k] for k in ['player_name','organization_id','service_time','current_service_days','service_status','review_reasons','old_snapshot_current_service_days']} for r in cases],indent=2))


if __name__=='__main__':main()
