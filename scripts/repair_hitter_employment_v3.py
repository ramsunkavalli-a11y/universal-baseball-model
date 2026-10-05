"""Rebuild employment-only source deltas; do not revise clinical facts or forecasts."""
from collections import defaultdict
from pathlib import Path
import json
import polars as pl
from audit_overseas_public_coverage import ROOT, GEN, read, verify
from universal_baseball.hitter_status_evidence import employment_kind as previous_kind
from universal_baseball.hitter_employment_v3 import reconcile
from universal_baseball.hitter_evidence_representation import job_evidence
from universal_baseball.storage import sha256_file

OUT = GEN / 'hitter-employment-v3'
POP = GEN / 'hitter-preseason-population-source'
STATUS = GEN / 'hitter-status-evidence-v2'


def save(name, obj):
    path = OUT / name
    if path.exists(): raise ValueError('Preserve repair artifact')
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n', encoding='utf8', newline='\n')


def main():
    if OUT.exists(): raise ValueError('Inspect existing repair instead of restarting')
    source = read(STATUS / 'source-seal.json')['source_hashes']
    captures = [POP / 'captures' / f'transactions-{y}.json' for y in range(2012, 2026)]
    captures += [GEN / 'hitter-injury-history-v2' / ('source-2015' if y == 2015 else 'source') / 'captures'
                 / f'transactions-{y}.json' for y in range(2015, 2025)]
    teamfiles = [POP / 'captures' / f'teams-{y}.json' for y in range(2012, 2026)]
    for p in captures + teamfiles + [POP / 'population.parquet']:
        key = str(p.relative_to(ROOT))
        if sha256_file(p) != source[key]: raise ValueError('Changed historical input')
    paths = [Path(__file__), ROOT / 'src/universal_baseball/hitter_employment_v3.py',
        ROOT / 'tests/test_hitter_employment_v3.py', ROOT / 'docs/hitter-overseas-role-assignment-amendment.md',
        STATUS / 'status-ledger.json', POP / 'population.parquet',
        GEN / 'overseas-role-sources/source-seal.json', GEN / 'overseas-role-sources/ledger.json',
        GEN / 'overseas-opportunity-inventory/inventory.json'] + captures + teamfiles
    hashes = {str(p.relative_to(ROOT)): sha256_file(p) for p in paths}
    OUT.mkdir(); save('source-seal.json', dict(hashes=hashes, employment_only=True,
        forecast_membership_unchanged=True, target_year_maximum=2025, new_fits=0))
    population = {r['candidate_key']: r for r in pl.read_parquet(POP / 'population.parquet').to_dicts()}
    previous = read(STATUS / 'status-ledger.json')['rows']
    if len(previous) != 83300 or len(population) != 83300: raise ValueError('Changed source origins')
    teams = {t['id'] for p in teamfiles for t in read(p)['teams']}; raw = defaultdict(list)
    for p in captures:
        for r in read(p)['transactions']:
            pid = (r.get('person') or {}).get('id')
            if pid and previous_kind(r, teams) is not None: raw[pid].append(r)
    indicators = ['status_major_link', 'status_minor_agreement', 'status_agreement_unspecified',
        'status_acquisition_only', 'status_released', 'status_employment_unknown',
        'status_employment_conflict', 'status_negative_listing_conflict', 'status_positive_listing_conflict']
    deltas, features, revised = [], [], {}
    wanted = {r['player_id'] for r in read(GEN / 'overseas-role-sources/ledger.json')['rows']}
    for i, old in enumerate(previous):
        key = old['candidate_key']; p = population[key]
        new = reconcile(old, p, raw[old['player_id']], teams)
        for k in old:
            if k not in {*indicators, 'employment'} and new[k] != old[k]:
                raise ValueError('Changed non-employment or clinical field')
        changed = {k: [old[k], new[k]] for k in indicators if old[k] != new[k]}
        if changed or new['employment'] != old['employment']:
            deltas.append(dict(candidate_key=key, player_id=old['player_id'], player_name=p['player_name'],
                origin_year=old['origin_year'], target_year=old['target_year'], information_date=old['information_date'],
                old_employment=old['employment'], employment=new['employment'],
                assignment_context=new['assignment_context'], changed_indicators=changed))
        features.append(dict(candidate_key=key, player_id=old['player_id'], origin_year=old['origin_year'],
            information_date=old['information_date'], assignment_context_records=len(new['assignment_context']),
            **{k: new[k] for k in indicators}))
        if old['player_id'] in wanted: revised[key] = new
        if (i+1) % 10000 == 0: print(json.dumps(dict(origins=i+1, changed_rows=len(deltas), new_fits=0)), flush=True)
    changed_people = {r['player_id'] for r in deltas}
    numeric = [r for r in deltas if r['changed_indicators']]
    save('employment-deltas.json', dict(rows=deltas, clinical_and_absence_unchanged=True,
        original_ledger_preserved=True, zero_forecasts_reassigned=True if False else False))
    pl.DataFrame(features).write_parquet(OUT / 'employment-indicators.parquet')
    walks = []
    for w in read(GEN / 'overseas-opportunity-inventory/inventory.json')['walks']:
        f = w['forecast']; key = f'{f["origin_year"]}:{f["player_id"]}'; new = revised[key]
        inputs = dict(w['actual_job_inputs']); inputs.update({k: new[k] for k in indicators})
        rebuilt = job_evidence(inputs, w['source'])
        walks.append(dict(row_id=w['row_id'], candidate_key=key, name=f['player_name'],
            old_employment=w['status']['employment'], corrected_employment=new['employment'],
            assignment_context=new['assignment_context'], changed_indicators={k: [w['status'][k], new[k]]
                for k in indicators if w['status'][k] != new[k]},
            old_job_evidence=w['reconstructed_professional_activity'], corrected_job_evidence=rebuilt,
            existing_PA={k: f[k] for k in ('current_pa', 'domestic_pa', 'repaired_domestic_pa')},
            current_forecast_missing=f['source_addition'], actual_MLB_PA=f['next_pa'],
            corrected_forecast=None, explanatory_inputs_only=True))
    save('player-walks.json', dict(unique_walks=len(walks), cases=walks))
    summary = dict(source_origins=83300, people=len({r['player_id'] for r in previous}),
        employment_path_changed_origins=len(deltas), employment_path_changed_people=len(changed_people),
        numeric_indicator_changed_origins=len(numeric), numeric_indicator_changed_people=len({r['player_id'] for r in numeric}),
        reviewed_foreign_origins=266, retained_unique_walks=len(walks),
        changed_signed_first_team_walks=[r['row_id'] for r in walks if r['old_job_evidence']['signed_first_team_work']
                                      != r['corrected_job_evidence']['signed_first_team_work']],
        new_fits=0, new_forecasts=0, source_only=True, human_review_status='pending')
    save('summary.json', summary); verify(hashes); print(json.dumps(summary), flush=True)


if __name__ == '__main__': main()
