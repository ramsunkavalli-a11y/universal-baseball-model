"""Close the eight reviewed source cases without claiming a forecasting gain."""
from pathlib import Path
import json
from universal_baseball.storage import sha256_file
import prepare_hitter_observed_return_v60 as e

NOTES={
('Yordan Alvarez',2022): 'The July 21 reserve-list activation closes the July 10 roster-absence observation. The two-year possible-absence upper bound is 23 regular-season calendar days, not 23 measured missed games. Earlier paternity activation does not erase an unrelated medical spell. His 100 late PA also independently contradict continued absence. PA was already closer under V59 but offense worse: this correct source cannot be judged by a lucky aggregate error.',
('Nick Castellanos',2016): 'There is no recognized activation record. The 15 PA window begins after his August 7 entry and proves observed return by October 2. Return may have been much earlier; 57 possible days is an upper bound, not a filled exact duration. The preceding 10 PA window overlaps the entry and is insufficient by itself. Comparison players include subsequent successes and less successful returns.',
('Maikel Franco',2016): 'The 2015 wrist entry is bounded by actual late-2015 MLB use, not carried through 2016 and later seasons. The 2016 630 PA/25 HR and late 101 PA are incompatible with years of uninterrupted IL absence. It remains a recorded prior injury; neither zero injury history nor perfect health is inferred.',
('Jarrett Parker',2016): 'October 12 placement is after the October 2 window end. The earlier 13 PA cannot clear it. Recorded unresolved stays one while possible regular-season absence days is zero: an offseason injury and missed regular-season opportunities are different facts. Future 177 PA is displayed, not used to clear the origin state.',
('Kyle Garlick',2022): 'May and June plain MLB activations end their own reported spells. The September 16 entry and October 3 transfer are later than the late-window start, so 29 window PA cannot clear that final spell. Recorded unresolved stays one. This preserves repeated injury history and later-entry risk instead of applying a blanket active-player rule.',
('Mark Canha',2016): 'May placement and June transfer have no positive later MLB window. Recorded unresolved stays one; 143 days is only possible absence. No late PA cannot distinguish continuing injury from role/source uncertainty. His subsequent 187 PA and Spangenberg comparison returning for 486 do not justify backdating recovery.',
('Gavin Lux',2023): 'Known knee surgery and November 6 named IL activation are retained. There are no 2023 MLB windows for this player; unavailable rows are not a fabricated positive return. His prior 471 MLB PA still matter. Recorded roster closure is not full medical recovery or a newly learned 487-PA forecast; generic inactive peers are not surgical-comeback support.',
('Matt McLain',2024): 'Shoulder placement/transfer and October 28 plain MLB activation are preserved. The full missed MLB season remains evidence, not retirement or permanent incapacity. The two-year 218-day possible upper bound includes prior oblique and current shoulder intervals; it is not a measured duration. The 174/176-PA forecasts remain underestimates versus 577; Endy Rodriguez returning for 57 shows why not every surgery return can simply be assigned a regular workload.'
}


def main():
    report=e.read(e.OUT/'report.json');cases=e.read(e.OUT/'cases.json')
    assert report['player_walkthrough_status']=='pending'
    for p,h in report['input_hashes'].items():assert sha256_file(Path(p))==h,p
    assert len(cases)==len(NOTES)==8
    lines=['# Observed roster return is not medical recovery','',
        'Source-only repair, no predictive fits or changed forecasts. Counts and timing precede future-outcome inspection.',
        '48 of 81 old-open source rows (41 people), and 45 of 72 evaluation rows, are observed closed.',
        '47 source rows have strictly later MLB windows; the additional closure is Riley Greene\'s reported offseason roster activation.',
        'Duration is a conservative possible-absence bound, not measured injury days. Missing medical scope remains unknown.',
        'Gain/harm forecast selection is inapplicable: no new forecasts were fitted. Prior source-qualified forecasts stay shown.',
        'Comparison players are chosen from origin-known medical scope/open state, age and MLB PA, never future success.','']
    lean=[]
    for c in cases:
        r=c['origin'];key=r['player_name'],r['origin_year'];assert key in NOTES
        assert not r['clinical_recovery_certified'] and not r['exact_first_return_date_known']
        columns=['row_id','player_id','player_name','origin_year','age','stage','pa_0','pa_1','pa_2',
                 'medical_scope','original_recorded_open','recorded_unresolved',
                 'possible_absence_days730_upper','absence_days730_lower',
                 'observed_return_intervals730','reported_roster_returns730',
                 'repaired_p','repaired_conditional_pa','repaired_pa','repaired_rate','repaired_value',
                 'status_p','status_conditional_pa','status_pa','status_rate','status_value',
                 'next_pa','next_value','clinical_recovery_certified','exact_first_return_date_known']
        lean.append({**c,'origin':{n:r[n]for n in columns},'review_note':NOTES[key]})
        lines += [f"## {r['player_name']} at December {r['origin_year']}",'',
            f"Age {r['age']}; current/prior MLB PA {r['pa_0']}/{r['pa_1']}/{r['pa_2']}.",
            f"Old open input {r['original_recorded_open']:.0f}; repaired unresolved observation {r['recorded_unresolved']:.0f}.",
            f"Possible two-year absence interval: {r['absence_days730_lower']}–{r['possible_absence_days730_upper']} regular-season calendar days. Exact return and clinical recovery remain unknown.",
            f"Preserved V53: p {r['repaired_p']:.3f} × conditional {r['repaired_conditional_pa']:.2f} = {r['repaired_pa']:.2f} expected PA.",
            f"Preserved V59: p {r['status_p']:.3f} × conditional {r['status_conditional_pa']:.2f} = {r['status_pa']:.2f} PA; actual {r['next_pa']}.",
            f"Unchanged hitting estimate {r['repaired_rate']:.3f} per 600 PA; batting plus replacement {r['repaired_value']:.3f}/{r['status_value']:.3f}, actual {r['next_value']:.3f}.",
            '',NOTES[key],'','Actual source counts:']
        for h in c['source_history']:
            lines.append(f"- {h['season']} {h['bucket']}: {h['plate_appearances']} PA, {h['home_runs']} HR, {h['strike_outs']} K.")
        lines+=['','Observed windows:']
        for w in c['windows']:
            lines.append(f"- {w['label']}: {w['start']}–{w['end']}, {w['pa']} PA.")
        if not c['windows']:lines.append('- No current-year observed MLB window row; no positive return inferred.')
        lines+=['','Source-to-state intervals:']
        for s in c['spells']:
            lines.append(f"- Entry {s['start']}, latest placement/transfer {s['latest_entry']}; upper end {s['end_upper']}; closure {s['closure_kind']}; open observation {s['open_observation']}; transaction IDs {s['transaction_ids']}.")
        lines+=['','Eligible medical/return records:']
        for t in c['records']:
            if t.get('il_kind') or t['kind']in ['mlb_return','mlb_activation']:
                lines.append(f"- Known {t['available_date']}, occurred {t['event_date']}: {t['description']}")
        lines+=['','Origin-known comparisons:']
        for p in c['peers']:
            lines.append(f"- {p['player_name']}: age {p['age']}, {p['pa_0']} origin MLB PA; original open {p['original_recorded_open']}, repaired unresolved {p['recorded_unresolved']}, possible days {p['possible_absence_days730_upper']}; preserved expected {p['repaired_pa']:.1f} PA versus {p['next_pa']} actual.")
        lines.append('')
    lines+=['## Disposition','',
        'Retain this adapter as a corrected observation-state source, not a validated health model or forecast upgrade.',
        'Old fits are unchanged; the next workload contrast must audit actual role/return support and use bound/missingness semantics.',
        'Do not substitute possible-duration upper bounds for measured days or assign every returning prospect a starting job.',
        'The older V59 medical coefficients and negative result remain source-qualified.']
    (e.OUT/'player-walkthrough.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    e.write('reviewed-cases.json',lean)
    report.update(player_walkthrough_status='complete',
        source_disposition='retain observation-state repair; predictive use not yet tested',
        forecast_disposition='preserve corrected V53; no upgrade from source-only repair',
        player_walkthrough_path=str(e.OUT/'player-walkthrough.md'))
    report['output_hashes'].update({str(e.OUT/n):sha256_file(e.OUT/n)for n in
                                 ['player-walkthrough.md','reviewed-cases.json']})
    e.write('report.json',report)
    archive=e.ROOT/'reports/model-evidence/hitter-observed-return-v60'
    archive.mkdir(parents=True,exist_ok=True)
    for n in ['report.json','source-contract.json','player-walkthrough.md','reviewed-cases.json']:
        (archive/n).write_bytes((e.OUT/n).read_bytes())
    print('Eight actual source reviews complete. No forecast changed.',flush=True)


if __name__=='__main__':
    main()
