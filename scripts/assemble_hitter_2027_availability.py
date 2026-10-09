"""Reuse reversible availability rules on dated player transaction captures."""
from collections import defaultdict
from datetime import date
from pathlib import Path
import gzip
import json
import polars as pl
from universal_baseball import availability_context_v29b as clinical
from universal_baseball.retirement_availability import events,state
from universal_baseball.storage import sha256_file
from assemble_hitter_2027_base import ROOT,OUT,MEM,PUBLIC
from capture_hitter_2027_origin_counts import write_once

ASOF=date(2026,10,9)


def main():
    receipt=PUBLIC/'availability-assembly.json';assert not receipt.exists()
    captures=[];paths=[]
    for path in sorted((MEM/'captures').glob('people-*.json.gz')):
        paths.append(path);tx=[]
        for person in json.loads(gzip.decompress(path.read_bytes()))['people']:
            for raw in person.get('transactions',[]):
                # Hydrated-person transactions omit person; parent ID is authority.
                if raw.get('person'):assert raw['person']['id']==person['id']
                tx.append({**raw,'person':{'id':person['id']}})
        captures.append((2026,path,{'transactions':tx}))
    facts=[]
    for name in ['availability_facts_v29.json','availability_facts_v29b.json']:
        path=ROOT/'config'/name;paths.append(path);facts.extend(json.loads(path.read_text())['events'])
    teams={r['id'] for r in json.loads(gzip.decompress((MEM/'captures/teams.json.gz').read_bytes()))['teams']}
    normalized,audit=clinical.normalize([(y,p) for y,_,p in captures],teams,facts,maximum=ASOF)
    retirements=events(captures,ASOF);by=defaultdict(list);ret=defaultdict(list)
    for r in normalized:by[r['player_id']].append(r)
    for r in retirements:ret[r['player_id']].append(r)
    pop=pl.read_parquet(OUT/'assembled.parquet');rows=[];walks=[]
    for o in pop.iter_rows(named=True):
        pid=o['player_id'];h=clinical.ledger(by[pid],ASOF);r=state(ret[pid],ASOF)
        rows.append(dict(row_id=o['row_id'],player_id=pid,reported_retired=r['reported_retired'],hard_unavailable=h['hard_unavailable'],
            hard_reason=h['hard_reason'],availability_state=h['availability_state'],nonmedical_reason=h['nonmedical_reason'],
            finite_ineligibility_end=h['finite_ineligibility_end'],latest_context_date=h['latest_context_date'],
            status_observed=bool(by[pid] or ret[pid]),medical_recovery_certified=False))
        if r['reported_retired'] or h['hard_unavailable'] or h['nonmedical_reason'] or pid in [804944,805811,808393,592450,665487,660271,672275,596019]:
            walks.append(dict(player_id=pid,name=o['player_name'],state=rows[-1],retirement=r,
                last_context=sorted(by[pid],key=lambda x:(x['event_date'],x['available_date']))[-8:],
                interpretation='Retirement or permanent ineligibility changes participation, not talent; October injury-list status alone never forces zero for all of 2027. Unresolved restrictions remain review cases.'))
    status=pl.DataFrame(rows,schema_overrides={'hard_reason':pl.String,'nonmedical_reason':pl.String,
        'finite_ineligibility_end':pl.Date,'latest_context_date':pl.Date})
    focal=status.filter(pl.col('player_id').is_in([592450,665487,660271,805811]))
    assert not focal['hard_unavailable'].any() and not focal['reported_retired'].any()
    assert status['row_id'].n_unique()==len(pop)
    path=OUT/'availability.parquet';assert not path.exists();status.write_parquet(path)
    walkpath=PUBLIC/'availability-player-walks.json.gz';assert not walkpath.exists()
    walkpath.write_bytes(gzip.compress(json.dumps(walks,default=str,allow_nan=False).encode(),mtime=0))
    write_once(receipt,dict(as_of=str(ASOF),population=len(pop),reported_retired=int(status['reported_retired'].sum()),
        hard_unavailable=int(status['hard_unavailable'].sum()),unresolved_nonmedical=int(status['nonmedical_reason'].is_not_null().sum()),
        normalization_audit=audit,source_walkthrough='complete',retirement_override_reversible=True,
        injury_season_out_not_carried_to_2027=True,known_medical_recovery_certified=False,
        limitation='Not a new injury recovery model; observed injuries and unresolved restrictions require distinct interpretation from definitive hard exclusions.',
        output_hashes={str(path):sha256_file(path),str(walkpath):sha256_file(walkpath)},
        input_hashes={str(p):sha256_file(p) for p in paths},runner_sha256=sha256_file(Path(__file__))))
    print(status.group_by('reported_retired','hard_unavailable').len().to_dicts(),flush=True)


if __name__=='__main__':main()
