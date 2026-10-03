"""Complete the actual count-to-prior-to-forecast review before disposition."""
import numpy as np
import polars as pl
from universal_baseball.storage import sha256_file
import evaluate_hitter_reliability_v50 as e


def main():
    read=e.prior.old.r.read
    cases=read(e.OUT/'cases.json'); notes_path=e.ROOT/'config/practical_hitter_reliability_v50_case_notes.json'; notes=read(notes_path)
    keys={f"{c['origin']['player_id']}|{c['origin']['origin_year']}" for c in cases}
    assert len(cases)==25 and keys==set(notes)
    verification=read(e.OUT/'verification.json'); assert verification['saved_heads_replayed']==70
    f=pl.read_parquet(e.OUT/'scored-predictions.parquet'); primary=[]
    for a in ['fixed_reliability','learned_reliability']:
        g=f.filter(pl.col('next_pa')>0).with_columns((pl.col('next_pa')*((pl.col('binary_scout_rate')-pl.col('next_batting_rate'))**2-(pl.col(a+'_rate')-pl.col('next_batting_rate'))**2)).alias('weighted_gain'))
        for label,q in [('largest gain',g.sort('weighted_gain',descending=True)),('largest harm',g.sort('weighted_gain'))]:
            o=q.row(0,named=True); assert f"{o['player_id']}|{o['origin_year']}" in notes
            primary.append(dict(arm=a,selection=label,player_id=o['player_id'],origin_year=o['origin_year'],player_name=o['player_name'],actual_pa=o['next_pa'],weighted_gain=o['weighted_gain']))
    e.write('primary-loss-case-check.json',dict(cases=primary,interpretation='PA-weighted error-squared contribution check, not a new fitted model or independent validation. Equal-origin headline weights are preserved in scores.'))
    lines=['# Actual player review of MLB evidence reliability','',
        'Twenty-five actual cases trace source counts through the conditional prior, transported MLB anchor, skill-specific shrinkage, coherent event probabilities and delivered offense. The source cases were checked before fits; actual cases and origin-selected peers remain in cases.json. Every forecast is next calendar year, not present-day minor-league equivalency, full WAR, control years or trade value. Zero next-year PA means unobserved conditional ability.','',
        'The 145 actual prior inputs are saved for every case. They cover separate-level minor counts/rates, age, exposure context, position, draft evidence and historical rankings. Own MLB performance enters only the explicit count anchor. Counts use three years with 1/.8/.6 recency; minor rates retain fixed 100-opportunity stabilization. MLB history is transported by completed league environments, not park-neutralized. Source/event alignment and 70 saved heads are replayed. Draft school class is unknown in many old source rows: this is a coverage gap, not a false high-school classification. No new college collection, current biography or protected outcome is used.','',
        'Each event blends u=(own count + alpha × prior)/(weighted MLB PA + alpha); eight u values are then normalized. Displayed own influence N/(N+alpha) is before that normalization, not a final causal allocation. Priors are probabilities among future MLB participants, not a validated hypothetical MLB grade for every DSL player.','',
        'Original selection adds each arm’s raw unweighted rate and value extrema. Some raw rate extrema have only one to three PA and cannot be the primary conclusion. A supplemental actual-PA-weighted error contribution check identifies Judge 2023 as both arms’ largest meaningful rate gain and Judge 2016 as their largest harm; both were already selected. Repeated historical development evidence remains qualified.','']
    for c in cases:
        o=c['origin']; key=f"{o['player_id']}|{o['origin_year']}"
        lines += [f"## {o['player_name']} from {o['origin_year']} to {o['target_year']}",'',
            f"Player {o['player_id']}, row {o['row_id']}, fold {o['outer_fold']}, age {o['age']}, stage {o['stage']}. Selection: {', '.join(c['selection'])}.",'',
            '| Source year | Level | PA | HR | K | Unintentional walks |','|---|---|---:|---:|---:|---:|']
        for h in c['source_history']:lines.append(f"| {h['season']} | {h['bucket']} | {h['plate_appearances']} | {h['home_runs']} | {h['strike_outs']} | {h['unintentional_walks']} |")
        lines += ['',f"Weighted transported own MLB PA: {c['weighted_MLB_PA']:.6f}. Actual-fold active profile: {c['active_profile']}. Full actual and scaled prior inputs, old counts/environments, saved fold support and all prior log-odds terms are in cases.json.",'',
            '| Forecast | Batting wins per 600 PA | Expected PA | Batting plus replacement contribution |','|---|---:|---:|---:|']
        for a in ['binary_scout','fixed_reliability','learned_reliability']:
            assert np.isclose(o[a+'_value'],o[a+'_pa']*(o[a+'_rate']/600+o['origin_replacement_rate']))
            lines.append(f"| {a} | {o[a+'_rate']:.6f} | {o[a+'_pa']:.6f} | {o[a+'_value']:.6f} |")
        actual='Unobserved' if not o['next_pa'] else f"{o['next_batting_rate']:.6f}"
        lines += [f"| Actual | {actual} | {o['next_pa']} | {o['next_value']:.6f} |",'',
            f"Unchanged expected PA = participation {o['binary_scout_p']:.8f} × conditional PA {o['binary_scout_conditional_pa']:.6f}. For each arm contribution = expected PA × (batting rate/600 + {o['origin_replacement_rate']:.8f}). These are mechanical comparisons, not an exact joint talent/workload distribution.",'']
        for a in ['fixed_reliability','learned_reliability']:
            h=c['heads'][a]
            lines += [f"### {a} actual probability construction",'',
                '| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |',
                '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
            for z in h['events']:
                alpha=h['alpha_by_event'][z['event']]
                assert np.isclose(z['pre_normalization_blend'],(z['source_pooled_count']+alpha*z['prior'])/(c['weighted_MLB_PA']+alpha))
                lines.append(f"| {z['event']} | {z['source_pooled_count']:.6f} | {z['origin_environment']:.6f} | {z['prior']:.6f} | {alpha:.6f} | {z['own_influence_before_normalization']:.6f} | {z['pre_normalization_blend']:.6f} | {z['predicted']:.6f} | {z['actual_count']} | {z['wins_per600']:.6f} |")
            assert np.isclose(sum(z['wins_per600'] for z in h['events']),o[a+'_rate'])
            lines += ['',f"Largest actual conditional-prior log-odds accounting terms: {h['top_prior_log_odds_terms']}. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.",'']
        lines += [notes[key],'',
            '| Origin selected peer | Age | Prior MLB PA | AAA PA | AA PA | Old rate | Adaptive rate | Expected PA | Actual PA | Actual rate |',
            '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
        for p in c['peers']:
            actual='Unobserved' if not p['next_pa'] else f"{p['next_batting_rate']:.6f}"
            lines.append(f"| {p['player_name'] or p['player_id']} | {p['age']} | {p['pa_0']} | {p['AAA_0_pa']} | {p['AA_0_pa']} | {p['binary_scout_rate']:.6f} | {p['learned_reliability_rate']:.6f} | {p['binary_scout_pa']:.6f} | {p['next_pa']} | {actual} |")
        lines.append('')
    lines += ['## Decision after the actual reviews','',
        'Do not replace the existing batting forecast with either new arm. Learned reliability improves on fixed-100, but rate RMSE 1.85346 is worse than working 1.82465 and contribution RMSE .44351 is worse than .43815 on the same binary workload. Nominal player-clustered intervals favor working. Adaptive alpha never hits declared bounds and all 70 heads converge; these execution passes do not make it a predictive winner.','',
        'Established Judge and Votto demonstrate a useful MLB anchor; Judge’s debut, Winn, Steer and Betts demonstrate missing development/translation. Alonso/Bellinger/Kurtz power and fast entry remain major failures. Volpe improves talent but workload remains low. Forsythe and Nevin show how accurate delivered value can hide opposing errors. Tiny-sample Kratz/Lee/Cozens/Reed rates are not latent-talent conclusions. Only origin 2021 improves versus the working rate; do not generalize that result.','',
        'Retain this implementation and learned differential trust as research, not deployment or proof that all explicit shrinkage fails. Next complete a common-unit public hitting comparison and isolate substantive talent/population gaps under the controlling plan. No frozen forecast change or goal completion.']
    out=e.OUT/'player-walkthrough.md';out.write_text('\n'.join(lines)+'\n',encoding='utf8')
    verification.update(player_walkthrough_status='complete',notes_sha256=sha256_file(notes_path),walkthrough_sha256=sha256_file(out));e.write('verification.json',verification)
    e.write('report.json',dict(player_walkthrough_status='complete',cases=25,saved_heads_replayed=70,adaptive_beats_fixed=True,working_talent_replaced=False,
        predictive_improvement_vs_working=False,whole_model_adopted=False,practical_goal_complete=False,profile_certification=False,
        protected_outcomes_used=False,frozen_forecast_changed=False,notes_sha256=sha256_file(notes_path),walkthrough_sha256=sha256_file(out)))
    pre=read(e.OUT/'preflight.json')
    e.write('preflight-summary.json',dict(full_preflight_sha256=sha256_file(e.OUT/'preflight.json'),
        **{k:v for k,v in pre.items() if k!='cells'},cells=[{k:v for k,v in c.items() if k not in ['training_row_ids','test_row_ids']} for c in pre['cells']]))
    print('25 actual reviews complete. Existing talent retained; no whole-model promotion.',flush=True)


if __name__=='__main__':main()
