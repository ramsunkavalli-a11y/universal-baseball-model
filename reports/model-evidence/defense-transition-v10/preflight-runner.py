"""One sealed position-development comparison on unchanged defensive exposure."""

from collections import defaultdict
import json
import math
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.defense_transition import evidence, keys, group, allocate
from universal_baseball.defense_repertoire import POSITIONS, ROLES
from universal_baseball.defense_opportunity_bridge import CHANNELS, native_from_outs
from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections, save
from run_defense_opportunity_v8 import score, native_score

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'reports/generated/defense-repertoire-v9'
SOURCE=ROOT/'reports/generated/defense-position-opportunity-v7'
OUT=ROOT/'reports/generated/defense-transition-v10'
PUBLIC=ROOT/'reports/model-evidence/defense-transition-v10'
PANEL=ROOT/'reports/generated/hitter-preseason-readiness-v68/predictions.parquet'


def read(p):return json.loads(p.read_text(encoding='utf8'))


def hashes(paths):return {str(p):sha256_file(p) for p in paths}


def write(name, data):
    save(OUT/name,data);save(PUBLIC/name,data)


def check():
    pre=read(OUT/'preflight.json')
    for p,h in pre['hashes'].items():assert sha256_file(Path(p))==h,p
    assert sha256_file(OUT/'features.parquet')==pre['features_sha256']
    assert sha256_file(OUT/'profile-support.parquet')==pre['profile_sha256']
    protections();return pre


def prepare():
    protections();assert not (OUT/'preflight.json').exists()
    OUT.mkdir(parents=True,exist_ok=True);PUBLIC.mkdir(parents=True,exist_ok=True)
    final=read(OLD/'final-review.json');assert final['player_walkthrough_status']=='complete'
    for p,h in final['hashes'].items():assert sha256_file(Path(p))==h,p
    oldpre=read(OLD/'preflight.json')
    for p,h in oldpre['hashes'].items():assert sha256_file(Path(p))==h,p
    f=pl.read_parquet(OLD/'features.parquet')
    assert sha256_file(OLD/'features.parquet')==oldpre['features_sha256']
    panel=pl.read_parquet(PANEL,columns=['row_id','player_id','origin_year','pa_0','pa_1','pa_2','prior_debut'])
    joined=f.join(panel.rename({'player_id':'cache_pid','origin_year':'cache_origin','pa_0':'cache_PA'}),on='row_id',how='left',validate='1:1')
    assert joined['cache_pid'].null_count()==0 and joined['cache_pid'].equals(joined['player_id'])
    assert joined['cache_origin'].equals(joined['origin_year']) and joined['cache_PA'].equals(joined['pa_0'])
    hist=defaultdict(list)
    for r in pl.read_parquet(SOURCE/'annual-usage.parquet').to_dicts():hist[r['player_id']].append(r)
    rows=[]
    for r in joined.drop('cache_pid','cache_origin','cache_PA').to_dicts():
        r.update(evidence(r,hist[r['player_id']]));rows.append(r)
    frame=pl.DataFrame(rows,infer_schema_length=None);assert frame.height==30506 and frame['target_year'].max()==2025
    frame.write_parquet(OUT/'features.parquet')
    cells=[];profiles=[]
    total=sum(pl.col(f'actual_{p}') for p in POSITIONS)
    def sample(r):
        p=r['transition_evidence_PA'];return '0' if p==0 else '1-49' if p<50 else '50-199' if p<200 else '200+'
    for c in oldpre['cells']:
        y,k=c['origin'],c['fold']
        base=frame.filter(pl.col('row_id').is_in(c['training_row_ids']))
        tr=base.filter(total>0);te=frame.filter(pl.col('row_id').is_in(c['test_row_ids']))
        assert tr['target_year'].max()<=y and not set(tr['player_id'])&set(te['player_id'])
        required={key for r in te.to_dicts() for key in keys(r)}
        support=[group(tr.to_dicts(),key) for key in sorted(required)]
        cells.append(dict(origin=y,fold=k,base_training_row_ids=base['row_id'].to_list(),training_row_ids=tr['row_id'].to_list(),
            test_row_ids=te['row_id'].to_list(),training_people=tr['player_id'].n_unique(),training_target_ceiling=int(tr['target_year'].max()),
            support=support,computed_before_position_numerators=True,player_disjoint=True))
        bucket=defaultdict(set)
        for r in tr.to_dicts():bucket[r['stage'],r['age_band'],sample(r),r['transition_primary_role'],r['transition_status']].add(r['player_id'])
        for r in te.to_dicts():
            key=(r['stage'],r['age_band'],sample(r),r['transition_primary_role'],r['transition_status'])
            choices=[s for key2 in keys(r) for s in support if s['key']==list(key2)]
            usable=[s for s in choices if s['people']>=20 and s['effective_people']>=10 and s['denominator_outs']>0]
            profiles.append(dict(row_id=r['row_id'],player_id=r['player_id'],origin=y,fold=k,stage=key[0],age_band=key[1],
                MLB_sample=key[2],primary_role=key[3],prior_MLB_status=key[4],training_people=len(bucket[key]),sparse=len(bucket[key])<20,
                chosen_group=usable[0]['key'] if usable else None,unsupported_transition=not bool(usable),unknown_repertoire=r['transition_unknown']))
    pl.DataFrame(profiles,infer_schema_length=None).write_parquet(OUT/'profile-support.parquet')
    paths=[Path(__file__),ROOT/'src/universal_baseball/defense_transition.py',ROOT/'tests/test_defense_transition.py',
        ROOT/'docs/defense-transition-v10-contract.md',SOURCE/'annual-usage.parquet',OLD/'features.parquet',OLD/'predictions.parquet',
        OLD/'preflight.json',OLD/'fit-report.json',OLD/'final-review.json',OLD/'player-walkthrough.json',OLD/'young-profile-diagnosis.json',
        ROOT/'src/universal_baseball/defense_opportunity_bridge.py',ROOT/'scripts/run_defense_opportunity_v8.py',PANEL]
    paths += [OLD/f"model-{c['origin']}-{c['fold']}.json" for c in cells]
    write('preflight.json',dict(before_fitting=True,cells=cells,profile_rows=len(profiles),
        sparse_profiles=sum(r['sparse'] for r in profiles),unseen_profiles=sum(r['training_people']==0 for r in profiles),
        unsupported_transition_rows=sum(r['unsupported_transition'] for r in profiles),unknown_repertoire_rows=sum(r['unknown_repertoire'] for r in profiles),
        fixed_exposure_and_DH=True,no_tuning=True,protected_outcomes_used=False,hashes=hashes(paths),
        features_sha256=sha256_file(OUT/'features.parquet'),profile_sha256=sha256_file(OUT/'profile-support.parquet')))
    print(json.dumps(dict(status='all_folds_sealed_before_fit',rows=len(profiles),unsupported=sum(r['unsupported_transition'] for r in profiles))))


def interval(frame, ref):
    people=frame['player_id'].unique().sort().to_list();idx={p:i for i,p in enumerate(people)}
    present=np.zeros((len(people),3));loss=np.zeros((len(people),3,2))
    for r in frame.to_dicts():
        i,j=idx[r['player_id']],r['origin_year']-2022;present[i,j]=1
        for a,arm in enumerate(('transition',ref)):
            loss[i,j,a]=np.mean([(r[f'{arm}_{p}']-r[f'actual_{p}'])**2 for p in POSITIONS])
    rng=np.random.default_rng(708008);changes=[]
    for _ in range(40):
        counts=rng.multinomial(len(people),np.full(len(people),1/len(people)),size=50)
        rmse=np.sqrt(np.einsum('bi,ija->bja',counts,loss)/(counts@present)[:,:,None])
        changes.extend((rmse[:,:,0]-rmse[:,:,1]).mean(axis=1))
    rmse=np.sqrt(loss.sum(axis=0)/present.sum(axis=0)[:,None])
    return dict(contrast='transition_minus_'+ref,change=float((rmse[:,0]-rmse[:,1]).mean()),
        interval_95=np.quantile(changes,[.025,.975]).tolist(),seed=708008,draws=2000,whole_person_clustered=True,development_only=True)


def share_score(q,arm):
    actual=q.select([f'actual_{p}' for p in POSITIONS]).to_numpy();a=actual/actual.sum(axis=1)[:,None]
    if arm=='transition':pred=q['transition_prediction_shares'].to_numpy()
    else:
        pred=q.select([f'{arm}_{p}' for p in POSITIONS]).to_numpy();total=pred.sum(axis=1)
        pred=np.divide(pred,total[:,None],out=np.zeros_like(pred),where=total[:,None]>0)
    return dict(rows=q.height,mean_cell_squared_share_error=float(np.mean((pred-a)**2))) if q.height else None


def fit():
    pre=check();assert not (OUT/'fit-report.json').exists()
    f=pl.read_parquet(OUT/'features.parquet');old=pl.read_parquet(OLD/'predictions.parquet')
    missing=[n for n in old.columns if n not in f.columns];base=f.join(old.select('row_id',*missing),on='row_id',how='left',validate='1:1')
    rows=[];modelnotes=[]
    for c in pre['cells']:
        y,k=c['origin'],c['fold'];tr=f.filter(pl.col('row_id').is_in(c['training_row_ids']));te=base.filter(pl.col('row_id').is_in(c['test_row_ids']))
        tables={tuple(s['key']):group(tr.to_dicts(),tuple(s['key']),True) for s in c['support']}
        for s in c['support']:assert all(tables[tuple(s['key'])][n]==v for n,v in s.items())
        conv=read(OLD/f'model-{y}-{k}.json')['native_conversions']
        path=OUT/f'model-{y}-{k}.json';save(path,dict(origin=y,fold=k,tables=list(tables.values()),
            training_row_ids=c['training_row_ids'],test_row_ids=c['test_row_ids'],native_conversions=conv))
        modelnotes.append(dict(path=str(path),sha256=sha256_file(path),origin=y,fold=k))
        for r in te.to_dicts():
            p=allocate(r,tables)
            for pos,v in zip(ROLES,p['values']):r[f'transition_{pos}']=v
            for channel,v in native_from_outs(p['values'],conv).items():r[f'transition_native_{channel}']=v
            r.update(transition_total_outs=sum(p['values'][:8]),transition_unallocated_outs=max(0.,p['unallocated_outs']),
                transition_prediction_shares=p['shares'],transition_prior_key=json.dumps(p['prior']['key']) if p['prior'] else None,
                transition_unsupported=p['unsupported_transition'],transition_cell_squared_error=float(np.mean([
                    (p['values'][j]-r[f'actual_{pos}'])**2 for j,pos in enumerate(POSITIONS)])))
            rows.append(r)
        print(f'Transition fold {y}/{k} saved',flush=True)
    q=pl.DataFrame(rows,infer_schema_length=None).sort('row_id');assert q.height==12432 and q['row_id'].n_unique()==12432
    assert q['transition_10'].equals(q['repair_10'])
    assert np.allclose(q['transition_total_outs'],q['repair_total_outs'],atol=1e-9,rtol=0)
    q.write_parquet(OUT/'predictions.parquet')
    overall=[];groups=[];native=[];placement=[]
    for y in (2022,2023,2024):
        year=q.filter(pl.col('origin_year')==y)
        for arm in ('carry','ratio','pooled','context','repair','transition'):overall.append(dict(origin=y,arm=arm,**score(year,arm)))
        for field in ('stage','age_band','transition_status'):
            for value in year[field].unique():
                s=year.filter(pl.col(field)==value)
                for arm in ('ratio','repair','transition'):groups.append(dict(origin=y,field=field,value=value,arm=arm,**score(s,arm)))
        positive=year.filter(sum(pl.col(f'actual_{p}') for p in POSITIONS)>0)
        for label,s in [('all_measured_defenders',positive),('zero_current_MLB_PA',positive.filter(pl.col('pa_0')==0)),
                        ('age_15_19',positive.filter(pl.col('age_band')=='3'))]:
            for arm in ('ratio','repair','transition'):placement.append(dict(origin=y,subset=label,arm=arm,score=share_score(s,arm)))
        for channel in CHANNELS:
            for arm in ('ratio','repair','transition'):
                for pos in (False,True):native.append(dict(origin=y,channel=channel,arm=arm,positive_only=pos,
                    unknown_rows=year[f'actual_native_{channel}'].null_count(),score=native_score(year,arm,channel,pos)))
    write('fit-report.json',dict(models=modelnotes,overall=overall,groups=groups,placement=placement,native_scores=native,
        intervals=[interval(q,ref) for ref in ('ratio','repair')],player_walkthrough_status='pending',disposition='pending_player_review',
        fixed_scalar_exposure_and_DH=True,protected_outcomes_used=False,hashes=hashes([OUT/'preflight.json',OUT/'predictions.parquet'])))
    protections();print(json.dumps(dict(status='provisional_needs_walkthrough',rows=q.height)))


def review():
    check();assert not (OUT/'player-walkthrough.json').exists()
    q=pl.read_parquet(OUT/'predictions.parquet');records=q.to_dicts();lookup={(r['player_id'],r['origin_year']):r for r in records}
    source=pl.read_parquet(SOURCE/'source.parquet');selected={};peers={}
    for file in ('player-walkthrough.json','young-profile-diagnosis.json'):
        for c in read(OLD/file)['cases']:
            key=(c['player_id'],c['origin']);selected.setdefault(key,[]).append('previous_focal_'+file)
            peerkeys=[(p['player_id'],p['origin']) for p in c['records'][1:]]
            if key not in peers:peers[key]=peerkeys
            else:peers[key]=list(dict.fromkeys(peers[key]+peerkeys))
    dev=[r for r in records if r['origin_year'] in (2022,2023)]
    gain=lambda r:r['repair_cell_squared_error']-r['transition_cell_squared_error']
    error=lambda r:r['transition_total_outs']-sum(r[f'actual_{p}'] for p in POSITIONS)
    for r,why in [(max(dev,key=gain),'new_largest_gain'),(min(dev,key=gain),'new_largest_loss'),
                  (max(dev,key=error),'new_false_high'),(min(dev,key=error),'new_false_low')]:
        key=(r['player_id'],r['origin_year']);selected.setdefault(key,[]).append(why)
        if key not in peers:
            pool=[p for p in records if p['player_id']!=r['player_id'] and p['origin_year']==r['origin_year'] and p['stage']==r['stage']
                and p['transition_primary_role']==r['transition_primary_role'] and p['age'] is not None and r['age'] is not None and abs(p['age']-r['age'])<=3]
            def dist(p):return (sum(abs(a-b) for a,b in zip(r['transition_shares'],p['transition_shares']))+
                abs(p['age']-r['age'])/3+.1*abs(math.log1p(p['role_defensive_sample'])-math.log1p(r['role_defensive_sample'])),p['row_id'])
            peers[key]=[(p['player_id'],p['origin_year']) for p in sorted(pool,key=dist)[:3]]
    cases=[]
    for key,reasons in sorted(selected.items()):
        traces=[]
        for pk in [key,*peers[key]]:
            r=lookup[pk];m=read(OUT/f"model-{r['origin_year']}-{r['outer_fold']}.json")
            calc=allocate(r,{tuple(t['key']):t for t in m['tables']})
            assert np.allclose(calc['values'],[r[f'transition_{p}'] for p in ROLES],atol=1e-9,rtol=0)
            origin=source.filter((pl.col('player_id')==r['player_id'])&pl.col('season').is_between(r['origin_year']-2,r['origin_year']))
            future=source.filter((pl.col('player_id')==r['player_id'])&(pl.col('season')==r['target_year'])&pl.col('is_mlb'))
            traces.append(dict(player_id=r['player_id'],player_name=r['player_name'],origin=r['origin_year'],fold=r['outer_fold'],age=r['age'],stage=r['stage'],
                current_MLB_PA=r['pa_0'],previous_MLB_PA=[r['pa_1'],r['pa_2']],prior_debut=r['prior_debut'],expected_PA=r['preseason_pa'],actual_PA=r['next_pa'],
                source_origin_rows=origin.to_dicts(),future_official_rows=future.to_dicts(),
                transition_inputs={n:v for n,v in r.items() if n.startswith('transition_') and not n.startswith('transition_native_')},
                calculation=calc,position_forecasts={arm:{str(p):r[f'{arm}_{p}'] for p in ROLES} for arm in ('ratio','repair','transition')},
                actuals={str(p):r[f'actual_{p}'] for p in ROLES},
                native_forecasts={arm:{c:r[f'{arm}_native_{c}'] for c in CHANNELS} for arm in ('ratio','repair','transition')},
                native_actuals={c:r[f'actual_native_{c}'] for c in CHANNELS},
                actual_PA_sensitivity=[v*r['next_pa']/r['preseason_pa'] if r['preseason_pa'] else 0 for v in calc['values']],
                sensitivity_not_forecast=True,nonarrival_unknown_skill=True))
        r=lookup[key];cases.append(dict(player_id=r['player_id'],player_name=r['player_name'],origin=r['origin_year'],reasons=reasons,records=traces))
    write('player-walkthrough.json',dict(status='mechanics_complete_baseball_judgment_pending',cases=cases,
        peer_selection='Preserve all preceding origin-selected peers, union duplicated focal peer sets; additional cases use origin/stage/role/age/exposure only.',
        protected_outcomes_used=False,hashes=hashes([OUT/'preflight.json',OUT/'fit-report.json',OUT/'predictions.parquet'])))
    print(json.dumps(dict(cases=len(cases),peers=sum(len(c['records'])-1 for c in cases),status='needs_independent_replay_and_baseball_judgment')))


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','fit','review'])
    args=p.parse_args();{'prepare':prepare,'fit':fit,'review':review}[args.action]()
