"""Close the game-role comparison after actual manual baseball reviews."""
import polars as pl
import evaluate_hitter_games_v38 as e
from universal_baseball.storage import sha256_file


def main():
    cases=e.s.r.read(e.OUT/'cases.json');note_path=e.s.r.ROOT/'config/practical_hitter_v38_case_notes.json';notes=e.s.r.read(note_path)
    verification=e.s.r.read(e.OUT/'verification.json');assert len(cases)==len(notes)==15 and verification['replayed_heads']==35
    support=pl.read_parquet(e.OUT/'role-support.parquet')
    lines=['# V38: completed games/role player walkthrough','',
        'Same historical rows/folds and unchanged batting head. Six fixed cases plus the largest PA/value gains, harms, false highs/lows and ordinary cases. Source-level review was completed before fitting. Every forecast head replays. Team game counts are not starts or healthy days. No protected 2026 outcomes.','',
        'Path accounting exactly reconstructs raw tree predictions from a count-weighted node reference and split-path effects. It is order/correlation dependent, not SHAP, a causal game effect, a fixed-feature ablation or an independent forecast. Refitting also changes the old features\' mapping. Peers use origin year/stage/debut, age, PA and draft inputs, never later outcomes.','']
    for c in cases:
        o=c['origin'];key=f"{o['player_name']}|{o['origin_year']}";assert key in notes
        lines.extend([f"## {o['player_name']}: {o['origin_year']} → {o['target_year']}",'','Selection: '+'; '.join(c['selection'])+'.','',
            f"Age {o['age']:g}; stage {o['stage']}; source position {o['source_position']}; draft pick {o['pick_number']}, class {o['draft_school_class'] or 'unknown'}; soft roster listing {o['on_40man']}.",'',
            '| Year | League | PA | Games | HR | K | UBB |','|---|---|---:|---:|---:|---:|---:|'])
        for h in c['source_history']:lines.append(f"| {h['season']} | {h['bucket']} | {h['plate_appearances']} | {h['games_played']} | {h['home_runs']} | {h['strike_outs']} | {h['unintentional_walks']} |")
        lines.extend(['','New workload inputs: '+', '.join(f'{k}={v:.5g}' for k,v in c['actual_new_inputs'].items() if k.startswith(('games_','role_')))+'.','',
            '| Forecast | MLB PA | Batting wins/600 | Batting + replacement wins |','|---|---:|---:|---:|'])
        for a in ['cohort','safe_ridge','games']:lines.append(f"| {a} | {o[a+'_pa']:.3f} | {o[a+'_rate']:.5f} | {o[a+'_value']:.5f} |")
        lines.extend([f"| Actual | {o['next_pa']} | {o['next_batting_rate']:.5f} | {o['next_value']:.5f} |",'',
            f"Fixed batting head; contribution = PA × (rate/600 + replacement {o['origin_replacement_rate']:.8f}). Not full WAR or joint uncertainty.",''])
        for label,account in [('Old workload',c['benchmark_path_accounting']),('Games workload',c['candidate_path_accounting'])]:
            lines.extend([f"{label}: reference {account['reference']:.4f}, raw prediction {account['raw_prediction']:.4f}, games/role path effects {account['game_feature_effect']:.4f}.",'',
                '| Path feature | Actual input | Accounting effect (PA) |','|---|---:|---:|'])
            for t in account['feature_effects'][:12]:lines.append(f"| {t['feature']} | {t['input']:.5f} | {t['path_effect']:.5f} |")
            lines.append('')
        lines.extend([notes[key],'',
            'Origin-selected peers: '+'; '.join(f"{p['player_name']} (MLB/AAA/AA PA {p['pa_0']}/{p['AAA_0_pa']}/{p['AA_0_pa']}; control→games→actual PA {p['cohort_pa']:.1f}→{p['games_pa']:.1f}→{p['next_pa']}; realized value {p['next_value']:.3f})" for p in c['peers'])+'.','',
            f"Games/role training profile: {support.filter(pl.col('row_id')==o['row_id'])['role_profile_players'][0]} distinct players. This sparse-profile diagnostic does not certify medical/job-context support.",''])
    lines.extend(['## Disposition','',
        'Retain as a promising research workload extension, not a promoted working forecast. All-cohort PA improves, upper-minor totals and brief-debut PA improve, but public MAE remains worse than V33b, value gains are small/uncertain, 2023 cohort over-allocation grows and major newcomer/return cases remain missed. Do not drop it as useless; do not claim it finishes the hitter model.','',
        'The remaining question is workload architecture: one shared population learner may underrepresent the different use/retention process of current MLB hitters. Next test one origin-known current-MLB workload head, keeping the existing non-MLB head and same batting rate/cohorts/settings. This is not future-outcome gating or a new algorithm sweep.'])
    path=e.OUT/'player-walkthrough.md';path.write_text('\n'.join(lines)+'\n',encoding='utf8')
    verification.update(player_walkthrough_status='complete',walkthrough_sha256=sha256_file(path));e.write('verification.json',verification)
    e.write('report.json',dict(player_walkthrough_status='complete',cases=15,adopted=False,retain_as_research=True,
        practical_model_goal_complete=False,batting_head_bit_exact=True,notes_sha256=sha256_file(note_path),walkthrough_sha256=sha256_file(path),
        public_mae_tolerance_pass=False,whole_value_improvement_established=False,protected_outcomes_used=False,frozen_forecast_changed=False))
    print('15 player reviews complete; retain games/role as research, no working-model promotion.')


if __name__=='__main__':main()
