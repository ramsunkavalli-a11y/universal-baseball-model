"""Complete the source-policy walkthrough before declaring the repair retained."""
import evaluate_hitter_retirement_v44 as e
from universal_baseball.storage import sha256_file


def main():
    cases=e.read(e.OUT/'cases.json');p=e.ROOT/'config/practical_hitter_retirement_v44_case_notes.json';notes=e.read(p)
    assert len(cases)==len(notes)==17
    lines=['# Dated retirement repair player review','',
        'Review all fourteen reported-retirement rows plus three fixed unchanged cases. These are following-calendar-year MLB workload and batting-plus-replacement targets, not full WAR. No fitted parameters change. All original inputs and old forecasts are saved; the policy affects delivered opportunity, not estimated hitting talent. Comparisons are selected by same origin and stage, then age/workload/quality distance, without using later outcomes.','']
    for c in cases:
        o=c['origin'];key=f"{o['player_id']}|{o['origin_year']}";assert key in notes
        lines.extend([f"## {o['player_name']} {o['origin_year']} to {o['target_year']}",'',
            f"Player {o['player_id']}, row {o['row_id']}; {c['selection']}; age {o['age']}, stage {o['stage']}. Origin evidence bridge {o['origin_evidence_bridge']}.",'',
            '| Season | Level | PA | HR | K | BB |','|---|---|---:|---:|---:|---:|'])
        for h in c['source_history']:lines.append(f"| {h['season']} | {h['bucket']} | {h['plate_appearances']} | {h['home_runs']} | {h['strike_outs']} | {h['unintentional_walks']} |")
        if not c['source_history']:lines.append('| No own observed batting within window | Unknown | — | — | — | — |')
        lines.extend(['','Inputs are unchanged: separate level counts, stabilized event rates and 1/.8/.6 recency. The new source status is '+str(c['status'])+'.','',
            '| Assembly | Original PA | Repaired PA | Original contribution | Repaired contribution | Unchanged batting wins/600 |','|---|---:|---:|---:|---:|---:|'])
        for a in e.ARMS:lines.append(f"| {a} | {o[a+'_pa']:.3f} | {o['retired_'+a+'_pa']:.3f} | {o[a+'_value']:.5f} | {o['retired_'+a+'_value']:.5f} | {o[a+'_rate']:.5f} |")
        lines.extend([f"| Actual | {o['next_pa']} | {o['next_pa']} | {o['next_value']:.5f} | {o['next_value']:.5f} | {'not observed at zero PA' if not o['next_pa'] else o['next_batting_rate']} |",'',
            'Intermediates: unresolved recorded retirement gives an availability multiplier of zero; otherwise one. Original contribution equals PA × (batting wins/600 / 600 + origin replacement rate). No hitting-rate revision, retraining, rescaling or injury inference occurs.','',notes[key],'',
            '| Origin-selected comparison | Age | Origin PA | Original to repaired expected PA | Actual PA | Actual contribution |','|---|---:|---:|---|---:|---:|'])
        for n in c['peers']:lines.append(f"| {n['player_name'] or n['player_id']} | {n['age']} | {n['pa_0']} | {n['safe_ridge_pa']:.2f} to {n['retired_safe_ridge_pa']:.2f} | {n['next_pa']} | {n['next_value']:.4f} |")
        lines.append('')
    lines.extend(['## Source and return limits','',
        'All fourteen flagged rows actually have zero following-year MLB PA, but they represent only ten people. That observed result is not proof retirement is irreversible or a calibrated zero comeback probability. Unit tests confirm a later eligible signing or retirement-list return clears the state and a backdated future event cannot affect an earlier forecast. Actual retirement-return pairs are not established by this small evaluated subset. The existing transaction captures have incomplete minor/foreign coverage and lack archived publication snapshots. Ortiz and Posey are independently cross-checked against dated primary announcements.','',
        'An opt-out, IL activation, release, free agency or mere roster page does not trigger this retirement policy. Unverified roster-only players stay in every original headline comparison and remain source-qualified.','',
        'Retain this reversible reported-retirement policy in the working research assembly. The public-matched workload error is unchanged; the practical hitter goal remains incomplete. Frozen 2026 and deployed forecasts remain unchanged.'])
    out=e.OUT/'player-walkthrough.md';out.write_text('\n'.join(lines)+'\n',encoding='utf8')
    v=e.read(e.OUT/'verification.json');v.update(player_walkthrough_status='complete',manual_notes_sha256=sha256_file(p),walkthrough_sha256=sha256_file(out));e.write('verification.json',v)
    e.write('report.json',dict(player_walkthrough_status='complete',cases=17,retirement_rows=14,distinct_retired_players=10,
        policy_retained_in_research=True,permanent_ineligibility_asserted=False,retirement_comeback_calibrated=False,
        working_assembly='V33b with V44 reversible reported-retirement policy',public_mae_tolerance_pass=False,
        practical_goal_complete=False,source_eligibility_qualified=True,all_level_retirement_coverage=False,
        protected_outcomes_used=False,frozen_forecast_changed=False,manual_notes_sha256=sha256_file(p),walkthrough_sha256=sha256_file(out)))
    print('17 source-to-forecast player walks complete; retain the dated reversible rule, not a claim the public gap is solved.')


if __name__=='__main__':main()
