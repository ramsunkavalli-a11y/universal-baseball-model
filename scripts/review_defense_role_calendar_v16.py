"""Preserve fixed walkthrough selection; corrected calendar and source only."""
from pathlib import Path
import json
import review_defense_role_population_v16 as original
import repair_defense_role_calendar_v16 as current
from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections


def main():
    protections()
    original.DEST=current.DEST;original.write=current.write
    # The old review's duplicate publication loop has an explicit PUBLIC root.
    original.PUBLIC=current.PUBLIC
    # Keep its extra publication path inside the new sibling, never overwrite
    # the original public scope-repair walkthrough.
    (current.PUBLIC/'scope-repair').mkdir(parents=True,exist_ok=True)
    original.main()
    (current.PUBLIC/'player-walkthrough.md').write_bytes(
        (current.DEST/'player-walkthrough.md').read_bytes())
    # Preserve both old numerical walks; only this sibling gets the final read.
    current.write('calendar-walkthrough-receipt.json',dict(
        runner_sha256=sha256_file(Path(__file__)),
        original_review_sha256=sha256_file(Path(original.__file__)),
        corrected_walkthrough_sha256=sha256_file(current.DEST/'player-walkthrough.json'),
        corrected_bounds_sha256=sha256_file(current.DEST/'current-role-period-bounds.parquet'),
        no_fits=True,player_walkthrough_status='pending_manual_read'))
    protections()


if __name__=='__main__':main()
