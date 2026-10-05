"""Publish bounded reviewed evidence without changing original experiment output."""
from check_hitter_direct_events import OUT,OLD,ROOT,read,save,verify
from universal_baseball.storage import sha256_file

JUDGMENT={
    (650402,2017):'Torres: strongest deterioration. Translated/persisted power is low and direct conversion omits age/scouting development; negative rate worsens the actual productive debut. Origin peers are mixed.',
    (641470,2018):'Collins: ordinary direct batting estimate fits the poor observed rate, but expected PA remains low. High source strikeouts reach the probability profile; tiny rookie exposure does not dominate.',
    (702616,2023):'Holliday: lower direct rate improves the largest error but still does not predict the collapse. Young elite origin peers include successful arrivals and a non-arrival; support is sparse.',
    (670541,2018):'Yordan: tiny DSL influence is resolved, but transferred power and hit/walk probabilities are too modest. Direct rate is negative against an exceptional productive debut; PA remains badly low.',
    (624413,2018):'Alonso: positive direct HR value is offset by a much larger negative singles term. The resulting negative rate worsens a strong AA/AAA power prospect; actual 53-HR breakout is not required to be forecast exactly.',
    (680757,2021):'Kwan: low contact risk is represented but still above observed K; negative power value dominates positive singles. Actual contact/BB production and playing time remain underpredicted.',
    (701762,2024):'Kurtz: HR and walks now have their defined direct value and rate improves materially. Fifty-PA precision is limited and removal sensitivity substantial; unchanged ten expected PA still fails delivered value.',
    (641553,2016):'Engel: low power yields a sensibly negative forecast closer to the poor debut. Actual strikeouts remain above prediction and most origin peers do not arrive; individual gain does not establish cohort calibration.',
    (690022,2024):'Ritter: direct rate is close to the actual poor rate, but ten expected versus 207 actual PA remains wrong. Small contribution error is not accurate opportunity.',
    (673548,2021):'Suzuki: positive foreign walks/hits now produce above-average direct talent, closer to actual. PA remains low and generic inactive US peers do not certify foreign professional support.',
    (807799,2022):'Yoshida: positive singles/walk terms overpredict actual talent while low PA partially cancel the error. Better contribution and worse conditional rate illustrate why both must be checked.',
    (808982,2023):'Lee debut: positive doubles/triples and other hit probabilities create too much optimism for the observed poor debut. A reasonable foreign fingerprint can miss; this larger worsening is retained.',
    (660271,2017):'Ohtani debut: direct foreign talent improves over the shared scalar head but remains far below actual, with 22 expected PA and zero matching profile. Mixed role is not fabricated into an MLB job.',
    (808975,2024):'Hyeseong Kim: direct rate stays modestly below observed rate and only 0.36 expected PA dominates the miss. Original name remains missing; this does not repair foreign arrival.',
    (666561,2016):'Hwang: substantial real KBO exposure produces near-average direct talent but the 57-PA actual debut is very poor. The small observed sample is not evidence of zero latent ability.',
    (553988,2021):'Machado: combined direct forecast remains poor, closer in sign to the seventeen-PA observed poor return. Sparse return and professional support prevent a broad transport claim.',
}


def main():
    assert not (OUT/'final-review.json').exists(),'Preserve completed result'
    pre=read(OUT/'preflight.json');verify(pre['input_hashes'])
    receipt=read(OUT/'evaluation-receipt.json');verify(receipt['hashes'])
    review=read(OUT/'calculation-review.json');verify(review['hashes'])
    for name in ['hitter-direct-event-result.md','hitter-direct-event-player-review.md']:
        assert 'Player walkthrough complete' in (ROOT/'docs'/name).read_text(encoding='utf8')
    old={c['row_id']:c for c in read(OLD/'completed-player-review.json')['cases']}
    cases=read(OUT/'reviewed-cases.json')['cases']
    for c in cases:
        r=c['origin'];key=r['player_id'],r['origin_year']
        if key in JUDGMENT:judgment=JUDGMENT[key]
        elif not c['direct_traces']['direct_foreign']['used'] and not r['source_addition']:
            judgment='Original MLB branch is exactly unchanged; new event probabilities are diagnostics only. '+old[c['row_id']]['review_judgment']
        elif c['actual']['PA']==0:
            judgment='Real source and cutoff-qualified probability profile remain. No next-year MLB PA means no observed hitting rate; expected contribution is a retained false-positive cost, not component confirmation.'
        else:
            # Every changed participant must receive a case-specific judgment.
            raise AssertionError(('Missing individual baseball judgment',key,r['player_name']))
        c['review_judgment']=judgment;c['player_walkthrough_status']='complete'
        if c['row_id'] in old:c['prior_source_and_fit_review']=old[c['row_id']]['review_judgment']
    save('completed-player-review.json',dict(cases=cases,player_walkthrough_status='complete',
        selection='All 45 earlier cases retained plus outcome-rank Torres and Collins; origin-only peers; outcomes not independent validation'))
    report=dict(integrity_pass=True,independent_fields=review['independent_score_fields'],cases=len(cases),
        player_walkthrough_status='complete',new_fits=0,protected_outcomes_used=False,
        predictive_improvement=False,profile_support_qualified=True,
        reasonability='Reject ready deployment: systematic negative never-debut contribution and power underprediction, with individual gains and harms reviewed',
        disposition='retain_current_no_direct_conversion_promotion',deployment_approved=False,candidate_frozen=False,broad_goal_complete=False,
        scores=read(OUT/'corrected-scores.json'),intervals=read(OUT/'intervals.json'),
        corrected_foreign_intervals=read(OUT/'corrected-foreign-intervals.json'),scope_correction=read(OUT/'numerical-scope-correction.json'),
        hashes={str(OUT/n):sha256_file(OUT/n) for n in ['predictions.parquet','corrected-scores.json','completed-player-review.json','calculation-review.json']})
    save('final-review.json',report)
    public=ROOT/'reports/model-evidence/hitter-direct-events';assert not public.exists();public.mkdir(parents=True)
    import json
    for name,obj in [('final-review.json',report),('case-comparison.json',dict(cases=cases))]:
        (public/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False,default=str)+'\n',encoding='utf8',newline='\n')
    print(f'{len(cases)} player walks complete; strongest incumbent retained. No 2026 opened.')


if __name__=='__main__':main()
