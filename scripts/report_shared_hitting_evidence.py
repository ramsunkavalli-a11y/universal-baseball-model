"""Persist completed negative-test review and separate integrity from adoption."""
import polars as pl
import evaluate_shared_hitting_evidence as e
from universal_baseball.storage import sha256_file


def main():
    cases=e.old.r.read(e.OUT/'cases.json');notes_path=e.old.r.ROOT/'config/practical_hitter_v35_case_notes.json'
    notes=e.old.r.read(notes_path);verification=e.old.r.read(e.OUT/'verification.json')
    assert len(cases)==len(notes)==17 and verification['replayed_new_heads']==70
    support=pl.read_parquet(e.OUT/'support.parquet')
    lines=['# Shared hitting evidence: completed player review','',
        'Fixed original rates versus one shared event-opportunity denominator. Identical players, targets and model settings. Separate rate-only, PA-only and combined products. Next-year MLB batting-plus-replacement contribution, not full WAR. Every saved head replays; this does not establish predictive success.','',
        'Nine fixed cases plus each product largest gain/harm, false high/low and ordinary example. Peers use origin year/stage/debut, age, MLB/upper-minor PA, observed quality and draft rank without future outcomes. Missing school/health matching limits certain peer interpretations.','']
    for c in cases:
        o=c['origin'];key=f"{o['player_name']}|{o['origin_year']}";assert key in notes
        lines.extend([f"## {o['player_name']}: {o['origin_year']} to {o['target_year']}",'',
            'Selection: '+'; '.join(c['selection'])+'.','',
            f"Age {o['age']:g}; MLB PA {o['pa_0']}/{o['pa_1']}/{o['pa_2']}; draft pick {o['pick_number']}, class {o['draft_school_class'] or 'unknown'}; soft roster listing {o['on_40man']}. Unchanged legacy quality/workload features remain in this specific test.",'',
            '| Year | League | Actual PA | HR | K | Unintentional walks |','|---|---|---:|---:|---:|---:|'])
        for h in c['source_history']:lines.append(f"| {h['season']} | {h['bucket']} | {h['plate_appearances']} | {h['home_runs']} | {h['strike_outs']} | {h['unintentional_walks']} |")
        lines.extend(['','Actual transformation: old = prior + centered events/(bucket opportunities + 100); new = prior + centered events/(all-bucket opportunities + 100).','',
            '| League/event | Weighted events | Bucket opportunities | All opportunities | Prior | Old | New |','|---|---:|---:|---:|---:|---:|---:|'])
        for t in c['transformations']:lines.append(f"| {t['bucket']}/{t['event']} | {t['weighted_events']:.2f} | {t['weighted_opportunities']:.2f} | {t['total_opportunities']:.2f} | {t['prior']:.4f} | {t['old']:.6f} | {t['new']:.6f} |")
        lines.extend(['','| Model | PA | Conditional batting wins/600 | Batting + replacement wins |','|---|---:|---:|---:|'])
        for a in ['cohort','rate_only','pa_only','shared']:lines.append(f"| {a} | {o[a+'_pa']:.3f} | {o[a+'_rate']:.5f} | {o[a+'_value']:.5f} |")
        lines.extend([f"| Actual | {o['next_pa']} | {o['next_batting_rate']:.5f} | {o['next_value']:.5f} |",'',
            f"Product uses PA × (rate/600 + origin replacement {o['origin_replacement_rate']:.7f}), not a joint predictive distribution.",'',
            f"Saved rate intercept {c['linear_intercept']:.6f}; fixed-old-model/new-encoding probe {c['fixed_old_model_new_encoding_probe']:.6f}. {c['probe_claim']}",'',
            '| Actual new feature | Raw | Fixed scaled | Fitted coefficient | Contribution |','|---|---:|---:|---:|---:|'])
        for t in c['linear_terms']:lines.append(f"| {t['feature']} | {t['raw']:.5f} | {t['fixed_scaled']:.5f} | {t['coefficient']:.7f} | {t['contribution']:.5f} |")
        lines.extend(['',notes[key],'',
            'Origin-selected peers: '+'; '.join(f"{p['player_name']} (age {p['age']:g}, MLB/AAA/AA PA {p['pa_0']}/{p['AAA_0_pa']}/{p['AA_0_pa']}; actual next {p['next_pa']} PA/{p['next_value']:.3f} wins)" for p in c['peers'])+'.','',
            'Training profile: '+'; '.join(f"{h['head']}={h['profile_players']} distinct people" for h in support.filter(pl.col('row_id')==o['row_id']).to_dicts())+'.',''])
    lines.extend(['## Decision','',
        'Do not adopt shared-denominator batting or combined assembly. Both conditional rate and delivered contribution worsen; the rate-only whole-cohort and brief-debut value intervals favor the old encoding. PA-only changes are small/uncertain and do not justify a new working forecast. Useful examples do not outweigh repeated harmful cases. This rejects this particular encoding within this legacy-feature assembly, not minor-league evidence, component forecasts or learned MLB equivalencies.','',
        'Next: a coherent MLB event-outcome target, rather than another alteration to the same value-regression inputs. Keep repaired-source V34 and working V33b anchors, fixed cohorts, component and delivered checks. No automatic deployment or 2026 outcomes.'])
    path=e.OUT/'player-walkthrough.md';path.write_text('\n'.join(lines)+'\n',encoding='utf8')
    verification.update(player_walkthrough_status='complete',player_walkthrough_sha256=sha256_file(path));e.write('verification.json',verification)
    e.write('report.json',dict(player_walkthrough_status='complete',cases=17,player_walkthrough_artifact=str(path),
        player_walkthrough_sha256=sha256_file(path),notes_sha256=sha256_file(notes_path),
        adopted=False,predictive_improvement_established=False,practical_model_goal_complete=False,
        protected_outcomes_used=False,frozen_forecast_changed=False,verification=verification))
    print('17 player walkthroughs complete; shared representation not adopted.')


if __name__=='__main__':main()
