"""Materialize scoped restrictions while preserving the first status ledger."""
from collections import Counter
from pathlib import Path
import json

from prepare_hitter_status_evidence import ROOT, OUT as ORIGINAL, sources, read, save, verify
from recover_hitter_status_evidence import save_wire
from universal_baseball.hitter_status_evidence_v2 import reconcile
from universal_baseball.storage import sha256_file

OUT = ROOT/'reports/generated/hitter-status-evidence-v2'


def main():
    assert not OUT.exists(),'Inspect actual existing execution before another attempt'
    receipt=read(ORIGINAL/'preparation-receipt.json')
    verify(receipt['source_hashes']);verify(receipt['artifact_hashes'])
    paths=[Path(__file__),ROOT/'src/universal_baseball/hitter_status_evidence_v2.py',
        ROOT/'tests/test_hitter_status_list_scopes.py',ROOT/'docs/hitter-status-list-scope-amendment.md',
        ORIGINAL/'preparation-receipt.json']
    hashes={**receipt['source_hashes'],**{str(p.relative_to(ROOT)):sha256_file(p) for p in paths}}
    save(OUT/'source-seal.json',dict(source_hashes=hashes,original_population_rows=83300,new_fits=0,
        original_ledger_preserved=True,protected_outcomes_read=False))
    population,raw,records,teams,reports,_,audit=sources();rows=[]
    old={r['candidate_key']:r for r in read(ORIGINAL/'status-ledger.json')['rows']};changes=[]
    for i,p in enumerate(population):
        pid=p['player_id'];r=reconcile(p,raw[pid],records[pid],teams,reports[pid]);rows.append(r)
        assert all(r[k]==old[r['candidate_key']][k] for k in r if k!='absence' and not k.startswith('status_'))
        changed={k:[old[r['candidate_key']][k],r[k]] for k in r if k.startswith('status_') and r[k]!=old[r['candidate_key']][k]}
        state=old[r['candidate_key']]['absence']['state']!=r['absence']['state']
        if changed or state:changes.append(dict(candidate_key=r['candidate_key'],name=p['player_name'],
            changed_indicators=changed,old_state=old[r['candidate_key']]['absence']['state'],new_state=r['absence']['state']))
        if (i+1)%15000==0:print(json.dumps(dict(rows=i+1,new_fits=0)),flush=True)
    assert len(rows)==len({r['candidate_key'] for r in rows})==83300
    save_wire(OUT/'status-ledger.json',dict(rows=rows))
    summary=dict(states=dict(Counter(r['employment']['state'] for r in rows)),
        absence_states=dict(Counter(r['absence']['state'] for r in rows)),
        indicators={k:sum(r[k] for r in rows) for k in rows[0] if k.startswith('status_')},
        changed_decision_rows=len(changes),new_fits=0,original_population_retained=True,
        original_forecasts_changed=False,clinical_normalization_reused=audit)
    save(OUT/'summary.json',summary);save(OUT/'changed-decisions.json',dict(rows=changes))
    save(OUT/'preparation-receipt.json',dict(status='source_built_review_pending',source_hashes=hashes,
        artifact_hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in
            [OUT/'source-seal.json',OUT/'status-ledger.json',OUT/'summary.json',OUT/'changed-decisions.json']}))
    print(json.dumps(summary),flush=True)


if __name__=='__main__':main()
