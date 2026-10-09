"""Capture compact 2026 origin aggregates; certify totals before using features."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import gzip
import hashlib
import json

import polars as pl
import requests

from universal_baseball.hitter_season_intake import SPORTS, project_page
from universal_baseball.storage import sha256_file

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'reports/generated/hitter-2027-origin-counts'
AUDIT = ROOT/'reports/model-evidence/hitter-2027-v1/origin-counts-review.json'
FIELDS = ['plate_appearances', 'at_bats', 'hits', 'doubles', 'triples', 'home_runs',
          'base_on_balls', 'intentional_walks', 'hit_by_pitch', 'strike_outs',
          'sac_bunts', 'sac_flies', 'stolen_bases', 'caught_stealing', 'runs', 'unclassified_pa']


def write_once(path, obj):
    text = json.dumps(obj, indent=2, allow_nan=False, ensure_ascii=False)+'\n'
    if path.exists():
        if path.read_text(encoding='utf8') != text:
            raise ValueError(f'Preserve existing artifact {path}')
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf8', newline='\n')


def capture(sport, kind, offset):
    path = OUT/'captures'/f'{kind}-sport-{sport}-offset-{offset}.json.gz'
    receipt = path.with_suffix('.receipt.json')
    endpoint = '/stats' if kind == 'players' else '/teams/stats'
    params = dict(stats='season', group='hitting', season=2026, sportIds=sport,
                  gameType='R', limit=5000, offset=offset)
    if kind == 'players':
        params['playerPool'] = 'ALL'
    if receipt.exists():
        info = json.loads(receipt.read_text(encoding='utf8'))
        if info['params'] != params or info['endpoint'] != endpoint or sha256_file(path) != info['compressed_sha256']:
            raise ValueError('Saved capture does not match request/hash')
        raw = gzip.decompress(path.read_bytes())
        if hashlib.sha256(raw).hexdigest() != info['response_sha256']:
            raise ValueError('Saved uncompressed hash mismatch')
    else:
        if path.exists():
            raise ValueError('Unreceipted capture; do not overwrite')
        response = requests.get('https://statsapi.mlb.com/api/v1'+endpoint, params=params, timeout=(15,45))
        response.raise_for_status()
        raw = response.content
        if not isinstance(json.loads(raw), dict):
            raise ValueError('Unexpected non-object response')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(gzip.compress(raw, mtime=0))
        info = dict(endpoint=endpoint, params=params, url=response.url,
                    captured_utc=datetime.now(timezone.utc).isoformat(),
                    response_sha256=hashlib.sha256(raw).hexdigest(), compressed_sha256=sha256_file(path))
        write_once(receipt, info)
    return project_page(json.loads(raw), season=2026, sport_id=sport, kind=kind), dict(path=str(path), **info)


def level(sport):
    groups, receipts = {}, []
    for kind in ['players', 'teams']:
        rows = []
        for offset in range(0, 25000, 5000):
            page, receipt = capture(sport, kind, offset)
            receipts.append(receipt)
            rows.extend(page)
            if len(page) < 5000:
                break
        else:
            raise ValueError('Pagination bound exceeded')
        key = 'player_id' if kind == 'players' else 'team_id'
        if not rows or len({r[key] for r in rows}) != len(rows):
            raise ValueError('Empty or duplicate source identities across pages')
        groups[kind] = rows
    diffs = {c: sum(r[c] for r in groups['players'])-sum(r[c] for r in groups['teams']) for c in FIELDS}
    info = dict(sport_id=sport, label=SPORTS[sport], player_rows=len(groups['players']),
                team_rows=len(groups['teams']), player_pa=sum(r['plate_appearances'] for r in groups['players']),
                player_minus_team_counts=diffs, event_totals_match=not any(diffs.values()),
                ambiguous_stint_rows=sum(r['needs_stint_resolution'] for r in groups['players']),
                unclassified_pa=sum(r['unclassified_pa'] for r in groups['players']),
                captures=receipts)
    print(f"{SPORTS[sport]}: {info['player_rows']} player rows; totals match={info['event_totals_match']}; multi-team/unknown stint rows={info['ambiguous_stint_rows']}", flush=True)
    return groups, info


def main():
    if AUDIT.exists():
        raise ValueError('Completed intake exists; preserve it and run its review instead')
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(level, SPORTS))
    players = pl.DataFrame([r for g, _ in results for r in g['players']])
    teams = pl.DataFrame([r for g, _ in results for r in g['teams']])
    if players.unique(['player_id', 'sport_id']).height != players.height:
        raise ValueError('Duplicate origin player-level identity')
    outputs = {}
    for name, frame in [('player-aggregates.parquet', players), ('team-aggregates.parquet', teams)]:
        path = OUT/name
        if path.exists():
            raise ValueError(f'Preserve {path}')
        frame.write_parquet(path)
        outputs[str(path)] = sha256_file(path)
    review = dict(status='aggregate_capture_requires_stint_and_source_player_review',
                  season=2026, forecast_season=2027, levels=[i for _, i in results],
                  outputs=outputs, total_rows=players.height,
                  code_hashes={str(p):sha256_file(p) for p in [Path(__file__), ROOT/'src/universal_baseball/hitter_season_intake.py']},
                  scope='All completed-season aggregate counts, not a current roster or dated team stints',
                  source_approved_for_features=False, models_fitted=0, old_forecasts_changed=False)
    write_once(AUDIT, review)


if __name__ == '__main__':
    main()
