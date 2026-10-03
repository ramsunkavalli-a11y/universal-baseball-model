"""Archive the bounded test only after actual source/fit/outcome player review."""
from pathlib import Path
import numpy as np
from universal_baseball.storage import sha256_file
import evaluate_hitter_graduation_v69 as e


def main():
    pre=e.read(e.OUT/'preflight.json');v=e.read(e.OUT/'verification.json');cases=e.read(e.OUT/'cases.json')
    rp=e.ROOT/'config/hitter_graduation_v69_review.json';review=e.read(rp)
    assert v['replayed_heads']==140 and set(review['cases'])=={f"{c['origin']['player_id']}|{c['origin']['origin_year']}" for c in cases}
    assert all(len(n)>200 for n in review['cases'].values())
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    scores=e.read(e.OUT/'scores.json');lines=['# Graduation context in hitter opportunity','',
        'Same 30,506 historical forecasts, chronological whole-player folds and unchanged hitting. Three new origin-known inputs distinguish sufficient AB graduation and recent ranking history from current absence. Retrospective-list and source-coverage qualifications remain. No protected 2026 use or deployment.','',
        '| Group | Rows | Original PA RMSE | Fresh-list PA RMSE | Graduate PA RMSE | Original MAE | Fresh-list MAE | Graduate MAE | Graduate offense RMSE |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for s in scores[:8]:
        a,b,d=[s['scores'][n] for n in ['baseline','preseason','graduation']]
        lines.append(f"| {s['scope']} | {s['rows']} | {a['pa_rmse']:.3f} | {b['pa_rmse']:.3f} | {d['pa_rmse']:.3f} | {a['pa_mae']:.3f} | {b['pa_mae']:.3f} | {d['pa_mae']:.3f} | {d['value_rmse']:.6f} |")
    lines += ['','Losses weight target years equally; raw totals are not rescaled. Offense includes custom batting and replacement, not full WAR or control/trade value. Profile counts are support warnings, not forecast intervals.',''];lean=[]
    for c in cases:
        r=c['origin'];key=f"{r['player_id']}|{r['origin_year']}"
        assert np.isclose(r['graduation_pa'],r['graduation_p']*r['graduation_conditional_pa'],atol=1e-8)
        lines += [f"## {r['player_name']} / {r['origin_year']} to {r['target_year']}",'',
            f"ID {r['player_id']}; row {r['row_id']}; fold {r['outer_fold']}; age {r['age']}; {r['stage']}; list available {c['information_date']}. Selected: {', '.join(c['selection'])}.",'',
            f"Observed MLB AB lower bound {r['observed_mlb_ab_lower_bound']}; added inputs "+str({n:c['actual_inputs'][n] for n in e.FEATURES})+'. Lower AB does not establish eligibility; no service-day reconstruction.','',
            'Raw MLB AB history: '+str(c['mlb_ab_history']),'',
            'Actual preseason ranking inputs: '+str({n:x for n,x in c['actual_inputs'].items() if n.startswith('scout_')}),'',
            '| Known season | Level | PA | HR | K | UBB |','| --- | --- | ---: | ---: | ---: | ---: |']
        for h in c['source_history']:lines.append(f"| {h['season']} | {h['bucket']} | {h['plate_appearances']} | {h['home_runs']} | {h['strike_outs']} | {h['unintentional_walks']} |")
        lines += ['','| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting/600 | Offense |','| --- | ---: | ---: | ---: | ---: | ---: |']
        for a in ['baseline','preseason','graduation']:lines.append(f"| {a} | {r[a+'_p']:.6f} | {r[a+'_conditional_pa']:.3f} | {r[a+'_pa']:.3f} | {r['baseline_rate']:.5f} | {r[a+'_value']:.5f} |")
        lines += [f"| Actual | {int(r['next_pa']>0)} | not a forecast | {r['next_pa']} | {r['next_batting_rate'] if r['next_pa'] else 'unobserved'} | {r['next_value']:.5f} |",'',
            f"PA product {r['graduation_p']:.9f} × {r['graduation_conditional_pa']:.9f}; offense yield {r['baseline_rate']:.9f}/600 + {r['origin_replacement_rate']:.9f}.",'',
            'Actual MLB counts: '+str(c['actual_history'])+'. No MLB PA is not observed zero hitting talent.','',
            'Actual earlier distinct-player profile support: '+str(c['training_profiles'])+'.','']
        compact={}
        for head,arms in c['saved_traces'].items():
            compact[head]={}
            for a,t in arms.items():
                assert np.isclose(t['reference']+sum(x['path_effect'] for x in t['feature_effects']),t['raw_prediction'],atol=1e-8)
                expected=r[a+('_raw_p' if head=='participation' else '_raw_conditional_pa')]
                assert np.isclose(t['linked_probability'] if head=='participation' else t['raw_prediction'],expected,atol=1e-8)
                selected=t['feature_effects'][:6];scout=[x for x in t['feature_effects'] if x['feature'].startswith('scout_')]
                lines += [f"Saved {a} {head}: reference {t['reference']:.6f}; raw additive {t['raw_prediction']:.6f}"+
                    (f"; linked probability {t['linked_probability']:.6f}." if head=='participation' else '; raw PA before bounds.'),'Largest path terms (accounting, not causality):']
                for x in selected:lines.append(f"- {x['feature']}: input {x['input']:.6f}, contribution {x['path_effect']:+.6f}.")
                lines += ['','Scouting/graduation path terms: '+str(scout),'']
                compact[head][a]=dict(reference=t['reference'],raw_prediction=t['raw_prediction'],largest_terms=selected,scouting_terms=scout,linked_probability=t.get('linked_probability'))
            lines += [f"Same fitted candidate with the three graduation inputs zero: {c['candidate_fit_with_graduation_features_zero'][head]:.6f}. Artificial mechanics probe only; existing MLB history remains. Not a validated replacement forecast.",'']
        lines += [review['cases'][key],'','| Origin-selected peer | Original PA | Fresh-list PA | Graduate PA | Actual PA | Graduate offense | Actual offense |',
            '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
        for p in c['peers']:lines.append(f"| {p['player_name']} | {p['baseline_pa']:.2f} | {p['preseason_pa']:.2f} | {p['graduation_pa']:.2f} | {p['next_pa']} | {p['graduation_value']:.3f} | {p['next_value']:.3f} |")
        lines.append('')
        lean.append({k:c[k] for k in ['selection','information_date','actual_inputs','mlb_ab_history','source_history','actual_history','training_profiles','peers','candidate_fit_with_graduation_features_zero','probe_interpretation']}
            |dict(player=r['player_name'],player_id=r['player_id'],origin_year=r['origin_year'],review_note=review['cases'][key],saved_terms=compact,
            forecasts={k:r[k] for k in ['baseline_p','preseason_p','graduation_p','baseline_conditional_pa','preseason_conditional_pa','graduation_conditional_pa',
                'baseline_pa','preseason_pa','graduation_pa','baseline_rate','baseline_value','preseason_value','graduation_value','next_pa','next_value']}))
    lines += ['## Decision after actual review','',review['decision'],'',review['next_step']]
    (e.OUT/'player-walkthrough.md').write_text('\n'.join(lines)+'\n',encoding='utf8');e.write('reviewed-case-summary.json',lean)
    v.update(player_walkthrough_status='complete',notes_sha256=sha256_file(rp));e.write('verification.json',v)
    paths=[e.OUT/n for n in ['predictions.parquet','scored-predictions.parquet','scores.json','intervals.json','verification.json','reviewed-case-summary.json','player-walkthrough.md','source-check.json']]
    code=[Path(__file__),rp,e.ROOT/'docs/hitter-graduation-v69-result.md']
    e.write('report.json',dict(player_walkthrough_status='complete',decision=review['decision'],next_step=review['next_step'],integrity=v,input_hashes=pre['input_hashes'],
        output_hashes={str(p):sha256_file(p) for p in paths},review_code_hashes={str(p):sha256_file(p) for p in code},protected_outcomes_used=False,
        frozen_forecast_changed=False,deployed_explorer_changed=False,whole_goal_complete=False))
    archive=e.ROOT/'reports/model-evidence/hitter-graduation-v69';archive.mkdir(parents=True,exist_ok=True)
    for n in ['report.json','scores.json','intervals.json','verification.json','reviewed-case-summary.json','player-walkthrough.md','source-check.json']:(archive/n).write_bytes((e.OUT/n).read_bytes())
    print('Actual player review archived; no automatic promotion.',flush=True)


if __name__=='__main__':main()
