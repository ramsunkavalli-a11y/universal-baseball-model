"""Publish an additive interpretation receipt without changing sealed scores."""
from pathlib import Path
import json
from universal_baseball.storage import sha256_file
from score_hitter_final_2026 import ROOT,OUT,read,write

NARRATED=[592450,670541,680776,665489,691718,681198,805808,641343,664034,
          667670,670770,593871,702518,805795,815908,815888,701762,808982,687462,699912]


def main():
    assert not (OUT/'review-completion.json').exists(),'Preserve interpretation receipt'
    scores=read(OUT/'score-report.json');walks=read(OUT/'player-walks.json');selection=read(OUT/'walk-selection.json')
    assert walks['all_sources_and_saved_fit_calculations_replayed'] and not scores['post_result_fit_or_tuning']
    by_id={w['player_id']:w for w in walks['walks']};assert set(NARRATED)<=set(by_id)
    docs=[ROOT/'docs/hitter-final-2026-result.md',ROOT/'docs/hitter-final-2026-player-review.md']
    assert all(p.exists() for p in docs)
    review=dict(status='completed_single_frozen_evaluation_with_qualified_disposition',player_walkthrough_status='complete',
        mechanical_player_replays=len(by_id),focal_cases=len(selection['focal_ids']),narrated_player_ids=NARRATED,
        source_and_execution_pass=True,predictive_superiority_established=False,baseball_reasonability='Qualified: close league PA hides prospect workload/value underprediction; major misses include rate and workload; sparse cameo promotions and entrant coverage unresolved.',
        disposition='Retain evaluated research reference; no automatic full-WAR, universal-coverage or trade-value deployment.',
        no_post_result_forecast_change=True,future_2026_retesting_forbidden=True,public_matched_comparison_unavailable=True,
        next_work='For a later forecast: entrant coverage and matched public benchmark, then one bounded historical prospect conditional-workload/exposure audit. No algorithm tournament or team-record rerun.',
        input_hashes={str(p):sha256_file(p) for p in [Path(__file__),OUT/'score-report.json',OUT/'player-walks.json',OUT/'walk-selection.json',*docs]})
    write(OUT/'review-completion.json',review)
    dest=ROOT/'reports/model-evidence/hitter-final-2026';dest.mkdir(parents=True,exist_ok=True)
    assert not (dest/'report.json').exists()
    # Publish compact evidence with every selected player's original counts,
    # intermediates and exact rate sum; omit duplicate full pre-freeze/tree dumps.
    compact=[]
    for w in walks['walks']:
        a={k:v for k,v in w.items() if k not in ['pre_freeze_walk','participation_trace','conditional_pa_trace','all_actual_rate_inputs']}
        for name in ['participation_trace','conditional_pa_trace']:
            a[name]={k:w[name][k] for k in ['reference','raw_prediction','feature_effects','interpretation']}
        compact.append(a)
    write(dest/'report.json',dict(scores=scores,review_completion=review,selection=selection,player_walks=compact,
        completed_target_source=read(ROOT/'reports/generated/hitter-final-2026-source/reconciliation.json'),
        opening_authorization=read(ROOT/'reports/generated/hitter-final-2026-source/authorization-and-freeze.json'),
        evidence_hashes={str(p):sha256_file(p) for p in [OUT/'review-completion.json',OUT/'player-walks.json',OUT/'score-report.json']}))
    print(json.dumps(dict(status=review['status'],narrated=len(NARRATED),replayed=len(by_id),public_evidence=str(dest/'report.json'))),flush=True)


if __name__=='__main__':main()
