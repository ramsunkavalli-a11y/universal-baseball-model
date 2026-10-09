"""Reuse the sealed comparison runner with a separately sealed fallback repair."""
from pathlib import Path
import test_hitter_2027_role_budget as runner
from universal_baseball import hitter_role_fallback_v1 as repaired
from universal_baseball.storage import sha256_file
from capture_hitter_2027_origin_counts import ROOT,write_once


def main():
    runner.PUBLIC=ROOT/'reports/model-evidence/hitter-2027-v1/role-fallback-repair'
    runner.OUT=ROOT/'reports/generated/hitter-2027-base/role-fallback-repair'
    runner.PUBLIC.mkdir(parents=True,exist_ok=True);runner.OUT.mkdir(parents=True,exist_ok=True)
    paths=[Path(__file__),Path(runner.__file__),ROOT/'src/universal_baseball/hitter_role_fallback_v1.py',
           ROOT/'docs/hitter-2027-role-fallback-repair.md',ROOT/'docs/hitter-2027-joint-role-result.md']
    write_once(runner.PUBLIC/'repair-execution-seal.json',dict(before_fitting=True,
        prior_player_review='complete',single_changed_mechanism='fallback exposure pooling, not normalized tiny-stint replacement',
        input_hashes={str(p):sha256_file(p) for p in paths}))
    runner.joint=repaired
    runner.main()


if __name__=='__main__':main()
