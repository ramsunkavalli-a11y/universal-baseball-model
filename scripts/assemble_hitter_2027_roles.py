"""Refreshed joint role workload and native opportunities; no skill/WAR fitting."""
from collections import defaultdict
from pathlib import Path
import gzip,json
import numpy as np
import polars as pl
from universal_baseball import hitter_role_fallback_v1 as model
from universal_baseball.defense_repertoire import ROLES
from universal_baseball.defense_opportunity_bridge import CHANNELS,native_conversion,native_from_outs
from universal_baseball.post_arrival_history import player_fold
from universal_baseball.storage import sha256_file
from run_defense_jobs_v14 import inputs
from run_defense_opportunity_v8 import native_exposure
from capture_hitter_2027_origin_counts import ROOT,write_once

OUT=ROOT/'reports/generated/hitter-2027-base'
PUBLIC=ROOT/'reports/model-evidence/hitter-2027-v1'
NEW=ROOT/'reports/generated/hitter-2027-nonbatting-source'


def main():
    assert not (PUBLIC/'role-production-review.json').exists()
    inventory,delta,hist=inputs()
    paths=[]
    def read(p):paths.append(p);return pl.read_parquet(p)
    usage=read(ROOT/'reports/generated/hitter-2027-position-source/annual-usage-reviewed.parquet')
    official=defaultdict(dict)
    for r in usage.to_dicts():
        hist[r['player_id']].append(r)
        if r['is_mlb']:official[r['player_id']]={p:r[f'outs_{p}'] for p in range(2,10)}
    dh_outs=129239/4858
    q=read(ROOT/'reports/generated/hitter-2027-batting-refresh/forecast.parquet').to_dicts()
    old=read(ROOT/'reports/generated/defense-repertoire-v9/features.parquet').filter((pl.col('target_year')>=2022)&(pl.col('next_pa')>0)).to_dicts()
    fresh=read(ROOT/'reports/generated/hitter-translation-inputs-2025/forecast-inputs-0.parquet').select('player_id','origin_year','target_year','outer_fold','source_position','pa_0','stage','age').to_dicts()
    counts=read(OUT/'values.parquet').filter(pl.col('season')==2026)
    actualpa=dict(zip(counts['player_id'],counts['mlb_pa']))
    current={r['player_id']:r for r in usage.filter(pl.col('is_mlb')).to_dicts()}
    for r in old:r['actual_10']+=delta.get((r['target_year'],r['player_id']),0)
    for r in fresh:
        pid=r['player_id'];r['next_pa']=actualpa.get(pid,0)
        if not r['next_pa']:continue
        assert r['origin_year']==2025 and r['target_year']==2026
        r.update({f'actual_{p}':current.get(pid,{}).get(f'outs_{p}' if p!=10 else 'starts_10',0) for p in ROLES})
        old.append(r)
    for r in old:
        r.update(model.evidence(r,hist[r['player_id']],inventory[r['origin_year']]['dh_outs']))
        ratio=dh_outs if r['target_year']==2026 else inventory[r['target_year']]['dh_outs']
        r['actual_job_total']=sum(r[f'actual_{p}'] for p in ROLES[:-1])+ratio*r['actual_10']
    assert len({(r['player_id'],r['origin_year']) for r in old})==len(old)
    for r in q:
        r['preseason_pa']=r['expected_pa'];r.update(model.evidence(r,hist[r['player_id']],dh_outs))
    native=read(ROOT/'reports/generated/defense-opportunity-v8/opportunity-records.parquet').to_dicts()
    for path in [NEW/'framing-annual.parquet',NEW/'catcher-opportunities.parquet',NEW/'arm-official-scope-annual.parquet',NEW/'receiving-native-annual.parquet']:
        for r in read(path).to_dicts():
            if 'pitches' in r:
                channel,n,valid='framing',r['pitches'],r['exposure_valid'] and r['framing_measurement_valid']
            elif 'component' in r:
                channel,n,valid=r['component'],r['opportunities'],r['exposure_valid'] and r['measurement_valid']
            else:
                channel,n=r['kind'],r['opportunities'];valid=r['isolated_outfield_quality_valid'] if channel=='arm' else r['quality_valid']
            exposure=native_exposure(official[r['player_id']],channel)
            native.append(dict(channel=channel,season=2026,player_id=r['player_id'],opportunities=n,
                official_exposure=exposure,valid=bool(valid) and exposure>0 and n is not None and n>=0))
    assert len({(r['season'],r['player_id'],r['channel']) for r in native})==len(native)
    assert max(r['season'] for r in native)==2026
    plans=[];pre=[]
    for fold in range(5):
        train=[r for r in old if r['outer_fold']!=fold];test=[r for r in q if r['outer_fold']==fold]
        assert not {r['player_id'] for r in train}&{r['player_id'] for r in test}
        assert max(r['target_year'] for r in train)==2026
        keys={key for r in test for key in model.keys(r)}
        tables={k:model.cell(train,k) for k in keys};assert model.supported(tables[('all',)])
        pre.append(dict(fold=fold,training_people=len({r['player_id'] for r in train}),training_rows=len(train),
            group_support=list(tables.values()),player_disjoint=True,target_ceiling=2026))
        plans.append((fold,train,test,keys))
    paths.extend([Path(__file__),ROOT/'src/universal_baseball/hitter_role_budget_v1.py',ROOT/'src/universal_baseball/hitter_role_fallback_v1.py',ROOT/'docs/hitter-2027-role-production-refresh.md'])
    write_once(PUBLIC/'role-production-preflight.json',dict(before_fitting=True,cells=pre,input_hashes={str(p):sha256_file(p) for p in paths}))
    outputs=[];models=[]
    for fold,train,test,keys in plans:
        tables={k:model.cell(train,k,True) for k in keys}
        conversions={c:native_conversion([r for r in native if r['channel']==c],2026,fold,player_fold) for c in CHANNELS}
        models.append(dict(fold=fold,tables=list(tables.values()),native_conversions=conversions))
        for r in test:
            p=model.predict(r,tables,dh_outs);nat=native_from_outs(p['values'],conversions)
            cap=r['participation_probability']*162*27
            outputs.append(dict(player_id=r['player_id'],player_name=r['player_name'],origin_year=2026,target_year=2027,
                stage=r['stage'],expected_pa=r['expected_pa'],participation_probability=r['participation_probability'],
                conditional_pa=r['conditional_pa'],source_position=r['source_position'],
                **{f'outs_{pos}':v for pos,v in zip(ROLES[:-1],p['values'][:-1])},DH_starts=p['values'][-1],
                **{f'native_{c}':v for c,v in nat.items()},evidence={k:r[k] for k in ['role_shares','role','family','current_vector','fallback_vector','fallback_sources','reliability','unknown']},
                calculation=p,expected_capacity=cap,capacity_warning=p['job_budget']>cap+1e-8,
                uncertain_minor_role=r['stage']!='Current MLB',native_conversions=conversions))
    by={r['player_id']:r for r in outputs};assert len(by)==len(q)==4851
    cases=json.loads(gzip.decompress((PUBLIC/'base-input-player-walks.json.gz').read_bytes()))['cases']
    ids={w['player_id'] for c in cases for w in [c['primary'],*c['peers']]}
    ids.update(r['player_id'] for r in sorted(outputs,key=lambda r:r['calculation']['job_budget'],reverse=True)[:5])
    ids.update(r['player_id'] for r in outputs if r['capacity_warning'])
    walks=[]
    for pid in sorted(ids):
        r=by[pid];p=r['calculation'];e=r['evidence'];jobs=np.array([r[f'outs_{pos}'] for pos in ROLES[:-1]]+[r['DH_starts']*dh_outs])
        assert np.allclose(jobs,p['job_budget']*np.array(e['role_shares']))
        assert np.isclose(p['job_outs_per_PA'],e['reliability']*(sum(e['current_vector'])/next(a['pa_0'] for a in q if a['player_id']==pid) if e['reliability'] else 0)+(1-e['reliability'])*p['prior']['job_outs_per_PA'])
        assert all(v==0 for v,s in zip(jobs,e['role_shares']) if s==0)
        walks.append(dict(forecast=r,history=[h for h in hist[pid] if 2024<=h['season']<=2026],
            interpretation='Shares use observed field/DH exposure, including larger older MLB evidence; native chances follow the relevant position only. Role changes are uncertain. No defensive skill or WAR awarded here.'))
    output=OUT/'role-opportunities.parquet';assert not output.exists();pl.DataFrame(outputs,infer_schema_length=None).write_parquet(output)
    walk=PUBLIC/'role-production-player-walks.json.gz';assert not walk.exists();walk.write_bytes(gzip.compress(json.dumps(walks,allow_nan=False,default=str).encode(),mtime=0))
    write_once(PUBLIC/'role-production-review.json',dict(people=len(outputs),models=models,player_calculations_replayed=True,
        player_interpretation='pending_written_review',role_unknown=sum(r['evidence']['unknown'] for r in outputs),
        capacity_warnings=[dict(player_id=r['player_id'],name=r['player_name'],budget=r['calculation']['job_budget'],capacity=r['expected_capacity']) for r in outputs if r['capacity_warning']],
        totals={**{f'outs_{p}':sum(r[f'outs_{p}'] for r in outputs) for p in ROLES[:-1]},'DH_starts':sum(r['DH_starts'] for r in outputs)},
        output_hashes={str(p):sha256_file(p) for p in [output,walk]},full_model_released=False))
    for pid in [804944,805811,808393,592450,665487,660271,672275,596019]:
        r=by[pid];print(r['player_name'],[(p,round(r[f'outs_{p}']/3,1)) for p in ROLES[:-1] if r[f'outs_{p}']>0],round(r['DH_starts'],1),r['capacity_warning'],flush=True)


if __name__=='__main__':main()
