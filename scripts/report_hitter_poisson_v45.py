"""Render the fourteen completed source/link/outcome reviews; no new fitting."""
import evaluate_hitter_poisson_v45 as e
from universal_baseball.storage import sha256_file


def main():
    cases=e.r.read(e.OUT/'cases.json');p=e.ROOT/'config/practical_hitter_poisson_v45_case_notes.json';notes=e.r.read(p)
    assert len(cases)==len(notes)==14
    lines=['# Count-link hitter model: fourteen actual player reviews','',
        'Next-calendar-year MLB PA and batting-plus-replacement contribution, not full WAR. Only the PA loss/link changes; batting estimates and availability policies are fixed. Cases include fixed diagnostics and largest gains, harms, false highs/lows and ordinary errors. Peers are selected using origin information, not later success.','']
    for c in cases:
        o=c['origin'];key=f"{o['player_id']}|{o['origin_year']}";assert key in notes
        lines.extend([f"## {o['player_name']} {o['origin_year']} to {o['target_year']}",'',
            f"Player {o['player_id']}, row {o['row_id']}; selected as {', '.join(c['selection'])}; age {o['age']}, {o['stage']}.",'',
            '| Season | Level | PA | Games | HR | K | BB |','|---|---|---:|---:|---:|---:|---:|'])
        for h in c['source_history']:lines.append(f"| {h['season']} | {h['bucket']} | {h['plate_appearances']} | {h['games_played']} | {h['home_runs']} | {h['strike_outs']} | {h['unintentional_walks']} |")
        lines.extend(['','| Forecast | Expected PA | Fixed batting wins/600 | Contribution |','|---|---:|---:|---:|'])
        for a in ['retired_games','poisson']:lines.append(f"| {a} | {o[a+'_pa']:.4f} | {o['cohort_rate']:.5f} | {o[a+'_value']:.6f} |")
        lines.extend([f"| Actual | {o['next_pa']} | {'unobserved at zero PA' if not o['next_pa'] else o['next_batting_rate']} | {o['next_value']:.6f} |",'',
            f"Contribution arithmetic: expected PA × ({o['cohort_rate']:.6f}/600 + {o['origin_replacement_rate']:.8f}). Candidate raw mean {c['count_accounting']['unbounded_mean_pa']:.6f}; raw log prediction {c['count_accounting']['raw_log_prediction']:.6f}. Retirement/permanent availability policies are identical.",'',
            'All 239 actual inputs and the exact two fitted-head traces are preserved in cases.json. Largest path effects below are descriptive tree accounting, not causal explanations. Candidate terms are additive in LOG mean, not additive PA. Missing-level role and rate defaults are not actual player measurements.','',
            '| Input | Actual encoded value | Identity-link path PA effect |','|---|---:|---:|'])
        for term in c['control_accounting']['feature_effects'][:8]:lines.append(f"| {term['feature']} | {term['input']} | {term['path_effect']:.6f} |")
        lines.extend(['','| Input | Actual encoded value | Count-link path LOG effect |','|---|---:|---:|'])
        for term in c['count_accounting']['feature_effects'][:8]:lines.append(f"| {term['feature']} | {term['input']} | {term['path_effect']:.6f} |")
        lines.extend(['',f"Distinct-player profile support: {c['training_profile']}. Actual mature-fold chronology support: {c['training_support']}.",'',notes[key],'',
            '| Origin-selected peer | Age | Origin MLB PA | Minor PA | Games mean PA | Count mean PA | Actual PA | Actual contribution |','|---|---:|---:|---:|---:|---:|---:|---:|'])
        for n in c['peers']:lines.append(f"| {n['player_name'] or n['player_id']} | {n['age']} | {n['pa_0']} | {n['minor_pa_0']} | {n['retired_games_pa']:.2f} | {n['poisson_pa']:.2f} | {n['next_pa']} | {n['next_value']:.5f} |")
        lines.append('')
    lines.extend(['## Disposition','',
        'Reject this fixed count-link candidate as a working-model replacement. Overall PA and contribution worsen, all seven origin PA errors worsen, public workload does not improve, and player gains coexist with consequential harms and offsetting errors. This does not reject every count model or prove the existing baseline complete. Keep V33b plus reversible retirement as the research working assembly, with V38 a separate games candidate. Do not attach a Poisson variance, arrival probability or calibrated risk claim. No next-model decision was made before completing these fourteen reviews. Protected 2026 outcomes and frozen/deployed forecasts remain unchanged.'])
    out=e.OUT/'player-walkthrough.md';out.write_text('\n'.join(lines)+'\n',encoding='utf8')
    v=e.r.read(e.OUT/'verification.json');v.update(player_walkthrough_status='complete',manual_notes_sha256=sha256_file(p),walkthrough_sha256=sha256_file(out));e.write('verification.json',v)
    e.write('report.json',dict(player_walkthrough_status='complete',cases=14,candidate_promoted=False,disposition='reject fixed Poisson loss/link replacement',
        working_assembly='V33b plus V44 reversible retirement',public_mae_tolerance_pass=False,practical_goal_complete=False,
        protected_outcomes_used=False,frozen_forecast_changed=False,manual_notes_sha256=sha256_file(p),walkthrough_sha256=sha256_file(out)))
    print('Fourteen source-to-forecast reviews complete; count-link replacement rejected, no risk claims.')


if __name__=='__main__':main()
