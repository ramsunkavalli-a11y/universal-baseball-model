"""Publish actual manual review; never equate an execution pass with adoption."""
import prepare_hitter_joint_forest_v43 as e
from universal_baseball.storage import sha256_file


def name(o):
    return 'Hyeseong Kim' if o['player_id']==808975 else o['player_name']


def main():
    cases=e.r.read(e.OUT/'cases.json')
    path=e.r.ROOT/'config/practical_hitter_joint_v43_case_notes.json'
    notes=e.r.read(path);verify=e.r.read(e.OUT/'verification.json')
    assert len(cases)==len(notes)==16 and verify['mean_and_event_heads_replayed']==35
    lines=['# Joint hitter forecast player review','',
        'The new forest uses the same 199 inputs and held-player chronological folds as the control. Targets are following-calendar-year MLB PA and batting-plus-replacement wins, not full WAR or a current prospect talent grade. Sixteen actual manual reviews follow. Outcome-selected examples diagnose mechanisms, not independent confirmation.','',
        'The three-year official count inputs retain each level separately, with recency weights 1/.8/.6 and stabilized event counts. No additional park/opponent, injury diagnosis, foreign statistics or depth chart is silently inserted. Age 27 with age_unknown=1 is a placeholder, not a known age. Captured roster flags have the separately documented dating limitation.','',
        'Neighbor selection comes from the fitted trees and origin inputs only; the subsequent outcomes are paired records already mature by the forecast cutoff. Full weights are saved per case, alongside actual inputs and all control coefficient/tree accounting. Listed outcomes include zero returns. The twelve largest weights are only an excerpt, not the entire distribution. Effective rows do not mean independent people.','']
    for c in cases:
        o=c['origin'];n=name(o);key=f"{n}|{o['origin_year']}";assert key in notes
        lines.extend([f"## {n} {o['origin_year']} to {o['target_year']}",'',
            'Selection: '+'; '.join(c['selection'])+'.','',
            f"Player {o['player_id']}, row {o['row_id']}, fold {o['outer_fold']}; stage {o['stage']}; age {o['age']} (unknown flag {o['age_unknown']}); listed position {o['source_position']}; draft year/pick {o['draft_year']}/{o['pick_number']}; captured 40-man {o['on_40man']}.",'',
            '| Season | Level bucket | PA | HR | K | Unintentional BB |','|---|---|---:|---:|---:|---:|'])
        for h in c['source_history']:
            lines.append(f"| {h['season']} | {h['bucket']} | {h['plate_appearances']} | {h['home_runs']} | {h['strike_outs']} | {h['unintentional_walks']} |")
        if not c['source_history']:lines.append('| No observed own batting history by cutoff | Unknown | — | — | — | — |')
        lines.extend(['','| Forecast | Expected MLB PA | Batting plus replacement wins |','|---|---:|---:|',
            f"| Control | {o['cohort_pa']:.3f} | {o['cohort_value']:.5f} |",
            f"| Joint forest | {o['joint_pa']:.3f} | {o['joint_value']:.5f} |",
            f"| Actual | {o['next_pa']} | {o['next_value']:.5f} |",'',
            f"Control future-active batting forecast: {o['cohort_rate']:.5f} wins/600. Contribution arithmetic: expected PA × (rate/600 + origin replacement {o['origin_replacement_rate']:.8f}). The future-PA-weighted rate is not necessarily an independent unweighted mean. The joint forecast instead averages the same weighted actual PA/value pairs; its implied yield is not a separately validated talent grade.",'',
            f"Joint probabilities: participation {o['joint_p_active']:.2%}, at least 400 PA {o['joint_p_400']:.2%}, negative contribution {o['joint_p_negative']:.2%}, at least two contribution wins {o['joint_p_2wins']:.2%}. PA deciles/median: {o['joint_pa_q10']}/{o['joint_pa_q50']}/{o['joint_pa_q90']}. Contribution deciles/median: "+'/'.join(f'{a:.4f}' for a in c['weighted_value_quantiles'])+'. The median is not expected PA.',''])
        for metric,t in c['benchmark_accounting'].items():
            lines.extend([f"Control {metric} accounting: reference {t['reference']:.6f}; raw prediction {t['raw_prediction']:.6f}. PA clipping or permanent-status override, when applicable, follows the raw prediction.",'',
                '| Actual input | Input or scaled input | Accounting effect |','|---|---:|---:|'])
            for a in t['feature_effects'][:8]:
                lines.append(f"| {a['feature']} | {a.get('scaled_input',a.get('input')):.6f} | {a['path_effect']:.6f} |")
            lines.append('')
        lines.extend([notes[key],'',
            f"Distinct-player profile support: {c['training_profile']}. Weighted distribution: {c['raw_distribution']['distinct_nonzero_weight_players']} people, effective rows {c['raw_distribution']['effective_rows']:.2f}, latest contributing target year {c['raw_distribution']['source_target_maximum']}. Sparse profile support remains qualified, not repaired by the overall leaf count.",'',
            '| Weighted origin neighbor | Origin | Age | Origin MLB / AAA / AA PA | Next MLB PA | Next contribution | Weight |','|---|---:|---:|---|---:|---:|---:|'])
        for p in c['neighbors']:
            label=p['player_name'] or f"Unnamed source player {p['player_id']}"
            lines.append(f"| {label} | {p['origin_year']} | {p['age']} | {p['pa_0']} / {p['AAA_0_pa']} / {p['AA_0_pa']} | {p['next_pa']} | {p['next_value']:.5f} | {p['distribution_weight']:.5f} |")
        lines.extend(['','Highest-weight zero follow-ups (also selected by fitted origin-feature weights): '+
            '; '.join(f"{p['player_name'] or p['player_id']} ({p['origin_year']}, weight {p['distribution_weight']:.5f})" for p in c['high_weight_zero_outcomes'])+'.',''])
    lines.extend(['## Decision after reviewing the players','',
        'Do not replace the working means. The joint candidate worsens PA and contribution error overall; all seven origin contribution errors worsen, and upper-minor opportunity totals fall farther below actual. Better league-wide PA totals are not a sufficient win. Its risk probabilities outperform a simple stage/debut reference, but upper-minor participation is underpredicted and lower-minor rare-event log loss worsens. Retain the empirical distribution implementation and case evidence as research, not validated uncertainty grafted onto a different point model.','',
        'The review identifies dated availability/context as a useful source repair, especially announced retirement and foreign-player eligibility. It also shows elite-value compression and broad readiness neighborhoods. These are different issues: first repair or explicitly qualify origin-known population/status evidence; do not launch another library sweep or tune to famous breakouts. Frozen 2026 and the deployed forecast stay unchanged.'])
    out=e.OUT/'player-walkthrough.md';out.write_text('\n'.join(lines)+'\n',encoding='utf8')
    verify.update(player_walkthrough_status='complete',walkthrough_sha256=sha256_file(out),manual_notes_sha256=sha256_file(path))
    e.write('verification.json',verify)
    e.write('report.json',dict(player_walkthrough_status='complete',cases=16,mean_forecast_adopted=False,
        risk_retained_as_research=True,risk_calibration_established_all_levels=False,meaningful_mean_gain_established=False,
        integrity_pass=True,profile_support_qualified=True,origin_eligibility_qualified=True,
        public_mae_tolerance_pass=False,working_forecast='V33b',protected_outcomes_used=False,
        frozen_forecast_changed=False,manual_notes_sha256=sha256_file(path),walkthrough_sha256=sha256_file(out)))
    print('16 manual paired-outcome walks complete; keep V33b means, retain risk research with qualifications.')


if __name__=='__main__':main()
