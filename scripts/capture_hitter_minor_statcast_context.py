"""Retain official historical minor schedule and venue authority, without fits."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import requests
from universal_baseball.storage import sha256_file
import capture_hitter_minor_statcast as capture

ROOT,OUT,CONTRACT=capture.ROOT,capture.OUT,capture.CONTRACT
SPORTS=[11,12,13,14,16]


def capture_schedule(year,sport):
    assert year in range(2021,2025) and sport in SPORTS
    base=OUT/'official-context'/f'schedule-{year}-{sport}';base.parent.mkdir(parents=True,exist_ok=True)
    path=base.with_suffix('.json.gz');receipt=base.with_suffix('.json')
    if receipt.exists():
        r=json.loads(receipt.read_text(encoding='utf8'))
        assert r['script_sha256']==sha256_file(Path(__file__)) and r['contract_sha256']==sha256_file(CONTRACT)
        assert r['compressed_sha256']==sha256_file(path)
        assert r['response_sha256']==hashlib.sha256(gzip.decompress(path.read_bytes())).hexdigest()
        return r
    assert not path.exists(),'Preserve unreceipted bytes'
    response=requests.get('https://statsapi.mlb.com/api/v1/schedule',params=dict(sportId=sport,
        startDate=f'{year}-03-01',endDate=f'{year}-10-31',gameTypes='R',hydrate='team,venue'),timeout=(20,60))
    response.raise_for_status();payload=response.content;data=response.json()
    assert 'dates' in data
    games=[g for d in data['dates'] for g in d['games']]
    assert all(int(g['season'])==year and g['gameType']=='R' for g in games)
    with gzip.GzipFile(filename=str(path),mode='wb',mtime=0) as z:z.write(payload)
    note=dict(season=year,sport_id=sport,requested_url=response.request.url,returned_url=response.url,
        captured_at=datetime.now(timezone.utc),response_bytes=len(payload),response_sha256=hashlib.sha256(payload).hexdigest(),
        compressed_path=str(path),compressed_sha256=sha256_file(path),games=len(games),unique_game_pks=len({g['gamePk'] for g in games}),
        script_sha256=sha256_file(Path(__file__)),contract_sha256=sha256_file(CONTRACT),model_fits=0,protected_outcomes_used=False)
    capture.write(receipt,note);print(f'{year} sport {sport}: {len(games)} schedule rows',flush=True)
    return note


if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=2) as pool:
        notes=list(pool.map(lambda x:capture_schedule(*x),[(y,s) for y in range(2021,2025) for s in SPORTS]))
    capture.write(OUT/'official-context/capture-report.json',dict(receipts=notes,source_approval=False,model_fits=0))
