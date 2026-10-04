"""Locked information comparison on repaired contact evidence and actual MLB targets."""
from pathlib import Path
import json
import sys
import joblib
import numpy as np
import polars as pl
from sklearn.linear_model import Ridge
from threadpoolctl import threadpool_limits
from universal_baseball import hitter_repaired_contact_information as info
from universal_baseball.forecast_validation import preflight
from universal_baseball.hitter_compatible_value import labels, UNIT
from universal_baseball.mlb_event_logit import EVENTS, VALUES
from universal_baseball.practical_hitter_v30 import score
from universal_baseball.storage import sha256_file
from prepare_practical_hitter_v33 import safe_matrix
from fit_practical_hitter_v31 import weights
from score_practical_hitter_v31 import rate_score, paired
from score_hitter_reliability_v50 import rate_interval
import evaluate_hitter_talent_bridge_v74 as bridge

ROOT = bridge.ROOT
OUT = ROOT / 'reports/generated/hitter-repaired-contact-information'
WORK = Path('D:/UBM-Source-Cache/hitter-repaired-contact-information')
SOURCE = Path('D:/UBM-Source-Cache/hitter-contact-identity-rebuild/assembly')
ARMS = ['coverage', 'mix', 'joint']
FIXED = [(701762, 2024), (694671, 2023), (668804, 2018), (643446, 2018),
         (640457, 2018), (677594, 2021), (624413, 2018), (702616, 2023),
         (670867, 2017), (592450, 2024), (665742, 2023)]


def read(p):
    return json.loads(Path(p).read_text(encoding='utf8'))


def write(name, value):
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / name
    if p.exists(): raise FileExistsError(f'Preserve artifact: {p}')
    p.write_text(json.dumps(value, indent=2, allow_nan=False, ensure_ascii=False, default=str) + '\n', encoding='utf8')


def full(fold):
    f = pl.read_parquet(bridge.OUT / f'features-{fold}.parquet').sort('row_id')
    return f.join(pl.read_parquet(WORK / 'contact-features.parquet'), on='row_id', validate='1:1')


def prepare():
    assert not (OUT / 'preflight.json').exists(), 'Preserve preflight'
    source_receipt = ROOT / 'reports/model-evidence/hitter-contact-identity-rebuild/final-report.json'
    approved = read(source_receipt)
    assert approved['source_gate'] == 'accepted_for_raw_measurement_test' and approved['source_walkthrough_status'] == 'complete'
    assert read(bridge.OUT / 'report.json')['player_walkthrough_status'] == 'complete'
    for p, h in approved['input_hashes'].items(): assert sha256_file(Path(p)) == h, p
    old = read(bridge.OUT / 'preflight.json')
    # Verify the sealed fold-local adjustments, not only the final report's flag.
    for p, h in old['input_hashes'].items(): assert sha256_file(Path(p)) == h, p
    source_paths = [SOURCE / f'cell-features-{y}.parquet' for y in info.YEARS]
    assembly = read(ROOT / 'reports/model-evidence/hitter-contact-identity-rebuild/assembly.json')
    for y in assembly['years']:
        for p, h in y['artifact_hashes'].items(): assert sha256_file(Path(p)) == h, p
    m = pl.concat([pl.read_parquet(p) for p in source_paths]).sort('season', 'league_id', 'player_id')
    f = pl.read_parquet(bridge.OUT / 'features-0.parquet').sort('row_id')
    q = pl.read_parquet(bridge.OUT / 'scored-predictions.parquet').sort('row_id')
    assert len(f) == 63282 and len(q) == 30506
    for pid, y in FIXED: assert q.filter((pl.col('player_id') == pid) & (pl.col('origin_year') == y)).height == 1, (pid, y)
    contact = info.materialize(f, m)
    WORK.mkdir(parents=True, exist_ok=True)
    path = WORK / 'contact-features.parquet'
    assert not path.exists(); contact.write_parquet(path)
    feature_sets = dict(coverage=old['features']['translated_ridge'] + info.COVERAGE,
                        mix=old['features']['translated_ridge'] + info.COVERAGE + info.SHAPE,
                        joint=old['features']['translated_ridge'] + info.FEATURES)
    assert len(old['features']['translated_ridge']) == 220
    cells, supports, profiles, ranges = [], [], [], []
    with threadpool_limits(limits=2):
        for k in range(5):
            f = full(k)
            for c in [c for c in old['cells'] if c['fold'] == k]:
                y = c['year']; tr = f.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id')
                te = f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
                active = tr.filter(pl.col('next_pa') > 0)
                r = q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
                assert r['row_id'].equals(te['row_id'])
                h = next(h for h in read(bridge.OUT / f'fit-{y}-{k}.json')['heads'] if h['arm'] == 'translated_ridge')
                assert sha256_file(Path(h['path'])) == h['sha256']
                got = joblib.load(h['path']).predict(safe_matrix(te, old['features']['translated_ridge']))
                assert np.allclose(got, r['translated_ridge_all_rate'], atol=1e-10, rtol=0)
                checks = {}
                for arm, cols in feature_sets.items():
                    for kind, g in [('full', tr), ('active', active)]:
                        sup, note = preflight(g, te, cutoff=y, fold=k, features=cols,
                                              expected_keys=te.select('row_id', 'horizon').iter_rows())
                        checks[arm + '_' + kind] = note
                        supports.append(sup.with_columns(pl.lit(arm).alias('arm'), pl.lit(kind).alias('kind')))
                    x, tx = safe_matrix(active, cols), safe_matrix(te, cols)
                    ranges += [dict(origin=y, fold=k, arm=arm, feature=col,
                                    minimum=float(x[:, j].min()), maximum=float(x[:, j].max()),
                                    test_outside=int(((tx[:, j] < x[:, j].min()) | (tx[:, j] > x[:, j].max())).sum()))
                               for j, col in enumerate(cols)]
                a, b = info.tagged(bridge.previous.tagged(active)), info.tagged(bridge.previous.tagged(te))
                for name, keys in [('contact', ['dc_band', 'stage', 'prior_debut']),
                                   ('refined', ['dc_band', 'stage', 'prior_debut', 'age_band', 'rank_band', 'new_draftee', 'thin_pro'])]:
                    n = a.group_by(keys).agg(pl.col('player_id').n_unique().alias('active_profile_people'))
                    profiles.append(b.select('row_id', *keys).join(n, on=keys, how='left', validate='m:1')
                                    .with_columns(pl.col('active_profile_people').fill_null(0), pl.lit(name).alias('profile_kind')))
                people = active.filter(pl.col('dc_available') > 0)['player_id'].n_unique()
                cells.append(dict(year=y, fold=k, information_date=c['information_date'],
                                  training_row_ids=c['training_row_ids'], test_row_ids=c['test_row_ids'],
                                  checks=checks, contact_active_training_people=people,
                                  contact_supported=people >= 20))
            print(f'Actual contact and anchor checks saved in memory for fold {k}.', flush=True)
    for name, table in [('support', pl.concat(supports)), ('profiles', pl.concat(profiles, how='diagonal_relaxed')),
                        ('ranges', pl.DataFrame(ranges))]:
        table.write_parquet(WORK / f'{name}.parquet')
    coverage = full(0).group_by('origin_year', 'stage', 'prior_debut').agg(pl.len().alias('rows'),
                      pl.col('dc_available').sum().alias('measured_rows')).sort('origin_year', 'stage', 'prior_debut')
    paths = source_paths + [source_receipt, Path(__file__), ROOT / 'src/universal_baseball/hitter_repaired_contact_information.py',
        ROOT / 'tests/test_hitter_repaired_contact_information.py', ROOT / 'docs/hitter-repaired-contact-information-contract.md',
        ROOT / 'scripts/prepare_practical_hitter_v33.py', ROOT / 'scripts/fit_practical_hitter_v31.py',
        ROOT / 'src/universal_baseball/hitter_compatible_value.py', ROOT / 'src/universal_baseball/forecast_validation.py',
        bridge.OUT / 'scored-predictions.parquet', bridge.OUT / 'preflight.json', bridge.OUT / 'report.json', bridge.COUNTS,
        *[bridge.OUT / f'features-{k}.parquet' for k in range(5)],
        *[WORK / (n + '.parquet') for n in ['contact-features', 'support', 'profiles', 'ranges']]]
    write('preflight.json', dict(before_fits=True, cells=cells, features=feature_sets, fixed_cases=FIXED,
        actual_checks=210, translated_anchor_replays=35, coverage=coverage.to_dicts(),
        input_hashes={str(p): sha256_file(p) for p in paths}, protected_outcomes_used=False,
        fallback_origin_2016=True, raw_context_limit='Not park or opponent neutral', opportunity_changed=False))
    print('All 210 actual checks and 35 anchor replays saved before fits.', flush=True)


def verify_inputs(pre):
    for p, h in pre['input_hashes'].items(): assert sha256_file(Path(p)) == h, p


def fit():
    pre = read(OUT / 'preflight.json'); verify_inputs(pre)
    anchor = pl.read_parquet(bridge.OUT / 'scored-predictions.parquet').sort('row_id')
    predictions = []
    with threadpool_limits(limits=2):
        for k in range(5):
            f = full(k)
            for c in [c for c in pre['cells'] if c['fold'] == k]:
                y = c['year']; note_path = OUT / f'fit-{y}-{k}.json'
                path = WORK / f'forecast-{y}-{k}.parquet'
                if note_path.exists():
                    n = read(note_path); assert sha256_file(path) == n['prediction_sha256']
                    for h in n['heads']: assert sha256_file(Path(h['path'])) == h['sha256']
                    predictions.append(path); continue
                assert not path.exists(), 'Unsealed forecast must be inspected, not overwritten'
                active = f.filter(pl.col('row_id').is_in(c['training_row_ids']) & (pl.col('next_pa') > 0)).sort('row_id')
                te = f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
                q = anchor.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
                assert q['row_id'].equals(te['row_id'])
                w = weights(active) * active['next_pa'].to_numpy(); w *= len(w) / w.sum()
                heads = []
                for arm, cols in pre['features'].items():
                    if c['contact_supported']:
                        model = Ridge(alpha=100)
                        model.fit(safe_matrix(active, cols), active['next_batting_rate'].to_numpy(), sample_weight=w)
                        raw = model.predict(safe_matrix(te, cols))
                        mp = WORK / f'{arm}-{y}-{k}.joblib'; assert not mp.exists(); joblib.dump(model, mp, compress=3)
                        heads.append(dict(arm=arm, path=str(mp), sha256=sha256_file(mp), training_rows=len(active),
                                          training_people=active['player_id'].n_unique(), max_target_year=int(active['target_year'].max())))
                    else:
                        raw = q['translated_ridge_rate'].to_numpy()
                    q = q.with_columns(pl.Series(arm + '_raw_rate', raw))
                    for suffix, primary in [('', True), ('_all', False)]:
                        a = arm + suffix
                        rate = info.assembly(raw, q['translated_ridge_rate'].to_numpy(), te['dc_available'].to_numpy(),
                                             prior_debut=q['prior_debut'].to_numpy(), primary=primary, supported=c['contact_supported'])
                        q = q.with_columns(pl.Series(a + '_rate', rate), pl.col('preseason_pa').alias(a + '_pa'))
                        q = q.with_columns((pl.col(a + '_pa') * (pl.col(a + '_rate') / 600 + pl.col('origin_replacement_rate'))).alias(a + '_value'))
                q = q.join(te.select('row_id', *info.FEATURES, 'dc_physical_exposure', 'dc_classified_exposure',
                                      'dc_actual_leagues', 'dc_source_seasons'), on='row_id', validate='1:1')
                q = q.with_columns(pl.lit(c['contact_supported']).alias('dc_supported_fold'))
                q.write_parquet(path)
                write(note_path.name, dict(year=y, fold=k, heads=heads, contact_supported=c['contact_supported'],
                                           prediction_path=str(path), prediction_sha256=sha256_file(path)))
                predictions.append(path)
                print(f'Repaired contact forecasts {y}/{k}: {len(heads)} fixed heads.', flush=True)
    q = pl.concat([pl.read_parquet(p) for p in predictions]).sort('row_id')
    assert q.select(anchor.columns).equals(anchor) and len(q) == 30506
    final = WORK / 'predictions.parquet'; assert not final.exists(); q.write_parquet(final)
    write('fit-report.json', dict(heads=90, unsupported_fallback_cells=5, unchanged_anchor_columns=True,
                                  predictions_path=str(final), predictions_sha256=sha256_file(final),
                                  player_walkthrough_status='pending', protected_outcomes_used=False))


def scope(q):
    never = q.filter(pl.col('prior_debut') == 0)
    out = [('all', q), ('never_debut', never), ('upper_never_debut', never.filter(pl.col('stage') == 'Upper minors')),
           ('lower_never_debut', never.filter(pl.col('stage') == 'Lower minors')),
           ('measured_never', never.filter(pl.col('dc_available') > 0)), ('unmeasured_never', never.filter(pl.col('dc_available') == 0)),
           ('new_draftees', never.filter(pl.col('new_draftee'))), ('thin_pro', never.filter(pl.col('thin_pro'))),
           ('current_brief', q.filter(pl.col('pa_0').is_between(1, 199))),
           ('public', q.filter((pl.col('pa_0') > 0) & pl.col('steamer_index').is_not_null() & pl.col('zips_index').is_not_null()))]
    out += [('never_origin_' + str(y), never.filter(pl.col('origin_year') == y)) for y in sorted(never['origin_year'].unique())]
    return [(n, g) for n, g in out if len(g)]


def scoring():
    pre = read(OUT / 'preflight.json'); verify_inputs(pre)
    report = read(OUT / 'fit-report.json'); assert sha256_file(Path(report['predictions_path'])) == report['predictions_sha256']
    q = pl.read_parquet(report['predictions_path']).sort('row_id')
    anchor = pl.read_parquet(bridge.OUT / 'scored-predictions.parquet').sort('row_id')
    assert q.select(anchor.columns).equals(anchor)
    f0 = full(0)
    q = q.join(bridge.previous.tagged(f0).select('row_id', 'new_draftee', 'thin_pro', 'rank_band',
             pl.col('next_batting_rate').alias('next_relative_rate')), on='row_id', validate='1:1')
    rebuilt = labels(q.select(['count_' + e for e in EVENTS]).to_numpy(),
                     q.select(['origin_env_' + e for e in EVENTS]).to_numpy(),
                     q.select(['target_env_' + e for e in EVENTS]).to_numpy(), q['origin_replacement_rate'].to_numpy())
    assert np.array_equal(rebuilt['pa'], q['next_pa'])
    assert np.allclose(rebuilt['relative_rate'], q['next_relative_rate'], atol=1e-10, rtol=0)
    assert np.allclose(rebuilt['common_value'], q['next_value'], atol=1e-10, rtol=0)
    arms = ['preseason', 'translated_ridge', *ARMS, *[a + '_all' for a in ARMS]]
    replayed, fallback = 0, 0
    with threadpool_limits(limits=2):
        for k in range(5):
            f = full(k)
            for c in [c for c in pre['cells'] if c['fold'] == k]:
                te = f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
                r = q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
                note = read(OUT / f"fit-{c['year']}-{k}.json")
                fallback += not note['contact_supported']
                for h in note['heads']:
                    assert sha256_file(Path(h['path'])) == h['sha256']
                    got = joblib.load(h['path']).predict(safe_matrix(te, pre['features'][h['arm']]))
                    assert np.allclose(got, r[h['arm'] + '_raw_rate'], atol=1e-10, rtol=0); replayed += 1
    assert replayed == 90 and fallback == 5
    for a in arms:
        assert q[a + '_pa'].equals(q['preseason_pa'])
        assert np.allclose(q[a + '_value'], q[a + '_pa'] * (q[a + '_rate'] / 600 + q['origin_replacement_rate']), atol=1e-10, rtol=0)
    for a in ARMS:
        unchanged = q.filter((pl.col('prior_debut') == 1) | (pl.col('dc_available') == 0) | ~pl.col('dc_supported_fold'))
        assert unchanged[a + '_rate'].equals(unchanged['translated_ridge_rate'])
        unchanged_all = q.filter((pl.col('dc_available') == 0) | ~pl.col('dc_supported_fold'))
        assert unchanged_all[a + '_all_rate'].equals(unchanged_all['translated_ridge_rate'])
    low = -(q.select(['target_env_' + e for e in EVENTS]).to_numpy() @ VALUES) * UNIT
    high = low + VALUES.max() * UNIT
    scores, intervals = [], []
    for n, g in scope(q):
        rel = g.drop('next_batting_rate').rename({'next_relative_rate': 'next_batting_rate'})
        scores.append(dict(scope=n, rows=len(g), active_rows=int((g['next_pa'] > 0).sum()),
                           actual_pa=int(g['next_pa'].sum()), actual_value=float(g['next_value'].sum()),
                           scores={a: score(g, a) for a in arms + (['steamer'] if n == 'public' else [])},
                           rate={a: rate_score(rel, a + '_rate') for a in arms},
                           rate_equal_player={a: rate_score(rel, a + '_rate', False) for a in arms},
                           common_origin_rate_sensitivity={a: dict(rate_score(g, a + '_rate'), unit='common-origin event reference')
                               for a in arms + (['common_steamer', 'common_zips'] if n == 'public' else [])}))
        if n in ['all', 'never_debut', 'upper_never_debut', 'lower_never_debut', 'measured_never']:
            for a, b in [('coverage', 'translated_ridge'), ('mix', 'coverage'), ('joint', 'mix'), ('joint', 'translated_ridge'),
                         ('joint_all', 'translated_ridge')]:
                intervals.append(dict(scope=n, **paired(g, a, b)))
                if (g['next_pa'] > 0).any(): intervals.append(dict(scope=n, **rate_interval(rel, a, b)))
    write('scores.json', scores); write('intervals.json', intervals)
    scored = WORK / 'scored-predictions.parquet'; assert not scored.exists(); q.write_parquet(scored)
    write('verification.json', dict(replayed_heads=replayed, fallback_cells=fallback, unchanged_opportunity=True,
        exact_anchor_columns=True, targets_independently_reconstructed=True, rows=len(q),
        mathematical_rate_violations={a: int(((q[a + '_rate'].to_numpy() < low) | (q[a + '_rate'].to_numpy() > high)).sum()) for a in arms},
        player_walkthrough_status='pending', protected_outcomes_used=False,
        scored_path=str(scored), scored_sha256=sha256_file(scored)))
    for s in scores[:6]:
        print(s['scope'], {a: (s['rate'][a]['rmse'], s['scores'][a]['value_rmse']) for a in arms[:5]}, flush=True)
    print('Scores provisional pending actual player review.', flush=True)


if __name__ == '__main__':
    {'prepare': prepare, 'fit': fit, 'score': scoring}[sys.argv[1]]()
