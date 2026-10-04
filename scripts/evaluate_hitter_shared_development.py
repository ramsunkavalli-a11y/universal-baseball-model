"""Sealed two-contrast rate experiment; no selection before actual player review."""
import json
from pathlib import Path
import sys
import joblib
import numpy as np
import polars as pl
from sklearn.linear_model import Ridge
from threadpoolctl import threadpool_limits
from universal_baseball.hitter_shared_development import (
    representation,preflight_shared,LEVEL_FEATURES,AGE_FEATURES,HORIZON_FEATURES)
from universal_baseball.storage import sha256_file
from prepare_practical_hitter_v33 import safe_matrix
from fit_practical_hitter_v31 import weights
from score_practical_hitter_v31 import score,rate_score,paired
from score_hitter_reliability_v50 import rate_interval
from audit_hitter_rate_support import tagged
import evaluate_hitter_talent_bridge_v74 as bridge

ROOT=bridge.ROOT;OUT=ROOT/'reports/generated/hitter-shared-development'
FOLLOW=ROOT/'reports/generated/hitter-followup-support'
ARMS=['level_age','shared_development']
FIXED=[(701762,2024,'Nick Kurtz'),(694671,2023,'Wyatt Langford'),(624413,2018,'Pete Alonso'),
    (670867,2017,'Kevin Maitan'),(821181,2024,'Juneiker Caceres'),(677594,2021,'Julio Rodríguez'),
    (702616,2023,'Jackson Holliday'),(592450,2024,'Aaron Judge'),(665161,2021,'Jeremy Peña')]


def read(path):return json.loads(Path(path).read_text(encoding='utf8'))
def write(name,obj):(OUT/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf8')
def verify(hashes):
    for p,h in hashes.items():assert sha256_file(Path(p))==h,p


def feature_names():
    base=read(bridge.OUT/'preflight.json')['features']['translated_ridge']
    control=base+LEVEL_FEATURES+AGE_FEATURES
    return dict(level_age=control,shared_development=control+HORIZON_FEATURES)


def context(k):
    full=tagged(pl.read_parquet(bridge.OUT/f'features-{k}.parquet')).sort('row_id')
    required=list(dict.fromkeys(['row_id','player_id','origin_year','outer_fold','age','age_unknown','age_centered',
        'prior_debut','dominant_level','audit_age_band','stage','source_position',*feature_names()['level_age'][:220]]))
    origin=full.select(required)
    labels=pl.read_parquet(FOLLOW/'annual.parquet').filter(pl.col('rate_training_eligible')).select(
        'row_id',pl.col('season').alias('target_year'),pl.col('followup_year').alias('horizon'),
        pl.col('mlb_pa').alias('next_pa'),pl.col('component_value').alias('next_value'),pl.col('batting_rate').alias('next_batting_rate'))
    annual=representation(origin.join(labels,on='row_id',how='inner',validate='1:m')).sort('row_id','horizon')
    test=representation(full)
    return annual,test


def membership(annual,y,k,arm):
    cond=(pl.col('target_year')<=y)&(pl.col('outer_fold')!=k)&(pl.col('next_pa')>0)
    if arm=='level_age':cond &= pl.col('horizon')==1
    return annual.filter(cond).sort('row_id','horizon')


def prepare():
    assert not (OUT/'preflight.json').exists(),'Preserve preparation'
    previous=read(FOLLOW/'final-report.json');assert previous['player_walkthrough_status']=='complete'
    verify(previous['source_and_execution_hashes']);verify(previous['review_hashes'])
    assert read(bridge.OUT/'report.json')['player_walkthrough_status']=='complete'
    old=read(bridge.OUT/'preflight.json');verify(old['input_hashes'])
    q=pl.read_parquet(bridge.OUT/'scored-predictions.parquet').sort('row_id')
    for pid,y,name in FIXED:
        assert q.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y))['player_name'].to_list()==[name]
    OUT.mkdir(parents=True,exist_ok=True);names=feature_names();cells=[];ranges=[];members=[]
    with threadpool_limits(limits=2):
        for k in range(5):
            annual,full=context(k)
            for c in old['cells']:
                if c['fold']!=k:continue
                y=c['year'];te=full.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
                saved=q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
                assert te['row_id'].equals(saved['row_id'])
                h=next(h for h in read(bridge.OUT/f'fit-{y}-{k}.json')['heads'] if h['arm']=='translated_ridge')
                verify({h['path']:h['sha256']})
                replay=joblib.load(h['path']).predict(safe_matrix(te,old['features']['translated_ridge']))
                assert np.allclose(replay,saved['translated_ridge_all_rate'],atol=1e-10,rtol=0)
                checks={}
                for arm in ARMS:
                    tr=membership(annual,y,k,arm)
                    note=preflight_shared(tr,te,y,k,names[arm],te['row_id'].to_list())
                    if arm=='level_age':
                        orig=full.filter(pl.col('row_id').is_in(c['training_row_ids'])&(pl.col('next_pa')>0)).sort('row_id')
                        assert tr['row_id'].equals(orig['row_id'])
                        assert np.allclose(tr['next_batting_rate'],orig['next_batting_rate'],atol=1e-10,rtol=0)
                    keys=['dominant_level','audit_age_band','prior_debut']
                    groups=tr.group_by(keys+['horizon']).agg(pl.col('player_id').n_unique().alias('people'),pl.len().alias('observations'))
                    note['exact_horizon_profiles']=groups.sort(*keys,'horizon').to_dicts();checks[arm]=note
                    members.append(tr.select('row_id','horizon','player_id','origin_year','target_year').with_columns(
                        pl.lit(y).alias('cutoff'),pl.lit(k).alias('held_fold'),pl.lit(arm).alias('arm')))
                    x,tx=safe_matrix(tr,names[arm]),safe_matrix(te,names[arm])
                    for i,n in enumerate(names[arm]):
                        lo,hi=float(x[:,i].min()),float(x[:,i].max())
                        ranges.append(dict(origin=y,fold=k,arm=arm,feature=n,minimum=lo,maximum=hi,
                            test_outside=int(((tx[:,i]<lo)|(tx[:,i]>hi)).sum())))
                cells.append(dict(year=y,fold=k,test_row_ids=te['row_id'].to_list(),checks=checks,
                    benchmark_head=h,weight_sum=checks['level_age']['training_observations']))
                print('Actual preflight saved in memory:',y,k,[(a,checks[a]['training_observations']) for a in ARMS],flush=True)
    pl.concat(members).write_parquet(OUT/'memberships.parquet');pl.DataFrame(ranges).write_parquet(OUT/'ranges.parquet')
    paths=[ROOT/'docs/hitter-shared-development-contract.md',Path(__file__),
        ROOT/'src/universal_baseball/hitter_shared_development.py',ROOT/'scripts/prepare_practical_hitter_v33.py',
        ROOT/'scripts/fit_practical_hitter_v31.py',ROOT/'scripts/score_practical_hitter_v31.py',ROOT/'scripts/score_hitter_reliability_v50.py',
        FOLLOW/'final-report.json',FOLLOW/'annual.parquet',FOLLOW/'support.parquet',bridge.OUT/'preflight.json',
        bridge.OUT/'report.json',bridge.OUT/'scored-predictions.parquet',OUT/'memberships.parquet',OUT/'ranges.parquet']
    paths += [bridge.OUT/f'features-{k}.parquet' for k in range(5)]
    write('preflight.json',dict(cells=cells,features=names,checks_before_fits=70,anchor_heads_replayed=35,
        input_hashes={str(p):sha256_file(p) for p in paths},fixed_cases=FIXED,
        exact_horizon_support_included=True,player_walkthrough_status='pending',protected_outcomes_used=False))


def fit():
    pre=read(OUT/'preflight.json');verify(pre['input_hashes'])
    sealed={str(OUT/'preflight.json'):sha256_file(OUT/'preflight.json'),str(Path(__file__)):sha256_file(Path(__file__))}
    if (OUT/'fit-seal.json').exists():assert read(OUT/'fit-seal.json')==sealed
    else:write('fit-seal.json',sealed)
    q=pl.read_parquet(bridge.OUT/'scored-predictions.parquet').sort('row_id')
    memberships=pl.read_parquet(OUT/'memberships.parquet');forecasts=[];fits=[]
    with threadpool_limits(limits=2):
        for k in range(5):
            annual,full=context(k)
            for c in pre['cells']:
                if c['fold']!=k:continue
                y=c['year'];pp=OUT/f'forecast-{y}-{k}.parquet';npth=OUT/f'fit-{y}-{k}.json'
                if pp.exists():
                    note=read(npth);verify(note['hashes']);forecasts.append(pl.read_parquet(pp));fits.append(note);continue
                te=full.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
                pred=q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id');heads=[]
                for arm in ARMS:
                    tr=membership(annual,y,k,arm)
                    stored=memberships.filter((pl.col('cutoff')==y)&(pl.col('held_fold')==k)&(pl.col('arm')==arm)).select('row_id','horizon','player_id','origin_year','target_year')
                    assert tr.select(stored.columns).equals(stored)
                    preflight_shared(tr,te,y,k,pre['features'][arm],c['test_row_ids'])
                    w=weights(tr)*tr['next_pa'].to_numpy();w*=c['weight_sum']/w.sum()
                    m=Ridge(alpha=100).fit(safe_matrix(tr,pre['features'][arm]),tr['next_batting_rate'].to_numpy(),sample_weight=w)
                    raw=m.predict(safe_matrix(te,pre['features'][arm]));assert np.isfinite(raw).all()
                    rate=np.where(pred['prior_debut'].to_numpy()==0,raw,pred['baseline_rate'].to_numpy())
                    path=OUT/f'{arm}-{y}-{k}.joblib';joblib.dump(m,path,compress=3)
                    heads.append(dict(arm=arm,path=str(path),sha256=sha256_file(path),training_observations=len(tr),
                        training_people=tr['player_id'].n_unique(),weight_sum=float(w.sum())))
                    pred=pred.with_columns(pl.Series(arm+'_all_rate',raw),pl.Series(arm+'_rate',rate),pl.col('preseason_pa').alias(arm+'_pa'))
                    pred=pred.with_columns((pl.col(arm+'_pa')*(pl.col(arm+'_rate')/600+pl.col('origin_replacement_rate'))).alias(arm+'_value'))
                pred.write_parquet(pp)
                note=dict(origin=y,fold=k,heads=heads,hashes={str(pp):sha256_file(pp),**{h['path']:h['sha256'] for h in heads}})
                write(npth.name,note);forecasts.append(pred);fits.append(note);print('Two heads fitted:',y,k,flush=True)
    result=pl.concat(forecasts).sort('row_id');assert result.select(q.columns).equals(q)
    result.write_parquet(OUT/'predictions.parquet');write('fits.json',fits)


def score_results():
    pre=read(OUT/'preflight.json');verify(pre['input_hashes']);verify(read(OUT/'fit-seal.json'))
    q=pl.read_parquet(OUT/'predictions.parquet').sort('row_id');replayed=0
    with threadpool_limits(limits=2):
        for k in range(5):
            _,full=context(k)
            for c in pre['cells']:
                if c['fold']!=k:continue
                te=full.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
                pred=q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
                for h in read(OUT/f"fit-{c['year']}-{k}.json")['heads']:
                    verify({h['path']:h['sha256']});m=joblib.load(h['path'])
                    assert np.allclose(m.predict(safe_matrix(te,pre['features'][h['arm']])),pred[h['arm']+'_all_rate'],atol=1e-10,rtol=0)
                    replayed+=1
    annual=pl.read_parquet(FOLLOW/'annual.parquet').filter(pl.col('followup_year')==1)
    rates=q.drop('next_batting_rate').join(annual.select('row_id',pl.col('batting_rate').fill_null(0).alias('next_batting_rate')),on='row_id',validate='1:1')
    never=q.filter(pl.col('prior_debut')==0)
    scopes=[('all',q),('never_debut',never),('upper_never_debut',never.filter(pl.col('stage')=='Upper minors')),
        ('lower_never_debut',never.filter(pl.col('stage')=='Lower minors')),
        ('new_draftees',never.filter(pl.col('new_draftee'))),('thin_pro',never.filter(pl.col('thin_pro'))),
        ('public',q.filter((pl.col('pa_0')>0)&pl.col('steamer_index').is_not_null()&pl.col('zips_index').is_not_null()))]
    scopes += [('never_origin_'+str(y),never.filter(pl.col('origin_year')==y)) for y in sorted(q['origin_year'].unique())]
    arms=['preseason','translated_ridge',*ARMS];scores=[];intervals=[]
    for name,g in scopes:
        if not len(g):continue
        r=rates.filter(pl.col('row_id').is_in(g['row_id'].to_list()))
        scores.append(dict(scope=name,rows=len(g),actual_pa=int(g['next_pa'].sum()),actual_value=float(g['next_value'].sum()),
            rate={a:rate_score(r,a+'_rate') for a in arms},unweighted_rate={a:rate_score(r,a+'_rate',False) for a in arms},
            delivered={a:score(g,a) for a in arms}))
        if name in ['all','never_debut','upper_never_debut','lower_never_debut']:
            for a,b in [('level_age','translated_ridge'),('shared_development','translated_ridge'),('shared_development','level_age'),('shared_development','preseason')]:
                intervals.append(dict(scope=name,delivered=paired(g,a,b),rate=rate_interval(r,a,b)))
    write('scores.json',scores);write('intervals.json',intervals)
    ids={}
    for pid,y,name in FIXED:
        row=q.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y)).row(0,named=True)
        assert row['player_name']==name;ids.setdefault(row['row_id'],[]).append('fixed')
    for arm in ARMS:
        delta=never.with_columns(((pl.col(arm+'_value')-pl.col('next_value'))**2-
            (pl.col('translated_ridge_value')-pl.col('next_value'))**2).alias('mse_delta'))
        for reason,g,col,descending in [('gain',delta,'mse_delta',False),('harm',delta,'mse_delta',True),
            ('false_high',delta.filter(pl.col('next_pa')==0),arm+'_value',True),
            ('false_low',delta.filter(pl.col('next_pa')>0).with_columns((pl.col(arm+'_value')-pl.col('next_value')).alias('error')),'error',False),
            ('ordinary',delta.filter(pl.col('next_pa')>=200).with_columns(abs(pl.col(arm+'_value')-pl.col('next_value')).alias('error')),'error',False)]:
            rid=g.sort(col,'row_id',descending=[descending,False])['row_id'][0];ids.setdefault(rid,[]).append(arm+'_'+reason)
    selected=[]
    actual_rates={r['row_id']:r['next_batting_rate'] for r in rates.select('row_id','next_batting_rate').iter_rows(named=True)}
    for rid,reasons in sorted(ids.items()):
        row=q.filter(pl.col('row_id')==rid).select('row_id','player_id','player_name','origin_year','outer_fold','age','stage','prior_debut',
            'preseason_p','preseason_conditional_pa','preseason_pa','next_pa','next_value',
            *[a+'_'+metric for a in arms for metric in ['rate','value']]).row(0,named=True)
        row.update(selection_reasons=reasons,actual_target_centered_rate=actual_rates[rid]);selected.append(row)
    write('selected-cases.json',selected)
    write('verification.json',dict(new_heads_replayed=replayed,evaluation_rows=len(q),original_columns_exact=True,
        rate_response='Target-year MLB average',delivered_response='Fixed common-origin event value',
        opportunity_unchanged=True,player_walkthrough_status='pending',disposition='provisional_no_selection',protected_outcomes_used=False))
    print(json.dumps(scores[:7],indent=2),flush=True)


if __name__=='__main__':
    {'prepare':prepare,'fit':fit,'score':score_results}[sys.argv[1]]()
