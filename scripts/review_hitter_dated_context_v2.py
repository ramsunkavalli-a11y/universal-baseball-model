"""Amended independent context review; preserve initial common-reference scores."""
from collections import Counter
from datetime import date
from pathlib import Path
import json

import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

from universal_baseball.histogram_prediction_trace import trace
from universal_baseball.storage import sha256_file
from universal_baseball.hitter_compatible_value import UNIT
from universal_baseball.mlb_event_logit import EVENTS, VALUES
from evaluate_hitter_readiness_v49 import logit_trace
import run_hitter_dated_context as run

ROOT, OUT = run.ROOT, run.OUT
PUBLIC = ROOT / 'reports/model-evidence/hitter-dated-context-integration'
FIXED = [('Hyeseong Kim', 808975, 2024), ('Jung Hoo Lee', 808982, 2024), ('Ha-Seong Kim', 673490, 2022),
         ('Eric Thames', 519346, 2016), ('Aaron Judge', 592450, 2024), ('Nick Kurtz', 701762, 2024),
         ('Steven Kwan', 680757, 2021), ('Junior Caminero', 691406, 2024)]
AMENDMENT = ROOT / 'docs/hitter-dated-context-scoring-amendment.md'


def policy(raw, q):
    p = np.asarray(raw['participation']).copy()
    p[q['hard_unavailable'].to_numpy() | q['reported_retired'].to_numpy()] = 0
    cond = np.clip(raw['conditional_pa'], 1, 800)
    return p, cond, p * cond


def errors(g, arm):
    p = g[arm + '_p'].to_numpy(); n = g['next_pa'].to_numpy()
    phat = g[arm + '_pa'].to_numpy(); v = g[arm + '_value'].to_numpy()
    actual = g['actual_relative_value'].to_numpy(); active = (n > 0).astype(float)
    lp = np.clip(p, 1e-12, 1 - 1e-12)
    return np.column_stack([(phat - n) ** 2, abs(phat - n), phat - n,
        (v - actual) ** 2, abs(v - actual), v - actual,
        (p - active) ** 2, -active * np.log(lp) - (1 - active) * np.log1p(-lp)])


def score(g, arm):
    e = errors(g, arm); years = g['origin_year'].to_numpy()
    avg = np.mean([e[years == y].mean(0) for y in np.unique(years)], axis=0)
    return dict(pa_rmse=float(np.sqrt(avg[0])), pa_mae=float(avg[1]), pa_bias=float(avg[2]),
        value_rmse=float(np.sqrt(avg[3])), value_mae=float(avg[4]), value_bias=float(avg[5]),
        brier=float(avg[6]), logloss=float(avg[7]), expected_pa=float(g[arm + '_pa'].sum()),
        expected_appearances=float(g[arm + '_p'].sum()), expected_relative_value=float(g[arm + '_value'].sum()))


def interval(g):
    delta = errors(g, 'ctx') - errors(g, 'current')
    _, yi = np.unique(g['origin_year'].to_numpy(), return_inverse=True)
    people, pi = np.unique(g['player_id'].to_numpy(), return_inverse=True)
    den = np.zeros((len(people), yi.max() + 1))
    num = np.zeros((*den.shape, delta.shape[1]))
    np.add.at(den, (pi, yi), 1); np.add.at(num, (pi, yi), delta)
    rng = np.random.default_rng(83); draws = []
    for rep in range(2000):
        sampled = rng.integers(0, len(people), len(people))
        w = np.bincount(sampled, minlength=len(people))
        d = w @ den
        if (d > 0).all():
            z = (np.tensordot(w, num, axes=(0, 0)) / d[:, None]).mean(0)
            if rep < 10:
                assert np.allclose(z, (num[sampled].sum(0) / den[sampled].sum(0)[:, None]).mean(0), atol=1e-9, rtol=0)
            draws.append(z)
    assert len(draws) >= 1900
    point = (num.sum(0) / den.sum(0)[:, None]).mean(0)
    draws = np.asarray(draws)
    return [dict(metric=m, candidate_minus_current=float(point[i]), lower=float(np.quantile(draws[:, i], .025)),
                 upper=float(np.quantile(draws[:, i], .975)), replicates=len(draws),
                 qualification='Nominal whole-player clustered exposed-development interval, equal represented origins')
            for i, m in enumerate(['pa_mse', 'pa_mae', 'pa_bias', 'value_mse', 'value_mae', 'value_bias', 'brier', 'logloss'])]


def actual_from_dated_counts(q):
    """Reconstruct labels, not forecast inputs, from dated MLB source counts."""
    stints = pl.read_parquet(ROOT / 'reports/generated/practical-hitter-v31/dated-stints.parquet')
    assert stints['season'].max() == 2025
    columns = ['plate_appearances', 'strike_outs', 'unintentional_walks', 'hit_by_pitch',
               'singles', 'doubles', 'triples', 'home_runs']
    counts = stints.filter(pl.col('sport_id') == 1).group_by('player_id', 'season').agg(pl.col(columns).sum())
    counts = counts.with_columns((pl.col('plate_appearances') - pl.sum_horizontal(columns[1:])).alias('other'))
    names = ['other', *columns[1:]]
    assert not counts.filter(pl.col('other') < 0).height
    totals = counts.group_by('season').agg(pl.col('plate_appearances', *names).sum())
    env = {r['season']: np.array([r[k] for k in names], float) / r['plate_appearances'] for r in totals.iter_rows(named=True)}
    actual = q.select('row_id', 'player_id', 'target_year', 'next_pa').join(
        counts.rename({'season': 'target_year'}), on=['player_id', 'target_year'], how='left', validate='m:1').sort('row_id')
    assert not actual.filter(pl.col('plate_appearances').is_null() & (pl.col('next_pa') > 0)).height
    raw = actual.select(pl.col(names).fill_null(0)).to_numpy()
    assert np.array_equal(raw, q.select(['count_' + e for e in EVENTS]).to_numpy())
    n = raw.sum(1); assert np.array_equal(n, q['next_pa'].to_numpy())
    origin_env = np.array([env[y] for y in q['origin_year']])
    target_env = np.array([env[y] for y in q['target_year']])
    for arr, prefix in [(origin_env, 'origin_env_'), (target_env, 'target_env_')]:
        assert np.allclose(arr, q.select([prefix + e for e in EVENTS]), atol=1e-14, rtol=0)
    production = np.divide(raw @ VALUES, n, out=np.zeros(len(q)), where=n > 0)
    rate = np.where(n > 0, (production - target_env @ VALUES) * UNIT, 0.)
    value = n * (rate / 600 + q['origin_replacement_rate'].to_numpy())
    assert np.allclose(rate[n > 0], q['actual_future_relative_rate'].to_numpy()[n > 0], atol=1e-10, rtol=0)
    assert np.allclose(value, q['relative_value_label'], atol=1e-10, rtol=0)
    common = n * (np.where(n > 0, (production - origin_env @ VALUES) * UNIT, 0.) / 600 + q['origin_replacement_rate'].to_numpy())
    assert np.allclose(common, q['next_value'], atol=1e-10, rtol=0)
    return rate, value


def main():
    assert not (OUT / 'verification.json').exists(), 'Preserve completed review'
    pre = run.read(OUT / 'preflight.json'); run.verify(pre['input_hashes']); run.verify(run.read(OUT / 'fit-seal.json'))
    report = run.read(OUT / 'fit-report.json')
    assert sha256_file(OUT / 'predictions.parquet') == report['output_sha256']
    old = pl.read_parquet(run.OLD / 'features.parquet').sort('row_id')
    f = pl.read_parquet(OUT / 'features.parquet').sort('row_id')
    anchor = pl.read_parquet(run.ANCHOR).sort('row_id')
    q = pl.read_parquet(OUT / 'predictions.parquet').sort('row_id')
    assert q.height == 30506 and q.select(anchor.columns).equals(anchor)
    population = {(r['player_id'], r['origin_year']): r for r in pl.read_parquet(run.POP / 'population.parquet').to_dicts()}
    foreign = {(r['player_id'], r['origin_year']): r for r in run.read(run.FOREIGN / 'origin-inputs.json')['rows']}
    # Reconstruct every source correction without using the materializer.
    changed = {}
    for a, b in zip(old.iter_rows(named=True), f.iter_rows(named=True), strict=True):
        p = population[a['player_id'], a['origin_year']]; expected = dict(a)
        expected['on_40man'] = int(p['returned_40man'])
        codes = set(p['roster_position_codes'])
        explicit = codes & ({str(i) for i in range(2, 11)} | {'Y'})
        if a['source_position'] in {'UNKNOWN', 'X', 'I', 'O'} and len(explicit) == 1 and '1' not in codes and not p['roster_cross_team_conflict'] and not p['roster_status_conflict']:
            pos = next(iter(explicit)); expected['source_position'] = pos
            for code in [*[str(i) for i in range(1, 11)], 'Y', 'UNKNOWN']:
                expected['position_' + code] = int(code == pos)
        overseas = foreign.get((a['player_id'], a['origin_year']))
        if a['age_unknown'] and overseas and overseas['birth_date'] and overseas['dated_role_hint'] in {'hitter_hint', 'two_way_hint', 'two_way_or_conflicting_hints'}:
            age = (date(a['origin_year'], 12, 31) - date.fromisoformat(overseas['birth_date'])).days / 365.2425
            expected.update(age=age, age_unknown=0, age_centered=(age - 27) / 5, age_squared=((age - 27) / 5) ** 2)
        assert {k: b[k] for k in old.columns} == expected
        differences = {k: dict(old=a[k], new=b[k]) for k in old.columns if a[k] != b[k]}
        assert b['ctx_changed'] == bool(differences)
        if differences:
            changed[a['row_id']] = differences
    replayed = 0
    with threadpool_limits(limits=2):
        for c, note in zip(pre['cells'], report['cells'], strict=True):
            y, k = c['year'], c['fold']; assert (y, k) == (note['year'], note['fold'])
            run.verify(note['hashes'])
            te = f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            before = old.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            saved = q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            assert te['row_id'].equals(saved['row_id'])
            for kind, heads, data in [('current', c['old_heads'], before), ('ctx', note['heads'], te)]:
                raw = {}
                for h in heads:
                    m = joblib.load(h['path']); x = data.select(pre['features']).to_numpy()
                    raw[h['head']] = m.predict_proba(x)[:, 1] if h['head'] == 'participation' else m.predict(x)
                    name = ('preseason' if kind == 'current' else 'ctx') + ('_raw_p' if h['head'] == 'participation' else '_raw_conditional_pa')
                    assert np.allclose(raw[h['head']], saved[name], atol=1e-10, rtol=0); replayed += 1
                p, cond, pa = policy(raw, saved)
                prefix = 'preseason' if kind == 'current' else 'ctx'
                for arr, suffix in [(p, '_p'), (cond, '_conditional_pa'), (pa, '_pa')]:
                    assert np.allclose(arr, saved[prefix + suffix], atol=1e-10, rtol=0)
            assert saved['ctx_rate'].equals(saved['combined_rate'])
            assert np.allclose(saved['ctx_value'], saved['ctx_pa'] * (saved['combined_rate'] / 600 + saved['origin_replacement_rate']), atol=1e-10, rtol=0)
            print(f'Independent old/new head and product replays: {y}/{k}', flush=True)
    actual_rate, actual_value = actual_from_dated_counts(q)
    q = q.with_columns(pl.col('preseason_p').alias('current_p'), pl.col('preseason_pa').alias('current_pa'),
        pl.col('combined_value').alias('current_value'),
        pl.Series('actual_hitting_rate', actual_rate), pl.Series('actual_relative_value', actual_value))
    assert q.filter(pl.col('next_pa') == 0)['actual_relative_value'].sum() == 0
    public = q.filter((pl.col('pa_0') > 0) & pl.col('steamer_index').is_not_null() & pl.col('zips_index').is_not_null())
    assert public.height == 2627
    scopes = [('all', q), ('public', public), ('current_MLB', q.filter(pl.col('pa_0') > 0)),
        ('upper_never_debut', q.filter((pl.col('prior_debut') == 0) & (pl.col('stage') == 'Upper minors'))),
        ('lower_never_debut', q.filter((pl.col('prior_debut') == 0) & (pl.col('stage') == 'Lower minors'))),
        ('absent_prior_debut', q.filter((pl.col('prior_debut') == 1) & (pl.col('pa_0') == 0))),
        ('changed_context', q.filter(pl.col('ctx_changed'))), ('foreign_history', q.filter(pl.col('ctx_foreign_history_known')))]
    scopes += [('origin_' + str(y), q.filter(pl.col('origin_year') == y)) for y in sorted(q['origin_year'].unique())]
    scores, intervals = [], []
    with threadpool_limits(limits=2):
        for name, g in scopes:
            assert g.height > 0
            stats = {arm: score(g, arm) for arm in ['current', 'ctx']}
            scores.append(dict(scope=name, rows=g.height, people=g['player_id'].n_unique(), scores=stats,
                actual_pa=int(g['next_pa'].sum()), actual_appearances=int((g['next_pa'] > 0).sum()),
                actual_relative_value=float(g['actual_relative_value'].sum())))
            if not name.startswith('origin_'):
                intervals.append(dict(scope=name, intervals=interval(g)))
            print(f'Matched scores and uncertainty complete: {name}', flush=True)
    benchmark = []
    for column in ['steamer_pa', 'archive_steamer_pa']:
        e = public[column].to_numpy() - public['next_pa'].to_numpy(); years = public['origin_year'].to_numpy()
        m = np.mean([[np.mean(e[years == y] ** 2), np.mean(abs(e[years == y]))] for y in np.unique(years)], axis=0)
        benchmark.append(dict(column=column, rmse=float(np.sqrt(m[0])), mae=float(m[1])))
    initial = run.read(OUT / 'scores.json')
    for a, b in zip(initial, scores, strict=True):
        assert a['scope'] == b['scope'] and a['rows'] == b['rows'] and a['people'] == b['people']
        for arm in ['current', 'ctx']:
            for key in ['pa_rmse', 'pa_mae', 'pa_bias', 'brier', 'logloss', 'expected_pa', 'expected_appearances']:
                assert np.isclose(a['scores'][arm][key], b['scores'][arm][key], atol=1e-12, rtol=0)
    assert benchmark == run.read(OUT / 'public-benchmark.json')
    run.write('scores-relative.json', scores); run.write('intervals-relative.json', intervals)
    run.write('public-benchmark-relative-review.json', benchmark)
    q = q.with_columns(((pl.col('ctx_pa') - pl.col('next_pa')) ** 2).alias('ctx_pa_mse'),
        ((pl.col('current_pa') - pl.col('next_pa')) ** 2).alias('current_pa_mse'))
    chosen = {}
    def choose(g, why):
        assert g.height; chosen.setdefault(g['row_id'][0], []).append(why)
    for name, pid, origin in FIXED:
        g = q.filter((pl.col('player_id') == pid) & (pl.col('origin_year') == origin))
        assert g.height == 1, (name, pid, origin)
        assert population[pid, origin]['player_name'] == name
        choose(g, 'fixed before fitting')
    gain = q.with_columns((pl.col('current_pa_mse') - pl.col('ctx_pa_mse')).alias('gain'))
    choose(gain.sort('gain', descending=True), 'largest PA squared-error gain')
    choose(gain.sort('gain'), 'largest PA squared-error harm')
    misses = q.with_columns((pl.col('ctx_pa') - pl.col('next_pa')).alias('error'))
    choose(misses.sort('error', descending=True), 'major false high')
    choose(misses.sort('error'), 'major false low')
    choose(misses.filter(pl.col('next_pa').is_between(200, 600)).sort(pl.col('error').abs()), 'ordinary active forecast')
    counts = pl.read_parquet(ROOT / 'reports/generated/practical-hitter-v31/counts.parquet')
    support = pl.read_parquet(OUT / 'profile-support.parquet')
    cases = []
    with threadpool_limits(limits=2):
        for rid, selection in chosen.items():
            r = q.filter(pl.col('row_id') == rid).row(0, named=True); y, k = r['origin_year'], r['outer_fold']
            a = old.filter(pl.col('row_id') == rid); b = f.filter(pl.col('row_id') == rid)
            c = next(c for c in pre['cells'] if c['year'] == y and c['fold'] == k)
            n = run.read(OUT / f'fit-{y}-{k}.json'); paths = {}; probe = {}
            for arm, heads, data in [('current', c['old_heads'], a), ('ctx', n['heads'], b)]:
                paths[arm] = {}
                for h in heads:
                    m = joblib.load(h['path']); x = data.select(pre['features']).to_numpy()[0]
                    paths[arm][h['head']] = logit_trace(m, x, pre['features']) if h['head'] == 'participation' else trace(m, x, pre['features'])
                    if arm == 'ctx':
                        bx = a.select(pre['features']).to_numpy()
                        probe[h['head']] = m.predict_proba(bx)[:, 1] if h['head'] == 'participation' else m.predict(bx)
            one = q.filter(pl.col('row_id') == rid)
            pp, pc, probe_pa = policy(probe, one)
            peers = q.filter((pl.col('origin_year') == y) & (pl.col('prior_debut') == r['prior_debut']) &
                (pl.col('stage') == r['stage']) & (pl.col('player_id') != r['player_id'])).join(
                    f.select('row_id', pl.col('age').alias('corrected_age'), pl.col('on_40man').alias('dated_listing')), on='row_id', validate='1:1')
            now = b.row(0, named=True)
            peers = peers.with_columns((((pl.col('corrected_age') - now['age']) / 3) ** 2 +
                ((pl.col('pa_0') - r['pa_0']) / 250) ** 2 + ((pl.col('minor_pa_0') - r['minor_pa_0']) / 250) ** 2 +
                (pl.col('dated_listing') != now['on_40man']).cast(pl.Float64)).alias('distance')).sort('distance', 'player_id').head(4)
            opportunity = (r['next_pa'] - r['ctx_pa']) * (r['combined_rate'] / 600 + r['origin_replacement_rate'])
            hitting = r['next_pa'] * (r['actual_hitting_rate'] - r['combined_rate']) / 600
            assert np.isclose(r['actual_relative_value'] - r['ctx_value'], opportunity + hitting, atol=1e-10)
            cases.append(dict(name=r['player_name'] or population[r['player_id'], y]['player_name'], original_saved_name=r['player_name'], player_id=r['player_id'], origin_year=y, selection=selection,
                information_date=c['information_date'], actual_dated_context=population[r['player_id'], y],
                own_source_changes=changed.get(rid, {}),
                actual_domestic_history=counts.filter((pl.col('player_id') == r['player_id']) & pl.col('season').is_between(y - 2, y)).sort('season', 'bucket').to_dicts(),
                foreign_history_not_used_in_this_fit=foreign.get((r['player_id'], y)),
                old_inputs=a.select(pre['features']).row(0, named=True), new_inputs=b.select(pre['features']).row(0, named=True),
                head_traces=paths, profile_support=support.filter(pl.col('row_id') == rid).to_dicts(),
                forecasts=dict(current_p=r['current_p'], current_conditional_pa=r['preseason_conditional_pa'], current_pa=r['current_pa'],
                    ctx_p=r['ctx_p'], ctx_conditional_pa=r['ctx_conditional_pa'], ctx_pa=r['ctx_pa'], fixed_hitting_rate=r['combined_rate'],
                    current_value=r['current_value'], ctx_value=r['ctx_value'], actual_pa=r['next_pa'], actual_hitting_rate=r['actual_hitting_rate'],
                    actual_relative_value=r['actual_relative_value'], opportunity_miss=opportunity, hitting_miss=hitting),
                candidate_same_fit_old_input_probe=dict(p=float(pp[0]), conditional_pa=float(pc[0]), pa=float(probe_pa[0]),
                    own_input_effect=float(r['ctx_pa'] - probe_pa[0]), refit_effect=float(probe_pa[0] - r['current_pa']),
                    interpretation='Mechanics only, not a new validated forecast or causal effect'),
                origin_only_peer_selection='same origin/stage/prior debut, nearest age/exposure/dated listing; no future results in distance',
                peers=peers.select('player_name', 'player_id', 'corrected_age', 'dated_listing', 'pa_0', 'minor_pa_0', 'distance', 'current_pa', 'ctx_pa', 'next_pa').to_dicts()))
    run.write('reviewed-cases.json', dict(cases=cases, player_walkthrough_status='pending_manual_baseball_review'))
    lines = ['# Corrected preseason context player walkthrough', '',
        'This tests playing time only. Hitting stays fixed. Actual outcomes below are diagnostics, not forecast inputs. Node-path terms explain arithmetic, not causal effects. Own-source changes and global refitting effects are distinguished with a same-fit old-input probe.', '']
    for c in cases:
        z = c['forecasts']; probe = c['candidate_same_fit_old_input_probe']
        lines += [f"## {c['name']} before {c['origin_year'] + 1}", '',
            'Selection: ' + ', '.join(c['selection']) + '.', '',
            'Actual source changes: ' + json.dumps(c['own_source_changes'], ensure_ascii=False) + '.', '',
            'Dated domestic component counts: ' + json.dumps(c['actual_domestic_history'], ensure_ascii=False) + '.', '',
            f"Original forecast {z['current_pa']:.2f} PA (p={z['current_p']:.4f}, conditional={z['current_conditional_pa']:.2f}); corrected context {z['ctx_pa']:.2f} PA (p={z['ctx_p']:.4f}, conditional={z['ctx_conditional_pa']:.2f}); actual {z['actual_pa']} PA. Fixed hitting estimate {z['fixed_hitting_rate']:.4f} custom batting wins/600; actual conditional hitting {z['actual_hitting_rate']:.4f}.", '',
            f"Same fitted candidate with old own inputs gives {probe['pa']:.2f} PA. Own input mechanics account for {probe['own_input_effect']:+.2f} PA; changing the fitted model accounts for {probe['refit_effect']:+.2f}. This is a diagnostic decomposition, not causal attribution or a new forecast arm.", '',
            f"Delivered relative contribution: old {z['current_value']:+.4f}, new {z['ctx_value']:+.4f}, actual {z['actual_relative_value']:+.4f}. Actual-minus-predicted decomposes into opportunity {z['opportunity_miss']:+.4f} and hitting {z['hitting_miss']:+.4f}; the two can offset.", '',
            'Actual held-player training profile support: ' + json.dumps(c['profile_support']) + '.', '',
            'Outcome-blind peers: ' + json.dumps(c['peers'], ensure_ascii=False) + '.', '',
            'Exact old/new inputs and all head terms are saved in reviewed-cases.json. Foreign counts, if present there, were not used in this fit. Missing listing is not retirement; any remaining foreign-history gap is not zero talent.', '']
    omitted = []
    for pid, y in [(660271, 2017), (673548, 2021), (807799, 2022), (808982, 2023)]:
        assert not anchor.filter((pl.col('player_id') == pid) & (pl.col('origin_year') == y)).height
        omitted.append(dict(player_id=pid, origin_year=y, source_context=population[pid, y],
            foreign_inputs=foreign[pid, y], original_forecast=None, new_forecast=None, additions_comparison_pending=True))
    run.write('omitted-foreign-cases.json', dict(cases=omitted))
    lines += ['## Omitted international entrants remain unfinished', '',
        'Ohtani before 2018, Suzuki before 2022, Yoshida before 2023 and Lee before 2024 are source additions with dated context and foreign counts but no old forecast. This matched original-row test cannot repair their missing forecasts. The separate additions/translation comparison is still required; none is counted as a correct zero here.', '']
    (OUT / 'player-walkthrough.md').write_text('\n'.join(lines).rstrip() + '\n', encoding='utf8', newline='\n')
    hashes = {str(p): sha256_file(p) for p in [OUT / 'predictions.parquet', OUT / 'scores-relative.json', OUT / 'intervals-relative.json',
        OUT / 'public-benchmark-relative-review.json', OUT / 'reviewed-cases.json', OUT / 'omitted-foreign-cases.json', OUT / 'player-walkthrough.md', Path(__file__), AMENDMENT, ROOT / 'scripts/review_hitter_dated_context.py',
        OUT / 'scores.json', OUT / 'intervals.json', OUT / 'public-benchmark.json',
        ROOT / 'reports/generated/practical-hitter-v31/dated-stints.parquet']}
    result = dict(source_rows_reconstructed=old.height, source_changes=len(changed), old_new_head_replays=replayed,
        all_original_forecasts_preserved=True, hitting_unchanged=True, source_column_changes=dict(Counter(k for v in changed.values() for k in v)),
        public_rows=public.height, cases=len(cases), same_fit_diagnostic_probes=len(cases),
        new_foreign_forecasts=0, player_walkthrough_status='pending_manual_baseball_review',
        deployment_approved=False, hashes=hashes)
    run.write('verification.json', result)
    PUBLIC.mkdir(parents=True, exist_ok=True)
    for name in ['scores-relative.json', 'intervals-relative.json', 'public-benchmark-relative-review.json', 'verification.json', 'player-walkthrough.md']:
        assert not (PUBLIC / name).exists()
        (PUBLIC / name).write_bytes((OUT / name).read_bytes())
    print(json.dumps({k: v for k, v in result.items() if k != 'hashes'}), flush=True)


if __name__ == '__main__':
    main()
