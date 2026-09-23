"""Package the history/calibration experiment and readable score tables."""
import json
import shutil
from pathlib import Path
from fit_hitter_history_calibration_v1 import OUT, PACKAGE
from fit_hitter_arrival_coherence_v1 import save
from universal_baseball.storage import sha256_file

LABELS = {'R': 'Original rich model', 'RC': 'Original + past-only calibration',
          'H': '+ observed-history summaries', 'HC': 'History + past-only calibration (primary)'}


def main():
    s = json.loads((OUT/'score-report.json').read_text())
    fit = json.loads((OUT/'fit-manifest.json').read_text())
    lines = ['# History continuity and prospect probability calibration: results', '',
             '2026-09-23. Exposed historical development tests; no production forecasts changed.', '',
             '## Plain-language decision', '',
             'The combined change is not a model upgrade. History summaries alone improve next-year',
             'arrival Brier by 1.11% and log loss by 1.17%, in five of six origins, with favorable',
             'paired player-cluster intervals. Keep that diagnostic arm as a follow-up candidate,',
             'not a post-hoc substitute for the primary combined arm. Its 2021 arrival count only',
             'moves from 58 to 61 versus 157 observed: missing-calendar-history summaries do not',
             'resolve the major pandemic-era failure.', '',
             'Past-only calibration raises the one-year probabilities too much in later cohorts.',
             'The combined method expects about 650 arrivals outside 2021 versus 520 observed,',
             'compared with the original 543. A global historical adjustment does not transfer',
             'reliably across these eras.', '',
             'For becoming a regular, the combined total moves from 19 to 30 versus 31 observed,',
             'but Brier gets slightly worse and log loss slightly better, both uncertain. It still',
             'underpredicts 2021 (11 versus 17) while overpredicting 2022 (19 versus 14). This is',
             'a concrete example of a close total hiding errors in who succeeds and when.', '',
             'Three-year arrival improves on average, but only one of the two origins improves',
             'on both scores, and the simpler logistic coverage benchmark remains better. No',
             'regular-workload or delivered-player-value claim is supported.', '',
             '## What changed in the experiment', '',
             'Added 25 inputs summarizing actually observed recent seasons, retaining elapsed calendar',
             'time and leaving all original exact-season lags intact. Short current seasons can draw',
             'on older performance; no missing season is invented and low PA is not labeled an injury.',
             'Separately calibrated each model using only older out-of-time forecasts with fully',
             'mature outcomes. The transformation adjusts probability levels, not within-year rankings.',
             'The combined history-plus-calibration model was declared primary before these fits.', '',
             'Training settings, player-identity weighting, cohorts and outcome definitions remain',
             'fixed. New history is assembled from the existing 2009–2024 snapshot archive; early',
             'history can be left-censored, and levels are retained rather than treated as equivalent.',
             'Calibration uses equal-origin weights, not outcome prevalence from the current test.', '',
             '## Main results', '',
             'Expected counts sum probabilities over player-season cases. The same player can appear',
             'in multiple origins. Lower Brier and log loss are better; scores weight origins equally.']
    for target, r in s['targets'].items():
        m = r['prospects']; hc = m['HC']
        lines += ['', '### '+target, '',
                  f"Decision: **{r['status']}**. {hc['rows']:,} never-debuted prospect snapshots; "
                  f"{hc['origins']} test origins; {hc['observed']} observed successes.", '',
                  '| Method | Expected successes | Brier | Log loss |', '|---|---:|---:|---:|']
        for a in LABELS:
            v = m[a]
            lines.append(f"| {LABELS[a]} | {v['expected']:.1f} | {v['brier']:.6f} | {v['log_loss']:.6f} |")
        lines += ['', 'Primary HC minus original R, paired player-cluster 95% intervals:', '']
        for loss, c in r['comparisons']['HC_minus_R'].items():
            lines.append(f"- {loss}: {c['delta']:+.6f} [{c['interval95'][0]:+.6f}, {c['interval95'][1]:+.6f}]; "
                         f"{c['improving_origins']}/{hc['origins']} improving origins.")
        lines += ['', 'Gates: '+', '.join(f'{k}={v}' for k, v in r['gates'].items())+'.', '',
                  '| Origin | Observed | R expected | RC expected | H expected | HC expected | HC/R Brier | HC/R log loss |',
                  '|---|---:|---:|---:|---:|---:|---:|---:|']
        annual = {a: {v['origin']: v for v in m[a]['annual']} for a in LABELS}
        for y, v in sorted(annual['HC'].items()):
            b = annual['R'][y]
            lines.append(f"| {y} | {v['observed']} | {b['expected']:.1f} | {annual['RC'][y]['expected']:.1f} | "
                         f"{annual['H'][y]['expected']:.1f} | {v['expected']:.1f} | {v['brier']/b['brier']:.3f} | "
                         f"{v['log_loss']/b['log_loss']:.3f} |")
        lines += ['', '| Prospect group | Cases | Observed | R expected | HC expected | HC/R Brier | HC/R log loss |',
                  '|---|---:|---:|---:|---:|---:|---:|']
        for name, group in r['slices'].items():
            if not group: continue
            v = group['HC']; b = group['R']
            lines.append(f"| {name} | {v['rows']} | {v['observed']} | {b['expected']:.1f} | {v['expected']:.1f} | "
                         f"{v['brier']/b['brier']:.3f} | {v['log_loss']/b['log_loss']:.3f} |")
        lines += ['', 'Groups overlap and are descriptive. Do not sum them or select a model per subgroup.', '',
                  '| Matched reference | Cases | HC / reference Brier | HC / reference log loss |',
                  '|---|---:|---:|---:|']
        for name, values in r['controls'].items():
            a, b = values['candidate'], values['reference']
            lines.append(f"| {name} | {a['rows']} | {a['brier']:.6f} / {b['brier']:.6f} | {a['log_loss']:.6f} / {b['log_loss']:.6f} |")
        lines += ['', 'Ranking, pooled captures within each origin:', '']
        for a in ('R', 'H'):
            top = r['ranking'][a]
            lines.append(f"- {a}: top 5% captures {top['0.05']['successes']}/{hc['observed']}; "
                         f"top 10% captures {top['0.1']['successes']}/{hc['observed']}.")
    lines += ['', '## Calibration support', '',
              '| Target / origin | Arm | Calibration origins | Positive cases | Intercept | Slope | Fallback |',
              '|---|---|---|---:|---:|---:|---|']
    for n in fit['calibrators']:
        lines.append(f"| {n['target']} / {n['year']} | {n['arm']} | {', '.join(map(str,n['origins']))} | "
                     f"{n['positives']} | {n['intercept']:.3f} | {n['slope']:.3f} | {n['fallback']} |")
    lines += ['', '## Limits and decision boundaries', '',
              '- Only 2021/2022 ordinary three-year windows are scored; they overlap and contain just 31 regular cases. These cannot pass the >=3-origin confirmation gate.',
              '- Regular means 450+ MLB PA in at least two of three years. It is not WAR, batting talent, an All-Star label or whole-career value.',
              '- The 2021/2022 three-year calibrators only see pre-pandemic outcomes. This test cannot learn an unprecedented era change from future information.',
              '- The 2019 pandemic-crossing results are separate in score-report.json; they are excluded from calibration and the main scores.',
              '- Auxiliary raw forecasts from 2013 onward supply calibration, not extra detailed modern test seasons. Early raw-contact/pitch/context coverage is limited as in the preceding experiment.',
              '- Player-cluster intervals do not capture every common season shock; the historical tests and diagnostic groups are already exposed development evidence.',
              '- No automatic adoption, count-matching inflation, player-specific boosts, target redefinition or after-the-fact tuning. Any probability improvement still needs delivered-value validation.', '',
              'A metadata-only runtime repair converted a NumPy boolean for JSON serialization.',
              'The original prefit manifest is intact. runtime-repair.json records old/new hashes;',
              'the original calibration module is reconstructed and hash-checked, then all calibrated',
              'predictions are compared to it within 1e-12. Parquet byte identity across rewrites is',
              'not assumed. Numerical recipes and acceptance gates were not changed.', '',
              f"Raw arm/fold records: {len(fit['fits'])}; newly fitted: {sum(not n.get('inherited',False) for n in fit['fits'])}, plus one mutation refit.",
              f"Future-label/predictor mutation maximum probability difference: {fit['future_mutation_maximum_difference']}.", '',
              '## Reproduce', '', '```powershell',
              '.venv/Scripts/python.exe -X utf8 scripts/fit_hitter_history_calibration_v1.py',
              '.venv/Scripts/python.exe -X utf8 scripts/score_hitter_history_calibration_v1.py',
              '.venv/Scripts/python.exe -X utf8 scripts/report_hitter_history_calibration_v1.py',
              '.venv/Scripts/python.exe -X utf8 scripts/verify_hitter_history_calibration_v1.py', '```', '',
              'The existing prefit manifest must not be overwritten; use --freeze only on a fresh reproduction.']
    Path('docs/hitter-history-calibration-v1-result.md').write_text('\n'.join(lines)+'\n', encoding='utf-8', newline='\n')
    names = ('prefit-manifest.json', 'fit-manifest.json', 'raw-predictions.parquet', 'predictions.parquet', 'score-report.json')
    if (OUT/'runtime-repair.json').exists(): names += ('runtime-repair.json',)
    PACKAGE.mkdir(parents=True, exist_ok=True)
    for n in names: shutil.copyfile(OUT/n, PACKAGE/n)
    code = [Path(__file__), Path('scripts/score_hitter_history_calibration_v1.py'),
            Path('scripts/verify_hitter_history_calibration_v1.py'), Path('scripts/score_hitter_detail_arrival_v1.py'),
            Path('src/universal_baseball/multiyear_hitter_followup.py')]
    save(PACKAGE/'manifest.json', {'files': {n: sha256_file(PACKAGE/n) for n in names},
         'report_code': {str(p): sha256_file(p) for p in code},
         'production_forecasts_changed': False, 'protected_outcomes_used': False})
    print(json.dumps({'package': str(PACKAGE), 'statuses': {t:r['status'] for t,r in s['targets'].items()}}))


if __name__ == '__main__': main()
