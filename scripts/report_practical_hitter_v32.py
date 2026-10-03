"""Complete the unfitted assembly review with persisted baseball judgments."""
import json
import numpy as np
import polars as pl
import evaluate_practical_hitter_v32 as e
from universal_baseball.storage import sha256_file

def fmt(v):return 'missing' if v is None else f'{v:.3f}'

def main():
    cases=e.r.read(e.OUT/'cases.json');notes=e.r.read(e.r.ROOT/'config/practical_hitter_v32_case_notes.json')
    f=pl.read_parquet(e.OUT/'predictions.parquet');source=pl.read_parquet(e.r.OUT/'scored-predictions.parquet')
    rebuilt,flags=e.assemble(source)
    assert f.equals(rebuilt) and len(f)==30506
    assert f.select('row_id','next_pa','next_value').equals(source.select('row_id','next_pa','next_value'))
    report=e.r.read(e.OUT/'report.json')
    lines=['# V32 opportunity/value reconnection: review and disposition','',
        'The reconnection removes most of V31’s lost batting-value accuracy on the V24 slice, but its small gain is uncertain and it still loses to the stronger older N approach. Retain as a development assembly, not a finished broad hitter model.',
        '', 'No refits, row changes, new rate clipping or held-out-total rescaling. Targets are next-year MLB PA and batting-plus-replacement wins, not full WAR or current prospect talent. Public forecasts retain snapshot/environment differences.','',
        '## Fixed comparisons','', '| Scope / arm | PA RMSE | Contribution RMSE | Contribution MAE |','|---|---:|---:|---:|']
    for s in e.r.read(e.OUT/'scores.json')[:5]:
        for a,v in s['scores'].items():lines.append(f"| {s['scope']} / {a} | {v['pa_rmse']:.2f} | {v['value_rmse']:.5f} | {v['value_mae']:.5f} |")
    lines.extend(['','The V24 reconnections lower value RMSE 0.91725 to 0.91401/base or 0.91411/detail. Their nominal paired MSE intervals include zero. Against N, base/detail reconnections worsen 0.44582 to 0.44792/0.44853; detail also harms the matched public N scope. No universal advantage is established.',
        '', '2021’s PA shortfall is unchanged by rate reconnection. The detailed N assembly still underprojects upper-minor contribution and overprojects lower-minor PA. Better public batting-value error than converted Steamer is not a pure hitting-talent superiority claim: conversion has a substantial mean offset and forecast snapshots are not identical.',
        '', '## Case selection and evidence','',
        'Eleven fixed diagnostics plus each assembly’s largest gain/harm, false high/low and ordinary partial-workload case, de-duplicated to twenty cases. Peers use same origin, source stage and debut status and distances in origin age, elapsed years, MLB/AAA/AA/minor PA and observed quality; no future outcome in selection. Full vectors, source counts, conditional support and inherited V31 saved-fit probes are in cases.json. The new step is exactly auditable arithmetic, not a newly learned adjustment.',''])
    assert len(cases)==20
    for c in cases:
        o=c['origin'];key=f"{o['player_name']}|{o['origin_year']}";assert key in notes
        lines.extend([f"### {o['player_name']} — cutoff {o['origin_year']}, target {o['target_year']}",'',
            'Selection: '+ '; '.join(c['selection'])+'.','',
            f"Known inputs: age {o['age']:g}; elapsed since debut {o['elapsed']}; captured listing {o['on_40man']} (not certified rights); MLB PA last three years {o['pa_0']}/{o['pa_1']}/{o['pa_2']}; current shrunk MLB quality {o['quality_0']:.3f}. Base/detail expected PA {o['base_hurdle_pa']:.2f}/{o['detail_hurdle_pa']:.2f}.",'',
            '| Season | League bucket | PA | HR | K | Unintentional BB |','|---|---|---:|---:|---:|---:|'])
        for s in c['raw_level_history']:lines.append(f"| {s['season']} | {s['bucket']} | {s['plate_appearances']} | {s['home_runs']} | {s['strike_outs']} | {s['unintentional_walks']} |")
        lines.extend(['','| Anchor | Old PA | Old value | Yield per PA | Base-PA value | Detail-PA value |','|---|---:|---:|---:|---:|---:|'])
        for a in e.ANCHORS:
            lines.append('| '+a+' | '+' | '.join(fmt(o[k]) for k in [a+'_pa',a+'_value',a+'_yield','base_'+a+'_value','detail_'+a+'_value'])+' |')
            if o[a+'_pa'] is not None:
                for stem,new in [('base','base_hurdle'),('detail','detail_hurdle')]:assert np.isclose(o[stem+'_'+a+'_value'],o[new+'_pa']*o[a+'_yield'])
        lines.extend(['',f"Weighted-rate calculation: {o['detail_hurdle_pa']:.6f} PA × ({o['rate_hist_pa_rate']:.6f}/600 + {o['origin_replacement_rate']:.8f}) = {o['detail_weighted_rate_value']:.6f}. This rate weights future opportunities and is not a current talent grade for never-arrivals.",'',
            f"Actual: {o['next_pa']} MLB PA and {o['next_value']:.6f} batting-plus-replacement wins.",'',notes[key],'',
            'Origin-selected peers: '+ '; '.join(f"{p['player_name']} ({p['pa_0']} current MLB PA; actual next {p['next_pa']} PA / {p['next_value']:.2f} value)" for p in c['comparisons'])+'.','',
            'Actual conditional-head profile support: '+ '; '.join(f"{s['head']}={s['conditional_profile_players']} distinct people" for s in c['conditional_support'])+'.',''])
    lines.extend(['## Decision and next step','',
        'Keep the improved broad-workload/source framework and preserved stronger batting anchors. Do not replace N with either reconnection or the broad weighted-rate product. No deployment or goal-completion claim.',
        '', 'The next structural test should reuse existing cutoff-known pedigree, exposure-pooled batting evidence with safe regularization geometry, and distinguish temporary absence/finite suspension from ordinary attrition. Do not repeat an algorithm tournament or tune manual boosts to these names. Existing evidence has not made the 2021 and rare-entry gaps disappear.'])
    path=e.OUT/'player-walkthrough.md';path.write_text('\n'.join(lines)+'\n',encoding='utf8')
    report.update(player_walkthrough_status='complete',player_walkthrough_artifact=str(path),player_walkthrough_sha256=sha256_file(path),
        arithmetic_replay='all rows exactly reproduced',targets_and_membership_unchanged=True,
        disposition='Retain matched V24 assembly as development only; withhold broad replacement: uncertain small gain and no advantage over older N.',
        case_notes_sha256=sha256_file(e.r.ROOT/'config/practical_hitter_v32_case_notes.json'))
    e.write('report.json',report);print(json.dumps(report,indent=2))

if __name__=='__main__':main()
