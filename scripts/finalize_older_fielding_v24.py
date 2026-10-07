"""Close the source/player checkpoint, not defense accuracy or the full goal."""
from pathlib import Path
import json
import xml.etree.ElementTree as ET
from universal_baseball.storage import sha256_file
from verify_double_play_support_v22 import read,write
from run_hitter_finite_return_baseline import protections

ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/'reports/model-evidence/defense-older-quality-v24'


def main():
    protections()
    assert not (PUBLIC/'final-review.json.gz').exists()
    reports=['audit-report','independent-review','player-walks','walk-replay']
    for name in reports:
        r=read(PUBLIC/(name+'.json.gz'))
        assert r['model_fits']==0
        for p,h in r['hashes'].items():assert sha256_file(Path(p))==h,p
    replay=read(PUBLIC/'walk-replay.json.gz');assert replay['calculations_pass'] and replay['origin_blind_peer_groups_replayed']==9
    tests=ET.parse(PUBLIC/'unit-tests.xml').getroot()
    suites=list(tests.iter('testsuite'))
    assert sum(int(s.attrib['tests']) for s in suites)==32
    assert all(int(s.attrib.get('failures',0))==int(s.attrib.get('errors',0))==0 for s in suites)
    package=ROOT/'model_artifacts/hitter-selected-2026-frozen-2026-10-05'
    manifest=json.loads((package/'freeze-manifest.json').read_text(encoding='utf8'))
    expected=next(r['sha256'] for r in manifest['files'] if r['path']=='forecast.parquet')
    assert sha256_file(package/'forecast.parquet')==expected
    paths=[Path(__file__),*[PUBLIC/(n+'.json.gz') for n in reports],PUBLIC/'unit-tests.xml',
        ROOT/'docs/defense-older-quality-v24-result.md',ROOT/'docs/defense-older-quality-v24-player-review.md']
    write(PUBLIC/'final-review.json.gz',dict(source_integrity_pass=True,coverage_and_support_replayed=True,
        player_walkthrough_status='complete',main_review='All six source cases, three prospect origins and their 27 outcome-blind peers inspected, including metric disagreement, small stints, delayed arrivals and position changes.',
        model_fits=0,quality_labels_created=0,predictive_validation=False,deployment_approved=False,
        older_source_accepted_for_separate_research=True,older_native_splice_allowed=False,
        next_step='Audit raw skill versus position-relative value before a bridge or new quality learner.',
        full_defense_goal_complete=False,frozen_forecast_unchanged=True,no_2026_selection=True,
        previous_goal_turn='Lovich read-only diagnosis did not advance defense; this checkpoint adds verified older measurements and changes the next accounting action.',
        hashes={str(p):sha256_file(p) for p in paths}))
    print('Older source and player checkpoint complete. No predictive or deployment approval; defense goal active.',flush=True)


if __name__=='__main__':main()
