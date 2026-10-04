"""Save actual outer and nested player/chronology support before any risk fits."""
import json
from pathlib import Path
import polars as pl
from universal_baseball.forecast_validation import preflight
from universal_baseball.storage import sha256_file
import evaluate_hitter_preseason_readiness_v68 as current

ROOT = current.ROOT
OUT = ROOT / 'reports/generated/hitter-workload-risk'


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def nested_rows(outer_training, outer_fold, inner_origin):
    inner_fold = (outer_fold + 1) % 5
    assert not outer_training.filter(pl.col('outer_fold') == outer_fold).height
    validation = outer_training.filter((pl.col('origin_year') == inner_origin) & (pl.col('outer_fold') == inner_fold))
    train = outer_training.filter((pl.col('target_year') <= inner_origin) &
        (pl.col('target_year') != 2020) & (pl.col('outer_fold') != inner_fold) & (pl.col('next_pa') > 0))
    assert not set(train['player_id']) & set(validation['player_id'])
    return train.sort('row_id'), validation.sort('row_id'), inner_fold


def profiles(train, test, label, outer_year, outer_fold, inner_origin=None):
    keys = ['prior_debut', 'stage', 'age_band', 'rank_band', 'new_draftee', 'thin_pro']
    counts = current.tagged(train).group_by(keys).agg(pl.col('player_id').n_unique().alias('profile_people'))
    return current.tagged(test).select('row_id', *keys).join(counts, on=keys, how='left', validate='m:1').with_columns(
        pl.col('profile_people').fill_null(0), pl.lit(label).alias('scope'), pl.lit(outer_year).alias('outer_year'),
        pl.lit(outer_fold).alias('outer_fold'), pl.lit(inner_origin, dtype=pl.Int64).alias('inner_origin'))


def main():
    assert not (OUT / 'preflight.json').exists(), 'Preserve existing preflight'
    handoff = read(ROOT / 'reports/generated/hitter-qualified-handoff/final-report.json')
    assert handoff['browser_verification'] == 'complete'
    for key in ['input_hashes', 'output_hashes', 'result_hashes']:
        for p, h in handoff.get(key, {}).items():
            assert sha256_file(Path(p)) == h, p
    previous = read(current.OUT / 'preflight.json')
    for p, h in previous['input_hashes'].items():
        assert sha256_file(Path(p)) == h, p
    f = pl.read_parquet(current.OUT / 'features.parquet')
    q = pl.read_parquet(current.OUT / 'scored-predictions.parquet')
    forest_path = ROOT / 'reports/generated/practical-hitter-joint-forest-v43/predictions.parquet'
    forest = pl.read_parquet(forest_path)
    assert len(q) == len(forest) == 30506
    assert q.sort('row_id')['row_id'].equals(forest.sort('row_id')['row_id'])
    assert f['next_pa'].max() <= 800 and f['next_pa'].min() >= 0
    assert f.select('player_id','outer_fold').unique().group_by('player_id').len()['len'].max() == 1
    dates = read(current.SOURCE / 'source-report.json')['release_evidence']
    names = previous['pa_features']
    cells, support, refined, memberships = [], [], [], []
    for c in previous['cells']:
        y, k = c['year'], c['fold']
        outer_train = f.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id')
        test = f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
        active = outer_train.filter(pl.col('next_pa') > 0)
        s, note = preflight(active, test, cutoff=y, fold=k, features=names,
            expected_keys=test.select('row_id','horizon').iter_rows())
        support.append(s.with_columns(pl.lit(y).alias('outer_year'),pl.lit(k).alias('outer_fold'),pl.lit('outer').alias('scope')))
        refined.append(profiles(active, test, 'outer', y, k))
        nested, empty, calibration_ids = [], [], []
        for origin in range(y - 3, y):
            tr, val, j = nested_rows(outer_train, k, origin)
            if val.is_empty():
                empty.append(dict(inner_origin=origin, reason='No eligible outer-training validation rows; excluded target 2020 or unavailable origin'))
                continue
            assert not tr.is_empty(), 'An empty nested training set needs a pre-fit amendment'
            assert not set(test['player_id']) & (set(tr['player_id']) | set(val['player_id']))
            assert max(dates[str(t)]['date'] for t in tr['target_year'].unique()) < dates[str(origin+1)]['date']
            s, inner_note = preflight(tr, val, cutoff=origin, fold=j, features=names,
                expected_keys=val.select('row_id','horizon').iter_rows())
            support.append(s.with_columns(pl.lit(y).alias('outer_year'),pl.lit(k).alias('outer_fold'),pl.lit('inner').alias('scope')))
            refined.append(profiles(tr, val, 'inner', y, k, origin))
            validation_active = val.filter(pl.col('next_pa') > 0)
            calibration_ids.extend(validation_active['row_id'].to_list())
            nested.append(dict(origin=origin,inner_fold=j,information_date=dates[str(origin+1)]['date'],
                training_row_ids=tr['row_id'].to_list(),validation_row_ids=val['row_id'].to_list(),
                calibration_row_ids=validation_active['row_id'].to_list(),preflight=inner_note,
                active_validation_rows=len(validation_active),active_validation_people=validation_active['player_id'].n_unique()))
            memberships.extend(dict(outer_year=y,outer_fold=k,inner_origin=origin,row_id=r,kind='calibration') for r in validation_active['row_id'])
        calibration = f.filter(pl.col('row_id').is_in(calibration_ids))
        assert len(calibration_ids) == len(set(calibration_ids)) == len(calibration)
        assert len(calibration) > 0, 'No dispersion support; declare fallback before fits'
        assert not set(calibration['player_id']) & set(test['player_id'])
        cells.append(dict(year=y,fold=k,information_date=c['information_date'],test_row_ids=c['test_row_ids'],
            outer_preflight=note,nested=nested,empty_inner_origins=empty,calibration_row_ids=calibration_ids,
            calibration_rows=len(calibration),calibration_people=calibration['player_id'].n_unique(),
            max_calibration_target=int(calibration['target_year'].max())))
    OUT.mkdir(parents=True,exist_ok=True)
    pl.concat(support,how='diagonal_relaxed').write_parquet(OUT/'support.parquet')
    pl.concat(refined,how='diagonal_relaxed').write_parquet(OUT/'profile-support.parquet')
    pl.DataFrame(memberships).write_parquet(OUT/'calibration-memberships.parquet')
    paths=[Path(__file__),ROOT/'docs/hitter-workload-risk-contract.md',current.OUT/'preflight.json',current.OUT/'features.parquet',
        current.OUT/'scored-predictions.parquet',current.SOURCE/'source-report.json',forest_path,
        ROOT/'reports/generated/hitter-qualified-handoff/final-report.json',ROOT/'src/universal_baseball/forecast_validation.py',
        ROOT/'scripts/evaluate_hitter_preseason_readiness_v68.py',ROOT/'scripts/fit_practical_hitter_v31.py',
        OUT/'support.parquet',OUT/'profile-support.parquet',OUT/'calibration-memberships.parquet']
    receipt=dict(before_fitting=True,new_fits=0,features=names,conditional_settings=previous['settings'],cells=cells,
        fixed_test_rows=30506,outer_cells=len(cells),nested_heads=sum(len(c['nested']) for c in cells),
        minimum_calibration_people=min(c['calibration_people'] for c in cells),
        maximum_target_pa=int(f['next_pa'].max()),outer_players_excluded_from_every_nested_fit_and_calibration=True,
        input_hashes={str(p):sha256_file(p) for p in paths},protected_outcomes_used=False,
        player_walkthrough_status='pending',predictive_validation='not_run')
    (OUT/'preflight.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:receipt[k] for k in ['new_fits','fixed_test_rows','outer_cells','nested_heads','minimum_calibration_people','maximum_target_pa']}),flush=True)


if __name__ == '__main__':
    main()
