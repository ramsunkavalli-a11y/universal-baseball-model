"""Literal contract/role source diagnosis on the existing foreign cohort."""
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
import json
from audit_overseas_public_coverage import ROOT, GEN, read, verify
from universal_baseball.hitter_status_evidence import employment_events
from universal_baseball.overseas_role_sources import reports_at_origin
from universal_baseball.storage import sha256_file

OUT = GEN / 'overseas-role-sources'
POP = GEN / 'hitter-preseason-population-source'
CONFIG = ROOT / 'config/hitter_overseas_role_source_review.json'


def save(name, obj):
    path = OUT / name
    if path.exists(): raise ValueError('Preserve source evidence')
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n', encoding='utf8', newline='\n')


def main():
    if OUT.exists(): raise ValueError('Inspect existing source execution rather than restarting')
    prior = read(GEN / 'overseas-public-coverage/final-review.json')
    if prior['player_walkthrough_status'] != 'complete': raise ValueError('Earlier review incomplete')
    verify(prior['hashes'])
    priorseal = read(GEN / 'hitter-status-evidence-v2/source-seal.json')['source_hashes']
    paths = [Path(__file__), CONFIG, ROOT / 'docs/hitter-overseas-role-source-contract.md',
        ROOT / 'src/universal_baseball/overseas_role_sources.py', ROOT / 'tests/test_overseas_role_sources.py',
        ROOT / 'src/universal_baseball/hitter_status_evidence.py', ROOT / 'src/universal_baseball/hitter_preseason_population.py',
        GEN / 'overseas-public-coverage/final-review.json', GEN / 'overseas-public-coverage/coverage.json',
        GEN / 'overseas-opportunity-inventory/inventory.json', GEN / 'foreign-origin-inputs/origin-inputs.json']
    captures = [POP / 'captures' / f'transactions-{y}.json' for y in range(2012, 2026)]
    captures += [GEN / 'hitter-injury-history-v2' / ('source-2015' if y == 2015 else 'source') / 'captures'
                 / f'transactions-{y}.json' for y in range(2015, 2025)]
    teamfiles = [POP / 'captures' / f'teams-{y}.json' for y in range(2012, 2026)]
    paths += captures + teamfiles
    for p in captures + teamfiles:
        key = str(p.relative_to(ROOT))
        if key not in priorseal or sha256_file(p) != priorseal[key]: raise ValueError('Changed historical capture')
    hashes = {str(p.relative_to(ROOT)): sha256_file(p) for p in paths}
    OUT.mkdir(); save('source-seal.json', dict(hashes=hashes, new_fits=0, pilot_not_population_complete=True))
    cohort = read(GEN / 'overseas-public-coverage/coverage.json')['ledger']
    byid = {r['row_id']: r for r in read(GEN / 'overseas-opportunity-inventory/inventory.json')['walks']}
    origin = {r['candidate_key']: r for r in read(GEN / 'foreign-origin-inputs/origin-inputs.json')['rows']}
    reports = read(CONFIG)['reports']; teams = {t['id'] for p in teamfiles for t in read(p)['teams']}
    ids = {r['player_id'] for r in cohort}; raw = defaultdict(list)
    for p in captures:
        for r in read(p)['transactions']:
            pid = (r.get('person') or {}).get('id')
            if pid in ids: raw[pid].append(r)
    ledger = []
    for r in cohort:
        pid, y = r['player_id'], r['origin_year']; s = origin[f'{y}:{pid}']
        cutoff = s['information_date']; events = employment_events(raw[pid], teams, date.fromisoformat(cutoff))
        latest = events[-1]['known_date'] if events else None
        tail = [e for e in events if e['known_date'] == latest]
        report = reports_at_origin(reports, pid, y + 1, cutoff)
        # Outcome mutation cannot select source facts; these functions receive no outcomes.
        future = dict(player_id=pid, target_year=y + 1, publication_day=f'{y+1}-12-31',
                      report_id='future_mutation', reported_role='everyday_center_field', contract_form='major')
        check = reports_at_origin([*reports, future], pid, y + 1, cutoff)
        if check['reports'] != report['reports'] or check['role_coverage'] != report['role_coverage']:
            raise ValueError('Future report changes eligible evidence')
        ledger.append(dict(row_id=r['row_id'], player_id=pid, player_name=r['player_name'], origin_year=y,
            target_year=y+1, information_date=cutoff, source_addition=r['source_addition'],
            route_used=r['route_used'], raw_latest_known_date=latest, raw_latest_events=tail,
            reviewed_reports=report, current_rights_certified=False,
            forecast_unchanged=True, same_prior_walk=r['row_id'] in byid))
    walks = []
    lookup = {r['row_id']: r for r in ledger}
    for rid, w in byid.items():
        f = w['forecast']
        walks.append(dict(source=lookup[rid], existing_compressed_status=w['employment_category'],
            existing_employment=w['status']['employment'], existing_job_inputs=w['reconstructed_professional_activity'],
            held_support=w['held_training_same_profile'], source_history=w['source']['foreign_history_counts'],
            existing_PA={k: f[k] for k in ('current_pa', 'domestic_pa', 'repaired_domestic_pa',
                                         'repaired_domestic_p', 'repaired_domestic_conditional_pa')},
            current_forecast_missing=f['source_addition'], actual_MLB_PA=f['next_pa'],
            head_trace_reference=f'reports/generated/overseas-opportunity-inventory/inventory.json#row_id={rid}'))
    if len(ledger) != 266 or len(walks) != 59: raise ValueError('Changed retained population')
    summary = dict(rows=266, people=len(ids), walk_rows=59, source_reports=len(reports),
        eligible_report_rows=sum(bool(r['reviewed_reports']['reports']) for r in ledger),
        role_observed_rows=sum(r['reviewed_reports']['role_coverage'] == 'observed_report' for r in ledger),
        role_counts=dict(Counter(v['reported_role'] for r in ledger for v in r['reviewed_reports']['reports'] if v['reported_role'])),
        latest_raw_employment_missing=sum(not r['raw_latest_events'] for r in ledger),
        new_fits=0, new_forecasts=0, pilot_not_population_complete=True, human_review_status='pending')
    save('ledger.json', dict(summary=summary, rows=ledger)); save('player-walks.json', dict(cases=walks))
    verify(hashes); print(json.dumps(summary), flush=True)


if __name__ == '__main__': main()
