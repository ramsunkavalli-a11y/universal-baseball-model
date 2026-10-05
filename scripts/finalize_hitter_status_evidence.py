"""Seal the actual source walkthrough, without approving forecasts or the goal."""
from pathlib import Path
import json

from prepare_hitter_status_evidence_v2 import ROOT,OUT,read,save,verify,sha256_file


def main():
    assert not (OUT/'final-review.json').exists(),'Preserve completed review'
    review=read(OUT/'independent-review.json');verify(review['hashes'])
    result=ROOT/'docs/hitter-status-evidence-result.md';walk=ROOT/'docs/hitter-status-player-review.md'
    text=walk.read_text(encoding='utf8');cases=read(OUT/'reviewed-cases.json')['cases']
    assert len(cases)==15 and review['rows_replayed']==83300 and review['historical_MLB_labels_reconstructed']==30506
    for c in cases:
        assert str(c['player_id']) in text and str(c['origin_year']) in text and c['new_forecast'] is None
    assert all(not c['changed_indicators'] for c in review['changes']['rows'])
    paths=[result,walk,Path(__file__),OUT/'independent-review.json',OUT/'reviewed-cases.json',OUT/'peer-membership-seal.json']
    final=dict(status='source_review_complete_retain_for_integration',player_walkthrough_status='complete_for_source_only',
        all_source_origins_retained=83300,employment_and_active_restrictions_independently_replayed=83300,
        historical_MLB_forecast_labels_reconstructed=30506,source_state_labels_changed=67,status_indicator_rows_changed=0,
        literal_listings_preserved=True,clinical_spells_unchanged=True,clinical_normalizer_newly_recertified=False,
        negative_listing_explicit_major_event_age_days=review['negative_listing_explicit_major_event_age_days'],
        multiple_restriction_rows=review['multiple_restriction_rows'],tests=review['tests'],protected_freeze=review['protected_freeze'],
        player_cases=15,peer_selection_before_outcomes=True,ambiguous_roles_and_stale_employment_remain=True,
        new_fits=0,forecasts_changed=False,predictive_improvement_established=False,deployment_approved=False,goal_achieved=False,
        source_hashes=review['hashes'],artifact_hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in paths})
    save(OUT/'final-review.json',final)
    public=ROOT/'reports/model-evidence/hitter-status-evidence'
    save(public/'final-review.json',final)
    compact=[]
    for c in cases:
        s=c['scoped_status'];old=c['unchanged_forecast'];context=c['previous_completed_context_forecast']
        compact.append(dict(name=c['name'],player_id=c['player_id'],origin_year=c['origin_year'],
            information_date=c['source_population']['information_date'],literal_40man=s['literal_returned_40man'],
            employment=s['employment']['state'],major_link=s['status_major_link'],absence=s['absence']['state'],
            active_channels=sorted(s['absence']['active_restrictions']),hard_unavailable=s['status_hard_unavailable'],
            tentative_return=s['absence']['reported_return_date'],current_PA=old['preseason_pa'] if old else None,
            prior_context_PA=context['ctx_pa'] if context else None,actual_next_MLB_PA=c['actual_next_MLB_PA'],new_PA=None,
            actual_stats_and_traces_private_artifact_sha256=sha256_file(OUT/'reviewed-cases.json')))
    save(public/'case-comparison.json',dict(cases=compact,source_walkthrough=str(walk.relative_to(ROOT)),
        forecasts_unchanged=True,no_new_predictive_comparison=True))
    print(json.dumps(dict(source_review='complete',rows=83300,cases=15,new_fits=0,deployment=False)),flush=True)


if __name__=='__main__':main()
