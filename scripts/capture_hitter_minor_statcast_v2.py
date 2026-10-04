"""Resume historical contact-only capture with additive terminal semantics."""
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
import capture_hitter_minor_statcast as old
from universal_baseball.hitter_minor_statcast_source_v2 import (
    COLUMNS, KEY, LIMIT, contact_url, split_window, validate_contact_response)
from universal_baseball.storage import sha256_file

ROOT, OUT, CONTRACT = old.ROOT, old.OUT, old.CONTRACT
AMENDMENT=ROOT/'docs/hitter-minor-statcast-contact-semantics-amendment.md'
MODULE=ROOT/'src/universal_baseball/hitter_minor_statcast_source_v2.py'


def capture(start, end, *, tracked=False, pilot=False):
    base=OUT/('pilot' if pilot else 'seasons')/f'{start}_{end}_{"tracked" if tracked else "all"}'
    base.parent.mkdir(parents=True,exist_ok=True)
    receipt_path=base.with_suffix('.json')
    if receipt_path.exists():
        note=json.loads(receipt_path.read_text(encoding='utf8'))
        assert note['contract_sha256']==sha256_file(CONTRACT)
        assert note['collector_sha256'] in [sha256_file(Path(old.__file__)),sha256_file(Path(__file__))]
        assert note['module_sha256'] in [sha256_file(old.MODULE),sha256_file(MODULE)]
        if 'amendment_sha256' in note:assert note['amendment_sha256']==sha256_file(AMENDMENT)
        for p,h in note['outputs'].items():assert sha256_file(Path(p))==h
        if note['capped']:
            return [r for a,b in split_window(start,end) for r in capture(a,b,tracked=tracked,pilot=pilot)]
        validate_contact_response(pl.read_parquet(base.with_suffix('.parquet')),start,end)
        return [note]
    raw_path=base.with_suffix('.csv.gz');url=contact_url(start,end,tracked=tracked)
    reused_rejected=None
    if raw_path.exists():
        rejected=base.with_suffix('.rejected.json');assert rejected.exists(),'Unreceipted bytes'
        saved=json.loads(rejected.read_text(encoding='utf8'))
        assert saved['outputs'][str(raw_path)]==sha256_file(raw_path)
        payload=gzip.decompress(raw_path.read_bytes())
        assert saved['response_sha256']==hashlib.sha256(payload).hexdigest()
        assert saved['requested_url']==url and saved['contract_sha256']==sha256_file(CONTRACT)
        captured_at=saved['captured_at'];returned_url=saved['returned_url'];reused_rejected=str(rejected)
    else:
        if shutil.disk_usage(ROOT).free<500_000_000:raise ValueError('Disk headroom below 500 MB')
        for attempt in range(3):
            try:
                response=requests.get(url,timeout=(20,90));response.raise_for_status();break
            except requests.RequestException:
                if attempt==2:raise
                time.sleep(2*(attempt+1))
        payload=response.content;captured_at=datetime.now(timezone.utc);returned_url=response.url
        with gzip.GzipFile(filename=str(raw_path),mode='wb',mtime=0) as z:z.write(payload)
    note=dict(start=start,end=end,tracked_flag=tracked,requested_url=url,returned_url=returned_url,
        captured_at=captured_at,response_sha256=hashlib.sha256(payload).hexdigest(),response_bytes=len(payload),
        contract_sha256=sha256_file(CONTRACT),amendment_sha256=sha256_file(AMENDMENT),
        collector_sha256=sha256_file(Path(__file__)),module_sha256=sha256_file(MODULE),
        outputs={str(raw_path):sha256_file(raw_path)},reused_rejected_response=reused_rejected,
        model_fits=0,protected_outcomes_used=False)
    first=payload.lstrip(b'\xef\xbb\xbf \r\n')
    if not first.startswith((b'"pitch_type"',b'pitch_type,')):
        old.write(base.with_suffix('.rejected-v2.json'),dict(note,accepted=False,reason='non-CSV'))
        raise ValueError('Unexpected response; preserved raw bytes')
    raw=pl.read_csv(io.BytesIO(payload),columns=COLUMNS,schema_overrides={c:pl.String for c in COLUMNS},null_values=['','null','NaN','nan'])
    capped=raw.height>=LIMIT
    terminal=raw.filter(pl.col('events').fill_null('').str.strip_chars().ne(''))
    note.update(raw_rows=raw.height,terminal_rows=terminal.height,capped=capped,accepted=not capped,
        returned_date_min=raw['game_date'].min(),returned_date_max=raw['game_date'].max(),games=raw['game_pk'].n_unique(),
        events=raw.group_by('events').len().sort('events').to_dicts(),
        nonterminal_rows=raw.height-terminal.height)
    if not capped:
        try:validate_contact_response(raw,start,end)
        except Exception as exc:
            old.write(base.with_suffix('.rejected-v2.json'),dict(note,accepted=False,reason=str(exc)));raise
        path=base.with_suffix('.parquet');assert not path.exists();raw.write_parquet(path)
        note['outputs'][str(path)]=sha256_file(path)
    old.write(receipt_path,note)
    print(f'{start}–{end}: {raw.height} source rows/{terminal.height} terminals, {note["games"]} games, capped={capped}',flush=True)
    if capped:return [r for a,b in split_window(start,end) for r in capture(a,b,tracked=tracked,pilot=pilot)]
    return [note]


def main(phase):
    OUT.mkdir(parents=True,exist_ok=True)
    if phase=='pilot':
        assert (OUT/'legacy-inventory.json').exists()
        work=[(date(y,7,1),date(y,7,1),False) for y in range(2021,2025)]
        work += [(date(2022,7,1),date(2022,7,1),True),(date(2023,7,1),date(2023,7,1),True),
            (date(2023,4,7),date(2023,4,7),False),(date(2023,6,9),date(2023,6,9),False)]
        final=OUT/'pilot-capture.json'
    else:
        approval=json.loads((OUT/'pilot-review.json').read_text(encoding='utf8'))
        assert approval['contact_request_approved'] and approval['tracked_flag_choice']=='omit'
        assert approval['contract_sha256']==sha256_file(CONTRACT)
        assert approval['pilot_report_sha256']==sha256_file(OUT/'pilot-capture.json')
        work=[]
        for year in [2021,2022,2023,2024]:
            start=date(year,3,1)
            while start<=date(year,10,31):
                end=min(start+timedelta(days=6),date(year,10,31))
                work.append((start,end,False));start=end+timedelta(days=1)
        final=OUT/'season-capture.json'
    assert not final.exists(),'Preserve completed capture'
    with ThreadPoolExecutor(max_workers=2) as pool:
        result=list(pool.map(lambda x:capture(x[0],x[1],tracked=x[2],pilot=phase=='pilot'),work))
    old.write(final,dict(receipts=[r for g in result for r in g],model_fits=0,source_approval=False,
        contract_sha256=sha256_file(CONTRACT),amendment_sha256=sha256_file(AMENDMENT),collector_sha256=sha256_file(Path(__file__))))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=['pilot','seasons'],required=True)
    main(parser.parse_args().phase)
