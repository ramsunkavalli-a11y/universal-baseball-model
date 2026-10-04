"""Seal employment comparison only after actual saved-fit/player review."""
from pathlib import Path
import numpy as np
import polars as pl
from universal_baseball.storage import sha256_file
import evaluate_hitter_employment_v71 as e


def main():
    pre=e.read(e.OUT/'preflight.json');v=e.read(e.OUT/'verification.json');cases=e.read(e.OUT/'cases.json')
    rp=e.ROOT/'config/hitter_employment_v71_review.json';review=e.read(rp)
    assert v['replayed_heads']==140 and set(review['cases'])=={f"{c['origin']['player_id']}|{c['origin']['origin_year']}" for c in cases}
    assert all(len(s)>200 for s in review['cases'].values())
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    details=pl.read_parquet(e.OUT/'source-details.parquet');records=e.read(e.OUT/'records.json');all_star=[]
    for r in details.filter(pl.col('employment_year_known')==1).iter_rows(named=True):
        latest=[s for s in records.get(str(r['player_id']),[]) if s['available_date']==r['latest_employment_date']]
        if latest and all('all-star' in (s['description'] or '').lower() or 'all star' in (s['description'] or '').lower() for s in latest):all_star.append(r['row_id'])
    q=pl.read_parquet(e.OUT/'scored-predictions.parquet');affected=q.filter(pl.col('row_id').is_in(all_star))
    assert len(all_star)==86 and len(affected)==80
    e.write('assignment-qualification.json',dict(source_rows=len(all_star),evaluation_rows=len(affected),source_row_ids=all_star,
        by_origin=affected.group_by('origin_year').len().sort('origin_year').to_dicts(),
        interpretation='Latest generic assignment is only an All-Star assignment, not current club employment or a contract. No new fits or modified forecasts.'))
    scores=e.read(e.OUT/'scores.json');lines=['# Employment evidence and hitter opportunity','',
        'Same 30,506 historical forecasts, chronological whole-player folds and fixed hitting. Three added inputs distinguish capture-era coverage, a current unambiguous employment event and recorded free agency. Unknown employment is not a deal; attachment is not a guaranteed MLB job. No protected 2026 use or deployment.','',
        '| Group | Rows | Original PA RMSE | Fresh-list PA RMSE | Employment PA RMSE | Original MAE | Fresh-list MAE | Employment MAE | Employment offense RMSE |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for s in scores[:8]:
        a,b,d=[s['scores'][n] for n in ['baseline','preseason','employment']]
        lines.append(f"| {s['scope']} | {s['rows']} | {a['pa_rmse']:.3f} | {b['pa_rmse']:.3f} | {d['pa_rmse']:.3f} | {a['pa_mae']:.3f} | {b['pa_mae']:.3f} | {d['pa_mae']:.3f} | {d['value_rmse']:.6f} |")
    lines+=['','Losses weight target years equally; raw totals are not rescaled. Offense is custom batting plus replacement, not full WAR. Development intervals are whole-player paired, not a fresh protected test. Exact transaction publication vintages and equal public-forecast information dates remain unverified.',''];lean=[]
    for c in cases:
        r=c['origin'];key=f"{r['player_id']}|{r['origin_year']}"
        assert np.isclose(r['employment_pa'],r['employment_p']*r['employment_conditional_pa'],atol=1e-8)
        lines += [f"## {r['player_name']} / {r['origin_year']} to {r['target_year']}",'',
            f"ID {r['player_id']}; row {r['row_id']}; fold {r['outer_fold']}; age {r['age']}; {r['stage']}; ranking information date {c['information_date']}. Selected: {', '.join(c['selection'])}.",'',
            'Employment evidence: '+str(c['employment_source']), '',
            'Dated records at cutoff: '+str(c['dated_records']), '',
            'Actual ranking inputs: '+str({n:x for n,x in c['actual_inputs'].items() if n.startswith('scout_')}), '',
            '| Known season | Level | PA | HR | K | UBB |','| --- | --- | ---: | ---: | ---: | ---: |']
        for h in c['source_history']:lines.append(f"| {h['season']} | {h['bucket']} | {h['plate_appearances']} | {h['home_runs']} | {h['strike_outs']} | {h['unintentional_walks']} |")
        lines+=['','| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting/600 | Offense |','| --- | ---: | ---: | ---: | ---: | ---: |']
        for a in ['baseline','preseason','employment']:lines.append(f"| {a} | {r[a+'_p']:.6f} | {r[a+'_conditional_pa']:.3f} | {r[a+'_pa']:.3f} | {r['baseline_rate']:.5f} | {r[a+'_value']:.5f} |")
        lines += [f"| Actual | {int(r['next_pa']>0)} | not a forecast | {r['next_pa']} | {r['next_batting_rate'] if r['next_pa'] else 'unobserved'} | {r['next_value']:.5f} |",'',
            f"PA product {r['employment_p']:.9f} × {r['employment_conditional_pa']:.9f}; offense yield {r['baseline_rate']:.9f}/600 + {r['origin_replacement_rate']:.9f}.",'',
            'Actual MLB counts: '+str(c['actual_history'])+'. No PA is not observed zero hitting talent.','',
            'Earlier distinct-player profile support: '+str(c['training_profiles'])+'. Broad support does not establish a matched elite-star analogue.','']
        compact={}
        for head,arms in c['saved_traces'].items():
            compact[head]={}
            for a,t in arms.items():
                assert np.isclose(t['reference']+sum(x['path_effect'] for x in t['feature_effects']),t['raw_prediction'],atol=1e-8)
                expected=r[a+('_raw_p' if head=='participation' else '_raw_conditional_pa')]
                assert np.isclose(t['linked_probability'] if head=='participation' else t['raw_prediction'],expected,atol=1e-8)
                largest=t['feature_effects'][:6]
                context=[x for x in t['feature_effects'] if x['feature'] in e.FEATURES or x['feature']=='on_40man']
                lines += [f"Saved {a} {head}: reference {t['reference']:.6f}; raw additive {t['raw_prediction']:.6f}"+
                    (f"; linked probability {t['linked_probability']:.6f}." if head=='participation' else '; raw PA before bounds.'),'',
                    'Largest path terms (accounting, not causality):','']
                for x in largest:lines.append(f"- {x['feature']}: input {x['input']:.6f}, contribution {x['path_effect']:+.6f}.")
                lines+=['','Employment and roster path terms: '+str(context),'']
                compact[head][a]=dict(reference=t['reference'],raw_prediction=t['raw_prediction'],largest_terms=largest,employment_roster_terms=context,linked_probability=t.get('linked_probability'))
            lines += [f"Same fitted candidate with the three new inputs zero: {c['candidate_fit_with_new_inputs_zero'][head]:.6f}. {c['probe_interpretation']}",'']
        lines += [review['cases'][key],'','| Origin-selected peer | Original PA | Fresh-list PA | Employment PA | Actual PA | Employment offense | Actual offense |',
            '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
        for p in c['peers']:lines.append(f"| {p['player_name']} | {p['baseline_pa']:.2f} | {p['preseason_pa']:.2f} | {p['employment_pa']:.2f} | {p['next_pa']} | {p['employment_value']:.3f} | {p['next_value']:.3f} |")
        lines.append('')
        lean.append({k:c[k] for k in ['selection','information_date','actual_inputs','employment_source','dated_records','source_history','actual_history','training_profiles','peers','candidate_fit_with_new_inputs_zero','probe_interpretation']}
            |dict(player=r['player_name'],player_id=r['player_id'],origin_year=r['origin_year'],review_note=review['cases'][key],saved_terms=compact,
            forecasts={k:r[k] for k in ['baseline_p','preseason_p','employment_p','baseline_conditional_pa','preseason_conditional_pa','employment_conditional_pa',
                'baseline_pa','preseason_pa','employment_pa','baseline_rate','baseline_value','preseason_value','employment_value','next_pa','next_value']}))
    lines+=['## Decision after actual review','',review['decision'],'',review['next_step']]
    (e.OUT/'player-walkthrough.md').write_text('\n'.join(lines)+'\n',encoding='utf8');e.write('reviewed-case-summary.json',lean)
    v.update(player_walkthrough_status='complete',notes_sha256=sha256_file(rp));e.write('verification.json',v)
    paths=[e.OUT/n for n in ['predictions.parquet','scored-predictions.parquet','scores.json','intervals.json','verification.json','reviewed-case-summary.json','player-walkthrough.md','exposure-support.json','assignment-qualification.json']]
    code=[Path(__file__),rp,e.ROOT/'docs/hitter-employment-v71-result.md']
    e.write('report.json',dict(player_walkthrough_status='complete',decision=review['decision'],next_step=review['next_step'],integrity=v,input_hashes=pre['input_hashes'],source_hashes=pre['source_hashes'],
        output_hashes={str(p):sha256_file(p) for p in paths},review_code_hashes={str(p):sha256_file(p) for p in code},protected_outcomes_used=False,
        frozen_forecast_changed=False,deployed_explorer_changed=False,whole_goal_complete=False))
    archive=e.ROOT/'reports/model-evidence/hitter-employment-v71';archive.mkdir(parents=True,exist_ok=True)
    for n in ['report.json','scores.json','intervals.json','verification.json','reviewed-case-summary.json','player-walkthrough.md','exposure-support.json','assignment-qualification.json']:(archive/n).write_bytes((e.OUT/n).read_bytes())
    print('Actual employment player review sealed; no automatic promotion.',flush=True)


if __name__=='__main__':main()
