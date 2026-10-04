"""Correct the public selector without changing the sealed fit runner."""
import hashlib
import inspect
from pathlib import Path

import evaluate_hitter_available_season_history as run
from prepare_hitter_extended_training import verify
from universal_baseball.storage import sha256_file


def main():
    # The sealed runner referenced zips_pa, which this anchor does not contain.
    # It failed before any scoring artifacts were saved. Apply precisely the
    # existing declared 2,627-player selector, keeping every other instruction.
    pre = run.read(run.OUT/'preflight.json')
    verify(pre['input_hashes'])
    assert not (run.OUT/'verification.json').exists()
    old = inspect.getsource(run.scoring)
    bad = "public = q.filter(pl.col('steamer_pa').is_not_null()&pl.col('zips_pa').is_not_null())"
    correct = "public = q.filter((pl.col('pa_0')>0)&pl.col('steamer_index').is_not_null()&pl.col('zips_index').is_not_null())"
    assert old.count(bad)==1
    fixed = old.replace(bad,correct)
    run.write('scoring-repair.json',dict(before_successful_scoring=True,fits_and_forecasts_changed=False,
        reason='Absent zips_pa field; use the previously declared current-MLB/two-public-system matched sample',
        old_instruction=bad,new_instruction=correct,expected_public_rows=2627,
        old_function_sha256=hashlib.sha256(old.encode()).hexdigest(),new_function_sha256=hashlib.sha256(fixed.encode()).hexdigest(),
        hashes={str(Path(run.__file__)):sha256_file(Path(run.__file__)),str(Path(__file__)):sha256_file(Path(__file__))}))
    namespace = dict(run.__dict__)
    exec(compile(fixed,str(Path(__file__))+'::corrected_scoring','exec'),namespace)
    namespace['scoring']()


if __name__=='__main__':
    main()
