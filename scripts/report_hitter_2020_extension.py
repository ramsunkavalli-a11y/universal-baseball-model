"""Close source-extension review without converting completion into success."""
import json
import polars as pl
import evaluate_hitter_2020_extension as e
from universal_baseball.storage import sha256_file


def main():
    cases=e.r.read(e.OUT/'cases.json')
    notes_path=e.r.ROOT/'config/practical_hitter_v34_case_notes.json'
    notes=e.r.read(notes_path);verify=e.r.read(e.OUT/'verification.json')
    assert verify['replayed_new_heads']==40
    assert len(cases)==len(notes)==15
    support=pl.read_parquet(e.OUT/'support.parquet')
    lines=['# Reconstructed 2020 training cohort: player review','',
        'The same 199 features, model settings and 30,506 evaluation rows are retained. Only the training population changes. All case input vectors are unchanged; later fitted partitions, linear coefficients and equal-origin training weights can change. Targets are next-year MLB PA and batting-plus-replacement wins, not full WAR.','',
        'Fixed diagnostic cases plus affected largest gain/harm, false high/low and ordinary example. Lux 2023 is explicitly an additional after-scoring missed-season contrast. Peers use only origin information; their later results are displayed, not used for selection.','']
    for c in cases:
        o=c['origin'];key=f"{o['player_name']}|{o['origin_year']}";assert key in notes
        lines.extend([f"## {o['player_name']}: {o['origin_year']} to {o['target_year']}",'',
            'Selection: '+'; '.join(c['selection'])+'.','',
            f"Age {o['age']:g}; observed MLB PA current/prior/older {o['pa_0']}/{o['pa_1']}/{o['pa_2']}; pooled MLB quality {o['pooled_mlb_quality']:.5f}; soft captured listing {o['on_40man']}; known draft {o['draft_known']}, pick {o['pick_number']}. No new focal-player input is introduced.",'',
            '| Source year | League | PA | HR | K | Unintentional walks |','|---|---|---:|---:|---:|---:|'])
        for h in c['source_history']:lines.append(f"| {h['season']} | {h['bucket']} | {h['plate_appearances']} | {h['home_runs']} | {h['strike_outs']} | {h['unintentional_walks']} |")
        lines.extend(['','| Forecast | PA | Conditional batting wins/600 | Batting + replacement wins |','|---|---:|---:|---:|'])
        for a in ['safe_ridge','cohort']:lines.append(f"| {a} | {o[a+'_pa']:.3f} | {o[a+'_rate']:.5f} | {o[a+'_value']:.5f} |")
        lines.extend([f"| Actual | {o['next_pa']} | {o['next_batting_rate']:.5f} | {o['next_value']:.5f} |",'',
            f"Value arithmetic: new PA × (new conditional batting rate/600 + origin replacement {o['origin_replacement_rate']:.7f}). This product is not a joint uncertainty distribution.",'',
            f"Fold {o['outer_fold']}; {c['added_training_people']} distinct origin-2020 training people. Rate fit maximum target year {c['saved_rate_model']['maximum_target_year']}; saved fit hash {c['saved_rate_model']['sha256']}.",'',
            'Profile support: '+'; '.join(f"{h['head']}={h['profile_players']} distinct training people" for h in support.filter(pl.col('row_id')==o['row_id']).to_dicts())+'.','',
            'Saved linear intercept: '+str(c['linear_intercept'])+'. Largest actual scaled terms:','',
            '| Feature | Raw | Fixed scaled | Coefficient | Contribution |','|---|---:|---:|---:|---:|'])
        for t in c['linear_terms']:lines.append(f"| {t['feature']} | {t['raw']:.5f} | {t['fixed_scaled']:.5f} | {t['coefficient']:.7f} | {t['contribution']:.5f} |")
        lines.extend(['',notes[key],'','Origin-selected peers: '+'; '.join(f"{p['player_name']}, age {p['age']:g}, origin MLB {p['pa_0']} PA, draft pick {p['pick_number']}: next {p['next_pa']} PA/{p['next_value']:.3f} wins" for p in c['peers'])+'.',''])
    lines.extend(['## Disposition','',
        'Keep the reconstructed source population and cancellation/missingness handling. Do not claim an established predictive gain or replace the working forecast: overall and public workload error slightly worsen, contribution differences are uncertain, and cohort/entry/absence problems remain. Use this repaired-source assembly as the fixed control for subsequent research while keeping V33b visible. No frozen forecast, protected 2026 outcomes or deployed explorer changes.','',
        'Next: one exposure/reliability representation test, rather than another algorithm tournament. In particular, a long upper-minor record and tiny MLB debut must coexist without assuming either source is infallible.'])
    path=e.OUT/'player-walkthrough.md';path.write_text('\n'.join(lines)+'\n',encoding='utf8')
    verify.update(player_walkthrough_status='complete',player_walkthrough_sha256=sha256_file(path))
    e.write('verification.json',verify)
    e.write('report.json',dict(player_walkthrough_status='complete',cases=len(cases),
        player_walkthrough_artifact=str(path),player_walkthrough_sha256=sha256_file(path),
        notes_sha256=sha256_file(notes_path),source_repair_retained=True,
        predictive_improvement_established=False,practical_model_goal_complete=False,
        protected_outcomes_used=False,frozen_forecast_changed=False,verification=verify))
    print('15 player walkthroughs complete. Source retained; predictive gain not established.')


if __name__=='__main__':main()
