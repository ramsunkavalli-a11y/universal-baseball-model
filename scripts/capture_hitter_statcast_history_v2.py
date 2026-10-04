"""Resume the same capture, preserving exceptional pitch codes for review."""
import calendar
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
import gzip
import hashlib
import io
import json
from pathlib import Path
import shutil
import time
import polars as pl
import requests
import capture_hitter_statcast_history as previous
from universal_baseball.storage import sha256_file

ROOT, OUT, CONTRACT, COLUMNS = previous.ROOT, previous.OUT, previous.CONTRACT, previous.COLUMNS
AMENDMENT = ROOT/'docs/hitter-statcast-capture-source-semantics-amendment.md'


def capture(year, month):
    assert year in range(2015,2023) and month in range(3,11)
    base = OUT/f'{year}-{month:02}'; receipt_path=base.with_suffix('.json')
    if receipt_path.exists():
        receipt=json.loads(receipt_path.read_text(encoding='utf8'))
        assert receipt['contract_sha256']==sha256_file(CONTRACT)
        assert receipt['collector_sha256'] in [sha256_file(Path(previous.__file__)),sha256_file(Path(__file__))]
        for path,digest in receipt['outputs'].items():
            assert sha256_file(Path(path))==digest
        if 'amendment_sha256' in receipt:
            assert receipt['amendment_sha256']==sha256_file(AMENDMENT)
        print(f'{year}-{month:02}: reused verified source.',flush=True)
        return receipt
    if shutil.disk_usage(ROOT).free < 500_000_000:
        raise ValueError('Stop: disk headroom below 500 MB')
    start=date(year,month,1); end=date(year,month,calendar.monthrange(year,month)[1])
    query=previous._SAVANT_DETAIL_TEMPLATE.format(start_date=start,end_date=end,team='').replace(
        'hfGT=R%7CPO%7CS%7C','hfGT=R%7C').replace('hfPR=&',r'hfPR=hit\.\.into\.\.play%7C&')
    url=previous.SAVANT_ROOT+query
    for attempt in range(3):
        try:
            response=requests.get(url,timeout=(20,90)); response.raise_for_status(); break
        except requests.RequestException:
            if attempt==2: raise
            time.sleep(2*(attempt+1))
    payload=response.content
    raw_path=base.with_suffix('.csv.gz')
    with gzip.GzipFile(filename=str(raw_path),mode='wb',mtime=0) as zipped:
        zipped.write(payload)
    first=payload.lstrip(b'\xef\xbb\xbf \r\n')
    if not first.startswith((b'"pitch_type"',b'pitch_type,')):
        previous.write(OUT/f'rejected-{year}-{month:02}.json',dict(url=url,accepted=False,
            response_sha256=hashlib.sha256(payload).hexdigest(),response_bytes=len(payload),raw_path=str(raw_path)))
        raise ValueError('Stop: response is not a Savant CSV; retained bytes')
    raw=pl.read_csv(io.BytesIO(payload),columns=COLUMNS,schema_overrides={c:pl.String for c in COLUMNS},
                     null_values=['null','NaN','nan',''])
    assert len(raw)<40000,'Potential truncated monthly response'
    if len(raw):
        assert set(raw['game_type'].unique())=={'R'} and set(raw['game_year'].cast(pl.Int64).unique())=={year}
        assert raw['game_date'].str.to_date().is_between(start,end).all()
    path=base.with_suffix('.parquet'); raw.write_parquet(path)
    projected=previous.project_savant_performance_rows(raw,regular_season_only=True)
    terminal=projected.filter(pl.col('is_plate_appearance_terminal'))
    unusual=raw.filter(pl.col('type').fill_null('')!='X')
    receipt=dict(season=year,month=month,requested_url=url,returned_url=response.url,
        captured_at=datetime.now(timezone.utc),response_sha256=hashlib.sha256(payload).hexdigest(),
        response_bytes=len(payload),raw_rows=len(raw),terminal_rows=len(terminal),
        missing_launch_speed=raw['launch_speed'].null_count(),missing_launch_angle=raw['launch_angle'].null_count(),
        returned_events=raw.group_by('events').len().sort('events').to_dicts(),
        unusual_pitch_codes=unusual.select('game_pk','batter','at_bat_number','pitch_number','type','events','description','des').to_dicts(),
        raw_columns=COLUMNS,contract_sha256=sha256_file(CONTRACT),amendment_sha256=sha256_file(AMENDMENT),
        collector_sha256=sha256_file(Path(__file__)),outputs={str(p):sha256_file(p) for p in [raw_path,path]},
        model_fits=0,protected_outcomes_used=False)
    previous.write(receipt_path,receipt)
    print(f'{year}-{month:02}: {len(raw)} contacts, {len(unusual)} exceptional codes.',flush=True)
    return receipt


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    # Prioritize the recent missing training years, without changing the scope.
    work=[(y,m) for y in [2021,2022,2020,2019,2018,2017,2016,2015] for m in [4,3,5,6,7,8,9,10]]
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda pair:capture(*pair),work))
    for year in range(2015,2023):
        previous.reconcile(year)


if __name__=='__main__': main()
