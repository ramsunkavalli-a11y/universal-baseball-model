"""Freeze interpretation/scoring code before any new forecast scores."""
import evaluate_hitter_value_integration_v76 as e
from universal_baseball.storage import sha256_file


def main():
    assert not (e.OUT/'scores.json').exists()
    assert not (e.OUT/'scoring-contract.json').exists()
    pre=e.read(e.OUT/'preflight.json');e.verify(pre['input_hashes'])
    paths=[e.ROOT/'scripts/score_hitter_value_integration_v76.py',
        e.ROOT/'docs/hitter-value-integration-v76-environment-supplement.md',
        e.ROOT/'docs/hitter-value-integration-v76-contract.md',e.OUT/'preflight.json',
        e.ROOT/'tests/test_hitter_value_integration_review.py',e.Path(__file__)]
    e.write('scoring-contract.json',dict(before_new_forecast_scores=True,
        hashes={str(p):sha256_file(p) for p in paths},primary_response='common_origin_value',
        secondary_response='season_relative_value_sensitivity_without_oracle_forecast_shift',
        predictive_disposition='pending_actual_player_walkthrough',protected_outcomes_used=False))
    print('Primary/secondary interpretation and scoring sealed before new scores.',flush=True)


if __name__=='__main__':main()
