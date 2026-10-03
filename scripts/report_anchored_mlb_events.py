"""Complete the anchor-repair review, not a success declaration."""
import polars as pl
import evaluate_anchored_mlb_events as e
from universal_baseball.storage import sha256_file


def main():
    cases=e.old.r.read(e.OUT/'cases.json');path_notes=e.old.r.ROOT/'config/practical_hitter_v37_case_notes.json'
    notes=e.old.r.read(path_notes);verification=e.old.r.read(e.OUT/'verification.json')
    assert len(cases)==len(notes)==15 and verification['saved_heads_replayed']==35
    support=pl.read_parquet(e.OUT/'support.parquet')
    lines=['# Empirical MLB anchor and learned event adjustment review','',
        'Same V36 144 features/likelihood/settings and fixed V34 workload. The only model repair is a direct own-MLB-count offset, with mature-target league transport during training. All earlier predictions remain byte-exact. No protected 2026 outcomes or frozen changes.','',
        'Eleven fixed diagnostics plus largest value gain/harm, false high/low and ordinary example. Peers use only origin-known stage/debut/age/exposure/quality/draft/college inputs, not future outcomes.','']
    for c in cases:
        o=c['origin'];key=f"{o['player_name']}|{o['origin_year']}";assert key in notes
        lines.extend([f"## {o['player_name']}: {o['origin_year']} to {o['target_year']}",'',
            'Selection: '+'; '.join(c['selection'])+'.','',
            f"Age {o['age']:g}; draft {o['pick_number']}/{o['draft_school_class'] or 'unknown'}; actual weighted MLB exposure {c['weighted_mlb_exposure']:.3f}, anchor reliability {c['anchor_reliability']:.5f}. Counts use 1/.8/.6 and one fixed 100-opportunity league prior; no schedule-inflated batting evidence.",'',
            '| Source year | League | Actual PA | HR | K | Unintentional walks |','|---|---|---:|---:|---:|---:|'])
        for h in c['source_history']:lines.append(f"| {h['season']} | {h['bucket']} | {h['plate_appearances']} | {h['home_runs']} | {h['strike_outs']} | {h['unintentional_walks']} |")
        lines.extend(['','Prediction logits = log(empirical origin anchor) + learned effect, then joint softmax. Rate conversion subtracts completed-origin league environment, not the anchor or future environment.','',
            '| Event | League reference | Own anchor | Naked model | Learned odds effect | New probability | Actual count | Wins/600 contribution |','|---|---:|---:|---:|---:|---:|---:|---:|'])
        for z in c['events']:lines.append(f"| {z['event']} | {z['origin_environment']:.6f} | {z['anchor']:.6f} | {z['naked_model']:.6f} | {z['linear_odds_effect']:.5f} | {z['predicted']:.6f} | {z['actual_target_count']:.0f} | {z['batting_wins_per600_contribution']:.5f} |")
        lines.extend(['','Event-value contributions sum to conditional batting wins/600 under the existing fixed neutral weights/scale and ten runs/win. Other/K have zero direct weight but affect the probability allocation.','',
            '| Model | Fixed PA | Conditional batting wins/600 | Batting + replacement wins |','|---|---:|---:|---:|'])
        for a in ['cohort','event','anchor_only','anchored']:lines.append(f"| {a} | {o[a+'_pa']:.3f} | {o[a+'_rate']:.5f} | {o[a+'_value']:.5f} |")
        lines.extend([f"| Actual | {o['next_pa']} | {o['next_batting_rate']:.5f} | {o['next_value']:.5f} |",'',
            f"Product = fixed PA × (rate/600 + origin replacement {o['origin_replacement_rate']:.7f}). Actual trained distinct active people {c['saved_fit']['training_players']}; optimizer {c['saved_fit']['optimizer']}.",'',
            'Largest actual odds terms (K, UBB, HBP, 1B, 2B, 3B, HR):','',
            '| Feature | Fixed scaled | Effects in event order |','|---|---:|---|'])
        for z in c['top_log_odds_terms']:lines.append(f"| {z['feature']} | {z['fixed_scaled']:.5f} | "+', '.join(f'{v:.5f}' for v in z['effects'].values())+' |')
        lines.extend(['',notes[key],'',
            'Origin-selected peers: '+'; '.join(f"{p['player_name']} (age {p['age']:g}, MLB/AAA/AA PA {p['pa_0']}/{p['AAA_0_pa']}/{p['AA_0_pa']}; actual next {p['next_pa']} PA/{p['next_value']:.3f} wins)" for p in c['peers'])+'.','',
            'Profile support: '+'; '.join(f"{h['head']}={h['profile_players']} distinct people" for h in support.filter(pl.col('row_id')==o['row_id']).to_dicts())+'.',''])
    lines.extend(['## Decision','',
        'Do not adopt this fixed 100-prior empirical anchor plus residual model. It repairs established power representation and improves the naked model overall, but loses to the actual working control on conditional rates/value, especially brief debuts. Keep the mathematical source/likelihood infrastructure and negative evidence; reject this specification, not all empirical component anchors.','',
        'Current V33b remains working hitter forecast. The broad practical goal is incomplete. Pause further event reweighting in this batch; next inspect available games/role evidence for workload, the outstanding public MAE and cohort allocation gap. A failed component experiment must not erase the stronger existing batting forecast.'])
    path=e.OUT/'player-walkthrough.md';path.write_text('\n'.join(lines)+'\n',encoding='utf8')
    verification.update(player_walkthrough_status='complete',player_walkthrough_sha256=sha256_file(path));e.write('verification.json',verification)
    e.write('report.json',dict(player_walkthrough_status='complete',cases=15,player_walkthrough_artifact=str(path),
        player_walkthrough_sha256=sha256_file(path),notes_sha256=sha256_file(path_notes),verification=verification,
        adopted=False,predictive_improvement_established=False,practical_model_goal_complete=False,
        protected_outcomes_used=False,frozen_forecast_changed=False))
    print('15 anchor-to-events-to-runs reviews complete; fixed specification not adopted.')


if __name__=='__main__':main()
