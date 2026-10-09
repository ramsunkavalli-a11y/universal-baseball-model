"""Fixed joint-budget comparison with same-row source-to-player reviews."""
from collections import defaultdict
from pathlib import Path
import gzip,json
import numpy as np
import polars as pl
from universal_baseball import hitter_role_budget_v1 as joint
from universal_baseball import defense_repertoire as ref
from universal_baseball.defense_value import position_value as existing_position_value
from universal_baseball.storage import sha256_file
from run_defense_jobs_v14 import inputs
from capture_hitter_2027_origin_counts import ROOT,write_once

PUBLIC=ROOT/'reports/model-evidence/hitter-2027-v1'
OUT=ROOT/'reports/generated/hitter-2027-base'


def position_value(values):
    return existing_position_value({f'value_{p}':v for p,v in zip(ref.ROLES,values)},'value')


def main():
    assert not (PUBLIC/'role-budget-test.json').exists()
    inventory,delta,hist=inputs()
    source=ROOT/'reports/generated/defense-repertoire-v9/features.parquet'
    frame=pl.read_parquet(source)
    rows=[]
    for r in frame.to_dicts():
        y,pid=r['origin_year'],r['player_id']
        r['actual_10']+=delta.get((r['target_year'],pid),0)
        r['carry_10']+=delta.get((y,pid),0)
        r.update(ref.make_repertoire(r,hist[pid]))
        r.update(joint.evidence(r,hist[pid],inventory[y]['dh_outs']))
        r['actual_job_total']=sum(r[f'actual_{p}'] for p in range(2,10))+r['actual_10']*inventory[r['target_year']]['dh_outs']
        rows.append(r)
    lookup={r['row_id']:r for r in rows}
    oldpre=ROOT/'reports/generated/defense-repertoire-v9/preflight.json'
    pre=json.loads(oldpre.read_text());checks=[];plans=[]
    for c in pre['cells']:
        y,k=c['origin'],c['fold']
        base=[lookup[i] for i in c['training_row_ids']]
        train=[r for r in base if r['target_year']>=2022]
        test=[lookup[i] for i in c['test_row_ids']]
        assert train and max(r['target_year'] for r in train)<=y
        assert not {r['player_id'] for r in base}&{r['player_id'] for r in test}
        support={key:joint.cell(train,key) for key in {key for r in test for key in joint.keys(r)}}
        assert joint.supported(support[('all',)])
        profiles=defaultdict(set)
        for r in train:profiles[r['stage'],r['age_band'],r['role']].add(r['player_id'])
        checks.append(dict(origin=y,fold=k,training_people=len({r['player_id'] for r in train}),
            support=list(support.values()),sparse_profiles=sum(len(profiles[r['stage'],r['age_band'],r['role']])<20 for r in test),
            target_ceiling=max(r['target_year'] for r in train)))
        plans.append((y,k,base,train,test,support))
    paths=[source,oldpre,Path(__file__),ROOT/'src/universal_baseball/hitter_role_budget_v1.py',ROOT/'docs/hitter-2027-joint-role-check.md',
           ROOT/'reports/generated/defense-budget-v13/reviewed-DH-starts.parquet',ROOT/'reports/generated/defense-position-opportunity-v7/annual-usage.parquet']
    receipt=dict(before_fitting=True,cells=checks,input_hashes={str(p):sha256_file(p) for p in paths})
    first=PUBLIC/'role-budget-preflight.json'
    if first.exists():
        old=json.loads(first.read_text())
        assert old['cells']==checks
        assert all(v==receipt['input_hashes'][p] for p,v in old['input_hashes'].items() if p!=str(Path(__file__)))
        receipt['execution_correction']='First run stopped before scores/output to adapt position_value(row,prefix) signature and deduplicate repeated group calculations. No model recipe or inputs changed.'
        write_once(PUBLIC/'role-budget-preflight-execution-correction.json',receipt)
    else:write_once(first,receipt)
    outputs=[]
    for y,k,base,train,test,support in plans:
        tables={key:joint.cell(train,key,True) for key in support}
        rt={key:ref.mean_group(base,key,True) for key in {key for r in test for key in ref.keys(r)}}
        for r in test:
            r=r.copy();b=ref.predict(r,rt);a=joint.predict(r,tables,inventory[y]['dh_outs'])
            r['joint_trace']=a;r['reference_trace']=b
            for arm,p in [('reference',b),('joint',a)]:
                r.update({f'{arm}_{pos}':v for pos,v in zip(ref.ROLES,p['values'])})
                r[arm+'_mse']=float(np.mean([(r[f'{arm}_{pos}']-r[f'actual_{pos}'])**2 for pos in ref.POSITIONS]))
            outputs.append(r)
    assert len(outputs)==12432 and len({r['row_id'] for r in outputs})==12432
    def score(rr,arm):
        x=np.array([[r[f'{arm}_{p}']-r[f'actual_{p}'] for p in ref.POSITIONS] for r in rr])
        dh=np.array([r[f'{arm}_10']-r['actual_10'] for r in rr])
        pv=np.array([position_value([r[f'{arm}_{p}'] for p in ref.ROLES])-position_value([r[f'actual_{p}'] for p in ref.ROLES]) for r in rr])
        return dict(n=len(rr),RMSE=float(np.sqrt(np.mean(x*x))),MAE=float(np.abs(x).mean()),
            DH_RMSE=float(np.sqrt(np.mean(dh*dh))),position_RMSE=float(np.sqrt(np.mean(pv*pv))),
            field_outs=sum(sum(r[f'{arm}_{p}'] for p in ref.POSITIONS) for r in rr),
            actual_outs=sum(sum(r[f'actual_{p}'] for p in ref.POSITIONS) for r in rr),
            DH_starts=sum(r[f'{arm}_10'] for r in rr),actual_DH=sum(r['actual_10'] for r in rr),
            position_runs=sum(position_value([r[f'{arm}_{p}'] for p in ref.ROLES]) for r in rr),
            actual_position_runs=sum(position_value([r[f'actual_{p}'] for p in ref.ROLES]) for r in rr))
    metrics=[]
    for field in ['all','origin_year','stage','age_band']:
        for val in sorted({r[field] for r in outputs}) if field!='all' else ['all']:
            rr=[r for r in outputs if field=='all' or r[field]==val]
            for arm in ['reference','joint']:metrics.append(dict(group=field,value=val,arm=arm,**score(rr,arm)))
    selected={}
    def select(r,why):selected.setdefault(r['row_id'],[]).append(why)
    for pid in [660271,805811,694192,702616,677951,621439,682626,672275]:
        for r in outputs:
            if r['player_id']==pid:select(r,'fixed')
    select(max(outputs,key=lambda r:r['reference_mse']-r['joint_mse']),'largest_gain')
    select(min(outputs,key=lambda r:r['reference_mse']-r['joint_mse']),'largest_harm')
    error=lambda r:sum(r[f'joint_{p}']-r[f'actual_{p}'] for p in ref.POSITIONS)
    select(max(outputs,key=error),'false_high');select(min(outputs,key=error),'false_low')
    regular=[r for r in outputs if r['next_pa']>=200]
    select(sorted(regular,key=lambda r:r['joint_mse'])[len(regular)//2],'ordinary_measured')
    walks=[]
    def detail(r):
        for arm in ['reference','joint']:
            assert np.allclose([r[f'{arm}_{p}'] for p in ref.ROLES],r[arm+'_trace']['values'])
        assert np.isclose(sum(r[f'joint_{p}'] for p in ref.POSITIONS)+r['joint_10']*inventory[r['origin_year']]['dh_outs'],
                          r['joint_trace']['job_budget']-r['joint_trace']['unallocated'])
        return dict(row=r,source=[h for h in hist[r['player_id']] if r['origin_year']-2<=h['season']<=r['target_year']],
                    source_origin_ceiling=r['origin_year'],realized_season=r['target_year'])
    for rid,reasons in selected.items():
        r=next(r for r in outputs if r['row_id']==rid)
        pool=[s for s in outputs if s['origin_year']==r['origin_year'] and s['player_id']!=r['player_id'] and s['role']==r['role'] and s['stage']==r['stage']]
        peers=sorted(pool,key=lambda s:(abs(s['pa_0']-r['pa_0']),abs(s['age']-r['age']),s['player_id']))[:3]
        walks.append(dict(reasons=reasons,primary=detail(r),peers=[detail(s) for s in peers],peer_rule='Same origin, role and stage; closest current MLB PA then age and ID, no outcomes'))
    walk=PUBLIC/'role-budget-player-walks.json.gz'
    assert not walk.exists();walk.write_bytes(gzip.compress(json.dumps(walks,allow_nan=False,default=str).encode(),mtime=0))
    output=OUT/'role-budget-historical.parquet';assert not output.exists()
    pl.DataFrame(outputs,infer_schema_length=None).write_parquet(output)
    result=dict(metrics=metrics,player_calculations_replayed=True,player_interpretation='pending_written_review',
                cases=len(walks),predictive_claim='development comparison with old fixed PA',release_approved=False,
                output_hashes={str(p):sha256_file(p) for p in [walk,output]})
    write_once(PUBLIC/'role-budget-test.json',result)
    print(json.dumps(metrics[:8]),flush=True)
    for w in walks:
        r=w['primary']['row']
        print(r['player_name'],r['target_year'],w['reasons'],'reference/joint/actual',
              [[round(r[f'{a}_{p}'],1) for p in ref.ROLES] for a in ['reference','joint','actual']],flush=True)


if __name__=='__main__':main()
