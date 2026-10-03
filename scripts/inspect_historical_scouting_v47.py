"""Capture bounded historical source samples; no model or future outcome access."""
from pathlib import Path
from datetime import datetime, timezone
import csv
import io
import json
import re
from collections import Counter
import requests
from html.parser import HTMLParser
from universal_baseball.storage import sha256_file

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/generated/practical-hitter-scouting-v47'


class InitialState(HTMLParser):
    def __init__(self):
        super().__init__()
        self.states = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key == 'data-init-state':
                self.states.append(json.loads(value))


def inspect_states():
    for year in [2013, 2016, 2024]:
        parser = InitialState()
        parser.feed((OUT/f'captures/mlb-top100-{year}.html').read_text(encoding='utf8'))
        assert len(parser.states) == 1
        state = parser.states[0]
        print(year, 'context', state['context'])
        payload = state['payload']
        print('query keys', list(payload['ROOT_QUERY']))
        print('types', Counter(v.get('__typename') for v in payload.values() if isinstance(v,dict)))
        ranks = next(v for k,v in payload['ROOT_QUERY'].items() if k.startswith('getPlayerRankingsFromSelection('))
        print('ranking count', len(ranks))
        for entry in ranks:
            entity=entry['playerEntity']; pid=int(entity['player']['__ref'].split(':')[1])
            if pid in [592450,641355,701762,683011,621446,666160,702616]:
                print('case',pid,entry['rank'],entity['eta'],[(b['contentTitle'],b['contentText'][:170]) for b in entity['prospectBio']])
        selected = [(k,v) for k,v in payload.items() if isinstance(v,dict) and 'prospectBio' in v]
        print('prospect keys', [(k,list(v) if isinstance(v,dict) else type(v).__name__) for k,v in selected[:3]])
        for k,v in selected[:2]:
            print('example', k, json.dumps(v, ensure_ascii=False)[:1000])


def capture(session, name, url):
    path = OUT / 'captures' / name
    meta = path.with_suffix(path.suffix + '.metadata.json')
    if path.exists():
        info = json.loads(meta.read_text(encoding='utf8'))
        assert info['url'] == url and info['sha256'] == sha256_file(path)
        return path, info
    response = session.get(url, timeout=60)
    response.raise_for_status()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(response.content)
    info = dict(url=url, final_url=response.url, captured_utc=datetime.now(timezone.utc).isoformat(),
                sha256=sha256_file(path), bytes=path.stat().st_size)
    meta.write_text(json.dumps(info, indent=2), encoding='utf8')
    return path, info


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers['User-Agent'] = 'UBM historical-source research (read-only)'
    source_url = 'https://api.github.com/repos/jacobdanovitch/Trouble-With-The-Curve/contents/data/twtc.csv'
    metadata, note = capture(session, 'twtc-file-metadata.json', source_url)
    repository_file = json.loads(metadata.read_text(encoding='utf8'))
    assert repository_file['name'] == 'twtc.csv' and repository_file['size'] < 30_000_000
    path, csv_note = capture(session, 'twtc.csv', repository_file['download_url'])
    rows = list(csv.DictReader(io.StringIO(path.read_text(encoding='utf-8-sig'))))
    keys = list(rows[0])
    schema = dict(rows=len(rows), columns=keys, populated={k:sum(bool(r[k].strip()) for r in rows) for k in keys})
    # Only bounded structural values, not bulk copyrighted scouting descriptions.
    short_keys = [k for k in keys if any(s in k.lower() for s in ['year','season','date','source','url','id','rank','grade','name'])]
    schema['structural_examples'] = [{k:r[k][:100] for k in short_keys} for r in rows[:5]]
    schema['year_distributions'] = {k:dict(Counter(r[k] for r in rows)) for k in keys if k.lower() in ['year','season','report_year']}
    pages = []
    for year in range(2011,2025):
        p, n = capture(session, f'mlb-top100-{year}.html', f'https://www.mlb.com/prospects/{year}/top100/')
        html = p.read_text(encoding='utf8')
        scripts = re.findall(r'<script\b[^>]*>(.*?)</script>', html, flags=re.S | re.I)
        candidates = []
        for body in scripts:
            if any(term in body.lower() for term in ['seager','bellinger','prospect','ranking']):
                candidates.append(dict(length=len(body), head=body[:160], seager=body.find('Seager'), bellinger=body.find('Bellinger')))
        pages.append(dict(year=year, source=n, script_candidates=candidates,
                          has_current_team_label='Current Team' in html, title=re.findall(r'<title>(.*?)</title>', html, flags=re.S)))
        print('Captured historical publisher page', year, n['bytes'], flush=True)
    report = dict(source_metadata=note, source_csv=csv_note, repository_blob_sha=repository_file['sha'],
                  dataset_schema=schema, publisher_pages=pages, fitted=False, source_review_status='pending',
                  protected_2026_outcomes_used=False)
    (OUT/'source-inspection.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf8')
    print(json.dumps(schema, indent=2, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    import sys
    if len(sys.argv)>1 and sys.argv[1]=='states':
        inspect_states()
    else:
        main()
