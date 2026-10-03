"""Readable stats-to-forecast review with explicit baseball judgments."""
import evaluate_practical_hitter_v30 as r
from universal_baseball.storage import sha256_file

NOTES={
('Spencer Steer',2022):'Strong upper-minor production helps the tree forecasts, but only modestly: the boosted models remain far below the actual regular workload. Ridge is a broken pandemic-lag extrapolation, not a successful prospect forecast. Origin-blind peers Jung/Jones also became regulars, but Stowers had only 33 PA; a blanket debut boost would harm him.',
('Masyn Winn',2023):'498 AAA PA with 18 HR and 83 K survives as useful evidence despite 137 weak MLB PA. Neutralizing minor rates lowers histogram PA about 48; the actual feature mechanism is sensible but magnitude is insufficient. Soderstrom is an important lower-workload counterexample among origin-blind peers.',
('Brent Rooker',2022):'28 HR in 365 AAA PA and prior MLB exposure do not overcome a 36-PA current MLB season in these workload trees. Minor-rate neutralization lowers several forecasts, showing the information is received, not lost in a join. Schrock/White did not become regulars; the model cannot assume every older AAA slugger gets Rooker’s opportunity.',
('Aaron Judge',2016):'19 HR/98 K in 410 AAA PA contrasts with 42 K in 95 MLB PA. Histogram neutralization actually raises PA: his minor-rate vector is not uniformly favorable to this workload fit. Debut strikeouts overpower broader promise. No model anticipates 678 PA; his later breakout is not an input.',
('Aaron Judge',2021):'633 current MLB PA, 39 HR and previous absence yield roughly 480–525 tree PA. The cohort mean is about 524; this is expected opportunity with injury/exit risk, not the healthy ceiling. A 696-PA season is possible but forecasts remain conservative.',
('Gavin Lux',2023):'Zero current MLB PA, but 471 and 381 in preceding seasons. Coarse zero-current profiles are mostly exits, explaining downward regression; actual recovery/role context is absent from this branch. Generic zero-history regressions do not distinguish this returner reliably.',
('Matt McLain',2024):'403 prior MLB PA with 16 HR and 115 K remains in history after a wholly absent year. Trees forecast 168–194 versus 577; minor-rate probes barely move the forecast. This is primarily opportunity/recovery representation, not failure to ingest his AAA hitting.',
('Fernando Tatis Jr.',2022):'Prior 546 MLB PA and 42 HR plus shortened-2020 production remain known. This branch cannot encode a dated temporary suspension/medical return beyond flags; tree PA falls below V24 and actual return. Ridge additionally suffers the fraction_2 extrapolation defect.',
('Wander Franco',2023):'Recent MLB production produces ordinary regular-workload forecasts despite the retained unresolved-availability flag. Point regressions cannot supply a defensible availability probability here. This forecast is not operationally safe without an explicit scenario; eventual zero is not retrospectively made known.',
('Tucupita Marcano',2024):'The documented permanent-status rule sets every arm to zero regardless of fitted raw workload. This is a known eligibility decision, not proof that the talent model learned attrition.',
('Eric Thames',2016):'Three years without domestic production look like disappearance. Actual foreign production is missing; an MLB signing is retained in case context but not included as a predictor. The 551-PA miss is a source/context gap, not a reason to manufacture strong foreign batting rates.',
('Fernando Tatis Jr.',2021):'546 PA/42 HR supports a large ordinary forecast. Actual zero next year is a severe later absence; this result alone does not justify anticipating future events at the cutoff. Ridge zero comes from a malfunctioning linear extrapolation, not foresight.',
('José Miguel Fernández',2022):'Three domestic zero seasons and a 34-year-old profile have approximately one-PA training mean. Ridge 800 is plainly unreasonable and traced to the unsupported season-fraction lag. Trees correctly stay near zero on this domestic-history target; missing foreign activity remains distinct.',
('Thomas Saggese',2024):'A brief MLB debut with substantial AAA exposure gives 168–266 forecasts against 295 actual. This ordinary case shows plausible upper-minor differentiation without promising every debut a full-time role.',
('Juan Soto',2022):'664/654/196 MLB history includes a shortened season. Trees remain around 600–640 against 708. Ridge zero is caused by a thousands-of-PA negative fraction_2 term, overwhelming strong performance: confirmed model-design defect, not baseball regression.',
('Bryan Lavastida',2022):'Very brief current MLB sample and upper-minor history do not guarantee another appearance. Trees stay around 90–122 but actual is zero. Ridge 800 is the same pandemic-feature extrapolation failure; this case rules out celebrating the coincidental Steer improvement.',
('Yuli Gurriel',2017):'A productive current season and age/history create a substantial direct-PA forecast despite a modest V24 forecast. Trees 505–564 align with 573 actual. This is a genuine opportunity-allocation gain within a supported recent-arrival slice, not a general claim about veterans.',
('Adonis García',2016):'Current 547 MLB PA encourages trees to forecast another large workload, but actual is 183. This deterioration is the counterweight to Gurriel: carrying forward a first regular season is reasonable yet uncertain; no model may be selected from gains alone.',
('Dustin Garneau',2017):'126 MLB PA with 36 K and AAA backup exposure gives roughly 49–101 PA versus 3 actual. Histogram lowers the old forecast but still overestimates a marginal role. This is a plausible backup/exit tradeoff, not a source bug.',
('Rhys Hoskins',2022):'672 PA/30 HR supports roughly 524–579 tree PA. Actual next-season zero does not make the pre-origin healthy forecast illogical; public preseason snapshots may know later spring injury. Ridge 800 is additionally distorted by fraction_2.',
('Matt Olson',2017):'24 HR in only 216 MLB PA and 23 HR in 343 AAA PA signal an unusual power breakout. The old approach forecasts 503 PA; shallow workload trees only 312–351 against 660. A major false-low cost of generic direct regression: pooling typical brief roles loses exceptional performance.',
('Adeiny Hechavarría',2016):'Three substantial MLB workloads and weak power produce roughly 427–475 PA against 348. An ordinary moderate overforecast, supported by comparable workloads. It is not necessary that every method beat V24 for this one player.',
('Norichika Aoki',2017):'374 current MLB PA carries forward to about 350–397, but actual domestic MLB PA is zero. Only one training player matches the local age/current-state profile: explicit support limitation and unmodeled foreign/contract context, not certified extrapolation.',
('Lane Adams',2017):'111 current MLB PA with upper-minor exposure forecasts 122–163 versus 29. Modest marginal-player overforecast; compare the entire backup cohort rather than interpreting good minor hitting as a guaranteed job.',
('Livan Soto',2022):'21 BABIP hits in 42 opportunities raises a tiny MLB debut’s apparent contact success. Trees forecast about 247–318 against 12; minor-rate neutralization barely helps, so the uplift is not justified by his AA power. This is a small-sample MLB/contact and opportunity overreaction to address in talent/workload integration.',
('Ryan Mountcastle',2023):'470 current PA after 609/586 and 18 current HR supports about 413–476 versus 507. Ordinary workload uncertainty, not a dramatic feature failure; the baseline is already close.',
('Darick Hall',2023):'18 HR in 334 AAA PA cannot erase weak 56-PA MLB production. Forecasts 65–92 versus zero show limited opportunities for an older marginal power profile. Neutralizing minor rates lowers some forecasts, but a blanket AAA-power boost would worsen this opposite-risk case.'}

def main():
    report=r.read(r.OUT/'report.json');assert report['mechanical_replay_complete']
    cases=r.read(r.OUT/'cases.json');lines=['# V30 workload comparison: player review','',
        'Next-calendar-year MLB PA and batting-plus-replacement value, not full WAR. All 4,396 rows retained. '
        'Fixed cases plus per-arm gains/losses/ordinary/false-high/false-low extremes; peers selected from origin-known age, debut, workload and quality, never future outcomes. '
        'All actual inputs, raw denominators, saved-fit probes and peer identities are in cases.json. Source transaction excerpts are retained diagnostic context, not complete predictors.','',
        '## Aggregate decision','',
        'No direct boosted workload model establishes a meaningful improvement over V24. All-year PA RMSE is 129.29–129.52 versus 128.62; '
        'public-active error is 148.40–149.39 versus 149.12 (Steamer 135.02). Public MAE remains about 116 versus 92.40. '
        'Fixed-yield value gains are small and paired intervals cross zero. Extra Trees worsens overall PA; ridge is invalid as a test of sensible linear regression '
        'because lagged near-constant schedule fractions permit severe unsupported extrapolation. Repair that defect separately; do not refit the original batch.','',
        '## Cases','']
    for t in cases:
        o=t['origin'];key=(o['player_name'],o['origin_year']);assert key in NOTES,key
        lines += [f"### {key[0]}: {key[1]} → {o['target_year']}",'',
            f"Age {o['age']:g}; MLB PA newest to oldest {o['pa_0']}/{o['pa_1']}/{o['pa_2']}. Fold {o['outer_fold']}. "
            f"Selected for: {', '.join(t['selection']['reasons'])}.",'',
            '| Source year/level | PA | HR | K | UBB | BABIP hits/opportunities |','|---|---:|---:|---:|---:|---:|']
        for s in t['raw_level_history']:
            lines.append(f"| {s['season']} {s['level_group']} | {s['plate_appearances']} | {s['home_runs']} | {s['strike_outs']} | {s['unintentional_walks']} | {s['babip_hits']}/{s['babip_opportunities']} |")
        lines+=['','Actual model inputs: each MLB/AAA/AA rate uses (events + 100 × fixed prior)/(opportunities + 100); '
            'levels remain separate. Lower-level stats above are context, not rate predictors in this batch. '
            '2020 MLB opportunity is schedule-normalized; canceled minor samples are flagged, not assigned poor rates. '
            'Age, three years of workload, shrinkage-adjusted observed MLB quality and exposure complete the 104-input vector. '
            f"The unchanged V24 expected yield is {t['fixed_expected_yield600']:.3f} batting-plus-replacement wins per 600 PA.",'',
            '| Forecast | PA | Fixed-yield value | Same-fit minor-rate-neutral raw PA |','|---|---:|---:|---:|',
            f"| V24 | {o['v24_pa']:.1f} | {o['v24_value']:.3f} | — |"]
        for a,v in t['arms'].items():lines.append(f"| {a} | {v['pa']:.1f} | {v['value']:.3f} | {v['fixed_fit_neutral_minor_rate_pa']:.1f} |")
        lines += [f"| Actual | {o['next_pa']} | {o['next_value']:.3f} | — |",'',
            'Neutralization is an artificial, same-fit mechanism probe (minor rates moved to priors, exposures unchanged), not a causal claim or replacement prediction. '
            'Point regressions do not estimate participation probabilities. Permanent-status zeros are applied explicitly.', '',
            NOTES[key],'',f"Local training profile: {t['training_profile']['players']} people / {t['training_profile']['rows']} rows; "
            f"mean PA {t['training_profile']['mean_pa']}; zero fraction {t['training_profile']['zero_fraction']}. This coarse neighborhood is descriptive, not proof of adequate support.",'',
            'Origin-blind comparisons: '+ '; '.join(f"{p['player_name']} (age {p['age']:g}, current PA {p['pa_0']}, V24 {p['v24_pa']:.0f}, histogram {p['hist_gb_pa']:.0f}, actual {p['next_pa']})" for p in t['comparisons'])+'.','']
    lines += ['## Mechanism defect and next work','',
        'In the 2022 ridge fold, fraction_2 has training mean 0.999869 and standard deviation 0.000377. The 2020 value 0.369547 is more than 1,600 standard deviations away. '
        'That feature alone adds 2,190 PA for Steer and subtracts 2,764 for Soto in different held-player fits. Clipping disguises the impossible raw predictions. '
        'Workload is already normalized for season length; remove redundant global fraction/environment regressors for the linear arm under a new repair contract. '
        'Do not conclude a biologically sensible linear baseline failed. Preserve every other arm and original result.', '',
        'Beyond this repair, do not spend another sweep changing gradient libraries. Winn/Steer/Rooker/Olson and their failed peers show that stronger talent/role representation and full-population coverage are more important. '
        'V24 remains the workload reference; no frozen forecast changed.']
    (r.OUT/'player-walkthrough.md').write_text('\n'.join(lines),encoding='utf8')
    report.update(player_walkthrough_status='complete',player_walkthrough_path=str(r.OUT/'player-walkthrough.md'),
        disposition='Retain V24 workload reference; direct trees inconclusive/no meaningful gain; ridge requires schedule-extrapolation repair, not family rejection.')
    report['output_hashes'][str(r.OUT/'player-walkthrough.md')]=sha256_file(r.OUT/'player-walkthrough.md')
    r.write('report.json',report)
    print('Completed all 27 selected player reviews; ridge design defect identified; no promotion.')

if __name__=='__main__':main()
