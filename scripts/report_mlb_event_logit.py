"""Complete event-to-runs player evidence before choosing the next experiment."""
import polars as pl
import evaluate_mlb_event_logit as e
from universal_baseball.storage import sha256_file


def main():
    cases=e.old.r.read(e.OUT/'cases.json');notes_path=e.old.r.ROOT/'config/practical_hitter_v36_case_notes.json'
    notes=e.old.r.read(notes_path);verification=e.old.r.read(e.OUT/'verification.json')
    assert len(cases)==len(notes)==13 and verification['saved_heads_replayed']==35
    support=pl.read_parquet(e.OUT/'support.parquet')
    lines=['# MLB event logit model player review','',
        'Next-year eight-event MLB count likelihood, 144 source-count/context inputs, explicit mature-training league offsets and completed-origin prediction offsets. Legacy batting-value quality and workload predictors excluded. Same evaluation players and V34 expected PA. Physically coherent probabilities are not automatically a useful batting forecast.','',
        'Ten fixed diagnostics plus largest delivered-value gain/harm, false high/low and ordinary example. Peers use only origin stage/debut/age/MLB and upper-minor workload/quality/draft rank/college status. Outcome-selected cases are diagnosis, not independent confirmation.','']
    for c in cases:
        o=c['origin'];key=f"{o['player_name']}|{o['origin_year']}";assert key in notes
        lines.extend([f"## {o['player_name']}: {o['origin_year']} to {o['target_year']}",'',
            'Selection: '+'; '.join(c['selection'])+'.','',
            f"Age {o['age']:g}; draft pick {o['pick_number']}, class {o['draft_school_class'] or 'unknown'}; captured listing {o['on_40man']} is soft. Full actual model features and saved fit are in cases.json; no individual target count/environment enters forecast inputs.",'',
            '| Source year | League | PA | HR | K | Unintentional walks |','|---|---|---:|---:|---:|---:|'])
        for h in c['source_history']:lines.append(f"| {h['season']} | {h['bucket']} | {h['plate_appearances']} | {h['home_runs']} | {h['strike_outs']} | {h['unintentional_walks']} |")
        lines.extend(['','Each logit is log(origin league probability) + fitted linear effect; softmax gives eight probabilities summing to one. Other is the anchored category.','',
            '| Event | Origin league probability | Linear odds effect | Forecast probability | Actual next count | Batting wins/600 contribution |','|---|---:|---:|---:|---:|---:|'])
        for z in c['events']:lines.append(f"| {z['event']} | {z['origin_environment']:.6f} | {z['linear_odds_effect']:.5f} | {z['predicted']:.6f} | {z['actual_target_count']:.0f} | {z['batting_wins_per600_contribution']:.5f} |")
        lines.extend(['','The contribution column uses existing neutral event values divided by wOBA scale and ten runs/win; sum equals the predicted batting rate. K/other affect other probabilities but have zero direct wOBA weight.','',
            '| Model | Fixed PA | Conditional batting wins/600 | Batting + replacement wins |','|---|---:|---:|---:|'])
        for a in ['cohort','event']:lines.append(f"| {a} | {o[a+'_pa']:.3f} | {o[a+'_rate']:.5f} | {o[a+'_value']:.5f} |")
        lines.extend([f"| Actual | {o['next_pa']} | {o['next_batting_rate']:.5f} | {o['next_value']:.5f} |",'',
            f"Final product: fixed PA × (rate/600 + origin replacement {o['origin_replacement_rate']:.7f}). Saved numerical fit: {c['saved_fit']['optimizer']}; {c['saved_fit']['training_players']} distinct active training people.",'',
            'Largest actual linear-effect terms (columns K, UBB, HBP, 1B, 2B, 3B, HR):','',
            '| Feature | Fixed scaled | Effects in event order |','|---|---:|---|'])
        for z in c['top_log_odds_terms']:lines.append(f"| {z['feature']} | {z['fixed_scaled']:.5f} | "+', '.join(f'{v:.5f}' for v in z['effects'].values())+' |')
        lines.extend(['',notes[key],'',
            'Origin-selected peers: '+'; '.join(f"{p['player_name']} (age {p['age']:g}, MLB/AAA/AA PA {p['pa_0']}/{p['AAA_0_pa']}/{p['AA_0_pa']}, draft {p['pick_number']}/{p['draft_school_class'] or 'unknown'}; actual {p['next_pa']} PA/{p['next_value']:.3f} wins)" for p in c['peers'])+'.','',
            'Profile support: '+'; '.join(f"{h['head']}={h['profile_players']} distinct people" for h in support.filter(pl.col('row_id')==o['row_id']).to_dicts())+'.',''])
    lines.extend(['## Decision','',
        'Do not adopt this naked event-logit model. Proper count likelihood improves over a league-only null, but batting rate/value regress and elite power is implausibly compressed. The exact specification is rejected, not coherent component forecasting as a family. Preserve all negative evidence and V33b/V34 controls.','',
        'Next bounded hypothesis: give the event model a direct empirical own-MLB-count anchor, then learn residual adjustments instead of reconstructing established batting from scratch. Keep the same conditional likelihood/settings/context and fixed workload; do not silently retune the penalty or famous-player outcomes.'])
    path=e.OUT/'player-walkthrough.md';path.write_text('\n'.join(lines)+'\n',encoding='utf8')
    verification.update(player_walkthrough_status='complete',player_walkthrough_sha256=sha256_file(path));e.write('verification.json',verification)
    e.write('report.json',dict(player_walkthrough_status='complete',cases=13,player_walkthrough_artifact=str(path),
        player_walkthrough_sha256=sha256_file(path),notes_sha256=sha256_file(notes_path),verification=verification,
        adopted=False,predictive_improvement_established=False,practical_model_goal_complete=False,
        protected_outcomes_used=False,frozen_forecast_changed=False))
    print('13 complete event-to-runs cases. Naked event model not adopted.')


if __name__=='__main__':main()
