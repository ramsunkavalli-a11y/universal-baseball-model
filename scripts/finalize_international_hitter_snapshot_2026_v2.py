"""Finalize preserved source/peer reviews using each receipt's actual schema."""
import json
from pathlib import Path
import subprocess
import sys

import finalize_international_hitter_snapshot_2026 as prior
from universal_baseball.international_snapshot_completion import validate_claims
from universal_baseball.storage import sha256_file

c, review, PEERS, DOCS = prior.c, prior.review, prior.PEERS, prior.DOCS


def finish():
    public = review.PUBLIC / 'report.json'
    if public.exists():
        raise FileExistsError('Preserve the completed public receipt')
    r = c.read(c.OUT / 'review.json'); review.verify(r['source_hashes']); validate_claims(r)
    peers = c.read(PEERS); review.verify(peers['source_hashes'])
    _, checks, _ = review.snapshot_counts()
    if checks != r['source_checks']:
        raise ValueError('Independent reconstruction differs from the sealed preparation')
    text = DOCS[1].read_text(encoding='utf8')
    if len(peers['source_cases']) != len(r['source_cases']):
        raise ValueError('Peer repair must retain every original control')
    for old, fixed in zip(r['source_cases'], peers['source_cases'], strict=True):
        for k in ['league', 'control', 'source_key', 'source_name']:
            if old[k] != fixed[k]: raise ValueError('Peer correction changed a focal control')
        if old['source_name'] not in text or str(old['cutoff2026']['counts']['pa']) not in text:
            raise ValueError('Missing original readable walk')
        for peer in fixed['aligned_comparison_source_peers']:
            if peer['source_key'] not in text or str(peer['window_pa']) not in text:
                raise ValueError('Missing equal-window comparison in readable review')
    readiness = c.read(c.ROOT / 'reports/model-evidence/hitter-candidate-readiness/report.json')
    evaluation = c.ROOT / 'reports/model-evidence/hitter-final-2026/report.json'
    expected = readiness['evidence_hashes']['reports\\model-evidence\\hitter-final-2026\\report.json']
    if sha256_file(evaluation) != expected:
        raise ValueError('Completed final evaluation receipt changed')
    preservation = []
    for script in ['verify_hitter_selected_2026_freeze.py', 'verify_hitter_full_2026_freeze.py']:
        process = subprocess.run([sys.executable, '-X', 'utf8', str(c.ROOT / 'scripts' / script)],
            cwd=c.ROOT, capture_output=True, text=True, check=True)
        preservation.append(dict(verifier=script, receipt=json.loads(process.stdout),
            historical_not_evaluated_flags_are_not_current_status=True))
    if sha256_file(evaluation) != expected:
        raise ValueError('Completed evaluation receipt changed during preservation checks')
    hashes = {str(p.relative_to(c.ROOT)): sha256_file(p) for p in [*DOCS, PEERS,
        c.OUT / 'review.json', c.ROOT / 'docs/hitter-next-action-correction.md',
        Path(__file__), Path(prior.__file__),
        c.ROOT / 'src/universal_baseball/international_snapshot_completion.py']}
    review.PUBLIC.mkdir(parents=True, exist_ok=True)
    payload = dict(r, source_walkthrough_status='complete_for_dated_source_snapshot',
        equal_window_comparison_review=peers['source_cases'],
        season_completion_qualified=False, universal_MLB_crosswalk_qualified=False,
        historical_role_or_park_exposure_qualified=False, deployment_approved=False,
        predictive_improvement_established=False, broad_goal_complete=False,
        player_forecasts_changed=False, freeze_preservation_checks=preservation,
        final_evaluation_receipt_sha256=expected, completed_readable_review_hashes=hashes,
        disposition='Retain dated counts, not final season totals or translated MLB talent; no forecast replacement.')
    public.write_text(json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + '\n',
                      encoding='utf8', newline='\n')
    print('Source review complete; six equal-window checks, both forecasts preserved, no new MLB evaluation.', flush=True)


if __name__ == '__main__':
    finish()
