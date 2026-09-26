"""Develop exposure source rules; freeze and test a new metadata-selected sample."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import polars as pl
from audit_defensive_event_sources_v1 import capture
from universal_baseball.storage import sha256_file
from universal_baseball.defensive_event_repair import official_events,reconcile_box
from universal_baseball.defensive_timeline import player_box_checks,TimelineError
from universal_baseball.catcher_exposure import (
    battery_timeline,runner_timeline,attach_exposures,pitch_box_checks,ExposureError,
)

OLD=[Path('model_artifacts')/n for n in ['defensive-event-source-repair-v1-2026-09-25','defensive-timeline-v1-2026-09-25']]
OUT=Path('model_artifacts/catcher-exposure-v1-2026-09-26')
PLAN=Path('docs/catcher-exposure-v1-contract.md')


def read(path):return json.loads(path.read_text(encoding='utf-8'))


def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')


def code_hashes():
    paths=[PLAN,Path(__file__).resolve().relative_to(Path.cwd()),Path('src/universal_baseball/catcher_exposure.py'),
        Path('src/universal_baseball/defensive_timeline.py'),Path('src/universal_baseball/defensive_event_repair.py'),
        Path('tests/test_catcher_exposure.py')]
    return {str(p):sha256_file(p) for p in paths}


def select():
    if (OUT/'selection.json').exists():raise ValueError('Selection already locked')
    old=read(OLD[0]/'selection.json');frames=[]
    for p,h in old['source_hashes'].items():
        assert sha256_file(Path(p))==h
        frames.append(pl.read_parquet(p,columns=['season','level','league_id','game_pk','game_date','game_type']).unique())
    games=pl.concat(frames,how='diagonal_relaxed').unique();conflict=games.group_by('game_pk').len().filter(pl.col('len')>1)
    games=games.join(conflict.select('game_pk'),on='game_pk',how='anti').filter(pl.col('game_type')=='R')
    selected=[]
    for _,g in games.group_by('season','level','league_id'):
        rows=g.to_dicts()
        for r in rows:r['selection_hash']=hashlib.sha256(f"defensive-source-repair-v1:{r['game_pk']}".encode()).hexdigest()
        selected.extend(sorted(rows,key=lambda r:r['selection_hash'])[4:6])
    previous={g['game_pk'] for s in OLD for g in read(s/'selection.json')['games']}
    assert not previous & {g['game_pk'] for g in selected}
    selected.sort(key=lambda r:(r['season'],r['level'],str(r['league_id']),r['selection_hash']))
    save(OUT/'selection.json',{'selected_at':datetime.now(timezone.utc).isoformat(),
        'contract_sha256':sha256_file(PLAN),'source_hashes':old['source_hashes'],
        'games':selected,'already_in_cache':[g['game_pk'] for g in selected if Path(f"data/quarantine/defensive-event-source-repair-v1/{g['game_pk']}.json").exists()],
        'prior_selections':{str(s/'selection.json'):sha256_file(s/'selection.json') for s in OLD}})
    print(f'Locked {len(selected)} new games')


def freeze():
    if (OUT/'validation-freeze.json').exists():raise ValueError('Already frozen')
    assert (OUT/'development-report.json').exists()
    save(OUT/'validation-freeze.json',{'time':datetime.now(timezone.utc).isoformat(),
        'code_hashes':code_hashes(),'selection_sha256':sha256_file(OUT/'selection.json'),
        'development_report_sha256':sha256_file(OUT/'development-report.json')})


def fetch():
    assert read(OUT/'validation-freeze.json')['code_hashes']==code_hashes()
    with ThreadPoolExecutor(max_workers=4) as pool:
        records=list(pool.map(capture,read(OUT/'selection.json')['games']))
    save(OUT/'captures.json',{'selection_sha256':sha256_file(OUT/'selection.json'),'records':records})
    print({'games':len(records),'errors':sum('error' in c for c in records)})


def audit(phase):
    roots=OLD if phase=='development' else [OUT]
    if phase=='validation':assert read(OUT/'validation-freeze.json')['code_hashes']==code_hashes()
    tables={k:[] for k in ['pitches','events','runner-pitches','pitch-checks','player-checks','team-checks','state-checks','credit-checks','matchup-checks']}
    games=[]
    for root in roots:
        selected={g['game_pk']:g for g in read(root/'selection.json')['games']}
        for cap in read(root/'captures.json')['records']:
            meta=selected[cap['game_pk']];g={**meta,'issues':[]}
            if 'error' in cap:
                games.append({**g,'issues':['capture_error'],'source_gate':False});continue
            p=Path(cap['path']);assert sha256_file(p)==cap['sha256'];payload=read(p)
            plays=payload['liveData']['plays']['allPlays']
            g['raw_pitches']=sum(bool(e.get('isPitch')) for a in plays for e in a.get('playEvents',[]))
            ev,_=official_events(payload,meta['game_pk'],meta['season']);g['raw_events']=len(ev)
            g['raw_event_families']=dict(Counter(r['family'] for r in ev))
            team=reconcile_box(payload,ev)
            if any(r['status']!='matched' for r in team):g['issues'].append('team_event_counts')
            bt=None;rt=None
            try:bt=battery_timeline(payload)
            except (ExposureError,TimelineError,ValueError,KeyError) as exc:g['issues'].append('battery: '+str(exc))
            try:rt=runner_timeline(payload)
            except (ExposureError,ValueError,KeyError) as exc:g['issues'].append('runner: '+str(exc))
            g['battery_reconstructed']=bt is not None;g['runner_reconstructed']=rt is not None
            rows={'team-checks':team}
            if rt:rows['state-checks']=rt['checks']
            if bt:
                a=attach_exposures(payload,ev,bt,rt);pc=pitch_box_checks(payload,a['pitches']);cc=player_box_checks(payload,a['events'],bt)
                pitch_ids=Counter((r['at_bat_index'],r['pitch_id']) for r in a['pitches'] if r['pitch_id'] is not None)
                g['duplicate_pitch_ids']=sum(n-1 for n in pitch_ids.values() if n>1)
                g['missing_pitch_ids']=sum(r['pitch_id'] is None for r in a['pitches'])
                if g['duplicate_pitch_ids']:g['issues'].append('duplicate_pitch_ids')
                rows.update({'pitches':a['pitches'],'events':a['events'],'runner-pitches':a['runner_pitches'],
                    'pitch-checks':pc,'player-checks':cc,'credit-checks':bt['credits'],'matchup-checks':bt['matchups']})
                if any(r['status']!='match' for r in pc):g['issues'].append('pitch_box_counts')
                if any(r['status']!='match' for r in cc):g['issues'].append('player_event_counts')
                if any(not r['match'] for r in bt['credits']):g['issues'].append('battery_scoring_credits')
                if any(not r['match'] for r in bt['matchups']):g['issues'].append('pitcher_matchups')
                if any(r['link_battery_match'] is False for r in a['events']):g['issues'].append('pitch_action_battery_mismatch')
                if any(r['battery_attribution']=='unresolved' for r in a['events']):g['issues'].append('event_battery_unknown')
                if rt and any(r['family'] in ['SB','CS','POCS'] and r['runner_from_base'] is None for r in a['events']):g['issues'].append('attempt_runner_absent')
                if rt and any(r['family'] in ['WP','PB'] and r['linked_blocking_at_risk'] is False for r in a['events']):g['issues'].append('blocking_failure_outside_predefined_risk')
                g['linked_events']=sum(r['pitch_link']!='unlinked' for r in a['events'])
                g['unlinked_blocking_events']=sum(r['family'] in ['WP','PB'] and r['pitch_link']=='unlinked' for r in a['events'])
                blocking_keys=Counter((r['at_bat_index'],r['linked_pitch_index']) for r in a['events'] if r['family'] in ['WP','PB'] and r['linked_pitch_index'] is not None)
                g['duplicate_blocking_pitch_labels']=sum(n-1 for n in blocking_keys.values() if n>1)
                if g['duplicate_blocking_pitch_labels']:g['issues'].append('duplicate_blocking_pitch_labels')
                g['pitch_count_gate']=all(r['status']=='match' for r in pc) and not g['duplicate_pitch_ids'] and all(r['match'] for r in bt['credits']+bt['matchups'])
            g['source_gate']=not g['issues'];games.append(g)
            g['blocking_model_source_gate']=g['source_gate'] and g.get('unlinked_blocking_events')==0
            for n,rs in rows.items():tables[n].extend({**r,'game_pk':meta['game_pk'],'season':meta['season'],'level':meta['level'],'game_source_gate':g['source_gate']} for r in rs)
    detail=Path('reports/generated/catcher-exposure-v1')/phase;detail.mkdir(parents=True,exist_ok=True);artifacts={}
    for n,rows in tables.items():
        path=detail/(n+'.parquet');pl.DataFrame(rows,infer_schema_length=None).write_parquet(path)
        artifacts[str(path)]={'rows':len(rows),'sha256':sha256_file(path)}
    report={'phase':phase,'code_hashes':code_hashes(),'games':games,'artifacts':artifacts,
        'totals':{n:len(r) for n,r in tables.items()},'game_gate':dict(Counter(g['source_gate'] for g in games)),
        'battery_reconstructed_games':sum(g.get('battery_reconstructed',False) for g in games),
        'runner_reconstructed_games':sum(g.get('runner_reconstructed',False) for g in games),
        'certified_pitch_mass':sum(g.get('raw_pitches',0) for g in games if g['source_gate']),
        'all_pitch_mass':sum(g.get('raw_pitches',0) for g in games),
        'certified_event_mass':sum(g.get('raw_events',0) for g in games if g['source_gate']),
        'all_event_mass':sum(g.get('raw_events',0) for g in games),
        'blocking_model_source_games':sum(g.get('blocking_model_source_gate',False) for g in games),
        'pitch_count_certified_games':sum(g.get('pitch_count_gate',False) for g in games),
        'event_linkage':[{'family':k[0],'pitch_link':k[1],'count':v} for k,v in sorted(Counter((r['family'],r['pitch_link']) for r in tables['events']).items())],
        'pitch_discrepancies':[r for r in tables['pitch-checks'] if r['status']!='match'],
        'player_discrepancies':[r for r in tables['player-checks'] if r['status']!='match'],
        'new_fits':0,'protected_outcomes_used':False,'production_changed':False}
    save(OUT/f'{phase}-report.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ['code_hashes','games','artifacts','pitch_discrepancies','player_discrepancies']},indent=2))
    print('Failures',json.dumps([{k:g[k] for k in ['game_pk','season','level','issues']} for g in games if not g['source_gate']],indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['select','development','freeze','fetch','validation']);args=ap.parse_args()
    if args.mode in ['development','validation']:audit(args.mode)
    else:{'select':select,'freeze':freeze,'fetch':fetch}[args.mode]()
