"""Bounded 2026 predictor capture for the 2027 build; no future outcomes."""
import argparse
import calendar
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
import gzip
import hashlib
import io
import json
from pathlib import Path
import time
import polars as pl
import requests
from universal_baseball.savant import SAVANT_ROOT, _SAVANT_DETAIL_TEMPLATE
from universal_baseball.mlb_contact_history import RAW_COLUMNS
from universal_baseball.storage import sha256_file

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'reports/generated/hitter-tracking-2026-source'
CONTRACT = ROOT/'docs/hitter-2027-tracking-intake.md'
COLUMNS = RAW_COLUMNS + ['launch_speed', 'launch_angle']


def write(path, obj):
    if path.exists():
        raise ValueError(f'Preserve {path}')
    path.write_text(json.dumps(obj, indent=2, allow_nan=False, default=str)+'\n', encoding='utf8', newline='\n')


def capture(month):
    if month not in range(3, 11):
        raise ValueError('Only declared 2026 season months')
    base = OUT/f'2026-{month:02}'; receipt_path = base.with_suffix('.json')
    if receipt_path.exists():
        obj = json.loads(receipt_path.read_text(encoding='utf8'))
        assert obj['contract_sha256'] == sha256_file(CONTRACT)
        assert obj['collector_sha256'] == sha256_file(Path(__file__))
        for path, digest in obj['outputs'].items():
            assert sha256_file(Path(path)) == digest
        print(f'2026-{month:02}: verified saved capture', flush=True)
        return obj
    start = date(2026, month, 1); end = min(date(2026, month, calendar.monthrange(2026, month)[1]), date(2026,10,9))
    query = _SAVANT_DETAIL_TEMPLATE.format(start_date=start, end_date=end, team='').replace(
        'hfGT=R%7CPO%7CS%7C', 'hfGT=R%7C').replace('hfPR=&', r'hfPR=hit\.\.into\.\.play%7C&')
    url = SAVANT_ROOT+query
    for attempt in range(3):
        try:
            response = requests.get(url, timeout=(20, 90)); response.raise_for_status(); break
        except requests.RequestException:
            if attempt == 2:
                raise
            time.sleep(2*(attempt+1))
    payload = response.content
    raw_path = base.with_suffix('.csv.gz')
    if raw_path.exists():
        raise ValueError(f'Unreceipted capture requires review: {raw_path}')
    with gzip.GzipFile(filename=str(raw_path), mode='wb', mtime=0) as zipped:
        zipped.write(payload)
    if not payload.lstrip(b'\xef\xbb\xbf \r\n').startswith((b'"pitch_type"', b'pitch_type,')):
        write(base.with_suffix('.rejected.json'), dict(url=url, bytes=len(payload),
            response_sha256=hashlib.sha256(payload).hexdigest(), accepted=False))
        raise ValueError('Not a Savant CSV; bytes preserved')
    raw = pl.read_csv(io.BytesIO(payload), columns=COLUMNS,
        schema_overrides={c: pl.String for c in COLUMNS}, null_values=['null', 'NaN', 'nan', ''])
    assert len(raw) < 40000, 'Potential source truncation'
    if len(raw):
        assert set(raw['game_type'].unique()) == {'R'}
        assert set(raw['game_year'].cast(pl.Int64).unique()) == {2026}
        assert raw['game_date'].str.to_date().is_between(start, end).all()
    path = base.with_suffix('.parquet'); assert not path.exists(); raw.write_parquet(path)
    obj = dict(season=2026, month=month, requested_url=url, returned_url=response.url,
        captured_at=datetime.now(timezone.utc).isoformat(), raw_rows=len(raw), response_bytes=len(payload),
        response_sha256=hashlib.sha256(payload).hexdigest(), collector_sha256=sha256_file(Path(__file__)),
        contract_sha256=sha256_file(CONTRACT), outputs={str(p): sha256_file(p) for p in [raw_path, path]},
        model_fits=0, source_2026_is_exposed_development=True, original_publication_vintage_verified=False)
    write(receipt_path, obj)
    print(f'2026-{month:02}: {len(raw)} raw contacts', flush=True)
    return obj


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--complete', action='store_true'); args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    capture(4)
    if args.complete:
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(capture, [3, 5, 6, 7, 8, 9, 10]))


if __name__ == '__main__':
    main()
