"""Seal the separately performed prefit source-case review."""
import evaluate_hitter_value_integration_v76 as e
from universal_baseball.storage import sha256_file


def main():
    pre=e.read(e.OUT/'preflight.json');e.verify(pre['input_hashes'])
    source=e.read(e.OUT/'source-reconciliation.json')
    assert source['source_case_review_status']=='pending'
    assert source['counts_exact'] and source['common_value_labels_reconstructed']
    assert len(source['cases'])==8 and pre['baseline_heads_replayed']==105
    for c in source['cases']:
        assert sum(c['events'].values())==c['next_pa']
        assert abs(c['reconstructed_value']-c['saved_actual_value'])<1e-10
    paths=[e.ROOT/'docs/hitter-value-integration-v76-source-review.md',
           e.OUT/'source-reconciliation.json',e.Path(__file__)]
    e.write('source-review.json',dict(source_case_review_status='complete',cases=8,
        preflight_sha256=sha256_file(e.OUT/'preflight.json'),
        review_hashes={str(p):sha256_file(p) for p in paths},
        player_forecast_walkthrough_status='pending_until_fits_and_scores',protected_outcomes_used=False))
    print('Eight actual source cases reviewed; fitting gate open.',flush=True)


if __name__=='__main__':main()
