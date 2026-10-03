"""Preflight the full historical population, then learn predictive skill reliability."""
from pathlib import Path
import sys
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
import evaluate_hitter_readiness_v49 as prior
import prepare_practical_hitter_v31 as source
from fit_practical_hitter_v31 import weights
from prepare_practical_hitter_v33 import safe_matrix,PED
from universal_baseball.forecast_validation import preflight
from universal_baseball.mlb_event_logit import EVENTS,batting_rate
from universal_baseball.mlb_predictive_reliability import fit,predict,transported_counts
from universal_baseball.storage import sha256_file

ROOT=prior.ROOT;OUT=ROOT/'reports/generated/practical-hitter-reliability-v50'
FEATURES=['age_centered','age_squared','age_unknown','elapsed_scaled','prior_debut','last_stat_gap',
    *[f'position_{p}' for p in source.POS],*[f'milb_canceled_{lag}' for lag in range(3)],*PED,
    *[f'pooled_{b}_{ev}' for b in source.BUCKETS if b!='MLB' for ev in ['pa',*source.EVENTS]]]
RANKS=[x for x in prior.old.r.read(prior.old.OUT/'preflight.json')['features'] if x.startswith('scout_')]
FEATURES+=RANKS
HISTORY=[f'history_{lag}_{ev}' for lag in range(3) for ev in EVENTS]
HISTORY_ENV=[f'history_env_{lag}_{ev}' for lag in range(3) for ev in EVENTS]


def write(name,obj):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_text(__import__('json').dumps(obj,indent=2,allow_nan=False,ensure_ascii=False)+'\n',encoding='utf8')


def arrays(g,target_environment=False):
    history=g.select(HISTORY).to_numpy().reshape(len(g),3,8)
    oldenv=g.select(HISTORY_ENV).to_numpy().reshape(len(g),3,8)
    env=g.select([('target' if target_environment else 'origin')+'_env_'+ev for ev in EVENTS]).to_numpy()
    x=safe_matrix(g,FEATURES)
    for j,name in enumerate(FEATURES):
        if name.startswith('scout_list_capacity_'):x[:,j]/=100.
    return x,transported_counts(history,oldenv,env),env


def prepare():
    assert prior.old.r.read(prior.OUT/'report.json')['player_walkthrough_status']=='complete'
    assert not (OUT/'preflight.json').exists()
    pre=prior.old.r.read(prior.OUT/'preflight.json');f=pl.read_parquet(prior.OUT/'features.parquet')
    old=ROOT/'reports/generated/practical-hitter-v36';assert prior.old.r.read(old/'report.json')['player_walkthrough_status']=='complete'
    labels=pl.read_parquet(old/'features.parquet').select('row_id',*[f'{stem}_{ev}' for stem in ['count','origin_env','target_env'] for ev in EVENTS])
    f=f.join(labels,on='row_id',validate='1:1');assert len(f)==63282 and f['count_K'].null_count()==0
    counts=pl.read_parquet(ROOT/'reports/generated/practical-hitter-v31/counts.parquet').filter(pl.col('bucket')=='MLB')
    counts=counts.with_columns((pl.col('babip_hits')-pl.col('doubles')-pl.col('triples')).alias('singles'))
    mapping=dict(K='strike_outs',UBB='unintentional_walks',HBP='hit_by_pitch',**{'1B':'singles','2B':'doubles','3B':'triples','HR':'home_runs'})
    counts=counts.with_columns((pl.col('plate_appearances')-pl.sum_horizontal(list(mapping.values()))).alias('other'))
    mapping['other']='other';assert counts.filter(pl.col('other')<0).is_empty()
    envs=counts.group_by('season').agg(pl.col('plate_appearances',*mapping.values()).sum())
    env={r['season']:np.array([r[mapping[ev]] for ev in EVENTS],float)/r['plate_appearances'] for r in envs.iter_rows(named=True)}
    lookup={(r['season'],r['player_id']):r for r in counts.iter_rows(named=True)};rows=[]
    for o in f.iter_rows(named=True):
        row={'row_id':o['row_id']}
        for lag in range(3):
            year=o['origin_year']-lag;raw=lookup.get((year,o['player_id']));assert year in env
            for j,ev in enumerate(EVENTS):
                row[f'history_{lag}_{ev}']=float(raw[mapping[ev]]) if raw else 0.
                row[f'history_env_{lag}_{ev}']=float(env[year][j])
            assert sum(row[f'history_{lag}_{ev}'] for ev in EVENTS)==o[f'pa_{lag}']
        assert np.allclose([o['origin_env_'+ev] for ev in EVENTS],env[o['origin_year']])
        if o['next_pa']>0:
            rate=batting_rate(np.array([[o['count_'+ev]/o['next_pa'] for ev in EVENTS]]),np.array([[o['target_env_'+ev] for ev in EVENTS]]))[0]
            assert np.isclose(rate,o['next_batting_rate'],atol=1e-9)
        rows.append(row)
    f=f.join(pl.DataFrame(rows),on='row_id',validate='1:1');OUT.mkdir(parents=True,exist_ok=True);f.write_parquet(OUT/'features.parquet')
    cells=[];support=[];profiles=[]
    for c in pre['cells']:
        tr=f.filter(pl.col('row_id').is_in(c['training_row_ids']));active=tr.filter(pl.col('next_pa')>0);te=f.filter(pl.col('row_id').is_in(c['test_row_ids']))
        checks={}
        for head,g in [('all',tr),('active',active)]:
            sup,note=preflight(g,te,cutoff=c['year'],fold=c['fold'],features=FEATURES+HISTORY+HISTORY_ENV,expected_keys=te.select('row_id','horizon').iter_rows())
            checks[head]=note;support.append(sup.with_columns(pl.lit(head).alias('head')))
        def tag(g):return prior.old.tag(g).with_columns(pl.when(pl.col('pooled_MLB_pa')==0).then(pl.lit('none')).when(pl.col('pooled_MLB_pa')<300).then(pl.lit('brief')).when(pl.col('pooled_MLB_pa')<1000).then(pl.lit('intermediate')).otherwise(pl.lit('substantial')).alias('own_mlb_exposure'))
        keys=['stage','prior_debut','age_band','rank_band','own_mlb_exposure']
        groups=tag(active).group_by(keys).agg(pl.col('player_id').n_unique().alias('active_profile_players'))
        profiles.append(tag(te).select('row_id',*keys).join(groups,on=keys,how='left',validate='m:1').with_columns(pl.col('active_profile_players').fill_null(0)))
        x,own,environment=arrays(active,True);assert np.isfinite(x).all() and np.isfinite(own).all()
        assert set(active['player_id']).isdisjoint(set(te['player_id'])) and active['target_year'].max()<=c['year']
        cells.append(dict(**c,reliability_preflight=checks,active_training_rows=len(active),active_training_players=active['player_id'].n_unique()))
    pl.concat(support).write_parquet(OUT/'support.parquet');pl.concat(profiles).sort('row_id').write_parquet(OUT/'profile-support.parquet')
    paths=[OUT/'features.parquet',OUT/'support.parquet',OUT/'profile-support.parquet',prior.OUT/'preflight.json',prior.OUT/'predictions.parquet',prior.OUT/'report.json',
        old/'features.parquet',old/'report.json',ROOT/'reports/generated/practical-hitter-v31/counts.parquet',Path(__file__),ROOT/'src/universal_baseball/mlb_predictive_reliability.py',
        ROOT/'src/universal_baseball/mlb_event_logit.py',ROOT/'scripts/prepare_practical_hitter_v33.py',ROOT/'docs/practical-hitter-reliability-v50-contract.md',
        ROOT/'docs/practical-hitter-reliability-v50-execution-amendment.md']
    write('preflight.json',dict(before_fitting=True,cells=cells,features=FEATURES,history_features=HISTORY,history_environment_features=HISTORY_ENV,
        input_hashes={str(p):sha256_file(p) for p in paths},arms=['fixed_reliability','learned_reliability'],evaluation_rows=30506,
        source_counts_and_existing_rate_exactly_reconstructed=True,protected_outcomes_used=False,frozen_forecast_changed=False))
    fixed=[(592450,2016),(592450,2024),(691026,2023),(668715,2022),(458015,2016),(641355,2016),(624413,2018),(683011,2022),(701762,2024),(806956,2024),(808393,2024)]
    source=[]
    for pid,year in fixed:
        q=f.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==year));assert len(q)==1
        o=q.to_dicts()[0];x,c,env0=arrays(q)
        source.append(dict(player_id=pid,origin_year=year,player_name=o['player_name'],raw_MLB_three_year_event_counts=q.select(HISTORY).to_dicts()[0],
            actual_prior_inputs=q.select(FEATURES).to_dicts()[0],origin_environment=env0[0].tolist(),transported_pooled_MLB_counts=c[0].tolist(),
            own_exposure=float(c[0].sum()),profile=pl.read_parquet(OUT/'profile-support.parquet').filter(pl.col('row_id')==o['row_id']).to_dicts()))
    write('before-fit-source-cases.json',source)
    print('35 all/active preflights and eleven source cases saved before fits;',len(FEATURES),'prior inputs; counts and rate labels exact.',flush=True)


def fit_all():
    pre=prior.old.r.read(OUT/'preflight.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    f=pl.read_parquet(OUT/'features.parquet');base=pl.read_parquet(prior.OUT/'predictions.parquet');frames=[];fits=[]
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y,k=c['year'],c['fold'];dest=OUT/f'forecast-{y}-{k}.parquet';note=OUT/f'fits-{y}-{k}.json'
            if dest.exists():
                saved=prior.old.r.read(note);assert sha256_file(dest)==saved['prediction_sha256']
                for head in saved['heads']:assert sha256_file(Path(head['path']))==head['sha256']
                frames.append(pl.read_parquet(dest));fits.extend(saved['heads']);continue
            tr=f.filter(pl.col('row_id').is_in(c['training_row_ids'])&(pl.col('next_pa')>0)).sort('row_id')
            te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id');q=base.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id');assert q['row_id'].equals(te['row_id'])
            x,own,env=arrays(tr,True);xt,ownt,envt=arrays(te);heads=[]
            for arm in pre['arms']:
                model=fit(x,own,tr.select(['count_'+ev for ev in EVENTS]).to_numpy(),env,weights(tr),arm=='learned_reliability')
                artifact=OUT/f'{arm}-{y}-{k}.joblib';joblib.dump(model,artifact,compress=3)
                detail=predict(model['beta'],model['alpha'],xt,ownt,envt);p=detail['probabilities'];rate=batting_rate(p,envt)
                assert np.isfinite(rate).all() and np.allclose(p.sum(1),1)
                q=q.with_columns(pl.Series(arm+'_rate',rate),pl.col('binary_scout_pa').alias(arm+'_pa'),*[pl.Series(arm+'_p_'+ev,p[:,j]) for j,ev in enumerate(EVENTS)])
                q=q.with_columns((pl.col(arm+'_pa')*(pl.col(arm+'_rate')/600+pl.col('origin_replacement_rate'))).alias(arm+'_value'))
                heads.append(dict(arm=arm,path=str(artifact),sha256=sha256_file(artifact),training_rows=len(tr),training_players=tr['player_id'].n_unique(),maximum_target_year=int(tr['target_year'].max()),
                    alpha_by_event=dict(zip(EVENTS,model['alpha'].tolist())),optimizer=model['optimizer']))
                print(f'{y}/{k} {arm}: {model["optimizer"]["iterations"]} iterations; alpha '+str([round(a) for a in model['alpha']]),flush=True)
            q.write_parquet(dest);write(note.name,dict(heads=heads,prediction_sha256=sha256_file(dest)));frames.append(q);fits.extend(heads)
    q=pl.concat(frames).sort('row_id');assert len(q)==30506 and q.select(base.columns).equals(base.sort('row_id'))
    q.write_parquet(OUT/'predictions.parquet');write('fits.json',fits)
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    write('fit-report.json',dict(heads=len(fits),rows=len(q),player_walkthrough_status='pending',protected_outcomes_used=False,frozen_forecast_changed=False))


if __name__=='__main__':prepare() if '--prepare' in sys.argv else fit_all()
