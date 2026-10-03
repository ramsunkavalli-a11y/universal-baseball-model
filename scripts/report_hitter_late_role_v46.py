"""Complete all eighteen player reviews before selecting a working forecast."""
import evaluate_hitter_late_role_v46 as e
from universal_baseball.storage import sha256_file


def main():
    cases=e.r.read(e.OUT/'cases.json');p=e.ROOT/'config/practical_hitter_late_role_v46_case_notes.json';notes=e.r.read(p);assert len(cases)==len(notes)==18
    lines=['# Late-season opportunity: eighteen actual player reviews','',
        'Next-calendar-year MLB expected PA and batting-plus-replacement contribution, not full WAR. Same batting head, identities, availability policies and learner settings; ten reliable MLB PA-timing features are added. The new window-game predictors were withheld before fits under the source amendment. Peers are selected by origin age/workload/quality, not outcomes.','',
        'Tree-path terms exactly reconstruct each fitted forecast but are descriptive, not causal. Their sum inside the new fit is not a decomposition of the old-to-new change, because all trees are refitted. All 249 actual inputs and full saved traces are preserved in cases.json.','']
    for c in cases:
        o=c['origin'];key=f"{o['player_id']}|{o['origin_year']}";assert key in notes
        lines.extend([f"## {o['player_name']} {o['origin_year']} to {o['target_year']}",'',
            f"Player {o['player_id']}, row {o['row_id']}; {', '.join(c['selection'])}; age {o['age']}, {o['stage']}.",'',
            '| Season | Level | PA | Source games | HR | K | BB |','|---|---|---:|---:|---:|---:|---:|'])
        for h in c['source_history']:lines.append(f"| {h['season']} | {h['bucket']} | {h['plate_appearances']} | {h['games_played']} | {h['home_runs']} | {h['strike_outs']} | {h['unintentional_walks']} |")
        lines.extend(['','| Season | Annual MLB PA | Preceding window PA | Late window PA | Preceding average team games | Late average team games |','|---|---:|---:|---:|---:|---:|'])
        for w in c['source_windows']:lines.append(f"| {w['season']} | {w['annual_pa']} | {w['preceding_pa']} | {w['late_pa']} | {w['preceding_team_games']:.5f} | {w['late_team_games']:.5f} |")
        if not c['source_windows']:lines.append('| Certified no own MLB PA within captured years | 0 | 0 | 0 | Year-level denominators preserved | Year-level denominators preserved |')
        lines.extend(['','Actual added inputs: '+str(c['added_inputs'])+'.','',
            '| Forecast | PA | Unchanged batting wins/600 | Contribution |','|---|---:|---:|---:|'])
        for a,rate in [('retired_games','cohort_rate'),('late','late_rate'),('retired_safe_ridge','safe_ridge_rate')]:lines.append(f"| {a} | {o[a+'_pa']:.4f} | {o[rate]:.5f} | {o[a+'_value']:.6f} |")
        lines.extend([f"| Actual | {o['next_pa']} | {'unobserved at zero PA' if not o['next_pa'] else o['next_batting_rate']} | {o['next_value']:.6f} |",'',
            f"Candidate raw mean {c['late_accounting']['raw_prediction']:.6f}, bounded/availability-adjusted mean {o['late_pa']:.6f}. Contribution = {o['late_pa']:.6f} × ({o['cohort_rate']:.6f}/600 + {o['origin_replacement_rate']:.8f}). Old working rate differs from the fixed V34/V38 rate and is shown as a separate complete assembly, not silently mixed.",''])
        for keytrace,title in [('control_accounting','Games control'),('late_accounting','Late-role candidate')]:
            lines.extend([f'### {title}: exact path accounting','',f"Reference {c[keytrace]['reference']:.6f} plus all full-record path terms = raw PA {c[keytrace]['raw_prediction']:.6f}.",'',
                '| Input | Actual encoded value | Path PA accounting |','|---|---:|---:|'])
            terms=c[keytrace]['feature_effects'][:8]
            terms=terms+[t for t in c[keytrace]['feature_effects'][8:] if t['feature'].startswith('late_usage')]
            for t in terms:lines.append(f"| {t['feature']} | {t['input']} | {t['path_effect']:.6f} |")
            lines.append('')
        lines.extend([f"Old distinct-player profile: {c['training_profile']}. Late-stage/debut/age/exposure profile: {c['late_profile']}. Actual mature fold support: {c['training_support']}.",'',notes[key],'',
            '| Origin-selected comparison | Age | Origin MLB PA | Minor PA | Games mean PA | Late mean PA | Actual PA | Actual contribution |','|---|---:|---:|---:|---:|---:|---:|---:|'])
        for n in c['peers']:lines.append(f"| {n['player_name'] or n['player_id']} | {n['age']} | {n['pa_0']} | {n['minor_pa_0']} | {n['retired_games_pa']:.2f} | {n['late_pa']:.2f} | {n['next_pa']} | {n['next_value']:.5f} |")
        lines.append('')
    lines.extend(['## Reviewed decision','',
        'Retain the reliable timing source and this modestly improved broad-population point candidate as research. Do not replace the working assembly or frozen/deployed forecast: incremental games-control intervals include no improvement, public PA MAE is worse than working V33b and far above Steamer, the 2021-origin workload error worsens and never-debut upper minors slightly deteriorate. Strong late-debut mechanism examples do not override those groups. Source execution passes are not predictive certification. The practical goal remains incomplete. All eighteen reviews are complete before a next-model choice.'])
    out=e.OUT/'player-walkthrough.md';out.write_text('\n'.join(lines)+'\n',encoding='utf8')
    v=e.r.read(e.OUT/'verification.json');v.update(player_walkthrough_status='complete',manual_notes_sha256=sha256_file(p),walkthrough_sha256=sha256_file(out));e.write('verification.json',v)
    e.write('report.json',dict(player_walkthrough_status='complete',cases=18,source_reviews=9,source_usable=True,research_candidate_retained=True,working_replaced=False,
        practical_goal_complete=False,public_mae_tolerance_pass=False,cohort_reasonability_pass=False,profile_certification_pass=False,
        source_eligibility_qualified=True,protected_outcomes_used=False,frozen_forecast_changed=False,manual_notes_sha256=sha256_file(p),walkthrough_sha256=sha256_file(out)))
    print('Eighteen actual player reviews complete; retain timing research, no working/frozen promotion.',flush=True)


if __name__=='__main__':main()
