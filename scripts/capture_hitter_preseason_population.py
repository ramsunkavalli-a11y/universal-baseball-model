"""Immutable source capture with an explicit temporal probe before broad retrieval."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
from pathlib import Path
import requests
from universal_baseball.storage import sha256_file

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/generated/hitter-preseason-population-source'
CONFIG=ROOT/'config/hitter_preseason_rank_v67_release_evidence.json'
BASE='https://statsapi.mlb.com/api/v1'


def read(p): return json.loads(Path(p).read_text(encoding='utf8'))


def write(p,obj):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    content=json.dumps(obj,ensure_ascii=False,allow_nan=False,separators=(',',':'))+'\n'
    if p.exists(): assert p.read_text(encoding='utf8')==content,'Preserve existing source receipt'
    else: p.write_text(content,encoding='utf8',newline='\n')


def capture(name,url,params):
    p=OUT/'captures'/name;meta=p.with_suffix('.json.metadata.json')
    if meta.exists():
        m=read(meta); assert m['url']==url and m['params']==params and sha256_file(p)==m['sha256'];return read(p),m
    if p.exists(): raise RuntimeError('Unreceipted capture exists; reconcile before retry: '+str(p))
    error=None
    for _ in range(3):
        try:
            response=requests.get(url,params=params,timeout=(10,30),headers={'User-Agent':'UBM historical preseason population research'})
            response.raise_for_status();payload=response.json()
            if not isinstance(payload,dict): raise ValueError('Expected source object')
            p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(response.content)
            m=dict(url=url,params=params,requested_url=response.url,captured_utc=datetime.now(timezone.utc).isoformat(),sha256=sha256_file(p),bytes=p.stat().st_size,
                   source_is_retrospective=True,contemporaneous_publication_vintage_verified=False)
            write(meta,m);return payload,m
        except requests.RequestException as e: error=e
    raise RuntimeError('Capture failed: '+name) from error


def roster(team,year,kind):
    cutoff=read(CONFIG)[str(year)]['date'];assert 2012<=year<=2025 and cutoff.startswith(str(year))
    data,meta=capture(f'roster-{year}-{team}-{kind}.json',f'{BASE}/teams/{team}/roster',dict(rosterType=kind,season=year,date=cutoff))
    assert isinstance(data.get('roster'),list)
    return data,meta


def probe():
    assert not (OUT/'probe.json').exists(),'Inspect completed probe, do not rerun it'
    requests_=[(137,2023),(137,2024),(137,2025),(158,2025),(108,2018),(108,2024)]
    artifacts={};payloads={}
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures={pool.submit(roster,t,y,k):(t,y,k) for t,y in requests_ for k in ['40Man','fullRoster']}
        for future in as_completed(futures):
            key=futures[future];data,meta=future.result();payloads[key]=data;artifacts[str(key)]=meta
            print('Probe',key,len(data['roster']),'source rows',flush=True)
    controls=[('Conforto',624424,137,2023,True),('Pollock',572041,137,2023,False),
              ('Canha',592192,137,2024,False),('Devers',646240,137,2025,False),
              ('Ohtani',660271,108,2018,True)]
    checks=[]
    for name,pid,t,y,expected in controls:
        for k in ['40Man','fullRoster']:
            rows=[r for r in payloads[t,y,k]['roster'] if r.get('person',{}).get('id')==pid]
            checks.append(dict(name=name,player_id=pid,team_id=t,season=y,roster_type=k,expected_presence=expected,present=bool(rows),passes=bool(rows)==expected,raw_rows=rows))
    for name,pid,t,y in [('Alfaro',595751,158,2025),('Sano',593934,108,2024)]:
        for k in ['40Man','fullRoster']:
            rows=[r for r in payloads[t,y,k]['roster'] if r.get('person',{}).get('id')==pid]
            checks.append(dict(name=name,player_id=pid,team_id=t,season=y,roster_type=k,expected_presence=None,present=bool(rows),passes=None,raw_rows=rows,
                               limit='Minor agreement does not imply 40-man membership; recorded effective timing differs from agreement timing.'))
    allowed=[k for k in ['40Man','fullRoster'] if all(c['passes'] for c in checks if c['roster_type']==k and c['passes'] is not None)]
    write(OUT/'probe.json',dict(checks=checks,source_captures=artifacts,allowed_for_further_capture=allowed,
        endpoint_membership_approved=False,full_roster_ownership_approved=False,source_review_status='pending',new_fits=0,
        contract_sha256=sha256_file(ROOT/'docs/hitter-preseason-population-source-contract.md'),code_sha256=sha256_file(Path(__file__))))
    print('Temporal controls permit further collection:',allowed,flush=True)


def collect():
    probe=read(OUT/'probe.json');assert sha256_file(Path(__file__))==probe['code_sha256']
    assert probe['contract_sha256']==sha256_file(ROOT/'docs/hitter-preseason-population-source-contract.md')
    assert '40Man' in probe['allowed_for_further_capture'],'Temporal source failure requires review first'
    allmeta=[]
    for y in range(2012,2026):
        cutoff=read(CONFIG)[str(y)]['date']
        teams,meta=capture(f'teams-{y}.json',BASE+'/teams',dict(sportId=1,season=y));allmeta.append(meta)
        ids=sorted({t['id'] for t in teams['teams']});assert len(ids)==30
        # fullRoster is collected only if its date controls survived; still not ownership.
        kinds=probe['allowed_for_further_capture']
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures={pool.submit(roster,t,y,k):(t,k) for t in ids for k in kinds}
            for future in as_completed(futures):
                data,meta=future.result();allmeta.append(meta)
        tx,meta=capture(f'transactions-{y}.json',BASE+'/transactions',dict(startDate=f'{y-1}-10-01',endDate=cutoff));allmeta.append(meta)
        assert isinstance(tx.get('transactions'),list)
        # Explicitly preserve advertised counts; final source review must resolve pagination.
        print('Captured',y,'cutoff',cutoff,'teams',len(ids),'roster kinds',kinds,'transactions',len(tx['transactions']),
              'advertised totals',{k:v for k,v in tx.items() if k not in ['copyright','transactions']},flush=True)
    write(OUT/'capture-report.json',dict(captures=allmeta,completed_years=list(range(2012,2026)),source_review_status='pending',
        retrospective_provider=True,population_materialized=False,new_fits=0,protected_2026_opened=False,
        contract_sha256=probe['contract_sha256'],code_sha256=probe['code_sha256'],date_config_sha256=sha256_file(CONFIG)))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['probe','collect']);args=parser.parse_args()
    (probe if args.mode=='probe' else collect)()
