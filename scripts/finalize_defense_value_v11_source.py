"""Close only the matched source gate after arithmetic and readable source walks."""
from pathlib import Path
import json
from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections, save

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'reports/generated/defense-value-v11'
PUBLIC = ROOT/'reports/model-evidence/defense-value-v11'


def main():
    protections()
    assert not (OUT/'source-final-review.json').exists()
    review = json.loads((OUT/'independent-source-verification.json').read_text())
    for p, h in {**review['hashes'], **review['output_hashes']}.items():
        assert sha256_file(Path(p)) == h, p
    cases = json.loads((OUT/'reviewed-source-player-cases.json').read_text())['records']
    assert len(cases) == 36 and sum(c['is_focal'] for c in cases) == 9
    assert {c['player_id'] for c in cases if c['is_focal']} == {
        545361, 595281, 592206, 677951, 694192, 682626, 662139, 621566, 805811}
    doc = ROOT/'docs/defense-value-v11-source-player-review.md'
    text = doc.read_text(encoding='utf8')
    assert all(s in text for s in ('Kiermaier', 'Trout', 'Castellanos', 'Witt',
        'Chourio', 'Álvarez', 'Varsho', 'Olson', 'Eldridge', 'unknown'))
    result = dict(status='matched_scoped_source_ready_for_predeclared_integration',
        player_walkthrough_status='complete', source_case_records=36, focal_cases=9,
        participant_coverage=review['participant_coverage'],
        independent_channel_rows_replayed=review['original_channel_rows_replayed'],
        measured_OF_only_totals_recovered=len(review['recovered_OF_only_totals']),
        fits=0, predictive_improvement_claim=False, full_WAR_claim=False,
        measurement_scope='Seven range positions, framing/throwing/blocking, OF arms, 1B receiving; DP and non-OF arms excluded.',
        lower_minors_skill_transfer_validated=False, unknown_quality_fallback='mean zero with unknown evidence flag, not an observed average grade',
        forecast_or_explorer_changed=False, protected_outcomes_used=False,
        next_step='Lock one delivered-defense/expanded-value contrast with unchanged batting and reviewed opportunity anchors, then score and walk players.',
        hashes={str(p):sha256_file(p) for p in [Path(__file__), doc, OUT/'source-review.json',
            OUT/'independent-source-verification.json', OUT/'reviewed-source-player-cases.json',
            OUT/'reviewed-component-ledger.parquet', OUT/'reviewed-player-ledger.parquet', OUT/'batting-ledger.parquet']})
    for dest in (OUT, PUBLIC): save(dest/'source-final-review.json', result)
    protections()
    print(json.dumps(dict(status=result['status'], player_walkthrough_status='complete')))


if __name__ == '__main__':
    main()
