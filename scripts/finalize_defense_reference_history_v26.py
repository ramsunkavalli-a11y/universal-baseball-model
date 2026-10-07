"""Seal a reviewed research correction, not deployment or the full defense goal."""
from pathlib import Path
import json
import xml.etree.ElementTree as ET
from universal_baseball.storage import sha256_file
from verify_defense_reference_history_v26 import ROOT,PUBLIC,read
from verify_double_play_support_v22 import write
from run_hitter_finite_return_baseline import protections


def main():
    protections();dest=PUBLIC/'final-review.json.gz';assert not dest.exists()
    reports=[PUBLIC/(s+'.json.gz') for s in ('preflight','report','player-walks','independent-review','raw-player-source-review','totals-diagnosis')]
    for path in reports:
        note=read(path);assert note['model_fits']==0
        for p,h in {**note.get('hashes',{}),**note.get('output_hashes',{})}.items():assert sha256_file(Path(p))==h,p
    replay=read(PUBLIC/'independent-review.json.gz');raw=read(PUBLIC/'raw-player-source-review.json.gz')
    assert replay['execution_integrity_pass'] and replay['quality_predictions_replayed']==13402
    assert replay['value_predictions_replayed']==12432 and replay['OF_channels_replayed']==37296
    assert replay['player_groups_replayed']==16 and replay['player_records_replayed']==64
    assert replay['selections_and_origin_only_peers_replayed'] and replay['all_scores_and_intervals_replayed']
    assert raw['raw_minor_splits_replayed']==428 and raw['annual_position_records_replayed']==582
    suites=list(ET.parse(PUBLIC/'unit-tests.xml').getroot().iter('testsuite'))
    assert sum(int(s.attrib['tests']) for s in suites)==9
    assert all(int(s.attrib.get('errors',0))==int(s.attrib.get('failures',0))==int(s.attrib.get('skipped',0))==0 for s in suites)
    docs=[ROOT/'docs'/('defense-reference-history-v26-'+s+'.md') for s in ('result','player-review','contract','storage-note')]
    review=docs[1].read_text(encoding='utf8')
    assert all(name in review for name in ('Trout','Happ','Soto','Bellinger','Castellanos','Rafaela','Witt','Willson Contreras','Siani','Adell','Burleson','Benson','Hernández','Chourio','Robert'))
    frozen=ROOT/'model_artifacts/hitter-selected-2026-frozen-2026-10-05'
    manifest=json.loads((frozen/'freeze-manifest.json').read_text(encoding='utf8'))
    expected=next(s['sha256'] for s in manifest['files'] if s['path']=='forecast.parquet')
    assert sha256_file(frozen/'forecast.parquet')==expected
    explorer=ROOT/'reports/generated/hitter-final-2026-reviewed-explorer'
    build=read(explorer/'build-review.json')
    for p,h in build['output_hashes'].items():assert sha256_file(Path(p))==h,p
    paths=[Path(__file__),*reports,*docs,PUBLIC/'unit-tests.xml',frozen/'freeze-manifest.json',explorer/'build-review.json']
    write(dest,dict(model_fits=0,execution_integrity_pass=True,player_walkthrough_status='complete',
        main_review='All sixteen groups and 64 player calculations reviewed, with annual source, centering/prior arithmetic, role/exposure, quality and delivery tradeoffs, origin-selected peers, nonarrivals and controls.',
        retain_as_research='Centered-before-shrinkage OF history; intrinsic skill separate; unmeasured quality explicit.',
        conditional_MLB_quality_evidence_positive=True,delivered_defense_evidence_positive=True,
        expanded_value_gain_uncertain=True,cohort_totals_reasonable=False,
        minor_talent_validated=False,age_development_improved=False,deployment_approved=False,
        full_defense_goal_complete=False,frozen_forecast_unchanged=True,explorer_unchanged=True,no_2026_selection=True,
        previous_goal_turn='No defense progress: read-only Lovich explanation. This turn completes the fixed OF comparison, independent source/score replay, player review and channel-level totals diagnosis.',
        next_step='Reconcile unchanged first-base/catcher reference priors and opportunities, then older-quality compatibility and supported minor-to-MLB talent; no prior tournament.',
        hashes={str(p):sha256_file(p) for p in paths}))
    print('Reviewed OF research correction sealed; overall defense goal remains active.')


if __name__=='__main__':main()
