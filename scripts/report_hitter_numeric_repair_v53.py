"""Require concrete case judgments and archive the corrected source milestone."""
from pathlib import Path
import shutil
import numpy as np
import evaluate_hitter_numeric_repair_v53 as e
from universal_baseball.storage import sha256_file


def main():
    cases=e.read(e.OUT/'cases.json');notes_path=e.ROOT/'config/practical_hitter_numeric_repair_v53_case_notes.json';notes=e.read(notes_path)
    assert set(notes)=={f"{c['origin']['player_id']}|{c['origin']['origin_year']}" for c in cases}
    assert all(len(n)>300 for n in notes.values())
    scores=e.read(e.OUT/'scores.json');verification=e.read(e.OUT/'verification.json');assert verification['replayed_heads']==105
    pre=e.read(e.OUT/'preflight.json');assert all(sha256_file(Path(p))==h for p,h in pre['input_hashes'].items())
    lines=['# Numeric history correction and actual player reviews','',
        'Ten source-to-forecast reviews complete. Same 30,506 historical forecasts, original chronological player folds and 105 saved/replayed heads. Numeric source repair is retained; it is not a material forecasting breakthrough or deployment approval. Protected 2026 remains untouched.','',
        'Reconstruction uses only origin and two earlier seasons with weights 1/.8/.6. Seven count rates per league keep the original 100-PA/opportunity neutral prior. No park/opponent adjustment is added. Time since draft is (origin minus dated draft year)/10 with an explicit float type; unknown is separately flagged. All other inputs and training labels are unchanged. New actual scoring uses the common origin environment, not the older target-centered units.','',
        '| Scope | Rows | Old PA RMSE | Corrected PA RMSE | Old hitting RMSE | Corrected hitting RMSE | Old offense RMSE | Corrected offense RMSE |','|---|---:|---:|---:|---:|---:|---:|---:|']
    for s in scores[:7]:
        a,b=s['scores']['old'],s['scores']['repaired'];r,t=s['rates']['old'],s['rates']['repaired']
        lines.append(f"| {s['scope']} | {s['rows']} | {a['pa_rmse']:.3f} | {b['pa_rmse']:.3f} | {r['rmse']:.4f} | {t['rmse']:.4f} | {a['value_rmse']:.5f} | {b['value_rmse']:.5f} |")
    lines += ['', 'Rates are actual-PA weighted among future MLB participants, with equal target-year weight; workload/offense retain non-arrivals. Rate units are fixed-event batting wins/600, not official wOBA or neutralized latent talent. Offense includes replacement but no fielding, position or running. Public snapshots have unknown exact dates. No superiority claim.','',
        'Fixed cases precede fits. Outcome-selected gain, harm, false high/low and ordinary cases are diagnostics, not independent confirmation. Four peers per case use origin year, stage, prior debut, age, minor exposure and draft rank without future outcomes; they are not equally talented or equally healthy. Profile counts are distinct training people in broad intersections, not proof of sufficiency.','']
    for c in cases:
        o=c['origin'];key=f"{o['player_id']}|{o['origin_year']}"
        lines += [f"## {o['player_name']} from {o['origin_year']} to {o['target_year']}",'',
            f"Player {o['player_id']}, row {o['row_id']}, fold {o['outer_fold']}; age {o['age']}, stage {o['stage']}. Selection: {', '.join(c['selection'])}.",'',
            '| Season | Level | PA | HR | K | UBB |','|---|---|---:|---:|---:|---:|']
        for h in c['source_history']:lines.append(f"| {h['season']} | {h['bucket']} | {h['plate_appearances']} | {h['home_runs']} | {h['strike_outs']} | {h['unintentional_walks']} |")
        lines += ['',f"Dated draft year {o['draft_year']}, pick {o['pick_number']}, source class {o['draft_school_class'] or 'unknown'}. No additional school/college evidence is collected.",'',
            '| Reconstructed input | Old | Corrected |','|---|---:|---:|']
        for n in pre['source_changes']:
            z=c['numeric_changes_and_probes'][n['feature']];lines.append(f"| {n['feature']} | {z['old']} | {z['repaired']} |")
        lines += ['', '| Forecast | MLB probability | PA if active | Expected PA | Batting wins per 600 | Offense wins |','|---|---:|---:|---:|---:|---:|',
            f"| Old | {o['old_p']:.6f} | {o['binary_scout_conditional_pa']:.6f} | {o['old_pa']:.6f} | {o['old_rate']:.6f} | {o['old_value']:.6f} |",
            f"| Corrected | {o['repaired_p']:.6f} | {o['repaired_conditional_pa']:.6f} | {o['repaired_pa']:.6f} | {o['repaired_rate']:.6f} | {o['repaired_value']:.6f} |",
            f"| Actual | {'1' if o['next_pa'] else '0'} | Not a forecast | {o['next_pa']} | {format(o['next_batting_rate'],'.6f') if o['next_pa'] else 'unobserved'} | {o['next_value']:.6f} |",'',
            f"Corrected product = {o['repaired_p']:.9f} × {o['repaired_conditional_pa']:.9f} PA × ({o['repaired_rate']:.9f}/600 + {o['origin_replacement_rate']:.9f}). All input fields, exact tree paths and Ridge sums are saved in cases.json.",'']
        for head,t in c['heads'].items():
            assert np.isfinite(t['raw_prediction']);terms=t['feature_effects'][:5]
            lines += [f"{head}: reference {t['reference']:.9f}, reconstructed raw output {t['raw_prediction']:.9f}. Largest fitted terms:", '']
            for z in terms:
                effect=z.get('effect',z.get('path_effect'));lines.append(f"- {z['feature']}: input {z['input']:.9f}, additive fitted contribution {effect:.9f}.")
            probe=c['numeric_changes_and_probes'][head]
            lines += ['',f"Same corrected fit with old numeric inputs: {probe['same_repaired_fit_with_old_inputs']:.9f}. This isolates input-path sensitivity from parameter refitting; it is not causal attribution or a validated alternative.",'']
        lines += ['Broad training-profile counts: '+', '.join(f"{p['head']} {p['profile_players']} distinct people" for p in c['training_profile'])+'.','',notes[key],'',
            '| Origin selected peer | Old PA | Corrected PA | Actual PA | Corrected rate | Actual rate |','|---|---:|---:|---:|---:|---:|']
        for p in c['peers']:lines.append(f"| {p['player_name']} | {p['old_pa']:.2f} | {p['repaired_pa']:.2f} | {p['next_pa']} | {p['repaired_rate']:.4f} | {format(p['next_batting_rate'],'.4f') if p['next_pa'] else 'unobserved'} |")
        lines.append('')
    lines += ['## Decision after review','',
        'Keep the explicit floating-point source repair for subsequent candidate construction, preserving the old candidate. A tiny score improvement cannot establish practical success. Full PA RMSE is 60.686 versus 60.650; common-origin offense RMSE .45383 versus .45387. Public broad hitting RMSE is 1.74350 versus old 1.74524, Steamer 1.77459 and ZiPS 1.75336; PA MAE 106.87 versus Steamer 92.08 still fails the practical 15% tolerance.','',
        'Nominal full-population offense MSE change is -.0000400, interval [-.0004472,+.0003667]; PA MSE change +4.290, interval [-3.085,+10.794]. Conditional rate MSE improves -.005068, interval [-.009666,-.000973], but prospect-only rates worsen slightly and do not establish an overall value win. All are development intervals after repeated historical testing.','',
        'Upper never-debut expected PA falls 73,989 to 73,593 against 92,891 actual, and expected arrivals remain about 593 against 730 actual. Lower never-debut still allocates 7,652 PA against 5,194. Public exact archive timing, 218 roster-only qualifications, park/opponent treatment and joint value uncertainty remain open. The source defect is real, but it does not explain away the missed fast entrants.','',
        'Next: one prospect-readiness alternative that shares strength across closely related level/exposure/pedigree profiles, using the corrected source and both entrants and non-arrivals. Do not fit a separate tiny Kurtz-like leaf on zero conditional examples, hand-boost named stars, or switch to another general algorithm tournament. Also preserve the known establishment/availability gap rather than pretending a prospect-only change can solve public MLB workload.']
    path=e.OUT/'player-walkthrough.md';path.write_text('\n'.join(lines)+'\n',encoding='utf8')
    verification.update(player_walkthrough_status='complete',notes_sha256=sha256_file(notes_path),walkthrough_sha256=sha256_file(path));e.write('verification.json',verification)
    e.write('report.json',dict(player_walkthrough_status='complete',cases=len(cases),source_repair_retained=True,
        material_predictive_gain=False,fast_entry_solved=False,full_hitter_goal_complete=False,
        frozen_forecast_changed=False,protected_outcomes_used=False,heads=105,
        evidence_hashes={str(p.relative_to(e.ROOT)):sha256_file(p) for p in [notes_path,path,e.OUT/'scores.json',e.OUT/'intervals.json',e.OUT/'scored-predictions.parquet']}))
    dest=e.ROOT/'reports/model-evidence/practical-hitter-numeric-repair-v53';dest.mkdir(parents=True,exist_ok=True)
    for name in ['source-reconciliation.json','verification.json','report.json','scores.json','intervals.json','cases.json','player-walkthrough.md','fit-report.json']:
        shutil.copy2(e.OUT/name,dest/name)
    e.write('preflight-summary.json',dict(cells=35,heads=105,checks=[dict(year=c['year'],fold=c['fold'],heads=c['repair_preflight']) for c in pre['cells']],
        input_hashes=pre['input_hashes'],protected_outcomes_used=False))
    shutil.copy2(e.OUT/'preflight-summary.json',dest/'preflight-summary.json')
    print('Ten actual player reviews complete; source correction retained, predictive breakthrough not claimed.',flush=True)


if __name__=='__main__':main()
