"""Close the reviewed experiment, not the unfinished practical-model goal."""
import prepare_practical_hitter_v31 as r
from universal_baseball.storage import sha256_file


def main():
    report=r.read(r.OUT/'score-report.json');assert report['player_walkthrough_status']=='pending'
    check=r.read(r.OUT/'verification.json');assert check['saved_heads_replayed']==700
    cases=r.read(r.OUT/'cases.json');notes=r.read(r.ROOT/'config/practical_hitter_v31_case_notes.json')
    for c in cases:
        o=c['origin'];assert f"{o['player_id']}:{o['origin_year']}" in notes
    lines=['# Hitter model comparison and player review','',
        'The broader rebuild improves next-year MLB playing-time predictions against V24, but does not improve delivered batting value against the strongest existing reference. '
        'Keep the workload architecture as a useful development result; do not replace the whole model with this batch. '
        'The practical-model goal remains open. This report covers historical next-calendar-year PA and batting plus replacement wins, not full WAR, current minor-league MLB-equivalent talent or career trade value.','',
        '## What changed','',
        'The source now includes never-debuted prospects and established hitters, retaining all 4,396 old comparison rows and exits. '
        'It separates Mexican League from affiliated AAA and DSL from other rookie leagues, uses dated reported position and soft December roster context, and reconstructs three years of separate-league event counts. '
        'A prefit correction replaces the largest season stint with all MLB stints when computing observed career PA. '
        'The two staged models forecast probabilities of zero, brief, partial and regular MLB use, then expected workload and delivered value within those states. '
        'The direct model forecasts expected PA and value without a participation distribution. '
        'Raw event rates are not park-adjusted; the existing adjustment packages have different fold provenance and were not silently reused.','',
        'All seven cutoffs use only mature earlier outcomes, with the entire held-player group excluded. '
        'All 700 saved heads replay exactly, all source event-rate inputs reconcile, and 14,857 historical MLB value labels independently recompose from the source events. '
        'Execution correctness is not predictive success. Conditional-head support is separately audited; that supplemental audit occurred during the fixed fits, not before every fit. '
        'No protected 2026 result, frozen forecast or production explorer was changed.','',
        '## Matched results','',
        'Errors give each year equal weight. RMSE emphasizes larger misses; MAE is the average absolute miss. '
        'Public comparisons retain all zero-PA outcomes, but their exact preseason dates differ from the December cutoff and their converted value has an environment caveat. '
        'Raw public rate results therefore cannot prove superior hitting talent.','']
    for scope,title in [('v24_matched','Same 4396 recent debut forecasts'),('public_active','Same 1789 public forecasts'),('legacy_n_matched','Same 21819 older reference forecasts')]:
        s=next(v for v in report['scores'] if v['scope']==scope)
        lines += ['### '+title,'','| Model | PA RMSE | PA MAE | Batting value RMSE |','|---|---:|---:|---:|']
        for arm in ['base_hurdle','detail_hurdle','direct_detail','v24','legacy_n','steamer']:
            if arm in s['scores']:
                v=s['scores'][arm];lines.append(f"| {arm} | {v['pa_rmse']:.2f} | {v['pa_mae']:.2f} | {v['value_rmse']:.4f} |")
        lines.append('')
    lines+=['The simple staged workload improves V24 PA RMSE from 128.62 to 125.87; paired MSE difference is −701, nominal player-cluster interval −1096 to −274. '
        'Detailed staged public PA RMSE is 145.23 versus 149.12 V24 and 135.02 Steamer. '
        'It meets the declared 10% RMSE-gap target, but PA MAE 113.18 still fails the 15%-over-Steamer target of 106.26. '
        'On the older reference overlap, detailed value RMSE 0.4548 loses to N at 0.4458; paired MSE difference +0.00805, interval +0.00308 to +0.01269. '
        'N uses different inherited fitting provenance, so this practical comparison does not isolate a feature or family effect. '
        'The direct-value arm also loses. Additional raw event detail does not establish an overall gain over the simple staged model.','',
        '## Cohort totals and the 2021 stress year','',
        '| Information cutoff | Actual cohort PA | Simple PA gap | Detailed PA gap | Detailed batting value gap |','|---|---:|---:|---:|---:|']
    for y in r.YEARS:
        s=next(v for v in report['scores'] if v['scope']=='origin_'+str(y));b=s['scores']['base_hurdle'];d=s['scores']['detail_hurdle']
        lines.append(f"| {y} | {s['actual_pa']:,} | {b['pa_total']-s['actual_pa']:+,.0f} | {d['pa_total']-s['actual_pa']:+,.0f} | {d['value_total']-s['actual_value']:+.1f} |")
    lines += ['',
        'The 2021 cutoff still underallocates roughly 19,000–21,000 PA. It is not acceptable to bury this under thousands of zero outcomes or force it to the exposed answer. '
        'Canceled 2020 MiLB history is flagged, but the first post-cancellation training folds cannot learn a novel cancellation effect from earlier years. '
        'This is a representation/support concern to test, not a proven causal diagnosis of all 2021 error. '
        'The 2022 universal DH is another target-environment change: before it, hitter cohorts omit many pure pitcher batting rows with negative batting value, so their observed value may exceed the full-league 570 allocation. '
        'The full-league target itself still recomposes; a hitter-cohort total above 570 is not automatically an accounting bug.','',
        '## Player walkthroughs','',
        'Fixed cases, each core model’s largest gains and harms, an ordinary case, pre-debut misses and rate extremes are all retained. '
        'Peers are nearest on cutoff-known age, career stage, exposure and observed MLB quality, never on future outcomes. '
        'Minor-rate probes use unchanged saved fits and unchanged exposure; they are artificial mechanism checks, not causal estimates or replacement forecasts. '
        'Full actual feature vectors, all raw denominators, ridge contribution terms, support counts and peer identities are preserved in cases.json.','']
    for c in cases:
        o=c['origin']|c['actual_features'];key=f"{o['player_id']}:{o['origin_year']}"
        lines += [f"### {o['player_name']} {o['origin_year']} to {o['target_year']}",'',
            f"Age {o['age']:g}; {o['stage']}; position code {o['source_position']}; MLB PA newest to oldest {o['pa_0']}/{o['pa_1']}/{o['pa_2']}; "
            f"captured December listing {o['on_40man']}; observed career MLB PA {o['career_mlb_observed_pa']}. "
            f"Selected for {', '.join(c['selection'])}.",'',
            '| Source year and league | PA | HR | K | UBB | BABIP hits and opportunities |','|---|---:|---:|---:|---:|---:|']
        for h in c['raw_level_history']:lines.append(f"| {h['season']} {h['bucket']} | {h['plate_appearances']} | {h['home_runs']} | {h['strike_outs']} | {h['unintentional_walks']} | {h['babip_hits']} / {h['babip_opportunities']} |")
        lines+=['','Actual inputs keep leagues/years separate. Each detailed event rate uses 100 fixed prior opportunities; MLB observed quality uses a 1,200-PA denominator prior. '
            'Age, exposure, source position, career stage, missingness and roster context are also included. No learned park or opponent neutralization appears in this branch.','',
            '| Forecast | Expected PA | Expected batting plus replacement wins | Regular chance | Same fit neutral minor PA |','|---|---:|---:|---:|---:|']
        for arm in ['v24','legacy_n','steamer']:
            if o.get(arm+'_pa') is not None:lines.append(f"| {arm} | {o[arm+'_pa']:.1f} | {o[arm+'_value']:.3f} | — | — |")
        for arm,v in c['arms'].items():
            chance=f"{100*v['probabilities'][3]:.1f}%" if 'probabilities' in v else 'not estimated'
            lines.append(f"| {arm} | {v['pa']:.1f} | {v['value']:.3f} | {chance} | {v['neutral_minor_rate_probe']['pa']:.1f} |")
        lines += [f"| Actual MLB next year | {o['next_pa']} | {o['next_value']:.3f} | — | — |",'',
            'Detailed staged calculation: probabilities '+', '.join(f'{v:.4f}' for v in c['arms']['detail_hurdle']['probabilities'])+'; '
            'conditional PA '+', '.join(f'{v:.1f}' for v in c['arms']['detail_hurdle']['conditional_pa'])+'; '
            'conditional value '+', '.join(f'{v:.3f}' for v in c['arms']['detail_hurdle']['conditional_value'])+'. '
            'Expected outputs sum the corresponding probability-weighted conditional totals.','',
            'Conditional batting rates above MLB average per 600 PA: '+', '.join(f'{a} {v:+.3f}' for a,v in c['rates'].items())+'. '
            'PA-weighted heads estimate contribution-weighted performance; equal-active heads target a different average. Neither establishes current prospect talent.','',
            'Local conditional training people: '+', '.join(f"{v['head']} {v['conditional_profile_players']}" for v in c['conditional_support'])+'. '
            'These coarse neighborhoods can still conceal rare feature-level extrapolation.','',notes[key],'',
            'Origin-blind peers: '+'; '.join(f"{p['player_name']} (age {p['age']:g}, current MLB {p['pa_0']} PA, detailed forecast {p['detail_hurdle_pa']:.0f} PA / {p['detail_hurdle_value']:.2f} value, actual {p['next_pa']} / {p['next_value']:.2f})" for p in c['comparisons'])+'.','']
    lines += ['## Decisions and next structural work','',
        'Retain the broad source rebuild and staged-workload development result. Keep the stronger archived hitting/value references mandatory. '
        'Do not deploy the direct-value replacement, declare the extra detail useless, or use the unstable conditional ridge outputs as prospect grades. '
        'The goal is not complete: average playing-time error, 2021 allocation, temporary-absence/roster interpretation and low-sample pedigree gaps remain material.','',
        'Next compare a coherent core using exposure-weighted batting histories, reliable cross-level shrinkage and explicit cutoff-known career context. '
        'Use existing draft/signing investment for brief professional samples rather than collecting new college data. '
        'Separate temporary absence from ordinary exit and treat captured roster presence as context, not reserve-rights certification. '
        'Check recent role/late-season use where dated source coverage actually exists. '
        'Correct rare-feature linear scaling before judging that family; do not respond with another library-only tournament. '
        'Park/opponent/contact inputs remain a supported extension once their chronological provenance is rebuilt. '
        'Reconcile forecasts against reasonable origin-known opportunity totals without retrospective rescaling to a held-out answer.','',
        'The separate team-filtered historical explorer exposes all three research models and actual outcomes; it is not a production replacement. '
        'Longer calendar paths, nonbatting WAR, club-control and trade value remain separate unfinished goals.']
    path=r.OUT/'player-walkthrough.md';path.write_text('\n'.join(lines),encoding='utf8')
    report.update(player_walkthrough_status='complete',player_walkthrough_path=str(path),
        disposition='Retain broad source/staged-workload development gain; withhold replacement value model; repair source-context/reliability and preserve stronger references.',
        practical_model_goal_complete=False,reviewed_cases=len(cases),execution_verified=True,predictive_value_improved=False,production_forecast_changed=False)
    report['output_hashes'][str(path)]=sha256_file(path);report['case_notes_sha256']=sha256_file(r.ROOT/'config/practical_hitter_v31_case_notes.json')
    r.write('score-report.json',report);check['player_walkthrough_status']='complete';r.write('verification.json',check)
    print(f'Completed {len(cases)} actual stats-to-forecast reviews. Practical model goal remains active.')


if __name__=='__main__':main()
