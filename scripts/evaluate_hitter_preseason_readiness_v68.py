"""One matched preseason-vintage opportunity comparison, with fixed hitting."""
from pathlib import Path
import json,sys
import joblib
import numpy as np
import polars as pl
from sklearn.ensemble import HistGradientBoostingClassifier,HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits
from universal_baseball.forecast_validation import preflight
from universal_baseball.storage import sha256_file
from fit_practical_hitter_v31 import weights
import evaluate_hitter_numeric_repair_v53 as base

ROOT=base.ROOT
OUT=ROOT/'reports/generated/hitter-preseason-readiness-v68'
SOURCE=ROOT/'reports/generated/hitter-preseason-readiness-v67'
VALUE=ROOT/'reports/generated/hitter-compatible-value-v63'
FIXED=[(701762,2024),(694671,2023),(641355,2016),(624413,2018),(666160,2016),(669394,2017),(806956,2024),(592450,2016)]

def read(p):return json.loads(Path(p).read_text(encoding='utf8'))
def write(n,o):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/n).write_text(json.dumps(o,indent=2,ensure_ascii=False,allow_nan=False,default=str),encoding='utf8')

def tagged(f):
    return f.with_columns(pl.when(pl.col('scout_listed_0')<0).then(-1).when(pl.col('scout_listed_0')==0).then(0)
        .when(pl.col('scout_rank_score_0')>=.81).then(1).when(pl.col('scout_rank_score_0')>=.51).then(2).otherwise(3).alias('rank_band'),
        pl.when(pl.col('age')<19).then(0).when(pl.col('age')<=22).then(1).when(pl.col('age')<=25).then(2).otherwise(3).alias('age_band'),
        ((pl.col('draft_known')==1)&(pl.col('draft_year')==pl.col('origin_year'))).alias('new_draftee'),
        (pl.sum_horizontal([pl.col(f'{b}_{k}_pa') for b in base.BUCKETS for k in range(3)])<150).alias('thin_pro'))

def prepare():
    assert not (OUT/'preflight.json').exists(),'Preserve prior experiment'
    r=read(SOURCE/'source-report.json');assert r['source_review_status']=='complete'
    assert r['release_date_review_status']=='complete_with_retrospective_table_qualification'
    for k in ['input_hashes','output_hashes','review_hashes']:
        for p,h in r[k].items():assert sha256_file(Path(p))==h,p
    old=pl.read_parquet(base.OUT/'features.parquet').sort('row_id');new=pl.read_parquet(SOURCE/'features.parquet').sort('row_id')
    assert old.drop(r['scouting_columns']).equals(new.drop(r['scouting_columns']))
    pre=read(base.OUT/'preflight.json');names=pre['pa_features'];assert len(names)==251
    OUT.mkdir(parents=True,exist_ok=True);new.write_parquet(OUT/'features.parquet')
    support=[];profiles=[];cells=[]
    for c in pre['cells']:
        checks={};info=r['release_evidence'][str(c['year']+1)]['date']
        for arm,f in [('baseline',old),('preseason',new)]:
            tr=f.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id');te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            assert max(r['release_evidence'][str(y)]['date'] for y in tr['target_year'].unique())<info
            for head,sub in [('participation',tr),('conditional_pa',tr.filter(pl.col('next_pa')>0))]:
                sup,note=preflight(sub,te,cutoff=c['year'],fold=c['fold'],features=names,expected_keys=te.select('row_id','horizon').iter_rows())
                note['preseason_information_date']=info;checks[arm+'_'+head]=note
                support.append(sup.with_columns(pl.lit(arm).alias('arm'),pl.lit(head).alias('head')))
                for kind,keys in [('broad',['prior_debut','stage','age_band','rank_band']),('refined',['prior_debut','stage','age_band','rank_band','new_draftee','thin_pro'])]:
                    a,b=tagged(sub),tagged(te);counts=a.group_by(keys).agg(pl.col('player_id').n_unique().alias('profile_people'))
                    profiles.append(b.select('row_id',*keys).join(counts,on=keys,how='left',validate='m:1').with_columns(
                        pl.col('profile_people').fill_null(0),pl.lit(arm).alias('arm'),pl.lit(head).alias('head'),pl.lit(kind).alias('kind')))
        cells.append(dict(**c,source_preflight=checks,information_date=info))
    pl.concat(support).write_parquet(OUT/'support.parquet');pl.concat(profiles,how='diagonal_relaxed').write_parquet(OUT/'profile-support.parquet')
    q=pl.read_parquet(VALUE/'scored-predictions.parquet');assert len(q)==30506 and set(q['row_id'])=={rid for c in cells for rid in c['test_row_ids']}
    paths=[base.OUT/'preflight.json',base.OUT/'features.parquet',SOURCE/'source-report.json',SOURCE/'features.parquet',SOURCE/'reviewed-source-cases.json',
        OUT/'features.parquet',OUT/'support.parquet',OUT/'profile-support.parquet',VALUE/'scored-predictions.parquet',
        ROOT/'docs/hitter-preseason-readiness-v67-contract.md',Path(__file__),ROOT/'scripts/fit_practical_hitter_v31.py']
    write('preflight.json',dict(cells=cells,pa_features=names,settings=pre['settings'],input_hashes={str(p):sha256_file(p) for p in paths},
        only_scouting_vintage_changed=True,source_qualification=r['release_date_review_status'],checks_before_fits=140,protected_outcomes_used=False))
    print('All actual chronological full/active checks saved before new fits.',flush=True)
    prof=pl.read_parquet(OUT/'profile-support.parquet')
    for pid,y in FIXED:
        rid=new.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y))['row_id'][0]
        print(pid,y,prof.filter((pl.col('row_id')==rid)&(pl.col('kind')=='refined')).select('arm','head','profile_people').to_dicts(),flush=True)

def fit():
    pre=read(OUT/'preflight.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    old=pl.read_parquet(base.OUT/'features.parquet');new=pl.read_parquet(OUT/'features.parquet');q=pl.read_parquet(VALUE/'scored-predictions.parquet');fits=[]
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y,k=c['year'],c['fold'];pp=OUT/f'forecast-{y}-{k}.parquet'
            if pp.exists():
                n=read(OUT/f'fit-{y}-{k}.json');assert sha256_file(pp)==n['prediction_sha256']
                for h in n['heads']:assert sha256_file(Path(h['path']))==h['sha256']
                fits.append(n);continue
            tr=new.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id');te=new.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            before=old.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id');result=q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            assert result['row_id'].equals(te['row_id']);oldnote=read(base.OUT/f'fit-{y}-{k}.json');raw={};heads=[]
            for head,sub in [('participation',tr),('conditional_pa',tr.filter(pl.col('next_pa')>0))]:
                bh=next(h for h in oldnote['heads'] if h['head']==head);assert sha256_file(Path(bh['path']))==bh['sha256']
                bm=joblib.load(bh['path']);x=before.select(pre['pa_features']).to_numpy()
                br=bm.predict_proba(x)[:,1] if head=='participation' else bm.predict(x)
                assert np.allclose(br,result['repaired_raw_p' if head=='participation' else 'repaired_raw_conditional_pa'],rtol=0,atol=1e-10)
                m=(HistGradientBoostingClassifier if head=='participation' else HistGradientBoostingRegressor)(**pre['settings'])
                m.fit(sub.select(pre['pa_features']).to_numpy(),sub['next_active' if head=='participation' else 'next_pa'].to_numpy(),sample_weight=weights(sub))
                x=te.select(pre['pa_features']).to_numpy();raw[head]=m.predict_proba(x)[:,1] if head=='participation' else m.predict(x)
                assert np.isfinite(raw[head]).all();mp=OUT/f'{head}-{y}-{k}.joblib';joblib.dump(m,mp,compress=3)
                heads.append(dict(head=head,path=str(mp),sha256=sha256_file(mp),baseline_path=bh['path'],baseline_sha256=bh['sha256'],
                    training_rows=len(sub),training_people=sub['player_id'].n_unique(),max_target_year=int(sub['target_year'].max())))
            p=raw['participation'].copy();p[result['hard_unavailable'].to_numpy()|result['reported_retired'].to_numpy()]=0
            cond=np.clip(raw['conditional_pa'],1,800)
            result=result.with_columns(pl.Series('preseason_raw_p',raw['participation']),pl.Series('preseason_p',p),
                pl.Series('preseason_raw_conditional_pa',raw['conditional_pa']),pl.Series('preseason_conditional_pa',cond),pl.Series('preseason_pa',p*cond),
                pl.col('baseline_rate').alias('preseason_rate'),pl.col('repaired_p').alias('baseline_p'),pl.col('repaired_conditional_pa').alias('baseline_conditional_pa'))
            result=result.with_columns((pl.col('preseason_pa')*(pl.col('baseline_rate')/600+pl.col('origin_replacement_rate'))).alias('preseason_value'))
            assert result.select(q.columns).equals(q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id'))
            result.write_parquet(pp);note=dict(year=y,fold=k,information_date=c['information_date'],heads=heads,prediction_sha256=sha256_file(pp));write(f'fit-{y}-{k}.json',note);fits.append(note)
            print(f'Preseason {y}/{k}: two heads saved, baseline replayed.',flush=True)
    result=pl.concat([pl.read_parquet(OUT/f"forecast-{c['year']}-{c['fold']}.parquet") for c in pre['cells']]).sort('row_id')
    assert len(result)==30506 and result.select(q.columns).equals(q.sort('row_id'))
    result.write_parquet(OUT/'predictions.parquet');write('fits.json',fits)
    write('fit-report.json',dict(new_heads=70,baseline_heads_replayed=70,unchanged_hitting=True,player_walkthrough_status='pending',protected_outcomes_used=False))

if __name__=='__main__':{'prepare':prepare,'fit':fit}[sys.argv[1]]()
