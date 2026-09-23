"""Package fixed population-ablation evidence; never replace delivered forecasts."""
import json
from pathlib import Path
import shutil
import polars as pl
from audit_player_path_population_v1 import OUT
from fit_hitter_arrival_coherence_v1 import save
from universal_baseball.storage import sha256_file

PACKAGE=Path('model_artifacts/player-path-population-v1-2026-09-23')


def main():
    report=json.loads((OUT/'score-report.json').read_text())
    audit=json.loads((OUT/'support-audit.json').read_text())
    feasibility=json.loads((OUT/'c1-feasibility.json').read_text())
    p=report['primary'];m=p['methods']
    lines=['# Historical snapshot repair: result','',
        '2026-09-23. Fixed experiment from [the pre-fit plan](player-path-population-v1-plan.md).',
        f"Decision: **{report['status']}**. No delivered player forecasts or explorer changed.",
        'No 2026 outcomes opened. Historical results remain exposed development evidence.','',
        '## What the audit found','',
        'Keeping only each player\'s latest eligible snapshot discards many young career states.',
        'The repair restores every mature historical snapshot, with each player receiving total weight one.',
        'Counts below use age <=23 and 1–99 current MLB PA; effective support accounts for repeated identities.','',
        '| Fit cutoff / horizon | Latest snapshots | Restored snapshots / identities | Effective identities |',
        '|---|---:|---:|---:|']
    for r in audit['folds']:
        if r['cold']:continue
        a,b=r['latest']['young_brief_mlb'],r['all']['young_brief_mlb']
        lines.append(f"| {r['cutoff']} / {r['horizon']} | {a['rows']} | {b['rows']} / {b['identities']} | {b['identity_ess']:.1f} |")
    lines += ['', 'Exact promotion timing is not identified by this annual panel; partial-season exposure is available,',
        'but cannot be relabeled as a dated late-season promotion. Missing timing remains unknown.',
        'No earlier matched delivered forecasts were available for 2012–15. No extra evaluation origins added.','',
        '## Normal three-year results','',
        'Same players at origins 2016, 2021 and 2022. Lower is better. Targets are batting plus replacement,',
        '**not whole WAR**. These are exact fitted-distribution scores, so v1 finite-sample scores differ slightly.','',
        '| Model | Cumulative CRPS | Mean RMSE |','|---|---:|---:|']
    labels={'B0':'Age/stage comparisons','F0':'Age/level/workload forest','F1':'Full-feature latest snapshots','A1':'Full-feature identity-balanced snapshots'}
    for name in m:
        lines.append(f"| {labels[name]} | {m[name]['crps']:.6f} | {m[name]['rmse']:.6f} |")
    lines.append(f"| Delivered mean forecast | — | {m['A1']['delivered_rmse']:.6f} |")
    lines += ['','Paired player-cluster CRPS differences (A1 minus reference; negative favors repair):','']
    for ref,v in p['paired'].items():
        lines.append(f"- {ref}: {v['delta']:+.6f}, 95% interval [{v['interval95'][0]:+.6f}, {v['interval95'][1]:+.6f}].")
    lines += ['','## Young players and prospect success','',
        '| Group | Rows | Actual regular-workload paths | F1 expected | A1 expected |',
        '|---|---:|---:|---:|---:|']
    for name in ('Never-debuted minors','Recent debut','Young brief MLB'):
        g=p['groups'][name]
        lines.append(f"| {name} | {g['A1']['rows']} | {g['A1']['events']['regular_workload']['observed']} | {g['F1']['events']['regular_workload']['predicted']:.2f} | {g['A1']['events']['regular_workload']['predicted']:.2f} |")
    lines += ['','Regular-workload means at least 450 PA in two of three years. Other fixed events:',
        'no MLB play, six cumulative batting/replacement wins, and two four-win batting/replacement seasons.',
        'They overlap and are not scouting grades or All-Star probabilities. The exposed 98-row young brief-MLB',
        'group remains diagnostic, not fresh confirmation. Full event counts and calibration are in the package.','',
        '## Acceptance checks','']
    for name,passed in p['gates'].items():
        lines.append(f"- {name}: {'PASS' if passed else 'NOT PASSED'}.")
    lines += ['',f"Simulation stability: {report['numerical_stability']}.",
        'Five fixed 400-draw seeds and one 1600-draw run reuse fitted models. CRPS, Brier and mean-MSE',
        'sampling estimates remove their IID finite-draw bias; log loss has a common fixed clipping rule.',
        'Exact means/probabilities/CRPS determine the main comparisons. Joint energy and intervals remain',
        'simulation diagnostics. Small negative corrected loss estimates are possible, not negative true risks.',
        'Whole-player bootstrapping does not remove common-season shocks. Nonoverlapping 2016/2021 results,',
        'fully player-disjoint 2022 sensitivity and pandemic stress tests are separately reported.',
        'All historical H6 windows cross 2020 and cannot confirm ordinary six-year accuracy.','',
        '## Projection-anchored follow-up readiness','',
        feasibility['what_exists'],'',feasibility['why_not_fit'],'',feasibility['not_a_claim_of_impossibility'],'',
        'Next prerequisites:','']
    lines += [f'- {s}' for s in feasibility['next_prerequisites']]
    lines += ['','Prior direct prospect-tail and component-tail tests were inspected and remain rejected;',
        'no new threshold search was added. Dollar valuation still needs whole-WAR accounting, dated rights/costs,',
        'and the beyond-six-calendar-year control/liability tail. No failures are rescued with a post-hoc blend.','',
        '## Reproduce','', '```powershell',
        '.venv/Scripts/python.exe -X utf8 scripts/fit_player_path_population_v1.py',
        '.venv/Scripts/python.exe -X utf8 scripts/score_player_path_population_v1.py',
        '.venv/Scripts/python.exe -X utf8 scripts/audit_projection_path_feasibility_v1.py',
        '.venv/Scripts/python.exe -X utf8 scripts/report_player_path_population_v1.py',
        '.venv/Scripts/python.exe -X utf8 scripts/verify_player_path_population_v1.py','```','',
        'The pre-fit manifest is immutable; do not refreeze it after fitting. All 44 fitted distributions,',
        '264 simulated prediction sets and their local hashes are recorded. Exact predictions and compact',
        'diagnostics are packaged; the larger simulation files remain locally reproducible.']
    Path('docs/player-path-population-v1-result.md').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
    PACKAGE.mkdir(parents=True,exist_ok=True)
    for name in ('support-audit.json','removed-young-snapshots.parquet','prefit-manifest.json','v1-reproduction.json',
        'fit-manifest.json','exact-predictions.parquet','score-report.json','c1-feasibility.json'):
        shutil.copyfile(OUT/name,PACKAGE/name)
    save(PACKAGE/'manifest.json',{'status':report['status'],'files':{p.name:sha256_file(p) for p in PACKAGE.iterdir() if p.name!='manifest.json'},
        'report_code':{str(p):sha256_file(p) for p in [Path(__file__),Path('scripts/audit_projection_path_feasibility_v1.py')]},
        'production_forecasts_changed':False,'protected_outcomes_used':False})
    print(json.dumps({'package':str(PACKAGE),'status':report['status']}))


if __name__=='__main__':main()
