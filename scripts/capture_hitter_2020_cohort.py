"""Capture historical roster membership only; mutable person fields are unused."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
import gzip
import json
from pathlib import Path

import polars as pl
from universal_baseball.playing_time_roster_source import (
    _get_json, STATS_API_BASE, project_team_40man_membership_payload,
)
from universal_baseball.storage import sha256_file

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/generated/hitter-2020-cohort'


def capture(relative, endpoint, params):
    path = OUT / 'captures' / relative
    if path.exists():
        with gzip.open(path, 'rt', encoding='utf8') as stream:
            obj = json.load(stream)
        assert obj['endpoint'] == endpoint and obj['params'] == params
    else:
        _, evidence = _get_json(STATS_API_BASE + endpoint, params=params)
        obj = dict(evidence, endpoint=endpoint, params=params,
                   captured_at=datetime.now(timezone.utc).isoformat())
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(gzip.compress(json.dumps(obj, sort_keys=True).encode(), mtime=0))
    return obj['payload'], dict(path=str(path), sha256=sha256_file(path),
                               endpoint=endpoint, params=params)


def one(job):
    team, kind = job
    payload, evidence = capture(f'{kind}/{team}.json.gz', f'/teams/{team}/roster',
        {'rosterType': kind, 'season': 2020, 'date': '2020-12-31'})
    rows = payload['roster']
    if kind == '40Man':
        frame = project_team_40man_membership_payload(payload, team_id=team,
            season=2020, as_of_date=date(2020, 12, 31))
        assert 15 <= len(frame) <= 65, (team, len(frame))
        return frame, evidence
    assert rows, ('Empty historical fullRoster', team)
    # Read historical roster-row position, never person.primaryPosition.
    projected = [dict(player_id=int(x['person']['id']),
        player_name=x['person']['fullName'], team_id=team,
        position=str(x.get('position', {}).get('code') or 'UNKNOWN')) for x in rows]
    return pl.DataFrame(projected).unique(), evidence


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    assert not (OUT / 'capture-report.json').exists(), 'Preserve completed source'
    teams, evidence = capture('teams.json.gz', '/teams', {'sportId': 1, 'season': 2020})
    ids = sorted({int(t['id']) for t in teams['teams']})
    assert len(ids) == 30
    jobs = [(t, k) for t in ids for k in ['fullRoster', '40Man']]
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(one, jobs))
    full = pl.concat([f for (t, k), (f, _) in zip(jobs, results) if k == 'fullRoster'])
    forty = pl.concat([f for (t, k), (f, _) in zip(jobs, results) if k == '40Man'])
    assert forty.unique(['season', 'player_id']).height == len(forty), 'Conflicting teams'
    assert full['team_id'].n_unique() == forty['team_id'].n_unique() == 30
    full.write_parquet(OUT / 'full-roster.parquet')
    forty.write_parquet(OUT / '40man.parquet')
    report = dict(year=2020, requested_teams=ids, captures=[evidence]+[e for _, e in results],
        full_roster_rows=len(full), full_roster_people=full['player_id'].n_unique(),
        forty_man_people=len(forty), source_meaning='Historical listing, not certified rights/status',
        mutable_person_fields_used=False, protected_outcomes_used=False)
    (OUT / 'capture-report.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k not in ['captures', 'requested_teams']}, indent=2))


def birthdates():
    assert (OUT / 'capture-report.json').exists()
    assert not (OUT / 'birthdate-report.json').exists(), 'Preserve completed dates'
    full = pl.read_parquet(OUT / 'full-roster.parquet')
    old = pl.read_parquet(ROOT / 'reports/generated/practical-hitter-v33b/features.parquet')
    old = old.filter((pl.col('origin_year') == 2019) & (pl.col('age_unknown') == 0))
    stints = pl.read_parquet(ROOT / 'reports/generated/practical-hitter-v31/dated-stints.parquet')
    known = set(old['player_id']) | set(stints.filter(
        (pl.col('season') <= 2020) & pl.col('reported_age').is_not_null())['player_id'])
    ids = sorted(set(full['player_id']) - known)
    chunks = [ids[i:i+150] for i in range(0, len(ids), 150)]
    def fetch(group):
        return capture(f'birthdates/{group[0]}.json.gz', '/people',
            {'personIds': ','.join(map(str, group)), 'fields': 'people,id,birthDate,fullName'})
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(fetch, chunks))
    rows = []
    for payload, _ in results:
        for person in payload['people']:
            # These are the only allowed fields. No current-position/age/status.
            assert set(person) <= {'id', 'birthDate', 'fullName'}
            rows.append(dict(player_id=int(person['id']),
                birth_date=person.get('birthDate'), player_name=person.get('fullName')))
    frame = pl.DataFrame(rows)
    assert frame['player_id'].n_unique() == len(frame)
    assert set(frame['player_id']) == set(ids), 'Incomplete immutable-date lookup'
    frame.write_parquet(OUT / 'birthdates.parquet')
    report = dict(requested_people=len(ids), returned_people=len(frame),
        missing_birth_dates=frame['birth_date'].null_count(),
        captures=[e for _, e in results], mutable_person_fields_used=False)
    (OUT / 'birthdate-report.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    print('Immutable dates:', len(frame), 'people; missing:', frame['birth_date'].null_count())


if __name__ == '__main__':
    import sys
    birthdates() if '--birthdates' in sys.argv else main()
