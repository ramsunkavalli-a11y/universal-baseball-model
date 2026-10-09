"""Append completion receipts without rewriting initial pending evidence."""
import json
from capture_hitter_2027_origin_counts import ROOT,write_once
from universal_baseball.storage import sha256_file


def main():
    root=ROOT/'reports/model-evidence/hitter-2027-v1'
    paths=[ROOT/'docs'/p for p in ['hitter-2027-full-value-review.md','hitter-2027-whole-value-initial-review.md',
        'hitter-2027-whole-value-result.md','hitter-2027-current-control-initial-review.md','hitter-2027-current-control-result.md']]
    paths += [root/p for p in ['historical-full-value-reviewed-scores.json','historical-full-value-cohort-diagnosis.json',
        'historical-full-value-reviewed-player-walks.json.gz','historical-full-value-cohort-walks.json.gz',
        'current-control-reviewed-v2-assembly.json','current-control-reviewed-v2-player-walks.json.gz']]
    protected={
        ROOT/'model_artifacts/hitter-selected-2026-frozen-2026-10-05/forecast.parquet':'1e92cdf15ead01576bdd8e93cecb5d219370a57fee512ab289851004c5a81171',
        ROOT/'reports/generated/hitter-final-2026-reviewed-explorer/data.json':'3b988303a0c435e9f173ecceb1643d1ca0697bda55b280173b993af386e30997',
        ROOT/'reports/generated/hitter-final-2026-reviewed-explorer/index.html':'f1bdfbbdc7374556aa9fe61b3a93146e0a804c558053f30caad30bdba10f7609'}
    for p,h in protected.items():assert sha256_file(p)==h
    write_once(root/'full-value-control-checkpoint.json',dict(
        historical_component_review='complete_qualified_development_retention',
        current_control_source_review='complete_estimated_not_official_service_register',
        pending_receipts_superseded_by_written_reviews=True,
        preserve_initial_results=True,frozen_outputs_unchanged=True,
        completed_goal=False,release_approved=False,
        remaining=['contract tails/terms','supported annual paths and uncertainty','control net valuation','2027 explorer and browser QA'],
        hashes={str(p):sha256_file(p) for p in paths}))
    print('Historical/value/control checkpoint sealed; finalization goal remains active.')


if __name__=='__main__':main()
