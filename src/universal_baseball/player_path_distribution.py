"""Empirical joint player paths: honest donor forests and proper-score helpers."""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import RandomForestRegressor

EVENTS = ('no_mlb', 'regular_workload', 'substantial_batting', 'sustained_high_batting')


def age_groups(age):
    a = np.asarray(age, float)
    return np.where(~np.isfinite(a), -1, np.where(a <= 18, 0, np.where(a <= 22, 1, np.where(a <= 26, 2, 3))))


def path_events(war, pa):
    war, pa = np.asarray(war), np.asarray(pa)
    if war.shape != pa.shape or not np.isfinite(war).all() or not np.isfinite(pa).all():
        raise ValueError('Expected matching complete path arrays')
    return np.stack([(pa <= 0).all(axis=-1), (pa >= 450).sum(axis=-1) >= 2,
                     war.sum(axis=-1) >= 6, (war >= 4).sum(axis=-1) >= 2], axis=-1)


def coarse_draws(train, test, draws=400, seed=417):
    """One complete donor trajectory per draw; never donate the query itself."""
    rng = np.random.default_rng(seed)
    ids, stages = train['player_id'].to_numpy(), train['stage'].to_numpy()
    ages = age_groups(train['age'].to_numpy())
    out = np.empty((test.height, draws), dtype=np.int32)
    for i, (pid, stage, age) in enumerate(test.select('player_id', 'stage', 'age').iter_rows()):
        eligible = ids != pid
        pool = np.flatnonzero(eligible & (stages == stage) & (ages == age_groups([age])[0]))
        if len(pool) < 40:
            pool = np.flatnonzero(eligible & (stages == stage))
        if len(pool) < 40:
            pool = np.flatnonzero(eligible)
        if not len(pool):
            raise ValueError('No independent donors')
        out[i] = rng.choice(pool, draws)
    return out


def forest_draws(train, test, features, horizon, draws=400, seed=417):
    """Two-fold honest forests; each tree supplies two whole-path donors."""
    if draws != 400 or train['player_id'].n_unique() != train.height:
        raise ValueError('Expected 400 draws and one snapshot per training player')
    x, tx = train.select(features).to_numpy(), test.select(features).to_numpy()
    x, tx = np.nan_to_num(x), np.nan_to_num(tx)
    y = train.select([f'war_h{h}' for h in range(1, horizon+1)]).to_numpy()
    if not np.isfinite(y).all():
        raise ValueError('Unobserved training paths')
    rng = np.random.default_rng(seed)
    order = rng.permutation(train.height)
    half = np.zeros(train.height, bool)
    half[order[:train.height//2]] = True
    ids = train['player_id'].to_numpy()
    query_ids = test['player_id'].to_numpy()
    out = np.empty((test.height, draws), np.int32)
    notes = []
    for side in (False, True):
        structure, donors = np.flatnonzero(half == side), np.flatnonzero(half != side)
        model = RandomForestRegressor(n_estimators=100, max_depth=8, min_samples_leaf=40,
            max_features=.7, bootstrap=False, random_state=seed, n_jobs=4)
        model.fit(x[structure], y[structure])
        notes.append({'structure_players': len(structure), 'donor_players': len(donors),
                      'overlap': int(len(np.intersect1d(ids[structure], ids[donors])))})
        for t, tree in enumerate(model.estimators_):
            path = tree.decision_path(x[donors]).tocsc()
            parent = np.full(tree.tree_.node_count, -1, int)
            for n, (left, right) in enumerate(zip(tree.tree_.children_left, tree.tree_.children_right)):
                if left >= 0:
                    parent[left] = parent[right] = n
            leaves = tree.apply(tx)
            for leaf in np.unique(leaves):
                node = int(leaf)
                while path.indptr[node+1]-path.indptr[node] < 21 and parent[node] >= 0:
                    node = parent[node]
                pool = donors[path.indices[path.indptr[node]:path.indptr[node+1]]]
                rows = np.flatnonzero(leaves == leaf)
                picked = rng.choice(pool, (len(rows), 2))
                bad = ids[picked] == query_ids[rows, None]
                while bad.any():
                    picked[bad] = rng.choice(pool, int(bad.sum()))
                    bad = ids[picked] == query_ids[rows, None]
                col = int(side)*200 + 2*t
                out[rows, col:col+2] = picked
    if (ids[out] == query_ids[:, None]).any():
        raise AssertionError('Self donor')
    return out, notes


def crps(samples, actual):
    """Exact CRPS of the finite equal-weight empirical distribution."""
    s = np.sort(np.asarray(samples), axis=1)
    n = s.shape[1]
    return np.abs(s-np.asarray(actual)[:, None]).mean(axis=1) - (s*(2*np.arange(n)+1-n)).sum(axis=1)/(n*n)


def energy_score(paths, actual):
    """Fixed independent path-pair Monte Carlo energy score, in annual wins."""
    p = np.asarray(paths)
    pairs = np.random.default_rng(9417).integers(p.shape[1], size=(2, 400))
    return np.linalg.norm(p-np.asarray(actual)[:, None, :], axis=2).mean(axis=1) - .5*np.linalg.norm(p[:, pairs[0]]-p[:, pairs[1]], axis=2).mean(axis=1)


def summarize_draws(war, pa, actual_war=None, actual_pa=None):
    wc, pc = war.sum(axis=2), pa.sum(axis=2)
    ev = path_events(war, pa)
    out = {'mean_batting': wc.mean(axis=1), 'mean_pa': pc.mean(axis=1)}
    for name, values in [('batting', wc), ('pa', pc)]:
        q = np.quantile(values, [.1, .5, .9], axis=1)
        for j, label in enumerate(('p10', 'p50', 'p90')):
            out[f'{name}_{label}'] = q[j]
    for j, name in enumerate(EVENTS):
        out['p_'+name] = ev[:, :, j].mean(axis=1)
    for h in range(war.shape[2]):
        out[f'mean_batting_h{h+1}'] = war[:, :, h].mean(axis=1)
        out[f'mean_pa_h{h+1}'] = pa[:, :, h].mean(axis=1)
    if actual_war is not None:
        actual = actual_war.sum(axis=1)
        out.update(actual_batting=actual, actual_pa=actual_pa.sum(axis=1),
            crps=crps(wc, actual), mse=(out['mean_batting']-actual)**2,
            energy=energy_score(war, actual_war),
            coverage80=((actual >= out['batting_p10']) & (actual <= out['batting_p90'])).astype(float),
            width80=out['batting_p90']-out['batting_p10'])
        ae = path_events(actual_war, actual_pa)
        for j, name in enumerate(EVENTS):
            p = np.clip(out['p_'+name], .5/(war.shape[1]+1), 1-.5/(war.shape[1]+1))
            out['actual_'+name] = ae[:, j].astype(int)
            out['brier_'+name] = (out['p_'+name]-ae[:, j])**2
            out['log_'+name] = -(ae[:, j]*np.log(p)+(1-ae[:, j])*np.log1p(-p))
    return out
