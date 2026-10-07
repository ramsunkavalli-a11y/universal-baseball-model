"""Resume exact saved captures with explicit legacy precision checks."""
from datetime import datetime,UTC
from pathlib import Path
import gzip
import hashlib
import json
import shutil

import polars as pl
import requests
from universal_baseball.older_fielding_source import decode
from universal_baseball.older_fielding_source_precision import normalized_with_precision
from universal_baseball.storage import sha256_file
from verify_double_play_support_v22 import ROOT,read,write
from run_hitter_finite_return_baseline import protections

OUT=ROOT/'reports/generated/defense-older-quality-v24'
PUBLIC=ROOT/'reports/model-evidence/defense-older-quality-v24'


def main():
    protections()
    first=PUBLIC/'source-preflight.json.gz'
    for p,d in read(first)['hashes'].items():assert sha256_file(Path(p))==d,p
    pre=PUBLIC/'precision-preflight.json.gz'
    paths=[Path(__file__),ROOT/'src/universal_baseball/older_fielding_source_precision.py',ROOT/'tests/test_older_fielding_source_precision.py',
        ROOT/'docs/defense-older-quality-v24-precision-amendment.md',first]
    if pre.exists():
        for p,d in read(pre)['hashes'].items():assert sha256_file(Path(p))==d,p
    else:write(pre,dict(before_remaining_captures=True,model_fits=0,maximum_decimal_outs_gap=.02,maximum_component_runs_gap=.001,
        first_runner_terminal='AssertionError after saved 2009 source; no ledger or model',hashes={str(p):sha256_file(p) for p in paths}))
    records=[];normalized=[]
    for year in range(2009,2022):
        path=OUT/f'fielding-{year}.html.gz';receipt=OUT/f'fielding-{year}-receipt.json.gz'
        params=dict(stats='fld',pos='all',lg='all',qual='0',type='1',season=str(year),season1=str(year),ind='0',pageitems='5000',pagenum='1')
        reused=path.exists()
        if reused:
            assert receipt.exists();rec=read(receipt);assert rec['compressed_sha256']==sha256_file(path)
            with gzip.open(path,'rb') as stream:content=stream.read()
        else:
            if shutil.disk_usage(ROOT).free<8*1024**2:raise RuntimeError('Preserve free disk reserve and completed captures')
            response=requests.get('https://www.fangraphs.com/leaders/major-league',params=params,
                headers={'User-Agent':'universal-baseball-model-source-review/0.1'},timeout=45)
            response.raise_for_status();content=response.content
            if len(content)>8*1024**2:raise RuntimeError('Unexpectedly large single response')
            rows,meta=decode(content.decode('utf8'),year);compressed=gzip.compress(content,mtime=0)
            if sum(p.stat().st_size for p in OUT.glob('fielding-*.html.gz'))+len(compressed)>8*1024**2:
                raise RuntimeError('Stop before exceeding compressed source budget')
            path.write_bytes(compressed)
            rec=dict(season=year,requested=params,requested_url=response.url,captured_at_utc=datetime.now(UTC).isoformat(),
                raw_sha256=hashlib.sha256(content).hexdigest(),compressed_sha256=sha256_file(path),raw_bytes=len(content),
                compressed_bytes=len(compressed),observed=meta,model_fits=0,
                redistribution='Private retained public capture; no bulk table publication')
            write(receipt,rec)
        assert hashlib.sha256(content).hexdigest()==rec['raw_sha256']
        rows,meta=decode(content.decode('utf8'),year);assert meta==rec['observed']
        out=[n for r in rows if (n:=normalized_with_precision(r)) is not None]
        assert len(out)==len({(n['player_id'],n['position']) for n in out}),('Duplicate source identities',year)
        normalized.extend(out)
        records.append(dict(season=year,raw_rows=len(rows),component_rows=len(out),known_conversion=sum(n['older_conversion_runs'] is not None for n in out),
            known_BIZ=sum(n['BIZ'] is not None for n in out),original_decimal_check_failures=sum(not n['original_decimal_innings_check'] for n in out),
            max_decimal_outs_gap=max(abs(n['decimal_innings_gap_outs']) for n in out),
            max_component_runs_gap=max(abs(n['component_sum_gap']) for n in out if n['component_sum_gap'] is not None),
            reused_exact_capture=reused,receipt_sha256=sha256_file(receipt),compressed_sha256=sha256_file(path)))
        print(json.dumps(records[-1]),flush=True)
    target=OUT/'older-conversion-ledger.parquet';assert not target.exists()
    pl.DataFrame(normalized,infer_schema_length=None).write_parquet(target)
    write(PUBLIC/'capture-report.json.gz',dict(years=records,total_rows=len(normalized),model_fits=0,player_walkthrough_status='pending',
        older_metric='UZR RngR + ErrR, kept separate from native range',raw_source_private=True,no_2026_selection=True,
        hashes={str(p):sha256_file(p) for p in (first,pre,target)}))
    protections()


if __name__=='__main__':main()
