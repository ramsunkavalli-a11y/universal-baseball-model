"""Separate 2025 collections using the sealed historical source helpers."""
import json
from pathlib import Path
import re
import sys
from datetime import datetime,timezone
from urllib.parse import urljoin

import polars as pl
import requests

import capture_npb_hitting_history as npb
import probe_kbo_hitting_source as probe
import qualify_kbo_hitting_source as qualify
import capture_kbo_hitting_history as kbo
from universal_baseball.chadwick import CHADWICK_SNAPSHOT_SHA
from universal_baseball.npb_history import batting_rows,roster_links,roster_names,attach_npb_ids,name_key,read_npb_crosswalk
from universal_baseball.npb_identity_overlay import reviewed_id
from universal_baseball.kbo_history import join_groups,FIELDS1,FIELDS2
from universal_baseball.kbo_identity import register_index,profile_identity,match_identity
from universal_baseball.international_hitter_source_2025 import npb_2025_links
from universal_baseball.storage import sha256_file

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/generated/international-hitter-source-2025'
RAW=ROOT/'data/quarantine/international-hitter-source-2025'
CONTRACT=ROOT/'docs/hitter-international-source-2025-contract.md'
REGISTER=ROOT/f'data/quarantine/npb-hitting-history/chadwick-{CHADWICK_SNAPSHOT_SHA}.zip'


def read(p):return json.loads(p.read_text(encoding='utf8'))


def seal_paths():
    paths=[CONTRACT,Path(__file__),REGISTER,Path(npb.__file__),Path(probe.__file__),
        Path(qualify.__file__),Path(kbo.__file__),
        *[ROOT/f'src/universal_baseball/{n}.py' for n in ['npb_history','npb_identity_overlay',
            'kbo_history','kbo_identity','international_hitter_source_2025']],
        ROOT/'reports/generated/npb-hitting-history/review.json',
        ROOT/'reports/generated/kbo-hitting-history/review.json',
        ROOT/'reports/generated/kbo-identity-overlay/identities.parquet']
    return {str(p):sha256_file(p) for p in paths}


def save(name,o):
    p=OUT/name;assert not p.exists(),f'Preserve completed {p}'
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(o,indent=2,ensure_ascii=False,allow_nan=False,default=str)+'\n',encoding='utf8',newline='\n')


def npb_capture():
    assert not (OUT/'npb-collection.json').exists()
    hashes=seal_paths();npb.RAW=RAW/'npb' # Local process only; original files untouched.
    index,meta=npb.capture('2025-season-index.html','https://npb.jp/bis/2025/stats/')
    ids,identity_meta=npb.capture('all-player-index.html','https://npb.jp/bis/players/all/index.html')
    links=npb_2025_links(index);listings=roster_links(ids,2025)
    rows=[];receipts=[meta,identity_meta];crosswalk=read_npb_crosswalk(REGISTER)
    for link in links:
        slug=link.rsplit('/',1)[-1].removesuffix('.html')
        body,meta=npb.capture(slug+'.html',urljoin('https://npb.jp',link))
        team,records=batting_rows(body,2025)
        identity_url=urljoin('https://npb.jp',listings[name_key(team)])
        identity,identity_meta=npb.capture(slug+'-identities.html',identity_url)
        listing=roster_names(identity,2025,team)
        for r in attach_npb_ids(records,listing):
            key,status=reviewed_id(r,listing);person=crosswalk.get(key,{})
            rows.append(dict(r,npb_id=key,npb_identity_status=status,
                player_id=person.get('player_id'),birth_date=person.get('birth_date'),
                chadwick_uuid=person.get('key_uuid'),table_slug=slug,
                source_url=meta['url'],source_sha256=meta['sha256'],
                identity_url=identity_meta['url'],identity_sha256=identity_meta['sha256']))
        receipts.extend([meta,identity_meta]);print('NPB 2025 captured',slug,len(records),flush=True)
    f=pl.DataFrame(rows,schema_overrides={'player_id':pl.Int64}).sort('table_slug','name_key')
    assert f.unique(['table_slug','name_key']).height==f.height and f['team_name'].n_unique()==12
    p=OUT/'npb-2025.parquet';assert not p.exists();f.write_parquet(p)
    assert all(sha256_file(Path(p))==h for p,h in hashes.items())
    save('npb-collection.json',dict(rows=len(f),pa=int(f['pa'].sum()),zero_pa=int((f['pa']==0).sum()),
        teams=12,unmatched_npb_rows=int(f['npb_id'].is_null().sum()),
        unmatched_mlb_rows=int(f['player_id'].is_null().sum()),residual_pa=int(f['unenumerated_pa'].sum()),
        source_hashes=hashes,captures=receipts,data_sha256=sha256_file(p),
        player_walkthrough_status='pending',source_review_status='pending',new_fits=0,forecast_changes=0))


def kbo_capture():
    assert not (OUT/'kbo-collection.json').exists()
    hashes=seal_paths();probe.RAW=RAW/'kbo' # New raw namespace; historical captures unchanged.
    attempt=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    session=requests.Session();session.headers['User-Agent']='UBM low-rate completed-season source research'
    a,ra,ca=qualify.group(session,2025,1,attempt)
    b,rb,cb=qualify.group(session,2025,2,attempt)
    rows=join_groups(a,b,2025);t1,r1=kbo.team_rows(session,2025,1,attempt);t2,r2=kbo.team_rows(session,2025,2,attempt)
    assert {r['팀명'] for r in t1}=={r['팀명'] for r in t2}
    headers={**dict(zip(FIELDS1,['G','PA','AB','R','H','2B','3B','HR','TB','RBI','SAC','SF'])),
             **dict(zip(FIELDS2,['BB','IBB','HBP','SO','GDP']))}
    for field,header in headers.items():
        if field=='games':continue
        teams=t1 if field in FIELDS1 else t2
        assert all(re.fullmatch(r'\d+',t[header]) for t in teams)
        assert sum(int(t[header]) for t in teams)==sum(r[field] for r in rows),(field,header)
    f=pl.DataFrame(rows).sort('kbo_id')
    p=OUT/'kbo-2025.parquet';assert not p.exists();f.write_parquet(p)
    save('kbo-collection.json',dict(rows=len(f),pa=int(f['pa'].sum()),zero_pa=int((f['pa']==0).sum()),
        teams=10,team_fields_reconciled=16,residual_pa=int(f['unenumerated_pa'].sum()),
        source_hashes=hashes,captures=ra+rb+r1+r2,groups=[ca,cb],team_tables=[t1,t2],
        data_sha256=sha256_file(p),player_walkthrough_status='pending',source_review_status='pending',
        new_fits=0,forecast_changes=0))


def kbo_identity():
    assert not (OUT/'kbo-identity-collection.json').exists()
    hashes=seal_paths();probe.RAW=RAW/'kbo-identities'
    source=pl.read_parquet(OUT/'kbo-2025.parquet')
    old=pl.read_parquet(ROOT/'reports/generated/kbo-identity-overlay/identities.parquet')
    lookup={r['kbo_id']:r for r in old.iter_rows(named=True)}
    index=register_index(REGISTER);session=requests.Session();new=[];receipts=[]
    keys=source.filter(pl.col('pa')>=100)['kbo_id'].sort().to_list()
    for key in keys:
        if key in lookup:continue
        url='https://eng.koreabaseball.com/Teams/PlayerInfoHitter/Summary.aspx?pcode='+key
        _,meta=probe.request(session,'2025-identity-'+key,url)
        raw=probe.RAW/('2025-identity-'+key+'.html')
        result=match_identity(profile_identity(raw.read_bytes(),key),index)
        lookup[key]=result;new.append(result);receipts.append(meta)
        print('New KBO static identity',key,result['match_status'],flush=True)
    rows=[]
    for r in source.iter_rows(named=True):
        identity=lookup.get(r['kbo_id'],{})
        rows.append(dict(r,player_id=identity.get('player_id'),birth_date=identity.get('birth_date'),
            english_name=identity.get('english_name'),identity_match_status=identity.get('match_status','uncollected'),
            current_role_salary_status_used=False))
    f=pl.DataFrame(rows,schema_overrides={'player_id':pl.Int64}).sort('kbo_id')
    assert len(f)==len(source) and f.select(source.columns).equals(source)
    p=OUT/'kbo-2025-identities.parquet';assert not p.exists();f.write_parquet(p)
    assert all(sha256_file(Path(p))==h for p,h in hashes.items())
    save('kbo-identity-collection.json',dict(source_rows=len(source),new_profiles=len(new),new_identities=new,
        captures=receipts,unmatched_mlb_rows=int(f['player_id'].is_null().sum()),
        original_identity_keys_reused=True,source_hashes=hashes,data_sha256=sha256_file(p),
        source_review_status='pending',new_fits=0,forecast_changes=0))


if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    {'npb':npb_capture,'kbo':kbo_capture,'identity':kbo_identity}[sys.argv[1]]()
