"""Seal source calibration and actual support before any minor forecast fit."""
import json
from pathlib import Path
import numpy as np
import polars as pl
from universal_baseball.forecast_validation import preflight
from universal_baseball.hitter_minor_statcast_forecast import (
    LEAGUES, METRICS, best_half, materialize, route, feature_names, support_tags,
)
from universal_baseball.hitter_talent_bridge import SCOUT_FEATURES, PROFILE_FEATURES
from universal_baseball.storage import sha256_file
from prepare_practical_hitter_v33 import safe_matrix
import prepare_hitter_statcast_next_year as mlb

ROOT = mlb.ROOT
OUT = ROOT/'reports/generated/hitter-minor-statcast-next-year'
SOURCE = ROOT/'reports/generated/hitter-minor-statcast-reviewed-source'
BRIDGE = ROOT/'reports/generated/hitter-talent-bridge-v74'
CONTRACT = ROOT/'docs/hitter-minor-statcast-next-year-contract.md'


def read(p):
    return json.loads(Path(p).read_text(encoding='utf8'))


def write(name, value):
    p = OUT/name
    assert not p.exists(), f'Preserve {p}'
    p.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False,
                           default=str)+'\n', encoding='utf8', newline='\n')


def verify_hashes(mapping):
    for p, h in mapping.items():
        assert sha256_file(Path(p)) == h, p


def main():
    assert not (OUT/'preflight.json').exists(), 'Preserve completed preparation'
    allowed = {'annual-launch-features.parquet','anchor.parquet','prefit-development-errors.json'}
    allowed |= {f'{stem}-{k}.{ext}' for k in range(5) for stem,ext in [('features','parquet'),('calibration','json')]}
    assert not OUT.exists() or all(p.name in allowed for p in OUT.iterdir()), 'Unexpected partial preparation'
    source_review = read(SOURCE/'final-review.json')
    assert source_review['qualified_source_approved_for_bounded_experiment']
    assert source_review['player_walkthrough_status'] == 'complete'
    verify_hashes(source_review['artifact_hashes'])
    mlb_review = read(mlb.OUT/'final-review.json')
    assert mlb_review['player_walkthrough_status'] == 'complete'
    verify_hashes(mlb_review['artifact_hashes'])
    bridge_review = read(BRIDGE/'report.json')
    assert bridge_review['player_walkthrough_status'] == 'complete'
    for group in ['input_hashes','output_hashes','evidence_hashes','local_fit_hashes']:
        verify_hashes(bridge_review.get(group,{}))
    bridge_pre = read(BRIDGE/'preflight.json'); verify_hashes(bridge_pre['input_hashes'])
    OUT.mkdir(parents=True,exist_ok=True)
    annual = pl.read_parquet(SOURCE/'annual-launch-features.parquet')
    best = []
    for year in range(2021, 2025):
        q = pl.read_parquet(SOURCE/f'launch-events-{year}.parquet').filter(pl.col('valid_ev'))
        for group in q.group_by('player_id', 'season', 'league_id').agg(pl.col('launch_speed')).iter_rows(named=True):
            values = group.pop('launch_speed')
            best.append(dict(**group, best_half_ev=best_half(values), checked_ev_n=len(values)))
    a = annual.join(pl.DataFrame(best), on=['player_id','season','league_id'], how='left', validate='1:1')
    assert a.select((pl.col('checked_ev_n').fill_null(0) == pl.col('measured_ev_contacts')).all()).item()
    if (OUT/'annual-launch-features.parquet').exists():
        assert pl.read_parquet(OUT/'annual-launch-features.parquet').sort('player_id','season','league_id').equals(a.sort('player_id','season','league_id'))
    else:
        a.write_parquet(OUT/'annual-launch-features.parquet')
    base = pl.read_parquet(mlb.OUT/'features.parquet').sort('row_id')
    anchor = pl.read_parquet(mlb.OUT/'scored-predictions.parquet').sort('row_id')
    b = pl.read_parquet(BRIDGE/'scored-predictions.parquet').sort('row_id')
    assert anchor['row_id'].equals(b['row_id']) and len(anchor) == 30506
    assert anchor['preseason_pa'].equals(b['preseason_pa'])
    fallback = np.where(anchor['prior_debut'].to_numpy() == 0,
                        b['translated_ridge_rate'].to_numpy(), anchor['ridge_measurements_rate'].to_numpy())
    anchor = anchor.with_columns(pl.Series('combined_rate', fallback))
    anchor = anchor.with_columns((pl.col('preseason_pa')*(pl.col('combined_rate')/600+pl.col('origin_replacement_rate'))).alias('combined_value'))
    if (OUT/'anchor.parquet').exists():
        assert pl.read_parquet(OUT/'anchor.parquet').equals(anchor)
    else:
        anchor.write_parquet(OUT/'anchor.parquet')
    original = read(ROOT/'reports/generated/practical-hitter-numeric-repair-v53/preflight.json')['rate_features']
    core = original + SCOUT_FEATURES + PROFILE_FEATURES + mlb.read(mlb.OUT/'preflight.json')['control_features'] + mlb.read(mlb.OUT/'preflight.json')['measurement_features']
    coverage, measurements = feature_names()
    arms = dict(minor_coverage=core+coverage, minor_measurements=core+coverage+measurements)
    assert len(core) == 283 and len(set(arms['minor_measurements'])) == len(arms['minor_measurements'])
    assert not any(n.startswith('next_') for n in arms['minor_measurements'])
    calibration_paths = []
    for fold in range(5):
        prior = pl.read_parquet(BRIDGE/f'features-{fold}.parquet').sort('row_id')
        assert prior['row_id'].equals(base['row_id'])
        f = base.join(prior.select('row_id', *SCOUT_FEATURES, *PROFILE_FEATURES), on='row_id', validate='1:1')
        f, refs = materialize(f, a, fold)
        assert np.isfinite(safe_matrix(f, arms['minor_measurements'])).all()
        path = OUT/f'features-{fold}.parquet'
        if path.exists():
            assert pl.read_parquet(path).equals(f), 'Partial-cache feature difference'
            assert read(OUT/f'calibration-{fold}.json')['references'] == refs
            assert read(OUT/f'calibration-{fold}.json')['features_sha256'] == sha256_file(path)
        else:
            f.write_parquet(path)
            write(f'calibration-{fold}.json', dict(held_fold=fold, references=refs,
                source_seasons_only=True, future_labels_used=False, features_sha256=sha256_file(path)))
        calibration_paths += [path, OUT/f'calibration-{fold}.json']
        print(f'Fold {fold}: own-season, whole-held-player-excluded source references sealed.', flush=True)
    cells, supports, profiles, ranges = [], [], [], []
    keys = ['prior_debut','msc_age_band','msc_exposure_band','msc_sample_band','msc_rank_band']
    for c in mlb.read(mlb.OUT/'preflight.json')['cells']:
        y, k = c['year'], c['fold']
        f = pl.read_parquet(OUT/f'features-{k}.parquet')
        train, test, context, disabled = route(f, c['training_row_ids'], c['test_row_ids'])
        assert train['target_year'].max() <= y and not set(train['player_id']) & set(test['player_id'])
        expected = anchor.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
        assert test['row_id'].equals(expected['row_id'])
        sup, note = preflight(train, test, cutoff=y, fold=k, features=arms['minor_measurements'],
                              expected_keys=test.select('row_id','horizon').iter_rows())
        supports.append(sup.with_columns(pl.lit(y).alias('msc_origin'),pl.lit(k).alias('msc_fold')))
        tr, te = support_tags(train), support_tags(test)
        for league in LEAGUES:
            counts = tr.filter(pl.col(f'msc_{league}_ev_n')>0).group_by(keys).agg(pl.col('player_id').n_unique().alias('profile_people'))
            p = te.filter(pl.col(f'msc_{league}_ev_n')>0).select('row_id','msc_eligible',*keys).join(counts,on=keys,how='left',validate='m:1')
            profiles.append(p.with_columns(pl.col('profile_people').fill_null(0), pl.lit(league).alias('league_id'),
                                           pl.lit(y).alias('origin'),pl.lit(k).alias('fold')))
        x, tx = safe_matrix(train, coverage+measurements), safe_matrix(test, coverage+measurements)
        for j, n in enumerate(coverage+measurements):
            ranges.append(dict(origin=y,fold=k,feature=n,disabled=n in disabled,
                train_min=float(x[:,j].min()),train_max=float(x[:,j].max()),
                outside=int(((tx[:,j]<x[:,j].min())|(tx[:,j]>x[:,j].max())).sum())))
        cells.append(dict(year=y,fold=k,training_row_ids=c['training_row_ids'],test_row_ids=c['test_row_ids'],
            rate_preflight=note,league_context=context,disabled_features=disabled,
            eligible_test_rows=int(test['msc_eligible'].sum()),
            own_tracked_test_rows=int((test['msc_own_ev_n']>0).sum())))
    pl.concat(supports).write_parquet(OUT/'support.parquet')
    pl.concat(profiles).write_parquet(OUT/'profile-support.parquet')
    write('feature-ranges.json',dict(ranges=ranges))
    paths = [CONTRACT, Path(__file__), ROOT/'src/universal_baseball/hitter_minor_statcast_forecast.py',
        ROOT/'tests/test_hitter_minor_statcast_forecast.py',SOURCE/'final-review.json',SOURCE/'annual-launch-features.parquet',
        BRIDGE/'preflight.json',BRIDGE/'report.json',BRIDGE/'verification.json',BRIDGE/'scored-predictions.parquet',
        mlb.OUT/'preflight.json',mlb.OUT/'final-review.json',mlb.OUT/'features.parquet',mlb.OUT/'scored-predictions.parquet',
        ROOT/'scripts/fit_hitter_minor_statcast_next_year.py',ROOT/'scripts/prepare_practical_hitter_v33.py',
        ROOT/'scripts/fit_practical_hitter_v31.py',ROOT/'src/universal_baseball/post_arrival_history.py',
        ROOT/'src/universal_baseball/forecast_validation.py',OUT/'anchor.parquet',OUT/'annual-launch-features.parquet',
        OUT/'support.parquet',OUT/'profile-support.parquet',OUT/'feature-ranges.json',*calibration_paths]
    paths += [SOURCE/f'launch-events-{y}.parquet' for y in range(2021,2025)]
    paths += [BRIDGE/f'features-{k}.parquet' for k in range(5)]
    write('preflight.json',dict(before_fitting=True,arms=arms,core_features=core,coverage_features=coverage,
        measurement_features=measurements,cells=cells,ridge_alpha=100,minimum_context_people=20,
        forecasts=30506,source_rows=63282,all_forecasts_retained=True,protected_outcomes_used=False,
        provider_original_vintage_known=False,full_profile_validation=False,deployment_approved=False,
        input_hashes={str(p):sha256_file(p) for p in paths}))
    print('Prefit sealed:',len(cells),'cells;',sum(c['eligible_test_rows'] for c in cells),'eligible minor forecasts; no fits.')


if __name__ == '__main__':
    main()
