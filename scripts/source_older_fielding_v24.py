"""Bounded public historical fielding capture, private bytes, no model fitting."""
from datetime import datetime,UTC
from pathlib import Path
import gzip
import hashlib
import json
import shutil

import polars as pl
import requests
from universal_baseball.older_fielding_source import decode,normalize
from universal_baseball.storage import sha256_file
from verify_double_play_support_v22 import ROOT,read,write
from run_hitter_finite_return_baseline import protections

OUT=ROOT/'reports/generated/defense-older-quality-v24'
PUBLIC=ROOT/'reports/model-evidence/defense-older-quality-v24'


def main():
    protections()
    assert read(ROOT/'reports/model-evidence/defense-double-play-talent-v23/final-review.json.gz')['player_walkthrough_status']=='complete'
    OUT.mkdir(parents=True,exist_ok=True);PUBLIC.mkdir(parents=True,exist_ok=True)
    pre=PUBLIC/'source-preflight.json.gz'
    paths=[Path(__file__),ROOT/'src/universal_baseball/older_fielding_source.py',ROOT/'tests/test_older_fielding_source.py',
        ROOT/'docs/defense-older-quality-v24-contract.md',ROOT/'reports/model-evidence/defense-double-play-talent-v23/final-review.json.gz']
    if pre.exists():
        for p,d in read(pre)['hashes'].items():assert sha256_file(Path(p))==d,p
    else:write(pre,dict(before_persistent_capture=True,source_years=list(range(2009,2022)),model_fits=0,no_2026_outcomes=True,
        maximum_compressed_capture_bytes=8*1024**2,unauthenticated_public_source=True,hashes={str(p):sha256_file(p) for p in paths}))
    records=[];normalized=[]
    for year in range(2009,2022):
        path=OUT/f'fielding-{year}.html.gz';receipt=OUT/f'fielding-{year}-receipt.json.gz'
        params=dict(stats='fld',pos='all',lg='all',qual='0',type='1',season=str(year),season1=str(year),ind='0',pageitems='5000',pagenum='1')
        if path.exists():
            assert receipt.exists();rec=read(receipt);assert rec['compressed_sha256']==sha256_file(path)
            with gzip.open(path,'rb') as stream:content=stream.read()
        else:
            if shutil.disk_usage(ROOT).free<8*1024**2:raise RuntimeError('Preserve free disk reserve and completed captures; resume exact source script later')
            response=requests.get('https://www.fangraphs.com/leaders/major-league',params=params,
                headers={'User-Agent':'universal-baseball-model-source-review/0.1'},timeout=45)
            response.raise_for_status();content=response.content
            if len(content)>8*1024**2:raise RuntimeError('Unexpectedly large single response')
            rows,meta=decode(content.decode('utf8'),year)
            compressed=gzip.compress(content,mtime=0)
            if sum(p.stat().st_size for p in OUT.glob('fielding-*.html.gz'))+len(compressed)>8*1024**2:
                raise RuntimeError('Stop before exceeding contracted compressed capture budget')
            path.write_bytes(compressed)
            rec=dict(season=year,requested=params,requested_url=response.url,captured_at_utc=datetime.now(UTC).isoformat(),
                raw_sha256=hashlib.sha256(content).hexdigest(),compressed_sha256=sha256_file(path),
                raw_bytes=len(content),compressed_bytes=len(compressed),observed=meta,model_fits=0,
                redistribution='Private retained public capture; no bulk table publication')
            write(receipt,rec)
        assert hashlib.sha256(content).hexdigest()==rec['raw_sha256']
        rows,meta=decode(content.decode('utf8'),year);assert meta==rec['observed']
        out=[n for r in rows if (n:=normalize(r)) is not None]
        assert len(out)==len({(n['player_id'],n['position']) for n in out}),('Duplicate source identities',year)
        assert all(n['decimal_innings_check'] for n in out)
        assert all(n['component_sum_gap'] is None or abs(n['component_sum_gap'])<1e-5 for n in out)
        normalized.extend(out)
        records.append(dict(season=year,raw_rows=len(rows),component_rows=len(out),known_conversion=sum(n['older_conversion_runs'] is not None for n in out),
            known_BIZ=sum(n['BIZ'] is not None for n in out),receipt_sha256=sha256_file(receipt),compressed_sha256=sha256_file(path)))
        print(json.dumps(records[-1]),flush=True)
    normalized_path=OUT/'older-conversion-ledger.parquet';assert not normalized_path.exists()
    pl.DataFrame(normalized,infer_schema_length=None).write_parquet(normalized_path)
    write(PUBLIC/'capture-report.json.gz',dict(years=records,total_rows=len(normalized),model_fits=0,player_walkthrough_status='pending',
        older_metric='UZR RngR + ErrR, kept separate from native range',raw_source_private=True,no_2026_selection=True,
        hashes={str(p):sha256_file(p) for p in (pre,normalized_path)}))
    protections()


if __name__=='__main__':main()
