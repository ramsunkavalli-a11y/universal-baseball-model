"""Explain a source defect; no replacement medical state or forecast is fitted."""
from datetime import date
from pathlib import Path
import json
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball import availability_context_v29b as a
from universal_baseball.histogram_prediction_trace import trace
from universal_baseball.storage import sha256_file
from evaluate_hitter_readiness_v49 import logit_trace
import evaluate_hitter_opportunity_status_v59 as e

FIXED=[(670541,2022),(592206,2016),(596748,2016),(519390,2016),(607680,2022),(592192,2016)]
NOTES={
    ('Yordan Alvarez',2022):'July 10 hand placement remains open after a July 21 reserve-list activation. The September 6 to October 5 window has 100 PA, proving a subsequent observed MLB return within that window. This does not prove complete health or an exact return date. An uninterrupted July-to-December IL spell is contradicted. The candidate open flag costs about twenty conditional PA, yet the resulting PA estimate is closer to actual; do not infer source correctness from that lucky result.',
    ('Nick Castellanos',2016):'An August 7 entry stays open despite 15 PA during the later September window. His captured open spell also persists into later source years. Lack of a named IL activation cannot outweigh actual MLB use as evidence against uninterrupted roster absence; it still does not certify the arm fully healed.',
    ('Maikel Franco',2016):'The reconstructed open entry starts August 12, 2015, yet 2016 late MLB usage is 101 PA. It also persists into 2017 and 2018 despite subsequent MLB appearances. This is a stale observation-state defect, not evidence of years of continuing roster absence. Do not train a medical penalty on it as current injury status.',
    ('Jarrett Parker',2016):'October 12 entry occurs AFTER the September late-window start and after that window ends. Thirteen late PA cannot disprove this later injury. This control prevents a blanket rule that every player with any late PA is healthy or returned after a particular spell.',
    ('Kyle Garlick',2022):'September 16 entry falls INSIDE the September 6 to October 5 window. Its 29 PA may all precede the injury; aggregate window PA alone cannot locate the return. Keep timing unresolved rather than automatically clearing the flag.',
    ('Mark Canha',2016):'May 9 entry has zero PA in the late window. This check finds no contradiction, but no PA is not proof an injury remained open: demotion, role, rehabilitation and source gaps can also prevent MLB use. The unchanged forecast and real future workload are shown, not used to establish the flag.'
}


def main():
    pre=e.read(e.OUT/'preflight.json')
    q=pl.read_parquet(e.OUT/'predictions.parquet')
    source=pl.read_parquet(e.OUT/'features.parquet')
    context=pl.read_parquet(e.OUT/'context.parquet').filter(pl.col('il_open')>0)
    window_root=e.ROOT/'reports/generated/practical-hitter-late-role-v46'
    manifest=e.read(window_root/'source-manifest.json')
    windows=pl.read_parquet(window_root/'windows.parquet')
    starts={r['season']:date.fromisoformat(r['start'])for r in manifest['sources']if r['window']=='late'}
    ends={r['season']:date.fromisoformat(r['end'])for r in manifest['sources']if r['window']=='late'}
    records=e.read(e.OUT/'records.json');rows=[];record_lookup={}
    for row in context.join(windows.rename({'season':'origin_year'}),on=['player_id','origin_year'],how='left',validate='1:1').iter_rows(named=True):
        rs=[{**r,'available_date':date.fromisoformat(r['available_date']),
            'event_date':date.fromisoformat(r['event_date'])}for r in records.get(str(row['player_id']),[])]
        cutoff=date(row['origin_year'],12,31)
        spells=a.il_episodes(rs,cutoff)[0];opened=[s for s in spells if s['open']]
        assert len(opened)==1
        spell=opened[0];start=starts[row['origin_year']]
        contradiction=bool(row['late_pa'] is not None and row['late_pa']>0 and start>spell['start'])
        rows.append(dict(row_id=row['row_id'],player_id=row['player_id'],origin_year=row['origin_year'],
            captured_open_start=spell['start'],late_start=start,late_end=ends[row['origin_year']],
            late_pa=row['late_pa'],continuous_absence_contradicted=contradiction,
            no_medical_recovery_inference=True,exact_return_date_known=False))
        record_lookup[row['row_id']]=a.as_of(rs,cutoff)
    audit=pl.DataFrame(rows)
    assert len(audit)==81
    joined=audit.join(q,on=['row_id','player_id','origin_year'],validate='1:1')
    assert len(joined)==72
    selected=[]
    # Names are resolved from fixed cohort information, not selected by future success.
    for key in NOTES:
        g=joined.filter((pl.col('player_name')==key[0])&(pl.col('origin_year')==key[1]))
        assert len(g)==1,key
        selected.append(g.row(0,named=True))
    cases=[];history=pl.read_parquet(e.ROOT/'reports/generated/practical-hitter-v31/counts.parquet')
    with threadpool_limits(limits=2):
        for row in selected:
            te=source.filter(pl.col('row_id')==row['row_id']);heads={}
            for head in e.read(e.OUT/f"fit-{row['origin_year']}-{row['outer_fold']}.json")['heads']:
                m=joblib.load(head['path']);names=head['features'];x=te.select(names).to_numpy()[0]
                heads[head['head']]=logit_trace(m,x,names)if head['head']=='participation'else trace(m,x,names)
            peers=joined.filter((pl.col('origin_year')==row['origin_year'])&
                (pl.col('player_id')!=row['player_id'])).with_columns(
                    (((pl.col('age')-row['age'])/3)**2+
                    ((pl.col('pa_0')-row['pa_0'])/300)**2).alias('distance')).sort('distance','player_id').head(3)
            cases.append(dict(origin=row,source_history=history.filter((pl.col('player_id')==row['player_id'])&
                pl.col('season').is_between(row['origin_year']-2,row['origin_year'])).sort('season','bucket').to_dicts(),
                eligible_records=record_lookup[row['row_id']],heads=heads,
                actual_status_input=float(te['status_open_medical'][0]),
                note=NOTES[row['player_name'],row['origin_year']],
                peers=peers.select('player_name','age','pa_0','captured_open_start','late_start','late_pa',
                    'continuous_absence_contradicted','status_pa','next_pa').to_dicts()))
    audit.write_parquet(e.OUT/'open-spell-audit.parquet')
    e.write('open-spell-cases.json',cases)
    lines=['# Recorded open injury spells contradicted by later MLB use','',
        'This explains a defect in the completed status experiment. No new model is fitted and no forecast is replaced.',
        'Compare only origin-known captured medical records and certified historical MLB windows, before reading future outcomes.',
        'A positive PA window entirely after a spell begins disproves uninterrupted IL roster absence. It does not prove complete recovery.',
        'An injury beginning during or after the window is not cleared from aggregate PA.',
        '47 of 81 source open-spell rows and 44 of 72 evaluation open-spell rows meet the strict contradiction rule.',
        'These are repeated player-origins, not independent people. Other rows are unresolved, not certified valid.',
        'The rare-signal training counts and learned medical coefficients are therefore not clean evidence about actual current injury.',
        '', '## Six actual source and forecast checks','']
    for c in cases:
        row=c['origin']
        lines += [f"### {row['player_name']} at the {row['origin_year']} cutoff",'',
            f"Captured entry {row['captured_open_start']}; late window {row['late_start']} to {row['late_end']}: {row['late_pa']} PA.",
            f"Model open input {c['actual_status_input']:.0f}; strict contradiction {row['continuous_absence_contradicted']}.",
            f"Preserved expected PA {row['repaired_pa']:.2f}; status forecast {row['status_pa']:.2f}; next-year actual {row['next_pa']}.",
            f"Appearance {row['status_p']:.2%}, conditional PA {row['status_conditional_pa']:.2f}, unchanged hitting rate {row['status_rate']:.3f} per 600 PA.",
            '',c['note'],'','Actual source counts:']
        for h in c['source_history']:
            lines.append(f"- {h['season']} {h['bucket']}: {h['plate_appearances']} PA, {h['home_runs']} HR, {h['strike_outs']} K.")
        lines += ['','Eligible captured records relevant to placement or return:']
        for r in c['eligible_records']:
            if r['event_date']>=row['captured_open_start'] and (r['il_kind']or r['kind']in ['mlb_return','mlb_activation','scope_exit']):
                lines.append(f"- Known {r['available_date']}, occurred {r['event_date']}: {r['description']}.")
        for head,detail in c['heads'].items():
            terms=[t for t in detail['feature_effects']if t['feature'].startswith('status_')]
            lines += ['',f"Actual saved {head} output {detail['raw_prediction']:.6f}; status terms: "+
                ('; '.join(f"{t['feature']} {t['path_effect']:+.4f}"for t in terms)or'none')+'.']
        lines += ['','Origin-known open-spell comparisons, including unresolved cases:']
        for r in c['peers']:
            lines.append(f"- {r['player_name']}: entry {r['captured_open_start']}, {r['late_pa']} late PA, contradiction {r['continuous_absence_contradicted']}; projected {r['status_pa']:.1f} PA versus {r['next_pa']} actual.")
        lines.append('')
    lines += ['## Repair requirement','',
        'Separate observed roster return from medical recovery. Reconstruct spells using dated actual MLB appearances,',
        'or use bounded interval evidence when exact return dates are unavailable. Keep late-injury counterexamples and unknowns.',
        'Do not merely flip the open flag or zero all past absence days; duration, recurrence and roster state must stay distinct.',
        'The existing V59 predictive result is source-qualified and not a rejection of health information.',
        'Do not refit this same ten-feature sweep until a corrected source-to-workload design is explicitly contracted.']
    (e.OUT/'open-spell-walkthrough.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    note=dict(source_rows=81,source_contradictions=int(audit['continuous_absence_contradicted'].sum()),
        evaluation_rows=72,evaluation_contradictions=int(joined['continuous_absence_contradicted'].sum()),
        reviewed_cases=6,player_walkthrough_status='complete',new_models_fitted=False,forecasts_changed=False,
        protected_outcomes_used=False,clinical_recovery_inferred=False,
        source_hashes={str(p):sha256_file(p)for p in [e.OUT/'records.json',e.OUT/'context.parquet',
            window_root/'windows.parquet',window_root/'source-manifest.json',Path(__file__)]})
    e.write('open-spell-report.json',note)
    archive=e.ROOT/'reports/model-evidence/practical-hitter-opportunity-status-v59'
    for name in ['open-spell-report.json','open-spell-cases.json','open-spell-walkthrough.md']:
        (archive/name).write_bytes((e.OUT/name).read_bytes())
    report=e.read(e.OUT/'report.json')
    report.update(source_integrity='cutoff execution passes; open-spell source is contradicted in 44 evaluation rows; no clean current-injury contrast',
        source_defect=note,rejection_of_health_information=False)
    report['output_hashes'].update({str(e.OUT/name):sha256_file(e.OUT/name)for name in ['open-spell-report.json','open-spell-cases.json','open-spell-walkthrough.md']})
    e.write('report.json',report)
    print(json.dumps(note,default=str,indent=2),flush=True)


if __name__=='__main__':
    main()
