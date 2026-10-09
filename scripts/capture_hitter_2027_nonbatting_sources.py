"""Refresh existing native source methods for the 2027 build, without fits."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import csv
import gzip
import hashlib
import io
import json

import polars as pl
import requests

from source_defensive_positions_v2 import embedded, decode as decode_fielding
from universal_baseball.player_value_baserunning_sources import (
    savant_baserunning_query_params,parse_savant_baserunning_csv,audit_savant_baserunning_rows)
from universal_baseball.storage import sha256_file
from capture_hitter_2027_origin_counts import ROOT,write_once

OUT=ROOT/'reports/generated/hitter-2027-nonbatting-source'
PUBLIC=ROOT/'reports/model-evidence/hitter-2027-v1'
BASE='https://baseballsavant.mlb.com/leaderboard/'


def tasks():
    field=dict(type='fielder',seasonStart=2026,seasonEnd=2026,minInnings=0,minResults=0)
    common=dict(game_type='Regular',n=1,season_start=2026,season_end=2026,split='no',team='',with_team_only=0)
    return [
        ('fielding-position',BASE+'fielding-run-value',dict(**field,groupBy='position'),'html'),
        ('fielding-aggregate',BASE+'fielding-run-value',field,'html'),
        ('framing',BASE+'catcher-framing',dict(type='catcher',seasonStart=2026,seasonEnd=2026,minPitches=1,min=1,team='',sortColumn='rv_tot',sortDirection='desc'),'html'),
        ('arm',BASE+'baserunning',dict(**common,type='Fld'),'html'),
        ('receiving',BASE+'first-base-scoops-receiving',{'type':'fielder_3','season[]':2026,'splitYear':1,'min':1,'minSplit':1,'gameType[]':'R'},'html'),
        ('throwing',BASE+'catcher-throwing',dict(**common,type='Cat',csv='true',target_base='All'),'csv'),
        ('blocking',BASE+'catcher-blocking',dict(**common,type='Cat',csv='true'),'csv'),
        ('running',BASE+'baserunning-run-value',savant_baserunning_query_params(2026),'csv'),
        ('official-fielding','https://statsapi.mlb.com/api/v1/stats',dict(stats='season',group='fielding',season=2026,sportIds=1,gameType='R',playerPool='ALL',limit=5000),'json'),
        ('official-team-pitching','https://statsapi.mlb.com/api/v1/teams/stats',dict(stats='season',group='pitching',season=2026,sportIds=1,gameType='R',limit=100),'json'),
    ]


def capture(task):
    name,url,params,kind=task
    path=OUT/'captures'/f'{name}.response.gz';receipt=path.with_suffix('.receipt.json')
    if receipt.exists():
        info=json.loads(receipt.read_text(encoding='utf8'))
        assert info['requested_url']==url and info['params']==params and sha256_file(path)==info['compressed_sha256']
        raw=gzip.decompress(path.read_bytes());assert hashlib.sha256(raw).hexdigest()==info['response_sha256']
    else:
        assert not path.exists(),'Unreceipted source response'
        response=requests.get(url,params=params,timeout=(15,45));response.raise_for_status();raw=response.content
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(gzip.compress(raw,mtime=0))
        info=dict(requested_url=url,params=params,returned_url=response.url,content_type=response.headers.get('content-type'),
                  captured_utc=datetime.now(timezone.utc).isoformat(),response_sha256=hashlib.sha256(raw).hexdigest(),compressed_sha256=sha256_file(path))
        write_once(receipt,info)
    content=raw.decode('utf-8-sig');meta={};audit={}
    if kind=='html':
        meta=embedded(content,'serverParams');rows=embedded(content,'data')
        if name.startswith('fielding'):
            decode_fielding(content,2026,name=='fielding-position')
        elif name=='framing':
            assert int(meta['seasonStart'])==int(meta['seasonEnd'])==2026 and meta['minPitches']==1
        elif name=='receiving':
            assert meta['season']==['2026'] and meta['gameType']==['R'] and meta['min']==meta['minSplit']==1
            assert {int(r['year']) for r in rows}=={2026}
        else:
            assert meta['season_start']==meta['season_end']==2026 and meta['entity_code']=='Fld' and meta['with_team_only'] is False
            assert {r['start_year'] for r in rows}=={2026}
    elif kind=='csv':
        assert not content.lstrip().startswith('<'),'HTML is not a CSV measurement'
        rows=parse_savant_baserunning_csv(content) if name=='running' else list(csv.DictReader(io.StringIO(content)))
        assert rows and {int(r['start_year']) for r in rows}=={2026}
        assert all(not str(r.get('end_year','')).strip() or int(r['end_year'])==2026 for r in rows)
        if name=='running':
            audit=audit_savant_baserunning_rows(rows)
            assert audit['advancement_source_usable']
    else:
        blocks=json.loads(content)['stats'];assert len(blocks)==1
        assert blocks[0]['group']['displayName']==params['group'] and blocks[0]['type']['displayName']=='season'
        rows=blocks[0]['splits'];assert rows and len(rows)<params['limit']
        assert {int(r['season']) for r in rows}=={2026}
        if name=='official-team-pitching':assert len(rows)==30
    assert rows,'Empty source cannot be treated as zero measurements'
    parsed=OUT/f'{name}-rows.json.gz'
    encoded=gzip.compress(json.dumps(rows,allow_nan=False,ensure_ascii=False).encode('utf8'),mtime=0)
    if parsed.exists():assert parsed.read_bytes()==encoded
    else:parsed.write_bytes(encoded)
    print(f'{name}: {len(rows)} rows, verified 2026 metadata',flush=True)
    return dict(source=name,rows=len(rows),metadata=meta,source_path=str(path),source_sha256=sha256_file(path),
                parsed_path=str(parsed),parsed_sha256=sha256_file(parsed),audit=audit,receipt=info)


def main():
    report=PUBLIC/'nonbatting-source-capture.json'
    assert not report.exists(),'Preserve completed source capture'
    with ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(capture,tasks()))
    write_once(report,dict(status='dated_2026_captures_component_reconciliation_pending',captures=results,
        source_approved_for_estimation=False,models_fitted=0,old_forecasts_changed=False,
        source_method='Existing official/native endpoints, new year, explicit metadata; no algorithm change',
        pending=['native component sums and official-position outs',
                 'native opportunity denominators and independent run numerators',
                 '2026 source-player walkthrough before component estimation'],runner_sha256=sha256_file(Path(__file__))))


if __name__=='__main__':main()
