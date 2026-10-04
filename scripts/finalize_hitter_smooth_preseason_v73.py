"""Seal the matched ranking comparison after real player and boundary review."""
from pathlib import Path
import numpy as np
import polars as pl
from universal_baseball.storage import sha256_file
import evaluate_hitter_smooth_preseason_v73 as e


def main():
    pre=e.read(e.OUT/'preflight.json');v=e.read(e.OUT/'verification.json')
    cases=e.read(e.OUT/'cases.json')+e.read(e.OUT/'additional-cases.json')
    rp=e.ROOT/'config/hitter_smooth_preseason_v73_review.json';review=e.read(rp)
    assert v['replayed_heads']==140 and len(cases)==13
    assert set(review['cases'])=={f"{c['origin']['player_id']}|{c['origin']['origin_year']}" for c in cases}
    assert all(len(s)>300 for s in review['cases'].values())
    assert next(c['origin']['player_name'] for c in cases if c['origin']['player_id']==670867)=='Kevin Maitan'
    assert next(c['origin']['player_name'] for c in cases if c['origin']['player_id']==669394)=='Jake Burger'
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    rate=e.read(e.OUT/'fixed-hitting-traces.json');rates={(c['player_id'],c['origin_year']):c for c in rate['cases']}
    for p,h in rate['source_hashes'].items():assert sha256_file(Path(p))==h,p
    heads={}
    for n in e.read(e.OUT/'fits.json'):
        for h in n['heads']:
            for p,k in [(h['path'],'sha256'),(h['old_path'],'old_sha256')]:heads[p]=h[k];assert sha256_file(Path(p))==h[k]
    q=pl.read_parquet(e.OUT/'scored-predictions.parquet');never=q.filter(pl.col('prior_debut')==0)
    bounds=never.group_by('origin_year').agg(*[x for a in e.ARMS[2:] for x in [
        (pl.col(a+'_raw_conditional_pa')<1).sum().alias(a+'_low'),(pl.col(a+'_raw_conditional_pa')>800).sum().alias(a+'_high'),
        pl.col(a+'_raw_conditional_pa').min().alias(a+'_min'),pl.col(a+'_raw_conditional_pa').max().alias(a+'_max')]]).sort('origin_year')
    e.write('boundary-review.json',dict(by_origin=bounds.to_dicts(),
        actual_active_lower_bounds={a:int(never.filter((pl.col('next_pa')>0)&(pl.col(a+'_raw_conditional_pa')<1)).height) for a in e.ARMS[2:]},
        interpretation='Most bounded rows do not play; their conditional response is unobserved. Small expected PA can conceal an implausible conditional head. This is not a blanket rejection based on the number of clips.'))
    employment_root=e.ROOT/'reports/generated/hitter-employment-v71'
    ef=pl.read_parquet(employment_root/'features.parquet').select('row_id','employment_year_fa')
    group=q.join(ef,on='row_id',validate='1:1').filter((pl.col('employment_year_fa')==1)&(pl.col('pa_0')>=200)&(pl.col('baseline_rate')>0))
    assert len(group)==102 and group['player_id'].n_unique()==82 and int(group['next_pa'].sum())==37613
    e.write('free-agent-control.json',dict(selection='Origin-known documented current free agency, at least 200 current MLB PA, positive fixed hitting forecast.',
        rows=len(group),people=group['player_id'].n_unique(),expected_pa=float(group['preseason_pa'].sum()),actual_pa=int(group['next_pa'].sum()),
        expected_appearances=float(group['preseason_p'].sum()),actual_appearances=int((group['next_pa']>0).sum()),
        row_ids=group['row_id'].to_list(),by_origin=group.group_by('origin_year').agg(pl.len(),pl.col('preseason_pa').sum(),pl.col('next_pa').sum(),
            pl.col('preseason_p').sum(),(pl.col('next_pa')>0).sum().alias('actual_appearances')).sort('origin_year').to_dicts(),
        interpretation='Descriptive pooled control, not independent-season proof of calibration. Belt remains in the group and original error totals. No blanket unsigned-player penalty follows.',
        source_hashes={str(employment_root/'features.parquet'):sha256_file(employment_root/'features.parquet')}))
    scores=e.read(e.OUT/'scores.json')
    lines=['# Fresher rankings and the smooth prospect model','',review['decision'],'',
        'The same 30,506 forecasts and 171 prospect inputs are retained. Only eight ranking-vintage inputs change in the matched smooth contrast. Established-player forecasts and the 199-input hitting model remain fixed. Target: next-calendar-year MLB use and custom batting plus replacement, not full WAR, career quality or six years of control.','',
        '| Group | Rows | Fresh tree PA RMSE | Old smooth PA RMSE | Fresh smooth PA RMSE | Fresh tree MAE | Fresh smooth MAE | Fresh tree offense RMSE | Fresh smooth offense RMSE |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for s in scores[:7]:
        a,b,d=[s['scores'][k] for k in ['preseason','old_smooth','smooth_preseason']]
        lines.append(f"| {s['scope']} | {s['rows']} | {a['pa_rmse']:.3f} | {b['pa_rmse']:.3f} | {d['pa_rmse']:.3f} | {a['pa_mae']:.3f} | {d['pa_mae']:.3f} | {a['value_rmse']:.6f} | {d['value_rmse']:.6f} |")
    lines+=['','Losses weight target years equally. Raw totals are not rescaled; intervals are paired whole-player development evidence. Release dates are documented, but first-publication ranking table vintages and equal public-forecast information dates remain unverified.','',
        'The original review ID for the named Maitan case selected Burger. Both are retained, with the correction recorded separately. The largest raw conditional-PA case is added by an ordered boundary rule; no forecast or original selection is removed.','']
    lean=[]
    for c in cases:
        r=c['origin'];key=f"{r['player_id']}|{r['origin_year']}";rt=rates[(r['player_id'],r['origin_year'])]
        assert np.isclose(rt['trace']['raw_prediction'],r['baseline_rate'],atol=1e-10,rtol=0)
        assert sha256_file(Path(rt['head_path']))==rt['head_sha256']
        lines += [f"## {r['player_name']} {r['origin_year']} to {r['target_year']}",'',
            f"ID {r['player_id']}; row {r['row_id']}; fold {r['outer_fold']}; age input {r['age']}; {r['stage']}. Information date {c['information_date']}. Selected: {', '.join(c['selection'])}.",'',
            '| Ranking input | Old source | Fresh source |','| --- | ---: | ---: |']
        for name,old in c['old_scouting'].items():lines.append(f"| {name} | {old:g} | {c['new_scouting'][name]:g} |")
        lines+=['','| Known season | Level | PA | HR | K | UBB |','| --- | --- | ---: | ---: | ---: | ---: |']
        for h in c['source_history']:lines.append(f"| {h['season']} | {h['bucket']} | {h['plate_appearances']} | {h['home_runs']} | {h['strike_outs']} | {h['unintentional_walks']} |")
        lines+=['','| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting per 600 PA | Offense |',
            '| --- | ---: | ---: | ---: | ---: | ---: |']
        for a in e.ARMS:lines.append(f"| {a} | {r[a+'_p']:.6f} | {r[a+'_conditional_pa']:.3f} | {r[a+'_pa']:.3f} | {r['baseline_rate']:.5f} | {r[a+'_value']:.5f} |")
        lines += [f"| Actual | {int(r['next_pa']>0)} | not a forecast | {r['next_pa']} | {r['next_batting_rate'] if r['next_pa'] else 'unobserved'} | {r['next_value']:.5f} |",'',
            f"Candidate product {r['smooth_preseason_p']:.9f} × {r['smooth_preseason_conditional_pa']:.9f}; offense yield {r['baseline_rate']:.9f}/600 + {r['origin_replacement_rate']:.9f}.",'',
            'Actual MLB counts: '+str(c['actual_history'])+'. No PA is not observed zero batting talent.','',
            '| Earlier profile | Head | Profile detail | Distinct people |','| --- | --- | --- | ---: |']
        for p in c['training_profiles']:lines.append(f"| {p['arm']} | {p['head']} | {p['kind']} | {p['profile_people']} |")
        lines+=['','Broad counts do not create matched elite-star analogues. Full profile definitions and all actual inputs are in the machine-readable case summary.','']
        compact={}
        for head,arms in c['saved_traces'].items():
            compact[head]={}
            for a,t in arms.items():
                assert np.isclose(t['reference']+sum(x['effect'] for x in t['feature_effects']),t['raw_prediction'],atol=1e-8)
                expected=r[a+('_raw_p' if head=='participation' else '_raw_conditional_pa')]
                assert np.isclose(t['linked_prediction'],expected,atol=1e-8)
                top=t['feature_effects'][:8];ranking=[x for x in t['feature_effects'] if x['feature'].startswith('scout_')]
                compact[head][a]=dict(reference=t['reference'],raw_prediction=t['raw_prediction'],linked_prediction=t['linked_prediction'],largest_terms=top,ranking_terms=ranking)
                lines += [f"Saved {a} {head}: reference {t['reference']:.6f}; additive output {t['raw_prediction']:.6f}; linked output {t['linked_prediction']:.6f}.",'',
                    'Largest standardized terms are exact accounting, not causal effects:','']
                for x in top:lines.append(f"- {x['feature']}: input {x['input']:.6f}, training scale {x['training_scale']:.6f}, standardized input {x['standardized_input']:.3f}, contribution {x['effect']:+.6f}.")
                lines+=['','Largest ranking contributions on this same fit: '+', '.join(f"{x['feature']} {x['effect']:+.6f}" for x in ranking[:4])+'. All ranking terms remain in the machine-readable summary.','']
            lines += [f"Same new fit with old ranking inputs: {c['candidate_fit_with_old_rankings'][head]:.6f}. {c['probe_interpretation']}",'']
        t=rt['trace'];assert np.isclose(t['reference']+sum(x['effect'] for x in t['feature_effects']),t['raw_prediction'],atol=1e-8)
        lines+= [f"Unchanged saved hitting head: reference {t['reference']:.6f}; prediction {t['raw_prediction']:.6f}. Largest terms on its deterministic input scale:",'']
        for x in t['feature_effects'][:8]:lines.append(f"- {x['feature']}: scaled input {x['input']:.6f}, contribution {x['effect']:+.6f}.")
        lines+=['',review['cases'][key],'','| Origin-selected peer | Fresh tree PA | Fresh smooth PA | Actual PA | Fresh smooth offense | Actual offense |',
            '| --- | ---: | ---: | ---: | ---: | ---: |']
        for p in c['peers']:lines.append(f"| {p['player_name']} | {p['preseason_pa']:.2f} | {p['smooth_preseason_pa']:.2f} | {p['next_pa']} | {p['smooth_preseason_value']:.3f} | {p['next_value']:.3f} |")
        lines.append('')
        lean.append({k:c[k] for k in ['selection','information_date','actual_inputs','old_scouting','new_scouting','source_history','actual_history','training_profiles','peers',
            'candidate_fit_with_old_rankings','probe_interpretation']}|dict(player=r['player_name'],player_id=r['player_id'],origin_year=r['origin_year'],
            forecasts={k:r[k] for k in ['next_pa','next_value','next_batting_rate','origin_replacement_rate','baseline_rate']+[a+'_'+x for a in e.ARMS for x in ['p','conditional_pa','pa','value']]},
            saved_terms=compact,fixed_hitting=rt,review_note=review['cases'][key]))
    lines+=['## Decision after actual review','',review['decision'],'',review['next_step']]
    (e.OUT/'player-walkthrough.md').write_text('\n'.join(lines)+'\n',encoding='utf8');e.write('reviewed-case-summary.json',lean)
    v.update(player_walkthrough_status='complete',reviewed_cases=len(cases),fixed_hitting_case_replays=len(cases),notes_sha256=sha256_file(rp),
        integrity_pass=True,matched_profile_support='sparse or absent for several focal active heads',predictive_result='fresh source helps old smooth model; model replacement uncertain/mixed',
        baseball_review='readiness gaps and conditional extrapolation persist',deployment_approved=False)
    e.write('verification.json',v)
    paths=[e.OUT/n for n in ['predictions.parquet','scored-predictions.parquet','scores.json','intervals.json','verification.json','cases.json','additional-cases.json',
        'reviewed-case-summary.json','player-walkthrough.md','boundary-review.json','free-agent-control.json','fixed-hitting-traces.json']]
    code=[Path(__file__),e.ROOT/'scripts/review_hitter_smooth_preseason_v73.py',rp,e.ROOT/'docs/hitter-smooth-preseason-v73-result.md',
        e.ROOT/'docs/hitter-smooth-preseason-v73-review-amendment.md',e.ROOT/'docs/hitter-review-judgment-v73.md']
    e.write('report.json',dict(player_walkthrough_status='complete',decision=review['decision'],next_step=review['next_step'],integrity=v,
        input_hashes=pre['input_hashes'],hitting_source_hashes=rate['source_hashes'],fitted_head_hashes=heads,
        output_hashes={str(p):sha256_file(p) for p in paths},review_code_hashes={str(p):sha256_file(p) for p in code},
        protected_outcomes_used=False,frozen_forecast_changed=False,deployed_explorer_changed=False,whole_goal_complete=False))
    archive=e.ROOT/'reports/model-evidence/hitter-smooth-preseason-v73';archive.mkdir(parents=True,exist_ok=True)
    for n in ['report.json','scores.json','intervals.json','verification.json','reviewed-case-summary.json','player-walkthrough.md','boundary-review.json','free-agent-control.json']:
        (archive/n).write_bytes((e.OUT/n).read_bytes())
    print('Thirteen real player reviews, all 140 opportunity replays and fixed hitting traces sealed; current candidate retained.',flush=True)


if __name__=='__main__':main()
