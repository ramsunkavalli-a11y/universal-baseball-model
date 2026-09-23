"""Archive fixed diagnostics and generate a compact evidence report."""
import json
import shutil
from pathlib import Path
from fit_hitter_era_schedule_v1 import OUT,PACKAGE
from fit_hitter_arrival_coherence_v1 import save
from universal_baseball.storage import sha256_file


def main():
    r=json.loads((OUT/'score-report.json').read_text());audit=json.loads((OUT/'schedule-audit.json').read_text())
    fit=json.loads((OUT/'fit-manifest.json').read_text())
    lines=['# Era and actual-schedule diagnostic results','',
        '2026-09-23. Exposed historical development tests. No production or 2026 forecast changes.','',
        '## What was tested','',
        '- R/A: inherited rich baseline and source-outage augmentation.',
        '- E/AE: corresponding refits without the explicit post-2021 era indicator.',
        '- S0/S1: identical no-era models trained on eligible origins from 2015 onward; S1 adds actual current minor schedule exposure.',
        '', 'S0 is essential: S1 versus full-history R mixes schedule, era and training-history changes.',
        'Every origin means a year-end forecast for the following MLB season.', '',
        '## Next-year MLB arrivals: never-debuted minor leaguers','',
        '| Origin | Actual | R | E | A | AE | S0 | S1 |', '|---|---:|---:|---:|---:|---:|---:|---:|']
    for y,m in sorted(r['annual'].items()):
        cells=[f"{m[a]['expected']:.1f}" if a in m else '—' for a in ('R','E','A','AE','S0','S1')]
        lines.append(f"| {y} | {m['R']['observed']} | "+' | '.join(cells)+' |')
    lines += ['', 'Counts are sums of player probabilities, not a count of players above an arbitrary threshold.', '',
        '## Proper-score comparisons','',
        '| Comparison | Score | Candidate | Reference | Difference | Player-cluster 95% interval | Improving origins |',
        '|---|---|---:|---:|---:|---|---:|']
    for name,c in r['comparisons'].items():
        for score,p in c['paired'].items():
            lines.append(f"| {name} | {score} | {c['candidate'][score]:.6f} | {c['reference'][score]:.6f} | {p['delta']:+.6f} | "
                         f"[{p['interval95'][0]:+.6f}, {p['interval95'][1]:+.6f}] | {p['improving_origins']} |")
    lines += ['', 'Lower scores are better. Comparisons use equal weight per origin and matching players.',
        'Player-cluster intervals do not account for all season-level shocks. Annual/stage tables are in the archived score report.', '',
        '## Fixed decisions','',
        f"- Era mechanism criterion supported: **{r['era_hypothesis_support']}**. This tests the explicit flag only, not all possible era proxies.",
        f"- Schedule evidence criteria satisfied: **{r['schedule_evidence']['supported']}**.",
        f"- Schedule broader research-candidate criteria satisfied: **{r['schedule_evidence']['broader_candidate']}**.",
        '- No criterion authorizes deployment: three-year arrival/regular workload and delivered value are not tested here.',
        '', 'Schedule gates: '+json.dumps(r['schedule_evidence'],sort_keys=True)+'.', '',
        '## Schedule audit','',
        '| Year | Prospects | Complete current schedule denominator | Mean PA | Mean PA/team game |',
        '|---|---:|---:|---:|---:|']
    for a in audit['prospects']:
        lines.append(f"| {a['origin_year']} | {a['players']} | {a['fully_covered']} | {a['mean_pa']:.1f} | {a['mean_pa_per_game']:.3f} |")
    lines += ['', 'The aggregate annual comparison mixes player/level composition and is not a causal decomposition.',
        'Team denominators use completed regular games, deduplicated by game ID including reversed home/away listings.',
        'Captures contain other same-sport leagues; player joins retain the existing input population, not a newly filtered one.',
        'No raw PA is increased. Multi-team fractions sum PA divided by each team’s full-season games.',
        'Partial schedule coverage produces a missing denominator, not a guessed value.',
        'This is schedule-relative workload, not individual injury, roster tenure or games personally available.', '',
        '## Verification and reproducibility','',
        f"{len(fit['fits'])} new fits plus {len(fit['mutations'])} future-mutation replays; both replays have zero difference.",
        'No new source fetches and no 2026 outcomes were used. Source/code hashes were locked before fitting.',
        'Run audit then fit --freeze only for a fresh reproduction; never replace the existing contract.', '', '```powershell',
        '.venv/Scripts/python.exe -X utf8 scripts/fit_hitter_era_schedule_v1.py',
        '.venv/Scripts/python.exe -X utf8 scripts/score_hitter_era_schedule_v1.py',
        '.venv/Scripts/python.exe -X utf8 scripts/report_hitter_era_schedule_v1.py',
        '.venv/Scripts/python.exe -X utf8 scripts/verify_hitter_era_schedule_v1.py', '```','']
    Path('docs/hitter-era-schedule-v1-result.md').write_text('\n'.join(lines),encoding='utf-8',newline='\n')
    PACKAGE.mkdir(parents=True,exist_ok=True)
    names=['prefit-manifest.json','fit-manifest.json','score-report.json','predictions.parquet',
           'schedule-audit.json','schedule-features.parquet','team-schedules.parquet']
    for n in names: shutil.copyfile(OUT/n,PACKAGE/n)
    code=[Path(__file__),Path('scripts/verify_hitter_era_schedule_v1.py'),Path('scripts/score_hitter_detail_arrival_v1.py'),
          Path('src/universal_baseball/multiyear_hitter_followup.py'),Path('docs/hitter-era-schedule-v1-result.md')]
    save(PACKAGE/'manifest.json',{'files':{n:sha256_file(PACKAGE/n) for n in names},
          'code':{str(p):sha256_file(p) for p in code},'protected_outcomes_used':False,'production_forecasts_changed':False})
    print(str(PACKAGE))


if __name__=='__main__':main()
