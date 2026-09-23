"""Identity-balanced empirical paths. Separate fitted distribution from simulation."""
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from .player_path_distribution import age_groups, path_events, EVENTS, summarize_draws


def identity_split(ids, seed=417):
    unique, inverse = np.unique(ids, return_inverse=True)
    half = np.zeros(len(unique), bool)
    half[np.random.default_rng(seed).permutation(len(unique))[:len(unique)//2]] = True
    return half[inverse]


def identity_ess(ids, weights):
    _, inverse = np.unique(ids, return_inverse=True)
    mass = np.bincount(inverse, weights=weights)
    return float(mass.sum()**2/(mass@mass))


def fitted_weights(train, test, features, horizon, method):
    """Exact mixture weights; no simulation seed can change the fitted forest."""
    ids, query = train['player_id'].to_numpy(), test['player_id'].to_numpy()
    row_weight = train['identity_weight'].to_numpy()
    weights = np.zeros((test.height, train.height), dtype=np.float32)
    notes = {'splits': [], 'node_identity_count': [], 'node_identity_ess': [], 'fallback_nodes': 0}
    if method == 'B0':
        stages, ages = train['stage'].to_numpy(), age_groups(train['age'].to_numpy())
        for i, (pid, stage, age) in enumerate(test.select('player_id','stage','age').iter_rows()):
            allowed = ids != pid
            pool = np.flatnonzero(allowed & (stages == stage) & (ages == age_groups([age])[0]))
            if len(pool) < 40:
                pool = np.flatnonzero(allowed & (stages == stage))
            if len(pool) < 40:
                pool = np.flatnonzero(allowed)
            if not len(pool):
                raise ValueError('No donors')
            weights[i, pool] = 1/len(pool)
    else:
        x = np.nan_to_num(train.select(features).to_numpy())
        tx = np.nan_to_num(test.select(features).to_numpy())
        y = train.select([f'war_h{h}' for h in range(1,horizon+1)]).to_numpy()
        if not np.isfinite(y).all():
            raise ValueError('Incomplete paths')
        half = identity_split(ids)
        for side in (False, True):
            structure, donors = np.flatnonzero(half == side), np.flatnonzero(half != side)
            if len(np.unique(ids[donors])) < 21:
                raise ValueError('Insufficient independent donor support')
            model = RandomForestRegressor(n_estimators=100, max_depth=8, min_samples_leaf=40,
                max_features=.7, bootstrap=False, random_state=417, n_jobs=4)
            kwargs = {'sample_weight':row_weight[structure]} if method == 'A1' else {}
            model.fit(x[structure], y[structure], **kwargs)
            overlap = len(np.intersect1d(ids[structure],ids[donors]))
            assert overlap == 0
            notes['splits'].append({'structure_players':len(np.unique(ids[structure])),
                'donor_players':len(np.unique(ids[donors])), 'overlap':overlap})
            for tree in model.estimators_:
                path = tree.decision_path(x[donors]).tocsc()
                parent = np.full(tree.tree_.node_count,-1,int)
                for node,(left,right) in enumerate(zip(tree.tree_.children_left, tree.tree_.children_right)):
                    if left >= 0:
                        parent[left] = parent[right] = node
                leaves = tree.apply(tx)
                for leaf in np.unique(leaves):
                    node = int(leaf)
                    while True:
                        pool = donors[path.indices[path.indptr[node]:path.indptr[node+1]]]
                        if len(np.unique(ids[pool])) >= 21 or parent[node] < 0:
                            break
                        node = parent[node]
                    notes['fallback_nodes'] += int(node != leaf)
                    notes['node_identity_count'].append(len(np.unique(ids[pool])))
                    notes['node_identity_ess'].append(identity_ess(ids[pool],row_weight[pool]))
                    mass = row_weight[pool]/row_weight[pool].sum()
                    rows = np.flatnonzero(leaves == leaf)
                    # Exclude the query separately within every tree, as v1 rejection sampling does.
                    for i in rows:
                        keep = ids[pool] != query[i]
                        weights[i,pool[keep]] += mass[keep]/mass[keep].sum()/200
    weights /= weights.sum(axis=1,keepdims=True)
    for i,pid in enumerate(query):
        assert not weights[i,ids==pid].any()
    for key in ('node_identity_count','node_identity_ess'):
        a = notes[key]
        notes[key] = {str(q):float(np.quantile(a,q)) for q in (0,.1,.5,.9,1)} if a else None
    notes['self_donors'] = 0
    notes['mean_identity_ess'] = float(np.mean([identity_ess(ids,w) for w in weights]))
    notes['mean_same_stage_mass'] = float(np.mean([
        w[train['stage'].to_numpy()==s].sum() for w,s in zip(weights,test['stage'].to_numpy())]))
    return weights, notes


def sample_weights(weights, draws, seed):
    rng = np.random.default_rng(seed)
    out = np.empty((len(weights),draws),dtype=np.int32)
    for i,w in enumerate(weights):
        cdf = np.cumsum(w,dtype=float)
        cdf /= cdf[-1]
        out[i] = np.searchsorted(cdf,rng.random(draws),side='right')
    return out


def exact_summary(weights, war, pa, actual_war=None, actual_pa=None):
    """Means, event scores and CRPS integrated over the entire forest distribution."""
    total = war.sum(axis=1)
    events = path_events(war,pa).astype(float)
    out = {'mean_batting':weights@total,'mean_pa':weights@pa.sum(axis=1)}
    for h in range(war.shape[1]):
        out[f'mean_batting_h{h+1}'] = weights@war[:,h]
        out[f'mean_pa_h{h+1}'] = weights@pa[:,h]
    for j,e in enumerate(EVENTS):
        out['p_'+e] = weights@events[:,j]
    if actual_war is not None:
        actual = actual_war.sum(axis=1)
        order = np.argsort(total)
        values = total[order]
        scores = []
        for w,y in zip(weights,actual):
            v = w[order].astype(float); v /= v.sum()
            scores.append(float(v@np.abs(values-y)-np.sum(v*values*(2*np.cumsum(v)-v-1))))
        out.update(actual_batting=actual,actual_pa=actual_pa.sum(axis=1),crps=np.array(scores),
                   mse=(out['mean_batting']-actual)**2)
        truth = path_events(actual_war,actual_pa)
        for j,e in enumerate(EVENTS):
            p = out['p_'+e]
            clipped = np.clip(p,.5/401,1-.5/401)
            out['actual_'+e] = truth[:,j].astype(int)
            out['brier_'+e] = (p-truth[:,j])**2
            out['log_'+e] = -(truth[:,j]*np.log(clipped)+(1-truth[:,j])*np.log1p(-clipped))
    return out


def iid_summary(war, pa, actual_war=None, actual_pa=None):
    """Unbiased IID CRPS/Brier/mean-MSE estimators; log uses a fixed clipping rule."""
    out = summarize_draws(war,pa,actual_war,actual_pa)
    if actual_war is None:
        return out
    n = war.shape[1]
    total = war.sum(axis=2)
    sorted_total = np.sort(total,axis=1)
    out['crps'] = np.abs(total-actual_war.sum(axis=1)[:,None]).mean(axis=1) - (
        sorted_total*(2*np.arange(n)+1-n)).sum(axis=1)/(n*(n-1))
    out['mse'] -= total.var(axis=1,ddof=1)/n
    # Disjoint pairs are independent IID draws: unbiased energy, O(n), no self-pair bias.
    out['energy'] = np.linalg.norm(war-actual_war[:,None,:],axis=2).mean(axis=1) - .5*np.linalg.norm(
        war[:,:n//2]-war[:,n//2:2*(n//2)],axis=2).mean(axis=1)
    for e in EVENTS:
        p, actual = out['p_'+e], out['actual_'+e]
        out['brier_'+e] -= p*(1-p)/(n-1)
        p = np.clip(p,.5/401,1-.5/401)
        out['log_'+e] = -(actual*np.log(p)+(1-actual)*np.log1p(-p))
    return out
