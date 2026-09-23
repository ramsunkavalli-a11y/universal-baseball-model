"""Archive the second, fixed mechanism test and its preceding failed routing test."""
import json
import shutil
from pathlib import Path
from fit_hitter_structural_missingness_v1 import OUT,PACKAGE
from fit_hitter_arrival_coherence_v1 import save
from universal_baseball.storage import sha256_file


def main():
    s=json.loads((OUT/'score-report.json').read_text());fit=json.loads((OUT/'fit-manifest.json').read_text())
    lines=['# Structural missingness: source outage versus individual absence','',
           '2026-09-23. Sequential exposed development experiment; no live forecasts changed.','',
           '## Why a second test was needed','',
           'The [first targeted experiment](hitter-canceled-season-v1-result.md) removed canceled-year',
           'inputs rather than labeling them as ordinary missing history. It improved 2021 next-year',
           'arrival Brier/log loss by 13.1%/15.3% and raised expected arrivals from 58 to 93 versus',
           '157 observed, but applying the same rule to 2022 raised arrivals to 176 versus 106.',
           'Its historical missing-input stress improved in all four cases. That supported the',
           'mechanism, but the proposed two-year routing failed its acceptance rule.','',
           'This follow-up was specified only after that result; it is not untouched confirmation.',
           'It tests one source-outage augmentation, with no weight, model-setting or calibration search.','',
           '## What was tested','',
           '- R: original rich model.',
           '- T: duplicate-only control with two dated source-outage flags.',
           '- A: same training copies/weights, with older annual inputs deliberately hidden and flagged as source outages.',
           '',
           'For each eligible prospect snapshot, the original receives half its weight and each of',
           'two masked copies one quarter. Total weight per original snapshot, identity and outcome',
           'class is unchanged. Other players keep a single row. The duplicate control uses the same',
           'copies and weights with inputs intact, isolating effects of duplication on tree fitting.',
           'Actual queries are never artificially masked. No future outcomes, fake batting lines,',
           'probability multipliers or player-specific corrections are used. Cumulative career',
           'summaries remain in all copies: this tests lost annual inputs, not lost development.','',
           '## Scores','',
           'Counts sum probabilities over player-season cases. Lower Brier/log loss are better.',
           'Year refers to the forecast origin: 2021 next-year outcomes occur in 2022.']
    for target,r in s['targets'].items():
        lines += ['',f'### {target}','',f"Status: **{r['status']}**.",'',
                  '| Model | Observed | Expected | Equal-origin Brier | Equal-origin log loss |',
                  '|---|---:|---:|---:|---:|']
        for arm,m in r['prospects'].items():
            lines.append(f"| {arm} | {m['observed']} | {m['expected']:.1f} | {m['brier']:.6f} | {m['log_loss']:.6f} |")
        lines += ['', '| Origin | Observed | R expected | T expected | A expected | A/R Brier | A/R log loss |',
                  '|---|---:|---:|---:|---:|---:|---:|']
        for y,m in r['annual'].items():
            a,b=m['A'],m['R']
            lines.append(f"| {y} | {a['observed']} | {b['expected']:.1f} | {m['T']['expected']:.1f} | {a['expected']:.1f} | "
                         f"{a['brier']/b['brier']:.3f} | {a['log_loss']/b['log_loss']:.3f} |")
        lines += ['',f"2021 count-error reduction: {100*r['2021_count_error_reduction']:.1f}%.", '',
                  'Gates: '+', '.join(f'{k}={v}' for k,v in r['gates'].items())+'.', '',
                  '| Comparison / score | Difference | Player-cluster 95% interval |',
                  '|---|---:|---|']
        comparisons={'2021 A–R':r['2021_comparison'],**{'pooled A–'+ref:c for ref,c in r['comparisons'].items()}}
        for name,comparison in comparisons.items():
            for score,c in comparison.items():
                lines.append(f"| {name} / {score} | {c['delta']:+.6f} | [{c['interval95'][0]:+.6f}, {c['interval95'][1]:+.6f}] |")
        lines += ['', '| 2021 group | Cases | Observed | R expected | A expected | A/R Brier | A/R log loss |',
                  '|---|---:|---:|---:|---:|---:|---:|']
        for group,m in r['slices']['2021'].items():
            if not m:continue
            a,b=m['A'],m['R']
            lines.append(f"| {group} | {a['rows']} | {a['observed']} | {b['expected']:.1f} | {a['expected']:.1f} | "
                         f"{a['brier']/b['brier']:.3f} | {a['log_loss']/b['log_loss']:.3f} |")
        lines += ['', '| Matched reference | Cases | A / reference Brier | A / reference log loss |',
                  '|---|---:|---:|---:|']
        for name,v in r['controls'].items():
            a,b=v['candidate'],v['reference']
            lines.append(f"| {name} | {a['rows']} | {a['brier']:.6f} / {b['brier']:.6f} | {a['log_loss']:.6f} / {b['log_loss']:.6f} |")
    lines += ['', '## Limits', '',
              '- Diagnosis and both fixes used exposed historical development results. Conditional player-cluster intervals do not capture all shared season shocks.',
              '- The cancellation flag marks known source unavailability, not injury or the amount of actual baseball development lost. Short schedules, selection after reorganization and changing opportunity may still matter.',
              '- The existing 2021 training records/outcomes are retained when mature. No year is discarded merely for being hard to predict.',
              '- Only two ordinary, overlapping three-year origins exist. Any long-horizon gain remains exploratory, and regular workload is not WAR or an All-Star target.',
              '- No blend or third tuning round is selected after these results. Passing a probability gate would still require delivered-player-value testing before deployment.',
              '- No live forecasts, explorer or frozen 2026 artifacts changed.', '',
              f"Completed {len(fit['fits'])} fits plus a future-mutation refit; maximum mutation difference {fit['future_mutation_max_difference']}.", '',
              '## Reproduce', '', '```powershell',
              '.venv/Scripts/python.exe -X utf8 scripts/fit_hitter_structural_missingness_v1.py',
              '.venv/Scripts/python.exe -X utf8 scripts/score_hitter_structural_missingness_v1.py',
              '.venv/Scripts/python.exe -X utf8 scripts/report_hitter_structural_missingness_v1.py',
              '.venv/Scripts/python.exe -X utf8 scripts/verify_hitter_structural_missingness_v1.py','```','',
              'Use --freeze only for a fresh reproduction. Keep the existing prefit contract intact.']
    Path('docs/hitter-structural-missingness-v1-result.md').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
    names=('prefit-manifest.json','fit-manifest.json','predictions.parquet','score-report.json')
    PACKAGE.mkdir(parents=True,exist_ok=True)
    for n in names:shutil.copyfile(OUT/n,PACKAGE/n)
    code=[Path(__file__),Path('scripts/score_hitter_structural_missingness_v1.py'),Path('scripts/verify_hitter_structural_missingness_v1.py'),
          Path('scripts/score_hitter_detail_arrival_v1.py'),Path('scripts/score_hitter_history_calibration_v1.py'),Path('src/universal_baseball/multiyear_hitter_followup.py')]
    save(PACKAGE/'manifest.json',{'files':{n:sha256_file(PACKAGE/n) for n in names},'code':{str(p):sha256_file(p) for p in code},
                               'protected_outcomes_used':False,'production_forecasts_changed':False})
    print(json.dumps({'package':str(PACKAGE),'statuses':{t:r['status'] for t,r in s['targets'].items()}}))


if __name__=='__main__':main()
