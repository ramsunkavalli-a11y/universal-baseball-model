"""Recover the terminal date-representation comparison failure, not model rules."""
from collections import Counter
from pathlib import Path
import json

from prepare_hitter_status_evidence_v2 import ROOT,OUT,ORIGINAL,sources,read,save,verify,reconcile,sha256_file
from recover_hitter_status_evidence import iso,save_wire


def main():
    assert (OUT/'source-seal.json').exists() and not (OUT/'status-ledger.json').exists()
    seal=read(OUT/'source-seal.json');verify(seal['source_hashes'])
    assert not (OUT/'recovery-seal.json').exists(),'Inspect actual existing recovery'
    extra=[Path(__file__),ROOT/'docs/hitter-status-v2-comparison-amendment.md',OUT/'source-seal.json']
    hashes={**seal['source_hashes'],**{str(p.relative_to(ROOT)):sha256_file(p) for p in extra}}
    save(OUT/'recovery-seal.json',dict(source_hashes=hashes,original_failure='date object versus serialized date preservation check',
        rules_population_and_clinical_content_unchanged=True,new_fits=0))
    population,raw,records,teams,reports,_,audit=sources();rows=[]
    old={r['candidate_key']:r for r in read(ORIGINAL/'status-ledger.json')['rows']};changes=[]
    for i,p in enumerate(population):
        pid=p['player_id'];r=reconcile(p,raw[pid],records[pid],teams,reports[pid])
        r=json.loads(json.dumps(r,default=iso,ensure_ascii=False,allow_nan=False));rows.append(r)
        assert all(r[k]==old[r['candidate_key']][k] for k in r if k!='absence' and not k.startswith('status_'))
        changed={k:[old[r['candidate_key']][k],r[k]] for k in r if k.startswith('status_') and r[k]!=old[r['candidate_key']][k]}
        if changed or old[r['candidate_key']]['absence']['state']!=r['absence']['state']:
            changes.append(dict(candidate_key=r['candidate_key'],name=p['player_name'],changed_indicators=changed,
                old_state=old[r['candidate_key']]['absence']['state'],new_state=r['absence']['state']))
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
            [OUT/'source-seal.json',OUT/'recovery-seal.json',OUT/'status-ledger.json',OUT/'summary.json',OUT/'changed-decisions.json']}))
    print(json.dumps(summary),flush=True)


if __name__=='__main__':main()
