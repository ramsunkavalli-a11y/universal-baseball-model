"""Seal completed interpretations without relabeling this as a finished model."""
from pathlib import Path
import json
from universal_baseball.storage import sha256_file
from capture_hitter_2027_origin_counts import ROOT,write_once


def main():
    public=ROOT/'reports/model-evidence/hitter-2027-v1'
    frozen=ROOT/'model_artifacts/hitter-selected-2026-frozen-2026-10-05'
    manifest=json.loads((frozen/'freeze-manifest.json').read_text())
    assert sha256_file(frozen/'freeze-manifest.json')==(frozen/'freeze-manifest.sha256').read_text().strip()
    for row in manifest['files']:assert sha256_file(frozen/row['path'])==row['sha256']
    explorer=ROOT/'reports/generated/hitter-final-2026-reviewed-explorer'
    assert sha256_file(explorer/'data.json')=='3b988303a0c435e9f173ecceb1643d1ca0697bda55b280173b993af386e30997'
    assert sha256_file(explorer/'index.html')=='f1bdfbbdc7374556aa9fe61b3a93146e0a804c558053f30caad30bdba10f7609'
    for stem,documents,evidence,disposition in [
        ('translation-repair-final-review',
         ['hitter-2027-small-sample-repair-contract.md','hitter-2027-small-sample-repair-result.md'],
         ['translation-repair-provisional-scores.json','translation-repair-player-walkthrough.json.gz','translation-repair-walkthrough-receipt.json'],
         'Retain qualified reasonability safeguard alongside unchanged anchor; historical rate RMSE 0.51% worse. No accuracy-upgrade claim or deployment.'),
        ('defense-rates-final-review',
         ['hitter-2027-nonbatting-source-review.md','hitter-2027-defense-rate-assembly.md'],
         ['nonbatting-source-player-review.json','arm-official-scope-review.json','defense-rates-assembly.json','defense-rates-player-walkthrough.json.gz'],
         'Existing skill recipes refreshed with current source evidence; no newly demonstrated accuracy gain, projected exposure or awarded WAR.')]:
        paths=[ROOT/'docs'/n for n in documents]+[public/n for n in evidence]
        write_once(public/f'{stem}.json',dict(player_walkthrough_status='complete',
            disposition=disposition,full_2027_model_complete=False,deployment_approved=False,
            frozen_files_verified=len(manifest['files']),old_explorer_unchanged=True,
            hashes={str(p):sha256_file(p) for p in paths}))
    print(f'Both written interpretations sealed; {len(manifest["files"])} frozen files and old explorer unchanged. Full v1 goal remains active.')


if __name__=='__main__':main()
