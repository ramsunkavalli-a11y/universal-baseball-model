"""Close the vintage comparison only after actual saved-fit baseball review."""
from pathlib import Path
import numpy as np
from universal_baseball.storage import sha256_file
import evaluate_hitter_preseason_readiness_v68 as e

def main():
    pre=e.read(e.OUT/'preflight.json');v=e.read(e.OUT/'verification.json');cases=e.read(e.OUT/'cases.json')
    rp=e.ROOT/'config/hitter_preseason_readiness_v68_review.json';review=e.read(rp)
    assert v['replayed_heads']==140 and set(review['cases'])=={f"{c['origin']['player_id']}|{c['origin']['origin_year']}" for c in cases}
    assert all(len(n)>200 for n in review['cases'].values())
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    scores=e.read(e.OUT/'scores.json');intervals=e.read(e.OUT/'intervals.json')
    lines=['# Preseason ranking comparison: source to saved model to reality','',
        'Same 30,506 historical players/seasons, whole-player chronological folds and fixed hitting forecasts. The only new information is the coming-season preseason ranking vintage. Other sources remain through December; this is not a complete Opening Day roster forecast. Repeated development evidence, qualified retrospective lists, no protected 2026 outcomes or automatic promotion.','',
        '| Group | Rows | Old PA RMSE | New PA RMSE | Old PA MAE | New PA MAE | Old offense RMSE | New offense RMSE |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for s in scores[:8]:
        a,b=s['scores']['baseline'],s['scores']['preseason']
        lines.append(f"| {s['scope']} | {s['rows']} | {a['pa_rmse']:.3f} | {b['pa_rmse']:.3f} | {a['pa_mae']:.3f} | {b['pa_mae']:.3f} | {a['value_rmse']:.6f} | {b['value_rmse']:.6f} |")
    lines += ['','Losses weight target years equally. Offense is custom-event batting plus replacement, not full WAR or trade value. Exact counts, origin totals, probability scores and nominal intervals accompany this review. Profile counts are support warnings, not individual prediction intervals.','']
    lean=[]
    for c in cases:
        r=c['origin'];key=f"{r['player_id']}|{r['origin_year']}"
        assert np.isclose(r['preseason_pa'],r['preseason_p']*r['preseason_conditional_pa'],atol=1e-8)
        assert np.isclose(r['preseason_value'],r['preseason_pa']*(r['baseline_rate']/600+r['origin_replacement_rate']),atol=1e-8)
        lines += [f"## {r['player_name']} / {r['origin_year']} to {r['target_year']}",'',
            f"Player {r['player_id']}; row {r['row_id']}; fold {r['outer_fold']}; age {r['age']}; {r['stage']}; new rank availability {c['information_date']}. Selected: {', '.join(c['selection'])}.",'',
            '| Known season | Level | PA | HR | K | UBB |','| --- | --- | ---: | ---: | ---: | ---: |']
        for h in c['source_history']:lines.append(f"| {h['season']} | {h['bucket']} | {h['plate_appearances']} | {h['home_runs']} | {h['strike_outs']} | {h['unintentional_walks']} |")
        if not c['source_history']:lines.append('| No own sample in window | unknown | — | — | — | — |')
        lines += ['',f"Old scouting: {c['old_scouting']}",'',f"New scouting: {c['new_scouting']}",'',
            '| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting/600 | Offense |','| --- | ---: | ---: | ---: | ---: | ---: |']
        for arm in ['baseline','preseason']:lines.append(f"| {arm} | {r[arm+'_p']:.6f} | {r[arm+'_conditional_pa']:.3f} | {r[arm+'_pa']:.3f} | {r['baseline_rate']:.5f} | {r[arm+'_value']:.5f} |")
        lines += [f"| Actual | {int(r['next_pa']>0)} | not a forecast | {r['next_pa']} | {r['next_batting_rate'] if r['next_pa'] else 'unobserved'} | {r['next_value']:.5f} |",'',
            f"Product: {r['preseason_p']:.9f} × {r['preseason_conditional_pa']:.9f}; offense yield: {r['baseline_rate']:.9f}/600 + {r['origin_replacement_rate']:.9f}.",'',
            'Actual MLB counts: '+('; '.join(f"{h['season']}: {h['plate_appearances']} PA, {h['home_runs']} HR, {h['strike_outs']} K, {h['unintentional_walks']} UBB" for h in c['actual_history']) or 'No MLB PA, not observed zero talent.'),'',
            'Distinct earlier training people in actual profiles:']
        for p in c['training_profiles']:lines.append(f"- {p['arm']} {p['head']} {p['kind']}: {p['profile_people']}; rank band {p['rank_band']}.")
        compact={}
        for head,arms in c['saved_traces'].items():
            compact[head]={}
            for arm,t in arms.items():
                assert np.isclose(t['reference']+sum(a['path_effect'] for a in t['feature_effects']),t['raw_prediction'],atol=1e-8)
                expected=r[('repaired_raw_p' if arm=='baseline' else 'preseason_raw_p')] if head=='participation' else r[('repaired_raw_conditional_pa' if arm=='baseline' else 'preseason_raw_conditional_pa')]
                assert np.isclose(t['linked_probability'] if head=='participation' else t['raw_prediction'],expected,atol=1e-8)
                lines += ['',f"Saved {arm} {head}: reference {t['reference']:.6f}, raw additive prediction {t['raw_prediction']:.6f}."+(' Log odds; probability '+format(t['linked_probability'],'.6f')+'.' if head=='participation' else ' Raw PA before the [1,800] bound.'),'Largest path terms (accounting, not causal effects):']
                for a in t['feature_effects'][:5]:lines.append(f"- {a['feature']}: input {a['input']:.6f}, contribution {a['path_effect']:+.6f}.")
                compact[head][arm]=dict(reference=t['reference'],raw_prediction=t['raw_prediction'],largest_terms=t['feature_effects'][:10],
                    scouting_terms=[a for a in t['feature_effects'] if a['feature'].startswith('scout_')],linked_probability=t.get('linked_probability'))
            lines += ['',f"Same fitted candidate with all old ranking inputs restored: {c['candidate_fit_with_old_rankings'][head]:.6f}. Mechanics probe only, not causality or a separately validated replacement forecast."]
        lines += ['',review['cases'][key],'','| Origin-selected peer | Old PA | New PA | Actual PA | Old offense | New offense | Actual offense |',
            '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
        for p in c['peers']:lines.append(f"| {p['player_name']} | {p['baseline_pa']:.2f} | {p['preseason_pa']:.2f} | {p['next_pa']} | {p['baseline_value']:.3f} | {p['preseason_value']:.3f} | {p['next_value']:.3f} |")
        lines.append('');c['review_note']=review['cases'][key]
        lean.append({k:c[k] for k in ['selection','information_date','source_history','actual_history','actual_inputs','old_scouting','new_scouting','training_profiles','peers','candidate_fit_with_old_rankings','review_note']}
            |dict(player=r['player_name'],player_id=r['player_id'],origin_year=r['origin_year'],saved_terms=compact,
            forecasts={k:r[k] for k in ['baseline_p','preseason_p','baseline_conditional_pa','preseason_conditional_pa','baseline_pa','preseason_pa','baseline_rate','baseline_value','preseason_value','next_pa','next_value']}))
    lines += ['## Decision after actual review','',review['decision'],'',review['next_step']]
    (e.OUT/'player-walkthrough.md').write_text('\n'.join(lines)+'\n',encoding='utf8');e.write('reviewed-cases.json',cases);e.write('reviewed-case-summary.json',lean)
    v.update(player_walkthrough_status='complete',notes_sha256=sha256_file(rp));e.write('verification.json',v)
    paths=[e.OUT/n for n in ['predictions.parquet','scored-predictions.parquet','scores.json','intervals.json','verification.json','reviewed-case-summary.json','player-walkthrough.md']]
    code=[Path(__file__),e.ROOT/'scripts/score_hitter_preseason_readiness_v68.py',rp,e.ROOT/'docs/hitter-preseason-readiness-v68-result.md']
    e.write('report.json',dict(player_walkthrough_status='complete',decision=review['decision'],next_step=review['next_step'],integrity=v,
        input_hashes=pre['input_hashes'],output_hashes={str(p):sha256_file(p) for p in paths},review_code_hashes={str(p):sha256_file(p) for p in code},
        protected_outcomes_used=False,frozen_forecast_changed=False,deployed_explorer_changed=False,whole_goal_complete=False))
    archive=e.ROOT/'reports/model-evidence/hitter-preseason-readiness-v68';archive.mkdir(parents=True,exist_ok=True)
    for n in ['report.json','scores.json','intervals.json','verification.json','reviewed-case-summary.json','player-walkthrough.md']:(archive/n).write_bytes((e.OUT/n).read_bytes())
    print('Actual player review archived; no automatic production promotion.',flush=True)

if __name__=='__main__':main()
