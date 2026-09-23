"""Package the targeted missing-season repair and its remaining limitations."""
import json
import shutil
from pathlib import Path
from fit_hitter_canceled_season_v1 import OUT,PACKAGE
from fit_hitter_arrival_coherence_v1 import save
from universal_baseball.storage import sha256_file


def main():
    s=json.loads((OUT/'score-report.json').read_text());fit=json.loads((OUT/'fit-manifest.json').read_text())
    lines=['# Canceled-season input routing: result','',
           '2026-09-23. Exposed historical development experiment; live models remain unchanged.','',
           '## What the repair does','',
           'A year with no minor-league season is not the same as a player individually missing',
           'a year. The original inputs encoded both as missing annual history. History summaries',
           'added in the last experiment did not remove that misleading block.','',
           'O fits a forecast using the same eligible training players and settings, but leaves',
           'out the exogenously unavailable annual block in both training and prediction. For',
           '2021, it uses current evidence and correctly dated 2019 evidence; for 2022 it uses',
           'current evidence and 2021 evidence. It never relabels 2019 as 2020, invents a stat line,',
           'scales PA, or learns a probability boost from the observed test totals. Valid cumulative',
           'career/level-path information remains available. Only never-debuted minor leaguers',
           'with no record in the canceled slot are routed to O. Other forecasts equal R exactly.','',
           'N removes both prior annual blocks as a diagnostic, not a candidate selected after scoring.',
           'R is the original full-detail model. O was the primary repair specified before fitting.','',
           'Official background and plan: [canceled-season experiment](hitter-canceled-season-v1-plan.md).',
           'The cancellation, shorter 2021 schedules and affiliate reorganization were known at',
           'the cutoff. This experiment isolates an input-meaning mismatch, not every era effect.','',
           '## Outcome comparisons','',
           'Counts are sums of probabilities over player-season cases, not a hard classification.',
           'A 2021 origin predicts 2022 arrivals or outcomes in 2022–2024. Lower proper scores are better.']
    for target,r in s['targets'].items():
        lines += ['',f'### {target}','',f"Status: **{r['status']}**.",'',
                  '| Origin | Cases | Observed | Original R expected | Outage O expected | No-prior N expected | O/R Brier | O/R log loss |',
                  '|---|---:|---:|---:|---:|---:|---:|---:|']
        for y,m in r['annual'].items():
            a,b=m['O'],m['R']
            lines.append(f"| {y} | {a['rows']} | {a['observed']} | {b['expected']:.1f} | {a['expected']:.1f} | "
                         f"{m['N']['expected']:.1f} | {a['brier']/b['brier']:.3f} | {a['log_loss']/b['log_loss']:.3f} |")
        lines += ['',f"2021 absolute count-error reduction: {100*r['2021_count_error_reduction']:.1f}%.",'',
                  'Gates: '+', '.join(f'{k}={v}' for k,v in r['gates'].items())+'.','',
                  '| Origin / score | O minus R | Paired player-cluster 95% interval |',
                  '|---|---:|---|']
        for y,c in r['O_minus_R'].items():
            for loss,v in c.items():
                lines.append(f"| {y} / {loss} | {v['delta']:+.6f} | [{v['interval95'][0]:+.6f}, {v['interval95'][1]:+.6f}] |")
        lines += ['', '| 2021 group | Cases | Observed | R expected | O expected | O/R Brier | O/R log loss |',
                  '|---|---:|---:|---:|---:|---:|---:|']
        for group,m in r['slices']['2021'].items():
            if not m:continue
            a,b=m['O'],m['R']
            lines.append(f"| {group} | {a['rows']} | {a['observed']} | {b['expected']:.1f} | {a['expected']:.1f} | "
                         f"{a['brier']/b['brier']:.3f} | {a['log_loss']/b['log_loss']:.3f} |")
        lines += ['', 'Groups overlap; they are descriptive, not model-selection opportunities. 2022 groups are in score-report.json.','',
                  '| Matched full-window reference | Cases | O / reference Brier | O / reference log loss |',
                  '|---|---:|---:|---:|']
        for name,v in r['controls'].items():
            a,b=v['candidate'],v['reference']
            lines.append(f"| {name} | {a['rows']} | {a['brier']:.6f} / {b['brier']:.6f} | {a['log_loss']:.6f} / {b['log_loss']:.6f} |")
        lines += ['', '2021 top-5% capture of observed successes:', '']
        for arm,ranks in r['ranking']['2021'].items():
            lines.append(f"- {arm}: {ranks['0.05']['successes']}/{r['annual']['2021'][arm]['observed']}.")
    lines += ['', '## Historical annual-input outage stress', '',
              'Hide only the annual stat/PBP block in query prospects, preserving cumulative career',
              'information in every arm. This tests source unavailability, not lost physical development.',
              'The intact original forecast is replayed exactly before inputs are hidden.', '',
              '| Origin / hidden lag | Observed | Intact R expected | Masked R expected | Available O expected | O/masked Brier | O/masked log loss |',
              '|---|---:|---:|---:|---:|---:|---:|']
    for r in s['outage_stress']:
        m=r['metrics'];a,b=m['available_O'],m['masked_R']
        lines.append(f"| {r['year']} / {r['hidden_lag']} | {a['observed']} | {m['intact_R']['expected']:.1f} | "
                     f"{b['expected']:.1f} | {a['expected']:.1f} | {a['brier']/b['brier']:.3f} | {a['log_loss']/b['log_loss']:.3f} |")
    lines += ['', f"Both scores improve over masked R in {s['recovery_wins']}/4 scenarios. This is not a claim that discarding available history improves forecasts.", '',
              '## Limits and verification', '',
              '- These are targeted development results after inspecting the 2021 error. They are not a newly protected test or a universal arrival-model replacement.',
              '- Regular means at least 450 MLB PA in two of three years, not an All-Star, high-quality hitter, whole-career success or WAR.',
              '- Three-year tests have only two overlapping normal origins. Their confirmation gate remains failed regardless of favorable 2021 changes.',
              '- Non-outage years and other cohorts are unchanged by routing; equality is not independent confirmation of a general improvement.',
              '- Model variants share the fixed dated source panel and inherit its auxiliary-feature and retrospective reconstruction limits.',
              '- Population contraction, shorter schedules, development delays and unusually high subsequent opportunity are possible remaining causes; none is estimated by matching test totals here.',
              '- No 2026 outcomes opened. No live forecast, explorer or delivered player value changed.', '',
              f"Fits: {len(fit['fits'])} targeted + 6 stress + 1 future-mutation refit.",
              f"Original replay maximum difference: {fit['original_replay_max_difference']}; future mutation: {fit['future_mutation_max_difference']}.", '',
              '## Reproduce', '', '```powershell',
              '.venv/Scripts/python.exe -X utf8 scripts/fit_hitter_canceled_season_v1.py',
              '.venv/Scripts/python.exe -X utf8 scripts/score_hitter_canceled_season_v1.py',
              '.venv/Scripts/python.exe -X utf8 scripts/report_hitter_canceled_season_v1.py',
              '.venv/Scripts/python.exe -X utf8 scripts/verify_hitter_canceled_season_v1.py', '```', '',
              'Use --freeze only in a fresh reproduction; do not overwrite the saved prefit manifest.']
    Path('docs/hitter-canceled-season-v1-result.md').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
    names=('prefit-manifest.json','fit-manifest.json','predictions.parquet','outage-stress.parquet','score-report.json')
    PACKAGE.mkdir(parents=True,exist_ok=True)
    for n in names:shutil.copyfile(OUT/n,PACKAGE/n)
    code=[Path(__file__),Path('scripts/score_hitter_canceled_season_v1.py'),Path('scripts/verify_hitter_canceled_season_v1.py'),
          Path('scripts/score_hitter_detail_arrival_v1.py'),Path('scripts/score_hitter_history_calibration_v1.py'),
          Path('src/universal_baseball/multiyear_hitter_followup.py')]
    save(PACKAGE/'manifest.json',{'files':{n:sha256_file(PACKAGE/n) for n in names},
          'code':{str(p):sha256_file(p) for p in code},'protected_outcomes_used':False,'production_forecasts_changed':False})
    print(json.dumps({'package':str(PACKAGE),'statuses':{t:r['status'] for t,r in s['targets'].items()}}))


if __name__=='__main__':main()
