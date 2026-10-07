"""Resume unchanged cells, with lossless compressed evidence after disk exhaustion."""
from collections import defaultdict
from pathlib import Path
import json
import math
import gzip
import hashlib

import numpy as np
import polars as pl

from run_hitter_finite_return_baseline import protections, save
from universal_baseball.storage import sha256_file as ordinary_sha
from universal_baseball.minor_range_talent import (ReferenceEngine,person_weights,design,ridge_fit,ridge_predict,
    preflight,BASE_NAMES,CHANNELS)

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'reports/generated/defense-minor-counts-v18'
OUT=ROOT/'reports/generated/defense-minor-range-v19'
PUBLIC=ROOT/'reports/model-evidence/defense-minor-range-v19'
ALPHAS=(10,100)


def read(p):
    packed=Path(str(p)+'.gz')
    if packed.exists():
        with gzip.open(packed,'rt',encoding='utf8') as f:return json.load(f)
    return json.loads(p.read_text(encoding='utf8-sig'))


def sha256_file(p):
    packed=Path(str(p)+'.gz')
    if packed.exists():
        with gzip.open(packed,'rb') as f:return hashlib.sha256(f.read()).hexdigest()
    return ordinary_sha(p)


def write(name,value):
    normalized=json.loads(json.dumps(value,allow_nan=False,default=str))
    for folder in (OUT,PUBLIC):
        target=folder/name;packed=Path(str(target)+'.gz')
        target.parent.mkdir(parents=True,exist_ok=True)
        if packed.exists() or (target.exists() and target.stat().st_size>0):
            assert read(target)==normalized, f'Changed saved evidence {target}'
            continue
        data=(json.dumps(value,indent=2,allow_nan=False,default=str)+'\n').encode('utf8')
        with packed.open('xb') as stream:
            with gzip.GzipFile(fileobj=stream,mode='wb',mtime=0) as gz:gz.write(data)
        assert read(target)==normalized


def metrics(rows,column):
    q=[r for r in rows if r['quality_rate'] is not None]
    if not q:return None
    w=person_weights(q);y=np.array([r['quality_rate'] for r in q]);v=np.array([r[column] for r in q]);e=v-y
    return dict(rows=len(q),people=len({r['player_id'] for r in q}),rmse=float(np.sqrt(np.average(e*e,weights=w))),
                mae=float(np.average(np.abs(e),weights=w)),bias=float(np.average(e,weights=w)))


def interval(rows):
    q=[r for r in rows if r['quality_rate'] is not None];by=defaultdict(list)
    for r in q:by[r['player_id']].append(r)
    b=[];c=[];bm=[];cm=[]
    for pid,rs in sorted(by.items()):
        be=np.array([r['baseline']-r['quality_rate'] for r in rs]);ce=np.array([r['candidate']-r['quality_rate'] for r in rs])
        b.append(np.mean(be*be));c.append(np.mean(ce*ce));bm.append(np.mean(abs(be)));cm.append(np.mean(abs(ce)))
    rng=np.random.default_rng(19019);ix=rng.integers(0,len(b),size=(2000,len(b)))
    delta=np.sqrt(np.array(c)[ix].mean(axis=1))-np.sqrt(np.array(b)[ix].mean(axis=1))
    mae=np.array(cm)[ix].mean(axis=1)-np.array(bm)[ix].mean(axis=1)
    return dict(seed=19019,replicates=2000,people=len(b),rmse_delta_interval=np.quantile(delta,[.025,.975]).tolist(),
                mae_delta_interval=np.quantile(mae,[.025,.975]).tolist())


def main():
    protections();assert (OUT/'archive-index.json').exists(),'Require verified lossless recovery'
    original_preflight=read(OUT/'run-preflight.json')
    for path,h in original_preflight['hashes'].items():assert sha256_file(Path(path))==h,path
    assert not (OUT/'resume-preflight.json.gz').exists(),'Do not restart a resumed run without checking its live handle'
    write('resume-preflight.json',dict(before_remaining_fits=True,statistical_rules_unchanged=True,
        hashes={str(p):sha256_file(p) for p in (Path(__file__),ROOT/'docs/defense-minor-range-v19-storage-amendment.md',
                ROOT/'scripts/compress_minor_range_v19_evidence.ps1',OUT/'run-preflight.json',OUT/'archive-index.json')}))
    reviewed=read(SOURCE/'final-review.json');assert reviewed['player_walkthrough_status']=='complete'
    for n in ('final-review','source-preflight','source-review','support-preflight','support-review','independent-review'):
        for path,h in read(SOURCE/f'{n}.json')['hashes'].items():assert sha256_file(Path(path))==h,path
    paths=[SOURCE/'counts.parquet',SOURCE/'origins.parquet',SOURCE/'labels.parquet',SOURCE/'final-review.json',
           ROOT/'docs/defense-minor-range-v19-contract.md',ROOT/'scripts/run_minor_range_talent_v19.py',ROOT/'src/universal_baseball/minor_range_talent.py',ROOT/'tests/test_minor_range_talent.py']
    origins=pl.read_parquet(SOURCE/'origins.parquet').filter(pl.col('position')>=3).to_dicts()
    originmap={(r['origin_year'],r['player_id'],r['position']):r for r in origins}
    raw=pl.read_parquet(SOURCE/'counts.parquet').filter(pl.col('position_code').is_in([str(p) for p in range(3,10)])).to_dicts()
    levelby={}
    for r in raw:
        k=(r['season'],r['player_id'],int(r['position_code']))
        if k not in originmap:continue
        level=r['normalized_level'];o=originmap[k];key=k+(level,)
        if key not in levelby:levelby[key]=dict(origin_year=k[0],player_id=k[1],position=k[2],level=level,age=o['age'],outs=0,**{f:0 for f in ('putOuts','assists','errors','chances','throwingErrors')})
        dest=levelby[key];dest['outs']+=r['fielding_outs']
        for f in ('putOuts','assists','errors','chances','throwingErrors'):
            assert r[f] is not None and r[f+'_status']=='recorded';dest[f]+=r[f]
    levelrows=list(levelby.values());byscope=defaultdict(list)
    for r in levelrows:byscope[r['origin_year'],r['player_id'],r['position']].append(r)
    for k,rs in byscope.items():assert sum(r['outs'] for r in rs)==originmap[k]['minor_outs']
    pool=pl.read_parquet(SOURCE/'labels.parquet').filter((pl.col('component')=='range')&(pl.col('window')==3)&(~pl.col('prior_current_MLB_fielding'))).to_dicts()
    evalrows=[r for r in pool if r['origin_year'] in (2021,2022)]
    write('run-preflight.json',dict(before_any_fit=True,no_2026_outcomes=True,previous_goal_turn='Progress: independently reviewed and pushed the minor count audit.',
        population_keys=[[r['origin_year'],r['player_id'],r['position']] for r in evalrows],rows=len(evalrows),
        source_level_rows=len(levelrows),primary_origin=2022,stress_origin=2021,target='fixed same-position 3-year native quality',
        hashes={str(p):sha256_file(p) for p in paths},player_walkthrough_status='pending'))
    engine=ReferenceEngine(levelrows);featurecache={};cells=[];outerpred=[]
    def signals(rows,excluded):
        result=[];details=[]
        for r in rows:
            k=(r['origin_year'],r['player_id'],r['position']);ck=k+(tuple(excluded),)
            if ck not in featurecache:featurecache[ck]=engine.features(byscope[k],excluded)
            s,t=featurecache[ck];result.append(s);details.append(t)
        return np.array(result),details
    def cell(cutoff,outer,held,kind):
        tag=f'{kind}-{cutoff}-{outer}-{held}'
        old=OUT/'cells'/f'{tag}-fit.json'
        if Path(str(old)+'.gz').exists() or (old.exists() and old.stat().st_size>0):
            saved=read(old)
            assert saved['tag']==tag and saved['cutoff']==cutoff and saved['outer_fold']==outer and saved['held_fold']==held
            assert sha256_file(OUT/f'cells/{tag}-preflight.json')==saved['preflight_hash']
            assert sha256_file(Path(saved['feature_path']))==saved['feature_hash']
            cells.append({k:v for k,v in saved.items() if k!='test_prediction_hash_input'})
            print(json.dumps(dict(cell=tag,reused_completed_fit=True)),flush=True)
            return saved['test_prediction_hash_input'],saved['fit_supported']
        excluded=tuple(sorted({outer,held}));tr=[r for r in pool if r['window_end']<=cutoff and r['quality_rate'] is not None and r['player_id']%5 not in excluded]
        te=[r for r in pool if r['origin_year']==cutoff and r['player_id']%5==held and r['player_id']%5!=outer] if kind=='inner' else [r for r in evalrows if r['origin_year']==cutoff and r['player_id']%5==outer]
        if kind=='outer':excluded=(outer,)
        agevalues=[r['age'] for r in tr if r['age'] is not None];median=float(np.median(agevalues)) if agevalues else 23.
        st,tt=signals(tr,excluded);se,et=signals(te,excluded)
        xc=design(tr,st,median,True);xe=design(te,se,median,True)
        audit=preflight(tr,te,cutoff,excluded,xc,xe)
        tag=f'{kind}-{cutoff}-{outer}-{held}'
        audit.update(kind=kind,outer_fold=outer,held_fold=held,age_median=median,candidate_features=list(BASE_NAMES)+list(CHANNELS),before_fit=True)
        write(f'cells/{tag}-preflight.json',audit)
        features=[]
        for scope,rows,sigs,traces,xs in [('train',tr,st,tt,xc),('test',te,se,et,xe)]:
            for r,s,t,x in zip(rows,sigs,traces,xs,strict=True):
                features.append(dict(scope=scope,origin_year=r['origin_year'],player_id=r['player_id'],position=r['position'],
                    signals=s.tolist(),candidate_design=x.tolist(),level_trace=json.dumps(t,allow_nan=False)))
        path=OUT/'cells'/f'{tag}-features.parquet';feature_frame=pl.DataFrame(features,infer_schema_length=None)
        if path.exists():assert pl.read_parquet(path).equals(feature_frame),'Incomplete cell features changed'
        else:feature_frame.write_parquet(path)
        cellout=dict(tag=tag,kind=kind,cutoff=cutoff,outer_fold=outer,held_fold=held,age_median=median,
            fit_supported=audit['fit_supported'],training_people=audit['training_people'],fits={},
            preflight_hash=sha256_file(OUT/f'cells/{tag}-preflight.json'),feature_path=str(path),feature_hash=sha256_file(path))
        preds={}
        for arm,include in [('baseline',False),('candidate',True)]:
            xt=xc if include else xc[:,:len(BASE_NAMES)];xv=xe if include else xe[:,:len(BASE_NAMES)]
            names=(*BASE_NAMES,*CHANNELS) if include else BASE_NAMES
            for alpha in ALPHAS:
                key=f'{arm}-{alpha}'
                if audit['fit_supported']:
                    fit=ridge_fit(xt,np.array([r['quality_rate'] for r in tr]),person_weights(tr),alpha,names)
                    pred=ridge_predict(fit,xv);cellout['fits'][key]=fit
                else:pred=np.zeros(len(te));cellout['fits'][key]=None
                preds[key]=pred
        # Unknown supervised level-position gets the matched baseline, not an extrapolated count effect.
        unseen=np.array([s['unseen_level_position'] for s in audit['profile_rows']])
        for alpha in ALPHAS:preds[f'candidate-{alpha}'][unseen]=preds[f'baseline-{alpha}'][unseen]
        records=[]
        for i,r in enumerate(te):
            records.append(dict(origin_year=r['origin_year'],player_id=r['player_id'],player_name=r['player_name'],position=r['position'],
                level=r['level'],age=r['age'],age_band=r['age_band'],sample_band=r['sample_band'],minor_outs=r['minor_outs'],
                quality_rate=r['quality_rate'],quality_status=r['quality_status'],future_opportunities=r['future_opportunities'],future_runs=r['future_runs'],
                future_official_position_outs=r['future_official_position_outs'],future_other_position_outs=r['future_other_position_outs'],
                fold=outer,cell_tag=tag,**{k:float(v[i]) for k,v in preds.items()},support=audit['profile_rows'][i]))
        cellout['test_prediction_hash_input']=records
        write(f'cells/{tag}-fit.json',cellout);cells.append({k:v for k,v in cellout.items() if k!='test_prediction_hash_input'})
        print(json.dumps(dict(cell=tag,training_people=audit['training_people'],test_rows=len(te),supported=audit['fit_supported'])),flush=True)
        return records,audit['fit_supported']
    tuning=[]
    for year in (2021,2022):
        inner_years=sorted({r['origin_year'] for r in pool if r['window_end']<=year})[-2:]
        for fold in range(5):
            val=[]
            for iy in inner_years:
                for held in range(5):
                    if held==fold:continue
                    records,supported=cell(iy,fold,held,'inner')
                    if supported:val.extend(records)
            selections={}
            for arm in ('baseline','candidate'):
                scores={str(alpha):metrics(val,f'{arm}-{alpha}') for alpha in ALPHAS}
                selected=min(ALPHAS,key=lambda a:(scores[str(a)]['rmse'],-a)) if val and metrics(val,f'{arm}-10') is not None else 100
                selections[arm]=selected
                tuning.append(dict(origin=year,outer_fold=fold,arm=arm,validation_origins=inner_years,selected_alpha=selected,
                    scores=scores,supported_validation_rows=len(val),default_if_no_support=not bool(val)))
            records,_=cell(year,fold,fold,'outer')
            for r in records:
                r['baseline']=r[f"baseline-{selections['baseline']}"];r['candidate']=r[f"candidate-{selections['candidate']}"]
                if r['support']['unseen_level_position']:r['candidate']=r['baseline']
                r['neutral']=0.;r['baseline_alpha']=selections['baseline'];r['candidate_alpha']=selections['candidate']
            outerpred.extend(records)
    assert len(outerpred)==len(evalrows) and {(r['origin_year'],r['player_id'],r['position']) for r in outerpred}=={(r['origin_year'],r['player_id'],r['position']) for r in evalrows}
    # Struct fields stay explicit; nested fit/input traces are retained separately.
    pl.DataFrame(outerpred,infer_schema_length=None).write_parquet(OUT/'predictions.parquet')
    groups=[];overall=[]
    for y in (2021,2022):
        rs=[r for r in outerpred if r['origin_year']==y]
        overall.append(dict(origin=y,rows=len(rs),measured_people=len({r['player_id'] for r in rs if r['quality_rate'] is not None}),
                            scores={arm:metrics(rs,arm) for arm in ('neutral','baseline','candidate')},interval=interval(rs),
                            statuses=dict(__import__('collections').Counter(r['quality_status'] for r in rs))))
        for column in ('position','level','age_band','sample_band'):
            for g in sorted({r[column] for r in rs},key=str):
                q=[r for r in rs if r[column]==g]
                groups.append(dict(origin=y,group=column,value=g,rows=len(q),scores={arm:metrics(q,arm) for arm in ('neutral','baseline','candidate')}))
    write('fit-report.json',dict(status='fitted_pending_independent_and_player_review',overall=overall,groups=groups,tuning=tuning,cells=cells,
        no_2026_outcomes=True,player_walkthrough_status='pending',no_forecast_or_explorer_change=True,
        hashes={str(p):sha256_file(p) for p in (OUT/'run-preflight.json',OUT/'predictions.parquet')}))
    protections();print(json.dumps(overall),flush=True)


if __name__=='__main__':main()
