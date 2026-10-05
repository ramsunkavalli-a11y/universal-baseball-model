"""Record reviewed source admission; no projections or automatic deployment."""
from pathlib import Path
import json

from prepare_foreign_hitter_additions import ROOT,OUT,read,save,verify,sha256_file


def main():
    assert not (OUT/'final-review.json').exists(),'Preserve completed review'
    review=read(OUT/'source-review.json');verify(review['source_hashes']);verify(review['artifact_hashes'])
    walk=ROOT/'docs/hitter-foreign-additions-player-review.md';text=walk.read_text(encoding='utf8')
    cases=read(OUT/'reviewed-cases.json')['cases'];assert len(cases)==8
    for c in cases:assert str(c['player_id']) in text and str(c['origin_year']) in text and c['old_forecast'] is None and c['new_forecast'] is None
    final=dict(status='source_admission_review_complete_for_integration',source_additions=148,qualified_batting_inputs=32,
        dispositions=review['dispositions'],qualified_with_real_recent_domestic_history=review['qualified_with_real_recent_domestic_history'],
        count_fields_reconstructed=review['count_fields_reconstructed'],future_mutation_origins_checked=14,tests=review['tests'],
        player_walkthrough_status='complete_for_source_only',fixed_player_cases=8,original_forecasts_unchanged=True,
        whole_population_coverage_certified=False,unknown_Colas_role_retained=True,new_fits=0,predictive_gain_established=False,
        deployment_approved=False,goal_achieved=False,source_hashes=review['source_hashes'],
        artifact_hashes={**review['artifact_hashes'],str(walk.relative_to(ROOT)):sha256_file(walk),
            str(Path(__file__).relative_to(ROOT)):sha256_file(Path(__file__)),str((OUT/'source-review.json').relative_to(ROOT)):sha256_file(OUT/'source-review.json')})
    save(OUT/'final-review.json',final)
    evidence=ROOT/'reports/model-evidence/foreign-hitter-additions';save(evidence/'final-review.json',final)
    save(evidence/'case-comparison.json',dict(cases=[dict(name=c['name'],player_id=c['player_id'],origin_year=c['origin_year'],
        qualified_batting_input=c['admission']['qualified_for_batting_input'],disposition=c['admission']['disposition'],
        recent_foreign_PA=c['admission']['recent_foreign_pa'],recent_domestic_PA=c['admission']['recent_observed_domestic_pa'],
        observed_career_MLB_PA=c['admission']['career_observed_mlb_pa'],actual_next_MLB_PA=c['actual_next_MLB_PA'],
        old_forecast=None,new_forecast=None) for c in cases],walkthrough=str(walk.relative_to(ROOT)),
        full_traces_private_artifact_sha256=sha256_file(OUT/'reviewed-cases.json')))
    print(json.dumps(dict(source_review='complete',qualified_batting_inputs=32,new_fits=0,deployment=False)),flush=True)


if __name__=='__main__':main()
