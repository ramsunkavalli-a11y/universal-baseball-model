"""Exact static identity reconciliation; MLB existence is not a predictor."""
from datetime import date, datetime
import csv
import io
import re
import unicodedata
from zipfile import ZipFile
from urllib.parse import parse_qs, urlsplit

from bs4 import BeautifulSoup


def name_key(value):
    text = unicodedata.normalize('NFKD', value).casefold()
    return ''.join(c for c in text if c.isalnum() and not unicodedata.combining(c))


def profile_identity(html, kbo_id):
    soup = BeautifulSoup(html, 'html.parser')
    codes = [parse_qs(urlsplit(a['href']).query).get('pcode', [None])[0]
             for a in soup.find_all('a', href=True)
             if 'PlayerInfoHitter/' in a['href'] and 'pcode=' in a['href']]
    if not codes or set(codes) != {kbo_id}:
        raise ValueError('Profile navigation ID mismatch')
    profiles = []
    for ul in soup.find_all('ul'):
        items = [x.get_text(' ', strip=True) for x in ul.find_all('li', recursive=False)]
        if any(x.startswith('Name :') for x in items):
            profiles.append(items)
    if len(profiles) != 1:
        raise ValueError('Missing or conflicting profile identity block')
    values = {x.split(':', 1)[0].strip(): x.split(':', 1)[1].strip()
              for x in profiles[0] if ':' in x}
    birthday = values.get('Born', '')
    try:
        birthday = datetime.strptime(birthday, '%d/%m/%Y').date().isoformat()
    except ValueError:
        birthday = None
    name = values.get('Name', '')
    return dict(kbo_id=kbo_id, english_name=name, birth_date=birthday,
                identity_available=bool(name and birthday))


def register_index(path):
    """Only name/DOB/structured keys, never career dates or future status."""
    index = {}
    fields = ['key_uuid', 'key_mlbam', 'name_first', 'name_last', 'name_given',
              'birth_year', 'birth_month', 'birth_day']
    with ZipFile(path) as archive:
        shards = sorted(p for p in archive.namelist()
                        if re.search(r'/data/people-[0-9a-f]\.csv$', p))
        if len(shards) != 16:
            raise ValueError('Incomplete register shards')
        for shard in shards:
            for original in csv.DictReader(io.StringIO(archive.read(shard).decode('utf8'))):
                row = {k: original[k] for k in fields}
                try:
                    birthday = date(*(int(row['birth_' + k]) for k in ['year', 'month', 'day'])).isoformat()
                except (ValueError, TypeError):
                    continue
                person = dict(key_uuid=row['key_uuid'],
                              player_id=int(row['key_mlbam']) if row['key_mlbam'] else None,
                              register_name=(row['name_first'] + ' ' + row['name_last']).strip(),
                              birth_date=birthday)
                for first in {row['name_first'], row['name_given']} - {''}:
                    for label in [first + row['name_last'], row['name_last'] + first]:
                        index.setdefault((birthday, name_key(label)), {})[row['key_uuid']] = person
    return index


def match_identity(profile, index):
    if not profile['identity_available']:
        return dict(**profile, match_status='missing_profile_name_or_birth',
                    key_uuid=None, player_id=None, register_name=None)
    people = index.get((profile['birth_date'], name_key(profile['english_name'])), {})
    person = next(iter(people.values())) if len(people) == 1 else {}
    return dict(**profile, match_status='exact_name_DOB' if len(people) == 1
                else 'ambiguous_exact_name_DOB' if people else 'unmatched_exact_name_DOB',
                key_uuid=person.get('key_uuid'), player_id=person.get('player_id'),
                register_name=person.get('register_name'))
