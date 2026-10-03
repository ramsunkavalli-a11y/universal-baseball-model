"""Matched source substitution with fixed hitting and retained opportunity heads."""
from pathlib import Path
import json
import sys
import joblib
import numpy as np
import polars as pl
from sklearn.ensemble import HistGradientBoostingClassifier,HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits
from fit_practical_hitter_v31 import weights
from universal_baseball.forecast_validation import preflight
from universal_baseball.storage import sha256_file
import evaluate_hitter_numeric_repair_v53 as base

ROOT=base.ROOT
OUT=ROOT/'reports/generated/hitter-school-opportunity-v66'
SCHOOL=ROOT/'reports/generated/hitter-cached-school-source-v65'
VALUE=ROOT/'reports/generated/hitter-compatible-value-v63'
REPLACEMENTS={'draft_hs':'school_background_hs','draft_jc':'school_background_jc','draft_college':'school_background_college'}
FIXED=[(701762,2024),(694671,2023),(641355,2016),(624413,2018),(806956,2024),(666160,2016),(621020,2016),(669394,2017)]


def read(p):return json.loads(Path(p).read_text(encoding='utf8'))


def write(name,obj):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf8')


def tagged(f,old=False):
    background=pl.when(pl.col('draft_college')==1).then(pl.lit('college')).when(pl.col('draft_hs')==1).then(pl.lit('hs')).when(pl.col('draft_jc')==1).then(pl.lit('jc')).otherwise(pl.lit('unknown')) if old else pl.col('school_background')
    return f.with_columns(background.alias('background'),
        pl.when(pl.col('age')<19).then(0).when(pl.col('age')<=22).then(1).when(pl.col('age')<=25).then(2).otherwise(3).alias('entry_age_band'),
        pl.when(pl.col('draft_known')==0).then(0).when(pl.col('draft_elapsed')==0).then(1).when(pl.col('draft_elapsed')<=.3).then(2).otherwise(3).alias('entry_time_band'),
        ((pl.col('draft_known')==1)&(pl.col('pick_number')<=15)).alias('top_pick'),
        (pl.sum_horizontal([pl.col(f'{b}_{k}_pa') for b in base.BUCKETS for k in range(3)])<150).alias('thin_pro'))


def prepare():
    assert not (OUT/'preflight.json').exists(),'Preserve an existing experiment'
    source_report=read(SCHOOL/'source-report.json');assert source_report['player_walkthrough_status']=='complete'
    for k in ['input_hashes','output_hashes']:
        for p,h in source_report[k].items():assert sha256_file(Path(p))==h,p
    assert read(VALUE/'report.json')['player_walkthrough_status']=='complete'
    pre=read(base.OUT/'preflight.json');names=pre['pa_features'];assert len(names)==251
    old=pl.read_parquet(base.OUT/'features.parquet').sort('row_id')
    overlay=pl.read_parquet(SCHOOL/'school-overlay.parquet').sort('row_id');assert old['row_id'].equals(overlay['row_id'])
    candidate=old.join(overlay,on='row_id',validate='1:1').with_columns([pl.col(v).alias(k) for k,v in REPLACEMENTS.items()]).sort('row_id')
    for c in old.columns:
        if c not in REPLACEMENTS:assert candidate[c].equals(old[c]),c
    assert candidate['draft_class_unknown'].equals(old['draft_class_unknown'])
    candidate.write_parquet(OUT/'features.parquet') if OUT.exists() else None
    OUT.mkdir(parents=True,exist_ok=True);candidate.write_parquet(OUT/'features.parquet')
    support=[];profile=[];cells=[]
    for c in pre['cells']:
        checks={}
        for arm,f in [('baseline',old),('school',candidate)]:
            tr=f.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id')
            te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            for head,sub in [('participation',tr),('conditional_pa',tr.filter(pl.col('next_pa')>0))]:
                s,note=preflight(sub,te,cutoff=c['year'],fold=c['fold'],features=names,expected_keys=te.select('row_id','horizon').iter_rows())
                support.append(s.with_columns(pl.lit(arm).alias('arm'),pl.lit(head).alias('head')));checks[arm+'_'+head]=note
                for kind,keys in [('broad',['prior_debut','entry_age_band','entry_time_band','background']),
                                  ('refined',['prior_debut','entry_age_band','entry_time_band','background','top_pick','thin_pro','stage'])]:
                    a=tagged(sub,old=arm=='baseline');b=tagged(te,old=arm=='baseline')
                    n=a.group_by(keys).agg(pl.col('player_id').n_unique().alias('profile_people'))
                    profile.append(b.select('row_id',*keys).join(n,on=keys,how='left',validate='m:1').with_columns(
                        pl.col('profile_people').fill_null(0),pl.lit(arm).alias('arm'),pl.lit(head).alias('head'),pl.lit(kind).alias('kind')))
        cells.append(dict(**c,source_preflight=checks))
    pl.concat(support).write_parquet(OUT/'support.parquet');pl.concat(profile,how='diagonal_relaxed').write_parquet(OUT/'profile-support.parquet')
    q=pl.read_parquet(VALUE/'scored-predictions.parquet')
    assert set(q['row_id'])=={rid for c in cells for rid in c['test_row_ids']} and len(q)==30506
    paths=[base.OUT/'preflight.json',base.OUT/'features.parquet',VALUE/'report.json',VALUE/'scored-predictions.parquet',
        SCHOOL/'source-report.json',SCHOOL/'source-cases.json',SCHOOL/'school-overlay.parquet',OUT/'features.parquet',OUT/'support.parquet',OUT/'profile-support.parquet',
        ROOT/'docs/hitter-school-opportunity-v66-contract.md',Path(__file__),ROOT/'scripts/fit_practical_hitter_v31.py']
    changes={k:int((candidate[k]!=old[k]).sum()) for k in REPLACEMENTS}
    write('preflight.json',dict(cells=cells,pa_features=names,settings=pre['settings'],input_hashes={str(p):sha256_file(p) for p in paths},
        changed_input_columns=changes,only_three_source_inputs_changed=True,precise_class_unknown_preserved=True,
        fixed_cases=[dict(player_id=pid,origin_year=y) for pid,y in FIXED],before_fitting=True,protected_outcomes_used=False))
    print('All 140 baseline/candidate full/active source preflights saved before 70 new fits.',changes,flush=True)


def fit():
    pre=read(OUT/'preflight.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    source=pl.read_parquet(OUT/'features.parquet');old=pl.read_parquet(base.OUT/'features.parquet')
    q=pl.read_parquet(VALUE/'scored-predictions.parquet');fits=[]
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            year,fold=c['year'],c['fold'];path=OUT/f'forecast-{year}-{fold}.parquet'
            if path.exists():
                n=read(OUT/f'fit-{year}-{fold}.json');assert sha256_file(path)==n['prediction_sha256']
                for h in n['heads']:assert sha256_file(Path(h['path']))==h['sha256']
                fits.append(n);continue
            tr=source.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id')
            te=source.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            prior_inputs=old.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            result=q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id');assert result['row_id'].equals(te['row_id'])
            baseline_note=read(base.OUT/f'fit-{year}-{fold}.json');raw={};heads=[]
            for head,sub in [('participation',tr),('conditional_pa',tr.filter(pl.col('next_pa')>0))]:
                bh=next(h for h in baseline_note['heads'] if h['head']==head);assert sha256_file(Path(bh['path']))==bh['sha256']
                bm=joblib.load(bh['path']);x=prior_inputs.select(pre['pa_features']).to_numpy()
                br=bm.predict_proba(x)[:,1] if head=='participation' else bm.predict(x)
                col='repaired_raw_p' if head=='participation' else 'repaired_raw_conditional_pa'
                assert np.allclose(br,result[col],rtol=0,atol=1e-10),(year,fold,head)
                model=(HistGradientBoostingClassifier if head=='participation' else HistGradientBoostingRegressor)(**pre['settings'])
                target='next_active' if head=='participation' else 'next_pa'
                model.fit(sub.select(pre['pa_features']).to_numpy(),sub[target].to_numpy(),sample_weight=weights(sub))
                x=te.select(pre['pa_features']).to_numpy();raw[head]=model.predict_proba(x)[:,1] if head=='participation' else model.predict(x)
                assert np.isfinite(raw[head]).all()
                mp=OUT/f'{head}-{year}-{fold}.joblib';joblib.dump(model,mp,compress=3)
                heads.append(dict(head=head,path=str(mp),sha256=sha256_file(mp),baseline_path=bh['path'],baseline_sha256=bh['sha256'],
                    training_rows=len(sub),training_people=sub['player_id'].n_unique(),max_target_year=int(sub['target_year'].max())))
            p=raw['participation'].copy();p[result['hard_unavailable'].to_numpy()|result['reported_retired'].to_numpy()]=0
            cond=np.clip(raw['conditional_pa'],1,800);pa=p*cond
            result=result.with_columns(pl.Series('school_raw_p',raw['participation']),pl.Series('school_p',p),
                pl.Series('school_raw_conditional_pa',raw['conditional_pa']),pl.Series('school_conditional_pa',cond),pl.Series('school_pa',pa),
                pl.col('baseline_rate').alias('school_rate'),pl.col('repaired_p').alias('baseline_p'),pl.col('repaired_conditional_pa').alias('baseline_conditional_pa'))
            result=result.with_columns((pl.col('school_pa')*(pl.col('baseline_rate')/600+pl.col('origin_replacement_rate'))).alias('school_value'))
            assert result.select(q.columns).equals(q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id'))
            result.write_parquet(path);n=dict(year=year,fold=fold,heads=heads,prediction_sha256=sha256_file(path));write(f'fit-{year}-{fold}.json',n);fits.append(n)
            print(f'School source {year}/{fold}: two heads saved; baseline replayed.',flush=True)
    result=pl.concat([pl.read_parquet(OUT/f"forecast-{c['year']}-{c['fold']}.parquet") for c in pre['cells']]).sort('row_id')
    assert len(result)==30506 and result.select(q.columns).equals(q.sort('row_id'))
    result.write_parquet(OUT/'predictions.parquet');write('fits.json',fits)
    write('fit-report.json',dict(new_heads=70,baseline_heads_replayed=70,all_old_forecast_columns_exact=True,hitting_unchanged=True,player_walkthrough_status='pending',protected_outcomes_used=False))


if __name__=='__main__':{'prepare':prepare,'fit':fit}[sys.argv[1]]()
