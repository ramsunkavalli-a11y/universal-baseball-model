"""Readable actual-player review and lean archival evidence."""
from pathlib import Path
import json
import numpy as np
import polars as pl
from universal_baseball.storage import sha256_file
from universal_baseball.practical_hitter_v30 import EVENTS
import evaluate_hitter_opportunity_status_v59 as e


def main():
    notes=e.read(e.ROOT/'config/practical_hitter_v59_case_notes.json')
    cases=e.read(e.OUT/'cases.json');scores=e.read(e.OUT/'scores.json')
    verification=e.read(e.OUT/'verification.json');pre=e.read(e.OUT/'preflight.json')
    assert verification['replayed_heads']==70 and verification['cases']==len(cases)==12
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    lookup={(x['name'],x['origin']):x['note'] for x in notes['notes']}
    assert set(lookup)=={(c['origin']['player_name'],c['origin']['origin_year'])for c in cases}
    lines=['# Player review of dated hitter opportunity records','',
        'All 30,506 historical next-year forecasts remain. Batting talent is exact; this tests appearance and workload only.',
        'The twelve cases include seven fixed diagnostics, largest delivered gain/harm, false high/low and an ordinary case.',
        'Peers use only same-origin stage/debut, age, current/prior MLB exposure, minor exposure and roster-listing distance.',
        'They are baseball-use comparisons, not matched medical/legal cases. Outcomes never select peers.',
        'Captured transaction versions are cutoff-eligible, not certified original historical publication snapshots.',
        'Current roster non-listing is not loss of organizational rights. Activation is not medical recovery.',
        'Full inputs, eligibility, support and both saved-model decompositions are in cases.json.','']
    for c in cases:
        o=c['origin'];key=o['player_name'],o['origin_year']
        lines += [f"## {key[0]} using information through {key[1]}",'',
            f"Forecast for MLB {o['target_year']}; selection: {', '.join(c['selection'])}.",
            f"Age {o['age']:.0f}; stage {o['stage']}; historical position code {o['source_position']}; roster flag {o['on_40man']}.",
            '', '| Season | League | PA | K | UBB | HR |', '|---|---|---:|---:|---:|---:|']
        for h in c['source_history']:
            lines.append(f"| {h['season']} | {h['bucket']} | {h['plate_appearances']} | {h['strike_outs']} | {h['unintentional_walks']} | {h['home_runs']} |")
        if not c['source_history']:lines.append('| — | No captured batting history | — | — | — | — |')
        lines += ['','Rates in opportunity inputs use fixed 100-opportunity event priors, with separate leagues.',
            'Three-year pooled counts use weights 1, 0.8 and 0.6. No new park/opponent adjustment or Statcast is introduced.']
        for bucket in ['MLB','AAA']:
            history=[h for h in c['source_history'] if h['bucket']==bucket]
            n=sum([1.,.8,.6][o['origin_year']-h['season']]*h['strike_outs'] for h in history)
            d=sum([1.,.8,.6][o['origin_year']-h['season']]*h['plate_appearances'] for h in history)
            actual=c['actual_inputs'][f'pooled_{bucket}_K']
            assert np.isclose((n+23)/(d+100),actual)
            lines.append(f"{bucket} pooled K: ({n:.2f} + 23) / ({d:.2f} + 100) = {actual:.6f}. Missing exposure returns the fixed prior, not observed average ability.")
        h=c['context']
        lines += ['',f"Captured context: {h['availability_state']}; medical scope {h['il_scope']}; captured absence days {h['il_days730']}; no recovery certified.",
            '', '| Added input | Value | Participation support | Conditional PA support | Used in heads |',
            '|---|---:|---:|---:|---|']
        for feature in e.FEATURES:
            supports=[c['head_feature_support'][head][feature]['players'] for head in ['participation','conditional_pa']]
            enabled=[feature in [t['feature'] for t in c['heads'][head]['feature_effects']] for head in ['participation','conditional_pa']]
            cell=next(x for x in pre['cells'] if x['year']==o['origin_year'] and x['fold']==o['outer_fold'])
            in_fit=[feature in cell['features'][head] for head in ['participation','conditional_pa']]
            lines.append(f"| {feature} | {c['actual_inputs'][feature]:.3f} | {supports[0]} | {supports[1]} | enabled {in_fit}; on path {enabled} |")
        lines += ['','Eligible captured context records (may include versioned records):']
        for r in c['cutoff_records']:
            lines.append(f"- Known by record date {r['available_date']}; event {r['event_date']}: {r['description']}.")
        if not c['cutoff_records']:lines.append('- No captured eligible context. This is not evidence of health or lack of organizational interest.')
        lines += ['','| Intermediate or result | Baseline | Status candidate | Observed |',
            '|---|---:|---:|---:|',
            f"| Appearance probability | {o['repaired_p']:.2%} | {o['status_p']:.2%} | {int(o['next_pa']>0)} |",
            f"| PA conditional on any appearance | {o['repaired_conditional_pa']:.2f} | {o['status_conditional_pa']:.2f} | {'not observable at zero PA' if not o['next_pa'] else o['next_pa']} |",
            f"| Expected PA | {o['repaired_pa']:.2f} | {o['status_pa']:.2f} | {o['next_pa']} |",
            f"| Batting wins per 600 PA | {o['repaired_rate']:.3f} | {o['status_rate']:.3f} | "+(f"{o['next_batting_rate']:.3f} |" if o['next_pa'] else "unobserved |"),
            f"| Batting plus replacement | {o['repaired_value']:.3f} | {o['status_value']:.3f} | {o['next_value']:.3f} |",
            '','Expected PA is probability times conditional PA; offense is PA times (batting rate/600 plus origin replacement). Neither is full WAR.']
        for head,v in c['heads'].items():
            lines += ['',f"Actual saved {head} head: reference {v['reference']:.6f}, additive output {v['raw_prediction']:.6f}.",
                'Largest count-weighted tree-path terms (not causal attribution):']
            for term in v['feature_effects'][:5]:
                lines.append(f"- {term['feature']} = {term['input']:.6f}: {term['path_effect']:+.6f}.")
            terms=[t for t in v['feature_effects']if t['feature'].startswith('status_')]
            lines.append('Status path terms: '+('; '.join(f"{t['feature']} {t['path_effect']:+.6f}" for t in terms) if terms else 'none')+'.')
            lines.append(f"Fixed-fit neutralized-status probe: {c['fixed_fit_probes'][head]['status_signals_neutralized']:.6f}; not a healthy counterfactual or validated replacement.")
        lines += ['', 'Distinct profile support: '+', '.join(f"{x['head']} {x['profile_players']} people"for x in c['training_profile'])+'.',
            '',lookup[key],'','Origin-known peers (baseline to status expected PA, then actual):']
        for peer in c['peers']:
            lines.append(f"- {peer['player_name']}: {peer['repaired_pa']:.1f} to {peer['status_pa']:.1f}; {peer['next_pa']} actual.")
        lines.append('')
    lines += ['## Cohort and decision checks','',
        'Public common matches: PA RMSE 138.488 to 138.375, MAE 106.871 to 106.911; Steamer 135.379 and 92.083.',
        'Exact historical release dates remain unknown. The roughly 16 percent MAE gap remains outside the declared 15 percent practical target.',
        'All-row PA RMSE improves 0.091 PA, but batting-value RMSE slightly worsens. Nominal paired intervals include no whole-model improvement.',
        'The 2021-origin shortfall improves, while 2023-origin overforecast worsens. More accurate overall totals do not imply correct allocation.',
        'Keep the sources and diagnostics qualified; do not promote this as a material workload upgrade or reject injury/status modeling generally.',
        'Specific gaps: unsupported medical comebacks, unresolved legal restrictions, possible stale captured open injury state, and job uncertainty.']
    (e.OUT/'player-walkthrough.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    verification['player_walkthrough_status']='complete'
    e.write('verification.json',verification)
    report=dict(**verification,decision=notes['decision'],source_integrity='cutoff checks pass with publication and open-spell qualifications',
        profile_support='sparse medical and nonmedical intersections remain; kept in scoring',
        predictive='tiny PA change; no meaningful public MAE or delivered-value improvement',
        reasonability='known major return and restriction forecasts remain inadequate',
        deployment='not_authorized_not_changed',manual_review=str(e.ROOT/'config/practical_hitter_v59_case_notes.json'),
        input_hashes=pre['input_hashes'],output_hashes={str(e.OUT/n):sha256_file(e.OUT/n)for n in ['predictions.parquet','scores.json','intervals.json','cases.json','player-walkthrough.md','verification.json']})
    e.write('report.json',report)
    archive=e.ROOT/'reports/model-evidence/practical-hitter-opportunity-status-v59'
    archive.mkdir(parents=True,exist_ok=True)
    for name in ['scores.json','intervals.json','verification.json','player-walkthrough.md']:
        (archive/name).write_bytes((e.OUT/name).read_bytes())
    short=dict(decision=report['decision'],player_walkthrough_status='complete',cases=12,
        source_rows=pre['source_rows'],replayed_heads=70,input_hashes=report['input_hashes'],
        output_hashes=report['output_hashes'],source_audit=pre['source_audit'],
        source_publication_vintages_verified=False,protected_outcomes_used=False,
        frozen_forecast_changed=False,clinical_recovery_inferred=False,
        cells=[{k:c[k]for k in ['year','fold','feature_support','checks']}for c in pre['cells']])
    (archive/'evidence-manifest.json').write_text(json.dumps(short,indent=2,allow_nan=False)+'\n',encoding='utf8')
    print('All twelve actual player reviews saved. Workload upgrade withheld.',flush=True)


if __name__=='__main__':
    main()
