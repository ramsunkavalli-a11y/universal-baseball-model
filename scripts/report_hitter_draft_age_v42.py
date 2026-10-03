"""Complete the required review before disposing of the representation test."""
import polars as pl
import prepare_hitter_draft_age_v42 as e
from universal_baseball.storage import sha256_file


def main():
    cases=e.r.read(e.OUT/'cases.json');path=e.r.ROOT/'config/practical_hitter_draft_age_v42_case_notes.json';notes=e.r.read(path)
    verify=e.r.read(e.OUT/'verification.json');assert len(cases)==len(notes)==15 and verify['replayed_heads']==70
    lines=['# V42 complete player walkthrough','',
        'Identical population/folds, future MLB targets and learners; school flags replaced with three draft-age inputs. Exact tree-path/coefficient accounting is descriptive, not causal. Every case includes actual counts, actual inputs, saved intermediates, results and origin-only selected peers. No protected 2026 outcomes.','']
    for c in cases:
        o=c['origin'];key=f"{o['player_name']}|{o['origin_year']}";assert key in notes
        lines.extend([f"## {o['player_name']} — {o['origin_year']} to {o['target_year']}",'',
            'Selection: '+'; '.join(c['selection'])+'.','',
            f"Age {o['age']}; stage {o['stage']}; listed position {o['source_position']}; draft {o['draft_year']}/pick {o['pick_number']}/class {o['draft_school_class'] or 'missing'}; approximate draft age {c['draft_age_proxy']}.",'',
            'New inputs: '+str({x:c['actual_inputs'][x] for x in e.ADDED})+'.','',
            '| Season | Bucket | PA | HR | K | UBB |','|---|---|---:|---:|---:|---:|'])
        for h in c['source_history']:lines.append(f"| {h['season']} | {h['bucket']} | {h['plate_appearances']} | {h['home_runs']} | {h['strike_outs']} | {h['unintentional_walks']} |")
        lines.extend(['','The original three-year pooled per-level exposure and stabilized event inputs are unchanged; recency weights 1/.8/.6 and fixed event priors remain. No learned school/age translation or park/opponent neutralization is silently inserted.','',
            '| Forecast | MLB PA | Batting wins/600 | Batting + replacement |','|---|---:|---:|---:|'])
        for a in ['cohort','draft_age','age_pa_only','age_rate_only']:lines.append(f"| {a} | {o[a+'_pa']:.3f} | {o[a+'_rate']:.5f} | {o[a+'_value']:.5f} |")
        lines.extend([f"| Actual | {o['next_pa']} | {o['next_batting_rate'] if o['next_pa'] else 'not observed'} | {o['next_value']:.5f} |",'',
            f"Contribution = PA × (batting rate / 600 + origin replacement {o['origin_replacement_rate']:.8f}). Separate means, not a joint distribution; no full WAR.",''])
        for label,a in c['accounting'].items():
            for metric,t in a.items():
                lines.extend([f"{label} {metric}: reference {t['reference']:.6f}, raw prediction {t['raw_prediction']:.6f}.",'',
                    '| Actual feature | Input (scaled for rate) | Accounting effect |','|---|---:|---:|'])
                displayed=list(t['feature_effects'][:8])
                if metric=='rate':
                    displayed.extend(v for v in t['feature_effects'][8:] if v['feature'].startswith('draft_'))
                for v in displayed:lines.append(f"| {v['feature']} | {v.get('scaled_input',v.get('input')):.6f} | {v['path_effect']:.6f} |")
                lines.append('')
        lines.extend([notes[key],'','Actual distinct-player profile support: '+str([(p['head'],p['profile_players']) for p in c['training_profile']])+'. Sparse groups are retained, not certified by the pooled sample.','',
            '| Origin-selected peer | Age | Recent pro PA | Control → age → actual MLB PA | Actual contribution |','|---|---:|---:|---|---:|'])
        for p in c['peers']:lines.append(f"| {p['player_name']} | {p['age']} | {p['recent_all_pa']} | {p['cohort_pa']:.1f} → {p['draft_age_pa']:.1f} → {p['next_pa']} | {p['next_value']:.4f} |")
        lines.append('')
    lines.extend(['## Disposition','',
        'No working-model promotion. Retain explicit draft-age/source-coverage diagnostics, and the consistent-age representation as research. Overall conditional batting improves slightly but combined value gain is tiny/uncertain, public PA/value slightly worsen, and fast-entry/return opportunity is essentially untouched. Source-label inconsistency was real; its simple replacement was not a practically established cure. No additional school/age parameter sweep.','',
        'The next substantial question is uncertainty and opportunity: distinguish next-year participation/range from longer-term talent promise and assess systematic PA calibration by observable workload profiles. Do not equate an individual breakout miss with a wrong cohort mean or use current-year outcomes to force a favorable prospect rank.'])
    out=e.OUT/'player-walkthrough.md';out.write_text('\n'.join(lines)+'\n',encoding='utf8')
    verify.update(player_walkthrough_status='complete',walkthrough_sha256=sha256_file(out));e.write('verification.json',verify)
    e.write('report.json',dict(player_walkthrough_status='complete',cases=15,adopted=False,retain_as_research=True,
        meaningful_gain_established=False,integrity_pass=True,profile_support_qualified=True,public_mae_tolerance_pass=False,
        working_forecast='V33b',protected_outcomes_used=False,frozen_forecast_changed=False,
        notes_sha256=sha256_file(path),walkthrough_sha256=sha256_file(out),source_review=e.r.read(e.OUT/'source-review.json')))
    print('15 actual player walks complete; representation retained as research, not an adopted forecast.')


if __name__=='__main__':main()
