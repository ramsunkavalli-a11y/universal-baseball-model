"""Native MLB framing quality, not innings-scaled catching contribution."""
from collections import defaultdict

import numpy as np

from universal_baseball.defense_native_range import player_weights

FEATURES=('history_rate','reliability','age_c','age_sq','age_missing','history_x_reliability')


def features(r):
    c=((r['age'] if r['age'] is not None else 27)-27)/10
    return dict(history_rate=r['history_rate'],reliability=r['reliability'],
                age_c=c,age_sq=c*c,age_missing=r['age'] is None,
                history_x_reliability=r['history_rate']*r['reliability'])


def matrix(rows):
    return np.array([[float(features(r)[c]) for c in FEATURES] for r in rows],dtype=float).reshape(len(rows),len(FEATURES))


def profile(r):
    age=r['age'];n=r['history_pitches']
    return ('unknown' if age is None else '<=24' if age<=24 else '25-29' if age<=29 else '30+',
            '<1000' if n<1000 else '1000-5999' if n<6000 else '6000+')


def preflight(train,test,origin,fold):
    assert all(r['window_end']<=origin and r['quality_rate'] is not None and r['player_id']%5!=fold for r in train)
    assert all(r['origin_year']==origin and r['player_id']%5==fold for r in test)
    assert {r['player_id'] for r in train}.isdisjoint(r['player_id'] for r in test)
    for rows in (train,test):
        assert len({(r['origin_year'],r['player_id']) for r in rows})==len(rows)
        assert np.isfinite(matrix(rows)).all()
    counts=defaultdict(set)
    for r in train:
        counts[profile(r)].add(r['player_id'])
    people=len({r['player_id'] for r in train});origins=sorted({r['origin_year'] for r in train})
    return dict(origin=origin,fold=fold,training_people=people,training_rows=len(train),training_origins=origins,
                fit_allowed=people>=40 and len(origins)>=2,
                train_keys=[[r['origin_year'],r['player_id']] for r in train],
                test_keys=[[r['origin_year'],r['player_id']] for r in test],
                profile_counts=[len(counts[profile(r)]) for r in test],
                all_training_histories_left_truncated=bool(train) and all(r['history_left_truncated'] for r in train))


def fit(rows):
    x=matrix(rows);w=player_weights(rows);y=np.array([r['quality_rate'] for r in rows])
    mean=np.average(x,axis=0,weights=w);sd=np.sqrt(np.average((x-mean)**2,axis=0,weights=w));sd[sd<1e-10]=1
    z=(x-mean)/sd;intercept=float(np.average(y,weights=w))
    beta=np.linalg.solve(z.T@(w[:,None]*z)+10*np.eye(len(FEATURES)),z.T@(w*(y-intercept)))
    return dict(mean=mean.tolist(),scale=sd.tolist(),coef=beta.tolist(),intercept=intercept,alpha=10,features=list(FEATURES))


def predict(model,rows):
    return model['intercept']+(matrix(rows)-model['mean'])/model['scale']@model['coef']


def score(rows,arm):
    y=np.array([r['quality_rate'] for r in rows]);p=np.array([r[arm] for r in rows]);w=player_weights(rows);e=p-y
    return dict(rows=len(rows),people=len({r['player_id'] for r in rows}),
                rmse=float(np.sqrt(np.average(e*e,weights=w))),mae=float(np.average(abs(e),weights=w)),
                bias=float(np.average(e,weights=w)),oracle_exposure_actual_runs=sum(r['future_runs'] for r in rows),
                oracle_exposure_predicted_runs=sum(r[arm]*r['future_pitches']/1000 for r in rows))
