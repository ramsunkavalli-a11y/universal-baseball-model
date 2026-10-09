"""Resolve combined season rows to actual team/league exposures, compactly."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import gzip
import hashlib
import json

import polars as pl
import requests

from universal_baseball.hitter_season_intake import project_page
from universal_baseball.storage import sha256_file
from capture_hitter_2027_origin_counts import ROOT, OUT, FIELDS, write_once

AUDIT = ROOT/'reports/model-evidence/hitter-2027-v1/team-stints-review.json'


def team_capture(team):
    sport, tid = team['sport_id'], team['team_id']
    path = OUT/'team-captures'/f'sport-{sport}-team-{tid}.json.gz'
    receipt = path.with_suffix('.receipt.json')
    params = dict(stats='season', group='hitting', season=2026, sportIds=sport,
                  teamId=tid, gameType='R', playerPool='ALL', limit=5000)
    if receipt.exists():
        info = json.loads(receipt.read_text(encoding='utf8'))
        if info['params'] != params or sha256_file(path) != info['compressed_sha256']:
            raise ValueError('Saved team capture mismatch')
        raw = gzip.decompress(path.read_bytes())
        if hashlib.sha256(raw).hexdigest() != info['response_sha256']:
            raise ValueError('Uncompressed team capture mismatch')
    else:
        if path.exists():
            raise ValueError('Unreceipted team capture')
        response = requests.get('https://statsapi.mlb.com/api/v1/stats', params=params, timeout=(15,45))
        response.raise_for_status()
        raw = response.content
        json.loads(raw)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(gzip.compress(raw, mtime=0))
        info = dict(params=params, url=response.url, captured_utc=datetime.now(timezone.utc).isoformat(),
                    compressed_sha256=sha256_file(path), response_sha256=hashlib.sha256(raw).hexdigest())
        write_once(receipt, info)
    rows = project_page(json.loads(raw), season=2026, sport_id=sport, kind='players')
    if not rows or len(rows) >= 5000 or any(r['team_id'] != tid for r in rows):
        raise ValueError('Empty, truncated or wrong-team response')
    delta = {c:sum(r[c] for r in rows)-team[c] for c in FIELDS}
    for r in rows:
        r['source_scope'] = 'player_team_sport_season'
        r['needs_stint_resolution'] = False
        r['number_of_teams'] = 1
    return rows, dict(team_id=tid, sport_id=sport, rows=len(rows), source_path=str(path),
                     source_sha256=sha256_file(path), deltas=delta, totals_match=not any(delta.values()))


def main():
    if AUDIT.exists():
        raise ValueError('Preserve completed team-source review')
    teams_path, players_path = OUT/'team-aggregates.parquet', OUT/'player-aggregates.parquet'
    teams, players = pl.read_parquet(teams_path), pl.read_parquet(players_path)
    results = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(team_capture, teams.sort('sport_id','team_id').to_dicts()):
            results.append(result)
            if len(results) % 30 == 0:
                print(f'{len(results)}/{len(teams)} team sources captured', flush=True)
    frame = pl.DataFrame([r for rows, _ in results for r in rows])
    keys = ['season','sport_id','player_id']
    if frame.unique([*keys,'team_id']).height != frame.height:
        raise ValueError('Duplicate player team-season')
    summed = frame.group_by(keys).agg(pl.col(FIELDS).sum())
    paired = players.select(*keys,*FIELDS).join(summed, on=keys, how='full', coalesce=True, suffix='_teams', validate='1:1')
    discrepancy = paired.filter(pl.any_horizontal([
        (pl.col(c)!=pl.col(c+'_teams')) | pl.col(c).is_null() | pl.col(c+'_teams').is_null() for c in FIELDS]))
    destination = OUT/'team-season-counts.parquet'
    if destination.exists():
        raise ValueError('Preserve existing team-season counts')
    frame.write_parquet(destination)
    reviews = [r for _, r in results]
    write_once(AUDIT, dict(status='team_source_reconciled_player_walkthrough_pending',
        season=2026, forecast_season=2027, team_sources=len(reviews), team_rows=frame.height,
        all_team_totals_match=all(r['totals_match'] for r in reviews),
        player_sport_count_discrepancies=discrepancy.to_dicts(),
        all_player_sport_totals_match=discrepancy.is_empty(), team_reviews=reviews,
        input_hashes={str(p):sha256_file(p) for p in [teams_path,players_path,Path(__file__)]},
        output_path=str(destination), output_sha256=sha256_file(destination),
        source_approved_for_features=False,
        limitation='Team-season exposure is not dated within-season order or current organization ownership.'))
    print(f'{frame.height} team-season rows; {len(discrepancy)} player-level differences', flush=True)


if __name__ == '__main__':
    main()
