"""Close the reviewed fixed comparison without refitting or promoting forecasts."""
from collections import Counter
from pathlib import Path
import json
import subprocess
import sys

import numpy as np
import polars as pl

from prepare_hitter_overseas_integration import ROOT, OUT, ANCHOR, read, verify
from universal_baseball.storage import sha256_file

RESULT = ROOT / 'docs/hitter-overseas-integration-result.md'
WALK = ROOT / 'docs/hitter-overseas-integration-player-review.md'
PUBLIC = ROOT / 'reports/model-evidence/hitter-overseas-integration'

# Manual classifications after reading each persisted source/input/head/peer trace.
# These are reviewer judgments, not machine inference or model-success assertions.
JUDGMENTS = {
    '2024:808975': ('mixed_source_gain_talent_harm', 'Corrected Hyeseong role and job improve PA, but rare translated/exposure features worsen hitting.'),
    '2024:808982': ('unsupported_talent_amplification', 'Lee has newer MLB evidence; a rare KBO contact term contributes +14.17 wins/600.'),
    '2022:673490': ('ineffective_foreign_fade', 'Ha-Seong retains 880 recent MLB PA but older foreign terms overshoot conditional talent.'),
    '2016:519346': ('professional_readiness_lost', 'Thames remains a very low workload forecast; neither saved job head splits on foreign features.'),
    '2024:592450': ('star_underprediction', 'Established Judge is recognized through recent MLB quality but both talent and PA regress below the current anchor.'),
    '2024:701762': ('fast_track_prospect_underprediction', 'Kurtz has known draft and scouting evidence, but generic prospect support does not identify his readiness.'),
    '2021:680757': ('emerging_regular_underprediction', 'Kwan contact and upper-minor history are present; PA remains low despite a modest talent gain.'),
    '2024:691406': ('partial_prospect_recognition', 'Caminero has substantial predicted opportunity but underestimates workload and talent; rehab-level terms have sizable effects.'),
    '2021:572228': ('retained_employment_harm', 'Voit trade-day activation is preserved but workload worsens, with a listing-conflict term also affecting talent.'),
    '2022:665487': ('finite_absence_confused_with_exit', 'Tatis known suspension and tentative return do not prevent very low participation; actual profile support is absent.'),
    '2024:680776': ('plausible_workload_underprediction', 'Duran clearing activation and MLB talent are represented; substantial residual PA underprediction remains.'),
    '2023:677551': ('unresolved_availability_not_modeled', 'Franco unresolved restrictions coexist with a near-certain participation forecast; later permanent facts cannot be backdated.'),
    '2024:672779': ('sourced_permanent_rule', 'Marcano known permanent eligibility rule correctly forces PA to zero; this is not learned-model validation.'),
    '2023:656555': ('useful_status_gain_still_low', 'Hoskins known signing improves expected PA from 26 to 225 versus 517, with sparse comparable jobs.'),
    '2023:474832': ('surprising_unsigned_exit', 'Belt non-signing remains an unexpected outcome; no invented retirement rule is warranted.'),
    '2017:660271': ('professional_readiness_and_talent_failure', 'Debut Ohtani has real NPB production but only 12 expected PA and a negative hitting forecast.'),
    '2021:673548': ('known_role_lost_and_low_opportunity', 'Suzuki broad OF is encoded UNKNOWN and his dated job still yields only 25 PA.'),
    '2022:807799': ('professional_readiness_lost', 'Debut Yoshida is forecast for 50 PA versus 580; high talent cannot compensate for low opportunity.'),
    '2023:808982': ('unsupported_talent_amplification', 'Debut Lee raw KBO contact drives a +10.32 rate forecast with only four matching profile people.'),
    '2023:680574': ('later_injury_uncertainty', 'McLain later injury was unavailable at the cutoff; retain the error without creating retrospective evidence.'),
    '2024:456781': ('ordinary_workload_harm', 'Solano predicted PA rises above actual; this prior harm is retained after source repair.'),
    '2016:460131': ('retained_nonarrival_domestic_history', 'Bogusevic recent AAA/MLB production is present alongside NPB; his non-return does not reveal conditional hitting.'),
    '2016:666561': ('brief_arrival_missed_sparse_rate', 'Hwang actual 57 PA are missed; a seemingly accurate conditional rate has zero matching active-profile support.'),
    '2021:519346': ('tiny_foreign_sample_instability', 'Thames two NPB PA coexist with recent MLB history yet foreign terms have large rate effects; future rate is unobserved.'),
    '2021:552662': ('retained_nonarrival_sparse_rate', 'Romero non-return is retained; large mover-count coefficient effects do not certify hitting.'),
    '2021:553988': ('brief_return_underprediction', 'Machado AAA and KBO histories are present; seventeen future PA are too little to validate talent.'),
    '2021:628329': ('retained_nonarrival_sparse_rate', 'Castillo AAA history remains and foreign doubles strongly affect rate; no next-year hitting outcome is observed.'),
    '2021:657733': ('retained_nonarrival_domestic_history', 'Ramos prior AAA power is preserved, but only one active profile person supports this foreign context.'),
    '2022:642220': ('unsupported_talent_shift_nonarrival', 'Witte old AAA production remains; a large mover-count term flips the rate without active-profile support.'),
    '2024:666632': ('unsupported_negative_rate_nonarrival', 'Perlaza AA/AAA/KBO power remains; an extreme negative rate is not validated by zero MLB PA.'),
    '2018:670541': ('lucky_value_gain_unsound_rate', 'Yordan old 57-PA DSL walk sample contributes +6.01 wins/600 and partially cancels too little expected PA.'),
    '2017:643217': ('ineffective_minor_fade', 'Benintendi older short-season walk/rank effects overwhelm newer full-season MLB evidence.'),
    '2016:592450': ('rookie_breakout_missed', 'Rookie Judge AAA power and brief MLB strikeouts are present; both workload and breakout talent are underestimated.'),
    '2023:660670': ('later_injury_uncertainty', 'Acuna forecast uses his strong current MLB year; later injury cannot be imported backward.'),
    '2017:541650': ('plausible_ordinary', 'Perez predicted workload and modest negative batting rate are close to the observed season.'),
    '2018:660271': ('ineffective_foreign_fade', 'Ohtani MLB debut is present but old foreign columns drive rate to -6.53 despite +1.67 actual.'),
    '2024:807799': ('ineffective_foreign_fade', 'Yoshida 1001 newer MLB PA coexist with a +5.12 foreign-feature accounting effect and a false-high value forecast.'),
    '2016:527038': ('plausible_ordinary', 'Flores age, upper-minor power and MLB contact give a close workload/rate/value forecast.'),
}


def save(path, value):
    assert not path.exists(), f'Preserve completed evidence: {path}'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n',
                    encoding='utf8', newline='\n')


def independent_metrics(g, arm):
    """Second scoring implementation, without importing the original scorer."""
    losses = []
    for year in sorted(g['origin_year'].unique()):
        t = g.filter(pl.col('origin_year') == year)
        pa, actual = t[arm + '_pa'].to_numpy(), t['next_pa'].to_numpy()
        value = t[arm + '_value'].to_numpy() - t['actual_relative_value'].to_numpy()
        p = t[arm + '_p'].to_numpy()
        yes = (actual > 0).astype(float)
        bounded = np.maximum(1e-12, np.minimum(1 - 1e-12, p))
        losses.append([np.mean((pa-actual)**2), np.mean(abs(pa-actual)),
                       np.mean(value**2), np.mean(abs(value)), np.mean((p-yes)**2),
                       np.mean(-yes*np.log(bounded)-(1-yes)*np.log(1-bounded))])
    mse_pa, mae_pa, mse_v, mae_v, brier, logloss = np.mean(losses, axis=0)
    return dict(pa_rmse=float(np.sqrt(mse_pa)), pa_mae=float(mae_pa),
                value_rmse=float(np.sqrt(mse_v)), value_mae=float(mae_v),
                brier=float(brier), logloss=float(logloss))


def run_check(args):
    run = subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True,
                         text=True, encoding='utf8', timeout=180)
    assert run.returncode == 0, run.stdout + run.stderr
    return dict(arguments=args, exit_code=run.returncode, stdout=run.stdout.strip())


def main():
    assert not (OUT/'final-review.json').exists(), 'Preserve completed review'
    assert RESULT.exists() and WALK.exists(), 'Manual report must precede disposition'
    pre = read(OUT/'preflight.json'); verify(pre['source_hashes'])
    seal = read(OUT/'fit-seal.json')
    assert seal['preflight_sha256'] == sha256_file(OUT/'preflight.json')
    assert seal['runner_sha256'] == sha256_file(ROOT/'scripts/fit_hitter_overseas_integration.py')
    fit = read(OUT/'fit-report.json')
    assert fit['new_heads'] == 210 and len(fit['cells']) == 35
    for cell in fit['cells']:
        verify(cell['hashes'])
        for h in cell['heads']:
            assert sha256_file(Path(h['path'])) == h['sha256']
    assert sha256_file(OUT/'predictions.parquet') == fit['output_sha256']
    receipt = read(OUT/'review-receipt.json')
    verify(receipt['input_hashes']); verify(receipt['output_hashes'])
    assert receipt['saved_heads_replayed'] == 210 and receipt['labels_independently_reconstructed']
    source = read(OUT/'addition-source-audit.json'); verify(source['hashes'])
    supplement = read(OUT/'score-supplement.json'); verify(supplement['source_hashes'])
    assert source['count_and_scout_checks'] == 2720 and source['complete_addition_predictors_unchanged']
    q = pl.read_parquet(OUT/'predictions.parquet')
    anchor = pl.read_parquet(ANCHOR).select('row_id', 'steamer_index', 'zips_index')
    q = q.join(anchor, on='row_id', how='left', validate='1:1')
    orig = q.filter(~pl.col('source_addition'))
    assert orig.height == 30506 and q.height == 30519
    known = pl.read_parquet(OUT/'features.parquet').filter(pl.col('ctx_foreign_history_known'))['row_id'].to_list()
    groups = dict(original_all=orig, additions=q.filter(pl.col('source_addition')),
                  public=orig.filter((pl.col('pa_0')>0) & pl.col('steamer_index').is_not_null() & pl.col('zips_index').is_not_null()),
                  original_foreign=orig.filter(pl.col('row_id').is_in(known)),
                  original_current_MLB=orig.filter(pl.col('pa_0')>0),
                  original_upper_never_debut=orig.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Upper minors')),
                  original_lower_never_debut=orig.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Lower minors')),
                  original_no_arrival=orig.filter(pl.col('next_pa')==0))
    for y in sorted(orig['origin_year'].unique()):
        groups['origin_'+str(y)] = orig.filter(pl.col('origin_year')==y)
    scores = read(OUT/'scores.json'); checked = 0
    for saved in scores['scopes']:
        g = groups[saved['scope']]
        assert saved['rows'] == g.height and saved['actual_pa'] == int(g['next_pa'].sum())
        assert np.isclose(saved['actual_value'], g['actual_relative_value'].sum(), atol=1e-10)
        for arm, metrics in saved['scores'].items():
            for name, v in independent_metrics(g, arm).items():
                assert np.isclose(v, metrics[name], rtol=0, atol=1e-10), (saved['scope'], arm, name)
                checked += 1
    cases = read(OUT/'reviewed-cases.json')['cases']
    keys = [f'{c["origin"]["origin_year"]}:{c["origin"]["player_id"]}' for c in cases]
    assert len(keys) == len(set(keys)) == 38 and set(keys) == set(JUDGMENTS)
    manual = WALK.read_text(encoding='utf8')
    for c in cases:
        o = c['origin']
        assert str(o['player_id']) in manual and str(o['origin_year']) in manual
        assert len(c['profile_support']) == 6 and c['mechanics']
        if o['source_addition']:
            assert all(o['current_'+s] is None for s in ['pa', 'rate', 'value'])
    categories = {why for c in cases for why in c['selection']}
    for arm in ['domestic', 'overseas']:
        assert {arm+' '+x for x in ['largest gain','largest harm','false high','false low','ordinary']} <= categories
    compact = []
    fields = ['source_position', 'age', 'age_unknown', 'on_40man', 'last_stat_gap',
              'status_major_link', 'status_finite_nonmedical', 'status_unresolved_nonmedical',
              'status_hard_unavailable', 'restriction_games_known', 'restriction_games',
              'return_report_known', 'return_report_days', 'employment_evidence_age_years',
              'draft_known', 'draft_rank', 'scout_rank_score_0', 'pooled_MLB_pa', 'pooled_AAA_pa']
    for c, key in zip(cases, keys, strict=True):
        o = c['origin']; judgment, explanation = JUDGMENTS[key]
        history = [dict(season=h['season'], level=h['bucket'], pa=h['plate_appearances'],
                        hr=h['home_runs'], k=h['strike_outs'], ubb=h['unintentional_walks'])
                   for h in c['domestic_history'] if h['season']>=o['origin_year']-2]
        forecasts = {arm:{s:o[arm+'_'+s] for s in ['p','conditional_pa','pa','rate','value']}
                     for arm in ['current','domestic','overseas']}
        mechanics = {}
        for name, m in c['mechanics'].items():
            mechanics[name] = {k:m[k] for k in ['raw_prediction','raw_log_odds','linked_probability',
                 'reference','intercept','foreign_feature_effect','foreign_splits_in_entire_model','interpretation'] if k in m}
            mechanics[name]['largest_accounting_terms'] = m['feature_effects'][:5]
        compact.append(dict(candidate_key=key, name=o['player_name'] or 'Hyeseong Kim',
            player_id=o['player_id'], origin_year=o['origin_year'], target_year=o['target_year'],
            cutoff=o['ctx_information_date'], fold=o['outer_fold'], selected_for=c['selection'],
            source_addition=o['source_addition'], recent_domestic_counts=history,
            recent_foreign_pa=c['foreign_history']['recent_foreign_pa'] if c['foreign_history'] else None,
            input_subset={k:c['actual_model_inputs'][k] for k in fields}, forecasts=forecasts,
            actual_pa=o['next_pa'], actual_relative_rate=o['actual_relative_rate'] if o['next_pa']>0 else None,
            actual_relative_value=o['actual_relative_value'], borrowed_foreign_rate=c['borrowed_foreign_rate_input'] if c['actual_model_inputs']['foreign_profile_present'] else None,
            mechanics=mechanics, origin_only_peers=c['origin_only_peers'], profile_support=c['profile_support'],
            manual_judgment=judgment, manual_explanation=explanation))
    support = pl.read_parquet(OUT/'profile-support.parquet').group_by('arm','head').agg(
        pl.len().alias('rows'), (pl.col('profile_people')==0).sum().alias('unsupported'),
        (pl.col('profile_people')<20).sum().alias('under_20_people')).sort('arm','head').to_dicts()
    tests = run_check(['-m','pytest','tests/test_hitter_overseas_inputs.py','tests/test_hitter_overseas_scoring.py','-q'])
    freeze = run_check(['scripts/verify_hitter_full_2026_freeze.py'])
    audited = [RESULT, WALK, Path(__file__), OUT/'review-receipt.json', OUT/'reviewed-cases.json',
               OUT/'scores.json', OUT/'intervals.json', OUT/'score-supplement.json',
               OUT/'addition-source-audit.json', OUT/'fit-seal.json']
    final = dict(status='review_complete_do_not_promote_repair_representation',
        execution_integrity='verified_with_recorded_preparation_and_check_order_qualifications',
        profile_support_decision='sparse_or_absent_for_material_foreign_and_availability_profiles',
        predictive_performance='fails_delivered_value_and_PA_weighted_hitting_comparison',
        baseball_reasonability='fails_rare_feature_and_newer_MLB_weighting_checks',
        player_walkthrough_status='complete', player_walkthrough_artifact=str(WALK.relative_to(ROOT)),
        manual_case_count=38, manual_classifications=dict(Counter(JUDGMENTS[k][0] for k in keys)),
        saved_heads_replayed=210, independently_recomputed_score_fields=checked,
        source_addition_count_checks=2720, future_mutation_origins=source['future_mutation_origins'],
        addition_feature_mutation_check_completed_after_fitting_started=True,
        tests=tests, protected_forecast=freeze, deployment_approved=False,
        protected_outcomes_used=False, current_forecast_and_explorer_changed=False,
        broad_goal_achieved=False,
        next_work='Coherent talent evidence precision/fade and professional/finite-absence representation; no new fit in this closeout',
        scores=scores, intervals=read(OUT/'intervals.json'), supplemental_diagnostics=supplement['rates'],
        profile_support=support, source_hashes=pre['source_hashes'],
        artifact_hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in audited})
    # Do not mutate original pending receipts; append final disposition with its own hashes.
    save(OUT/'final-review.json', final)
    save(PUBLIC/'final-review.json', final)
    save(PUBLIC/'case-comparison.json', dict(cases=compact,
        peer_rule=read(OUT/'reviewed-cases.json')['peer_rule'],
        readable_review=str(WALK.relative_to(ROOT)),
        private_full_trace_sha256=sha256_file(OUT/'reviewed-cases.json'),
        rate_units='future-season-relative batting wins above average per 600 PA',
        value_units='batting plus replacement wins, not full WAR',
        bulk_foreign_history_and_member_exports_not_published=True))
    print(json.dumps(dict(status=final['status'], manual_cases=38, score_fields=checked,
                         tests=tests['stdout'], freeze=freeze['stdout']), indent=2))


if __name__ == '__main__':
    main()
