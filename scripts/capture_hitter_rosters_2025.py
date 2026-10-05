"""Dated 2025 membership-only capture with explicit transaction date controls."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import requests
import polars as pl
from universal_baseball.playing_time_roster_source import STATS_API_BASE, project_team_40man_membership_payload
from universal_baseball.storage import sha256_file

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'reports/generated/hitter-rosters-2025-source'
CONTRACT = ROOT/'docs/hitter-2025-source-extension-contract.md'


def write(path, obj):
    assert not path.exists(), f'Preserve {path}'
    path.write_text(json.dumps(obj, indent=2, allow_nan=False, default=str)+'\n', encoding='utf8', newline='\n')


def capture(name, endpoint, params):
    if params.get('season', 2025) != 2025:
        raise ValueError('Only declared 2025 source')
    for k in ['date', 'startDate', 'endDate']:
        if k in params and not ('2025-01-01' <= params[k] <= '2025-12-31'):
            raise ValueError('Out-of-bound source date')
    path = OUT/'captures'/f'{name}.json.gz'; receipt = path.with_suffix('.receipt.json')
    if receipt.exists():
        obj = json.loads(receipt.read_text(encoding='utf8'))
        assert obj['params'] == params and obj['endpoint'] == endpoint
        assert obj['contract_sha256'] == sha256_file(CONTRACT)
        assert obj['collector_sha256'] == sha256_file(Path(__file__))
        assert obj['compressed_sha256'] == sha256_file(path)
        with gzip.open(path, 'rb') as f:
            payload = f.read()
        assert hashlib.sha256(payload).hexdigest() == obj['response_sha256']
    else:
        assert not path.exists(), f'Unreceipted raw capture {path}'
        response = requests.get(STATS_API_BASE+endpoint, params=params, timeout=(15, 60))
        response.raise_for_status(); payload = response.content
        obj = json.loads(payload)
        if not isinstance(obj, dict):
            raise ValueError('Response must be JSON object')
        path.parent.mkdir(parents=True, exist_ok=True)
        with gzip.GzipFile(filename=str(path), mode='wb', mtime=0) as f:
            f.write(payload)
        write(receipt, dict(endpoint=endpoint, params=params, requested_url=response.url,
            captured_at=datetime.now(timezone.utc).isoformat(), response_sha256=hashlib.sha256(payload).hexdigest(),
            compressed_sha256=sha256_file(path), collector_sha256=sha256_file(Path(__file__)),
            contract_sha256=sha256_file(CONTRACT), protected_outcomes_used=False))
    return json.loads(payload)


def roster(team, day):
    payload = capture(f'{team}-{day}', f'/teams/{team}/roster',
        {'rosterType': '40Man', 'season': 2025, 'date': day})
    return project_team_40man_membership_payload(payload, team_id=team, season=2025, as_of_date=date.fromisoformat(day))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT/'review.json').exists():
        raise ValueError('Preserve completed source review')
    teams = capture('teams-2025', '/teams', {'sportId': 1, 'season': 2025})['teams']
    ids = sorted({int(t['id']) for t in teams}); assert len(ids) == 30
    with ThreadPoolExecutor(max_workers=2) as pool:
        frames = list(pool.map(lambda t: roster(t, '2025-12-31'), ids))
    r = pl.concat(frames).sort('season', 'team_id', 'player_id')
    sizes = r.group_by('team_id').len().sort('team_id')
    unique = r.group_by('season', 'player_id').len().filter(pl.col('len') != 1)
    checks = []
    # Two unrelated 2025 trades test date behavior, not today's affiliations.
    for pid, old_team, new_team in [(646240, 111, 137), (647304, 109, 136)]:
        tx = capture(f'transactions-{pid}-2025', '/transactions',
            {'playerId': pid, 'startDate': '2025-01-01', 'endDate': '2025-12-31'})['transactions']
        if any(t.get('person', {}).get('id') != pid or not '2025-01-01' <= t.get('date', '')[:10] <= '2025-12-31' for t in tx):
            raise ValueError('Transaction date/player filter not honored')
        transitions = [t for t in tx if t.get('typeCode') == 'TR' and t.get('fromTeam', {}).get('id') == old_team
                       and t.get('toTeam', {}).get('id') == new_team]
        for team, day, expected in [(old_team, '2025-05-31', True), (new_team, '2025-05-31', False),
                                    (old_team, '2025-12-31', False), (new_team, '2025-12-31', True)]:
            f = roster(team, day); actual = pid in f['player_id']
            checks.append(dict(player_id=pid, team_id=team, as_of_date=day, expected=expected, actual=actual,
                               passed=actual == expected, corroborating_trades=transitions))
    path = OUT/'year-end-2025.parquet'; assert not path.exists(); r.write_parquet(path)
    approved = (all(c['passed'] and c['corroborating_trades'] for c in checks)
                and not len(unique) and sizes['len'].is_between(15, 65).all())
    hashes = {str(p): sha256_file(p) for p in sorted((OUT/'captures').glob('*'))}
    write(OUT/'review.json', dict(membership_rows=len(r), teams=r['team_id'].n_unique(), team_sizes=sizes.to_dicts(),
        duplicate_memberships=unique.to_dicts(), date_controls=checks, input_hashes=hashes,
        roster_sha256=sha256_file(path), source_walkthrough_status='complete' if approved else 'pending',
        approved_for_membership_feature=approved, status_not_health_or_rights=True,
        status_conflicts=int(r['source_status_conflict'].sum()),
        parent_team_mismatches=int(r['source_parent_team_id_mismatch'].sum()),
        model_fits=0, protected_outcomes_used=False))
    print(f'2025 dated rosters: {len(r)} members, {r["team_id"].n_unique()} teams, approved={approved}', flush=True)


if __name__ == '__main__':
    main()
