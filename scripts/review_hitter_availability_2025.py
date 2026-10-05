"""Review preserved captures after initial status-table null-schema failure.

The collector and twelve raw receipts remain byte-for-byte unchanged. Only the
consumer table's explicit nullable string/date schema differs from the initial
execution; no source, date, classification or retirement rule is changed.
"""
from collections import defaultdict
from datetime import date
from pathlib import Path
import json
import gzip
import polars as pl
import capture_hitter_availability_2025 as source
from universal_baseball.retirement_availability import events,state
from universal_baseball import availability_context_v29b as clinical
from universal_baseball.storage import sha256_file

ROOT,OUT,MAXIMUM=source.ROOT,source.OUT,source.MAXIMUM


def main():
    assert not (OUT/'review.json').exists(),'Preserve completed source review'
    captured=[source.capture(m) for m in range(1,13)]
    prior=[];paths=[source.CONTRACT,Path(__file__),Path(source.__file__),ROOT/'src/universal_baseball/retirement_availability.py',
        ROOT/'src/universal_baseball/availability_context_v29.py',ROOT/'src/universal_baseball/availability_context_v29b.py']
    seal=source.read(ROOT/'reports/generated/practical-hitter-retirement-v44/source-manifest.json')['input_hashes']
    for y in range(2015,2025):
        p=ROOT/'reports/generated/hitter-injury-history-v2'/('source-2015' if y==2015 else 'source')/'captures'/f'transactions-{y}.json'
        assert sha256_file(p)==seal[str(p)];prior.append((y,p,source.read(p)));paths.append(p)
    captures=[*prior,*[c for c,_ in captured]];paths.extend(p for c,receipt in captured for p in [c[1],receipt])
    rp=ROOT/'reports/generated/hitter-rosters-2025-source/captures/teams-2025.json.gz'
    with gzip.open(rp,'rt',encoding='utf8') as f:teams={t['id'] for t in json.load(f)['teams']}
    assert len(teams)==30;paths.append(rp)
    fact_paths=[ROOT/'config/availability_facts_v29.json',ROOT/'config/availability_facts_v29b.json'];paths.extend(fact_paths)
    facts=[e for p in fact_paths for e in source.read(p)['events']]
    normalized,audit=clinical.normalize([(y,p) for y,_,p in captures],teams,facts,maximum=MAXIMUM)
    retirements=events(captures,MAXIMUM);by=defaultdict(list);ret=defaultdict(list)
    for r in normalized:by[r['player_id']].append(r)
    for r in retirements:ret[r['player_id']].append(r)
    pp=ROOT/'reports/generated/hitter-base-inputs-2025-reviewed/assembled-before-translation.parquet';pop=pl.read_parquet(pp);paths.append(pp)
    rows=[];walks=[]
    for o in pop.iter_rows(named=True):
        pid=o['player_id'];r=state(ret[pid],MAXIMUM);h=clinical.ledger(by[pid],MAXIMUM)
        future=dict(transaction_id=999999999,player_id=pid,available_date=date(2026,1,1),event_date=date(2025,1,1),
            kind='deceased',description='inadmissible future sentinel',il_kind=None,mlb_team_scope=True,duration_years=None)
        assert clinical.ledger(by[pid]+[future],MAXIMUM)==h
        future_ret=dict(transaction_id=999999999,player_id=pid,known_date=date(2026,1,1),event_date=date(2025,1,1),kind='retired')
        assert state(ret[pid]+[future_ret],MAXIMUM)==r
        row=dict(row_id=o['row_id'],player_id=pid,reported_retired=r['reported_retired'],hard_unavailable=h['hard_unavailable'],
            hard_reason=h['hard_reason'],availability_state=h['availability_state'],nonmedical_reason=h['nonmedical_reason'],
            context_latest_known_date=h['latest_context_date'],medical_recovery_certified=False,
            status_observation='eligible_captured_evidence' if by[pid] or ret[pid] else 'no_captured_evidence_not_certified_health')
        rows.append(row)
        if r['reported_retired'] or h['hard_unavailable'] or r['return_evidence'] or pid in [592450,701762,670541,808982,691406,656555]:
            walks.append(dict(player_id=pid,name=o['player_name'],actual_state=row,retirement_events=ret[pid],retirement_resolution=r,
                hard_or_nonmedical_events=[e for e in by[pid] if e['kind'] in ['deceased','permanent_ineligible','reinstated','restricted',
                    'suspended_unspecified','ineligible_unspecified','finite_ineligible']],
                judgment='Dated reported retirement or definitive hard restriction forces only participation to zero; talent is not relabeled.'
                    if row['reported_retired'] or row['hard_unavailable'] else
                    'No definitive override: injury, release, unknown job and a reported return are not permanent unavailability.',
                future_mutation_invariant=True))
    status=pl.DataFrame(rows,schema_overrides={'hard_reason':pl.String,'nonmedical_reason':pl.String,'context_latest_known_date':pl.Date})
    assert len(status)==4030 and status['row_id'].n_unique()==4030
    past_path=ROOT/'reports/generated/hitter-preseason-readiness-v68/scored-predictions.parquet';past=pl.read_parquet(past_path);paths.append(past_path)
    for o in past.iter_rows(named=True):
        known=date(o['origin_year'],12,31)
        assert state(ret[o['player_id']],known)['reported_retired']==o['reported_retired'],(o['player_id'],o['origin_year'],'retirement')
        assert clinical.ledger(by[o['player_id']],known)['hard_unavailable']==o['hard_unavailable'],(o['player_id'],o['origin_year'],'hard')
    status.write_parquet(OUT/'availability.parquet')
    source.write(OUT/'completed-player-walks.json',dict(walks=walks,source_only=True,protected_outcomes_used=False))
    source.write(OUT/'review.json',dict(source_review_status='complete_with_coverage_qualification',source_year=2025,source_cutoff=str(MAXIMUM),
        preserved_collector_schema_failure=True,consumer_repair='Explicit nullable string/date schema only; no changed captures or classification.',
        monthly_captures=12,raw_transactions=sum(len(c[2]['transactions']) for c,_ in captured),population=4030,
        reported_retired=int(status['reported_retired'].sum()),hard_unavailable=int(status['hard_unavailable'].sum()),
        no_captured_evidence=status.filter(pl.col('status_observation')=='no_captured_evidence_not_certified_health').height,
        historical_overrides_checked=len(past),historical_overrides_unchanged=True,source_player_walks=len(walks),normalization_audit=audit,
        source_player_walkthrough_status='complete',publication_vintage_verified=False,all_level_completeness_certified=False,
        candidate_fitted=False,candidate_frozen=False,protected_outcomes_used=False,
        input_hashes={str(p):sha256_file(p) for p in paths},output_hashes={str(p):sha256_file(p) for p in OUT.iterdir() if p.suffix in ['.json','.parquet']}))
    print(f'2025 status: {len(walks)} walks; {len(past)} historical overrides unchanged; {status["reported_retired"].sum()} retired and {status["hard_unavailable"].sum()} hard restrictions.',flush=True)


if __name__=='__main__':main()
