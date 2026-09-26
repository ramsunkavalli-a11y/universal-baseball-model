"""Preselect historical games, then capture official event authority for repair."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import polars as pl
import requests

from universal_baseball.storage import sha256_file
from universal_baseball.defensive_event_repair import (
    official_events, reconcile_box, narrative_capacity, ground_ball_responsibility,
)
from universal_baseball.pbp_opportunity_events import resolve_overlapping_terminal_plays

ROOT = Path('data/working/pbp-opportunity-foundation-v1')
OUT = Path('model_artifacts/defensive-event-source-repair-v1-2026-09-25')
CACHE = Path('data/quarantine/defensive-event-source-repair-v1')
YEARS = (2016, 2018, 2021, 2024)
CONTRACT = Path('docs/defensive-event-source-repair-v1-contract.md')


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8', newline='\n')


def select():
    target = OUT / 'selection.json'
    if target.exists():
        raise RuntimeError('Selection already locked; do not overwrite it')
    sources = {}
    frames = []
    for year in YEARS:
        for path in sorted(ROOT.glob(f'season={year}/level=*/terminal/*.parquet')):
            sources[str(path)] = sha256_file(path)
            frames.append(pl.read_parquet(path, columns=['season','level','league_id','game_pk','game_date','game_type']).unique())
    games = pl.concat(frames, how='diagonal_relaxed').unique()
    conflict = games.group_by('game_pk').len().filter(pl.col('len') > 1)
    games = games.join(conflict.select('game_pk'), on='game_pk', how='anti').filter(pl.col('game_type') == 'R')
    selected = []
    for _, group in games.group_by('season','level','league_id'):
        rows = group.to_dicts()
        for row in rows:
            row['selection_hash'] = hashlib.sha256(f"defensive-source-repair-v1:{row['game_pk']}".encode()).hexdigest()
        selected.extend(sorted(rows, key=lambda x:x['selection_hash'])[:2])
    selected.sort(key=lambda x:(x['season'],x['level'],str(x['league_id']),x['selection_hash']))
    save(target, {'contract_hash':sha256_file(CONTRACT), 'selected_before_events':True,
        'selection_time':datetime.now(timezone.utc).isoformat(), 'source_hashes':sources,
        'eligible_games':games.height, 'excluded_metadata_conflict_games':conflict.height,
        'games':selected})
    print(f'Locked {len(selected)} games from {games.height} eligible games', flush=True)


def capture(row):
    game = row['game_pk']
    assert row['season'] in YEARS and int(row['game_date'][:4]) in YEARS
    path = CACHE / f'{game}.json'
    url = f'https://statsapi.mlb.com/api/v1.1/game/{game}/feed/live'
    try:
        if not path.exists():
            response = requests.get(url, timeout=40)
            response.raise_for_status()
            payload = response.json()
            # Never preserve a wrong-game/year response as historical evidence.
            if payload['gameData']['game']['pk'] != game or int(payload['gameData']['datetime']['officialDate'][:4]) not in YEARS:
                raise ValueError('Wrong game/year from authority')
            save(path, payload)
        return {'game_pk':game,'url':url,'path':str(path),'sha256':sha256_file(path)}
    except (requests.RequestException, ValueError, KeyError) as exc:
        return {'game_pk':game,'url':url,'error':str(exc)}


def fetch():
    selection = json.loads((OUT/'selection.json').read_text())
    assert selection['contract_hash'] == sha256_file(CONTRACT)
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(capture, selection['games']))
    save(OUT/'captures.json', {'selection_sha256':sha256_file(OUT/'selection.json'),
        'captured_at':datetime.now(timezone.utc).isoformat(), 'records':records})
    print(json.dumps({'captures':len(records),'errors':sum('error' in r for r in records)}))


def audit():
    selection = json.loads((OUT/'selection.json').read_text())
    assert selection['contract_hash'] == sha256_file(CONTRACT)
    selected = {r['game_pk']:r for r in selection['games']}
    frames = []
    for path, digest in selection['source_hashes'].items():
        assert sha256_file(Path(path)) == digest
        frames.append(pl.read_parquet(path).filter(pl.col('game_pk').is_in(list(selected))))
    terminal = resolve_overlapping_terminal_plays(frames)
    terminal_map = {(r['game_pk'],r['at_bat_index']):r for r in terminal.to_dicts()}
    captures = json.loads((OUT/'captures.json').read_text())
    assert captures['selection_sha256'] == sha256_file(OUT/'selection.json')
    events, coordinates, reconciliations, game_status = [], [], [], []
    for capture in captures['records']:
        game = capture['game_pk']
        meta = selected[game]
        if 'error' in capture:
            game_status.append({**meta,'status':'capture_error','detail':capture['error']})
            continue
        path = Path(capture['path'])
        assert sha256_file(path) == capture['sha256']
        payload = json.loads(path.read_text(encoding='utf-8'))
        try:
            e, xy = official_events(payload,game,meta['season'])
            for row in e+xy:
                row.update(season=meta['season'],level=meta['level'],league_id=meta['league_id'])
            events.extend(e)
            coordinates.extend(xy)
            for row in reconcile_box(payload,e):
                row.update(season=meta['season'],level=meta['level'],league_id=meta['league_id'])
                reconciliations.append(row)
            game_status.append({**meta,'status':'evaluated',
                'official_home_league':payload['gameData']['teams']['home'].get('league',{}).get('id'),
                'official_away_league':payload['gameData']['teams']['away'].get('league',{}).get('id'),
                'official_play_count':len(payload['liveData']['plays']['allPlays']),
                'archived_terminal_count':sum(r['game_pk']==game for r in terminal_map.values())})
        except (KeyError,ValueError) as exc:
            game_status.append({**meta,'status':'source_gate_error','detail':str(exc)})
    # At most one old narrative event per family/base/PA; no invented runner match.
    grouped = defaultdict(list)
    for row in events:
        grouped[(row['game_pk'],row['at_bat_index'])].append(row)
    coverage = []
    for key, rows in grouped.items():
        t = terminal_map.get(key)
        usable = t is not None and not t['has_source_conflict']
        available = narrative_capacity(t['pa_description']) if usable else Counter()
        for (kind,base), count in Counter((r['family'],r['event_type'].split('_')[-1]
               if r['family'] in ('SB','CS','POCS') else None) for r in rows).items():
            # POCS deliberately excluded from old clean throwing.
            cap = available[(kind,base)] if kind != 'POCS' else 0
            meta = selected[key[0]]
            coverage.append({'season':meta['season'],'level':meta['level'],'league_id':meta['league_id'],
                'game_pk':key[0],'at_bat_index':key[1],'family':kind,'base':base,'official_events':count,
                'terminal_present':t is not None,'terminal_usable':usable,
                'old_narrative_max_matches':min(count,cap),
                'old_with_battery_max_matches':min(count,cap) if usable and t['fielder_2'] is not None and t['pitcher'] is not None else 0})
    ledger = []
    for row in terminal_map.values():
        ledger.extend(ground_ball_responsibility(row))
    sums = defaultdict(float)
    for row in ledger:
        sums[(row['game_pk'],row['at_bat_index'])] += row['share']
    assert all(abs(v-1)<1e-12 for v in sums.values())
    assert len(sums) == terminal.filter(pl.col('bb_type')=='ground_ball').height
    coord_checks = []
    for row in coordinates:
        t = terminal_map.get((row['game_pk'],row['at_bat_index']))
        present = t is not None and not t['has_source_conflict']
        all_xy = present and all(v is not None for v in (t['hc_x'],t['hc_y'],row['official_x'],row['official_y']))
        coord_checks.append({**row,'terminal_present':present,
            'both_coordinates':bool(all_xy),
            'coordinates_agree':bool(all_xy and abs(t['hc_x']-row['official_x'])<.011 and abs(t['hc_y']-row['official_y'])<.011)})
    cover = pl.DataFrame(coverage)
    summary = cover.group_by('season','level','family').agg(
        pl.col('official_events').sum(),pl.col('old_narrative_max_matches').sum(),
        pl.col('old_with_battery_max_matches').sum()).sort('season','level','family')
    totals = cover.group_by('family').agg(pl.col('official_events').sum(),pl.col('old_narrative_max_matches').sum(),
        pl.col('old_with_battery_max_matches').sum()).sort('family')
    for name,rows in [('events',events),('box-reconciliation',reconciliations),('coverage',coverage),
            ('responsibility-candidate',ledger),('coordinate-checks',coord_checks)]:
        save(OUT/f'{name}.json',rows)
    report = {'selection_sha256':sha256_file(OUT/'selection.json'),
        'captures_sha256':sha256_file(OUT/'captures.json'),
        'code_hashes':{p:sha256_file(Path(p)) for p in ['scripts/audit_defensive_event_sources_v1.py',
            'src/universal_baseball/defensive_event_repair.py']},
        'games':game_status, 'terminal_plays':terminal.height,
        'terminal_conflicting_keys':terminal.filter(pl.col('has_source_conflict')).height,
        'event_totals':totals.to_dicts(),'coverage_by_season_level':summary.to_dicts(),
        'box_status_counts':dict(Counter(r['status'] for r in reconciliations)),
        'box_discrepancies':[r for r in reconciliations if r['status']!='matched'],
        'ground_balls':len(sums),'responsibility_rows':len(ledger),
        'responsibility_basis_shares':dict(Counter({k:sum(r['share'] for r in ledger if r['basis']==k) for k in {r['basis'] for r in ledger}})),
        'unknown_fielder_share':sum(r['share'] for r in ledger if r['unknown_fielder']),
        'coordinate_rows':len(coord_checks),'coordinate_both':sum(r['both_coordinates'] for r in coord_checks),
        'coordinate_agree':sum(r['coordinates_agree'] for r in coord_checks),
        'source_event_gate':('sample_event_accounting_passed' if all(r['status']=='matched' for r in reconciliations)
            and len(reconciliations)==len(selected)*8 else 'not_passed'),
        'battery_attribution_gate':'not_certified','range_opportunity_gate':'not_certified',
        'new_fits':0,'frozen_forecasts_changed':False,'protected_outcomes_used':False}
    save(OUT/'report.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ('games','coverage_by_season_level','code_hashes')},indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['select','fetch','audit'])
    args = parser.parse_args()
    {'select':select,'fetch':fetch,'audit':audit}[args.mode]()
