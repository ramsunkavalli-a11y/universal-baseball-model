"""Complete the player review before choosing a next representation."""
from pathlib import Path
import shutil
import polars as pl
from score_practical_hitter_v31 import paired
from universal_baseball.storage import sha256_file
import evaluate_hitter_prospect_pooling_v54 as e


def main():
    cs=e.read(e.OUT/'cases.json');notes_path=e.ROOT/'config/practical_hitter_prospect_pooling_v54_case_notes.json';notes=e.read(notes_path)
    assert set(notes)=={f"{c['origin']['player_id']}|{c['origin']['origin_year']}" for c in cs}
    pre=e.read(e.OUT/'preflight.json');assert all(sha256_file(Path(p))==h for p,h in pre['input_hashes'].items())
    scores=e.read(e.OUT/'scores.json');q=pl.read_parquet(e.OUT/'predictions.parquet')
    extra=paired(q.filter(pl.col('prior_debut')==0),'prospect_pa_only','repaired','value');e.write('pa-only-interval.json',extra)
    lines=['# Shared prospect models and actual player review','',
        'Seven complete source-to-fit reviews. The full shared candidate is not adopted: modest workload improvement is offset by worse hitting and overconfident rare-profile extrapolation. Its PA-only construction remains qualified research, not a proven delivered-value win. All established-player forecasts remain bit-exact.','',
        'Inputs use repaired three-year counts separately by fourteen leagues, draft context, rankings, age and role. Current highest observed level comes from current-year positive PA, even a cameo; it is not asserted to be the season-ending job. Log exposure and simple age/draft × upper-level interactions supplement that indicator. StandardScaler learns each head mean/scale from its actual chronological, held-player-excluded training subset. Logistic and Ridge penalties/settings are unchanged after results. No future public projection, player identity or protected season enters training.','',
        '| Scope | Rows | Baseline PA RMSE | Shared PA RMSE | Baseline rate RMSE | Shared rate RMSE | Baseline offense RMSE | Shared offense RMSE | PA only offense RMSE |','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for s in scores[:5]:
        a,b,t=s['scores']['repaired'],s['scores']['shared'],s['scores']['prospect_pa_only']
        lines.append(f"| {s['scope']} | {s['rows']} | {a['pa_rmse']:.3f} | {b['pa_rmse']:.3f} | {s['rates']['repaired']['rmse']:.4f} | {s['rates']['shared']['rmse']:.4f} | {a['value_rmse']:.5f} | {b['value_rmse']:.5f} | {t['value_rmse']:.5f} |")
    lines += ['', 'Rate scoring uses actual PA among future participants and equal target years. All non-arrivals remain in workload/contribution scoring. Rate is the custom fixed-event origin-centered wins/600, not official wOBA, park-neutral latent skill or current MLB-equivalent DSL ability. Offense includes replacement only. Four origin-selected peers use age/stage/exposure/draft rank without future outcomes; they do not establish identical health or talent. Sparse profile counts remain qualifications despite shared slopes.','']
    for c in cs:
        o=c['origin'];key=f"{o['player_id']}|{o['origin_year']}"
        lines += [f"## {o['player_name']} from {o['origin_year']} to {o['target_year']}",'',
            f"Player {o['player_id']}, row {o['row_id']}, fold {o['outer_fold']}; age {o['age']}, highest current observed {c['known_highest_current']}. Selection: {', '.join(c['selection'])}.",'',
            '| Year | League | PA | HR | K | UBB |','|---|---|---:|---:|---:|---:|']
        for h in c['source_history']:lines.append(f"| {h['season']} | {h['bucket']} | {h['plate_appearances']} | {h['home_runs']} | {h['strike_outs']} | {h['unintentional_walks']} |")
        lines += ['',f"Draft {o['draft_year']}, pick {o['pick_number']}, class {o['draft_school_class'] or 'unknown'}. Existing neutral 100-opportunity pooling is inherited; no park/opponent adjustment is newly introduced.",'',
            '| Forecast | Appearance probability | Conditional PA | Expected PA | Batting wins per 600 | Offense wins |','|---|---:|---:|---:|---:|---:|']
        for a,label in [('repaired','Corrected baseline'),('shared','Shared prospect')]:
            lines.append(f"| {label} | {o[a+'_p']:.6f} | {o[a+'_conditional_pa']:.6f} | {o[a+'_pa']:.6f} | {o[a+'_rate']:.6f} | {o[a+'_value']:.6f} |")
        lines += [f"| Actual | {int(o['next_pa']>0)} | Not a forecast | {o['next_pa']} | {format(o['next_batting_rate'],'.6f') if o['next_pa'] else 'unobserved'} | {o['next_value']:.6f} |",'',
            f"PA-only offense {o['prospect_pa_only_value']:.6f}, rate-only offense {o['prospect_rate_only_value']:.6f}. Shared expected PA is {o['shared_p']:.9f} × {o['shared_conditional_pa']:.9f}; offense adds origin replacement {o['origin_replacement_rate']:.9f}/PA to the rate/600.",'']
        for h,t in c['heads'].items():
            lines += [f"{h}: intercept {t['reference']:.9f}, exact linear sum {t['raw_prediction']:.9f}, linked output {t['linked_prediction']:.9f}. Each contribution is coefficient × (input minus training mean)/training scale.",'',
                '| Feature | Origin input | Training mean | Training scale | Fitted contribution |','|---|---:|---:|---:|---:|']
            for z in t['feature_effects'][:5]:lines.append(f"| {z['feature']} | {z['input']:.7f} | {z['training_mean']:.7f} | {z['training_scale']:.7f} | {z['effect']:.7f} |")
            lines.append('')
        lines += ['Broad actual training-profile support: '+', '.join(f"{p['head']} {p['profile_players']} distinct people" for p in c['training_profile'])+'.','',notes[key],'',
            '| Origin selected peer | Baseline PA | Shared PA | Actual PA | Shared rate | Actual rate |','|---|---:|---:|---:|---:|---:|']
        for p in c['peers']:lines.append(f"| {p['player_name']} | {p['repaired_pa']:.2f} | {p['shared_pa']:.2f} | {p['next_pa']} | {p['shared_rate']:.4f} | {format(p['next_batting_rate'],'.4f') if p['next_pa'] else 'unobserved'} |")
        lines.append('')
    lines += ['## Decision and next step','',
        'Do not adopt the full candidate. Never-debut offense MSE worsens +.001886, nominal interval [-.000383,+.004730]; conditional rate MSE worsens +1.2260, [.5535,1.9774]. Prospect PA MSE improves -10.974, [-45.147,+20.705], a modest uncertain gain. PA-only offense MSE changes -.0000292, [-.000558,+.000459], not an established delivered-value gain.','',
        'Upper-never PA increases 73,593 to 78,029 versus 92,891 actual, while lower PA falls 7,652 to 6,762 versus 5,194. Total never-debut arrivals worsen 683 to 666 versus 787, despite better upper-group allocation. Expected total offense becomes close (219.39 versus 214.80 actual) but individual forecasts worsen. Holliday and Azocar explain why totals and products are insufficient.','',
        'The intended smooth pooling raises some fast-entry prospects, but StandardScaler amplifies rare rookie-sport count rates. Those rates have little variation among conditional training participants, so small known samples can become extreme standardized inputs. Holliday receives an implausibly firm +4.38 wins/600 while Bellinger is pulled down by older complex HR. This is a representation failure visible in exact fitted terms, not a reason to reject all prospect-specific prediction.','',
        'Next bounded repair: compare this same linear/hurdle construction using fixed baseball-unit scaling rather than dividing rare rate columns by tiny training standard deviations. Keep settings, source, population, folds and outputs unchanged and retain both controls. Do not tune to Holliday or Kurtz, introduce a new library, or claim profile support has increased. Separately dated scouting and MLB availability still remain missing information.']
    path=e.OUT/'player-walkthrough.md';path.write_text('\n'.join(lines)+'\n',encoding='utf8')
    verification=e.read(e.OUT/'verification.json');verification.update(player_walkthrough_status='complete',notes_sha256=sha256_file(notes_path),walkthrough_sha256=sha256_file(path));e.write('verification.json',verification)
    e.write('report.json',dict(player_walkthrough_status='complete',cases=len(cs),full_candidate_adopted=False,pa_only_research=True,
        rare_rate_scaling_problem_identified=True,meaningful_joint_improvement=False,established_forecasts_unchanged=True,
        protected_outcomes_used=False,frozen_forecast_changed=False,
        evidence_hashes={str(p.relative_to(e.ROOT)):sha256_file(p) for p in [notes_path,path,e.OUT/'scores.json',e.OUT/'intervals.json',e.OUT/'predictions.parquet']}))
    e.write('preflight-summary.json',dict(cells=35,heads=105,features=pre['features'],checks=[dict(year=c['year'],fold=c['fold'],heads=c['preflight']) for c in pre['cells']],
        input_hashes=pre['input_hashes'],prefit_output_namespace_correction=pre.get('prefit_output_namespace_correction')))
    dest=e.ROOT/'reports/model-evidence/practical-hitter-prospect-pooling-v54';dest.mkdir(parents=True,exist_ok=True)
    for name in ['report.json','scores.json','intervals.json','pa-only-interval.json','verification.json','preflight-summary.json','cases.json','player-walkthrough.md','fit-report.json']:shutil.copy2(e.OUT/name,dest/name)
    print('Seven actual reviews complete; retain corrected baseline, full prospect candidate not adopted.',flush=True)


if __name__=='__main__':main()
