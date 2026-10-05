"""Resume terminal source serialization failure with original decisions intact."""
from collections import Counter
from datetime import date
import json
from pathlib import Path

from prepare_hitter_status_evidence import ROOT, OUT, FIXED, sources, read, save, verify, reconcile
from universal_baseball.availability_context_v29 import as_of
from universal_baseball.storage import sha256_file


def iso(value):
    if isinstance(value, date):return value.isoformat()
    raise TypeError(type(value).__name__)


def save_wire(path, value):
    save(path, json.loads(json.dumps(value, default=iso, ensure_ascii=False, allow_nan=False)))


def main():
    assert (OUT/'source-seal.json').exists() and not (OUT/'status-ledger.json').exists()
    seal=read(OUT/'source-seal.json');verify(seal['source_hashes'])
    paths=[Path(__file__),ROOT/'docs/hitter-status-serialization-amendment.md',OUT/'source-seal.json']
    assert not (OUT/'recovery-seal.json').exists(),'Inspect an actual terminal recovery before another attempt'
    save(OUT/'recovery-seal.json',dict(original_sources_verified=True, original_failure='date serialization',
        rules_and_population_unchanged=True,new_fits=0,
        hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in paths}))
    population,raw,records,teams,reports,_,audit=sources();rows=[]
    for i,p in enumerate(population):
        pid=p['player_id'];rows.append(reconcile(p,raw[pid],records[pid],teams,reports[pid]))
        if (i+1)%15000==0:print(json.dumps(dict(rows=i+1,source_only=True)),flush=True)
    assert len(rows)==len({r['candidate_key'] for r in rows})==83300
    summary=dict(states=dict(Counter(r['employment']['state'] for r in rows)),
        absence_states=dict(Counter(r['absence']['state'] for r in rows)),
        indicators={key:sum(r[key] for r in rows) for key in rows[0] if key.startswith('status_')},
        original_population_retained=True,forecasts_changed=False,new_fits=0,
        yearly_availability_audit=audit)
    save_wire(OUT/'status-ledger.json',dict(rows=rows));save(OUT/'summary.json',summary)
    fixed=list(FIXED)
    ordinary=sorted([p for p in population if p['origin_year']==2024 and p['current_model_origin']
        and p['returned_40man'] and p['recent_mlb_pa']>=400 and p['role_status']=='hitter_history_or_listing_hint'
        and p['player_id'] not in {c[1] for c in FIXED}],key=lambda p:p['player_id'])[0]
    fixed.append((ordinary['player_name'],ordinary['player_id'],2024))
    lut={r['candidate_key']:r for r in rows};pop={p['candidate_key']:p for p in population};cases=[]
    for name,pid,y in fixed:
        key=f'{y}:{pid}';p=pop.get(key);r=lut.get(key)
        if p:
            cutoff=date.fromisoformat(p['information_date'])
            future=dict(transaction_id=-999999,player_id=pid,available_date=date(y+1,12,31),
                event_date=date(y,1,1),kind='deceased',il_kind=None,description='future backdated mutation',
                category='unspecified',surgery=False,duration_years=None)
            assert reconcile(p,raw[pid],records[pid]+[future],teams,reports[pid])==r
        cases.append(dict(name=name,player_id=pid,origin_year=y,source_population_row=p,
            status=r,raw_employment_events=raw[pid],
            eligible_absence_records=as_of(records[pid],cutoff) if p else [],
            future_mutation_invariant=bool(p),new_PA_forecast=None))
    save_wire(OUT/'source-cases.json',dict(cases=cases,player_walkthrough_status='pending'))
    save(OUT/'preparation-receipt.json',dict(status='source_built_review_pending',population_rows=len(rows),
        original_forecasts_changed=False,player_walkthrough_status='pending',new_fits=0,
        source_hashes={**seal['source_hashes'],**read(OUT/'recovery-seal.json')['hashes']},
        artifact_hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in
            [OUT/'source-seal.json',OUT/'recovery-seal.json',OUT/'status-ledger.json',OUT/'summary.json',OUT/'source-cases.json']}))
    print(json.dumps(summary),flush=True)


if __name__=='__main__':main()
