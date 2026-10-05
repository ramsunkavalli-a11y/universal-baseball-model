"""Independent static-profile/register reconstruction and bounded source walks."""
from datetime import date, datetime
import csv
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import unicodedata
from urllib.parse import parse_qs, urlsplit
from zipfile import ZipFile

from bs4 import BeautifulSoup
import polars as pl

import capture_kbo_identity_overlay as capture
from universal_baseball.storage import sha256_file

ROOT, OUT = capture.ROOT, capture.OUT
EVIDENCE = ROOT / 'reports/model-evidence/kbo-identity-overlay'
FIXED = [('67341', 808982), ('64300', 673490), ('67304', 808975), ('75125', 666560), ('64914', 519346)]


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def normalized(text):
    expanded = unicodedata.normalize('NFKD', text.lower())
    return ''.join(c for c in expanded if c.isalnum() and unicodedata.category(c) != 'Mn')


def main():
    assert not (OUT / 'review.json').exists(), 'Preserve completed review'
    report = read(OUT / 'collection.json')
    for mapping in [report['hashes'], report['output_hashes']]:
        for path, expected in mapping.items():
            assert sha256_file(ROOT / path) == expected, path
    index = {}
    with ZipFile(capture.REGISTER) as archive:
        shards = sorted(p for p in archive.namelist() if re.search(r'/data/people-[0-9a-f]\.csv$', p))
        assert len(shards) == 16
        for shard in shards:
            for row in csv.DictReader(io.StringIO(archive.read(shard).decode('utf8'))):
                try:
                    birthday = date(int(row['birth_year']), int(row['birth_month']), int(row['birth_day'])).isoformat()
                except ValueError:
                    continue
                for first in {row['name_first'], row['name_given']} - {''}:
                    for text in [row['name_last'] + first, first + row['name_last']]:
                        index.setdefault((birthday, normalized(text)), {})[row['key_uuid']] = dict(
                            key_uuid=row['key_uuid'], player_id=int(row['key_mlbam']) if row['key_mlbam'] else None,
                            register_name=(row['name_first'] + ' ' + row['name_last']).strip())
    ids = pl.read_parquet(OUT / 'identities.parquet')
    original = pl.read_parquet(capture.SOURCE / 'first-team-batting.parquet')
    joined = pl.read_parquet(OUT / 'reviewed-batting.parquet')
    assert joined.select(original.columns).equals(original)
    selected = original.filter(pl.col('pa') >= 100)['kbo_id'].unique().sort().to_list()
    assert selected == read(OUT / 'membership-seal.json')['kbo_ids'] == ids.sort('kbo_id')['kbo_id'].to_list()
    reconstructed = []
    for row in ids.iter_rows(named=True):
        key = row['kbo_id']
        receipt = OUT / 'identities' / (key + '.json')
        assert sha256_file(receipt) == report['identity_capture_hashes'][key]
        r = read(receipt); meta = r['source_meta']
        html = capture.probe.RAW / ('review-english-identity-' + key + '.html')
        assert sha256_file(html) == meta['sha256'] and meta['http_status'] == 200
        assert meta['url'] == meta['returned_url']
        assert meta['url'].endswith('Summary.aspx?pcode=' + key)
        soup = BeautifulSoup(html.read_bytes(), 'html.parser')
        nav = [parse_qs(urlsplit(a['href']).query).get('pcode', [None])[0] for a in soup.select('a[href]')
               if 'PlayerInfoHitter/' in a['href'] and 'pcode=' in a['href']]
        assert nav and set(nav) == {key}
        items = [li.get_text(' ', strip=True) for ul in soup.find_all('ul')
                 if any(li.get_text(' ', strip=True).startswith('Name :') for li in ul.find_all('li', recursive=False))
                 for li in ul.find_all('li', recursive=False)]
        names = [x.split(':', 1)[1].strip() for x in items if x.startswith('Name :')]
        birthdays = [x.split(':', 1)[1].strip() for x in items if x.startswith('Born :')]
        assert len(names) == len(birthdays) == 1
        try:
            birthday = datetime.strptime(birthdays[0], '%d/%m/%Y').date().isoformat()
        except ValueError:
            birthday = None
        available = bool(names[0] and birthday)
        candidates = index.get((birthday, normalized(names[0])), {}) if available else {}
        person = next(iter(candidates.values())) if len(candidates) == 1 else {}
        status = 'missing_profile_name_or_birth' if not available else 'exact_name_DOB' if len(candidates) == 1 else 'ambiguous_exact_name_DOB' if candidates else 'unmatched_exact_name_DOB'
        expected = dict(kbo_id=key, english_name=names[0], birth_date=birthday, identity_available=available,
                        match_status=status, key_uuid=person.get('key_uuid'), player_id=person.get('player_id'),
                        register_name=person.get('register_name'))
        assert row == r['identity'] == expected, key
        reconstructed.append(expected)
    for key, pid in FIXED:
        assert ids.filter(pl.col('kbo_id') == key)['player_id'].to_list() == [pid]
    cases = []
    keys = [key for key, _ in FIXED]
    # Add known foreign and unresolved ordinary controls selected on source ID/exposure only.
    possible = joined.filter((pl.col('pa') >= 100) & ~pl.col('kbo_id').is_in(keys))
    matched = possible.filter(pl.col('player_id').is_not_null()).sort('kbo_id', 'season').row(0, named=True)
    missing = possible.filter(pl.col('player_id').is_null()).sort('kbo_id', 'season').row(0, named=True)
    keys += [matched['kbo_id'], missing['kbo_id']]
    for key in keys:
        identity = ids.filter(pl.col('kbo_id') == key).row(0, named=True)
        history = joined.filter(pl.col('kbo_id') == key).sort('season')
        assert history.select(original.columns).equals(original.filter(pl.col('kbo_id') == key).sort('season'))
        cases.append(dict(identity=identity, selection='fixed' if key in dict(FIXED) else 'lowest_source_ID_100_PA_exact_MLBAM' if key == matched['kbo_id'] else 'lowest_source_ID_100_PA_unresolved_MLBAM',
                          observed_rows=history.height, observed_pa=int(history['pa'].sum()),
                          source_lines=history.select('season', 'pa', 'hr', 'so', 'bb', 'ibb').to_dicts(),
                          current_role_salary_status_used=False, forecast_eligibility_changed=False))
    capture.probe.write_new(OUT / 'reviewed-cases.json', dict(cases=cases, new_fits=0))
    lines = ['# Korean identity source player review', '',
             'Exact names and birth dates connect source records; they do not establish an MLB job or batting talent. All original counts and unresolved rows remain. Current profile roles, salaries, career spans and future MLB performance are not used.', '']
    for c in cases:
        i = c['identity']
        lines += [f"## {i['english_name'] or 'English name unavailable'}", '',
                  f"KBO {i['kbo_id']}; birth date {i['birth_date']}; MLBAM {i['player_id']}; status {i['match_status']}. Selection {c['selection']}.", '',
                  f"All {c['observed_rows']} observed player-season rows and {c['observed_pa']} PA retain their original counts. The identity match does not use these performance totals. No original forecast or eligibility changed.", '',
                  'Source lines: ' + json.dumps(c['source_lines'], ensure_ascii=False), '',
                  f"[Official profile]({read(OUT / 'identities' / (i['kbo_id'] + '.json'))['source_meta']['url']}) and the pinned Chadwick register supply the name and birth-date comparison. No surname-only, birthday-only or fuzzy match is accepted. An unresolved MLBAM join is missing identity infrastructure, not zero talent.", '']
    (OUT / 'player-walkthrough.md').write_text('\n'.join(lines) + '\n', encoding='utf8', newline='\n')
    tests = subprocess.run([sys.executable, '-m', 'pytest', 'tests/test_kbo_identity.py', '-q'], cwd=ROOT, capture_output=True, text=True)
    assert tests.returncode == 0, tests.stdout + tests.stderr
    freeze = subprocess.run([sys.executable, 'scripts/verify_hitter_full_2026_freeze.py'], cwd=ROOT, capture_output=True, text=True)
    assert freeze.returncode == 0, freeze.stdout + freeze.stderr
    result = dict(collected_identities=len(reconstructed), reconstructed_identity_fields=len(reconstructed) * 8,
                  match_status=report['match_status'], MLBAM_joined_identities=report['MLBAM_joined_identities'],
                  source_rows_preserved=original.height, joined_rows=int(joined['player_id'].is_not_null().sum()),
                  uncollected_source_ids=report['uncollected_source_ids'], cases=len(cases), fixed_joins_unchanged=True,
                  player_walkthrough_status='complete_for_identity_source', historical_role_qualified=False,
                  all_league_crosswalk_qualified=False, forecasts_changed=False, new_fits=0,
                  tests=tests.stdout, protected_freeze=json.loads(freeze.stdout),
                  hashes={str(p.relative_to(ROOT)): sha256_file(p) for p in [Path(__file__), OUT / 'collection.json',
                      OUT / 'reviewed-cases.json', OUT / 'player-walkthrough.md', OUT / 'reviewed-batting.parquet']})
    capture.probe.write_new(OUT / 'review.json', result)
    capture.probe.write_new(EVIDENCE / 'review.json', result)
    (EVIDENCE / 'player-walkthrough.md').write_bytes((OUT / 'player-walkthrough.md').read_bytes())
    print(json.dumps({k: v for k, v in result.items() if k != 'hashes'}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
