"""Archive a qualified source ledger; do not fit or change current forecasts."""
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import zipfile

import polars as pl
import capture_hitter_preseason_population as c
import capture_hitter_preseason_population_v2 as v2
from universal_baseball.hitter_preseason_population import (
    available_date, canonical, classify_event, reconcile_transactions, roster_people, transaction_key)
from universal_baseball.storage import sha256_file

ROOT, OUT = c.ROOT, c.OUT
EVIDENCE = ROOT/'reports/model-evidence/hitter-preseason-population-source'
PANEL = ROOT/'reports/generated/hitter-preseason-readiness-v68/features.parquet'
STINTS = ROOT/'reports/generated/practical-hitter-v31/dated-stints.parquet'
PREDICTIONS = ROOT/'reports/generated/hitter-minor-statcast-precision/scored-predictions.parquet'
POSITIVE = {'minor_agreement','agreement_unspecified','acquisition','contract_selection','activation'}
FIXED = [
    ('Michael Conforto',624424,2022,'missing_returner'),
    ('Miguel Sano',593934,2023,'agreement_vs_official_date'),
    ('Jorge Alfaro',595751,2024,'missing_returner_minor_contract'),
    ('Shohei Ohtani',660271,2017,'foreign_two_way_without_40man'),
    ('Seiya Suzuki',673548,2021,'foreign_professional_lockout_cutoff'),
    ('Masataka Yoshida',807799,2022,'foreign_professional'),
    ('Jung Hoo Lee',808982,2023,'foreign_professional'),
    ('Hyeseong Kim',808975,2024,'old_fullroster_temporal_counterexample'),
    ('AJ Pollock',572041,2022,'negative_giants_team_date'),
    ('Mark Canha',592192,2023,'negative_giants_team_date'),
    ('Rafael Devers',646240,2024,'negative_giants_team_date'),
    ('David Wright',431151,2017,'retained_old_absent_hitter'),
    ('Brandon Belt',474832,2023,'unsigned_nonreturner'),
]


def build(year, cutoff, current, rosters, events, stints, mlb_teams):
    """No outcomes accepted: retain originals and show all dated MLB-team candidates."""
    assert 2012 <= year <= 2025 and cutoff.startswith(str(year))
    origin = year-1
    assert all(r['origin_year'] == origin for r in current)
    old = {r['player_id']:r for r in current}
    assert len(old) == len(current)
    roster_map, event_map, late_map = defaultdict(list), defaultdict(list), defaultdict(list)
    for team, rows in rosters.items():
        assert team in mlb_teams
        for pid, group in roster_people(rows).items():
            roster_map[pid].extend(dict(team_id=team,raw=r) for r in group)
    seen = {}
    for event in events:
        key = transaction_key(event)
        if key in seen:
            assert seen[key] == event, 'Contradictory event under composite key'
            continue
        seen[key] = event
        pid = event.get('person',{}).get('id')
        if not pid or classify_event(event,mlb_teams) == 'outside_mlb_team_event':
            continue
        day = available_date(event)
        item = dict(raw=event,kind=classify_event(event,mlb_teams),available_date=day)
        (event_map if day and day <= cutoff else late_map)[pid].append(item)
    history = defaultdict(list)
    for s in stints:
        if s['season'] <= origin and s['plate_appearances'] > 0:
            history[s['player_id']].append(s)
    records, details = [], {}
    # A source candidate is not approved hitter eligibility or current employment.
    for pid in sorted(set(old)|set(roster_map)|set(event_map)):
        rs, es, hs = roster_map[pid],event_map[pid],history[pid]
        prior = sorted(hs,key=lambda s:(-s['season'],-s['plate_appearances'],s['team_id']))
        last = prior[0] if prior else None
        recent = [s for s in hs if origin-2 <= s['season'] <= origin]
        positions = sorted({r['raw'].get('position',{}).get('code','UNKNOWN') for r in rs})
        positive = [e for e in es if e['kind'] in POSITIVE]
        primary = last['position'] if last else 'UNKNOWN'
        hitter_hint = primary in {str(i) for i in range(2,11)} or bool(set(positions)&{str(i) for i in range(2,11)})
        role = 'hitter_history_or_listing_hint' if hitter_hint else 'pitcher_or_two_way_unresolved' if primary=='1' or '1' in positions else 'unknown'
        name = (old.get(pid,{}).get('player_name') or (last['player_name'] if last else None)
                or (rs[0]['raw']['person'].get('fullName') if rs else None)
                or (es[0]['raw']['person'].get('fullName') if es else None))
        teams = sorted({r['team_id'] for r in rs})
        latest = max((e['available_date'] for e in es),default=None)
        latest_kinds = sorted({e['kind'] for e in es if e['available_date']==latest})
        row = dict(candidate_key=f'{origin}:{pid}',origin_year=origin,target_year=year,information_date=cutoff,
                   player_id=pid,player_name=name,current_model_origin=pid in old,
                   current_row_id=old.get(pid,{}).get('row_id'),returned_40man=bool(rs),
                   roster_team_ids=teams,roster_position_codes=positions,roster_cross_team_conflict=len(teams)>1,
                   roster_raw_rows=len(rs),roster_duplicate_rows=len(rs)-len(teams),
                   roster_status_conflict=any(len({(r['raw'].get('status',{}).get('code'),r['raw'].get('parentTeamId'))
                       for r in rs if r['team_id']==t})>1 for t in teams),
                   eligible_mlb_team_event_records=len(es),positive_context_records=len(positive),
                   late_event_records=len(late_map[pid]),latest_event_date=latest,latest_event_kinds=latest_kinds,
                   scope_exit_records=sum(e['kind']=='scope_exit' for e in es),
                   minor_agreement_records=sum(e['kind']=='minor_agreement' for e in es),
                   origin_has_positive_context=bool(rs or positive),
                   latest_domestic_stat_season=last['season'] if last else None,
                   last_domestic_source_position=primary,role_status=role,
                   recent_domestic_pa=sum(s['plate_appearances'] for s in recent),
                   recent_mlb_pa=sum(s['plate_appearances'] for s in recent if s['sport_id']==1),
                   domestic_batting_history_missing=not bool(hs),
                   hitter_eligibility_approved=False,complete_historical_rights_verified=False)
        records.append(row)
        details[pid] = dict(roster_rows=rs,eligible_events=es,late_events=late_map[pid])
    return records,details


def main():
    assert not (OUT/'population-report.json').exists(), 'Preserve completed materialization'
    report = c.read(OUT/'capture-report-v3.json')
    assert report['code_sha256']==sha256_file(ROOT/'scripts/capture_hitter_preseason_population_v3.py')
    assert report['mechanics_sha256']==sha256_file(ROOT/'src/universal_baseball/hitter_preseason_population.py')
    assert report['date_config_sha256']==sha256_file(c.CONFIG)
    for path in (OUT/'captures').glob('*.metadata.json'):
        meta = c.read(path)
        raw = path.with_name(path.name.removesuffix('.metadata.json'))
        assert sha256_file(raw)==meta['sha256']
    panel = pl.read_parquet(PANEL)
    assert len(panel)==63282 and panel['origin_year'].max()==2024
    stints = pl.read_parquet(STINTS)
    assert stints['season'].max()==2025
    records, details, checks = [], {}, []
    for year in range(2012,2026):
        cutoff = c.read(c.CONFIG)[str(year)]['date']
        teams = {t['id'] for t in c.read(OUT/f'captures/teams-{year}.json')['teams']}
        rosters = {team:c.read(OUT/f'captures/roster-{year}-{team}-40Man.json')['roster'] for team in teams}
        events = c.read(OUT/f'captures/transactions-{year}.json')['transactions']
        parts = [(a,b,c.read(OUT/f'captures/transactions-{year}-{a}-{b}.json')['transactions'])
                 for a,b in v2.months(f'{year-1}-10-01',cutoff)]
        summary = reconcile_transactions(events,parts,f'{year-1}-10-01',cutoff)
        for name,value in c.read(OUT/'capture-report-v3.json')['transaction_checks'][year-2012].items():
            if name not in ('season','cutoff'):
                assert summary[name]==value
        origin_rows = panel.filter(pl.col('origin_year')==year-1).select('player_id','player_name','origin_year','row_id').to_dicts()
        past = stints.filter(pl.col('season')<=year-1).to_dicts()
        rows, raw = build(year,cutoff,origin_rows,rosters,events,past,teams)
        # Remove all target-season data and corrupt it; membership and source summaries cannot change.
        changed = stints.with_columns(pl.when(pl.col('season')>=year).then(999999).otherwise(pl.col('plate_appearances')).alias('plate_appearances'))
        assert rows==build(year,cutoff,origin_rows,rosters,events,changed.to_dicts(),teams)[0]
        records.extend(rows)
        details.update({(year-1,pid):value for pid,value in raw.items()})
        checks.append(dict(target_year=year,cutoff=cutoff,source_candidates=len(rows),
                           original_origins=sum(r['current_model_origin'] for r in rows),
                           added_source_origins=sum(not r['current_model_origin'] for r in rows),
                           added_positive_hitter_hints=sum(not r['current_model_origin'] and r['origin_has_positive_context'] and
                               r['role_status']=='hitter_history_or_listing_hint' for r in rows),
                           late_event_records=sum(r['late_event_records'] for r in rows),future_invariance_pass=True,
                           source_records=summary))
    ledger = pl.DataFrame(records,schema_overrides={'current_row_id':pl.Int64,'latest_domestic_stat_season':pl.Int64,
                                                  'latest_event_date':pl.String}).sort('origin_year','player_id')
    assert ledger['candidate_key'].n_unique()==len(ledger)
    retained = ledger.filter(pl.col('current_model_origin')).select(pl.col('current_row_id').alias('row_id'),'origin_year','player_id').sort('row_id')
    assert retained.equals(panel.select('row_id','origin_year','player_id').sort('row_id'))
    ledger.write_parquet(OUT/'population.parquet')
    # Seal the future-blind identities before reading predictions or later results for review.
    c.write(OUT/'population-membership-seal.json',dict(rows=len(ledger),original_rows=len(retained),
        sha256=sha256_file(OUT/'population.parquet'),new_hitter_eligibility_approved=False,new_fits=0,
        rules_sha256=sha256_file(Path(__file__)),source_checks=checks))
    cases = []
    for name,pid,origin,selection in FIXED:
        match = ledger.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==origin))
        row = match.row(0,named=True) if len(match) else None
        cases.append(dict(display_name=name,player_id=pid,origin_year=origin,selection=selection,
                          source_row=row,raw_source=details.get((origin,pid)),
                          own_history=stints.filter((pl.col('player_id')==pid)&pl.col('season').is_between(origin-2,origin))
                              .sort('season','bucket','team_id').to_dicts()))
    ordinary = ledger.filter((pl.col('origin_year')==2024)&pl.col('current_model_origin')&pl.col('returned_40man')&
                             (pl.col('recent_mlb_pa')>=400)&~pl.col('player_id').is_in([v[1] for v in FIXED])).sort('player_id').row(0,named=True)
    pid = ordinary['player_id']
    cases.append(dict(display_name=ordinary['player_name'],player_id=pid,origin_year=2024,selection='lowest_id_regular_listed_not_fixed',
        source_row=ordinary,raw_source=details[2024,pid],own_history=stints.filter((pl.col('player_id')==pid)&pl.col('season').is_between(2022,2024)).sort('season','bucket','team_id').to_dicts()))
    q = pl.read_parquet(PREDICTIONS)
    assert len(q)==30506
    for case in cases:
        pid,origin = case['player_id'],case['origin_year']
        case['existing_forecast'] = q.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==origin)).select(
            'row_id','stage','preseason_p','preseason_conditional_pa','preseason_pa','combined_rate','combined_value','next_pa').to_dicts()
        case['diagnostic_next_pa'] = stints.filter((pl.col('player_id')==pid)&(pl.col('season')==origin+1)&(pl.col('sport_id')==1))['plate_appearances'].sum()
        focal = case['source_row']
        if focal:
            peers = ledger.filter((pl.col('origin_year')==origin)&(pl.col('player_id')!=pid)&
                (pl.col('role_status')==focal['role_status'])&
                (pl.col('domestic_batting_history_missing')==focal['domestic_batting_history_missing'])).with_columns(
                    (((pl.col('recent_mlb_pa')-focal['recent_mlb_pa'])/300)**2+
                     ((pl.col('recent_domestic_pa')-focal['recent_domestic_pa'])/400)**2+
                     (pl.col('returned_40man').cast(pl.Int64)-int(focal['returned_40man']))**2).alias('distance'))
            case['origin_selected_peers'] = peers.sort('distance','player_id').head(4).select(
                'player_id','player_name','recent_mlb_pa','recent_domestic_pa','returned_40man','role_status','distance').to_dicts()
        else:
            case['origin_selected_peers'] = []
        case['peer_limit'] = 'Domestic exposure and listing/role hints only; not comparable foreign talent, age, contract, injury or rights. No outcomes select peers.'
    c.write(OUT/'source-cases.json',dict(cases=cases,player_walkthrough_status='pending',new_forecasts=False))
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    archive = EVIDENCE/'raw-captures.zip'
    assert not archive.exists()
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted((OUT/'captures').iterdir()):
            entry = zipfile.ZipInfo(p.name,date_time=(2026,10,4,0,0,0))
            entry.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(entry,p.read_bytes())
    c.write(OUT/'population-report.json',dict(
        source_checks=checks,source_population_rows=len(ledger),all_original_rows_retained=True,
        original_rows=len(retained),evaluated_current_forecasts=30506,forecast_sha256=sha256_file(PREDICTIONS),
        source_membership_sealed_before_outcomes=True,new_hitter_eligibility_approved=False,
        current_forecasts_changed=False,new_fits=0,protected_2026_opened=False,player_walkthrough_status='pending',
        input_hashes={str(p):sha256_file(p) for p in [Path(__file__),PANEL,STINTS,PREDICTIONS,c.CONFIG,
            ROOT/'src/universal_baseball/hitter_preseason_population.py',ROOT/'tests/test_hitter_preseason_population.py',
            ROOT/'docs/hitter-preseason-population-source-contract.md',ROOT/'docs/hitter-preseason-population-probe-amendment.md',
            ROOT/'docs/hitter-preseason-population-transaction-amendment.md',OUT/'probe.json',OUT/'probe-adjudication.json',OUT/'capture-report-v3.json']},
        output_hashes={str(p):sha256_file(p) for p in [OUT/'population.parquet',OUT/'population-membership-seal.json',OUT/'source-cases.json',archive]},
        retrospective_source=True,full_roster_admission_allowed=False,
        foreign_talent_solution_complete=False,complete_historical_rights_verified=False))
    print(json.dumps(checks,indent=2))


if __name__=='__main__': main()
