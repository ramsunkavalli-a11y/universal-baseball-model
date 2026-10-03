"""Review every fallback choice and preserve component offsets and cohort harms."""
import evaluate_hitter_scouting_v48 as e
from universal_baseball.storage import sha256_file


def main():
    cases=e.old.r.read(e.OUT/'cases.json');p=e.ROOT/'config/practical_hitter_scouting_v48_case_notes.json';notes=e.old.r.read(p);assert len(cases)==len(notes)==20
    prior=e.old.r.read(e.ROOT/'config/practical_hitter_scouting_v47_case_notes.json')
    lines=['# Positive historical scouting and production fallback player review','',
        'Twenty actual cases compare the original count/games mean, unrestricted ranking mean and the positive-rank fallback against next-calendar-year MLB reality. The model gate selects the ranking head for 450 verified current listings and preserves count-only means for all other 30,056 players. No refits, target-based selection or manual name exceptions. These are repeated, exposed development tests—not an independent confirmation.','',
        'Target units are MLB PA and batting-plus-replacement wins, not full WAR, immediate MLB-equivalent talent, trade value or six years of control. Rates are the unchanged PA-weighted future-MLB head. All original source fields, 251 inputs and full paths/support are in cases.json. Peers use only origin age/stage/debut/exposure/quality/rank; they need not match draft pedigree. Outcome-selected extrema are diagnostics. The two lower-minor cases were added as explicit follow-up to the aggregate calibration failure, without changing any predictor or prediction.','']
    for c in cases:
        o=c['origin'];key=f"{o['player_id']}|{o['origin_year']}";assert key in notes
        lines.extend([f"## {o['player_name']} {o['origin_year']} to {o['target_year']}",'',
            f"Player {o['player_id']}; row {o['row_id']}; fold {o['outer_fold']}; age {o['age']}; {o['stage']}, snapshot {o['snapshot_level']}. Selected as {', '.join(c['selection'])}.",'',
            '| Season | Level | PA | Source games | HR | K | UBB |','|---|---|---:|---:|---:|---:|---:|'])
        for h in c['source_history']:lines.append(f"| {h['season']} | {h['bucket']} | {h['plate_appearances']} | {h['games_played']} | {h['home_runs']} | {h['strike_outs']} | {h['unintentional_walks']} |")
        lines.extend(['','Origin source ranks: '+str(c['source_ranks'])+'.','', 'Actual twelve added inputs: '+str(c['added_inputs'])+'.','',
            f"Positive current listing: {o['positive_rank_gate']}. Selected saved head: {c['selected_head']}. Source edition qualifications and original partial/unknown-list policies carry forward.",'',
            '| Forecast | Expected MLB PA | Fixed batting wins per 600 | Batting plus replacement |','|---|---:|---:|---:|'])
        for a in ['retired_games','scout','fallback']:lines.append(f"| {a} | {o[a+'_pa']:.5f} | {o['cohort_rate']:.6f} | {o[a+'_value']:.6f} |")
        lines.extend([f"| Actual | {o['next_pa']} | {'Unobserved at zero PA' if not o['next_pa'] else o['next_batting_rate']} | {o['next_value']:.6f} |",'',
            f"Fallback contribution = {o['fallback_pa']:.6f} × ({o['cohort_rate']:.6f}/600 + {o['origin_replacement_rate']:.8f}). Working V33b is separately scored with its different rate, not silently mixed.",''])
        for name,title in [('control_accounting','Count model'),('scout_accounting','Ranking model')]:
            t=c[name];terms=t['feature_effects'][:8]+[x for x in t['feature_effects'][8:] if x['feature'].startswith('scout_')]
            lines.extend([f'### {title} path accounting','',f"Reference {t['reference']:.6f} plus the full saved path terms = raw PA {t['raw_prediction']:.6f}. Clipping/availability then yields its displayed mean. Descriptive accounting is not a causal decomposition between refitted models.",'',
                '| Input | Encoded value | Path PA accounting |','|---|---:|---:|'])
            for x in terms:lines.append(f"| {x['feature']} | {x['input']} | {x['path_effect']:.6f} |")
            lines.append('')
        lines.extend([f"General profile: {c['training_profile']}. Rank-specific distinct-player support: {c['rank_profile']}. Actual original-fold support: {c['training_support']}.",'',notes[key],''])
        if key in prior:lines.extend(['Earlier unrestricted-ranking interpretation (retained, not presented as the new fallback output): '+prior[key],''])
        lines.extend(['| Origin selected peer | Age | MLB PA | Minor PA | Listed | Rank score | Count PA | Rank PA | Actual PA | Actual contribution |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|'])
        for q in c['peers']:lines.append(f"| {q['player_name'] or q['player_id']} | {q['age']} | {q['pa_0']} | {q['minor_pa_0']} | {q['scout_listed_0']} | {q['scout_rank_score_0']} | {q['retired_games_pa']:.3f} | {q['scout_pa']:.3f} | {q['next_pa']} | {q['next_value']:.5f} |")
        lines.append('')
    lines.extend(['## Decision after review','',
        'The fallback prevents new harm to unlisted rising/drafted prospects and retains valuable ranked readiness gains. Broad PA and contribution nominal intervals favor the games control, but public PA MAE remains 20.1 percent above Steamer. The lower-minor total worsens to 12,315 versus 6,072 actual, and 2023-origin PA totals rise to 194,137 versus 182,194 actual. Mayer, Salas, Brinson and Frazier keep real false-high/delay risk. These failures block whole-model adoption despite excellent pooled total PA.','',
        'Retain the explicit fallback as research evidence, not a promoted forecast. Do not erase Devers to make the lower group pass or claim every high-quality prospect is MLB-ready. The substantive remaining issue is learning readiness separately from eventual talent, with actual level/sample/age support and correctly conditioned opportunity. A later bounded architecture comparison can use binary MLB participation plus conditional PA on the already audited rank/count panel, rather than another arbitrary gate or more library sweeps. It must include the no-ranking counterpart, source-supported lower-level players and false highs, and cannot silently replace a six-year value system. Current protected forecast and working assembly remain unchanged; practical goal incomplete.'])
    out=e.OUT/'player-walkthrough.md';out.write_text('\n'.join(lines)+'\n',encoding='utf8')
    v=e.old.r.read(e.OUT/'verification.json');v.update(player_walkthrough_status='complete',cases=20,notes_sha256=sha256_file(p),walkthrough_sha256=sha256_file(out));e.write('verification.json',v)
    e.write('report.json',dict(player_walkthrough_status='complete',cases=20,research_fallback_retained=True,whole_model_adopted=False,working_replaced=False,
        practical_goal_complete=False,public_mae_tolerance_pass=False,cohort_reasonability_pass=False,profile_certification_pass=False,
        post_review_development_design=True,protected_outcomes_used=False,frozen_forecast_changed=False,notes_sha256=sha256_file(p),walkthrough_sha256=sha256_file(out)))
    print('Twenty actual fallback reviews complete; research retained, cohort/public gaps block promotion.',flush=True)


if __name__=='__main__':main()
