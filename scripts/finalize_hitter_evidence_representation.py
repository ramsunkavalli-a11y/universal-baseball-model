"""Append the performed manual review and independently audit published scores."""
from collections import Counter
from pathlib import Path
import json
import subprocess
import sys

import numpy as np
import polars as pl
from prepare_hitter_evidence_representation import ROOT, OUT, read, save
from universal_baseball.storage import sha256_file

PUBLIC=ROOT/'reports/model-evidence/hitter-evidence-representation'
RESULT=ROOT/'docs/hitter-evidence-representation-result.md'
WALK=ROOT/'docs/hitter-evidence-representation-player-review.md'

# Judgments are authored after reading saved source, fit accounting and peers.
# They are not inferred automatically from the sign of the final error.
JUDGMENTS={
 '2024:808975':('useful_professional_job_repair','Professional activity and listing now produce plausible opportunity, but conditional support is sparse.'),
 '2024:808982':('stable_talent_incomplete_opportunity','KBO amplification is removed; foreign production barely affects rate and workload remains much too low.'),
 '2022:673490':('modest_talent_and_workload_gain','Newer MLB information remains; both components improve but still undershoot. Sparse foreign profiles qualify the result.'),
 '2016:519346':('professional_job_gain_talent_failure','Known first-team activity and employment improve opportunity; KBO production does not meaningfully determine hitting.'),
 '2024:592450':('recognized_star_still_regressed','MLB quality drives a strong rate; age and expected-workload regression still miss the realized peak.'),
 '2024:701762':('fast_track_prospect_failure','Known pedigree and rank are present, but generic no-MLB opportunity and attenuated production severely underpredict.'),
 '2021:680757':('emerging_regular_failure','AA/AAA production is retained; generic conditional-workload and pooled talent remain too low.'),
 '2024:691406':('brief_debut_prospect_harm','Actual minor and brief MLB evidence remain, but both rate and opportunity decline against a successful later season.'),
 '2021:572228':('retained_employment_harm','Dated major link remains; PA and contribution worsen despite real job evidence.'),
 '2022:665487':('finite_absence_not_resolved','Last positive MLB workload helps conditional PA, but literal listing and sparse availability learning still suppress participation.'),
 '2024:680776':('plausible_small_gain','Newer MLB work and quality produce a modest contribution gain while PA remains too low.'),
 '2023:677551':('unresolved_restriction_ignored','Ordinary roster and work paths still imply near-certain participation despite known unresolved restriction.'),
 '2024:672779':('explicit_permanent_rule','The sourced permanent rule forces zero; the raw learner does not establish this result.'),
 '2023:656555':('useful_returner_job_gain','Retained old MLB work plus dated employment improves opportunity and delivered contribution; seven conditional profile people remain sparse.'),
 '2023:474832':('surprising_unsigned_exit','No invented retirement; lack of signed work modestly lowers expected opportunity, but later non-signing remains an error.'),
 '2017:660271':('mixed_role_source_and_support_gap','Absent major-link/listing evidence and no exact support leave a very low debut forecast despite pedigree and NPB production.'),
 '2021:673548':('professional_job_gain_talent_failure','Broad OF and first-team work are repaired; opportunity is still low and foreign production nearly ignored.'),
 '2022:807799':('professional_job_gain_talent_failure','Professional work improves PA, but pooled talent remains below average despite strong NPB production.'),
 '2023:808982':('plausible_workload_rate_miss','New debut workload is much more plausible; poor subsequent small-sample hitting is not anticipated.'),
 '2023:680574':('later_injury_uncertainty','Later injury is not backdated; large zero-work outcome remains, with modestly lower rate and PA.'),
 '2024:456781':('employment_opportunity_harm','Known work and job increase PA above actual and amplify a rate miss; age already lowers projections.'),
 '2016:460131':('retained_nonarrival','Real domestic and foreign evidence remain, with a small expected opportunity and no later arrival.'),
 '2016:666561':('job_source_gap_and_small_sample_rate','Unknown employment suppresses PA; realized poor rate is observed only over 57 PA, not a source-absence zero.'),
 '2021:519346':('tiny_foreign_source_stable_nonarrival','Two actual NPB PA have negligible production influence; older MLB activity is retained, no later return.'),
 '2021:552662':('retained_nonarrival','Actual foreign work is retained but no dated linked job; small expected PA, zero observed outcome.'),
 '2021:553988':('sparse_return_small_observed_sample','Professional work raises conditional PA but low participation dominates; 17 actual PA do not establish precise talent.'),
 '2021:628329':('retained_nonarrival','Domestic and small foreign history remain; expected opportunity is small and no later MLB return occurs.'),
 '2021:657733':('retained_nonarrival','Actual AAA and KBO histories remain; no future return is used for eligibility or job inputs.'),
 '2022:642220':('retained_nonarrival','Minor and NPB history remain; no linked job and absent conditional support, zero later MLB PA.'),
 '2024:666632':('retained_false_positive_cost','Professional and upper-minor activity yield 41 expected PA against no arrival; retained in all scoring.'),
 '2018:670541':('source_amplification_fixed_talent_not_solved','Old DSL removal now has negligible same-fit effect; both prospect talent and expected workload remain serious misses.'),
 '2017:643217':('sensible_newer_MLB_weighting','Tiny old short-season influence is removed; recent MLB work is retained and the new rate improves without implausible amplification.'),
 '2016:592450':('brief_debut_star_false_low','Real AAA and MLB evidence and rank remain but generic rate and workload miss an exceptional later season.'),
 '2023:660670':('later_injury_star_false_high','Prior star production supports the high rate; later injury and decline are not origin-known inputs.'),
 '2017:541650':('ordinary_modest_harm','Rate is nearly unchanged; higher PA worsens delivered error against modest actual hitting.'),
 '2018:660271':('stable_postdebut_forecast','Prior extreme NPB effect is removed; newer MLB quality produces reasonable rate and PA, with unresolved exact-profile support.'),
 '2024:807799':('pooled_MLB_head_harm_not_foreign_amplification','New rate worsens while foreign production term is negligible; the refitted shared head, not raw NPB dominance, drives the harm.'),
 '2016:527038':('ordinary_minor_harm','Newer MLB quality remains; small workload/rate changes slightly worsen contribution without a rare source effect.'),
 '2018:443558':('largest_gain_retained_employment','New PA is more sensible with recent large workloads and dated job; ensuing exceptional rate remains badly underpredicted.'),
 '2016:430832':('largest_harm_talent_decline_interaction','Increased PA is closer to actual; optimistic rate amplifies the unexpected decline. Tiny rehab production is not the cause.'),
 '2016:456665':('ordinary_product_cancellation','Near-perfect delivered product partly cancels too little workload and too much rate; neither component is independently exact.'),
}


def independent_score(g,arm):
    values=[]
    for year in sorted(g['origin_year'].unique()):
        f=g.filter(pl.col('origin_year')==year)
        ap=f['next_pa'].to_numpy();dp=f[arm+'_pa'].to_numpy()-ap
        dv=f[arm+'_value'].to_numpy()-f['actual_relative_value'].to_numpy()
        p=f[arm+'_p'].to_numpy();yes=(ap>0).astype(float);lp=np.clip(p,1e-12,1-1e-12)
        values.append([np.mean(dp**2),np.mean(abs(dp)),np.mean(dp),np.mean(dv**2),np.mean(abs(dv)),np.mean(dv),
                       np.mean((p-yes)**2),np.mean(-yes*np.log(lp)-(1-yes)*np.log1p(-lp))])
    v=np.mean(values,axis=0)
    return dict(pa_rmse=float(np.sqrt(v[0])),pa_mae=float(v[1]),pa_bias=float(v[2]),
                value_rmse=float(np.sqrt(v[3])),value_mae=float(v[4]),value_bias=float(v[5]),brier=float(v[6]),logloss=float(v[7]),
                expected_pa=float(g[arm+'_pa'].sum()),expected_arrivals=float(g[arm+'_p'].sum()),expected_value=float(g[arm+'_value'].sum()))


def command(args):
    r=subprocess.run([sys.executable,*args],cwd=ROOT,capture_output=True,text=True,encoding='utf8')
    assert r.returncode==0,r.stdout+r.stderr
    return dict(args=args,exit_code=r.returncode,stdout=r.stdout)


def main():
    receipt=read(OUT/'review-receipt.json')
    assert receipt['saved_heads_replayed']==140 and receipt['labels_independently_reconstructed']
    for p,h in {**receipt['input_hashes'],**receipt['output_hashes']}.items():assert sha256_file(Path(p))==h,p
    cases=read(OUT/'reviewed-cases.json')['cases'];scores=read(OUT/'scores.json')
    keys=[f'{c["origin"]["origin_year"]}:{c["origin"]["player_id"]}' for c in cases]
    assert len(keys)==len(set(keys))==41 and set(keys)==set(JUDGMENTS)
    q=pl.read_parquet(OUT/'predictions.parquet');checked=0
    for scope in scores['scopes']:
        name=scope['scope']
        if name not in ['original_all','additions'] and not name.startswith('origin_'):continue
        g=q.filter(pl.col('source_addition')) if name=='additions' else q.filter(~pl.col('source_addition'))
        if name.startswith('origin_'):g=g.filter(pl.col('origin_year')==int(name.split('_')[1]))
        assert g.height==scope['rows']
        for a,expected in scope['scores'].items():
            actual=independent_score(g,a)
            for n,value in actual.items():assert np.isclose(value,expected[n],atol=1e-9,rtol=0),(name,a,n);checked+=1
    tests=command(['-m','pytest','tests/test_hitter_evidence_representation.py','tests/test_hitter_representation_fit_recovery.py',
                   'tests/test_hitter_representation_scoring.py','-q','-p','no:cacheprovider'])
    freeze=command(['scripts/verify_hitter_full_2026_freeze.py'])
    compact=[]
    fields=['age','source_position','on_40man','status_major_link','status_agreement_unspecified','status_finite_nonmedical',
            'status_unresolved_nonmedical','status_hard_unavailable','draft_known','draft_rank','scout_rank_score_0',
            'last_MLB_work','signed_first_team_work','position_outfield_unspecified']
    for c,key in zip(cases,keys,strict=True):
        o=c['origin'];a=c['actual_model_inputs'];kind,why=JUDGMENTS[key]
        assert c['mechanics'] and c['source_representation'] and len(c['profile_support'])==4
        if o['source_addition']:assert o['current_pa'] is None and o['current_rate'] is None
        mechanics={}
        for n,m in c['mechanics'].items():
            mechanics[n]={p:m[p] for p in ['intercept','prediction','reference','raw_prediction','linked_probability'] if p in m}
            mechanics[n]['largest_terms']=m['feature_effects'][:8]
            if n.endswith('_rate'):
                mechanics[n]['source_terms']=[t for t in m['feature_effects'] if t['feature'].startswith('evidence_')]
        compact.append(dict(candidate_key=key,player_id=o['player_id'],name=o['player_name'] or 'Hyeseong Kim',
            origin_year=o['origin_year'],target_year=o['target_year'],fold=o['outer_fold'],cutoff=a['ctx_information_date'],
            selection=c['selection'],source_addition=o['source_addition'],
            recent_domestic_counts=[{n:r[n] for n in ['season','bucket','plate_appearances','home_runs','strike_outs','unintentional_walks']}
                                    for r in c['recent_domestic_counts']],
            source_representation=c['source_representation'],input_subset={n:a[n] for n in fields},
            forecasts={arm:{n:o[arm+'_'+n] for n in ['p','conditional_pa','pa','rate','value']}
                       for arm in ['current','domestic','overseas','repaired_domestic','repaired_overseas']},
            actual_pa=o['next_pa'],actual_rate=o['actual_relative_rate'] if o['next_pa'] else None,
            actual_value=o['actual_relative_value'],mechanics=mechanics,profile_support=c['profile_support'],
            origin_only_peers=c['origin_only_peers'],manual_judgment=kind,manual_explanation=why))
    paths=[RESULT,WALK,Path(__file__),OUT/'review-receipt.json',OUT/'reviewed-cases.json',OUT/'scores.json',
           OUT/'intervals.json',OUT/'mechanics-probes.json',OUT/'fit-seal.json',OUT/'resume-seal.json']
    final=dict(status='review_complete_keep_current_no_integrated_promotion',player_walkthrough_status='complete',
        manual_case_count=41,manual_classifications=dict(Counter(v[0] for v in JUDGMENTS.values())),
        execution_integrity='140 heads replay and compatible targets independently reconstructed; interrupted-model hash timing qualified',
        independently_recomputed_score_fields=checked,profile_support_decision='Sparse intersections retained; no unqualified full-cohort claim',
        predictive_performance='Small uncertain PA gain; no delivered-value or overall hitting gain versus current',
        baseball_reasonability='Source amplification repaired; prospect talent/readiness and rare availability remain unresolved',
        tests=tests,protected_forecast=freeze,protected_outcomes_used=False,deployable_candidate_selected=False,
        deployment_approved=False,current_forecast_and_explorer_changed=False,broad_goal_achieved=False,
        scores=scores,intervals=read(OUT/'intervals.json'),mechanics_probes=read(OUT/'mechanics-probes.json'),
        profile_support=receipt['profile_support'],readable_result=str(RESULT.relative_to(ROOT)),
        player_walkthrough_artifact=str(WALK.relative_to(ROOT)),
        next_work='Audit why the pooled head barely uses non-established MLB production; preserve useful current talent routing before any new fit. Freeze before authorized 2026 access.',
        hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in paths})
    save('final-review.json',final)
    PUBLIC.mkdir(parents=True,exist_ok=True)
    for name,value in [('final-review.json',final),('case-comparison.json',dict(cases=compact,
        player_walkthrough_status='complete',peer_rule=read(OUT/'reviewed-cases.json')['peer_rule'],
        rate_units='future-season-relative batting wins above average per 600 PA',value_units='batting plus replacement, not full WAR',
        bulk_foreign_sources_and_member_exports_not_published=True))]:
        path=PUBLIC/name;assert not path.exists()
        path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False,default=str)+'\n',encoding='utf8',newline='\n')
    print(json.dumps(dict(status=final['status'],cases=41,independent_fields=checked,tests=tests['stdout'],freeze=freeze['stdout']),indent=2))


if __name__=='__main__':main()
