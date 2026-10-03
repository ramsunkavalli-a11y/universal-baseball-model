"""Complete origin-domain review without concealing unchanged prospect failures."""
import polars as pl
import evaluate_hitter_domains_v39 as e
from universal_baseball.storage import sha256_file


def main():
    r=e.previous.s.r;cases=r.read(e.OUT/'cases.json');path_notes=r.ROOT/'config/practical_hitter_v39_case_notes.json';notes=r.read(path_notes)
    verification=r.read(e.OUT/'verification.json');assert len(cases)==len(notes)==17 and verification['replayed_heads']==35
    support=pl.read_parquet(e.OUT/'support.parquet');lines=['# V39: completed current-MLB workload walkthrough','',
        'Expected next-calendar-year MLB PA. Future exits are included in training, and the head is chosen only from positive origin MLB PA. Nine fixed cases plus PA/value gains, harms, false highs/lows and ordinary cases; non-MLB predictions remain exactly unchanged. Same strongest batting-rate head. No protected 2026.','',
        'Exact tree-path accounting reconstructs each saved prediction but is order/correlation dependent, not SHAP or causal feature attribution. Origins, profiles and comparison distance never use subsequent success. Medical/job analogues are not supplied merely by same-stage/exposure peers.','']
    for c in cases:
        o=c['origin'];key=f"{o['player_name']}|{o['origin_year']}";assert key in notes
        lines.extend([f"## {o['player_name']}: {o['origin_year']} → {o['target_year']}",'','Selection: '+'; '.join(c['selection'])+'.','',
            f"Age {o['age']:g}, current stage {o['stage']}, source position {o['source_position']}, soft roster listing {o['on_40man']}; draft pick {o['pick_number']} ({o['draft_school_class'] or 'unknown'}). Actual head: {c['candidate_head']}.",'',
            '| Year | League | PA | Games | HR | K | UBB |','|---|---|---:|---:|---:|---:|---:|'])
        for h in c['source_history']:lines.append(f"| {h['season']} | {h['bucket']} | {h['plate_appearances']} | {h['games_played']} | {h['home_runs']} | {h['strike_outs']} | {h['unintentional_walks']} |")
        lines.extend(['','Actual game/role inputs: '+', '.join(f'{k}={v:.5g}' for k,v in c['actual_features'].items() if k.startswith(('games_','role_')))+'.','',
            '| Forecast | PA | Batting wins/600 | Batting + replacement wins |','|---|---:|---:|---:|'])
        for a in ['safe_ridge','cohort','games','domain']:lines.append(f"| {a} | {o[a+'_pa']:.3f} | {o[a+'_rate']:.5f} | {o[a+'_value']:.5f} |")
        lines.extend([f"| Actual | {o['next_pa']} | {o['next_batting_rate']:.5f} | {o['next_value']:.5f} |",'',
            f"Fixed batting rate; contribution = PA × (rate/600 + origin replacement {o['origin_replacement_rate']:.8f}). Not full WAR or joint uncertainty.",''])
        for label,a in [('Shared workload',c['benchmark_path_accounting']),('Origin-domain workload',c['candidate_path_accounting'])]:
            lines.extend([f"{label}: reference {a['reference']:.4f}, raw prediction {a['raw_prediction']:.4f}.",'',
                '| Path feature | Actual input | Accounting effect (PA) |','|---|---:|---:|'])
            for t in a['feature_effects'][:12]:lines.append(f"| {t['feature']} | {t['input']:.5f} | {t['path_effect']:.5f} |")
            lines.append('')
        lines.extend([notes[key],'',
            'Origin-selected comparisons: '+'; '.join(f"{p['player_name']} (age {p['age']:g}, MLB/AAA/AA PA {p['pa_0']}/{p['AAA_0_pa']}/{p['AA_0_pa']}; shared→domain→actual PA {p['games_pa']:.1f}→{p['domain_pa']:.1f}→{p['next_pa']}; realized contribution {p['next_value']:.3f})" for p in c['peers'])+'.',''])
        sup=support.filter(pl.col('row_id')==o['row_id'])
        lines.extend([f"Dedicated training profile: {sup['mlb_profile_players'][0]} distinct people." if len(sup) else 'No dedicated current-MLB head: unchanged previously reviewed shared-head support applies.',''])
    lines.extend(['## Disposition','',
        'Do not adopt this domain-specific head. Public workload RMSE/MAE and delivered value worsen versus the shared games head; whole-cohort changes are small/uncertain. Some comeback/debut gains accompany genuine harmful losses to young regulars and prior accurate forecasts. The branch cannot address first arrival or missed-season returns. This rejects this fixed branch/settings, not the idea that role retention differs from first arrival.','',
        'Close this workload branch batch and retain the established coherent baseline plus the games challenger visibly. Next reassess compatible park/opponent-adjusted contact/PBP winner inputs for the broad batting target. Do not keep making arbitrary PA subgroup branches or event-prior changes, and do not use favorable anecdotes as validation.'])
    path=e.OUT/'player-walkthrough.md';path.write_text('\n'.join(lines)+'\n',encoding='utf8')
    verification.update(player_walkthrough_status='complete',walkthrough_sha256=sha256_file(path));e.write('verification.json',verification)
    e.write('report.json',dict(player_walkthrough_status='complete',cases=17,adopted=False,predictive_improvement_established=False,
        practical_model_goal_complete=False,notes_sha256=sha256_file(path_notes),walkthrough_sha256=sha256_file(path),
        protected_outcomes_used=False,frozen_forecast_changed=False,noncurrent_mlb_bit_exact=True))
    print('17 player reviews complete; dedicated current-MLB head not adopted.')


if __name__=='__main__':main()
