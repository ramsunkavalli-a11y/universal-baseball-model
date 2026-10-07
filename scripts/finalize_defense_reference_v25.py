"""Close reviewed accounting, never predictive validation or the defense goal."""
from pathlib import Path
import gzip
import json
import xml.etree.ElementTree as ET
from universal_baseball.storage import sha256_file
from verify_double_play_support_v22 import write
from run_hitter_finite_return_baseline import protections

ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/'reports/model-evidence/defense-reference-v25/fold-repair'


def main():
    protections();assert not (PUBLIC/'final-review.json.gz').exists()
    reports=[PUBLIC/(s+'.json.gz') for s in ['preflight','report','player-walks','independent-review']]
    for p in reports:
        note=json.load(gzip.open(p,'rt',encoding='utf8'))
        assert note['model_fits']==0
        for path,h in {**note['hashes'],**note.get('output_hashes',{})}.items():assert sha256_file(Path(path))==h,path
    replay=json.load(gzip.open(PUBLIC/'independent-review.json.gz','rt',encoding='utf8'))
    assert replay['integrity_pass'] and replay['all_saved_assemblies_replayed']==111888
    assert replay['origin_blind_peer_groups_replayed']==8 and replay['player_records_replayed']==32
    suites=list(ET.parse(PUBLIC/'unit-tests.xml').getroot().iter('testsuite'))
    assert sum(int(s.attrib['tests']) for s in suites)==13
    assert all(int(s.attrib.get('failures',0))==int(s.attrib.get('errors',0))==0 for s in suites)
    frozen=ROOT/'model_artifacts/hitter-selected-2026-frozen-2026-10-05'
    manifest=json.loads((frozen/'freeze-manifest.json').read_text(encoding='utf8'))
    expected=next(r['sha256'] for r in manifest['files'] if r['path']=='forecast.parquet')
    assert sha256_file(frozen/'forecast.parquet')==expected
    paths=[Path(__file__),*reports,PUBLIC/'unit-tests.xml',
        ROOT/'docs/defense-reference-v25-result.md',ROOT/'docs/defense-reference-v25-player-review.md']
    write(PUBLIC/'final-review.json.gz',dict(model_fits=0,execution_integrity_pass=True,
        player_walkthrough_status='complete',main_review='All eight fixed cases and 24 origin-selected peers reviewed: reference signs, role changes, small/unknown measurements, sparse-prior artifact and unaffected infield/catcher misses.',
        native_value_reference_mismatch_confirmed=True,intrinsic_skill_preserved=True,
        naive_after_shrinkage_conversion_approved=False,compatible_sparse_prior_still_required=True,
        predictive_validation=False,deployment_approved=False,full_defense_goal_complete=False,
        next_step='Contract a centered-before-shrinkage history baseline and aligned value target; no weight sweep or older/native splice.',
        frozen_forecast_unchanged=True,explorer_unchanged=True,no_2026_selection=True,
        previous_goal_turn='No defense progress: read-only Lovich explanation. This turn saves older-quality milestone and verifies reference accounting.',
        hashes={str(p):sha256_file(p) for p in paths}))
    print('Accounting and player checkpoint complete. Compatible history prior/value comparison next; full goal active.',flush=True)


if __name__=='__main__':main()
