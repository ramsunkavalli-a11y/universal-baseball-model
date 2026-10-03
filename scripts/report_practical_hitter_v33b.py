"""Record completed player judgments separately from predictive success."""
import json
import numpy as np
import prepare_practical_hitter_v31 as r
from universal_baseball.storage import sha256_file

OUT=r.ROOT/'reports/generated/practical-hitter-v33b'

def main():
    verification=r.read(OUT/'verification.json');assert verification['saved_heads_replayed']==315
    cases=r.read(OUT/'cases.json');notes=r.read(r.ROOT/'config/practical_hitter_v33b_case_notes.json')
    decision=r.read(r.ROOT/'config/practical_hitter_v33b_decision.json')
    scores=r.read(OUT/'scores.json');intervals=r.read(OUT/'intervals.json')
    lines=['# Corrected practical hitter comparison and player review','',decision['summary'],'',
        'Targets: next-calendar-year MLB PA and batting-plus-replacement wins. Not full WAR, pure current minor-league talent, six club-control years or trade value. All 30,506 identities/non-arrivals retained; no 2026 outcomes or frozen forecast changes.','',
        '## What changed and what was repaired','',
        'Three-year actual event counts are pooled at 1/.8/.6 by source league before one fixed prior. Existing cutoff-known draft picks/attached school classes provide entry context; unavailable pedigree stays unknown. A linear diagnostic uses fixed physical scales rather than rare-league training standard deviations. Temporary-absence, foreign production, park/opponent and job-context gaps remain.',
        '', 'The earlier broad expansion wrongly admitted 597 incomplete origin-2020 training identities. Their absent roster capture became listing zero. Those rows are now explicitly excluded from every training set, not deleted from source history or testing. All later candidate fits AND a matched direct control were refitted. Original V31/V32 and interrupted V33 artifacts remain qualified/preserved. Earlier results cannot be called adopted gains.',
        '', '## Scores on identical populations','',
        '| Scope / model | PA RMSE | PA MAE | Batting + replacement RMSE | Value MAE |','|---|---:|---:|---:|---:|']
    for g in scores[:5]:
        for a,v in g['scores'].items():lines.append(f"| {g['scope']} / {a} | {v['pa_rmse']:.2f} | {v['pa_mae']:.2f} | {v['value_rmse']:.5f} | {v['value_mae']:.5f} |")
    lines.extend(['',decision['statistics'],'',
        'Public forecasts have different preseason/December knowledge dates; their raw-count conversion uses origin environment versus realized target environment. Converted value has a substantial mean offset. Do not infer superior pure batting-talent accuracy from that loss. Older N has different fitting provenance; it remains a demanding reference, not an isolated causal comparison.','',
        '## All-origin totals and reasonability','',
        '| Origin | Actual PA | Pooled PA gap | Draft PA gap | Control PA gap | Actual value | Linear assembly value gap |',
        '|---|---:|---:|---:|---:|---:|---:|'])
    for g in scores:
        if not g['scope'].startswith('origin_'):continue
        v=g['scores'];lines.append(f"| {g['scope']} | {g['actual_pa']:.0f} | {v['pooled']['pa_total']-g['actual_pa']:.0f} | {v['pedigree']['pa_total']-g['actual_pa']:.0f} | {v['repaired_direct']['pa_total']-g['actual_pa']:.0f} | {g['actual_value']:.2f} | {v['safe_ridge']['value_total']-g['actual_value']:.2f} |")
    lines.extend(['',decision['baseball_limits'],'',
        '## Player walkthroughs','',
        'Fixed diagnostic identities plus each arm’s largest gain/harm against the corrected direct control, false high/low, ordinary partial-workload example and the largest linear rate. Origin-only nearest peers also include draft-knownness/rank/college background. Selected outcomes diagnose mechanics, not independent validation.',''])
    for c in cases:
        o=c['origin'];key=f"{o['player_name']}|{o['origin_year']}";assert key in notes,key
        lines.extend([f"### {o['player_name']} — {o['origin_year']} → {o['target_year']}",'',
            'Selection: '+'; '.join(c['selection'])+'.','',
            f"Inputs: age {o['age']:g}, MLB PA {o['pa_0']}/{o['pa_1']}/{o['pa_2']}, current observed quality {o['quality_0']:.4f}, pooled MLB quality {o['pooled_mlb_quality']:.4f}; captured listing {o['on_40man']} (not certified rights). Draft known {o['draft_known']}, year {o['draft_year']}, pick {o['pick_number']}, class {o['draft_school_class'] or 'unknown'}, rank {o['draft_rank']:.4f}, rank × low-exposure {o['draft_rank_low_exposure']:.4f}.",'',
            '| Source year | League | PA | HR | K | Unintentional walks |','|---|---|---:|---:|---:|---:|'])
        for h in c['raw_level_history']:lines.append(f"| {h['season']} | {h['bucket']} | {h['plate_appearances']} | {h['home_runs']} | {h['strike_outs']} | {h['unintentional_walks']} |")
        lines.extend(['','| Model | Expected PA | Expected batting + replacement | Weighted conditional rate* |','|---|---:|---:|---:|'])
        for arm in ['repaired_direct','pooled','pedigree','pooled_product','pedigree_product','safe_ridge']:
            rate=o.get(arm+'_rate');lines.append(f"| {arm} | {o[arm+'_pa']:.2f} | {o[arm+'_value']:.4f} | {'—' if rate is None else f'{rate:.4f}'} |")
        for arm in ['pooled','pedigree']:
            assert np.isclose(o[arm+'_product_value'],o[arm+'_pa']*(o[arm+'_rate']/600+o['origin_replacement_rate']),atol=1e-10)
        lines.extend(['',f"Actual: {o['next_pa']} PA / {o['next_value']:.4f} batting-plus-replacement wins. *Rate is conditional on future activity and contribution weighted; it is not a current prospect grade.",'',
            'Saved-fit unknown-pedigree probe: '+json.dumps(c['pedigree_neutral_probe'])+'. Artificial input probe, not a causal effect or independently validated replacement forecast.','',notes[key],'',
            'Peers selected without future outcomes: '+'; '.join(f"{p['player_name']} (age {p['age']:g}, current MLB {p['pa_0']} PA, draft pick {p['pick_number']}; actual next {p['next_pa']} PA / {p['next_value']:.2f})" for p in c['comparisons'])+'.','',
            'Training profile support: '+'; '.join(f"{h['head']}={h['profile_players']} distinct people" for h in c['conditional_support'])+'.','',
            'Actual pooled transformations (weighted count + 100 × prior)/(weighted opportunities + 100):','',
            '| League / event | Weighted events | Weighted opportunities | Prior | Actual input |','|---|---:|---:|---:|---:|'])
        for h in c['pooled_transformations']:
            lines.append(f"| {h['bucket']} / {h['event']} | {h['weighted_events']:.2f} | {h['weighted_opportunities']:.2f} | {h['prior']:.4f} | {h['input']:.6f} |")
        lines.extend(['','Largest saved linear contributions (fixed physical scales, not learned tiny SD):','',
            '| Feature | Raw | Fixed scaled | Coefficient | Contribution |','|---|---:|---:|---:|---:|'])
        for t in c['safe_ridge_terms']['terms']:lines.append(f"| {t['feature']} | {t['raw']:.5f} | {t['fixed_scaled']:.5f} | {t['coefficient']:.5f} | {t['contribution']:.5f} |")
        lines.extend(['',f"Linear intercept: {c['safe_ridge_terms']['intercept']:.6f}. Full feature vectors and source/fit paths are in the machine-readable cases. No changed model parameters in the diagnostic probe.",''])
    lines.extend(['## Disposition','',decision['disposition'],'',decision['next_step'],'',
        '315 saved heads replay, including 135 reused identical early heads and 180 new fits. Input hashes and every evaluation target/identity stay fixed. Unit/source checks and completed player review are separate from predictive success and deployment approval.'])
    path=OUT/'player-walkthrough.md';path.write_text('\n'.join(lines)+'\n',encoding='utf8')
    report=dict(player_walkthrough_status='complete',cases=len(cases),player_walkthrough_artifact=str(path),player_walkthrough_sha256=sha256_file(path),
        verification=verification,disposition=decision['disposition'],next_step=decision['next_step'],practical_model_goal_complete=False,
        predictive_certification=False,protected_outcomes_used=False,frozen_forecast_changed=False,
        source_training_repair_complete=True,notes_sha256=sha256_file(r.ROOT/'config/practical_hitter_v33b_case_notes.json'))
    (OUT/'report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    verification.update(player_walkthrough_status='complete',player_walkthrough_sha256=sha256_file(path))
    (OUT/'verification.json').write_text(json.dumps(verification,indent=2),encoding='utf8')
    print('Completed player review:',len(cases),'cases. Goal is not automatically completed.')

if __name__=='__main__':main()
