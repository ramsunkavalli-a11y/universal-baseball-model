"""Independent source construction, augmented ridge solves and matched scores."""
from collections import Counter, defaultdict
import math
from pathlib import Path

import numpy as np
import polars as pl

from run_defense_position_transfer_v4 import ROOT, SOURCE, OUT, PUBLIC, read, write, key
from universal_baseball import defense_native_range as base
from universal_baseball import defense_position_transfer as transfer
from universal_baseball.storage import sha256_file
from audit_defensive_talent_support import verify
from run_hitter_finite_return_baseline import protections


def close(a,b):
    assert math.isclose(a,b,abs_tol=1e-9,rel_tol=1e-9),(a,b)


def independent_extra(r):
    pos=r['position'];d=3000/(r['history_outs']+3000)
    n=r['other_outs'];rate=1500*r['other_runs']/(3000+n)*d
    rel=n/(3000+n)*d;share=r['other_pivot_share']
    return [rate if 4<=pos<=6 else 0,rate if 7<=pos<=9 else 0,
            rel if 4<=pos<=6 else 0,rel if 7<=pos<=9 else 0,
            rel*share if pos in (4,5) else 0,rel*(1-share) if pos==6 else 0,
            rel*share if pos in (7,9) else 0,rel*(1-share) if pos==8 else 0]


def independent_matrix(rows,disabled):
    x=np.column_stack([base.matrix(rows),np.array([independent_extra(r) for r in rows])])
    for c in disabled:
        x[:,transfer.FEATURES.index(c)]=0
    return x


def main():
    protected=protections();pre=read(OUT/'preflight.json');report=read(OUT/'report.json')
    verify(pre['hashes']);verify(report['hashes'])
    assert pre['protections']==report['protections']==protected
    rows=pl.read_parquet(OUT/'predictions.parquet').to_dicts()
    original={key(r):r for r in pl.read_parquet(SOURCE/'predictions.parquet').to_dicts()}
    native=defaultdict(list)
    for r in pl.read_parquet(SOURCE/'component-ledger.parquet').to_dicts():
        native[r['player_id']].append(r)
    assert set(original)=={key(r) for r in rows}
    for r in rows:
        for c,v in original[key(r)].items():
            assert r[c]==v,(key(r),c)
        allowed={4,5,6} if r['position'] in (4,5,6) else {7,8,9} if r['position'] in (7,8,9) else set()
        allowed.discard(r['position'])
        n=runs=pivot=0.
        invalid=0
        positions=set()
        for s in native[r['player_id']]:
            if not r['origin_year']-2<=s['season']<=r['origin_year'] or s['position'] not in allowed:
                continue
            if not s['range_valid']:
                invalid+=s['native_outs'];continue
            w=2.**(s['season']-r['origin_year']);n+=s['native_outs']*w;runs+=s['range_runs']*w
            positions.add(s['position'])
            if s['position']==(6 if r['position'] in (4,5,6) else 8):
                pivot+=s['native_outs']*w
        close(n,r['other_outs']);close(runs,r['other_runs']);close(invalid,r['other_invalid_outs'])
        close(1500*runs/(3000+n),r['other_rate']);close(n/(3000+n),r['other_reliability'])
        close(pivot/n if n else 0,r['other_pivot_share']);assert len(positions)==r['other_positions']
    models={(m['origin'],m['fold']):m['model'] for m in read(OUT/'models.json')['models']}
    solved=0
    for c in pre['checks']:
        year,fold=c['origin'],c['fold']
        tr=[r for r in rows if r['quality_rate'] is not None and r['window_end']<=year and r['origin_year']<year and r['player_id']%5!=fold]
        te=[r for r in rows if r['origin_year']==year and r['player_id']%5==fold]
        assert set(map(tuple,c['train_keys']))=={key(r) for r in tr}
        assert set(map(tuple,c['test_keys']))=={key(r) for r in te}
        assert {r['player_id'] for r in tr}.isdisjoint(r['player_id'] for r in te)
        # Count feature support independently rather than trusting the preflight flag.
        supported={name:set() for name in transfer.EXTRA}
        profiles=defaultdict(set)
        for r in tr:
            for name,value in zip(transfer.EXTRA,independent_extra(r)):
                if abs(value)>1e-12:
                    supported[name].add(r['player_id'])
            n=r['other_outs'];label='<300' if n<300 else '300-1499' if n<1500 else '1500+'
            profiles[(*base.profile(r),label)].add(r['player_id'])
        assert c['added_feature_people']=={name:len(p) for name,p in supported.items()}
        assert c['disabled_features']==[name for name in transfer.EXTRA if len(supported[name])<20]
        for r in te:
            n=r['other_outs'];label='<300' if n<300 else '300-1499' if n<1500 else '1500+'
            assert r['transfer_profile_people']==len(profiles[(*base.profile(r),label)])
        m=models[year,fold]
        if m is None:
            assert not c['fit_allowed']
            for r in te:
                close(r['transfer'],r['history_rate'])
            continue
        assert c['fit_allowed'] and m['disabled']==c['disabled_features']
        x=independent_matrix(tr,m['disabled']);counts=Counter(r['player_id'] for r in tr)
        w=np.array([1/counts[r['player_id']] for r in tr]);y=np.array([r['quality_rate'] for r in tr])
        mean=np.average(x,axis=0,weights=w);sd=np.sqrt(np.average((x-mean)**2,axis=0,weights=w));sd[sd<1e-10]=1
        z=(x-mean)/sd;intercept=float(np.average(y,weights=w))
        beta=np.linalg.lstsq(np.vstack([np.sqrt(w)[:,None]*z,np.sqrt(10)*np.eye(z.shape[1])]),
                             np.concatenate([np.sqrt(w)*(y-intercept),np.zeros(z.shape[1])]),rcond=None)[0]
        assert np.allclose(beta,m['coef'],rtol=0,atol=1e-10)
        assert np.allclose(mean,m['mean']) and np.allclose(sd,m['scale'])
        pred=intercept+(independent_matrix(te,m['disabled'])-mean)/sd@beta
        for r,p in zip(te,pred):
            close(r['transfer'],p)
        solved+=1
    # Independent headline and per-origin errors and person-balanced weighting.
    for name in ['primary',*report['by_origin']]:
        selected=[r for r in rows if r['quality_rate'] is not None and (r['origin_year']>=2022 if name=='primary' else r['origin_year']==int(name))]
        actual=report['primary'] if name=='primary' else report['by_origin'][name]
        counts=Counter(r['player_id'] for r in selected);w=np.array([1/counts[r['player_id']] for r in selected])
        for arm in ('neutral','history','calibrated','transfer'):
            e=np.array([r[arm]-r['quality_rate'] for r in selected])
            close(np.sqrt(np.average(e*e,weights=w)),actual['scores'][arm]['rmse'])
            close(np.average(e,weights=w),actual['scores'][arm]['bias'])
        assert base.paired_interval(selected,'transfer','calibrated')==actual['transfer_minus_calibrated']
    walk=read(OUT/'player-walkthrough.json');wc=read(OUT/'walk-review.json')
    assert walk['player_walkthrough_status']=='complete' and wc['hash']==sha256_file(OUT/'player-walkthrough.json')
    for c in walk['cases']:
        for p in [c['primary'],*c['peers']]:
            r=p['forecast'];m=models[r['origin_year'],r['fold']]
            if m:
                close(m['intercept']+sum(p['fitted_terms'].values()),r['transfer'])
                blank={**r,'other_outs':0.,'other_runs':0.,'other_pivot_share':0.}
                probe=m['intercept']+(independent_matrix([blank],m['disabled'])[0]-m['mean'])/m['scale']@m['coef']
                close(probe,p['zero_other_fixed_fit_probe'])
    review=dict(execution_integrity='pass',matched_predictions=len(rows),independent_ridge_solves=solved,
                player_walkthrough_status='complete',walk_cases=wc['cases'],fully_replayed_peers=wc['fully_replayed_peers'],
                unknown_quality_peers=wc['unknown_quality_peers'],no_2026_outcomes=True,deployment_approved=False,
                disposition='Retain related-position representation as qualified research; aggregate gain uncertain and thin-target bias remains. No forecast promotion.',
                protections=protected,hashes={str(p):sha256_file(p) for p in (OUT/'player-walkthrough.json',OUT/'walk-review.json',Path(__file__))})
    write('final-review.json',review)
    PUBLIC.mkdir(parents=True,exist_ok=True)
    for name in ('report.json','preflight.json','models.json','source-player-walkthrough.json','player-walkthrough.json','walk-review.json','final-review.json'):
        target=PUBLIC/name;assert not target.exists()
        target.write_bytes((OUT/name).read_bytes())
    print({k:v for k,v in review.items() if k not in ('hashes','protections')})


if __name__=='__main__':
    main()
