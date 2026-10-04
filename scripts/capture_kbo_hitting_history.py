"""Resume only sealed years; collect remaining KBO years through live forms."""
from datetime import datetime,timezone
import json
from pathlib import Path
import re

import polars as pl
import requests

import probe_kbo_hitting_source as probe
import qualify_kbo_hitting_source as qualify
from universal_baseball.kbo_history import join_groups,FIELDS1,FIELDS2
from universal_baseball.storage import sha256_file

ROOT=probe.ROOT
OUT=ROOT/'reports/generated/kbo-hitting-history'
CONTRACT=ROOT/'docs/hitter-kbo-history-collection-contract.md'


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def team_rows(session,year,number,attempt):
    url=probe.BASE+f'/Record/Team/Hitter/Basic{number}.aspx'
    stem=f'bulk-{attempt}-{year}-teams-group{number}'
    initial,meta=probe.request(session,stem+'-initial',url)
    _,values=qualify.state(initial,url)
    key=probe.control(values,'$ddlSeason$ddlSeason')
    soup,second=qualify.post(session,initial,url,stem+'-year',key,{key:str(year)})
    _,values=qualify.state(soup,url)
    assert values[key]==str(year) and values[probe.control(values,'$ddlSeries$ddlSeries')]=='0'
    tables=soup.select('table.tData'); assert len(tables)==1
    headers=[x.get_text(strip=True) for x in tables[0].select('thead th')]
    rows=[]
    for tr in tables[0].select('tbody tr'):
        cells=[x.get_text(strip=True) for x in tr.find_all('td',recursive=False)]
        assert len(cells)==len(headers)
        rows.append(dict(zip(headers,cells,strict=True)))
    expected=8 if year<=2012 else 9 if year<=2014 else 10
    assert len(rows)==expected and len({r['팀명'] for r in rows})==expected
    return rows,[meta,second]


def main():
    assert not (OUT/'collection.json').exists(), 'Do not overwrite completed collection'
    qout=qualify.OUT
    reviewed=read(qout/'review.json'); q=read(qout/'qualification.json')
    assert reviewed['player_walkthrough_status']=='complete_for_source'
    for name,expected in reviewed['hashes'].items():
        assert sha256_file(ROOT/name)==expected,('Qualification changed',name)
    source_files=[CONTRACT,Path(__file__),Path(qualify.__file__),Path(probe.__file__),
                  ROOT/'src/universal_baseball/kbo_history.py']
    seals={str(p.relative_to(ROOT)):sha256_file(p) for p in source_files}
    original=pl.read_parquet(qout/'qualified-seasons.parquet')
    checks,frames=[],[]
    OUT.mkdir(parents=True,exist_ok=True)
    for year in range(2005,2025):
        yearly=OUT/f'{year}.parquet'; receipt=OUT/f'{year}.json'
        if receipt.exists():
            previous=read(receipt)
            assert previous['source_code_hashes']==seals
            assert previous['data_sha256']==sha256_file(yearly)
            frame=pl.read_parquet(yearly)
            assert frame.height==previous['check']['rows']
            assert frame['season'].unique().to_list()==[year]
            print('Verified cached year',year,frame.height,flush=True)
        else:
            assert not yearly.exists(), 'Unreceipted year artifact; investigate before resume'
            if year in q['seasons']:
                frame=original.filter(pl.col('season')==year).sort('kbo_id')
                check=next(c for c in q['checks'] if c['season']==year)
                previous=dict(check=check,captures=[],reused_qualified_season=True,
                              qualification_sha256=sha256_file(qout/'qualification.json'),
                              qualification_review_sha256=sha256_file(qout/'review.json'),
                              raw_capture_attempt=q['attempt'])
            else:
                session=requests.Session()
                session.headers['User-Agent']='UBM historical research; low-rate published public form collection'
                attempt='bulk-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
                receipts=[]
                first,meta,c1=qualify.group(session,year,1,attempt); receipts.extend(meta)
                second,meta,c2=qualify.group(session,year,2,attempt); receipts.extend(meta)
                rows=join_groups(first,second,year)
                t1,meta=team_rows(session,year,1,attempt); receipts.extend(meta)
                t2,meta=team_rows(session,year,2,attempt); receipts.extend(meta)
                assert {r['팀명'] for r in t1}=={r['팀명'] for r in t2}
                headers={**dict(zip(FIELDS1,['G','PA','AB','R','H','2B','3B','HR','TB','RBI','SAC','SF'])),
                         **dict(zip(FIELDS2,['BB','IBB','HBP','SO','GDP']))}
                for field,header in headers.items():
                    if field=='games':
                        continue
                    teams=t1 if field in FIELDS1 else t2
                    assert all(re.fullmatch(r'\d+',t[header]) for t in teams)
                    expected=sum(int(t[header]) for t in teams)
                    assert expected==sum(r[field] for r in rows),('Totals mismatch',year,field)
                check=dict(season=year,groups=[c1,c2],rows=len(rows),pa=sum(r['pa'] for r in rows),
                           zero_pa=sum(r['pa']==0 for r in rows),small_pa=sum(0<r['pa']<=10 for r in rows),
                           unenumerated_pa=sum(r['unenumerated_pa'] for r in rows),
                           team_count_fields_reconciled=16,team_count=len(t1),
                           all_displayed_players_preserved=True)
                frame=pl.DataFrame(rows).sort('kbo_id')
                previous=dict(check=check,captures=receipts,reused_qualified_season=False,
                              raw_capture_attempt=attempt)
            frame.write_parquet(yearly)
            previous.update(data_sha256=sha256_file(yearly),source_code_hashes=seals)
            probe.write_new(receipt,previous)
            print('Sealed complete year',previous['check'],flush=True)
        frames.append(frame)
        checks.append(previous['check'])
    data=pl.concat(frames,how='vertical').sort('season','kbo_id')
    assert data.select('season','kbo_id').unique().height==data.height
    assert data['season'].unique().sort().to_list()==list(range(2005,2025))
    path=OUT/'first-team-batting.parquet'
    assert not path.exists(); data.write_parquet(path)
    probe.write_new(OUT/'collection.json',dict(seasons=list(range(2005,2025)),checks=checks,
        rows=data.height,pa=int(data['pa'].sum()),data_sha256=sha256_file(path),source_code_hashes=seals,
        per_year_receipt_hashes={str(y):sha256_file(OUT/f'{y}.json') for y in range(2005,2025)},
        source_walkthrough_status='five_year_probe_complete_full_collection_review_pending',
        full_collection_independently_reviewed=False,all_league_MLBAM_crosswalk_qualified=False,
        new_fits=0,forecasts_changed=False,protected_2026_opened=False))
    print('Collected all twenty seasons',data.height,'rows',flush=True)


if __name__=='__main__':
    main()
