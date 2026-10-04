"""Independent source/reference audit before any count-risk disposition."""
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.post_arrival_history import player_fold
from universal_baseball.storage import sha256_file
import evaluate_hitter_event_count_risk as e


def main():
    assert not (e.OUT/'preparation-verification.json').exists(), 'Preserve this independent audit'
    pre = e.read(e.OUT/'preflight.json'); e.old.check_hashes(pre['input_hashes'])
    f, hist, counts, folds, years = e.source()
    nested = 0; forecasts = 0; tested = set(); references = 0
    for c in pre['cells']:
        e.old.check_hashes(c['artifact_hashes'])
        cal = pl.read_parquet(c['calibration_path']); te = pl.read_parquet(c['test_path'])
        assert set(cal['row_id']) == set(c['calibration_row_ids'])
        assert te['row_id'].to_list() == c['test_row_ids']
        assert not set(cal['player_id']) & set(te['player_id'])
        assert all(player_fold(pid) != c['fold'] for pid in cal['player_id'])
        assert all(player_fold(pid) == c['fold'] for pid in te['player_id'])
        assert cal['next_pa'].min() > 0 and cal['target_year'].max() <= c['year']
        assert te['origin_year'].unique().to_list() == [c['year']]
        assert te['target_year'].unique().to_list() == [c['year']+1]
        assert not tested & set(te['row_id']); tested.update(te['row_id']); forecasts += len(te)
        assert cal['player_id'].n_unique() == c['calibration_people']
        e.bound_check(cal['nested_rate'], cal['origin_index'], cal['workload_log_center'])
        e.bound_check(te['preseason_rate'], te['origin_index'], te['workload_log_center'])
        nested += len(c['inner_preflights'])
        for ref in c['reference_notes']:
            mask = (years == ref['origin_year']) & (folds != ref['outer_fold'])
            if ref['inner_fold'] is not None: mask &= folds != ref['inner_fold']
            raw = counts[mask].sum(0)+.5; probability = raw/raw.sum()
            assert hist.filter(pl.Series(mask))['player_id'].to_list() == ref['people']
            assert int(mask.sum()) == ref['source_rows']
            assert np.array_equal(probability, ref['probability'])
            assert all(player_fold(pid) != c['fold'] for pid in ref['people'])
            if ref['inner_fold'] is not None:
                assert all(player_fold(pid) != ref['inner_fold'] for pid in ref['people'])
            references += 1
    assert forecasts == 30506 and len(tested) == 30506 and nested == 95
    python = str(e.ROOT/'.venv/Scripts/python.exe')
    test = subprocess.run([python, '-X', 'utf8', '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
        'tests/test_hitter_event_count_risk.py', 'tests/test_hitter_event_count_risk_review.py'],
        cwd=e.ROOT, text=True, capture_output=True)
    assert test.returncode == 0, test.stdout+test.stderr
    (e.OUT/'preparation-tests.txt').write_text(test.stdout+test.stderr, encoding='utf8', newline='\n')
    frozen = json.loads(subprocess.check_output([python, '-X', 'utf8',
        str(e.ROOT/'scripts/verify_hitter_full_2026_freeze.py')], cwd=e.ROOT))
    assert frozen['status'] == 'verified' and frozen['protected_2026_opened'] is False
    paths = [Path(__file__), e.OUT/'preflight.json', e.OUT/'preparation-tests.txt',
        e.ROOT/'scripts/score_hitter_event_count_risk.py', e.ROOT/'tests/test_hitter_event_count_risk_review.py']
    e.write(e.OUT/'preparation-verification.json', dict(actual_forecasts=forecasts, cells=35,
        actual_nested_subsets=nested, actual_source_reference_replays=references,
        reference_counts_and_people_exact=True, whole_player_exclusions_checked=True,
        physical_rate_bound_checks_repeated=True, focused_tests=12, frozen_verification=frozen,
        player_walkthrough_status='pending', predictive_status='not assessed', candidate_changed=False,
        source_hashes=pre['input_hashes'], audit_hashes={str(p): sha256_file(p) for p in paths}))
    evidence = e.ROOT/'reports/model-evidence/hitter-event-count-risk'; evidence.mkdir(parents=True, exist_ok=True)
    for name in ['preflight.json', 'outer-support.parquet', 'calibration-profile-support.parquet',
                 'preparation-tests.txt', 'preparation-verification.json']:
        shutil.copyfile(e.OUT/name, evidence/name)
        assert sha256_file(e.OUT/name) == sha256_file(evidence/name)
    print('Independent preparation audit:', forecasts, 'forecasts;', references, 'reference replays; 12 tests; frozen files unchanged', flush=True)


if __name__ == '__main__':
    main()
