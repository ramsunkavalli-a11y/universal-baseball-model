"""Verify experiment hashes, raw fits, calibration chronology and scored counts."""
import json
from pathlib import Path
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from fit_hitter_history_calibration_v1 import OUT, PACKAGE, MAIN, RAW, assemble, verify_prefit
from universal_baseball.hitter_detail_arrival import TARGETS, eligible, target_values
from universal_baseball.hitter_history_calibration import calibrate
from universal_baseball.storage import sha256_file
from score_hitter_detail_arrival_v1 import metrics


def main():
    meta = json.loads((PACKAGE/'manifest.json').read_text())
    for n,h in meta['files'].items(): assert sha256_file(PACKAGE/n) == h
    for n,h in meta['report_code'].items(): assert sha256_file(Path(n)) == h
    pre = json.loads((PACKAGE/'prefit-manifest.json').read_text())
    verify_prefit(pre)
    fit = json.loads((PACKAGE/'fit-manifest.json').read_text())
    assert fit['prefit_sha256'] == sha256_file(PACKAGE/'prefit-manifest.json')
    for n,h in fit['files'].items(): assert sha256_file(PACKAGE/n) == h
    panel, arms = assemble(); assert arms == pre['arms']
    raw = pl.read_parquet(PACKAGE/'raw-predictions.parquet')
    predictions = pl.read_parquet(PACKAGE/'predictions.parquet')
    for f in (raw, predictions):
        assert not f.select('origin_year','player_id','target','arm').is_duplicated().any()
        assert f['probability'].is_finite().all() and f['probability'].min() > 0 and f['probability'].max() < 1
    for target, years in RAW.items():
        for year in years:
            train = eligible(panel, year, target)
            test = panel.filter(pl.col('origin_year') == year)
            assert train['origin_year'].max()+TARGETS[target] <= year
            np.testing.assert_allclose(train.group_by('player_id').agg(pl.col('identity_weight').sum())['identity_weight'],1)
            for arm in arms:
                f = raw.filter((pl.col('target') == target) & (pl.col('origin_year') == year) & (pl.col('arm') == arm))
                np.testing.assert_array_equal(f['player_id'], test['player_id'])
                np.testing.assert_array_equal(f['actual'], target_values(test, target))
    for n in fit['calibrators']:
        target, year, arm = n['target'], n['year'], n['arm']
        history = raw.filter((pl.col('target') == target) & (pl.col('arm') == arm))
        current = history.filter(pl.col('origin_year') == year)
        p, note = calibrate(history, current, year, target)
        expected = predictions.filter((pl.col('target') == target) & (pl.col('origin_year') == year) & (pl.col('arm') == arm+'C'))
        np.testing.assert_allclose(p, expected['probability'], rtol=0, atol=1e-12)
        for k,v in note.items():
            if isinstance(v, float): np.testing.assert_allclose(n[k], v, rtol=1e-12, atol=1e-12)
            else: assert n[k] == v
        assert n['latest_label'] <= year
    assert fit['future_mutation_maximum_difference'] == 0
    scores = json.loads((PACKAGE/'score-report.json').read_text())
    for target,r in scores['targets'].items():
        if TARGETS[target] == 3: assert not r['gates']['support']
        for arm in ('R','RC','H','HC'):
            f = predictions.filter((pl.col('target') == target) & ~pl.col('pandemic') & pl.col('prospect') & (pl.col('arm') == arm))
            assert sorted(f['origin_year'].unique().to_list()) == list(MAIN[target])
            measured = metrics(f)
            for k in ('rows','players','observed','expected','brier','log_loss'):
                np.testing.assert_allclose(measured[k],r['prospects'][arm][k],rtol=1e-12,atol=1e-12)
    print(json.dumps({'verified': True, 'raw_folds':len(fit['fits']), 'prediction_rows':predictions.height,
                      'protected_outcomes_used':False, 'production_forecasts_changed':False}))


if __name__ == '__main__':
    with threadpool_limits(limits=4): main()
