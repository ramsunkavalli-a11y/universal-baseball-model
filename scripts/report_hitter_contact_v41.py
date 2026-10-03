"""Complete real player reviews, preserving gains, harms and component cancellation."""
import math
import polars as pl
import evaluate_hitter_contact_v41 as e
from universal_baseball.storage import sha256_file


def main():
    cases=e.e.r.read(e.OUT/'cases.json');notes_path=e.e.r.ROOT/'config/practical_hitter_contact_v41_case_notes.json';notes=e.e.r.read(notes_path)
    verification=e.e.r.read(e.OUT/'verification.json');assert len(cases)==len(notes)==16 and verification['replayed_rate_heads']==60
    pre=e.e.r.read(e.OUT/'preflight.json');lines=['# V41: completed future-MLB contact player review','',
        'Same 30,506 historical rows, whole-player chronological folds, V34 workload and replacement rates. Conditional batting rate and delivered batting-plus-replacement are distinct. No protected 2026 outcomes. Sixty rate heads replay; 7,625 unsupported rows retain the exact baseline.','',
        'Coefficient/tree-path accounting exactly reconstructs each fitted rate. It is not a causal contact effect, SHAP or a fixed-input ablation; refitting changes the old feature mapping. The histogram candidate also changes architecture versus the ridge benchmark, so its loss cannot be attributed solely to contact. Source-measurement equivalence across levels remains uncertain. Origin-selected peers include later unsuccessful players.','']
    assert 30506-sum(c['contact_supported_rows'] for c in pre['cells'])==7625
    for c in cases:
        o=c['origin'];key=f"{o['player_name']}|{o['origin_year']}";assert key in notes
        lines.extend([f"## {o['player_name']}: {o['origin_year']} → {o['target_year']}",'','Selection: '+'; '.join(c['selection'])+'.','',
            f"Age {o['age']:.1f}; stage {o['stage']}; source position {o['source_position']}; draft pick {o['pick_number']}; contact-supported application {o['contact_supported']}.",'',
            '| Year | League | PA | K | UBB | HR |','|---|---|---:|---:|---:|---:|'])
        for h in c['batting_history']:lines.append(f"| {h['season']} | {h['bucket']} | {h['plate_appearances']} | {h['strike_outs']} | {h['unintentional_walks']} | {h['home_runs']} |")
        lines.extend(['','| Bucket | Weighted contacts | Measured/PA | Pull fly | GB share |','|---|---:|---:|---:|---:|'])
        for b in e.e.r.BUCKETS:
            a=c['actual_inputs']
            if not a[f'shape_{b}_available']:continue
            lines.append(f"| {b} | {math.expm1(a[f'shape_{b}_log_n']):.3f} | {a[f'shape_{b}_coverage']:.5f} | {a[f'shape_{b}_PULL_OFFB']:.5f} | {sum(a[f'shape_{b}_{d}_GB'] for d in ['PULL','CENTER','OPPO']):.5f} |")
        lines.extend(['','| Forecast | MLB PA | Batting wins/600 | Batting + replacement wins |','|---|---:|---:|---:|'])
        for a in ['cohort','contact_ridge','contact_hist']:lines.append(f"| {a} | {o[a+'_pa']:.3f} | {o[a+'_rate']:.5f} | {o[a+'_value']:.5f} |")
        lines.extend([f"| Actual | {o['next_pa']} | {o['next_batting_rate']:.5f} | {o['next_value']:.5f} |",'',
            f"Forecast contribution = fixed expected PA × (batting rate / 600 + origin replacement {o['origin_replacement_rate']:.8f}). This is not full WAR or a joint predictive distribution.",''])
        for label,account in [('Benchmark ridge',c['benchmark_accounting']),*c['candidate_accounting'].items()]:
            if account.get('fallback'):lines.extend([f"{label}: exact {account['raw_prediction']:.5f} baseline fallback — {account['reason']}.",'']);continue
            lines.extend([f"{label}: reference {account['reference']:.5f}; reconstructed rate {account['raw_prediction']:.5f}.",'',
                '| Feature | Model input | Rate accounting |','|---|---:|---:|'])
            for v in account['feature_effects'][:12]:lines.append(f"| {v['feature']} | {v.get('scaled_input',v.get('input')):.6f} | {v['path_effect']:.6f} |")
            lines.append('')
        lines.extend([notes[key],'','Origin-selected peers: '+'; '.join(
            f"{p['player_name']} (origin MLB/AAA/AA PA {p['pa_0']}/{p['AAA_0_pa']}/{p['AA_0_pa']}; expected/actual MLB PA {p['cohort_pa']:.1f}/{p['next_pa']}; baseline/ridge/tree rate {p['cohort_rate']:.3f}/{p['contact_ridge_rate']:.3f}/{p['contact_hist_rate']:.3f}; "+
            (f"actual batting rate {p['next_batting_rate']:.3f}" if p['next_pa'] else 'no future MLB PA; no observed batting rate')+')' for p in c['peers'])+'.',''])
    lines.extend(['## Disposition','','Do not adopt either contact-rate candidate. Ridge loses slightly and uncertainly; the histogram candidate loses materially overall and compresses exceptional established hitters. Small player gains do not repair first-arrival/return opportunity or fast-entry talent. Preserve the raw reconstructed input and its source flags as reusable infrastructure; do not conclude all shape, shape×outcome or park-adjusted talent models are useless. Close this bounded transfer batch rather than search parameter/prior variants until one wins.'])
    walk=e.OUT/'player-walkthrough.md';walk.write_text('\n'.join(lines)+'\n',encoding='utf8')
    verification.update(player_walkthrough_status='complete',walkthrough_sha256=sha256_file(walk));e.e.write('verification.json',verification)
    e.e.write('report.json',dict(player_walkthrough_status='complete',cases=len(cases),adopted=False,source_reconstruction_retained=True,
        candidate_ridge_gain_established=False,candidate_histogram_worse=True,working_model='V33b',workload_research='V38',
        practical_model_goal_complete=False,source_notes_sha256=sha256_file(e.OUT/'source-review.json'),notes_sha256=sha256_file(notes_path),
        walkthrough_sha256=sha256_file(walk),protected_outcomes_used=False,frozen_forecast_changed=False))
    print('16 reviews complete; neither candidate adopted. Working V33b unchanged.',flush=True)


if __name__=='__main__':main()
