"""Develop event-time defense, then test on separately locked historical games."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import argparse
import hashlib
import json
from pathlib import Path
import polars as pl

from audit_defensive_event_sources_v1 import capture
from universal_baseball.defensive_event_repair import official_events, reconcile_box
from universal_baseball.defensive_timeline import defensive_timeline, attach_battery, player_box_checks, TimelineError
from universal_baseball.pbp_opportunity_events import resolve_overlapping_terminal_plays
from universal_baseball.storage import sha256_file

OLD=Path('model_artifacts/defensive-event-source-repair-v1-2026-09-25')
OUT=Path('model_artifacts/defensive-timeline-v1-2026-09-25')
PLAN=Path('docs/defensive-timeline-v1-contract.md')


def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')


def code_hashes():
    return {str(p):sha256_file(p) for p in [PLAN,Path(__file__),
        Path('src/universal_baseball/defensive_timeline.py'),Path('src/universal_baseball/defensive_event_repair.py'),
        Path('tests/test_defensive_timeline.py')]}


def select():
    if (OUT/'selection.json').exists():raise ValueError('Already locked')
    original=json.loads((OLD/'selection.json').read_text());frames=[]
    for path,digest in original['source_hashes'].items():
        assert sha256_file(Path(path))==digest
        frames.append(pl.read_parquet(path,columns=['season','level','league_id','game_pk','game_date','game_type']).unique())
    games=pl.concat(frames,how='diagonal_relaxed').unique()
    conflicts=games.group_by('game_pk').len().filter(pl.col('len')>1)
    games=games.join(conflicts.select('game_pk'),on='game_pk',how='anti').filter(pl.col('game_type')=='R')
    selected=[]
    for _,g in games.group_by('season','level','league_id'):
        rows=g.to_dicts()
        for r in rows:r['selection_hash']=hashlib.sha256(f"defensive-source-repair-v1:{r['game_pk']}".encode()).hexdigest()
        selected.extend(sorted(rows,key=lambda r:r['selection_hash'])[2:4])
    assert not {r['game_pk'] for r in selected}&{r['game_pk'] for r in original['games']}
    selected.sort(key=lambda r:(r['season'],r['level'],str(r['league_id']),r['selection_hash']))
    save(OUT/'selection.json',{'original_selection_sha256':sha256_file(OLD/'selection.json'),
        'contract_sha256':sha256_file(PLAN),'source_hashes':original['source_hashes'],'games':selected,
        'outcomes_opened_before_selection':False})
    print(f'Locked {len(selected)} disjoint validation games')


def freeze():
    if (OUT/'validation-freeze.json').exists():raise ValueError('Already frozen')
    assert (OUT/'development-report.json').exists()
    save(OUT/'validation-freeze.json',{'code_hashes':code_hashes(),
        'selection_sha256':sha256_file(OUT/'selection.json'),'development_report_sha256':sha256_file(OUT/'development-report.json')})


def fetch():
    assert json.loads((OUT/'validation-freeze.json').read_text())['code_hashes']==code_hashes()
    selection=json.loads((OUT/'selection.json').read_text())
    with ThreadPoolExecutor(max_workers=4) as pool:records=list(pool.map(capture,selection['games']))
    save(OUT/'captures.json',{'selection_sha256':sha256_file(OUT/'selection.json'),'records':records})
    print({'games':len(records),'errors':sum('error' in r for r in records)})


def audit(phase):
    root=OLD if phase=='development' else OUT
    if phase=='validation':assert json.loads((OUT/'validation-freeze.json').read_text())['code_hashes']==code_hashes()
    sel=json.loads((root/'selection.json').read_text());capture_manifest=json.loads((root/'captures.json').read_text())
    records={r['game_pk']:r for r in capture_manifest['records']}
    ids=[r['game_pk'] for r in sel['games']]
    frames=[]
    for path,digest in sel['source_hashes'].items():
        assert sha256_file(Path(path))==digest
        frames.append(pl.read_parquet(path).filter(pl.col('game_pk').is_in(ids)))
    t=resolve_overlapping_terminal_plays(frames)
    tmap={(r['game_pk'],r['at_bat_index']):r for r in t.to_dicts()}
    attributed=[];playerchecks=[];credits=[];terminalchecks=[];games=[];matchups=[];boxchecks=[];changes=[]
    for meta in sel['games']:
        game=meta['game_pk'];cap=records[game]
        if 'error' in cap:
            games.append({**meta,'status':'capture_error'});continue
        path=Path(cap['path']);assert sha256_file(path)==cap['sha256']
        payload=json.loads(path.read_text(encoding='utf-8'))
        try:
            events,_=official_events(payload,game,meta['season'])
            timeline=defensive_timeline(payload)
            ev=attach_battery(events,timeline)
            for name,rows,target in [('events',ev,attributed),('player',player_box_checks(payload,ev,timeline),playerchecks),
                ('credits',timeline['credits'],credits),('matchups',timeline['matchups'],matchups),
                ('box',reconcile_box(payload,ev),boxchecks),('changes',timeline['changes'],changes)]:
                target.extend({**r,'game_pk':game,'season':meta['season'],'level':meta['level']} for r in rows)
            for row in timeline['terminal']:
                archived=tmap.get((game,row['at_bat_index']))
                for position in range(1,10):
                    field='pitcher' if position==1 else f'fielder_{position}'
                    known=archived is not None and not archived['has_source_conflict'] and archived.get(field) is not None
                    terminalchecks.append({'game_pk':game,'at_bat_index':row['at_bat_index'],'position':position,
                        'timeline':row[f'fielder_{position}'],'archived':archived.get(field) if known else None,
                        'status':'unavailable_or_conflicted' if not known else 'match' if row[f'fielder_{position}']==archived[field] else 'mismatch'})
            games.append({**meta,'status':'reconstructed','events':len(ev),'changes':len(timeline['changes'])})
        except (TimelineError,ValueError,KeyError) as exc:
            games.append({**meta,'status':'reconstruction_failed','reason':str(exc)})
    tables={'events':attributed,'player-checks':playerchecks,'credit-checks':credits,'terminal-checks':terminalchecks,
        'matchup-checks':matchups,'box-checks':boxchecks,'substitutions':changes}
    detail=Path('reports/generated/defensive-timeline-v1')/phase;detail.mkdir(parents=True,exist_ok=True)
    artifacts={}
    for name,rows in tables.items():
        path=detail/f'{name}.parquet';pl.DataFrame(rows,infer_schema_length=None).write_parquet(path)
        artifacts[str(path)]={'sha256':sha256_file(path),'rows':len(rows)}
    report={'phase':phase,'selection_sha256':sha256_file(root/'selection.json'),'code_hashes':code_hashes(),
        'games':games,'game_status':dict(Counter(g['status'] for g in games)),
        'events':len(attributed),'event_families':dict(Counter(e['family'] for e in attributed)),
        'battery_status':dict(Counter(e['battery_attribution'] for e in attributed)),
        'player_checks':dict(Counter((r['metric']+':'+r['status']) for r in playerchecks)),
        'player_discrepancies':[r for r in playerchecks if r['status']!='match'],
        'credit_checks':len(credits),'credit_discrepancies':[r for r in credits if not r['match']],
        'matchup_checks':len(matchups),'matchup_discrepancies':[r for r in matchups if not r['match']],
        'terminal_check_status':dict(Counter(r['status'] for r in terminalchecks)),
        'terminal_discrepancies':[r for r in terminalchecks if r['status']=='mismatch'],
        'box_check_status':dict(Counter(r['status'] for r in boxchecks)),
        'box_discrepancies':[r for r in boxchecks if r['status']!='matched'],
        'substitutions':dict(Counter(r['type'] for r in changes)),
        'artifacts':artifacts,'new_fits':0,'production_changed':False,'protected_outcomes_used':False}
    save(OUT/f'{phase}-report.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ('games','code_hashes','artifacts')},indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['select','development','freeze','fetch','validation']);args=ap.parse_args()
    if args.mode in ('development','validation'):audit(args.mode)
    else:{'select':select,'freeze':freeze,'fetch':fetch}[args.mode]()
