"""Review actual saved forecasts; never refit or alter sealed experiment outputs."""
import sys
import json
from pathlib import Path
import numpy as np
from universal_baseball.storage import sha256_file
from universal_baseball.mlb_event_logit import VALUES
import evaluate_hitter_value_integration_v76 as e


def audit():
    pre = e.read(e.OUT/'preflight.json')
    e.verify(pre['input_hashes'])
    e.verify(e.read(e.OUT/'scoring-contract.json')['hashes'])
    e.verify(e.read(e.OUT/'source-review.json')['review_hashes'])
    verified = e.read(e.OUT/'verification.json')
    assert verified['new_heads_replayed'] == verified['expected_heads'] == 350
    cases = e.read(e.OUT/'cases.json')
    assert len(cases) == 15
    summaries = []
    for c in cases:
        r = c['origin']
        assert set(c['actual_inputs']) == set(pre['features'])
        events = np.array([r['count_'+v] for v in e.EVENTS])
        assert events.sum() == r['next_pa']
        actual = (events@VALUES-r['next_pa']*r['origin_index'])/11.93+r['next_pa']*c['replacement']
        assert np.isclose(actual, r['next_value'], atol=1e-10)
        means = np.array([r['counts_mean_'+v] for v in e.EVENTS])
        assert np.isclose(means.sum(), r['counts_pa'], atol=1e-10)
        value = (means@VALUES-r['counts_pa']*r['origin_index'])/11.93+r['counts_pa']*c['replacement']
        assert np.isclose(value, r['counts_value'], atol=1e-10)
        assert np.isclose(sum(z['contribution'] for z in c['event_contributions']), value, atol=1e-10)
        paths = {}
        for name, t in c['saved_traces'].items():
            rebuilt = t['reference']+sum(z['path_effect'] for z in t['feature_effects'])
            saved_link = t['log_mean'] if name.startswith('count_') else t['raw_prediction']
            assert np.isclose(rebuilt, saved_link, atol=1e-9)
            prediction = np.exp(rebuilt) if name.startswith('count_') else rebuilt
            col = 'counts_raw_'+name[6:] if name.startswith('count_') else name+'_raw'
            assert np.isclose(prediction, r[col], atol=1e-9)
            paths[name] = dict(reference=t['reference'], prediction=prediction,
                link='log_mean' if name.startswith('count_') else 'identity',
                largest_effects=t['feature_effects'][:4])
        summaries.append(dict(row_id=r['row_id'], player_id=r['player_id'], name=r['player_name'],
            origin_year=r['origin_year'], fold=r['outer_fold'], selection=c['selection'], age=r['age'],
            stage=r['stage'], source_history=c['source_history'], actual_history=c['actual_history'],
            source_inputs={n:c['actual_inputs'][n] for n in ['scout_rank_score_0','on_40man',
                'draft_rank','draft_elapsed','pooled_mlb_quality','translated_reliability',
                'translated_log_exposure','translated_supported_fraction']},
            translated_probabilities={v:c['translated_profile']['translated_probability_'+v] for v in e.EVENTS},
            legacy_display_differences=c['legacy_display_differences'],
            baseline_intermediates={n:r['current_'+n] for n in ['p','conditional_pa','rate']},
            forecasts={a:{m:r[a+'_'+m] for m in ['pa','value']} for a in ['current','bridge','direct','active','counts']},
            actual_pa=r['next_pa'],actual_value=r['next_value'],relative_actual_value=c['season_relative_actual_value'],
            actual_events=dict(zip(e.EVENTS,events.tolist())),count_events=dict(zip(e.EVENTS,means.tolist())),
            count_event_value=c['event_contributions'],paths=paths,
            current_paths={n:t['feature_effects'][:4] if 'feature_effects' in t else t for n,t in c['current_saved_traces'].items()},
            refined_support=[p for p in c['training_profiles'] if p['kind']=='refined'],
            peers=c['peers_selected_without_outcomes'],peer_limit=c['peer_limit'],
            incompatibilities={a:r[a+'_incompatible'] for a in ['current','bridge','direct','active','counts']}))
    e.write('review-case-summary.json',summaries)
    paths=[e.OUT/n for n in ['preflight.json','source-review.json','scoring-contract.json','verification.json',
        'fits.json','scores.json','intervals.json','event-diagnostics.json','public-rate-context.json',
        'season-relative-sensitivity.json','scored-predictions.parquet','cases.json','review-case-summary.json']]
    paths.append(Path(__file__))
    e.write('review-audit.json',dict(hashes={str(p):sha256_file(p) for p in paths},
        exact_saved_paths_reconstructed=150,actual_response_and_count_value_rebuilt=True,
        player_walkthrough_status='pending',protected_outcomes_used=False))
    for c in summaries:
        print(c['name'],c['origin_year'],c['selection'],'PA',round(c['forecasts']['current']['pa'],2),
            round(c['forecasts']['counts']['pa'],2),c['actual_pa'],'value',
            [round(c['forecasts'][a]['value'],3) for a in ['current','bridge','direct','active','counts']],
            round(c['actual_value'],3),flush=True)


def finalize():
    audited=e.read(e.OUT/'review-audit.json');e.verify(audited['hashes'])
    pre=e.read(e.OUT/'preflight.json');e.verify(pre['input_hashes'])
    e.verify(e.read(e.OUT/'scoring-contract.json')['hashes'])
    notes=e.read(e.ROOT/'config/hitter_value_integration_v76_review.json')
    cases=e.read(e.OUT/'review-case-summary.json')
    assert set(notes['players'])=={str(c['row_id']) for c in cases}
    assert all(len(v)>100 for v in notes['players'].values())
    completed=[dict(**c,baseball_review=notes['players'][str(c['row_id'])]) for c in cases]
    e.write('reviewed-cases.json',completed)
    paths=[e.OUT/'reviewed-cases.json',e.ROOT/'config/hitter_value_integration_v76_review.json',
           e.ROOT/'docs/hitter-value-integration-v76-result.md']
    e.write('report.json',dict(execution_integrity=True,new_heads_replayed=350,baseline_heads_replayed=105,
        evaluation_rows=30506,exact_saved_paths_reconstructed=150,player_walkthrough_status='complete',
        reviewed_cases=len(completed),predictive_disposition=notes['disposition'],
        current_candidate_changed=False,full_goal_complete=False,
        profile_claim='Full and active support gaps, incomplete external production and origin-only peer limits remain qualified',
        reasonability=notes['reasonability'],source_and_execution_hashes=audited['hashes'],
        review_hashes={str(p):sha256_file(p) for p in paths},protected_outcomes_used=False,
        frozen_forecast_changed=False,deployment_approved=False))
    print('All fifteen actual player reviews complete; no candidate promotion.',flush=True)


def view():
    for c in e.read(e.OUT/'review-case-summary.json')[int(sys.argv[2]):int(sys.argv[3])]:
        history=[{n:h[n] for n in ['season','bucket','plate_appearances','strike_outs',
            'unintentional_walks','home_runs','babip_hits','doubles','triples']} for h in c['source_history']]
        compact=dict(name=c['name'],year=c['origin_year'],age=c['age'],stage=c['stage'],history=history,
            inputs=c['source_inputs'],translated_probability=c['translated_probabilities'],
            baseline=c['baseline_intermediates'],forecasts=c['forecasts'],actual_pa=c['actual_pa'],
            actual_events=c['actual_events'],actual_value=c['actual_value'],relative=c['relative_actual_value'],
            count_events=c['count_events'],paths={n:c['paths'][n] for n in ['direct','active','count_K','count_HR']},
            support={p['subset']:p['profile_people'] for p in c['refined_support']},
            peers=[{n:p[n] for n in ['player_name','age','pa_0','minor_pa_0','AA_0_pa','AAA_0_pa',
                'scout_rank_score_0','next_pa','next_value']} for p in c['peers']],
            incompatible=c['incompatibilities'])
        print(json.dumps(compact,ensure_ascii=False),flush=True)


if __name__=='__main__':
    {'audit':audit,'finalize':finalize,'view':view}[sys.argv[1]]()
