"""Package fixed richer-input probability results and limitations."""
import json
from pathlib import Path
import shutil
import polars as pl
from fit_hitter_detail_arrival_v1 import OUT
from fit_hitter_arrival_coherence_v1 import save
from universal_baseball.storage import sha256_file
from universal_baseball.hitter_detail_arrival import eligible,target_values

PACKAGE=Path('model_artifacts/hitter-detail-arrival-v1-2026-09-23')
LABELS={'B0':'Age / level / workload','B1':'Aggregate batting history','B2':'History + coverage controls',
    'D':'+ development detail','C':'+ contact / pitch / context','R':'+ all detail (primary)'}


def main():
    score=json.loads((OUT/'score-report.json').read_text())
    pre=json.loads((OUT/'prefit-manifest.json').read_text())
    fit=json.loads((OUT/'fit-manifest.json').read_text())
    panel=pl.read_parquet(OUT/'input-panel.parquet')
    query_ids=panel.filter(pl.col('origin_year')==2022)['player_id'].to_list()
    cold_audit=[]
    for target in ('next_year','arrival_three','regular_three'):
        for cold in (False,True):
            f=eligible(panel,2022,target,query_ids if cold else ()).filter(pl.col('prospect'))
            y=target_values(f,target)
            cold_audit.append({'target':target,'cold':cold,'prospect_training_rows':f.height,
                'positive_rows':int(y.sum()),'observed_rate':float(y.mean())})
    save(OUT/'cold-population-audit.json',{'rows':cold_audit,
        'interpretation':'Excluding every 2022 query identity changes the historical training population, removing many later survivors. This is not a random identity holdout; low probabilities alone do not prove identity leakage.'})
    lines=['# Does detail better identify future major leaguers?','',
        '2026-09-23. Fixed, matched-population probability experiment. No live forecasts changed.',
        'No protected 2026 outcomes used. These are exposed historical development results.','',
        '## Plain-language finding','',
        'More detail helps next-year arrival on average in the tree model: Brier improves about 1.4%',
        'and log loss about 2.0% versus aggregate batting history. Both paired intervals favor detail.',
        'It also beats the coverage control on those pooled scores. But only three of six years improve,',
        'and the logistic family gets worse with the same full detail. This is a useful lead, not a stable upgrade.',
        'Against the stronger existing probability ensemble on their shared four years, Brier is slightly',
        'better but log loss is worse. The weak basic control is not the final benchmark.','',
        'Three-year arrival improves versus aggregate stats, but its additional gain over coverage controls',
        'is uncertain, and it still expects only 460 arrivals versus 649 observed player-origin cases.',
        'For becoming a regular, full detail expects 19 cases versus 31 observed; the coverage control',
        'expects 23 and has better proper scores. Merely adding all fields does not solve that problem.',
        'The simpler logistic coverage model also beats the rich tree model for three-year arrival,',
        'so the remaining issue is not demonstrably just missing detail. No arm is deployed.','',
        '## What was tested','',
        'Same players, training cutoffs, identity weights and model settings; only inputs change.',
        'The full challenger includes batting history, level progression, raw contact-type/direction ×',
        'outcome bins, park-adjusted contact residuals, universal pitch-result rates, and available',
        'prior-opponent context. Coverage controls isolate information from simply having more data.',
        'No synthetic balancing of arrival counts, class weighting or post-hoc calibration was used.',
        'LightGBM is the controlled main comparison; fixed regularized logistic models check family dependence.',
        'The unit is a player at a season-end snapshot, not an independent career per row.','',
        'Input counts: '+', '.join(f'{a}={len(c)}' for a,c in pre['arms'].items())+'.',
        'Constant or unobserved training fields are dropped separately within each fit and recorded.','',
        '## Never-debuted minor leaguers','',
        'Lower Brier and log loss are better. Expected counts are sums of probabilities, not counts',
        'of players above an arbitrary cutoff. A player appearing in two test seasons appears twice.']
    for target,label in [('next_year','MLB appearance next year'),('arrival_three','MLB appearance within three years'),('regular_three','450+ PA in at least two of three years')]:
        r=score['targets'][target];g=r['groups']['prospects'];m=g['lightgbm/R']
        lines += ['',f'### {label}','',f"Status: `{r['status']}`. {m['rows']:,} snapshots, {m['players']:,} players, {m['origins']} test origins.",
            f"Observed events: **{m['observed']}**.",'',
            '| Inputs | Expected events | Brier | Log loss |','|---|---:|---:|---:|']
        for a,label2 in LABELS.items():
            x=g['lightgbm/'+a]
            lines.append(f"| {label2} | {x['expected']:.1f} | {x['brier']:.6f} | {x['log_loss']:.6f} |")
        lines += ['', 'Paired full-detail minus coverage-control differences (player-cluster 95% intervals):','']
        for name,x in r['paired_prospect_comparisons']['lightgbm/R_minus_B2'].items():
            lines.append(f"- {name}: {x['delta']:+.6f}, [{x['interval95'][0]:+.6f}, {x['interval95'][1]:+.6f}]; {x['improving_origins']}/{m['origins']} origins improve.")
        lines += ['', 'Predeclared checks: '+', '.join(f"{k}={'pass' if v else 'not passed'}" for k,v in r['gates'].items())+'.']
        l=g['logistic/R'];b=g['logistic/B2']
        lines += [f"Logistic family check: Brier {b['brier']:.6f} → {l['brier']:.6f}; log loss {b['log_loss']:.6f} → {l['log_loss']:.6f}."]
    lines += ['', '## Practical references on identical available rows','',
        'These are supplementary stronger historical references, not the controlled feature experiment.',
        'Their training recipes and weights differ. Do not read a feature win over B0 as beating the incumbent.','',
        '| Target | Reference | Rows | Full-detail Brier / reference | Full-detail log loss / reference |',
        '|---|---|---:|---:|---:|']
    for target,models in score['practical_references'].items():
        for name,x in models.items():
            a,b=x['challenger'],x['reference']
            lines.append(f"| {target} | {name} | {a['rows']} | {a['brier']:.6f} / {b['brier']:.6f} | {a['log_loss']:.6f} / {b['log_loss']:.6f} |")
    lines += ['', '## Limits and decision boundaries','',
        '- One-year normal tests: 2017, 2018, 2021–2024. Three-year normal tests: only 2021/2022; they overlap in outcome years.',
        '- The three-year confirmation gate remains failed because fewer than three normal origins exist. The separate 2019 pandemic stress is not pooled into it.',
        '- Raw contact history begins in 2015, park/pitch detail in 2016, prior-opponent context in 2021. At the three-year cutoffs, the latter has no mature training examples and is dropped—not tested successfully.',
        '- Earlier history is retained for both controls and challengers; missing PBP does not remove a player. That gives baseline history, not extra early detailed examples.',
        '- Cold-identity 2022 results and all starting-group/annual/calibration/discrimination results are in score-report.json. Auxiliary features are vintage-safe but not a fully refitted cold-identity auxiliary pipeline.',
        '- The cold test severely underpredicts in both arms. Removing every 2022 player also removes many historical survivors: prospect training arrival frequency falls from 3.11% to 1.73%, and regular-workload frequency from 0.332% to 0.094%. This is a population-shift stress, not a random-player holdout or proof that identity leakage explains the ordinary result. See cold-population-audit.json.',
        '- Year-end reconstruction and previous feature recipe choices are exposed development evidence, not historically issued forecasts.',
        '- Regular workload does not measure hitting quality or full WAR. Even a probability improvement needs a separate delivered-value test before deployment.',
        '- No after-the-fact selection of D/C, blending, probability inflation, model retuning or public-FV floor is applied.','',
        f"Completed {len(fit['fits'])} fits; future-label/predictor mutation maximum probability change: {fit['future_mutation_maximum_difference']:.1f}.",
        'Model settings, source hashes, dropped features, coverage and training maturity are retained in the package.','',
        '## Next bounded direction','',
        'Retain detail as an arrival research input. Before a career simulator, specify a compact,',
        'regularized arrival/continuation comparison with calibration learned only from earlier mature',
        'forecasts and the stronger probability benchmarks. Separately diagnose training-population and',
        'era shifts. Do not calibrate to these exposed test totals or rescue R by selecting D/C after the fact.',
        'A subsequent probability winner must still improve delivered player value before deployment.','',
        '## Reproduce','', '```powershell',
        '.venv/Scripts/python.exe -X utf8 scripts/fit_hitter_detail_arrival_v1.py',
        '.venv/Scripts/python.exe -X utf8 scripts/score_hitter_detail_arrival_v1.py',
        '.venv/Scripts/python.exe -X utf8 scripts/report_hitter_detail_arrival_v1.py',
        '.venv/Scripts/python.exe -X utf8 scripts/verify_hitter_detail_arrival_v1.py','```','',
        'The frozen pre-fit contract must not be overwritten. The input panel is locally reproducible from hashed sources; it is not a new external-data release.']
    Path('docs/hitter-detail-arrival-v1-result.md').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
    names=('prefit-manifest.json','fit-manifest.json','predictions.parquet','reference-predictions.parquet','score-report.json','cold-population-audit.json')
    PACKAGE.mkdir(parents=True,exist_ok=True)
    for n in names:shutil.copyfile(OUT/n,PACKAGE/n)
    code=[Path(__file__),Path('scripts/score_hitter_detail_arrival_v1.py'),Path('scripts/verify_hitter_detail_arrival_v1.py'),
        Path('src/universal_baseball/multiyear_hitter_followup.py')]
    save(PACKAGE/'manifest.json',{'files':{n:sha256_file(PACKAGE/n) for n in names},'report_code':{str(p):sha256_file(p) for p in code},
        'production_forecasts_changed':False,'protected_outcomes_used':False})
    print(json.dumps({'package':str(PACKAGE),'statuses':{k:v['status'] for k,v in score['targets'].items()}}))


if __name__=='__main__':main()
