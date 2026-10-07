"""Count correction with a protected baseline and real sparse-profile fallback."""
from collections import Counter, defaultdict

import numpy as np


def audit(train,test,cutoff,excluded,min_people=30):
    keys=lambda rows:[(r['origin_year'],r['player_id'],r['position']) for r in rows]
    if len(keys(train))!=len(set(keys(train))) or len(keys(test))!=len(set(keys(test))):
        raise ValueError('Duplicate identity')
    if any(r['window_end']>cutoff or r['quality_rate'] is None for r in train):
        raise ValueError('Immature or missing quality label')
    if any(r['player_id']%5 in excluded for r in train):raise ValueError('Held player entered training')
    if {r['player_id'] for r in train}&{r['player_id'] for r in test}:raise ValueError('Player overlap')
    people=len({r['player_id'] for r in train});origins=sorted({r['origin_year'] for r in train})
    return dict(cutoff=cutoff,excluded_folds=list(excluded),training_keys=keys(train),test_keys=keys(test),
                people=people,origins=origins,fit_supported=people>=min_people and len(origins)>=2,
                mature_labels=True,person_separation=True)


def fit(signals,residuals,rows,alpha=100.):
    s=np.asarray(signals,dtype=float);y=np.asarray(residuals,dtype=float)
    if s.shape!=(len(rows),4) or y.shape!=(len(rows),):raise ValueError('Mismatched correction inputs')
    if not np.isfinite(s).all() or not np.isfinite(y).all():raise ValueError('Nonfinite correction input')
    counts=Counter(r['player_id'] for r in rows);w=np.array([1/counts[r['player_id']] for r in rows])
    scale=np.sqrt(np.average(s*s,axis=0,weights=w));active=scale>1e-12
    scale=np.where(active,scale,1.);z=s/scale
    coef=np.linalg.solve(z.T@(w[:,None]*z)+alpha*np.eye(4),z.T@(w*y));coef[~active]=0.
    return dict(scale=scale.tolist(),coefficients=coef.tolist(),alpha=alpha,intercept=0.,active=active.tolist(),
                person_weight_sum=float(w.sum()))


def profile_table(rows,signals):
    stage=defaultdict(set);joint=defaultdict(set);indices=defaultdict(list)
    for i,r in enumerate(rows):
        key=(r['position'],r['level']);stage[key].add(r['player_id']);indices[key].append(i)
        joint[key+(r['age_band'],r['sample_band'])].add(r['player_id'])
    signals=np.asarray(signals,dtype=float)
    return dict(stage=stage,joint=joint,bounds={key:(signals[ix].min(axis=0),signals[ix].max(axis=0)) for key,ix in indices.items()})


def predict(model,baseline,row,signal,profiles):
    signal=np.asarray(signal,dtype=float);key=(row['position'],row['level'])
    stage_people=len(profiles['stage'].get(key,set()))
    joint_people=len(profiles['joint'].get(key+(row['age_band'],row['sample_band']),set()))
    reasons=[]
    if model is None:reasons.append('unsupported_pooled_correction')
    if stage_people<10:reasons.append('fewer_than_ten_position_level_people')
    if joint_people<5:reasons.append('fewer_than_five_joint_profile_people')
    if signal.shape!=(4,) or not np.isfinite(signal).all():reasons.append('missing_count_signal')
    bounds=profiles['bounds'].get(key)
    outside=[] if bounds is None or signal.shape!=(4,) or not np.isfinite(signal).all() else ((signal<bounds[0])|(signal>bounds[1])).tolist()
    if any(outside):reasons.append('count_signal_outside_position_level_range')
    terms=(signal/np.array(model['scale']))*np.array(model['coefficients']) if not reasons else np.zeros(4)
    correction=float(terms.sum())
    return dict(candidate=float(baseline+correction),baseline=float(baseline),correction=correction,
                correction_terms=terms.tolist(),applied=not reasons,reasons=reasons,
                stage_people=stage_people,joint_people=joint_people,outside=outside)
