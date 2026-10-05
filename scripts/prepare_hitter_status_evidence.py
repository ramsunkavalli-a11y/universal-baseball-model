"""Build dated status inputs on the unchanged population; no projection fits."""
from collections import Counter, defaultdict
from datetime import date
import json
from pathlib import Path

import polars as pl

from prepare_foreign_component_translation import ROOT, read, save, verify
from universal_baseball import availability_context_v29b as clinical
from universal_baseball.hitter_status_evidence import reconcile, employment_kind
from universal_baseball.storage import sha256_file

OUT = ROOT/'reports/generated/hitter-status-evidence'
POP = ROOT/'reports/generated/hitter-preseason-population-source'
REPORTS = ROOT/'config/hitter_status_return_reports.json'
FACTS = [ROOT/'config/availability_facts_v29.json', ROOT/'config/availability_facts_v29b.json']
FIXED = [('Luke Voit',572228,2021),('Fernando Tatis Jr.',665487,2022),
    ('Jarren Duran',680776,2024),('Wander Franco',677551,2023),('Tucupita Marcano',672779,2024),
    ('Eric Thames',519346,2016),('Rhys Hoskins',656555,2023),('Brandon Belt',474832,2023),
    ('Hyeseong Kim',808975,2024),('Shohei Ohtani',660271,2017),('Seiya Suzuki',673548,2021),
    ('Masataka Yoshida',807799,2022),('Jung Hoo Lee',808982,2023),('Matt McLain',680574,2023)]


def sources():
    population = pl.read_parquet(POP/'population.parquet').to_dicts()
    assert len(population)==83300
    verified = read(ROOT/'reports/generated/availability-context-v29b/source-manifest.json')['source_hashes']
    lookup = {str(Path(p).resolve()):h for p,h in verified.items()}
    paths = [POP/'population.parquet', POP/'final-review.json', REPORTS, *FACTS,
        ROOT/'docs/hitter-status-evidence-contract.md', Path(__file__),
        ROOT/'src/universal_baseball/hitter_status_evidence.py',
        ROOT/'src/universal_baseball/availability_context_v29.py',
        ROOT/'src/universal_baseball/availability_context_v29b.py',
        ROOT/'tests/test_hitter_status_evidence.py']
    captures=[];teams=set();raw=defaultdict(list)
    for year in range(2012,2026):
        path=POP/f'captures/teams-{year}.json';paths.append(path)
        teams.update(t['id'] for t in read(path)['teams'])
    for year in range(2015,2025):
        path=ROOT/'reports/generated/hitter-injury-history-v2'/('source-2015' if year==2015 else 'source')/f'captures/transactions-{year}.json'
        assert str(path.resolve()) in lookup and sha256_file(path)==lookup[str(path.resolve())]
        captures.append((year,read(path)));paths.append(path)
    for year in range(2012,2026):
        path=POP/f'captures/transactions-{year}.json'
        meta=path.with_suffix('.json.metadata.json')
        assert sha256_file(path)==read(meta)['sha256']
        captures.append((year,read(path)));paths.extend([path,meta])
    for _,payload in captures:
        for r in payload['transactions']:
            pid=(r.get('person') or {}).get('id')
            if pid and employment_kind(r,teams) is not None:
                raw[pid].append(r)
    facts=[f for path in FACTS for f in read(path)['events']]
    records,audit=clinical.normalize(captures,teams,facts,maximum=date(2025,1,24))
    byperson=defaultdict(list)
    for r in records:byperson[r['player_id']].append(r)
    reports=defaultdict(list)
    for r in read(REPORTS)['events']:reports[r['player_id']].append(r)
    return population,raw,byperson,teams,reports,paths,audit


def main():
    assert not OUT.exists(), 'Inspect existing status execution instead of restarting'
    population,raw,records,teams,reports,paths,audit=sources()
    save(OUT/'source-seal.json',dict(source_hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in paths},
        original_population_rows=83300,new_fits=0,protected_outcomes_read=False))
    rows=[]
    for i,p in enumerate(population):
        pid=p['player_id']
        rows.append(reconcile(p,raw[pid],records[pid],teams,reports[pid]))
        if (i+1)%15000==0: print(json.dumps(dict(rows=i+1,source_only=True)),flush=True)
    assert len(rows)==len({r['candidate_key'] for r in rows})==83300
    summary=dict(states=dict(Counter(r['employment']['state'] for r in rows)),
        absence_states=dict(Counter(r['absence']['state'] for r in rows)),
        indicators={key:sum(r[key] for r in rows) for key in rows[0] if key.startswith('status_')},
        original_population_retained=True,forecasts_changed=False,new_fits=0,
        yearly_availability_audit=audit)
    save(OUT/'status-ledger.json',dict(rows=rows))
    save(OUT/'summary.json',summary)
    fixed=list(FIXED)
    ordinary=sorted([p for p in population if p['origin_year']==2024 and p['current_model_origin']
        and p['returned_40man'] and p['recent_mlb_pa']>=400 and p['role_status']=='hitter_history_or_listing_hint'
        and p['player_id'] not in {c[1] for c in FIXED}],key=lambda p:p['player_id'])[0]
    fixed.append((ordinary['player_name'],ordinary['player_id'],2024))
    lut={r['candidate_key']:r for r in rows};pop={p['candidate_key']:p for p in population};cases=[]
    for name,pid,y in fixed:
        key=f'{y}:{pid}';p=pop.get(key);r=lut.get(key)
        if p:
            future=dict(transaction_id=-999999,player_id=pid,available_date=date(y+1,12,31),
                event_date=date(y,1,1),kind='deceased',il_kind=None,description='future backdated mutation',
                category='unspecified',surgery=False,duration_years=None)
            assert reconcile(p,raw[pid],records[pid]+[future],teams,reports[pid])==r
        cases.append(dict(name=name,player_id=pid,origin_year=y,source_population_row=p,
            status=r,raw_employment_events=raw[pid],normalized_absence_records=records[pid],
            future_mutation_invariant=bool(p),new_PA_forecast=None))
    save(OUT/'source-cases.json',dict(cases=cases,player_walkthrough_status='pending'))
    save(OUT/'preparation-receipt.json',dict(status='source_built_review_pending',population_rows=len(rows),
        original_forecasts_changed=False,player_walkthrough_status='pending',new_fits=0,
        source_hashes=read(OUT/'source-seal.json')['source_hashes'],
        artifact_hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in
            [OUT/'source-seal.json',OUT/'status-ledger.json',OUT/'summary.json',OUT/'source-cases.json']}))
    print(json.dumps(summary),flush=True)


if __name__=='__main__':main()
