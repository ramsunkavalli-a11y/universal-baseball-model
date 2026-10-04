"""First-stage cold-player talent generation, then one locked opportunity test."""
import sys
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from sklearn.linear_model import Ridge
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits
from universal_baseball.forecast_validation import preflight
from universal_baseball.storage import sha256_file
from fit_practical_hitter_v31 import weights
from prepare_practical_hitter_v33 import safe_matrix
import prepare_hitter_talent_opportunity as setup

ROOT, OUT = setup.ROOT, setup.OUT
read, write, verify = setup.read, setup.write, setup.verify
ARMS = {'coverage': ['talent_known'], 'talent': ['talent_known', 'talent_mlb_rate']}


def seal():
    pre = read(OUT/'preflight.json')
    verify(pre['input_hashes'])
    paths = [Path(__file__), OUT/'preflight.json']
    hashes = {str(p): sha256_file(p) for p in paths}
    if (OUT/'fit-seal.json').exists():
        assert read(OUT/'fit-seal.json') == hashes
    else:
        write('fit-seal.json', hashes)
    return pre


def features():
    assert not (OUT/'generation-report.json').exists(), 'Preserve generation result'
    pre = seal()
    f = pl.read_parquet(setup.current.OUT/'features.parquet').sort('row_id')
    anchor = pl.read_parquet(setup.current.OUT/'scored-predictions.parquet').sort('row_id')
    generated = {}; notes = []
    with threadpool_limits(limits=2):
        for g in pre['graphs']:
            path = OUT/(g['tag']+'.parquet'); npth = OUT/(g['tag']+'.json')
            val = f.filter(pl.col('row_id').is_in(g['validation_row_ids'])).sort('row_id')
            if path.exists():
                note = read(npth); verify(note['hashes'])
                assert note['preflight_sha256'] == sha256_file(OUT/'preflight.json')
            else:
                tr = f.filter(pl.col('row_id').is_in(g['training_row_ids'])).sort('row_id')
                assert not set(tr['player_id']) & set(val['player_id'])
                if g['estimated']:
                    model = Ridge(alpha=pre['ridge_alpha'])
                    w = weights(tr)*tr['next_pa'].to_numpy(); w *= len(w)/w.sum()
                    model.fit(safe_matrix(tr, pre['rate_features']), tr['next_batting_rate'].to_numpy(), sample_weight=w)
                    pred = model.predict(safe_matrix(val, pre['rate_features']))
                    assert np.isfinite(pred).all()
                    mp = OUT/(g['tag']+'.joblib'); joblib.dump(model, mp, compress=3)
                    hashes = {str(mp):sha256_file(mp)}
                else:
                    pred = np.zeros(len(val)); hashes = {}
                result = val.select('row_id', 'player_id', 'origin_year', 'outer_fold').with_columns(
                    pl.Series('talent_mlb_rate', pred), pl.lit(int(g['estimated'])).alias('talent_known'))
                result.write_parquet(path)
                hashes[str(path)] = sha256_file(path)
                note = dict(tag=g['tag'], cutoff=g['cutoff'], excluded_folds=g['excluded_folds'],
                    training_row_ids=g['training_row_ids'], validation_row_ids=g['validation_row_ids'],
                    training_rows=g['training_rows'], training_people=g['training_people'],
                    estimated=g['estimated'], hashes=hashes,
                    preflight_sha256=sha256_file(OUT/'preflight.json'))
                write(npth.name, note)
                print(g['tag'], 'estimated' if g['estimated'] else 'unknown history', len(val), flush=True)
            generated[g['tag']] = pl.read_parquet(path)
            assert generated[g['tag']]['row_id'].to_list() == g['validation_row_ids']
            notes.append(note)
    extra_paths = []; checks = []; outer_support = []; ranges = []; replay_count = 0
    for k in range(5):
        lookup = {}
        for c in pre['cells']:
            if c['fold'] != k:
                continue
            for use in c['uses']:
                values = generated[use['tag']].filter(pl.col('row_id').is_in(use['row_ids']))
                assert len(values) == len(use['row_ids'])
                for r in values.select('row_id', 'talent_known', 'talent_mlb_rate').iter_rows(named=True):
                    if r['row_id'] in lookup:
                        assert lookup[r['row_id']] == r
                    lookup[r['row_id']] = r
        added = pl.DataFrame(list(lookup.values())).sort('row_id')
        path = OUT/f'generated-features-{k}.parquet'; added.write_parquet(path); extra_paths.append(path)
        expanded = f.join(added, on='row_id', how='inner', validate='1:1').sort('row_id')
        assert expanded.select(f.columns).equals(f.filter(pl.col('row_id').is_in(added['row_id'])))
        for c in pre['cells']:
            if c['fold'] != k:
                continue
            y = c['year']
            tr = expanded.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id')
            te = expanded.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            assert len(tr) == len(c['training_row_ids']) and len(te) == len(c['test_row_ids'])
            q = anchor.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            assert (te['talent_known'] == 1).all(), 'Unestimated outer test must be explicitly reviewed before continuing'
            assert np.allclose(te['talent_mlb_rate'], q['baseline_rate'], atol=1e-10, rtol=0)
            rate_note = read(setup.RATE/f'fit-{y}-{k}.json')
            h = next(h for h in rate_note['heads'] if h['head'] == 'rate')
            verify({h['path']:h['sha256']})
            with threadpool_limits(limits=2):
                assert np.allclose(joblib.load(h['path']).predict(safe_matrix(te, pre['rate_features'])),
                    te['talent_mlb_rate'], atol=1e-10, rtol=0)
            replay_count += 1
            for arm, extra in ARMS.items():
                cols = pre['pa_features']+extra
                for head, sub in [('participation', tr), ('conditional_pa', tr.filter(pl.col('next_pa') > 0))]:
                    supp, note = preflight(sub, te, cutoff=y, fold=k, features=cols,
                        expected_keys=te.select('row_id', 'horizon').iter_rows())
                    checks.append(dict(year=y, fold=k, arm=arm, head=head, preflight=note,
                        unknown_training_rows=int((sub['talent_known'] == 0).sum())))
                    outer_support.append(supp.with_columns(pl.lit(arm).alias('arm'), pl.lit(head).alias('head')))
                    known = sub.filter(pl.col('talent_known') == 1)
                    lo, hi = float(known['talent_mlb_rate'].min()), float(known['talent_mlb_rate'].max())
                    ranges.append(dict(year=y, fold=k, arm=arm, head=head, minimum=lo, maximum=hi,
                        outside_rows=te.filter((pl.col('talent_mlb_rate') < lo) | (pl.col('talent_mlb_rate') > hi))['row_id'].to_list()))
    support_path = OUT/'second-stage-support.parquet'; pl.concat(outer_support).write_parquet(support_path)
    extra_paths.append(support_path)
    write('generation-report.json', dict(rate_contexts=len(notes), rate_heads=sum(n['estimated'] for n in notes),
        saved_current_rate_heads_replayed=replay_count, current_test_hitting_exact=True,
        second_stage_checks_before_opportunity_fits=checks, generated_ranges=ranges, notes=notes,
        output_hashes={str(p):sha256_file(p) for p in extra_paths},
        player_walkthrough_status='pending', protected_outcomes_used=False))
    print('All generated forecasts and 140 full/active opportunity checks saved before second-stage fits.', flush=True)


def fit():
    pre = seal(); gen = read(OUT/'generation-report.json')
    verify(gen['output_hashes'])
    assert len(gen['second_stage_checks_before_opportunity_fits']) == 140
    for n in gen['notes']:
        verify(n['hashes'])
    f = pl.read_parquet(setup.current.OUT/'features.parquet')
    q = pl.read_parquet(setup.current.OUT/'scored-predictions.parquet')
    notes = []
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y, k = c['year'], c['fold']; pp = OUT/f'forecast-{y}-{k}.parquet'
            if pp.exists():
                note = read(OUT/f'fit-{y}-{k}.json'); verify(note['hashes']); notes.append(note); continue
            expanded = f.join(pl.read_parquet(OUT/f'generated-features-{k}.parquet'),
                on='row_id', how='inner', validate='1:1')
            tr = expanded.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id')
            te = expanded.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            result = q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            assert te['row_id'].equals(result['row_id'])
            heads = []; hashes = {}
            for arm, extra in ARMS.items():
                cols = pre['pa_features']+extra; raw = {}
                for head, sub in [('participation', tr), ('conditional_pa', tr.filter(pl.col('next_pa') > 0))]:
                    cls = HistGradientBoostingClassifier if head == 'participation' else HistGradientBoostingRegressor
                    m = cls(**pre['settings'])
                    label = 'next_active' if head == 'participation' else 'next_pa'
                    m.fit(sub.select(cols).to_numpy(), sub[label].to_numpy(), sample_weight=weights(sub))
                    x = te.select(cols).to_numpy()
                    raw[head] = m.predict_proba(x)[:,1] if head == 'participation' else m.predict(x)
                    assert np.isfinite(raw[head]).all()
                    mp = OUT/f'{arm}-{head}-{y}-{k}.joblib'; joblib.dump(m, mp, compress=3)
                    hashes[str(mp)] = sha256_file(mp)
                    heads.append(dict(arm=arm, head=head, path=str(mp), sha256=sha256_file(mp),
                        features=cols, training_rows=len(sub), training_people=sub['player_id'].n_unique()))
                p = raw['participation'].copy()
                p[result['hard_unavailable'].to_numpy() | result['reported_retired'].to_numpy()] = 0
                conditional = np.clip(raw['conditional_pa'], 1, 800)
                pa = p*conditional
                value = pa*(result['baseline_rate'].to_numpy()/600+result['origin_replacement_rate'].to_numpy())
                result = result.with_columns(pl.Series(arm+'_raw_p', raw['participation']), pl.Series(arm+'_p', p),
                    pl.Series(arm+'_raw_conditional_pa', raw['conditional_pa']),
                    pl.Series(arm+'_conditional_pa', conditional), pl.Series(arm+'_pa', pa), pl.Series(arm+'_value', value))
            result = result.join(te.select('row_id', 'talent_known', 'talent_mlb_rate'), on='row_id', validate='1:1')
            assert result.select(q.columns).equals(q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id'))
            result.write_parquet(pp); hashes[str(pp)] = sha256_file(pp)
            note = dict(year=y, fold=k, heads=heads, hashes=hashes, information_date=c['information_date'])
            write(f'fit-{y}-{k}.json', note); notes.append(note)
            print(f'Opportunity {y}/{k}: control and talent heads saved; hitting unchanged', flush=True)
    result = pl.concat([pl.read_parquet(OUT/f'forecast-{c["year"]}-{c["fold"]}.parquet') for c in pre['cells']]).sort('row_id')
    assert len(result) == 30506 and result.select(q.columns).equals(q.sort('row_id'))
    result.write_parquet(OUT/'predictions.parquet')
    write('fit-report.json', dict(new_opportunity_heads=140, cells=notes, all_current_columns_exact=True,
        hitting_unchanged=True, player_walkthrough_status='pending', protected_outcomes_used=False,
        output_sha256=sha256_file(OUT/'predictions.parquet')))


if __name__ == '__main__':
    {'features':features, 'fit':fit}[sys.argv[1]]()
