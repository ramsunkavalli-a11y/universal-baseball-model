"""Sealed joint-role/capacity test, fixed skill and batting, targets through 2025."""

from collections import defaultdict
from pathlib import Path
import argparse
import json

import numpy as np
import polars as pl

from universal_baseball import defense_jobs as jobs
from universal_baseball import defense_repertoire as repertoire
from universal_baseball.defense_opportunity_bridge import native_from_outs
from universal_baseball.defense_value import position_value, score_rows, paired_interval
from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections, save

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/generated/defense-jobs-v14'
PUBLIC=ROOT/'reports/model-evidence/defense-jobs-v14'
SOURCE=ROOT/'reports/generated/defense-position-opportunity-v7'
OLD=ROOT/'reports/generated/defense-repertoire-v9'
TRANS=ROOT/'reports/generated/defense-transition-v10'
DH=ROOT/'reports/generated/defense-budget-v13'
VALUE=ROOT/'reports/generated/defense-value-v12'
ARMS=('reference','joint','candidate')
POSITIONS=repertoire.POSITIONS
ROLES=repertoire.ROLES


def read(p):return json.loads(p.read_text(encoding='utf8'))


def write(name,data):
    for d in (OUT,PUBLIC):save(d/name,data)


def hashes(paths):return {str(p):sha256_file(p) for p in paths}


def verify(h):
    for p,v in h.items():assert sha256_file(Path(p))==v,p


def inputs():
    raw=pl.read_parquet(SOURCE/'source.parquet').filter(pl.col('is_mlb'))
    dh=pl.read_parquet(DH/'reviewed-DH-starts.parquet')
    delta={(r['season'],r['player_id']):r['certified_dual_DH_starts'] for r in dh.to_dicts()}
    inventory={}
    for (y,),g in raw.group_by('season'):
        outs=[int(g.filter(pl.col('position_code')==str(p))['fielding_outs'].sum()) for p in POSITIONS]
        starts=[int(g.filter(pl.col('position_code')==str(p))['games_started'].sum()) for p in POSITIONS]
        assert len(set(outs))==len(set(starts))==1
        ds=int(dh.filter(pl.col('season')==y)['reviewed_DH_starts'].sum())
        inventory[y]=dict(outs=outs,starts=starts[0],DH_starts=ds,dh_outs=outs[0]/starts[0],
                          caps=[*outs,ds*outs[0]/starts[0]])
        if y>=2022:assert ds==starts[0]
    hist=defaultdict(list)
    for r in pl.read_parquet(SOURCE/'annual-usage.parquet').to_dicts():
        if r['is_mlb']:r['starts_10']+=delta.get((r['season'],r['player_id']),0)
        hist[r['player_id']].append(r)
    return inventory,delta,hist


def prepare():
    protections();OUT.mkdir(parents=True,exist_ok=True);PUBLIC.mkdir(parents=True,exist_ok=True)
    assert not (OUT/'preflight.json').exists()
    for path in [DH/'final-review.json',VALUE/'final-review.json']:
        receipt=read(path);assert receipt['player_walkthrough_status']=='complete'
    inventory,delta,hist=inputs()
    oldpre=read(OLD/'preflight.json');f=pl.read_parquet(TRANS/'features.parquet')
    assert len(f)==30506 and f['row_id'].n_unique()==len(f) and f['target_year'].max()==2025
    rows=[]
    for r in f.to_dicts():
        y,t,pid=r['origin_year'],r['target_year'],r['player_id']
        r['raw_actual_DH']=r['actual_10'];r['raw_carry_DH']=r['carry_10']
        r['actual_10']+=delta.get((t,pid),0);r['carry_10']+=delta.get((y,pid),0)
        r['origin_dh_outs']=inventory[y]['dh_outs']
        r['actual_job_vector']=[*[float(r[f'actual_{p}']) for p in POSITIONS],r['actual_10']*inventory[t]['dh_outs']]
        r.update(jobs.evidence(r,hist[pid],r['origin_dh_outs']))
        rows.append(r)
    frame=pl.DataFrame(rows,infer_schema_length=None);frame.write_parquet(OUT/'features.parquet')
    lookup={r['row_id']:r for r in rows};cells=[];profiles=[]
    def sample(r):
        pa=r['job_evidence_PA'];return '0' if pa==0 else '1-49' if pa<50 else '50-199' if pa<200 else '200+'
    for c in oldpre['cells']:
        y,k=c['origin'],c['fold']
        base=[lookup[i] for i in c['training_row_ids']]
        train=[r for r in base if r['target_year']>=2022 and sum(r['actual_job_vector'])>0]
        test=[lookup[i] for i in c['test_row_ids']]
        assert train and all(r['target_year']<=y and r['origin_year']+1==r['target_year'] for r in base)
        assert all(r['outer_fold']!=k for r in base) and all(r['outer_fold']==k and r['origin_year']==y for r in test)
        assert {r['player_id'] for r in base}.isdisjoint(r['player_id'] for r in test)
        needed={key for r in test for key in jobs.keys(r)}
        support=[jobs.group(train,key) for key in sorted(needed)]
        refneeded={key for r in test for key in repertoire.keys(r)}
        refsupport=[repertoire.mean_group(base,key) for key in sorted(refneeded)]
        bucket=defaultdict(set)
        for r in train:
            bucket[r['stage'],r['age_band'],sample(r),r['job_primary_role'],r['job_status'],r['job_evidence_kind']].add(r['player_id'])
        table={tuple(s['key']):s for s in support}
        for r in test:
            key=(r['stage'],r['age_band'],sample(r),r['job_primary_role'],r['job_status'],r['job_evidence_kind'])
            chosen=next((table[key2] for key2 in jobs.keys(r) if jobs.supported(table[key2])),None)
            profiles.append(dict(row_id=r['row_id'],player_id=r['player_id'],origin=y,fold=k,
                stage=key[0],age_band=key[1],MLB_sample=key[2],role=key[3],status=key[4],evidence_kind=key[5],
                detailed_training_people=len(bucket[key]),sparse=len(bucket[key])<20,
                chosen_group=chosen['key'] if chosen else None,unsupported=chosen is None,unknown_role=r['job_unknown']))
        cells.append(dict(origin=y,fold=k,reference_training_row_ids=c['training_row_ids'],
            training_row_ids=[r['row_id'] for r in train],test_row_ids=c['test_row_ids'],
            training_people=len({r['player_id'] for r in train}),training_target_years=sorted({r['target_year'] for r in train}),
            support=support,reference_support=refsupport,player_disjoint=True))
    pl.DataFrame(profiles,infer_schema_length=None).write_parquet(OUT/'profile-support.parquet')
    # Only mature same-policy cohorts can inform the omitted-player reserve.
    reservations=[]
    for y in (2022,2023,2024):
        past=[]
        for origin in sorted({r['origin_year'] for r in rows if 2022<=r['target_year']<=y}):
            cohort=[r for r in rows if r['origin_year']==origin];target=origin+1
            matched=np.sum([r['actual_job_vector'] for r in cohort],axis=0)
            full=np.array(inventory[target]['caps'],float)
            assert (matched<=full+.001).all()
            past.append(dict(origin=origin,target=target,known_people=len(cohort),
                             full_job_time=full.tolist(),matched_job_time=matched.tolist(),
                             omitted_fraction=((full-matched)/full).tolist()))
        assert past
        fraction=np.max([r['omitted_fraction'] for r in past],axis=0)
        full=np.array(inventory[y]['caps'],float)
        reservations.append(dict(origin=y,origin_inventory=inventory[y],mature_cohorts=past,
                                 reserve_fraction=fraction.tolist(),outside_reserve=(full*fraction).tolist()))
    paths=[Path(__file__),ROOT/'scripts/review_defense_jobs_v14.py',ROOT/'scripts/verify_defense_jobs_v14.py',
           ROOT/'docs/defense-jobs-v14-contract.md',ROOT/'src/universal_baseball/defense_jobs.py',
           ROOT/'tests/test_defense_jobs.py',ROOT/'src/universal_baseball/defense_repertoire.py',
           ROOT/'src/universal_baseball/defense_value.py',ROOT/'src/universal_baseball/defense_opportunity_bridge.py',
           SOURCE/'source.parquet',SOURCE/'annual-usage.parquet',DH/'reviewed-DH-starts.parquet',DH/'final-review.json',
           TRANS/'features.parquet',OLD/'preflight.json',OLD/'predictions.parquet',VALUE/'predictions.parquet',
           VALUE/'channel-predictions.parquet',VALUE/'final-review.json']
    paths += [OLD/f"model-{c['origin']}-{c['fold']}.json" for c in cells]
    write('preflight.json',dict(before_fitting=True,before_numerators=True,cells=cells,forecasts=12432,
        reservations=reservations,profiles=len(profiles),sparse_profiles=sum(p['sparse'] for p in profiles),
        unseen_profiles=sum(p['detailed_training_people']==0 for p in profiles),unknown_roles=sum(p['unknown_role'] for p in profiles),
        unsupported_groups=sum(p['unsupported'] for p in profiles),no_2026_outcomes=True,no_deployment=True,
        source_hashes=hashes(paths),feature_sha256=sha256_file(OUT/'features.parquet'),
        profile_sha256=sha256_file(OUT/'profile-support.parquet'),
        qualification='Same-policy training begins with target 2022; broad means do not certify detailed prospect support.'))
    print(json.dumps(dict(status='sealed_before_fit',forecasts=12432,cells=len(cells),
                         training_people=[c['training_people'] for c in cells],sparse=sum(p['sparse'] for p in profiles))),flush=True)


def check():
    protections();p=read(OUT/'preflight.json');verify(p['source_hashes'])
    assert sha256_file(OUT/'features.parquet')==p['feature_sha256']
    assert sha256_file(OUT/'profile-support.parquet')==p['profile_sha256']
    return p


def fit():
    pre=check();assert not (OUT/'fit-report.json').exists()
    frame=pl.read_parquet(OUT/'features.parquet');lookup={r['row_id']:r for r in frame.to_dicts()}
    saved=pl.read_parquet(OLD/'predictions.parquet');legacy={r['row_id']:r for r in saved.to_dicts()}
    predictions=[];modelnotes=[]
    for c in pre['cells']:
        y,k=c['origin'],c['fold'];path=OUT/f'model-{y}-{k}.json'
        assert not path.exists(),'Never refit/overwrite a saved fold'
        tr=[lookup[i] for i in c['training_row_ids']];base=[lookup[i] for i in c['reference_training_row_ids']]
        tables={tuple(s['key']):jobs.group(tr,tuple(s['key']),True) for s in c['support']}
        refs={tuple(s['key']):repertoire.mean_group(base,tuple(s['key']),True) for s in c['reference_support']}
        for s in c['support']:assert all(tables[tuple(s['key'])][n]==v for n,v in s.items())
        for s in c['reference_support']:assert all(refs[tuple(s['key'])][n]==v for n,v in s.items())
        conv=read(OLD/f'model-{y}-{k}.json')['native_conversions']
        save(path,dict(origin=y,fold=k,tables=list(tables.values()),reference_tables=list(refs.values()),
                       native_conversions=conv,training_row_ids=c['training_row_ids'],
                       reference_training_row_ids=c['reference_training_row_ids'],test_row_ids=c['test_row_ids']))
        modelnotes.append(dict(path=str(path),sha256=sha256_file(path)))
        for i in c['test_row_ids']:
            r=dict(lookup[i]);a=repertoire.predict(r,refs)
            old=legacy[i]
            assert np.allclose(a['values'][:8],[old[f'repair_{p}'] for p in POSITIONS],atol=1e-8,rtol=0)
            for p,v in zip(ROLES,a['values']):r[f'reference_{p}']=v
            r['reference_potential_outs']=a['potential_total_outs'];r['reference_unallocated_outs']=a['unallocated_outs']
            r['reference_prior_key']=json.dumps(a['prior']['key'])
            mass=a['potential_total_outs']+a['values'][-1]*r['origin_dh_outs']
            joint=jobs.allocate(r,tables,mass)
            r['job_total']=mass;r['job_unknown_mass']=joint['unknown_mass']
            r['job_prediction_shares']=joint['shares'];r['job_learned_shares']=joint['learned_shares']
            r['job_prior_key']=json.dumps(joint['prior']['key']) if joint['prior'] else None
            r['job_prior_people']=joint['prior']['people'] if joint['prior'] else 0
            for j,p in enumerate(ROLES):r[f'joint_{p}']=joint['values'][j]/(r['origin_dh_outs'] if p==10 else 1.)
            predictions.append(r)
        print(f'Saved joint job fold {y}/{k}',flush=True)
    budgets=[]
    for spec in pre['reservations']:
        y=spec['origin'];selected=sorted([r for r in predictions if r['origin_year']==y],key=lambda r:r['row_id'])
        dh=spec['origin_inventory']['dh_outs']
        seed=np.array([[r[f'joint_{p}']*(dh if p==10 else 1.) for p in ROLES] for r in selected])
        unknown=sum(r['job_unknown_mass'] for r in selected)
        full=np.array(spec['origin_inventory']['caps'],float)
        caps=full-np.array(spec['outside_reserve'])-unknown/9.
        assert (caps>0).all()
        candidate,receipt=jobs.reconcile(seed,caps)
        budgets.append(dict(origin=y,full_capacity=full.tolist(),outside_reserve=spec['outside_reserve'],
                            unknown_role_reserve=unknown,unknown_per_position=unknown/9.,caps=caps.tolist(),
                            known_seed_total=float(seed.sum()),**receipt))
        for r,values in zip(selected,candidate):
            r['candidate_global_job_factor']=receipt['global_mass_factor']
            r['candidate_column_multipliers']=receipt['multipliers']
            for j,p in enumerate(ROLES):r[f'candidate_{p}']=values[j]/(dh if p==10 else 1.)
    quality=defaultdict(list)
    for c in pl.read_parquet(VALUE/'channel-predictions.parquet').to_dicts():quality[c['row_id']].append(c)
    oldvalue={r['row_id']:r for r in pl.read_parquet(VALUE/'predictions.parquet').to_dicts()}
    details=[]
    for r in predictions:
        v=oldvalue[r['row_id']];entries=quality[r['row_id']]
        assert len(entries)==12
        for field in ['actual_defense','actual_batting','batting_forecast','known_quality_channels','unknown_target_channels']:
            r[field]=v[field]
        r['actual_PA']=r['next_pa'];r['actual_fielding_outs']=sum(r[f'actual_{p}'] for p in POSITIONS)
        r['actual_position_runs']=position_value(r,'actual')
        r['actual_expanded']=None if r['actual_defense'] is None else r['actual_batting']+(r['actual_defense']+r['actual_position_runs'])/10.
        framing=next(c['actual_runs'] for c in entries if c['channel']=='framing')
        r['actual_no_framing']=None if r['actual_expanded'] is None else r['actual_expanded']-framing/10.
        conv=read(OUT/f"model-{r['origin_year']}-{r['outer_fold']}.json")['native_conversions']
        channel_runs={}
        for arm in ARMS:
            native=native_from_outs([r[f'{arm}_{p}'] for p in ROLES],conv)
            for channel,val in native.items():r[f'{arm}_native_{channel}']=val
            runs={}
            for c in entries:
                exposure=r[f'{arm}_{c["channel"][-1]}'] if c['channel'].startswith('range_') else native[c['channel']]
                runs[c['channel']]=exposure*c['history_quality']/c['rate_unit']
            r[f'{arm}_position_runs']=position_value(r,arm)
            r[f'{arm}_defense']=sum(runs.values())
            r[f'{arm}_expanded']=r['batting_forecast']+(r[f'{arm}_position_runs']+r[f'{arm}_defense'])/10.
            r[f'{arm}_no_framing']=r[f'{arm}_expanded']-runs['framing']/10.
            channel_runs[arm]=runs
        for c in entries:
            details.append(dict(row_id=r['row_id'],player_id=r['player_id'],origin_year=r['origin_year'],
                channel=c['channel'],actual_runs=c['actual_runs'],actual_official_exposure=c['actual_official_exposure'],
                history_quality=c['history_quality'],rate_unit=c['rate_unit'],quality_evidence_observed=c['quality_evidence_observed'],
                **{arm+'_runs':channel_runs[arm][c['channel']] for arm in ARMS}))
        assert r['preseason_pa']==v['expected_PA']
    q=pl.DataFrame(predictions,infer_schema_length=None).sort('row_id')
    assert len(q)==12432 and q['row_id'].n_unique()==12432 and q['target_year'].max()==2025
    q.write_parquet(OUT/'predictions.parquet');pl.DataFrame(details,infer_schema_length=None).write_parquet(OUT/'channel-predictions.parquet')
    write('fit-report.json',dict(status='unscored_pending_review',models=modelnotes,budgets=budgets,forecasts=len(q),
        hashes=hashes([OUT/'preflight.json',OUT/'predictions.parquet',OUT/'channel-predictions.parquet']),
        no_2026_outcomes=True,no_deployment=True,player_walkthrough_status='pending'))
    protections();print('Saved joint and constrained forecasts. No score-based choice or quality refit.',flush=True)


def score():
    check();fitnote=read(OUT/'fit-report.json');verify(fitnote['hashes']);verify({m['path']:m['sha256'] for m in fitnote['models']})
    assert not (OUT/'report.json').exists()
    f=pl.read_parquet(OUT/'predictions.parquet');rows=f.to_dicts();metrics={};intervals=[]
    for target in ('expanded','defense','position_runs','no_framing'):
        fields=[a+'_'+target for a in ARMS]
        metrics[target]=dict(all_observed=score_rows(rows,fields,'actual_'+target),
            actual_defenders=score_rows([r for r in rows if r['actual_fielding_outs']>0],fields,'actual_'+target),
            known_quality=score_rows([r for r in rows if r['known_quality_channels']>0],fields,'actual_'+target))
        intervals.append(paired_interval(rows,'candidate_'+target,'reference_'+target,'actual_'+target))
    groups=[]
    for y in (2022,2023,2024):
        for stage in sorted(f['stage'].unique()):
            for band in ('<=24','25-29','30+','unknown'):
                selected=[r for r in rows if r['origin_year']==y and r['stage']==stage and
                    ('unknown' if r['age'] is None else '<=24' if r['age']<=24 else '25-29' if r['age']<=29 else '30+')==band]
                if selected:groups.append(dict(origin=y,stage=stage,age_band=band,rows=len(selected),
                    actual_defenders=sum(r['actual_fielding_outs']>0 for r in selected),
                    expanded=score_rows(selected,[a+'_expanded' for a in ARMS],'actual_expanded'),
                    position=score_rows(selected,[a+'_position_runs' for a in ARMS],'actual_position_runs')))
    cell=[];totals=[]
    inv,_,_=inputs()
    for y in (2022,2023,2024):
        selected=[r for r in rows if r['origin_year']==y]
        actual=np.array([r['actual_job_vector'] for r in selected])
        for arm in ARMS:
            pred=np.array([[r[f'{arm}_{p}']*(r['origin_dh_outs'] if p==10 else 1.) for p in ROLES] for r in selected])
            cell.append(dict(origin=y,arm=arm,rows=len(selected),job_cell_rmse=float(np.sqrt(np.mean((pred-actual)**2)))))
            totals.append(dict(origin=y,arm=arm,predicted_roles=[sum(r[f'{arm}_{p}'] for r in selected) for p in ROLES],
                actual_matched_roles=[sum(r[f'actual_{p}'] for r in selected) for p in ROLES],
                actual_full_roles=[*inv[y+1]['outs'],inv[y+1]['DH_starts']],
                predicted_position_runs=sum(r[f'{arm}_position_runs'] for r in selected),
                actual_position_runs=sum(r['actual_position_runs'] for r in selected)))
    channels=pl.read_parquet(OUT/'channel-predictions.parquet');cs=[]
    for (name,),g in channels.group_by('channel'):
        rs=g.to_dicts()
        for label,s in [('all_observed',rs),('actual_exposure',[r for r in rs if r['actual_official_exposure']>0]),
                        ('measured_history',[r for r in rs if r['quality_evidence_observed']])]:
            cs.append(dict(channel=name,scope=label,metrics=score_rows(s,[a+'_runs' for a in ARMS],'actual_runs')))
    failures=[]
    for name in ('position_runs','defense'):
        m=metrics[name]['all_observed']['per_origin']
        for y in (2022,2023,2024):
            ref=next(r['rmse'] for r in m if r['origin']==y and r['arm']=='reference_'+name)
            cand=next(r['rmse'] for r in m if r['origin']==y and r['arm']=='candidate_'+name)
            if cand>1.05*ref:failures.append(dict(origin=y,metric=name,relative_deterioration=cand/ref-1))
    write('report.json',dict(status='provisional_pending_player_review',metrics=metrics,intervals=intervals,
        groups=groups,job_cell_scores=cell,totals=totals,channels=cs,component_tolerance_failures=failures,
        sparse_profiles=read(OUT/'preflight.json')['sparse_profiles'],
        complete_value_rows=f.filter(pl.col('actual_expanded').is_not_null()).height,
        partial_value_rows=f.filter(pl.col('actual_expanded').is_null()).height,
        no_2026_outcomes=True,no_deployment=True,player_walkthrough_status='pending',
        hashes=hashes([OUT/'fit-report.json',OUT/'predictions.parquet',OUT/'channel-predictions.parquet'])))
    print(json.dumps({name:m['all_observed']['equal_origin'] for name,m in metrics.items()},indent=2),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','fit','score']);args=p.parse_args()
    globals()[args.mode]()
