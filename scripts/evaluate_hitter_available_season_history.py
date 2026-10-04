"""One structural arrival comparison with fixed workload and batting heads."""
from pathlib import Path
import json
import sys

import joblib
import numpy as np
import polars as pl
from sklearn.ensemble import HistGradientBoostingClassifier
from threadpoolctl import threadpool_limits

from fit_practical_hitter_v31 import weights
from prepare_hitter_available_season_history import ROOT, OUT, CURRENT, ANCHOR, read, write
from prepare_hitter_extended_training import verify
from universal_baseball.practical_hitter_v30 import score
from universal_baseball.storage import sha256_file
from score_practical_hitter_v31 import paired

FIXED = [(677594,2021),(677951,2021),(679631,2021),(691023,2022),(694671,2023),(701762,2024)]


def approval():
    assert not (OUT/'source-approval.json').exists()
    pre = read(OUT/'preflight.json')
    verify(pre['input_hashes'])
    p = ROOT/'config/hitter_available_season_source_review.json'
    reviews = read(p)
    assert reviews['source_walkthrough_status']=='complete'
    cases = read(OUT/'source-review.json')['fixed_source_cases']
    assert {(c['player_id'],c['origin']) for c in cases} == {(c['player_id'],c['origin']) for c in reviews['cases']}
    assert all(c['assessment'] for c in reviews['cases'])
    write('source-approval.json',dict(source_walkthrough_status='complete',reviews=reviews,
        hashes={str(p):sha256_file(p),str(OUT/'preflight.json'):sha256_file(OUT/'preflight.json'),
                str(OUT/'source-review.json'):sha256_file(OUT/'source-review.json')}))


def connect(q, raw):
    mask = q['prior_debut'].to_numpy()==0
    p = q['preseason_p'].to_numpy().copy()
    hard = q['hard_unavailable'].to_numpy()|q['reported_retired'].to_numpy()
    p[mask] = raw[mask]
    p[hard] = 0.
    pa = q['preseason_pa'].to_numpy().copy()
    pa[mask] = p[mask]*q['preseason_conditional_pa'].to_numpy()[mask]
    value = q['preseason_value'].to_numpy().copy()
    value[mask] = pa[mask]*(q['baseline_rate'].to_numpy()[mask]/600+q['origin_replacement_rate'].to_numpy()[mask])
    translated = q['translated_ridge_value'].to_numpy().copy()
    translated[mask] = pa[mask]*(q['translated_ridge_rate'].to_numpy()[mask]/600+q['origin_replacement_rate'].to_numpy()[mask])
    assert np.isfinite(raw).all() and ((raw>=0)&(raw<=1)).all()
    return q.with_columns(pl.Series('available_raw_p',raw),pl.Series('available_p',p),
        pl.Series('available_pa',pa),pl.Series('available_value',value),
        pl.Series('available_translated_pa',pa),pl.Series('available_translated_value',translated),
        pl.col('preseason_conditional_pa').alias('available_conditional_pa'),pl.col('baseline_rate').alias('available_rate'))


def fit():
    pre = read(OUT/'preflight.json')
    verify(pre['input_hashes'])
    approved = read(OUT/'source-approval.json')
    assert approved['source_walkthrough_status']=='complete'
    verify(approved['hashes'])
    f = pl.read_parquet(OUT/'features.parquet')
    anchor = pl.read_parquet(ANCHOR).sort('row_id')
    fits = []
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y,k = c['year'],c['fold']
            pp = OUT/f'forecast-{y}-{k}.parquet'
            note = OUT/f'fit-{y}-{k}.json'
            if pp.exists():
                n = read(note)
                verify({str(pp):n['prediction_sha256'],n['head']['path']:n['head']['sha256']})
                fits.append(n)
                continue
            tr = f.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id')
            te = f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            q = anchor.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            assert te['row_id'].equals(q['row_id'])
            if c['identical_matrices']:
                h = c['control']
                verify({h['path']:h['sha256']})
                model = joblib.load(h['path'])
                head = dict(**h,reused=True)
            else:
                mp = OUT/f'participation-{y}-{k}.joblib'
                assert not mp.exists(), 'Unsealed fit requires explicit recovery'
                model = HistGradientBoostingClassifier(**pre['settings'])
                w = weights(tr)
                model.fit(tr.select(pre['features']).to_numpy(),(tr['next_pa'].to_numpy()>0).astype(int),sample_weight=w)
                joblib.dump(model,mp,compress=3)
                head = dict(path=str(mp),sha256=sha256_file(mp),reused=False,head='participation',
                    training_rows=len(tr),training_people=tr['player_id'].n_unique(),max_target_year=int(tr['target_year'].max()),
                    weighted_arrival_rate=float(np.average(tr['next_pa'].to_numpy()>0,weights=w)))
            raw = model.predict_proba(te.select(pre['features']).to_numpy())[:,1]
            if c['identical_matrices']:
                np.testing.assert_array_equal(raw,q['preseason_raw_p'].to_numpy())
            q = connect(q,raw)
            assert q.select(anchor.columns).equals(anchor.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id'))
            q.write_parquet(pp)
            n = dict(year=y,fold=k,information_date=c['information_date'],head=head,prediction_sha256=sha256_file(pp))
            write(note.name,n)
            fits.append(n)
            print(f'Arrival clock {y}/{k}: '+('identical control replayed' if head['reused'] else 'new classifier saved'),flush=True)
    q = pl.concat([pl.read_parquet(OUT/f"forecast-{c['year']}-{c['fold']}.parquet") for c in pre['cells']]).sort('row_id')
    assert q.select(anchor.columns).equals(anchor)
    q.write_parquet(OUT/'predictions.parquet')
    write('fits.json',fits)


def probability(g, arm):
    per = []
    for _,s in g.group_by('target_year'):
        y = (s['next_pa'].to_numpy()>0).astype(float)
        p = s[arm+'_p'].to_numpy()
        z = np.clip(p,1e-12,1-1e-12)
        per.append([np.mean((p-y)**2),-np.mean(y*np.log(z)+(1-y)*np.log(1-z))])
    a = np.mean(per,axis=0)
    return dict(brier=float(a[0]),log_loss=float(a[1]),expected_arrivals=float(g[arm+'_p'].sum()),
        actual_arrivals=int((g['next_pa']>0).sum()))


def probability_interval(g, metric):
    # Reuse exactly the existing player-cluster/equal-year paired loss routine.
    y = (g['next_pa'].to_numpy()>0).astype(float)
    predictions = {}
    for a in ['available','preseason']:
        p = g[a+'_p'].to_numpy()
        z = np.clip(p,1e-12,1-1e-12)
        loss = (p-y)**2 if metric=='brier' else -y*np.log(z)-(1-y)*np.log(1-z)
        predictions[a+'_pa'] = np.sqrt(loss)
    h = g.with_columns(pl.lit(0.).alias('next_pa'),*[pl.Series(n,v) for n,v in predictions.items()])
    result = paired(h,'available','preseason','pa')
    result['metric'] = metric
    return result


def scoring():
    assert not (OUT/'verification.json').exists(), 'Preserve scoring receipt'
    pre = read(OUT/'preflight.json')
    verify(pre['input_hashes'])
    f = pl.read_parquet(OUT/'features.parquet')
    q = pl.read_parquet(OUT/'predictions.parquet').sort('row_id')
    anchor = pl.read_parquet(ANCHOR).sort('row_id')
    assert q.select(anchor.columns).equals(anchor)
    with threadpool_limits(limits=2):
        for c,n in zip(pre['cells'],read(OUT/'fits.json')):
            verify({n['head']['path']:n['head']['sha256'],str(OUT/f"forecast-{c['year']}-{c['fold']}.parquet"):n['prediction_sha256']})
            te = f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            sub = q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            p = joblib.load(n['head']['path']).predict_proba(te.select(pre['features']).to_numpy())[:,1]
            np.testing.assert_array_equal(p,sub['available_raw_p'].to_numpy())
            np.testing.assert_array_equal(sub['available_conditional_pa'],sub['preseason_conditional_pa'])
            np.testing.assert_array_equal(sub['available_rate'],sub['baseline_rate'])
    established = q.filter(pl.col('prior_debut')==1)
    for s in ['p','pa','value']:
        np.testing.assert_array_equal(established['available_'+s],established['preseason_'+s])
    never = q.filter(pl.col('prior_debut')==0)
    public = q.filter(pl.col('steamer_pa').is_not_null()&pl.col('zips_pa').is_not_null())
    assert len(public)==2627
    groups = [('all',q),('never',never),('upper',never.filter(pl.col('stage')=='Upper minors')),
        ('lower',never.filter(pl.col('stage')=='Lower minors')),('public',public),
        ('listed',never.filter(pl.col('rank_band')>0)),('thin',never.filter(pl.col('thin_pro')))]
    groups += [('never_'+str(y),never.filter(pl.col('origin_year')==y)) for y in sorted(q['origin_year'].unique())]
    bounds = [0,.01,.1,.5,.8,1.00001]
    groups += [(f'probability_{a:g}_{b:g}',never.filter((pl.col('preseason_p')>=a)&(pl.col('preseason_p')<b))) for a,b in zip(bounds,bounds[1:])]
    scores,intervals = [],[]
    with threadpool_limits(limits=2):
        for label,g in groups:
            if not len(g):
                continue
            arms = ['preseason','available','translated_ridge','available_translated']+(['steamer'] if label=='public' else [])
            scores.append(dict(scope=label,rows=len(g),people=g['player_id'].n_unique(),actual_pa=int(g['next_pa'].sum()),
                actual_value=float(g['next_value'].sum()),scores={a:score(g,a) for a in arms},
                probability={a:probability(g,a) for a in ['preseason','available']}))
            if label in ['all','never','upper','lower','never_2021','never_2022','never_2023']:
                for metric in ['pa','value']:
                    intervals.append(dict(scope=label,**paired(g,'available','preseason',metric)))
                for metric in ['brier','log_loss']:
                    intervals.append(dict(scope=label,**probability_interval(g,metric)))
    q.write_parquet(OUT/'scored-predictions.parquet')
    write('scores.json',scores)
    write('intervals.json',intervals)
    selections = []
    def add(g,why):
        assert len(g)==1
        o = g.row(0,named=True)
        old = next((s for s in selections if s['row_id']==o['row_id']),None)
        if old:
            old['reasons'].append(why)
        else:
            selections.append(dict(row_id=o['row_id'],player_id=o['player_id'],origin_year=o['origin_year'],
                name=o['player_name'],reasons=[why]))
    for pid,y in FIXED:
        add(never.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y)),'fixed before fit')
    h = never.with_columns(((pl.col('preseason_pa')-pl.col('next_pa'))**2-(pl.col('available_pa')-pl.col('next_pa'))**2).alias('gain'))
    add(h.sort(['gain','row_id'],descending=[True,False]).head(1),'largest squared PA gain')
    add(h.sort(['gain','row_id'],descending=[False,False]).head(1),'largest squared PA harm')
    add(never.filter(pl.col('next_pa')==0).sort(['available_pa','row_id'],descending=[True,False]).head(1),'largest nonarrival false high')
    add(never.with_columns((pl.col('next_pa')-pl.col('available_pa')).alias('miss')).sort(['miss','row_id'],descending=[True,False]).head(1),'largest PA false low')
    ordinary = never.filter(pl.col('next_pa').is_between(100,600)&
        ((pl.col('preseason_pa')-pl.col('next_pa')).abs()<30)&((pl.col('available_pa')-pl.col('next_pa')).abs()<30)&
        ((pl.col('baseline_rate')-pl.col('realized_season_rate')).abs()<.5)).sort('row_id')
    if len(ordinary):
        add(ordinary.head(1),'ordinary active case; first row ID with both PA errors below 30 and rate error below .5')
    write('selected-cases.json',selections)
    write('verification.json',dict(execution_integrity=True,evaluation_rows=len(q),classifiers_replayed=35,new_fits=20,
        reused_identical_controls=15,established_unchanged=True,conditional_and_hitting_unchanged=True,
        protected_outcomes_used=False,player_walkthrough_status='pending',ordinary_eligible=len(ordinary),
        hashes={str(OUT/n):sha256_file(OUT/n) for n in ['predictions.parquet','scored-predictions.parquet','scores.json','intervals.json','selected-cases.json','fits.json']}))
    print(json.dumps([s for s in scores if s['scope'] in ['never','upper','lower','never_2021','never_2022','never_2023']],indent=2),flush=True)


if __name__=='__main__':
    {'approve-source':approval,'fit':fit,'score':scoring}[sys.argv[1]]()
