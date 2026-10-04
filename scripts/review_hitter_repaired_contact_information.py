"""Actual source, saved-linear-head and outcome walks before disposition."""
import sys
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.hitter_numeric_history import BUCKETS
from universal_baseball.practical_hitter_v30 import EVENTS
from universal_baseball.storage import sha256_file
import evaluate_hitter_repaired_contact_information as e


def peers(f, q, r):
    g = f.filter((pl.col('origin_year') == r['origin_year']) & (pl.col('stage') == r['stage']) &
                 (pl.col('prior_debut') == r['prior_debut']) & (pl.col('player_id') != r['player_id']))
    restrictions = []
    for col in ['source_position', 'new_draftee', 'draft_college']:
        sub = g.filter(pl.col(col) == r[col])
        if sub.height >= 4:
            g = sub; restrictions.append(col)
    dimensions = [('age', 4.), ('draft_known', 1.), ('draft_rank', .2),
                  ('scout_rank_score_0', .3), ('career_mlb_observed_pa', 3000.), ('quality_0', 1.)]
    dimensions += [(f'{b}_{lag}_pa', 200.) for b in BUCKETS for lag in range(3)]
    # Rates contribute only when both have exposure at the level; absence is not bad hitting.
    distance = sum(((pl.col(c) - r[c]) / scale) ** 2 for c, scale in dimensions)
    for b in BUCKETS:
        if r[f'pooled_{b}_pa'] > 0:
            for ev in ['K', 'BB', 'HR', 'BABIP']:
                c = f'pooled_{b}_{ev}'
                distance += pl.when(pl.col(f'pooled_{b}_pa') > 0).then(((pl.col(c) - r[c]) / .1) ** 2).otherwise(0)
    selected = g.with_columns(distance.alias('origin_distance')).sort('origin_distance', 'player_id').head(4)
    assert selected.height == 4
    columns = ['row_id', 'player_id', 'player_name', 'age', 'source_position', 'draft_known', 'pick_number',
               'draft_college', 'scout_rank_score_0', 'origin_distance', *[f'{b}_0_pa' for b in BUCKETS]]
    result = selected.select(columns).join(q.select('row_id', 'preseason_pa', 'translated_ridge_rate',
             'joint_rate', 'joint_all_rate', 'next_pa', 'next_relative_rate', 'next_value'), on='row_id', validate='1:1')
    return dict(restrictions=restrictions, rate_dimensions='K, BB, HR and BABIP at mutually exposed levels',
                selection='Own-origin age, draft, rank, performance and three separate level-exposure years; no future outcome in distance',
                cases=result.to_dicts())


def extract():
    assert not (e.OUT / 'cases.json').exists(), 'Preserve selected cases'
    pre = e.read(e.OUT / 'preflight.json'); e.verify_inputs(pre)
    verification = e.read(e.OUT / 'verification.json')
    assert sha256_file(e.Path(verification['scored_path'])) == verification['scored_sha256']
    q = pl.read_parquet(verification['scored_path']).sort('row_id')
    selected = {}
    def choose(g, reason):
        assert g.height > 0
        selected.setdefault(g['row_id'][0], []).append(reason)
    for pid, y in e.FIXED:
        choose(q.filter((pl.col('player_id') == pid) & (pl.col('origin_year') == y)), 'fixed before fit')
    never = q.filter(pl.col('prior_debut') == 0)
    for a in e.ARMS:
        error = never.with_columns(((pl.col('translated_ridge_value') - pl.col('next_value')) ** 2 -
                                   (pl.col(a + '_value') - pl.col('next_value')) ** 2).alias('gain'),
                                  (pl.col(a + '_value') - pl.col('next_value')).alias('error'))
        for why, sub in [('gain', error.sort('gain', descending=True)), ('harm', error.sort('gain')),
                         ('false high', error.sort('error', descending=True)), ('false low', error.sort('error')),
                         ('ordinary active', error.filter(pl.col('next_pa').is_between(100, 600)).sort(pl.col('error').abs()))]:
            choose(sub, a + ' largest ' + why if why != 'ordinary active' else a + ' ordinary active')
    active = never.filter(pl.col('next_pa') > 0).with_columns(
        ((pl.col('translated_ridge_rate') - pl.col('next_relative_rate')) ** 2 -
         (pl.col('joint_rate') - pl.col('next_relative_rate')) ** 2).alias('gain'))
    choose(active.sort('gain', descending=True), 'joint largest active-rate gain')
    choose(active.sort('gain'), 'joint largest active-rate harm')
    measured = never.filter(pl.col('dc_available') > 0)
    if not any(q.filter(pl.col('row_id') == rid)['stage'][0] == 'Lower minors' for rid in selected):
        choose(measured.filter(pl.col('stage') == 'Lower minors').sort('dc_classified_exposure', descending=True), 'lower-stage source-coverage control')
    counts = pl.read_parquet(e.bridge.COUNTS)
    contact = pl.concat([pl.read_parquet(e.SOURCE / f'cell-features-{y}.parquet') for y in e.info.YEARS])
    support = pl.read_parquet(e.WORK / 'profiles.parquet')
    cases = []
    with threadpool_limits(limits=2):
        for k in range(5):
            f = e.bridge.previous.tagged(e.full(k))
            for rid, reasons in selected.items():
                row = f.filter(pl.col('row_id') == rid)
                if row['outer_fold'][0] != k: continue
                r = q.filter(pl.col('row_id') == rid).row(0, named=True)
                source_row = row.row(0, named=True)
                note = e.read(e.OUT / f"fit-{r['origin_year']}-{k}.json")
                traces = {}
                for h in note['heads']:
                    assert sha256_file(e.Path(h['path'])) == h['sha256']
                    a = h['arm']; cols = pre['features'][a]; model = joblib.load(h['path'])
                    x = e.safe_matrix(row, cols)[0]; terms = x * model.coef_
                    predicted = float(model.intercept_ + terms.sum())
                    assert np.isclose(predicted, r[a + '_raw_rate'], atol=1e-10, rtol=0)
                    parts = {block: float(sum(t for c, t in zip(cols, terms) if c in names))
                             for block, names in [('coverage', e.info.COVERAGE), ('mix', e.info.SHAPE), ('detail', e.info.DETAIL)]}
                    neutral = x.copy()
                    for j, c in enumerate(cols):
                        if c in e.info.DETAIL: neutral[j] = 0
                    probe = float(model.predict(neutral[None, :])[0])
                    assert np.isclose(probe, predicted - parts['detail'], atol=1e-10, rtol=0)
                    traces[a] = dict(intercept=float(model.intercept_), raw_prediction=predicted,
                        primary_prediction=r[a + '_rate'], all_player_prediction=r[a + '_all_rate'],
                        primary_applied=bool(r['prior_debut'] == 0 and r['dc_available'] and r['dc_supported_fold']),
                        block_contributions=parts, neutral_detail_probe=probe,
                        interpretation='Exact within-fit linear sum; not the total change between refitted models or a causal effect',
                        effects=sorted([dict(feature=c, raw_input=source_row[c], scaled_input=float(v), coefficient=float(b), effect=float(t))
                                        for c, v, b, t in zip(cols, x, model.coef_, terms)], key=lambda z: abs(z['effect']), reverse=True))
                history = counts.filter((pl.col('player_id') == r['player_id']) & pl.col('season').is_between(r['origin_year'] - 2, r['origin_year']))
                measures = contact.filter((pl.col('player_id') == r['player_id']) & pl.col('season').is_between(r['origin_year'] - 2, r['origin_year']))
                rate_actual = r['next_relative_rate'] if r['next_pa'] > 0 else None
                outputs = {a: {c: r[a + '_' + c] for c in ['rate', 'pa', 'value']}
                           for a in ['preseason', 'translated_ridge', *e.ARMS, *[a + '_all' for a in e.ARMS]]}
                cases.append(dict(row_id=rid, player_id=r['player_id'], player_name=r['player_name'], origin_year=r['origin_year'],
                    target_year=r['target_year'], outer_fold=k, selection=reasons,
                    information_date=next(c['information_date'] for c in pre['cells'] if c['year'] == r['origin_year'] and c['fold'] == k),
                    age=r['age'], stage=r['stage'], prior_debut=r['prior_debut'],
                    pedigree={c: source_row[c] for c in ['draft_known', 'pick_number', 'draft_college', 'draft_hs', 'draft_jc', 'draft_elapsed', 'scout_rank_score_0']},
                    source_history=history.sort('season', 'bucket').to_dicts(),
                    contact_history=[{key: value for key, value in s.items() if not key.startswith('rate_') and (not key.startswith('count_') or value != 0)}
                                     for s in measures.sort('season', 'league_id').to_dicts()],
                    actual_MLB_history=counts.filter((pl.col('player_id') == r['player_id']) & (pl.col('season') == r['target_year']) & (pl.col('bucket') == 'MLB')).to_dicts(),
                    contact_inputs=row.select(e.info.FEATURES + ['dc_physical_exposure', 'dc_classified_exposure', 'dc_actual_leagues', 'dc_source_seasons']).to_dicts()[0],
                    forecasts=outputs, arrival_probability=r['preseason_p'], conditional_pa=r['preseason_conditional_pa'],
                    actual=dict(pa=r['next_pa'], rate=rate_actual, value=r['next_value']),
                    supported_fold=r['dc_supported_fold'], active_profile_support=support.filter(pl.col('row_id') == rid).to_dicts(),
                    linear_traces=traces, peers=peers(f, q, source_row),
                    probe_limit='Uniform outcomes within the same contact type at unchanged exposure; possibly artificial. Mechanics only, not a new forecast.'))
    paths = [e.OUT / 'preflight.json', e.OUT / 'verification.json', e.Path(verification['scored_path']),
             e.Path(__file__), e.bridge.COUNTS, e.WORK / 'profiles.parquet', *[e.SOURCE / f'cell-features-{y}.parquet' for y in e.info.YEARS]]
    e.write('cases.json', dict(player_walkthrough_status='pending', cases=cases,
            input_hashes={str(p): sha256_file(p) for p in paths}))
    for c in cases:
        print(c['player_name'], c['origin_year'], c['selection'],
              {a: round(c['forecasts'][a]['rate'], 3) for a in ['preseason', 'translated_ridge', *e.ARMS]},
              'actual', c['actual'], 'support', [s['active_profile_people'] for s in c['active_profile_support']], flush=True)


if __name__ == '__main__':
    {'extract': extract}[sys.argv[1]]()
