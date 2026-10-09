"""Small public full-season WAR capture for a fixed historical integration check."""
from datetime import datetime,UTC
from pathlib import Path
import gzip,json,re,hashlib
import requests
import polars as pl
from universal_baseball.storage import sha256_file
from capture_hitter_2027_origin_counts import ROOT,write_once

OUT=ROOT/'reports/generated/hitter-2027-base/historical-full-value'
PUBLIC=ROOT/'reports/model-evidence/hitter-2027-v1'


def decode(text,year):
    m=re.search(r'<script\b[^>]*\bid=["\x27]__NEXT_DATA__["\x27][^>]*>(.*?)</script>',text,re.S)
    if not m:raise ValueError('No public season table; do not bypass source restrictions')
    page=json.loads(m[1])['props']['pageProps'];context=page['qsContext']
    assert int(context['season'])==int(context['season1'])==year and context['stats']=='bat' and str(context['qual'])=='0'
    matches=[q for q in page['dehydratedState']['queries'] if q['queryKey'][0]=='leaders/major-league/data']
    assert len(matches)==1
    q=matches[0];query=q['queryKey'][1];body=q['state']['data'];rows=body['data']
    assert query['season']==query['season1']==year and query['stats']=='bat' and str(query['qual'])=='0'
    assert len(rows)==body['totalCount'] and rows
    assert all(r['Season']==r['SeasonMin']==r['SeasonMax']==year for r in rows)
    return rows,dict(context=context,query=query,total_count=body['totalCount'],date_range=body.get('dateRange'))


def main():
    OUT.mkdir(parents=True,exist_ok=True);results=[];receipts=[]
    for year in range(2020,2026):
        p=OUT/f'fg-batting-{year}.html.gz';rp=OUT/f'fg-batting-{year}.receipt.json'
        params=dict(stats='bat',pos='all',lg='all',qual='0',type='8',season=str(year),season1=str(year),ind='0',pageitems='5000',pagenum='1')
        if p.exists():
            rec=json.loads(rp.read_text());assert sha256_file(p)==rec['sha256'];content=gzip.decompress(p.read_bytes())
        else:
            response=requests.get('https://www.fangraphs.com/leaders/major-league',params=params,
                headers={'User-Agent':'universal-baseball-model-source-review/0.1'},timeout=45)
            response.raise_for_status();content=response.content;rows,meta=decode(content.decode(),year)
            # Full batting tables carry many more fields than fielding tables.
            # First attempt hit the old fielding-sized raw cap before any write.
            assert len(content)<32*1024**2
            compressed=gzip.compress(content,mtime=0)
            assert len(compressed)<4*1024**2
            p.write_bytes(compressed)
            rec=dict(url=response.url,captured_at_utc=datetime.now(UTC).isoformat(),sha256=sha256_file(p),
                raw_sha256=hashlib.sha256(content).hexdigest(),observed=meta,public_unauthenticated=True)
            write_once(rp,rec)
        assert hashlib.sha256(content).hexdigest()==rec['raw_sha256']
        rows,meta=decode(content.decode(),year);assert meta==rec['observed']
        normalized=[]
        for r in rows:
            pid=r.get('xMLBAMID');assert pid is not None and int(pid)>0
            normalized.append(dict(season=year,player_id=int(pid),name=r['PlayerName'],fangraphs_id=str(r['playerid']),
                PA=float(r['PA']),WAR=float(r['WAR']),Bat=r.get('Bat'),BsR=r.get('BsR'),Fld=r.get('Fld'),
                Pos=r.get('Pos'),Rep=r.get('Rep'),Lg=r.get('Lg'),Off=r.get('Off'),Def=r.get('Def'),FRM=r.get('FRM'),
                age=r.get('Age'),source=str(p)))
        assert len(normalized)==len({r['player_id'] for r in normalized})
        results.extend(normalized);receipts.append(rec)
        print(year,len(normalized),'PA',sum(r['PA'] for r in normalized),'WAR',sum(r['WAR'] for r in normalized),flush=True)
    output=OUT/'fg-actual-hitter-war.parquet';assert not output.exists()
    pl.DataFrame(results,infer_schema_length=None).write_parquet(output)
    write_once(PUBLIC/'historical-WAR-source.json',dict(source='FanGraphs public all-qualification season batting table',
        seasons=list(range(2020,2026)),rows=len(results),output_sha256=sha256_file(output),captures=receipts,
        no_model_fit=True,no_public_forecast_score_yet=True,private_captures_not_bulk_redistributed=True))


if __name__=='__main__':main()
