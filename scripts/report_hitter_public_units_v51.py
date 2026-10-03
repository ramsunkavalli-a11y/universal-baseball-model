"""Complete raw-event benchmark accounting and its actual player review."""
import numpy as np
import polars as pl
from universal_baseball.practical_hitter_v30 import score
from universal_baseball.storage import sha256_file
import audit_hitter_public_units_v51 as e


def main():
    read=e.previous.prior.old.r.read;audit=read(e.OUT/'audit.json');cases=read(e.OUT/'cases.json')
    path=e.ROOT/'config/practical_hitter_public_units_v51_case_notes.json';notes=read(path)
    assert len(cases)==11 and set(notes)=={f"{c['origin']['player_id']}|{c['origin']['origin_year']}" for c in cases}
    assert all(sha256_file(e.Path(p))==h for p,h in audit['input_hashes'].items())
    scores=read(e.OUT/'scores.json')
    for s in scores:
        for metric in s['rates'].values():metric['unit']='fixed-event batting wins per 600 PA centered on the shared origin-season MLB environment'
    e.write('scores.json',scores)
    f=pl.read_parquet(e.OUT/'predictions.parquet');g=f.filter((pl.col('pa_0')>0)&pl.col('steamer_index').is_not_null()&pl.col('zips_index').is_not_null())
    workload=[]
    for label,q in [('all_current_common',g),('legacy_common',g.filter(pl.col('v24_pa').is_not_null())),
        ('public_one_PA_diagnostic',g.filter(pl.col('steamer_pa')<=1.001)),('public_more_PA_diagnostic',g.filter(pl.col('steamer_pa')>1.001))]:
        workload.append(dict(scope=label,rows=len(q),actual_pa=float(q['next_pa'].sum()),zero_actual_pa=int((q['next_pa']==0).sum()),
            scores={a:{k:v for k,v in score(q,a).items() if k.startswith('pa_')} for a in ['working','binary','steamer']}))
    e.write('workload-information-diagnostic.json',dict(groups=workload,
        interpretation='Archive one-PA grouping is a post-score diagnostic, not origin UBM eligibility or a replacement headline. Exact public dates are unknown; information advantage is a hypothesis, not proven for every one-PA row.',
        no_new_fits=True,evaluation_rows_dropped=False))
    lines=['# Hitting comparisons using the same event units','',
        'Eleven actual source-to-forecast reviews complete. Fixed index weights use total PA, not official wOBA or park-neutral true talent. Predictions are unchanged; actual and forecast comparisons now share one unit. No future environment is inserted into a forecast. All original public results remain preserved.','',
        'Raw actual index = weighted mature MLB event counts/actual PA. UBM implied index = origin index + relative forecast/UNIT, where UNIT=600/(10×1.193). Public index = the same fixed-weight numerator/projected total PA. Common readable rate = UNIT×(index-origin index); all systems subtract the same origin. Contribution uses origin replacement. This is a same-unit event diagnostic, not full WAR or trade/control value.','',
        'The larger public sample contains 2,627 current-MLB forecasts, 2,088 with actual MLB PA; 1,789 legacy matches are retained exactly. Common membership still excludes missing public forecasts and non-current players, so it does not certify all prospects. A zero actual index stored on inactive rows is never scored as an observed talent value.','',
        'Peer selection uses origin year, age, elapsed and workload, without future results. It does not establish equal power/park/health profiles. Public source dates remain unknown. The one-PA availability grouping below is a diagnostic only: no row is removed from the primary population and no model uses future/public labels as an input.','']
    for c in cases:
        o=c['origin'];key=f"{o['player_id']}|{o['origin_year']}"
        lines += [f"## {o['player_name']} from {o['origin_year']} to {o['target_year']}",'',
            f"Player {o['player_id']}, row {o['row_id']}, fold {o['outer_fold']}; age {o['age']}, elapsed {o['elapsed']}. Selection: {', '.join(c['selection'])}.",'',
            '| Source year | Level | PA | HR | K | UBB |','|---|---|---:|---:|---:|---:|']
        for h in c['source_history']:lines.append(f"| {h['season']} | {h['bucket']} | {h['plate_appearances']} | {h['home_runs']} | {h['strike_outs']} | {h['unintentional_walks']} |")
        lines += ['',f"Origin league index {o['origin_index']:.9f}; realized target index {o['target_index']:.9f}. Only the origin enters forecast conversion. Old actual centered rate {o['old_actual_rate']:.6f}; common-origin actual rate {'unobserved' if not o['next_pa'] else format(o['next_batting_rate'],'.6f')}.",'',
            '| Forecast | Event index | Origin centered wins per 600 | PA | Contribution |','|---|---:|---:|---:|---:|']
        for a in e.ARMS:
            assert np.isclose((o[a+'_index']-o['origin_index'])*e.UNIT,o[a+'_rate'])
            pa='Conditional exposure only' if a=='zips' else f"{o[a+'_pa']:.6f}"
            value='Not a workload forecast' if a=='zips' else f"{o[a+'_value']:.6f}"
            lines.append(f"| {a} | {o[a+'_index']:.9f} | {o[a+'_rate']:.6f} | {pa} | {value} |")
        lines += [f"| Actual | {'Unobserved' if not o['next_pa'] else format(o['actual_index'],'.9f')} | {'Unobserved' if not o['next_pa'] else format(o['next_batting_rate'],'.6f')} | {o['next_pa']} | {o['next_value']:.6f} |",'',
            '| Public system | Projected PA | 1B | 2B | 3B | HR | BB | IBB | HBP | Weighted numerator |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
        for a in ['steamer','zips']:
            r=c['public_counts'][a];assert np.isclose(r['numerator']/r['PA'],o[a+'_index'])
            lines.append('| '+a+' | '+' | '.join(f"{r[k]:.6f}" for k in ['PA','1B','2B','3B','HR','BB','IBB','HBP','numerator'])+' |')
        lines += ['',f"UBM implied index = {o['origin_index']:.9f} + {o['binary_rate']:.6f}/{e.UNIT:.9f} = {o['binary_index']:.9f}. Actual event numerator/counts and source environments remain in cases.json. Contribution = expected PA × (rate/600 + {o['origin_replacement_rate']:.9f}). Prior model fitting/support remains governed by the reviewed V34/V49 artifacts; this no-fit audit does not certify them anew.",'',notes[key],'',
            '| Origin selected peer | UBM rate | Steamer rate | Actual rate | Actual PA |','|---|---:|---:|---:|---:|']
        for p in c['peers']:
            actual='Unobserved' if not p['next_pa'] else f"{p['next_batting_rate']:.6f}"
            lines.append(f"| {p['player_name']} | {p['binary_rate']:.6f} | {p['steamer_rate']:.6f} | {actual} | {p['next_pa']} |")
        lines.append('')
    lines += ['## Decision after review','',
        'The existing UBM hitting estimate is plausibly competitive on this fixed-event metric, not certified superior. Broader conditional rate RMSE is 1.74524 versus Steamer 1.77459 and ZiPS 1.75336; legacy-only 1.76092 versus 1.78377 and 1.75262. Target 2023 loses to both public systems. Timing, selection, parks, fixed weights and repeated development exposure prevent a blanket superiority claim.','',
        'Playing time remains the clearer issue: broader binary PA RMSE 138.28 versus Steamer 135.38; MAE 106.79 versus 92.08. Public one-PA rows explain a substantial part of the MAE gap (52.58 versus 11.12 within that group), but excluding them would change the question. On the remaining diagnostic group MAE is 115.50 versus 106.23. Potentially different availability information is concrete, not proof that UBM already solves it.','',
        'Retain existing talent plus qualified binary readiness as the coherent development candidate. Do not replace talent with V50. Prospect fast entry, elite-power compression, availability and translated/contextual talent remain visible gaps. Finish a concise practical candidate handoff and benchmark dashboard; do not launch another undirected algorithm tournament. No frozen forecast change or protected outcomes.']
    out=e.OUT/'player-walkthrough.md';out.write_text('\n'.join(lines)+'\n',encoding='utf8')
    audit.update(player_walkthrough_status='complete',notes_sha256=sha256_file(path),walkthrough_sha256=sha256_file(out));e.write('audit.json',audit)
    e.write('report.json',dict(player_walkthrough_status='complete',cases=11,common_units_verified=True,existing_talent_retained=True,
        working_or_frozen_forecast_changed=False,practical_goal_complete=False,public_timing_certified=False,whole_population_certified=False,
        no_model_fits=True,protected_outcomes_used=False))
    print('11 actual raw-event reviews complete; public workload information diagnostic retained without changing membership.',flush=True)


if __name__=='__main__':main()
