"""Close the manually reviewed source checkpoint, never the defense goal."""
from pathlib import Path
import re
import subprocess
import sys

from capture_defense_role_v15 import ROOT, OUT, read, receipt
from audit_defense_role_v15 import source_check_seal
from run_hitter_finite_return_baseline import protections
from universal_baseball.storage import sha256_file


def main():
    protections(); source_check_seal()
    assert not (OUT/'final-review.json').exists()
    source=read(OUT/'source-review.json');verify=read(OUT/'independent-verification.json')
    walk=read(OUT/'player-walkthrough.json')
    assert verify['source_integrity']=='pass' and source['verified_scopes']==114
    assert source['unknown_scopes']==[] and source['unknown_cases']==[]
    assert walk['focal_cases']==19 and walk['peer_records']==57 and walk['total_old_records']==76
    assert len(walk['additional_source_contrasts'])==5
    for item in [source,verify,walk,read(OUT/'pbp-inventory.json')]:
        for path,expected in item['hashes'].items():assert sha256_file(Path(path))==expected,path
    tests=['test_defense_role_logs.py','test_defense_jobs.py','test_defense_budget_source.py',
           'test_defense_value.py','test_defense_value_source.py','test_defense_repertoire.py',
           'test_defense_transition.py','test_defense_transition_scores.py',
           'test_defense_opportunity_bridge.py','test_position_role_source.py']
    command=[sys.executable,'-X','utf8','-m','pytest',*[f'tests/{t}' for t in tests],'-q','-p','no:cacheprovider']
    result=subprocess.run(command,cwd=ROOT,encoding='utf8',capture_output=True,check=False)
    assert result.returncode==0,result.stdout+result.stderr
    match=re.search(r'(\d+) passed',result.stdout);assert match and int(match[1])==74
    receipt('test-review.json',dict(command=command,exit_code=result.returncode,passed=74,
        stdout=result.stdout,stderr=result.stderr,qualification='Execution regression tests, not predictive improvement.'))
    files=[ROOT/'docs/defense-role-v15-source-contract.md',ROOT/'docs/defense-role-v15-scope-amendment.md',
        ROOT/'docs/defense-role-v15-result.md',ROOT/'src/universal_baseball/defense_role_logs.py',
        ROOT/'tests/test_defense_role_logs.py',Path(__file__),
        *[ROOT/'scripts'/name for name in ['capture_defense_role_v15.py','probe_defense_role_scope_v15.py',
           'audit_defense_role_v15.py','inventory_defense_role_pbp_v15.py','verify_defense_role_v15.py',
           'review_defense_role_v15.py']],
        *[OUT/name for name in ['capture-seal.json','scope-amendment-seal.json','probe-review.json',
           'source-seal.json','explicit-scope-manifest.json','source-review.json','pbp-inventory.json',
           'independent-verification.json','player-walkthrough.json','player-walkthrough.md','test-review.json',
           'verified-role-games.parquet','verified-role-periods.parquet','pbp-case-presence.parquet']],
        ROOT/'reports/generated/defense-jobs-v14/predictions.parquet',
        ROOT/'reports/generated/defense-jobs-v14/final-review.json']
    receipt('final-review.json',dict(source_integrity='pass_for_bounded_reviewed_scopes',
        player_walkthrough_status='complete',manual_review='Main agent read the entire 960-line source walkthrough, '
        'checked focal and peer dates/totals against saved period records, and documented current-use versus repertoire '
        'defects plus the cases where latest-use persistence would miss. Five added source contrasts retained.',
        reviewed_focal_cases=19,reviewed_peer_records=57,additional_source_contrasts=5,
        source_scopes=114,annual_position_totals=281,position_games=9396,period_cells=424,dated_DH_additions=51,
        test_count=74,new_fits=0,new_forecasts=0,predictive_improvement='not_tested',
        disposition='Retain verified dated source views. Reject ignored sport filtering and unusable date-range response. '
        'Certify population-wide current-assignment/full-repertoire features before the single role repair.',
        unresolved=['Source agreement uses one official provider, not independent boxscore validation of every game.',
            'Only bounded cases are certified; no full training/forecast population dated-source coverage claim.',
            'No role repair fitted; upcoming assignments, workload, sparse/minor quality and long horizons remain open.',
            'Terminal-PA fielder snapshots do not measure exact innings or DH starts.',
            'Separate Lovich small-sample batting defect remains unresolved.'],
        no_deployment=True,no_forecast_or_explorer_changes=True,no_2026_selection=True,
        overall_goal_still_active=True,hashes={str(p):sha256_file(p) for p in files}))
    protections();print('Reviewed source checkpoint sealed; 74 regression tests pass; no fit, forecast or deployment changes.',flush=True)


if __name__=='__main__':main()
