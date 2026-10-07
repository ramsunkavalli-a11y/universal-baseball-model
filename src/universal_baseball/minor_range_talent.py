"""Transparent minor-count signals; conditional MLB range, not player value."""
from collections import defaultdict, Counter
import math

import numpy as np

LEVELS=('AAA','AA','Aplus','A','Aminus','ADVANCED_ROOKIE','ROOKIE_COMBINED','COMPLEX','DSL')
CHANNELS=('glove_avoidance','throw_avoidance','infield_plays','outfield_plays')
BASE_NAMES=('age','age_unknown','log_outs',*[f'position_{p}' for p in range(3,10)],*[f'level_{l}' for l in LEVELS])


def age_group(age):
    return 'unknown' if age is None else '<=19' if age<=19 else '20-22' if age<=22 else '23-25' if age<=25 else '26+'


def moments(mean,second,inverse_n,people,binomial):
    """Method-of-moments count noise correction; None strength means zero signal."""
    if people<30 or mean<=0 or (binomial and mean>=1):
        return dict(mean=mean,between_variance=0.,strength=None,people=people)
    v=max(0.,second-mean*mean)*people/(people-1)
    if binomial:
        between=max(0.,(v-mean*(1-mean)*inverse_n)/(1-inverse_n)) if inverse_n<1 else 0.
        between=min(between,mean*(1-mean)*(1-1e-9))
        strength=mean*(1-mean)/between-1 if between>0 else None
    else:
        between=max(0.,v-mean*inverse_n)
        strength=mean/between if between>0 else None
    return dict(mean=mean,between_variance=between,strength=strength,people=people)


def posterior_deviation(x,n,prior,reverse=False):
    k=prior['strength'];reliability=n/(n+k) if n>0 and k is not None else 0.
    raw=x/n if n>0 else None
    deviation=reliability*(raw-prior['mean']) if raw is not None else 0.
    return dict(raw_rate=raw,reliability=reliability,posterior_rate=prior['mean']+deviation,
                deviation=-deviation if reverse else deviation)


class ReferenceEngine:
    """Dated three-calendar-year reference moments, excluding people not just rows."""
    def __init__(self,rows):
        self.years=defaultdict(list);self.tables={}
        for r in rows:self.years[r['origin_year']].append(r)

    def table(self,year):
        if year in self.tables:return self.tables[year]
        groups=defaultdict(lambda:defaultdict(lambda:np.zeros(4)))
        for y in range(year-2,year+1):
            for r in self.years.get(y,()):
                p=r['position'];a=age_group(r['age']);l=r['level'];pid=r['player_id']
                choices=(('position_level_age',p,l,a),('position_level',p,l),('position_age',p,a),('position',p))
                measurements=[(0,r['errors']-r['throwingErrors'],r['chances']),(1,r['throwingErrors'],r['chances'])]
                if p in (4,5,6):measurements.append((2,r['assists'],r['outs']))
                if p in (7,8,9):measurements.append((3,r['putOuts'],r['outs']))
                for c,x,n in measurements:
                    if n<=0:continue
                    rate=x/n
                    for key in choices:groups[key+(c,)][pid]+=np.array([1.,rate,rate*rate,1/n])
        table={}
        for key,people in groups.items():
            means={pid:np.array([1.,v[1]/v[0],v[2]/v[0],v[3]/v[0]]) for pid,v in people.items()}
            folds=np.zeros((5,4))
            for pid,v in means.items():folds[pid%5]+=v
            table[key]=(means,folds)
        self.tables[year]=table
        return table

    def prior(self,r,c,excluded):
        year=r['origin_year'];p=r['position'];l=r['level'];a=age_group(r['age']);pid=r['player_id']
        choices=(('position_level_age',p,l,a),('position_level',p,l),('position_age',p,a),('position',p))
        table=self.table(year);selected=None
        for key in choices:
            people,folds=table.get(key+(c,),({},np.zeros((5,4))))
            stats=sum((folds[f] for f in range(5) if f not in excluded),np.zeros(4))
            if pid%5 not in excluded and pid in people:stats-=people[pid]
            n=int(round(stats[0]))
            selected=(key,stats,n)
            if n>=30:break
        key,stats,n=selected
        prior=moments(stats[1]/n if n else 0.,stats[2]/n if n else 0.,stats[3]/n if n else 0.,n,c in (0,1))
        prior.update(scope=list(key),reference_years=[y for y in range(year-2,year+1) if y in self.years],excluded_folds=list(excluded),focal_player_removed=True)
        return prior

    def features(self,rs,excluded):
        signals=np.zeros(4);denoms=np.zeros(4);traces=[]
        for r in rs:
            pos=r['position'];item=dict(level=r['level'],outs=r['outs'],counts={f:r[f] for f in ('putOuts','assists','errors','chances','throwingErrors')},signals=[])
            measurements=[(0,r['errors']-r['throwingErrors'],r['chances']),(1,r['throwingErrors'],r['chances'])]
            if pos in (4,5,6):measurements.append((2,r['assists'],r['outs']))
            if pos in (7,8,9):measurements.append((3,r['putOuts'],r['outs']))
            for c,x,n in measurements:
                prior=self.prior(r,c,excluded);s=posterior_deviation(x,n,prior,c in (0,1))
                signals[c]+=n*s['deviation'];denoms[c]+=n
                item['signals'].append(dict(channel=CHANNELS[c],numerator=x,denominator=n,prior=prior,**s))
            traces.append(item)
        out=np.divide(signals,denoms,out=np.zeros(4),where=denoms>0)
        return out,traces


def person_weights(rows):
    ns=Counter(r['player_id'] for r in rows)
    return np.array([1/ns[r['player_id']] for r in rows])


def design(rows,signals,age_median,candidate):
    xs=[]
    for r,s in zip(rows,signals,strict=True):
        age=r['age']
        x=[((age if age is not None else age_median)-23)/5,int(age is None),math.log1p(r['minor_outs'])-math.log(1501)]
        x.extend(int(r['position']==p) for p in range(3,10))
        x.extend(int(r['level']==l) for l in LEVELS)
        if candidate:x.extend(s)
        xs.append(x)
    return np.asarray(xs,dtype=float).reshape(len(rows),len(BASE_NAMES)+(len(CHANNELS) if candidate else 0))


def ridge_fit(x,y,weights,alpha,names):
    if not (np.isfinite(x).all() and np.isfinite(y).all() and np.isfinite(weights).all()):raise ValueError('Nonfinite fitted inputs')
    mu=np.average(x,axis=0,weights=weights);ym=float(np.average(y,weights=weights))
    sd=np.ones(x.shape[1]);indices=[0,2,*range(len(BASE_NAMES),x.shape[1])]
    for j in indices:
        v=float(np.average((x[:,j]-mu[j])**2,weights=weights));sd[j]=math.sqrt(v) if v>1e-20 else 1.
    z=(x-mu)/sd
    coef=np.linalg.solve(z.T@(weights[:,None]*z)+alpha*np.eye(x.shape[1]),z.T@(weights*(y-ym)))
    assert np.isfinite(coef).all()
    return dict(names=list(names),mean=mu.tolist(),scale=sd.tolist(),target_mean=ym,coefficients=coef.tolist(),alpha=alpha,
                weighted_people=float(weights.sum()),training_min=x.min(axis=0).tolist(),training_max=x.max(axis=0).tolist())


def ridge_predict(fit,x):
    return fit['target_mean']+((x-np.array(fit['mean']))/np.array(fit['scale']))@np.array(fit['coefficients'])


def preflight(train,test,cutoff,excluded,xtrain,xtest):
    if any(r['window_end']>cutoff or r['quality_rate'] is None for r in train):raise ValueError('Immature or unknown training label')
    if any(r['player_id']%5 in excluded for r in train):raise ValueError('Held person entered training')
    ids={r['player_id'] for r in train}
    if not ids.isdisjoint(r['player_id'] for r in test):raise ValueError('Train/test person overlap')
    keys=lambda rows:[(r['origin_year'],r['player_id'],r['position']) for r in rows]
    if len(set(keys(train)))!=len(train) or len(set(keys(test)))!=len(test):raise ValueError('Duplicate population')
    if any(r['origin_year']!=cutoff for r in test):raise ValueError('Moved evaluation origin')
    if not (np.isfinite(xtrain).all() and np.isfinite(xtest).all()):raise ValueError('Missing required fitted input')
    profiles=defaultdict(set);stages=defaultdict(set)
    for r in train:
        profiles[r['level'],r['position'],r['age_band'],r['sample_band']].add(r['player_id'])
        stages[r['level'],r['position']].add(r['player_id'])
    supported=len(ids)>=30 and len({r['origin_year'] for r in train})>=2
    return dict(cutoff=cutoff,excluded_folds=list(excluded),training_people=len(ids),training_origins=sorted({r['origin_year'] for r in train}),
        train_keys=keys(train),test_keys=keys(test),fit_supported=supported,train_test_people_disjoint=True,label_chronology=True,
        profile_rows=[dict(player_id=r['player_id'],position=r['position'],level_position_people=len(stages[r['level'],r['position']]),
                         joint_people=len(profiles[r['level'],r['position'],r['age_band'],r['sample_band']]),
                         unseen_level_position=len(stages[r['level'],r['position']])==0,
                         outside_feature_range=((xtest[i]<xtrain.min(axis=0))|(xtest[i]>xtrain.max(axis=0))).tolist() if len(train) else []) for i,r in enumerate(test)],
        train_feature_min=xtrain.min(axis=0).tolist() if len(train) else [],train_feature_max=xtrain.max(axis=0).tolist() if len(train) else [])
