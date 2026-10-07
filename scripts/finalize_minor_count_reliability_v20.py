"""Reviewed source milestone, explicitly not completion of the defense goal."""
from pathlib import Path
import gzip
import json
import subprocess

from minor_count_archive_access_v20 import digest,main as verify_archive
from run_hitter_finite_return_baseline import protections
from universal_baseball.storage import sha256_file

ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/'reports/model-evidence/defense-count-reliability-v20'


def read(p):
    with gzip.open(p,'rt',encoding='utf8') as f:return json.load(f)


def main():
    protections();paths=[]
    for name in ('preflight','summary','independent-review','player-walkthrough','player-walkthrough-replayed'):
        p=PUBLIC/f'{name}.json.gz';record=read(p);paths.append(p)
        for path,h in record['hashes'].items():assert digest(Path(path))==h,path
    initial=read(PUBLIC/'player-walkthrough.json.gz');replayed=read(PUBLIC/'player-walkthrough-replayed.json.gz')
    for key in ('selection_manifest','peers','walks','people'):assert initial[key]==replayed[key],key
    assert replayed['model_refits']==0 and replayed['storage_replay_of_sealed_player_trace']
    summary=read(PUBLIC/'summary.json.gz');assert summary['source_screen_pass']
    verify_archive(False)
    command=[str(ROOT/'.venv/Scripts/python.exe'),'-X','utf8','-m','pytest',
             'tests/test_minor_count_reliability.py','tests/test_minor_range_talent.py','tests/test_minor_fielding_counts.py',
             '-q','-p','no:cacheprovider']
    result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf8')
    assert result.returncode==0 and '47 passed' in result.stdout,(result.stdout,result.stderr)
    paths.extend([Path(__file__),ROOT/'scripts/minor_count_archive_access_v20.py',ROOT/'scripts/replay_minor_count_players_v20.py',
        ROOT/'docs/defense-count-reliability-v20-result.md',ROOT/'docs/defense-count-reliability-v20-contract.md',
        PUBLIC/'reference-fits.zip',PUBLIC/'archive-index.json.gz'])
    path=PUBLIC/'final-review.json.gz';assert not path.exists()
    with gzip.open(path,'wt',encoding='utf8') as f:
        json.dump(dict(status='reviewed_count_calibration_recipe_not_MLB_talent',player_walkthrough_status='complete',
            focal_cases=9,peer_comparisons=27,distinct_player_origins=36,forecast_records_replayed=73069,
            reference_groups_replayed=5352,source_screen_pass=True,statistical_reasonability='pass_with_stated_scope',
            source_recipe_retained=True,future_MLB_quality_improvement_established=False,defense_goal_complete=False,
            model_deployment_approved=False,model_refits_for_storage_replay=0,no_2026_outcomes=True,forecast_unchanged=True,
            previous_goal_turn='No defense progress: read-only Lovich batting diagnosis. This turn repairs and tests the defense input calculation.',
            unit_test_command=command,unit_test_output=result.stdout.strip(),
            remaining=['Separately supported minor-count correction for later MLB quality with protected baseline',
                       'Throwing, receiving, double plays, catcher and position-transfer quality',
                       'Lower-minor mature talent paths and delivered-value integration',
                       'Separate Lovich batting defect'],
            hashes={str(p):sha256_file(p) for p in paths}),f,allow_nan=False,separators=(',',':'))
    protections();print(dict(milestone='reviewed source reliability',defense_goal_complete=False,tests=result.stdout.strip()))


if __name__=='__main__':main()
