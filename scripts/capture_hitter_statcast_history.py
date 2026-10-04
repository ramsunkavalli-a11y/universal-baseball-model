"""Bounded resumable official 2015-2022 contact capture; no modeling."""
import argparse
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
from universal_baseball.savant import SAVANT_ROOT, _SAVANT_DETAIL_TEMPLATE, project_savant_performance_rows
from universal_baseball.mlb_contact_history import RAW_COLUMNS
from universal_baseball.storage import sha256_file

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'reports/generated/hitter-statcast-historical-capture'
CONTRACT = ROOT/'docs/hitter-statcast-historical-capture-contract.md'
COLUMNS = RAW_COLUMNS+['launch_speed', 'launch_angle']


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False, default=str)+'\n', encoding='utf8', newline='\n')


def capture(year, month):
    if year not in range(2015, 2023) or month not in range(3, 11):
        raise ValueError('Protected/out-of-contract request')
    base = OUT/f'{year}-{month:02}'
    receipt_path = base.with_suffix('.json')
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text(encoding='utf8'))
        assert receipt['contract_sha256'] == sha256_file(CONTRACT)
        assert receipt['collector_sha256'] == sha256_file(Path(__file__))
        for path, digest in receipt['outputs'].items():
            assert sha256_file(Path(path)) == digest
        print(f'{year}-{month:02}: reused verified source.', flush=True)
        return receipt
    if shutil.disk_usage(ROOT).free < 500_000_000:
        raise ValueError('Stop capture: disk headroom below 500 MB')
    start = date(year, month, 1); end = date(year, month, calendar.monthrange(year, month)[1])
    query = _SAVANT_DETAIL_TEMPLATE.format(start_date=start, end_date=end, team='').replace(
        'hfGT=R%7CPO%7CS%7C', 'hfGT=R%7C').replace('hfPR=&', r'hfPR=hit\.\.into\.\.play%7C&')
    url = SAVANT_ROOT+query
    for attempt in range(3):
        try:
            response = requests.get(url, timeout=(20, 90))
            response.raise_for_status()
            payload = response.content
            first = payload.lstrip(b'\xef\xbb\xbf \r\n')
            if not first.startswith((b'"pitch_type"', b'pitch_type,')):
                failed_path=OUT/f'failed-{year}-{month:02}-{time.time_ns()}.response.gz'
                with gzip.GzipFile(filename=str(failed_path), mode='wb', mtime=0) as zipped:
                    zipped.write(payload)
                write(failed_path.with_suffix('.json'), dict(requested_url=url, returned_url=response.url,
                    response_sha256=hashlib.sha256(payload).hexdigest(), response_bytes=len(payload),
                    content_type=response.headers.get('Content-Type'), prefix=first[:100].decode('utf8',errors='replace'),
                    accepted=False, model_fits=0, contract_sha256=sha256_file(CONTRACT)))
                raise ValueError(f'Stop capture: unexpected response; {response.headers.get("Content-Type")}; {first[:100]!r}')
            break
        except requests.RequestException:
            if attempt == 2:
                raise
            time.sleep(2*(attempt+1))
    raw = pl.read_csv(io.BytesIO(payload), columns=COLUMNS,
                      schema_overrides={c: pl.String for c in COLUMNS}, null_values=['null', 'NaN', 'nan', ''])
    if len(raw) >= 40_000:
        raise ValueError('Stop capture: monthly response may hit source row limit')
    if len(raw):
        assert set(raw['game_type'].unique()) == {'R'}
        assert set(raw['game_year'].cast(pl.Int64).unique()) == {year}
        assert raw['game_date'].str.to_date().is_between(start, end).all()
        assert set(raw['type'].unique()) == {'X'}, 'In-play filter did not constrain returned pitches'
    raw_path = base.with_suffix('.csv.gz')
    with gzip.GzipFile(filename=str(raw_path), mode='wb', mtime=0) as zipped:
        zipped.write(payload)
    path = base.with_suffix('.parquet'); raw.write_parquet(path)
    projected = project_savant_performance_rows(raw, regular_season_only=True)
    terminal = projected.filter(pl.col('is_plate_appearance_terminal'))
    receipt = dict(season=year, month=month, requested_url=url, returned_url=response.url,
        captured_at=datetime.now(timezone.utc), response_sha256=hashlib.sha256(payload).hexdigest(),
        response_bytes=len(payload), raw_rows=len(raw), terminal_rows=len(terminal),
        missing_launch_speed=raw['launch_speed'].null_count(), missing_launch_angle=raw['launch_angle'].null_count(),
        returned_events=raw.group_by('events').len().sort('events').to_dicts(),
        raw_columns=COLUMNS, contract_sha256=sha256_file(CONTRACT), collector_sha256=sha256_file(Path(__file__)),
        outputs={str(p): sha256_file(p) for p in [raw_path, path]}, model_fits=0, protected_outcomes_used=False)
    write(receipt_path, receipt)
    print(f'{year}-{month:02}: {len(raw)} contacts, {len(payload)//1_000_000} MB before compression.', flush=True)
    return receipt


def reconcile(year):
    chunks = [OUT/f'{year}-{m:02}.json' for m in range(3, 11)]
    if not all(p.exists() for p in chunks):
        return
    receipts = [json.loads(p.read_text(encoding='utf8')) for p in chunks]
    raw = pl.concat([pl.read_parquet(p.with_suffix('.parquet')) for p in chunks])
    key = ['game_pk', 'batter', 'at_bat_number', 'pitch_number']
    assert raw.unique(key).height == len(raw)
    projected = project_savant_performance_rows(raw, regular_season_only=True)
    terminal = projected.filter(pl.col('is_plate_appearance_terminal'))
    measured = terminal.group_by(pl.col('batter_mlbam_id').alias('player_id')).agg(
        pl.len().alias('source_contacts'),
        *[(pl.col('events')==event).sum().alias(name) for event, name in
          [('single','singles'),('double','doubles'),('triple','triples'),('home_run','home_runs')]])
    counts_path = ROOT/'reports/generated/practical-hitter-v31/counts.parquet'
    expected = pl.read_parquet(counts_path).filter((pl.col('season')==year)&(pl.col('bucket')=='MLB')).with_columns(
        (pl.col('babip_hits')-pl.col('doubles')-pl.col('triples')).alias('singles')).select(
            'player_id', 'singles', 'doubles', 'triples', 'home_runs')
    dated_path = ROOT/'reports/generated/practical-hitter-v31/dated-stints.parquet'
    dates = pl.read_parquet(dated_path).filter((pl.col('season')==year)&(pl.col('bucket')=='MLB')).group_by('player_id').agg(
        (pl.col('at_bats')-pl.col('strike_outs')+pl.col('sac_flies')+pl.col('sac_bunts')).sum().alias('official_contacts'))
    joined = expected.join(measured, on='player_id', how='full', coalesce=True, suffix='_source').join(dates, on='player_id', how='full', coalesce=True)
    fields = ['singles','doubles','triples','home_runs']
    joined = joined.with_columns(pl.col(fields+[c+'_source' for c in fields]+['source_contacts','official_contacts']).fill_null(0))
    errors = joined.filter(pl.any_horizontal([pl.col(c)!=pl.col(c+'_source') for c in fields])|
                          (pl.col('source_contacts')!=pl.col('official_contacts')))
    errors.write_parquet(OUT/f'reconciliation-{year}.parquet')
    report = dict(season=year, raw_contacts=len(raw), terminal_contacts=len(terminal),
        source_rows_without_true_PA=len(raw)-len(terminal), people=raw['batter'].n_unique(),
        exact_hit_counts=joined.select(pl.all_horizontal([pl.col(c)==pl.col(c+'_source') for c in fields]).all()).item(),
        exact_contact_denominator=joined['source_contacts'].equals(joined['official_contacts']),
        players_with_discrepancies=len(errors), discrepancy_rows=errors.to_dicts(),
        official_count_sha256=sha256_file(counts_path), official_dated_sha256=sha256_file(dated_path),
        chunk_receipt_hashes={str(p):sha256_file(p) for p in chunks}, new_model_fits=0,
        approved_for_modeling=False, source_walkthrough_status='pending')
    write(OUT/f'reconciliation-{year}.json', report)
    print(f'{year}: exact hits={report["exact_hit_counts"]}, exact contact denominator={report["exact_contact_denominator"]}; {len(errors)} people need review.', flush=True)


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--complete',action='store_true'); args=parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    probe = capture(2015, 4)
    if not args.complete:
        print('Probe captured; inspect before continuing.', flush=True); return
    assert probe['raw_rows'] > 0 and probe['raw_rows'] == probe['terminal_rows']
    work = [(y,m) for y in range(2015,2023) for m in [4,3,5,6,7,8,9,10] if (y,m)!=(2015,4)]
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda pair:capture(*pair), work))
    for y in range(2015,2023):
        reconcile(y)


if __name__=='__main__':
    main()
