"""Finish actual readiness reviews before interpreting or exposing the experiment."""
import numpy as np
from universal_baseball.storage import sha256_file
import evaluate_hitter_readiness_v49 as e


def main():
    cases=e.old.r.read(e.OUT/'cases.json')
    path=e.ROOT/'config/practical_hitter_readiness_v49_case_notes.json'
    notes=e.old.r.read(path)
    keys={f"{c['origin']['player_id']}|{c['origin']['origin_year']}" for c in cases}
    assert len(cases)==31 and keys==set(notes)
    v=e.old.r.read(e.OUT/'verification.json');assert v['replayed_heads']==140
    lines=['# MLB participation and conditional workload: actual player review','',
        'Thirty-one actual cases, with full original inputs and node paths in cases.json. Selection includes the twenty fixed fallback cases plus each binary arm’s consequential PA/contribution gains, harms, false highs/lows and ordinary outcomes. These exposed historical tests are development evidence, not a new untouched validation set.','',
        'Target: next-calendar-year MLB PA and batting-plus-replacement contribution. No full WAR, present-day MLB-equivalent talent, trade value, service/control horizon or career distribution is estimated here. Both binary arms preserve every non-arrival. The batting rate is held fixed; a better contribution number can reflect offsetting workload and rate mistakes.','',
        'Inputs are three actual source years of separate-level counts, fixed shrinkage/recency, age, observed history, position, draft/roster evidence and games/use; the scouting arm adds twelve historical ranking fields. Missing history is not zero production. Models do not add park-neutral contact, tracking quality or diagnosed future injuries. Participation path terms are log odds; conditional-use path terms are PA. Both are descriptive accounting, not causal feature effects. Equal-origin weights are recomputed within each declared training population; the two fitted heads are not claimed to constitute one exact joint weighted distribution.','',
        'Peers were selected using origin age, stage, debut, exposure, quality and rank, not future outcomes. They need not match draft pedigree. Conditional support counts only distinct people whose active MLB outcome was already known in that earlier training fold. A large coarse group does not certify a rare fast-moving prospect.','']
    for c in cases:
        o=c['origin'];key=f"{o['player_id']}|{o['origin_year']}"
        lines += [f"## {o['player_name']} — {o['origin_year']} to {o['target_year']}",'',
            f"Player {o['player_id']}; row {o['row_id']}; fold {o['outer_fold']}; age {o['age']}; {o['stage']}; snapshot {o['snapshot_level']}. Selection: {', '.join(c['selection'])}.",'',
            '| Source year | Level | PA | Games | HR | K | UBB |','|---|---|---:|---:|---:|---:|---:|']
        for h in c['source_history']:
            lines.append(f"| {h['season']} | {h['bucket']} | {h['plate_appearances']} | {h['games_played']} | {h['home_runs']} | {h['strike_outs']} | {h['unintentional_walks']} |")
        lines += ['',f"Historical rank rows: {c['source_ranks']}. Source editions remain qualified; a complete-table absence is not a zero scouting grade. Partial/missing-table absence is unknown.",'',
            f"Draft known/year/pick: {o['draft_known']}/{o['draft_year']}/{o['pick_number']}; roster flag {o['on_40man']}; retirement {o['reported_retired']}; hard unavailable {o['hard_unavailable']}. Full 251 actual encoded inputs are persisted in cases.json.",'',
            '| Forecast | MLB probability | PA if active | Expected PA | Fixed batting wins / 600 | Contribution |','|---|---:|---:|---:|---:|---:|---:|']
        for a in ['retired_games','scout','fallback','binary_count','binary_scout']:
            p=f"{o[a+'_p']:.6f}" if a.startswith('binary') else 'Not estimated'
            pa=f"{o[a+'_conditional_pa']:.6f}" if a.startswith('binary') else 'Not estimated'
            lines.append(f"| {a} | {p} | {pa} | {o[a+'_pa']:.6f} | {o['cohort_rate']:.6f} | {o[a+'_value']:.6f} |")
        lines += [f"| Actual | {int(o['next_pa']>0)} | {'Unobserved' if not o['next_pa'] else o['next_pa']} | {o['next_pa']} | {'Unobserved' if not o['next_pa'] else o['next_batting_rate']} | {o['next_value']:.6f} |",'']
        for a in ['binary_count','binary_scout']:
            assert np.isclose(o[a+'_pa'],o[a+'_p']*o[a+'_conditional_pa'])
            assert np.isclose(o[a+'_value'],o[a+'_pa']*(o['cohort_rate']/600+o['origin_replacement_rate']))
            lines += [f"### {a}: probability and workload accounting",'',
                f"Effective probability {o[a+'_p']:.8f} × bounded conditional PA {o[a+'_conditional_pa']:.6f} = expected PA {o[a+'_pa']:.6f}. Contribution = that PA × ({o['cohort_rate']:.6f}/600 + {o['origin_replacement_rate']:.8f}). Raw probability {o[a+'_raw_p']:.8f} is preserved separately from any availability override.",'']
            for head in ['participation','conditional_pa']:
                t=c['heads'][a][head];unit='log odds' if head=='participation' else 'PA'
                assert np.isclose(t['reference']+sum(x['path_effect'] for x in t['feature_effects']),t['raw_prediction'])
                extra=f"; logistic link gives probability {t['linked_probability']:.8f}" if head=='participation' else '; then bound hypothetical PA to [1,800]'
                lines += [f"{head}: reference {t['reference']:.6f} plus all saved terms = raw {t['raw_prediction']:.6f} {unit}{extra}. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.",'',
                    '| Actual input | Encoded value | Path accounting |','|---|---:|---:|']
                terms=t['feature_effects'][:8]+[x for x in t['feature_effects'][8:] if x['feature'].startswith('scout_')]
                for x in terms:lines.append(f"| {x['feature']} | {x['input']} | {x['path_effect']:.6f} {unit} |")
                lines.append('')
        lines += [f"Full-population rank profile: {c['broad_rank_profile']}. Active-label conditional profile: {c['conditional_rank_profile']}.",'',
            f"Actual original-fold general support: {c['training_support']}.",'',notes[key],'',
            '| Origin-selected peer | Age | MLB PA | Minor PA | Rank score | Scouting probability | Conditional PA | Expected PA | Actual PA | Actual contribution |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
        for q in c['peers']:
            lines.append(f"| {q['player_name'] or q['player_id']} | {q['age']} | {q['pa_0']} | {q['minor_pa_0']} | {q['scout_rank_score_0']} | {q['binary_scout_p']:.5f} | {q['binary_scout_conditional_pa']:.2f} | {q['binary_scout_pa']:.2f} | {q['next_pa']} | {q['next_value']:.5f} |")
        lines.append('')
    lines += ['## Decision after the actual reviews','',
        'Retain both binary constructions as qualified research. The scouting binary has the best broad/public PA point scores in this reviewed batch, and the ranked-lower-minor expected PA excess falls from 3,769 to 1,044 versus 836 actual. Salas falls from the fallback’s 232 to 7, rather than equating a high ranking with immediate readiness. But ranked lower-minor arrival count is still low (5.55 expected versus nine observed), showing that a reasonable PA sum can conceal opposing probability/workload errors.','',
        'Upper never-debut PA is 73,989 versus 92,891 actual, and 593.7 expected participants versus 730 observed. Langford (47 versus 557 PA), Kurtz (2 versus 489) and Bellinger (14 versus 548) remain serious fast-entry misses. Preseason nonlisting is stale for new top draftees and rapidly advancing prospects. Brinson and Mayer remain false highs. Conditional profile support is particularly thin for ranked young players.','',
        'On the 1,789 identical public matches, PA RMSE is 142.11 versus Steamer 135.02, but MAE is 110.09 versus 92.40 (19.1% higher), missing the predeclared 15% practical MAE target. The public contribution comparison has an environment qualification and is not proof of superior talent. The fixed rate badly misses Judge/Votto/Bellinger and is not improved by this architecture test.','',
        'The origin-only roster/absence diagnostic is separately preserved. Current 400-PA players without a roster listing have almost exact total PA (60,954 versus 60,860) despite too-low participation, offset by conditional use. Therefore do not blanket-remove the roster signal. Prior regulars absent now remain underpredicted (2,052 versus 3,892), with Tatis a consequential miss. No future cause is inserted into a forecast.','',
        'No whole-model adoption, protected forecast change or goal completion. Complete the talent/population milestone in the controlling practical plan rather than another marginal workload gate/library sweep. Preserve these readiness models as explicit alternatives and the concrete prospect/absence failures; do not attach a six-year valuation claim to a one-year offense test.']
    out=e.OUT/'player-walkthrough.md';out.write_text('\n'.join(lines)+'\n',encoding='utf8')
    v.update(player_walkthrough_status='complete',cases=31,notes_sha256=sha256_file(path),walkthrough_sha256=sha256_file(out));e.write('verification.json',v)
    e.write('report.json',dict(player_walkthrough_status='complete',cases=31,research_binary_retained=True,whole_model_adopted=False,working_replaced=False,
        practical_goal_complete=False,public_pa_rmse_tolerance_pass=True,public_pa_mae_tolerance_pass=False,cohort_reasonability_pass=False,
        profile_certification_pass=False,protected_outcomes_used=False,frozen_forecast_changed=False,notes_sha256=sha256_file(path),walkthrough_sha256=sha256_file(out)))
    pre=e.old.r.read(e.OUT/'preflight.json')
    e.write('preflight-summary.json',dict(full_preflight_path=str(e.OUT/'preflight.json'),full_preflight_sha256=sha256_file(e.OUT/'preflight.json'),
        **{k:v for k,v in pre.items() if k!='cells'},cells=[{k:v for k,v in c.items() if k not in ['training_row_ids','test_row_ids']} for c in pre['cells']]))
    print('31 actual readiness reviews complete. Research retained; talent, readiness and public MAE gaps remain.',flush=True)


if __name__=='__main__':main()
