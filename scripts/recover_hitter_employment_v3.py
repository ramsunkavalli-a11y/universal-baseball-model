"""Resume source walks only, retaining the completed employment-only rebuild."""
from pathlib import Path
import json
import math
import polars as pl
from repair_hitter_employment_v3 import ROOT, GEN, OUT, read, verify, save
from universal_baseball.hitter_evidence_representation import job_evidence
from universal_baseball.storage import sha256_file


def main():
    if {p.name for p in OUT.iterdir()} != {'source-seal.json', 'employment-deltas.json', 'employment-indicators.parquet'}:
        raise ValueError('Recovery requires the exact completed-rebuild stopped state')
    verify(read(OUT / 'source-seal.json')['hashes'])
    paths = [OUT / 'source-seal.json', OUT / 'employment-deltas.json', OUT / 'employment-indicators.parquet',
             Path(__file__), ROOT / 'docs/hitter-employment-v3-execution-recovery.md']
    save('execution-recovery.json', dict(error="KeyError: origin_year in job_evidence before first walk",
        source_rebuild_repeated=False, source_outputs_overwritten=False, new_fits=0,
        source_walk_metadata='Same saved forecast origin_year and pa_0; no new source decisions',
        hashes={str(p.relative_to(ROOT)): sha256_file(p) for p in paths}))
    d = read(OUT / 'employment-deltas.json')['rows']
    delta = {r['candidate_key']: r for r in d}
    f = pl.read_parquet(OUT / 'employment-indicators.parquet')
    indicators = [n for n in f.columns if n.startswith('status_')]
    mapping = {r['candidate_key']: r for r in f.to_dicts()}
    walks = []
    required = ['origin_year', 'pa_0', 'on_40man', 'last_stat_gap',
                *[f'{n}_{lag}' for lag in range(3) for n in ('work', 'quality')],
                'status_major_link', 'status_agreement_unspecified']
    for w in read(GEN / 'overseas-opportunity-inventory/inventory.json')['walks']:
        r = w['forecast']; key = f'{r["origin_year"]}:{r["player_id"]}'
        inputs = dict(w['actual_job_inputs'], origin_year=r['origin_year'], pa_0=r['pa_0'])
        if not set(required).issubset(inputs): raise ValueError('Incomplete required source fields')
        oldjob = job_evidence(inputs, w['source'])
        for n, v in oldjob.items():
            if not math.isclose(v, w['reconstructed_professional_activity'][n], abs_tol=1e-12, rel_tol=0):
                raise ValueError('Original professional fields do not reconstruct')
        new = mapping[key]; inputs.update({n: new[n] for n in indicators})
        rebuilt = job_evidence(inputs, w['source'])
        walks.append(dict(row_id=w['row_id'], candidate_key=key, name=r['player_name'],
            old_employment=w['status']['employment'],
            corrected_employment=delta[key]['employment'] if key in delta else w['status']['employment'],
            assignment_context=delta[key]['assignment_context'] if key in delta else [],
            changed_indicators={n: [w['status'][n], new[n]] for n in indicators if w['status'][n] != new[n]},
            old_job_evidence=oldjob, corrected_job_evidence=rebuilt,
            existing_PA={n: r[n] for n in ('current_pa', 'domestic_pa', 'repaired_domestic_pa')},
            current_forecast_missing=r['source_addition'], actual_MLB_PA=r['next_pa'],
            corrected_forecast=None, explanatory_inputs_only=True))
    if len(walks) != 59: raise ValueError('Changed retained walks')
    save('player-walks.json', dict(unique_walks=59, cases=walks))
    numeric = [r for r in d if r['changed_indicators']]
    summary = dict(source_origins=f.height, people=f['player_id'].n_unique(),
        employment_path_changed_origins=len(d), employment_path_changed_people=len({r['player_id'] for r in d}),
        numeric_indicator_changed_origins=len(numeric), numeric_indicator_changed_people=len({r['player_id'] for r in numeric}),
        reviewed_foreign_origins=266, retained_unique_walks=59,
        changed_signed_first_team_walks=[r['row_id'] for r in walks if r['old_job_evidence']['signed_first_team_work']
                                       != r['corrected_job_evidence']['signed_first_team_work']],
        new_fits=0, new_forecasts=0, source_only=True, human_review_status='pending')
    save('summary.json', summary)
    verify(read(OUT / 'source-seal.json')['hashes']); verify(read(OUT / 'execution-recovery.json')['hashes'])
    print(json.dumps(summary), flush=True)


if __name__ == '__main__': main()
