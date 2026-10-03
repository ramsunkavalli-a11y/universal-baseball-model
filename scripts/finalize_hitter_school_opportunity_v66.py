"""Require actual baseball review before closing the source comparison."""
from pathlib import Path
import numpy as np
from universal_baseball.storage import sha256_file
import evaluate_hitter_school_opportunity_v66 as e


def main():
    cases=e.read(e.OUT/'cases.json');pre=e.read(e.OUT/'preflight.json');v=e.read(e.OUT/'verification.json')
    review_path=e.ROOT/'config/hitter_school_opportunity_v66_review.json';review=e.read(review_path);notes=review['cases']
    assert v['replayed_heads']==140
    assert set(notes)=={f"{c['origin']['player_id']}|{c['origin']['origin_year']}" for c in cases}
    assert all(len(x)>200 for x in notes.values())
    for path,h in pre['input_hashes'].items():assert sha256_file(Path(path))==h,path
    scores=e.read(e.OUT/'scores.json');intervals=e.read(e.OUT/'intervals.json')
    lines=['# School background comparison and actual player review','',
        'Same 30,506 historical forecasts and thirty-five chronological whole-player folds. Only three broad school indicators change. The precise-class unknown flag, hitting forecasts, labels, membership and settings remain fixed. No protected 2026 outcomes or production changes. Repeated historical development evidence, not independent confirmation.','',
        '| Scope | Rows | Baseline PA RMSE | Candidate PA RMSE | Baseline PA MAE | Candidate PA MAE | Baseline offense RMSE | Candidate offense RMSE |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for s in scores[:8]:
        a,b=s['scores']['baseline'],s['scores']['school']
        lines.append(f"| {s['scope']} | {s['rows']} | {a['pa_rmse']:.3f} | {b['pa_rmse']:.3f} | {a['pa_mae']:.3f} | {b['pa_mae']:.3f} | {a['value_rmse']:.6f} | {b['value_rmse']:.6f} |")
    lines += ['', 'Losses weight each target year equally. Offense is fixed-event batting plus replacement, not full WAR or trade value. Public forecast archive dating remains qualified. All cohort counts and probability scores are saved separately. No continuous prediction intervals are certified.','',
        'Eight cases were locked before fitting. Additional largest gains, harms, false highs/lows and ordinary cases follow fixed score ordering; they are diagnostics, not new independent validation. Four peers use only origin-known age, exposure, draft rank, stage and debut status; their outcomes are then shown without dropping non-arrivals.','']
    lean=[]
    for c in cases:
        r=c['origin'];key=f"{r['player_id']}|{r['origin_year']}";inp=c['actual_inputs']
        assert np.isclose(r['school_pa'],r['school_p']*r['school_conditional_pa'],atol=1e-8)
        assert np.isclose(r['school_value'],r['school_pa']*(r['baseline_rate']/600+r['origin_replacement_rate']),atol=1e-8)
        lines += [f"## {r['player_name']} from {r['origin_year']} to {r['target_year']}",'',
            f"Player {r['player_id']}, row {r['row_id']}, fold {r['outer_fold']}; age {inp['age'] if 'age' in inp else r['age']}; stage {r['stage']}. Selected for {', '.join(c['selection'])}.",'',
            '| Source season | Level | PA | HR | K | Unintentional walks |','| --- | --- | ---: | ---: | ---: | ---: |']
        for h in c['source_history']:lines.append(f"| {h['season']} | {h['bucket']} | {h['plate_appearances']} | {h['home_runs']} | {h['strike_outs']} | {h['unintentional_walks']} |")
        if not c['source_history']:lines.append('| No own batting sample in the three-year window | unknown | — | — | — | — |')
        lines += ['',f"Selected pick: {inp['draft_year']}/{inp['pick_number']}; class {inp['draft_school_class'] or 'unknown'}, name {inp['school_source_name'] or 'unknown'}. Broad background {inp['school_background']}; {inp['school_background_basis']}; evidence year {inp['school_background_evidence_year']}. Exact old/new indicators: {c['old_flags']} → {c['new_flags']}. Precise class-unknown input remains {inp['draft_class_unknown']}.",'',
            '| Forecast | Any MLB PA probability | PA if active | Expected PA | Fixed hitting per 600 | Offense |',
            '| --- | ---: | ---: | ---: | ---: | ---: |',
            f"| Baseline | {r['baseline_p']:.6f} | {r['baseline_conditional_pa']:.3f} | {r['baseline_pa']:.3f} | {r['baseline_rate']:.5f} | {r['baseline_value']:.5f} |",
            f"| Candidate | {r['school_p']:.6f} | {r['school_conditional_pa']:.3f} | {r['school_pa']:.3f} | {r['baseline_rate']:.5f} | {r['school_value']:.5f} |",
            f"| Observed | {int(r['next_pa']>0)} | not a forecast | {r['next_pa']} | {format(r['next_batting_rate'],'.5f') if r['next_pa'] else 'unobserved'} | {r['next_value']:.5f} |",'',
            f"Candidate product: {r['school_p']:.9f} × {r['school_conditional_pa']:.9f}; contribution uses ({r['baseline_rate']:.9f}/600 + {r['origin_replacement_rate']:.9f}). Hitting is held fixed, not newly neutralized or learned. Actual MLB counts:"]
        for h in c['actual_history']:lines.append(f"- {h['season']}: {h['plate_appearances']} PA, {h['home_runs']} HR, {h['strike_outs']} K, {h['unintentional_walks']} walks.")
        if not c['actual_history']:assert r['next_pa']==0;lines.append('- No MLB PA; no observed zero talent rate.')
        lines += ['','Distinct training people in the actual background/entry profiles:']
        for p in c['training_profiles']:lines.append(f"- {p['arm']} {p['head']} {p['kind']}: {p['profile_people']} people; background {p['background']}.")
        compact={}
        for head,arms in c['saved_traces'].items():
            compact[head]={}
            for arm,t in arms.items():
                assert np.isclose(t['reference']+sum(a['path_effect'] for a in t['feature_effects']),t['raw_prediction'],atol=1e-8)
                expected=r[('repaired_raw_p' if arm=='baseline' else 'school_raw_p')] if head=='participation' else r[('repaired_raw_conditional_pa' if arm=='baseline' else 'school_raw_conditional_pa')]
                if head=='participation':assert np.isclose(t['linked_probability'],expected,atol=1e-10)
                else:assert np.isclose(t['raw_prediction'],expected,atol=1e-8)
                lines += ['',f"Saved {arm} {head}: reference {t['reference']:.6f}, raw additive output {t['raw_prediction']:.6f}."+(' This is log odds, not PA; the logistic link gives '+format(t['linked_probability'],'.6f')+'.' if head=='participation' else ' Conditional PA is bounded only after this calculation.'),'Largest exact path contributions:']
                for a in t['feature_effects'][:5]:lines.append(f"- {a['feature']}: input {a['input']:.6f}, path contribution {a['path_effect']:+.6f}.")
                compact[head][arm]=dict(reference=t['reference'],raw_prediction=t['raw_prediction'],largest_terms=t['feature_effects'][:10],
                    school_terms=[x for x in t['feature_effects'] if x['feature'] in e.REPLACEMENTS],linked_probability=t.get('linked_probability'))
            lines += ['',f"Same candidate fit with this player's old school flags gives {c['candidate_fit_with_old_flags'][head]:.6f}. This is an input-path probe, not a causal estimate or a validated replacement forecast. Changes with unchanged own flags reflect refitting on repaired training evidence."]
        lines += ['',notes[key],'','| Origin selected peer | Baseline PA | Candidate PA | Actual PA | Baseline offense | Candidate offense | Actual offense |',
            '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
        for p in c['peers']:lines.append(f"| {p['player_name']} | {p['baseline_pa']:.2f} | {p['school_pa']:.2f} | {p['next_pa']} | {p['baseline_value']:.3f} | {p['school_value']:.3f} | {p['next_value']:.3f} |")
        lines.append('')
        c['review_note']=notes[key]
        lean.append(dict(player=r['player_name'],player_id=r['player_id'],origin_year=r['origin_year'],selection=c['selection'],
            forecasts={k:r[k] for k in ['baseline_p','school_p','baseline_conditional_pa','school_conditional_pa','baseline_pa','school_pa','baseline_rate','baseline_value','school_value','next_pa','next_value']},
            source_history=c['source_history'],actual_history=c['actual_history'],old_flags=c['old_flags'],new_flags=c['new_flags'],actual_inputs=inp,
            training_profiles=c['training_profiles'],saved_terms=compact,old_flag_probes=c['candidate_fit_with_old_flags'],peers=c['peers'],review_note=notes[key]))
    lines += ['## Decision after actual review','',review['decision'],'',review['next_step']]
    (e.OUT/'player-walkthrough.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    e.write('reviewed-cases.json',cases);e.write('reviewed-case-summary.json',lean)
    v.update(player_walkthrough_status='complete',notes_sha256=sha256_file(review_path));e.write('verification.json',v)
    paths=[e.OUT/p for p in ['predictions.parquet','scored-predictions.parquet','scores.json','intervals.json','verification.json','reviewed-case-summary.json','player-walkthrough.md']]
    code=[Path(__file__),e.ROOT/'scripts/score_hitter_school_opportunity_v66.py',review_path,e.ROOT/'docs/hitter-school-opportunity-v66-result.md']
    report=dict(player_walkthrough_status='complete',decision=review['decision'],next_step=review['next_step'],integrity=v,
        input_hashes=pre['input_hashes'],output_hashes={str(p):sha256_file(p) for p in paths},review_code_hashes={str(p):sha256_file(p) for p in code},
        protected_outcomes_used=False,frozen_forecast_changed=False,deployed_explorer_changed=False,whole_goal_complete=False)
    e.write('report.json',report)
    archive=e.ROOT/'reports/model-evidence/hitter-school-opportunity-v66';archive.mkdir(parents=True,exist_ok=True)
    for name in ['report.json','scores.json','intervals.json','verification.json','reviewed-case-summary.json','player-walkthrough.md']:(archive/name).write_bytes((e.OUT/name).read_bytes())
    print('Actual player review completed; comparison archived without production promotion.',flush=True)


if __name__=='__main__':main()
