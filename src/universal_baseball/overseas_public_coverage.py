"""Exact-ID public source coverage; no model fitting or accuracy selection."""
import csv
import math

REQUIRED = ('PA', 'AB', 'H', '1B', '2B', '3B', 'HR', 'BB', 'IBB', 'SO', 'HBP', 'SF', 'SH')
EVENTS = ('other', 'K', 'UBB', 'HBP', '1B', '2B', '3B', 'HR')


def read_archive(path, record):
    system = record['system'].lower()
    if (system not in ('steamer', 'zips') or record['year'] not in range(2022, 2026)
            or not record['label_verified'] or record['vintage_class'] != 'historical_preseason'):
        raise ValueError('Unsupported or unverified archive')
    indexed, invalid = {}, []
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        if not set((*REQUIRED, 'Name', 'PlayerId', 'MLBAMID')).issubset(reader.fieldnames or []):
            raise ValueError('Required source columns missing')
        rows = 0
        for raw in reader:
            rows += 1
            counts = {c: float(raw[c]) for c in REQUIRED}
            if any(not math.isfinite(v) or v < 0 for v in counts.values()):
                raise ValueError('Invalid event counts')
            if counts['IBB'] > counts['BB'] + 1e-6:
                raise ValueError('IBB exceeds BB')
            if abs(counts['H'] - sum(counts[c] for c in ('1B', '2B', '3B', 'HR'))) > .001:
                raise ValueError('Hit accounting mismatch')
            if abs(counts['PA'] - sum(counts[c] for c in ('AB', 'BB', 'HBP', 'SF', 'SH'))) > .001:
                raise ValueError('PA accounting mismatch')
            events = dict(K=counts['SO'], UBB=counts['BB'] - counts['IBB'],
                          **{c: counts[c] for c in ('HBP', '1B', '2B', '3B', 'HR')})
            events['other'] = counts['PA'] - sum(events.values())
            if events['other'] < -1e-6:
                raise ValueError('Events exceed PA')
            token = raw['MLBAMID'] or ''
            if not token.isascii() or not token.isdigit() or int(token) <= 0:
                invalid.append({c: raw[c] for c in ('Name', 'PlayerId', 'MLBAMID')})
                continue
            pid = int(token)
            if pid in indexed:
                raise ValueError('Duplicate MLBAM identity')
            indexed[pid] = dict(player_id=pid, name=raw['Name'], FG_id=raw['PlayerId'],
                PA=counts['PA'], counts=counts,
                event_probability=[events[e] / counts['PA'] for e in EVENTS] if counts['PA'] else None,
                workload_interpretation='unconditional' if system == 'steamer' else 'conditional',
                exact_snapshot_day_known=False)
    if rows != record['rows']:
        raise ValueError('Changed archive row count')
    return indexed, dict(system=system, year=record['year'], rows=rows,
                         valid_ids=len(indexed), invalid_ids=invalid)


def coverage_status(archives, system, target_year, player_id):
    archive = archives.get((system, target_year))
    if archive is None:
        return 'archive_year_unavailable', None
    row = archive.get(player_id)
    if row is None:
        return 'identity_absent', None
    return ('zero_projected_PA' if row['PA'] == 0 else 'positive_projected_PA'), row
