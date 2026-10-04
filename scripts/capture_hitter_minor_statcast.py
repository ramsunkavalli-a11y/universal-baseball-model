"""Bounded historical minor contact capture, preserving capped older caches."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
import gzip
import hashlib
import io
import json
from pathlib import Path
import shutil
import time
import polars as pl
import requests
from universal_baseball.hitter_minor_statcast_source import (
    COLUMNS, KEY, LIMIT, contact_url, split_window, validate_contact_response)
from universal_baseball.storage import sha256_file

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'reports/generated/hitter-minor-statcast-capture'
CONTRACT = ROOT/'docs/hitter-minor-statcast-source-contract.md'
LEGACY = Path('C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/universal-baseball-model/reports/generated/pitcher-tracking-source/2023/milb/raw')
MODULE = ROOT/'src/universal_baseball/hitter_minor_statcast_source.py'


def write(path, payload):
    assert not path.exists(), f'Preserve {path}'
    path.write_text(json.dumps(payload, indent=2, allow_nan=False, default=str)+'\n', encoding='utf8', newline='\n')


def capture(start, end, *, tracked=False, pilot=False):
    base = OUT/('pilot' if pilot else 'seasons')/f'{start}_{end}_{"tracked" if tracked else "all"}'
    base.parent.mkdir(parents=True, exist_ok=True)
    receipt_path = base.with_suffix('.json')
    if receipt_path.exists():
        note = json.loads(receipt_path.read_text(encoding='utf8'))
        assert note['contract_sha256'] == sha256_file(CONTRACT)
        assert note['collector_sha256'] == sha256_file(Path(__file__))
        assert note['module_sha256'] == sha256_file(MODULE)
        for p, h in note['outputs'].items():
            assert sha256_file(Path(p)) == h
        if note['capped']:
            return [item for a, b in split_window(start,end) for item in capture(a,b,tracked=tracked,pilot=pilot)]
        return [note]
    if shutil.disk_usage(ROOT).free < 500_000_000:
        raise ValueError('Disk headroom below 500 MB')
    url = contact_url(start, end, tracked=tracked)
    for attempt in range(3):
        try:
            response = requests.get(url, timeout=(20,90))
            response.raise_for_status()
            break
        except requests.RequestException:
            if attempt == 2: raise
            time.sleep(2*(attempt+1))
    payload = response.content
    raw_path = base.with_suffix('.csv.gz')
    assert not raw_path.exists(), f'Unreceipted raw bytes already exist: {raw_path}'
    with gzip.GzipFile(filename=str(raw_path), mode='wb', mtime=0) as zipped:
        zipped.write(payload)
    note = dict(start=start, end=end, tracked_flag=tracked, requested_url=url,
        returned_url=response.url, captured_at=datetime.now(timezone.utc),
        response_sha256=hashlib.sha256(payload).hexdigest(), response_bytes=len(payload),
        contract_sha256=sha256_file(CONTRACT), collector_sha256=sha256_file(Path(__file__)),
        module_sha256=sha256_file(MODULE), outputs={str(raw_path):sha256_file(raw_path)},
        model_fits=0, protected_outcomes_used=False)
    first = payload.lstrip(b'\xef\xbb\xbf \r\n')
    if not first.startswith((b'"pitch_type"', b'pitch_type,')):
        write(base.with_suffix('.rejected.json'), dict(note, accepted=False, reason='non-CSV response'))
        raise ValueError('Unexpected source response; exact bytes preserved')
    raw = pl.read_csv(io.BytesIO(payload), columns=COLUMNS,
        schema_overrides={c:pl.String for c in COLUMNS}, null_values=['','null','NaN','nan'])
    capped = raw.height >= LIMIT
    note.update(raw_rows=raw.height, capped=capped, accepted=not capped,
        returned_date_min=raw['game_date'].min(), returned_date_max=raw['game_date'].max(),
        games=raw['game_pk'].n_unique(), events=raw.group_by('events').len().sort('events').to_dicts())
    if not capped:
        try:
            validate_contact_response(raw,start,end)
        except Exception as exc:
            write(base.with_suffix('.rejected.json'),dict(note,accepted=False,reason=str(exc)))
            raise
        path = base.with_suffix('.parquet'); assert not path.exists()
        raw.write_parquet(path); note['outputs'][str(path)] = sha256_file(path)
    write(receipt_path, note)
    print(f'{start}–{end}: {raw.height} rows, {note["games"]} games, capped={capped}', flush=True)
    if capped:
        return [item for a,b in split_window(start,end) for item in capture(a,b,tracked=tracked,pilot=pilot)]
    return [note]


def pilot():
    inventory=[]
    for path in sorted(LEGACY.glob('*.csv')):
        raw=pl.read_csv(path,columns=COLUMNS,schema_overrides={c:pl.String for c in COLUMNS},null_values=['','null'])
        expected_start=path.stem[-21:-11]; expected_end=path.stem[-10:]
        inventory.append(dict(path=str(path),sha256=sha256_file(path),rows=raw.height,
            requested_start=expected_start,requested_end=expected_end,
            returned_start=raw['game_date'].min(),returned_end=raw['game_date'].max(),
            contacts=raw.filter((pl.col('type')=='X')&pl.col('events').is_not_null()).height,
            potentially_capped=raw.height>=LIMIT))
    inventory_path=OUT/'legacy-inventory.json'
    if inventory_path.exists():
        assert json.loads(inventory_path.read_text(encoding='utf8'))['files']==inventory
    else:
        write(inventory_path,dict(files=inventory,not_approved_as_full_history=True,
            no_old_predictive_result_reclassified=True))
    work=[(date(y,7,1), False) for y in range(2021,2025)]
    work += [(date(2022,7,1),True),(date(2023,7,1),True),
             (date(2023,4,7),False),(date(2023,6,9),False)]
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda item:capture(item[0],item[0],tracked=item[1],pilot=True),work))
    write(OUT/'pilot-capture.json',dict(receipts=[r for group in results for r in group],
        model_fits=0,source_approval=False,contract_sha256=sha256_file(CONTRACT)))


def seasons():
    approval=json.loads((OUT/'pilot-review.json').read_text(encoding='utf8'))
    assert approval['contact_request_approved'] and approval['tracked_flag_choice']=='omit'
    assert approval['contract_sha256']==sha256_file(CONTRACT)
    assert approval['pilot_report_sha256']==sha256_file(OUT/'pilot-capture.json')
    work=[]
    for year in [2021,2022,2023,2024]:
        start=date(year,3,1)
        while start<=date(year,10,31):
            end=min(start+timedelta(days=6),date(year,10,31))
            work.append((start,end));start=end+timedelta(days=1)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda item:capture(*item),work))
    receipts=[r for group in results for r in group]
    write(OUT/'season-capture.json',dict(receipts=receipts,model_fits=0,source_approval=False,
        contract_sha256=sha256_file(CONTRACT),pilot_review_sha256=sha256_file(OUT/'pilot-review.json')))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=['pilot','seasons'],required=True)
    args=parser.parse_args();OUT.mkdir(parents=True,exist_ok=True)
    pilot() if args.phase=='pilot' else seasons()
