"""Independent raw counts, exact IDs and source-only player walks."""
from pathlib import Path
from datetime import date
import json
import re
import sys

from bs4 import BeautifulSoup
import polars as pl
import requests

import capture_international_hitter_2025 as c
import review_kbo_hitting_source as kr
import review_kbo_hitting_history as kt
from universal_baseball.npb_history import COUNTS
from universal_baseball.kbo_history import FIELDS1,FIELDS2
from universal_baseball.international_hitter_source_2025 import recent_counts
from universal_baseball.kbo_identity import register_index,profile_identity,match_identity
from universal_baseball.storage import sha256_file

ROOT,OUT,RAW=c.ROOT,c.OUT,c.RAW
FIXED=[('NPB',808959),('NPB',672960),('NPB',592122),('KBO',823550),('KBO',621550)]


def read(p):return json.loads(p.read_text(encoding='utf8'))


def frames():
    return {'NPB':pl.read_parquet(OUT/'npb-2025.parquet'),
            'KBO':pl.read_parquet(OUT/'kbo-2025-identities.parquet')}


def meta_checks(folder,receipts):
    available=[]
    for p in folder.glob('*.json'):
        if p.name.endswith('.request.json'):continue
        meta=read(p)
        if 'url' not in meta:continue
        html=Path(str(p).removesuffix('.metadata.json')) if p.name.endswith('.metadata.json') else p.with_suffix('.html')
        assert sha256_file(html)==meta['sha256']
        assert meta['url']==meta['returned_url']
        available.append(meta)
    assert all(r in available for r in receipts)


def verify():
    assert not (OUT/'independent-review.json').exists()
    reports={n:read(OUT/n) for n in ['npb-collection.json','kbo-collection.json','kbo-identity-collection.json']}
    for r in reports.values():
        for p,h in r['source_hashes'].items():assert sha256_file(Path(p))==h,p
    fs=frames();npb=fs['NPB'];kbo=fs['KBO'];checks=0
    assert sha256_file(OUT/'npb-2025.parquet')==reports['npb-collection.json']['data_sha256']
    assert sha256_file(OUT/'kbo-2025.parquet')==reports['kbo-collection.json']['data_sha256']
    assert sha256_file(OUT/'kbo-2025-identities.parquet')==reports['kbo-identity-collection.json']['data_sha256']
    for (slug,),part in npb.partition_by('table_slug',as_dict=True).items():
        path=RAW/'npb'/(slug+'.html');soup=BeautifulSoup(path.read_bytes(),'html.parser')
        raw={}
        for tr in soup.select('table.tablefix2 tr'):
            td=tr.find_all('td',recursive=False)
            if not td:continue
            assert len(td)==23
            for node in td[0].find_all('sup'):node.extract()
            key=re.sub(r'\s+','',td[0].get_text())
            assert key not in raw
            raw[key]=[int(x.get_text()) for x in td[1:20]]
        assert set(raw)==set(part['name_key'])
        for r in part.iter_rows(named=True):
            assert raw[r['name_key']]==[r[k] for k in COUNTS]
            checks+=len(COUNTS)
    meta_checks(RAW/'npb',reports['npb-collection.json']['captures'])
    groups=[]
    for g in reports['kbo-collection.json']['groups']:
        first=list((RAW/'kbo').glob(f"qualification-*-2025-group{g['group']}-count-first.html"))
        assert len(first)==1
        stem=first[0].name.removesuffix('-count-first.html');rows={}
        for page in range(1,g['last_page']+1):
            p=first[0] if page==1 else RAW/'kbo'/f'{stem}-page{page}.html'
            new=kr.raw_page(p,g['group']);assert not set(new)&set(rows);rows.update(new)
        assert len(rows)==g['rows'];groups.append(rows)
    assert set(groups[0])==set(groups[1])==set(kbo['kbo_id'])
    for r in kbo.iter_rows(named=True):
        expected={**groups[0][r['kbo_id']],**groups[1][r['kbo_id']]}
        assert all(r[k]==v for k,v in expected.items());checks+=17
    teamfiles=[next((RAW/'kbo').glob(f'bulk-*-2025-teams-group{g}-year.html')) for g in [1,2]]
    teams=[kt.team_counts(p) for p in teamfiles];assert len(teams[0])==len(teams[1])==10
    headers={**dict(zip(FIELDS1,['G','PA','AB','R','H','2B','3B','HR','TB','RBI','SAC','SF'])),
             **dict(zip(FIELDS2,['BB','IBB','HBP','SO','GDP']))}
    for field,header in headers.items():
        if field=='games':continue
        assert kbo[field].sum()==sum(int(t[header]) for t in teams[0 if field in FIELDS1 else 1])
    meta_checks(RAW/'kbo',reports['kbo-collection.json']['captures'])
    meta_checks(RAW/'kbo-identities',reports['kbo-identity-collection.json']['captures'])
    index=register_index(c.REGISTER)
    for r in reports['kbo-identity-collection.json']['new_identities']:
        raw=RAW/'kbo-identities'/('2025-identity-'+r['kbo_id']+'.html')
        assert match_identity(profile_identity(raw.read_bytes(),r['kbo_id']),index)==r
    old=pl.read_parquet(ROOT/'reports/generated/kbo-identity-overlay/identities.parquet')
    new_keys={r['kbo_id'] for r in reports['kbo-identity-collection.json']['new_identities']}
    for r in kbo.filter(~pl.col('kbo_id').is_in(list(new_keys))).iter_rows(named=True):
        before=old.filter(pl.col('kbo_id')==r['kbo_id'])
        if len(before):
            assert before['player_id'][0]==r['player_id'] and before['birth_date'][0]==r['birth_date']
        else:assert r['player_id'] is None and r['identity_match_status']=='uncollected'
    c.save('independent-review.json',dict(raw_count_fields_reconstructed=checks,npb_rows=len(npb),kbo_rows=len(kbo),
        kbo_team_count_fields_reconciled=16,new_static_identities_replayed=len(new_keys),
        sources_reconciled=True,source_player_walkthrough_status='pending',
        new_fits=0,forecast_changes=0,code_sha256=sha256_file(Path(__file__)),
        hashes={str(p):sha256_file(p) for p in [OUT/'npb-collection.json',OUT/'kbo-collection.json',
            OUT/'kbo-identity-collection.json',OUT/'npb-2025.parquet',OUT/'kbo-2025-identities.parquet',
            Path(kr.__file__),Path(kt.__file__),Path(__file__)]}))


def walks():
    assert not (OUT/'player-walks.json').exists()
    review=read(OUT/'independent-review.json')
    for p,h in review['hashes'].items():assert sha256_file(Path(p))==h
    fs=frames();hist={'NPB':pl.read_parquet(ROOT/'reports/generated/npb-hitting-history/reviewed-batting.parquet'),
                     'KBO':pl.read_parquet(ROOT/'reports/generated/kbo-identity-overlay/reviewed-batting.parquet')}
    allrows={league:hist[league].to_dicts()+fs[league].to_dicts() for league in fs}
    selected=[]
    for league,pid in FIXED:
        g=fs[league].filter(pl.col('player_id')==pid);assert len(g)==1,(league,pid)
        selected.append((league,g.row(0,named=True),'fixed coverage case'))
    for league,f in fs.items():
        key='npb_id' if league=='NPB' else 'kbo_id'
        ordinary=f.filter((pl.col('pa')>0)&pl.col('player_id').is_null()).sort(key,nulls_last=True).head(1)
        assert len(ordinary);selected.append((league,ordinary.row(0,named=True),'lowest source ID positive PA without MLBAM'))
    zero=fs['NPB'].filter(pl.col('pa')==0).sort('npb_id',nulls_last=True).head(1)
    selected.append(('NPB',zero.row(0,named=True),'lowest source ID zero PA control'))
    c.save('walk-selection.json',dict(cases=[dict(league=l,source_id=r['npb_id' if l=='NPB' else 'kbo_id'],
        player_id=r['player_id'],rule=rule) for l,r,rule in selected],future_outcomes_used=False))
    cases=[];c.npb.RAW=RAW/'npb-english';c.probe.RAW=RAW/'kbo-english'
    session=requests.Session()
    for league,r,rule in selected:
        key='npb_id' if league=='NPB' else 'kbo_id';sid=r[key]
        assert sid is not None
        # Unmapped sources are selected by their real source key, never pooled
        # together because all happen to have player_id=None.
        source=[x for x in allrows[league] if x[key]==sid and 2023<=x['season']<=2025]
        annual=sorted(source,key=lambda x:(x['season'],x.get('table_slug','')))
        labeled=[dict(x,player_id=-1) for x in source] # Internal source-only selector, not an MLB ID.
        before=recent_counts(labeled,-1,2024);after=recent_counts(labeled,-1,2025)
        after['player_id']=r['player_id'];before['player_id']=r['player_id']
        altered=labeled+[dict(labeled[-1],season=2026,pa=999999,hr=999999)]
        probe=recent_counts(altered,-1,2025);probe['player_id']=r['player_id'];assert probe==after
        english=[]
        if r['pa']>0 and league=='NPB':
            url=r['source_url'].replace('/bis/','/bis/eng/',1)
            body,meta=c.npb.capture(r['table_slug']+'.html',url)
            soup=BeautifulSoup(body,'html.parser');assert '2025' in soup.title.get_text() and 'Individual Batting' in soup.title.get_text()
            matches=[]
            for tr in soup.find_all('tr'):
                td=tr.find_all('td',recursive=False)
                if len(td) not in [23,24]:continue
                start=1 if len(td)==23 else 2
                if all(re.fullmatch(r'\d+',x.get_text(strip=True)) for x in td[start:start+19]):
                    if [int(x.get_text()) for x in td[start:start+19]]==[r[k] for k in COUNTS]:matches.append(td[start-1].get_text(' ',strip=True))
            assert len(matches)==1
            english=[dict(count_fields=19,english_name=matches[0],meta=meta,same_provider_rendering=True)]
        elif r['pa']>0 and league=='KBO':
            # Only source counts/static identity; kr's optional MLB request is disabled.
            kr.probe.RAW=c.probe.RAW
            e=kr.english_case(session,r,None)
            english=[e]
        age=(date(2025,12,31)-date.fromisoformat(r['birth_date'])).days/365.2425 if r.get('birth_date') else None
        peers=fs[league].filter(pl.col(key)!=sid).to_dicts()
        def distance(p):
            base=abs(p['pa']-r['pa'])/300
            if r.get('birth_date') and p.get('birth_date'):
                a=(date(2025,12,31)-date.fromisoformat(p['birth_date'])).days/365.2425
                base+=abs(a-age)/5
            elif r.get('birth_date'):base+=2
            return base
        peers=sorted(peers,key=lambda p:(distance(p),p[key] or ''))[:3]
        cases.append(dict(league=league,source_id=sid,rule=rule,player_id=r['player_id'],
            age_at_origin=age,source_2025=r,annual_counts=[{k:x[k] for k in ['season',*COUNTS] if k in x} for x in annual],
            before_last_season=before,with_last_season=after,english_count_checks=english,
            peers=[dict(source_id=p[key],player_id=p['player_id'],pa=p['pa'],hr=p['hr'],so=p['so'],bb=p['bb'],
                        distance=distance(p)) for p in peers],
            future_mutation_invariance=True,new_projection=None,
            scope='Raw overseas evidence only; not park adjusted, MLB translated or employment qualified'))
        print('Source walk',league,sid,r['player_id'],r['pa'],flush=True)
    c.save('player-walks.json',dict(cases=cases,source_player_walkthrough_status='mechanical_complete_readable_review_pending',
        fixed_cases=5,ordinary_controls=3,new_fits=0,forecast_changes=0,protected_final_2026_forecasts_changed=False))


if __name__=='__main__':{'verify':verify,'walk':walks}[sys.argv[1]]()
