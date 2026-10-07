"""Record a reviewed, nonpromoted milestone without declaring the defense goal done."""
from pathlib import Path
import subprocess

from verify_minor_range_correction_v21 import ROOT,PUBLIC,read,write
from minor_range_archive_access_v21 import digest,check
from run_hitter_finite_return_baseline import protections
from universal_baseball.storage import sha256_file


def main():
    protections();paths=[]
    for name in ('preflight','sources-complete','resume-preflight','nuisance-tuning-preflight','fit-report','independent-review',
                 'player-walkthrough','player-walkthrough-supplement'):
        path=PUBLIC/f'{name}.json.gz';value=read(path);paths.append(path)
        for p,h in value['hashes'].items():assert digest(Path(p))==h,p
    check(False)
    first=read(PUBLIC/'player-walkthrough.json.gz');extra=read(PUBLIC/'player-walkthrough-supplement.json.gz')
    origins={tuple(w['identity'][:2]) for w in first['walks']+extra['walks']}
    positions={tuple(w['identity']) for w in first['walks']+extra['walks']}
    assert len(origins)==72 and len(positions)==202 and extra['all_changed_measured_forecasts_walked']
    report=read(PUBLIC/'fit-report.json.gz');assert report['screen_failed_checks']==['no_supported_primary_RMSE_gain']
    command=[str(ROOT/'.venv/Scripts/python.exe'),'-m','pytest','tests/test_minor_range_correction.py',
             'tests/test_nuisance_range_tuning.py','tests/test_minor_range_resume.py','tests/test_minor_count_reliability.py',
             'tests/test_minor_range_talent.py','tests/test_minor_fielding_counts.py','-q','-p','no:cacheprovider']
    result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf8')
    assert result.returncode==0,(result.stdout,result.stderr)
    paths.extend([Path(__file__),ROOT/'scripts/minor_range_archive_access_v21.py',PUBLIC/'archive-index.json.gz',PUBLIC/'execution-artifacts.zip',
        ROOT/'docs/defense-minor-correction-v21-result.md',ROOT/'tests/test_minor_range_resume.py'])
    write(PUBLIC/'final-review.json.gz',dict(status='reviewed_sparse_future_MLB_quality_correction_not_promoted',
        player_walkthrough_status='complete',initial_focal_selections=len(first['selection_manifest']),supplemental_focal_selections=len(extra['selections']),
        distinct_player_origins=len(origins),position_walks=len(positions),all_nine_changed_measured_forecasts_reviewed=True,
        baseline_exact_replay=True,source_groups_replayed=7519,forecasts_replayed=13133,statistical_screen_pass=False,
        predictive_claim='Small development gain concentrated in three primary people; interval includes zero',
        reasonability='Sparse-source extremes are prevented; young and lower-minor talent misses remain',
        model_deployment_approved=False,defense_goal_complete=False,no_2026_outcomes=True,forecast_unchanged=True,
        previous_goal_turn='No defense progress: read-only Lovich diagnosis; resumed the stopped fixed comparison and completed replay/player review now.',
        exact_archived_duplicate_prior_files_removed=7519,raw_data_and_old_work_preserved=True,
        remaining=['Double-play measurement and older comparable future-MLB quality support',
                   'Lower-minors talent, age/development and position movement',
                   'Delivered defense and full player value integration','Separate Lovich batting defect'],
        unit_test_command=command,unit_test_output=result.stdout.strip(),hashes={str(p):sha256_file(p) for p in paths}))
    protections();print(dict(milestone='Reviewed protected-baseline count correction; not promoted',tests=result.stdout.strip(),defense_goal_complete=False),flush=True)


if __name__=='__main__':main()
