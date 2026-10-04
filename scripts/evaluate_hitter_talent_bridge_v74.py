"""Fixed hitting comparison with held-player, own-origin translation inputs."""
from pathlib import Path
import json
import sys

import joblib
import numpy as np
import polars as pl
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from threadpoolctl import threadpool_limits

from universal_baseball.forecast_validation import preflight
from universal_baseball.hitter_talent_bridge import (
    EVENTS, PROFILE_FEATURES, SCOUT_FEATURES, event_counts, materialize,
)
from universal_baseball.post_arrival_history import player_fold
from universal_baseball.practical_hitter_v30 import score
from universal_baseball.storage import sha256_file
from fit_practical_hitter_v31 import weights
from prepare_practical_hitter_v33 import safe_matrix
from score_practical_hitter_v31 import paired, rate_score
from score_hitter_reliability_v50 import rate_interval
import evaluate_hitter_preseason_readiness_v68 as previous

ROOT = previous.ROOT
OUT = ROOT / 'reports/generated/hitter-talent-bridge-v74'
BASE = ROOT / 'reports/generated/practical-hitter-numeric-repair-v53'
COUNTS = ROOT / 'reports/generated/practical-hitter-v31/counts.parquet'
CONTRACT = ROOT / 'docs/hitter-talent-bridge-v74-contract.md'
ARMS = ['scout_ridge', 'translated_ridge', 'translated_hist']
FIXED = [(701762, 2024, 'Nick Kurtz'), (694671, 2023, 'Wyatt Langford'),
         (641355, 2016, 'Cody Bellinger'), (624413, 2018, 'Pete Alonso'),
         (677594, 2021, 'Julio Rodríguez'), (702616, 2023, 'Jackson Holliday'),
         (670867, 2017, 'Kevin Maitan'), (691026, 2023, 'Masyn Winn'),
         (592450, 2024, 'Aaron Judge')]


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def write(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(obj, indent=2, ensure_ascii=False,
                                     allow_nan=False, default=str) + '\n', encoding='utf8')


def names():
    original = read(BASE / 'preflight.json')['rate_features']
    assert len(original) == 199 and not any(c.startswith('scout_') for c in original)
    return original, {'scout_ridge': original + SCOUT_FEATURES,
                      'translated_ridge': original + SCOUT_FEATURES + PROFILE_FEATURES,
                      'translated_hist': original + SCOUT_FEATURES + PROFILE_FEATURES}


def prepare():
    assert not (OUT / 'preflight.json').exists(), 'Preserve sealed preflight'
    assert read(ROOT / 'reports/generated/hitter-smooth-preseason-v73/report.json')['player_walkthrough_status'] == 'complete'
    f = pl.read_parquet(previous.OUT / 'features.parquet').sort('row_id')
    anchor = pl.read_parquet(previous.OUT / 'scored-predictions.parquet').sort('row_id')
    assert len(f) == 63282 and len(anchor) == 30506
    assert all(player_fold(pid) == fold for pid, fold in f.select('player_id', 'outer_fold').unique().iter_rows())
    for pid, year, expected in FIXED:
        r = anchor.filter((pl.col('player_id') == pid) & (pl.col('origin_year') == year))
        assert len(r) == 1 and r['player_name'][0] == expected, (pid, expected, r.select('player_name').to_dicts())
    counts = pl.read_parquet(COUNTS).filter(pl.col('season') <= 2024)
    event_counts(counts)
    original, features = names()
    old_pre = read(previous.OUT / 'preflight.json')
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = [CONTRACT, Path(__file__), ROOT / 'src/universal_baseball/hitter_talent_bridge.py',
              ROOT / 'src/universal_baseball/post_arrival_history.py', ROOT / 'src/universal_baseball/forecast_validation.py',
              ROOT / 'scripts/prepare_practical_hitter_v33.py', ROOT / 'scripts/fit_practical_hitter_v31.py',
              previous.OUT / 'features.parquet', previous.OUT / 'scored-predictions.parquet', previous.OUT / 'preflight.json',
              BASE / 'preflight.json', COUNTS]
    source_hashes = {str(p): sha256_file(p) for p in inputs}
    # A source-only graph is learned before rating fits, with its own provenance.
    # Cache only when every input hash still matches; never restart from a lock.
    for fold in range(5):
        path = OUT / f'features-{fold}.parquet'
        note_path = OUT / f'translation-{fold}.json'
        if path.exists() and note_path.exists():
            note = read(note_path)
            old_hashes = note['input_hashes']
            different = {p for p in source_hashes if source_hashes[p] != old_hashes.get(p)}
            assert not different or (different == {str(Path(__file__))} and
                old_hashes[str(Path(__file__))] == 'ea5c8e5e958fbbf12e674c01864e641fb534552970643494c580169ae5277a88'), 'Unapproved source-cache changes'
            assert set(old_hashes) == set(source_hashes) and sha256_file(path) == note['features_sha256']
        else:
            profiles, graphs = materialize(counts, f.select('row_id', 'player_id', 'origin_year'), held_fold=fold)
            full = f.join(profiles.drop('player_id', 'origin_year'), on='row_id', validate='1:1')
            assert full.select(f.columns).equals(f)
            full.write_parquet(path)
            write(note_path.name, dict(input_hashes=source_hashes, graphs=graphs,
                                      features_sha256=sha256_file(path), source_cutoff=2024,
                                      profiles_missing=int(full['translated_missing'].sum())))
        print(f'Own-origin graph features sealed for held-player fold {fold}.', flush=True)
    supports, profiles, ranges, cells, replayed = [], [], [], [], 0
    with threadpool_limits(limits=2):
        for cell in old_pre['cells']:
            y, fold = cell['year'], cell['fold']
            full = pl.read_parquet(OUT / f'features-{fold}.parquet')
            tr = full.filter(pl.col('row_id').is_in(cell['training_row_ids'])).sort('row_id')
            te = full.filter(pl.col('row_id').is_in(cell['test_row_ids'])).sort('row_id')
            actual = anchor.filter(pl.col('row_id').is_in(te['row_id'].to_list())).sort('row_id')
            assert te['row_id'].equals(actual['row_id'])
            old_fit = read(BASE / f'fit-{y}-{fold}.json')
            h = next(h for h in old_fit['heads'] if h['head'] == 'rate')
            assert sha256_file(Path(h['path'])) == h['sha256']
            predicted = joblib.load(h['path']).predict(safe_matrix(te, original))
            assert np.allclose(predicted, actual['baseline_rate'], atol=1e-10, rtol=0)
            replayed += 1
            checks = {}
            for arm, cols in features.items():
                for kind, sub in [('full', tr), ('active', tr.filter(pl.col('next_pa') > 0))]:
                    sup, note = preflight(sub, te, cutoff=y, fold=fold, features=cols,
                                          expected_keys=te.select('row_id', 'horizon').iter_rows())
                    checks[arm + '_' + kind] = note
                    supports.append(sup.with_columns(pl.lit(arm).alias('arm'), pl.lit(kind).alias('kind')))
                    for tag, keys in [('broad', ['stage', 'prior_debut', 'age_band', 'rank_band']),
                                      ('refined', ['stage', 'prior_debut', 'age_band', 'rank_band', 'new_draftee', 'thin_pro'])]:
                        a, b = previous.tagged(sub), previous.tagged(te)
                        n = a.group_by(keys).agg(pl.col('player_id').n_unique().alias('profile_people'))
                        profiles.append(b.select('row_id', *keys).join(n, on=keys, how='left', validate='m:1').with_columns(
                            pl.col('profile_people').fill_null(0), pl.lit(arm).alias('arm'),
                            pl.lit(kind).alias('kind'), pl.lit(tag).alias('profile_kind')))
                active = tr.filter(pl.col('next_pa') > 0)
                x, tx = safe_matrix(active, cols), safe_matrix(te, cols)
                for i, col in enumerate(cols):
                    lo, hi = float(x[:, i].min()), float(x[:, i].max())
                    ranges.append(dict(origin=y, fold=fold, arm=arm, feature=col, minimum=lo, maximum=hi,
                                       test_outside=int(((tx[:, i] < lo) | (tx[:, i] > hi)).sum())))
            cells.append(dict(**cell, checks=checks))
    pl.concat(supports).write_parquet(OUT / 'support.parquet')
    pl.concat(profiles, how='diagonal_relaxed').write_parquet(OUT / 'profile-support.parquet')
    pl.DataFrame(ranges).write_parquet(OUT / 'feature-ranges.parquet')
    generated = [OUT / n for n in ['support.parquet', 'profile-support.parquet', 'feature-ranges.parquet']]
    generated += [OUT / f'{stem}-{k}.{ext}' for k in range(5)
                  for stem, ext in [('features', 'parquet'), ('translation', 'json')]]
    write('preflight.json', dict(cells=cells, features=features, original_features=original,
                                checks_before_fits=210, original_heads_replayed=replayed,
                                input_hashes={**source_hashes, **{str(p): sha256_file(p) for p in generated}},
                                fixed_cases=FIXED, protected_outcomes_used=False, rate_clipping=False))
    print('210 actual full/active checks and 35 original head replays saved before rating fits.', flush=True)


def fit():
    pre = read(OUT / 'preflight.json')
    for p, h in pre['input_hashes'].items():
        assert sha256_file(Path(p)) == h, p
    anchor = pl.read_parquet(previous.OUT / 'scored-predictions.parquet')
    fits, completed = [], []
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y, k = c['year'], c['fold']
            pp = OUT / f'forecast-{y}-{k}.parquet'
            if pp.exists():
                n = read(OUT / f'fit-{y}-{k}.json')
                assert sha256_file(pp) == n['prediction_sha256']
                for h in n['heads']:
                    assert sha256_file(Path(h['path'])) == h['sha256']
                fits.append(n)
                completed.append(pp)
                continue
            f = pl.read_parquet(OUT / f'features-{k}.parquet')
            tr = f.filter(pl.col('row_id').is_in(c['training_row_ids']) & (pl.col('next_pa') > 0)).sort('row_id')
            te = f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            q = anchor.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            assert q['row_id'].equals(te['row_id'])
            w = weights(tr) * tr['next_pa'].to_numpy()
            w *= len(w) / w.sum()
            heads = []
            for arm, cols in pre['features'].items():
                model = (HistGradientBoostingRegressor(max_iter=250, max_depth=3, min_samples_leaf=30,
                         learning_rate=.05, l2_regularization=10, early_stopping=False, random_state=31)
                         if arm == 'translated_hist' else Ridge(alpha=100))
                model.fit(safe_matrix(tr, cols), tr['next_batting_rate'].to_numpy(), sample_weight=w)
                pred = model.predict(safe_matrix(te, cols))
                assert np.isfinite(pred).all()
                path = OUT / f'{arm}-{y}-{k}.joblib'
                joblib.dump(model, path, compress=3)
                heads.append(dict(arm=arm, path=str(path), sha256=sha256_file(path),
                                  training_rows=len(tr), training_people=tr['player_id'].n_unique(),
                                  maximum_target_year=int(tr['target_year'].max())))
                primary = np.where(q['prior_debut'].to_numpy() == 0, pred, q['baseline_rate'].to_numpy())
                for suffix, rate in [('', primary), ('_all', pred)]:
                    a = arm + suffix
                    q = q.with_columns(pl.Series(a + '_rate', rate), pl.col('preseason_pa').alias(a + '_pa'))
                    q = q.with_columns((pl.col(a + '_pa') * (pl.col(a + '_rate') / 600 + pl.col('origin_replacement_rate'))).alias(a + '_value'))
            q.write_parquet(pp)
            n = dict(year=y, fold=k, heads=heads, prediction_sha256=sha256_file(pp), information_date=c['information_date'])
            write(f'fit-{y}-{k}.json', n)
            fits.append(n)
            completed.append(pp)
            print(f'Three fixed hitting heads saved: {y}/{k}.', flush=True)
    q = pl.concat([pl.read_parquet(p) for p in completed]).sort('row_id')
    assert len(q) == 30506 and q.select(anchor.columns).equals(anchor.sort('row_id'))
    q.write_parquet(OUT / 'predictions.parquet')
    write('fits.json', fits)


def trace_ridge(model, row, cols):
    x = safe_matrix(row, cols)[0]
    effects = x * model.coef_
    raw = float(model.intercept_ + effects.sum())
    assert np.isclose(raw, model.predict(x[None, :])[0], atol=1e-10)
    return dict(intercept=float(model.intercept_), prediction=raw,
                effects=sorted([dict(feature=c, scaled_input=float(v), coefficient=float(b), effect=float(e))
                                for c, v, b, e in zip(cols, x, model.coef_, effects)],
                               key=lambda r: abs(r['effect']), reverse=True),
                interpretation='Exact linear sum, not causal attribution')


def scoring():
    pre = read(OUT / 'preflight.json')
    for p, h in pre['input_hashes'].items():
        assert sha256_file(Path(p)) == h, p
    q = pl.read_parquet(OUT / 'predictions.parquet')
    baseline = pl.read_parquet(previous.OUT / 'scored-predictions.parquet').sort('row_id')
    assert q.select(baseline.columns).equals(baseline)
    tagged = previous.tagged(pl.read_parquet(previous.OUT / 'features.parquet'))
    q = q.join(tagged.select('row_id', 'rank_band', 'new_draftee', 'thin_pro'), on='row_id', validate='1:1')
    all_arms = ['preseason', *ARMS, *[a + '_all' for a in ARMS]]
    replayed = 0
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y, k = c['year'], c['fold']
            f = pl.read_parquet(OUT / f'features-{k}.parquet')
            te = f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            r = q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            for h in read(OUT / f'fit-{y}-{k}.json')['heads']:
                assert sha256_file(Path(h['path'])) == h['sha256']
                pred = joblib.load(h['path']).predict(safe_matrix(te, pre['features'][h['arm']]))
                assert np.allclose(pred, r[h['arm'] + '_all_rate'], atol=1e-10, rtol=0)
                replayed += 1
    for a in all_arms:
        assert q[a + '_pa'].equals(q['preseason_pa'])
        assert np.allclose(q[a + '_value'], q[a + '_pa'] * (q[a + '_rate'] / 600 + q['origin_replacement_rate']), atol=1e-10, rtol=0)
    established = q.filter(pl.col('prior_debut') == 1)
    assert all(established[a + '_rate'].equals(established['preseason_rate']) for a in ARMS)
    never = q.filter(pl.col('prior_debut') == 0)
    public = q.filter((pl.col('pa_0') > 0) & pl.col('steamer_index').is_not_null() & pl.col('zips_index').is_not_null())
    assert len(public) == 2627
    scopes = [('all', q), ('never_debut', never), ('upper_never_debut', never.filter(pl.col('stage') == 'Upper minors')),
              ('lower_never_debut', never.filter(pl.col('stage') == 'Lower minors')), ('public', public),
              ('new_draftees', never.filter(pl.col('new_draftee'))), ('thin_pro', never.filter(pl.col('thin_pro'))),
              ('current_brief', q.filter(pl.col('pa_0').is_between(1, 199))), ('current_regular', q.filter(pl.col('pa_0') >= 400))]
    scopes += [('never_origin_' + str(y), never.filter(pl.col('origin_year') == y)) for y in sorted(never['origin_year'].unique())]
    scopes += [('never_rank_' + str(k), never.filter(pl.col('rank_band') == k)) for k in [-1, 0, 1, 2, 3]]
    scores, intervals = [], []
    for name, g in scopes:
        if not len(g):
            continue
        extra = ['steamer'] if name == 'public' else []
        scores.append(dict(scope=name, rows=len(g), people=g['player_id'].n_unique(), actual_pa=int(g['next_pa'].sum()),
                           actual_value=float(g['next_value'].sum()),
                           scores={a: score(g, a) for a in all_arms + extra},
                           rate={a: rate_score(g, a + '_rate') for a in all_arms + (['common_steamer', 'common_zips'] if name == 'public' else [])},
                           unweighted_rate={a: rate_score(g, a + '_rate', False) for a in all_arms}))
        if name in ['never_debut', 'upper_never_debut', 'lower_never_debut']:
            for a in ARMS:
                intervals.append(dict(scope=name, **paired(g, a, 'preseason')))
                if (g['next_pa'] > 0).any():
                    intervals.append(dict(scope=name, **rate_interval(g, a, 'preseason')))
    write('scores.json', scores)
    write('intervals.json', intervals)
    q.write_parquet(OUT / 'scored-predictions.parquet')
    selected = {}
    def choose(g, reason):
        assert len(g)
        selected.setdefault(g['row_id'][0], []).append(reason)
    for pid, y, name in FIXED:
        choose(q.filter((pl.col('player_id') == pid) & (pl.col('origin_year') == y)), 'fixed before fit')
    for a in ARMS:
        err = never.with_columns(((pl.col('preseason_value') - pl.col('next_value')) ** 2 -
                                (pl.col(a + '_value') - pl.col('next_value')) ** 2).alias('gain'),
                                (pl.col(a + '_value') - pl.col('next_value')).alias('error'))
        for reason, g in [('gain', err.sort('gain', descending=True)), ('harm', err.sort('gain')),
                          ('false high', err.sort('error', descending=True)), ('false low', err.sort('error')),
                          ('ordinary', err.filter(pl.col('next_pa').is_between(100, 600)).sort(pl.col('error').abs()))]:
            choose(g, a + ' largest ' + reason if reason != 'ordinary' else a + ' ordinary active')
    history = pl.read_parquet(COUNTS)
    support = pl.read_parquet(OUT / 'profile-support.parquet')
    cases = []
    with threadpool_limits(limits=2):
        for rid, reasons in selected.items():
            r = q.filter(pl.col('row_id') == rid).row(0, named=True)
            f = pl.read_parquet(OUT / f"features-{r['outer_fold']}.parquet")
            row = f.filter(pl.col('row_id') == rid)
            note = read(OUT / f"fit-{r['origin_year']}-{r['outer_fold']}.json")
            graph = next(g for g in read(OUT / f"translation-{r['outer_fold']}.json")['graphs'] if g['cutoff'] == r['origin_year'])
            traces, probes = {}, {}
            for h in note['heads']:
                a, cols = h['arm'], pre['features'][h['arm']]
                m = joblib.load(h['path'])
                if a != 'translated_hist':
                    traces[a] = trace_ridge(m, row, cols)
                else:
                    x = safe_matrix(row, cols)
                    staged = [float(z[0]) for z in m.staged_predict(x)]
                    assert np.isclose(staged[-1], r[a + '_all_rate'], atol=1e-10)
                    traces[a] = dict(initial=float(m._baseline_prediction[0, 0]),
                                     prediction=staged[-1], every_tree_cumulative=staged)
                neutral = row.with_columns([pl.lit(0.).alias(c) for c in PROFILE_FEATURES[:8]])
                probes[a] = float(m.predict(safe_matrix(neutral, cols))[0])
            old_note = read(BASE / f"fit-{r['origin_year']}-{r['outer_fold']}.json")
            old_head = next(h for h in old_note['heads'] if h['head'] == 'rate')
            traces['baseline'] = trace_ridge(joblib.load(old_head['path']), row, pre['original_features'])
            peers = q.filter((pl.col('origin_year') == r['origin_year']) & (pl.col('stage') == r['stage']) &
                             (pl.col('prior_debut') == r['prior_debut']) & (pl.col('player_id') != r['player_id'])).with_columns(
                (((pl.col('age') - r['age']) / 3) ** 2 + ((pl.col('minor_pa_0') - r['minor_pa_0']) / 250) ** 2 +
                 (pl.col('new_scout_rank_score_0') - r['new_scout_rank_score_0']) ** 2).alias('distance')).sort('distance', 'player_id').head(4)
            used_buckets = row['translation_buckets'][0].split(',')
            cases.append(dict(origin=r, selection=reasons, information_date=note['information_date'],
                              actual_inputs={c: row[c][0] for c in pre['features']['translated_ridge']},
                              profile=row.select([c for c in row.columns if c.startswith(('translation_', 'translated_probability_'))]).to_dicts()[0],
                              graph=dict(cutoff=graph['cutoff'], held_fold=graph['held_fold'], pair_count=graph['pair_count'],
                                         people=len(graph['people']), edges=graph['edges'],
                                         offsets={b: graph['offsets'][b] for b in used_buckets if b in graph['offsets']},
                                         disconnected=graph['disconnected_buckets']),
                              source_history=history.filter((pl.col('player_id') == r['player_id']) & pl.col('season').is_between(r['origin_year'] - 2, r['origin_year'])).sort('season', 'bucket').to_dicts(),
                              actual_history=history.filter((pl.col('player_id') == r['player_id']) & (pl.col('season') == r['target_year']) & (pl.col('bucket') == 'MLB')).to_dicts(),
                              saved_traces=traces, same_fit_neutral_profile_probes=probes,
                              probe_limit='Profile-centered MLB reference at unchanged exposures/rank; possibly artificial, mechanics only, not causal.',
                              training_profiles=support.filter(pl.col('row_id') == rid).to_dicts(),
                              peers=peers.select('player_id', 'player_name', 'age', 'minor_pa_0', 'new_scout_rank_score_0',
                                                 'preseason_pa', 'preseason_rate', 'preseason_value',
                                                 *[a + '_' + c for a in ARMS for c in ['rate', 'value']], 'next_pa', 'next_value', 'next_batting_rate').to_dicts()))
    write('cases.json', cases)
    write('verification.json', dict(replayed_heads=replayed, expected_heads=105, unchanged_PA=True,
                                    primary_established_rate_unchanged=True, all_old_columns_exact=True,
                                    player_walkthrough_status='pending', cases=len(cases), protected_outcomes_used=False,
                                    frozen_forecast_changed=False, physical_violations={a: int(q.filter(
                                        (pl.col(a + '_rate') < pl.col('physical_low')) | (pl.col(a + '_rate') > pl.col('physical_high'))).height) for a in all_arms}))
    for s in scores[:7]:
        print(s['scope'], {a: (round(v['value_rmse'], 6), round(s['rate'][a]['rmse'], 4) if s['rate'][a]['rmse'] is not None else None)
                           for a, v in s['scores'].items()}, flush=True)
    print(f'{len(cases)} selected player reviews pending; no model disposition yet.', flush=True)


if __name__ == '__main__':
    {'prepare': prepare, 'fit': fit, 'score': scoring}[sys.argv[1]]()
