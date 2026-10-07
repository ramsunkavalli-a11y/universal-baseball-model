"""Nested penalty memberships exclude nuisance people everywhere."""
from universal_baseball.minor_range_correction import audit


def plans(pool,cutoff,excluded):
    available=sorted({r['origin_year'] for r in pool if r['window_end']<=cutoff})[-2:]
    result=[]
    for origin in available:
        for held in range(5):
            if held in excluded:continue
            full_excluded=sorted(set(excluded)|{held})
            train=[r for r in pool if r['window_end']<=origin and r['quality_rate'] is not None
                   and r['player_id']%5 not in full_excluded]
            test=[r for r in pool if r['origin_year']==origin and r['player_id']%5==held]
            check=audit(train,test,origin,full_excluded)
            if any(r['window_end']>cutoff for r in test):raise ValueError('Immature nested validation window')
            result.append(dict(validation_origin=origin,validation_fold=held,outer_cutoff=cutoff,excluded_people_folds=list(excluded),audit=check))
    return result
