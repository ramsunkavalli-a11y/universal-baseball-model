"""Post-review readback and test receipt; no source/result overwrites."""
from pathlib import Path
import re
import subprocess
import sys
import json

import repair_defense_role_calendar_v16 as current
from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections


def main():
    protections();out=current.DEST
    final=json.loads((out/'final-review.json').read_text(encoding='utf8'))
    for path,digest in final['input_hashes'].items():assert sha256_file(Path(path))==digest,path
    source=json.loads((out/'source-review.json').read_text(encoding='utf8'))
    for field in ('input_hashes','output_hashes'):
        for path,digest in source[field].items():assert sha256_file(Path(path))==digest,path
    walk_lines=len((out/'player-walkthrough.md').read_text(encoding='utf8').splitlines())
    assert walk_lines==684 and final['player_walkthrough_status']=='complete'
    tests=['tests/test_defense_role_calendar.py','tests/test_defense_role_scope.py',
        'tests/test_defense_role_logs.py','tests/test_defense_budget_source.py',
        'tests/test_defense_jobs.py','tests/test_defense_repertoire.py',
        'tests/test_defense_value.py','tests/test_defense_opportunity_bridge.py']
    command=[sys.executable,'-X','utf8','-m','pytest',*tests,'-q','-p','no:cacheprovider']
    run=subprocess.run(command,cwd=current.ROOT,capture_output=True,text=True,encoding='utf8')
    assert run.returncode==0,run.stdout+run.stderr
    count=re.search(r'(\d+) passed',run.stdout);assert count and int(count.group(1))==57
    current.write('readback-review.json',dict(source_integrity='pass',player_walkthrough_status='complete',
        review_lines=walk_lines,
        clerical_correction='The preserved final-review manual_reviewer description says 695 lines; the complete review is 684 lines. Case membership, review and source results are unchanged.',
        tests_passed=57,test_command=command,test_stdout=run.stdout,test_stderr=run.stderr,
        final_receipt_sha256=sha256_file(out/'final-review.json'),
        readback_sha256=sha256_file(Path(__file__)),no_fits=True,no_accuracy_claim=True,no_deployment=True))
    protections();print('Readback verified source/result hashes, all 684 review lines, fixed case membership and 57 tests.',flush=True)


if __name__=='__main__':main()
