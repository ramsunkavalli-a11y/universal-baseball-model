"""Dated roster, biography and rights evidence; not inferred current ownership."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date,datetime,timezone
from pathlib import Path
import gzip
import hashlib
import json
import shutil
import polars as pl
import requests
from universal_baseball.playing_time_roster_source import project_team_40man_membership_payload
from universal_baseball.people_control_source import project_people_control_payload
from universal_baseball.storage import sha256_file
from capture_hitter_2027_origin_counts import ROOT,write_once

ASOF=date(2026,10,9)
OUT=ROOT/'reports/generated/hitter-2027-membership-source'
PUBLIC=ROOT/'reports/model-evidence/hitter-2027-v1'


def capture(name,endpoint,params):
    path=OUT/'captures'/f'{name}.json.gz';receipt=path.with_suffix('.receipt.json')
    if receipt.exists():
        info=json.loads(receipt.read_text(encoding='utf8'))
        assert info['endpoint']==endpoint and info['params']==params and info['as_of']==str(ASOF)
        assert sha256_file(path)==info['compressed_sha256']
        raw=gzip.decompress(path.read_bytes());assert hashlib.sha256(raw).hexdigest()==info['response_sha256']
    else:
        assert not path.exists(),'Unreceipted capture must not be overwritten'
        response=requests.get('https://statsapi.mlb.com/api/v1'+endpoint,params=params,timeout=(15,60))
        response.raise_for_status();raw=response.content;payload=json.loads(raw)
        assert isinstance(payload,dict)
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(gzip.compress(raw,mtime=0))
        write_once(receipt,dict(endpoint=endpoint,params=params,as_of=str(ASOF),url=response.url,
            captured_utc=datetime.now(timezone.utc).isoformat(),response_sha256=hashlib.sha256(raw).hexdigest(),compressed_sha256=sha256_file(path)))
    return json.loads(raw)


def roster(task):
    tid,kind=task
    payload=capture(f'roster-{tid}-{kind}',f'/teams/{tid}/roster',dict(rosterType=kind,season=2026,date=str(ASOF)))
    assert isinstance(payload.get('roster'),list)
    return tid,kind,payload


def people(batch):
    key=hashlib.sha256(','.join(map(str,batch)).encode()).hexdigest()[:16]
    payload=capture('people-'+key,'/people',dict(personIds=','.join(map(str,batch)),hydrate='currentTeam,rosterEntries,transactions,draft'))
    returned=[r['id'] for r in payload['people']]
    assert len(returned)==len(set(returned)) and set(returned)<=set(batch),'Unexpected/duplicate people identity'
    return key,payload,sorted(set(batch)-set(returned))


def save_frame(path,frame):
    if path.exists():
        assert pl.read_parquet(path).equals(frame),'Preserve changed membership table'
    else:frame.write_parquet(path)


def main():
    assert not (PUBLIC/'membership-source-capture.json').exists(),'Preserve completed capture'
    OUT.mkdir(parents=True,exist_ok=True)
    assert shutil.disk_usage(OUT.resolve()).free>500*1024**2,'Keep storage headroom'
    teams=capture('teams','/teams',dict(sportId=1,season=2026))['teams']
    tids=sorted({r['id'] for r in teams});assert len(tids)==30
    rosters=[];candidates=[];roster_names={}
    with ThreadPoolExecutor(max_workers=4) as pool:
        for tid,kind,payload in pool.map(roster,[(t,k) for t in tids for k in ['40Man','fullRoster']]):
            if kind=='40Man':rosters.append(project_team_40man_membership_payload(payload,team_id=tid,season=2026,as_of_date=ASOF))
            for row in payload['roster']:
                pid=int(row['person']['id']);roster_names[pid]=row['person']['fullName']
                candidates.append(dict(player_id=pid,requested_team=tid,roster_type=kind,
                    position_code=str(row.get('position',{}).get('code','')),
                    status_code=row.get('status',{}).get('code'),status_description=row.get('status',{}).get('description')))
        print('All 30 dated 40-man and full-roster queries captured',flush=True)
    forty=pl.concat(rosters).sort('team_id','player_id')
    assert forty['player_id'].n_unique()==len(forty),'Ambiguous current 40-man ownership'
    assert forty.group_by('team_id').len()['len'].is_between(15,65).all()
    candidate=pl.DataFrame(candidates).unique().sort('player_id','requested_team','roster_type')
    f=pl.read_parquet(ROOT/'reports/generated/hitter-2027-origin-counts/team-season-inputs.parquet')
    old=pl.read_parquet(ROOT/'model_artifacts/hitter-selected-2026-frozen-2026-10-05/forecast.parquet',columns=['player_id'])
    ids=sorted(set(f.filter(pl.col('position')!='1')['player_id'])|set(old['player_id'])|
        set(candidate.filter(pl.col('position_code')!='1')['player_id']))
    # Named source discrepancies are captured too, without assuming they belong
    # in the final hitter population or merging names into a different identity.
    required_ids=set(ids)
    ids=sorted(set(ids)|{829096,682643,801736,842661,692369,825101,833193,837758})
    batches=[ids[i:i+40] for i in range(0,len(ids),40)]
    bios=[];controls=[];entries=[];transactions=[];identity_gaps=[]
    with ThreadPoolExecutor(max_workers=3) as pool:
        for i,(key,payload,missing) in enumerate(pool.map(people,batches),1):
            assert not set(missing)&required_ids,'Required population identity absent from people source'
            identity_gaps.extend(dict(player_id=pid,batch=key,status='External-export identity unresolved; no invented biography or name merge') for pid in missing)
            projected=project_people_control_payload(payload,as_of_date=ASOF,source_snapshot_id='2027-origin-people-'+key)
            controls.append(projected.people);entries.append(projected.roster_entries);transactions.append(projected.transactions)
            for r in payload['people']:
                bios.append(dict(player_id=r['id'],player_name=r.get('fullName'),birth_date=r.get('birthDate'),
                    debut_date=r.get('mlbDebutDate'),position_code=r.get('primaryPosition',{}).get('code'),
                    birth_country=r.get('birthCountry'),bat_side=r.get('batSide',{}).get('code'),
                    pitch_hand=r.get('pitchHand',{}).get('code'),height=r.get('height'),weight=r.get('weight'),
                    active=r.get('active'),current_team_id=r.get('currentTeam',{}).get('id'),
                    current_parent_org_id=r.get('currentTeam',{}).get('parentOrgId')))
            if i%20==0 or i==len(batches):print(f'People/rights histories {i}/{len(batches)} batches',flush=True)
    tables=dict(forty_man=forty,roster_candidates=candidate,bios=pl.DataFrame(bios,infer_schema_length=None).sort('player_id'),
        people_control=pl.concat(controls).sort('player_id'),roster_entries=pl.concat(entries,how='vertical_relaxed').sort('player_id','start_date','team_id'),
        transactions=pl.concat(transactions,how='vertical_relaxed').unique().sort('player_id','effective_date','transaction_id'))
    outputs={}
    for name,frame in tables.items():
        path=OUT/f'{name.replace("_","-")}.parquet';save_frame(path,frame);outputs[str(path)]=sha256_file(path)
    write_once(PUBLIC/'membership-source-capture.json',dict(as_of=str(ASOF),season=2026,first_projection_year=2027,
        people=len(bios),tables={k:len(v) for k,v in tables.items()},current_roster_teams=30,
        external_identity_gaps=identity_gaps,
        population_reconciled=False,current_rights_certified=False,service_days_certified=False,
        qualification='Current-team metadata and fullRoster are candidate evidence, not final ownership. Reconcile dated entries, releases, transactions, service and contract obligations before financial output.',
        compact_source_bytes=sum(p.stat().st_size for p in (OUT/'captures').glob('*.gz')),
        output_hashes=outputs,runner_sha256=sha256_file(Path(__file__))))
    print(f'Membership/rights sources captured for {len(bios)} identities; ownership reconciliation remains.',flush=True)


if __name__=='__main__':main()
