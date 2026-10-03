"""Persist the actual rank/source/forecast review before choosing another test."""
import evaluate_hitter_scouting_v47 as e
from universal_baseball.storage import sha256_file


def main():
    cases=e.r.read(e.OUT/'cases.json');p=e.ROOT/'config/practical_hitter_scouting_v47_case_notes.json';notes=e.r.read(p)
    assert len(cases)==len(notes)==15
    source=e.r.read(e.OUT/'source-review.json');assert source['player_walkthrough_status']=='complete'
    lines=['# Historical scouting and MLB playing time','',
        'Historical rankings improve readiness forecasts for some highly ranked prospects, but stale preseason absence harms newly drafted and rising prospects. This review covers fifteen actual model cases after nine source cases. The comparison predicts next-calendar-year MLB PA and batting-plus-replacement contribution, not full WAR, a guaranteed role, present-day MLB skill or six years of club control.','',
        'All 30,506 forecasts are retained, including non-arrivals and 218 unverified roster-only cases. Origins 2016–2018 and 2021–2024 predict 2017–2019 and 2022–2025. Target 2020 is excluded; its source MLB evidence is preserved and canceled MiLB is not zero performance. Each model excludes the held player group and future labels. Twelve rank inputs are added to 239 count/games/draft inputs; hitting rate is exactly unchanged.','',
        'Peers use origin age, stage, debut status, workload, quality and ranking distance without future outcomes; they do not guarantee identical draft pedigree or contact shape. The full 251 inputs, tree paths, history and support are in cases.json. Path terms reconstruct a fitted mean, not causal changes between two refitted ensembles. Unknown list evidence is -1, not zero talent. Annual rank tables are retrospective reproductions, not certified archived editions; the Brinson source disagreement remains disclosed.','']
    for c in cases:
        o=c['origin'];key=f"{o['player_id']}|{o['origin_year']}";assert key in notes
        lines.extend([f"## {o['player_name']} {o['origin_year']} to {o['target_year']}",'',
            f"Player {o['player_id']}, row {o['row_id']}, fold {o['outer_fold']}; {', '.join(c['selection'])}. Age {o['age']}; {o['stage']}; career observed MLB PA {o['career_mlb_observed_pa']}.",'',
            '| Season | Level | PA | Source games | HR | K | UBB |','|---|---|---:|---:|---:|---:|---:|'])
        for h in c['source_history']:lines.append(f"| {h['season']} | {h['bucket']} | {h['plate_appearances']} | {h['games_played']} | {h['home_runs']} | {h['strike_outs']} | {h['unintentional_walks']} |")
        lines.extend(['','Source ranks: '+str(c['source_ranks'])+'.','', 'Actual twelve added inputs: '+str(c['added_inputs'])+'.','',
            '| Forecast | Expected MLB PA | Batting wins per 600 PA | Batting plus replacement wins |','|---|---:|---:|---:|'])
        for a,rate in [('retired_games','cohort_rate'),('scout','scout_rate'),('retired_safe_ridge','safe_ridge_rate')]:lines.append(f"| {a} | {o[a+'_pa']:.4f} | {o[rate]:.5f} | {o[a+'_value']:.6f} |")
        lines.extend([f"| Actual | {o['next_pa']} | {'Unobserved at zero PA' if not o['next_pa'] else o['next_batting_rate']} | {o['next_value']:.6f} |",'',
            f"Raw candidate PA {c['scout_accounting']['raw_prediction']:.6f}; bounded and availability-adjusted PA {o['scout_pa']:.6f}. Contribution = {o['scout_pa']:.6f} × ({o['cohort_rate']:.6f}/600 + {o['origin_replacement_rate']:.8f}). The separate working assembly uses its own different fixed rate; it is not silently mixed into the rank comparison.",''])
        for keytrace,title in [('control_accounting','Count and games control'),('scout_accounting','Ranking candidate')]:
            t=c[keytrace];terms=t['feature_effects'][:8]+[x for x in t['feature_effects'][8:] if x['feature'].startswith('scout_')]
            lines.extend([f'### {title} fitted path','',f"Reference {t['reference']:.6f} plus the complete stored terms reconstructs raw PA {t['raw_prediction']:.6f}.",'',
                '| Input | Encoded value | Path accounting in PA |','|---|---:|---:|'])
            for x in terms:lines.append(f"| {x['feature']} | {x['input']} | {x['path_effect']:.6f} |")
            lines.append('')
        lines.extend([f"General distinct-player profile: {c['training_profile']}. Rank-specific profile: {c['rank_profile']}. Actual mature training support: {c['training_support']}.",'',notes[key],'',
            '| Origin selected peer | Age | MLB PA | Minor PA | Listed | Rank score | Control PA | Candidate PA | Actual PA | Actual contribution |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|'])
        for q in c['peers']:lines.append(f"| {q['player_name'] or q['player_id']} | {q['age']} | {q['pa_0']} | {q['minor_pa_0']} | {q['scout_listed_0']} | {q['scout_rank_score_0']} | {q['retired_games_pa']:.2f} | {q['scout_pa']:.2f} | {q['next_pa']} | {q['next_value']:.5f} |")
        lines.append('')
    lines.extend(['## Cohort findings and decision','',
        'The broad incremental games-control intervals include no gain, while listed and top20 intervals favor rankings. Public workload MAE is 110.553 versus Steamer 92.399 and still fails the predeclared 15 percent tolerance. Upper-minor individual error improves but total expected PA falls to 95,576 versus 102,951 actual, farther below the control. Lower-minor expected PA is 10,509 versus 6,072 actual; the small pooled score does not establish calibration. Origins 2017 and 2024 worsen versus games, while 2021 improves on PA but contribution totals remain high.','',
        'Retain ranked-prospect readiness evidence as qualified research, not the unmodified whole-population forecast. Do not replace working V33b plus retirement, the frozen 2026 forecast or its deployed explorer. Stale absence for new draftees and fast movers, elite conditional-rate compression, sparse ranked training profiles and current-MLB availability remain unresolved. A justified next bounded repair is to prevent a stale absent ranking from overwriting the count-based fallback; test that explicit source-applicability policy as development evidence, not a new algorithm sweep or independent confirmation. All fifteen player reviews are complete before this decision.'])
    out=e.OUT/'player-walkthrough.md';out.write_text('\n'.join(lines)+'\n',encoding='utf8')
    v=e.r.read(e.OUT/'verification.json');v.update(player_walkthrough_status='complete',manual_notes_sha256=sha256_file(p),walkthrough_sha256=sha256_file(out));e.write('verification.json',v)
    e.write('report.json',dict(player_walkthrough_status='complete',cases=15,source_reviews=9,rank_source_usable=True,source_edition_qualified=True,
        qualified_rank_readiness_retained=True,whole_population_candidate_adopted=False,working_replaced=False,practical_goal_complete=False,
        public_mae_tolerance_pass=False,cohort_reasonability_pass=False,profile_certification_pass=False,protected_outcomes_used=False,
        frozen_forecast_changed=False,manual_notes_sha256=sha256_file(p),walkthrough_sha256=sha256_file(out)))
    pre=e.r.read(e.OUT/'preflight.json')
    e.write('preflight-summary.json',dict(full_preflight_path=str(e.OUT/'preflight.json'),full_preflight_sha256=sha256_file(e.OUT/'preflight.json'),
        **{k:v for k,v in pre.items() if k!='cells'},cells=[{k:v for k,v in c.items() if k not in ['training_row_ids','test_row_ids']} for c in pre['cells']]))
    print('Fifteen actual model reviews complete; retain qualified rank evidence, no whole-model promotion.',flush=True)


if __name__=='__main__':main()
