"""No-fit common-event comparison; never recenter forecasts on future means."""
from pathlib import Path
import json
import numpy as np
import polars as pl
from universal_baseball.mlb_event_logit import EVENTS,VALUES,NEUTRAL_WOBA_SCALE
from universal_baseball.public_archive import REQUIRED
from universal_baseball.storage import sha256_file
from score_practical_hitter_v31 import rate_score,paired
import evaluate_hitter_reliability_v50 as previous

ROOT=previous.ROOT;OUT=ROOT/'reports/generated/practical-hitter-public-units-v51'
ARMS=['working','binary','fixed','learned','steamer','zips']
UNIT=600/(10*NEUTRAL_WOBA_SCALE)


def write(name,value):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_text(json.dumps(value,indent=2,allow_nan=False,ensure_ascii=False)+'\n',encoding='utf8')


def metrics(g,arm):
    rows=[]
    for _,q in g.group_by('target_year'):
        error=(q[arm+'_value']-q['next_value']).to_numpy()
        rows.append([np.mean(error**2),np.mean(abs(error)),np.mean(error)])
    v=np.mean(rows,axis=0)
    return dict(rmse=float(np.sqrt(v[0])),mae=float(v[1]),bias=float(v[2]),expected_total=float(g[arm+'_value'].sum()))


def prepare():
    assert previous.prior.old.r.read(previous.OUT/'report.json')['player_walkthrough_status']=='complete'
    assert not (OUT/'audit.json').exists(),'Preserve previous audit evidence'
    OUT.mkdir(parents=True,exist_ok=True)
    f=pl.read_parquet(previous.OUT/'scored-predictions.parquet').filter(pl.col('target_year').is_between(2022,2025))
    source=pl.read_parquet(previous.OUT/'features.parquet')
    cols=['row_id',*[stem+'_'+ev for stem in ['count','origin_env','target_env'] for ev in EVENTS]]
    f=f.join(source.select(cols),on='row_id',validate='1:1')
    origin=f.select(['origin_env_'+ev for ev in EVENTS]).to_numpy()@VALUES
    target=f.select(['target_env_'+ev for ev in EVENTS]).to_numpy()@VALUES
    counts=f.select(['count_'+ev for ev in EVENTS]).to_numpy();actual_pa=counts.sum(1)
    assert np.array_equal(actual_pa,f['next_pa'].to_numpy())
    index=np.divide(counts@VALUES,actual_pa,out=np.zeros(len(f)),where=actual_pa>0)
    active=actual_pa>0
    assert np.allclose((index[active]-target[active])*UNIT,f['next_batting_rate'].to_numpy()[active])
    f=f.with_columns(pl.Series('origin_index',origin),pl.Series('target_index',target),pl.Series('actual_index',index),
        pl.Series('old_actual_rate',f['next_batting_rate'].to_numpy()),pl.Series('old_actual_value',f['next_value'].to_numpy()))
    mappings={'working':'safe_ridge','binary':'binary_scout','fixed':'fixed_reliability','learned':'learned_reliability'}
    for arm,old in mappings.items():
        pa='retired_safe_ridge_pa' if arm=='working' else old+'_pa'
        f=f.with_columns((pl.col(old+'_rate')/UNIT+pl.col('origin_index')).alias(arm+'_index'),pl.col(old+'_rate').alias(arm+'_rate'),pl.col(pa).alias(arm+'_pa'))
    manifest_path=ROOT/'model_artifacts/public-benchmark-intake-v2/verified-archive-manifest.json'
    manifest=json.loads(manifest_path.read_text());hashes={str(p):sha256_file(p) for p in [manifest_path,previous.OUT/'scored-predictions.parquet',previous.OUT/'features.parquet',Path(__file__),ROOT/'docs/practical-hitter-public-units-v51-contract.md']}
    raw_lookup={};intake=[]
    for system in ['steamer','zips']:
        frames=[]
        for record in manifest['records']:
            if record['system'].lower()!=system:continue
            assert record['label_verified'] and record['vintage_class']=='historical_preseason' and record['year'] in range(2022,2026)
            path=ROOT/record['private_file'];assert sha256_file(path)==record['sha256'];hashes[str(path)]=record['sha256']
            raw=pl.read_csv(path,infer_schema=False);data=raw.with_columns(pl.col(c).cast(pl.Float64,strict=True) for c in REQUIRED)
            a=data.select(REQUIRED).to_numpy();assert np.isfinite(a).all() and (a>=0).all()
            assert data.filter(pl.col('IBB')>pl.col('BB')+1e-6).is_empty()
            assert data.filter((pl.col('H')-pl.sum_horizontal(['1B','2B','3B','HR'])).abs()>.001).is_empty()
            assert data.filter((pl.col('PA')-pl.sum_horizontal(['AB','BB','HBP','SF','SH'])).abs()>.001).is_empty()
            data=data.with_columns(pl.col('MLBAMID').cast(pl.Int64,strict=False).alias('player_id'))
            invalid=data.filter(pl.col('player_id').is_null()|(pl.col('player_id')<=0));data=data.filter(pl.col('player_id')>0)
            assert data['player_id'].n_unique()==len(data)
            numerator=.6926*(pl.col('BB')-pl.col('IBB'))+.7222*pl.col('HBP')+.8776*pl.col('1B')+1.2352*pl.col('2B')+1.5572*pl.col('3B')+1.989*pl.col('HR')
            data=data.with_columns(numerator.alias('numerator'))
            frames.append(data.select('player_id',pl.lit(record['year']).alias('target_year'),pl.col('PA').alias('archive_'+system+'_pa'),
                pl.when(pl.col('PA')>0).then(pl.col('numerator')/pl.col('PA')).otherwise(None).alias(system+'_index')))
            raw_lookup[system,record['year']]={r['player_id']:r for r in data.to_dicts()}
            intake.append(dict(system=system,year=record['year'],rows=len(raw),valid=len(data),invalid_ids=len(invalid),zero_forecast_pa=int((data['PA']==0).sum())))
        f=f.join(pl.concat(frames),on=['player_id','target_year'],how='left',validate='1:1')
    coverage=[]
    for (year,),g in f.group_by('target_year'):
        coverage.append(dict(target_year=year,locked_rows=len(g),current_mlb_rows=int((g['pa_0']>0).sum()),
            missing={a:dict(rows=int(g[a+'_index'].null_count()),actual_pa=float(g.filter(pl.col(a+'_index').is_null())['next_pa'].sum())) for a in ['steamer','zips']}))
    # A common origin-centered target reconciles exactly with raw event errors.
    f=f.with_columns(pl.when(pl.col('next_pa')>0).then((pl.col('actual_index')-pl.col('origin_index'))*UNIT).otherwise(0.).alias('next_batting_rate'))
    f=f.with_columns((pl.col('next_pa')*(pl.col('next_batting_rate')/600+pl.col('origin_replacement_rate'))).alias('next_value'))
    for arm in ['steamer','zips']:
        f=f.with_columns(((pl.col(arm+'_index')-pl.col('origin_index'))*UNIT).alias(arm+'_rate'))
    f=f.with_columns(pl.col('archive_steamer_pa').alias('steamer_pa'))
    for arm in ARMS[:-1]:
        f=f.with_columns((pl.col(arm+'_pa')*(pl.col(arm+'_rate')/600+pl.col('origin_replacement_rate'))).alias(arm+'_value'))
    common=f.filter((pl.col('pa_0')>0)&pl.col('steamer_index').is_not_null()&pl.col('zips_index').is_not_null())
    legacy=common.filter(pl.col('v24_pa').is_not_null());assert len(legacy)==1789
    for a in ARMS:
        q=common.filter(pl.col('next_pa')>0)
        assert np.allclose((q[a+'_index']-q['actual_index'])*UNIT,q[a+'_rate']-q['next_batting_rate'])
    scopes=[('legacy_public',legacy),('all_current_common_public',common),('elapsed_6plus',common.filter(pl.col('elapsed')>=6))]
    scopes += [('year_'+str(y),common.filter(pl.col('target_year')==y)) for y in range(2022,2026)]
    scopes += [('current_PA_'+str(lo)+'_'+str(hi),common.filter(pl.col('pa_0').is_between(lo,hi))) for lo,hi in [(1,199),(200,399),(400,2000)]]
    scores=[];intervals=[]
    for label,g in scopes:
        if not len(g):continue
        scores.append(dict(scope=label,rows=len(g),people=g['player_id'].n_unique(),conditional_rows=int((g['next_pa']>0).sum()),
            actual_pa=float(g['next_pa'].sum()),actual_value=float(g['next_value'].sum()),rates={a:rate_score(g,a+'_rate') for a in ARMS},
            delivered={a:metrics(g,a) for a in ARMS[:-1]}))
        if label in ['legacy_public','all_current_common_public','elapsed_6plus']:
            from score_hitter_reliability_v50 import rate_interval
            intervals += [dict(scope=label,**rate_interval(g,'binary',ref)) for ref in ['steamer','zips']]
            intervals.append(dict(scope=label,**paired(g,'binary','steamer','value')))
    f.write_parquet(OUT/'predictions.parquet');write('scores.json',scores);write('intervals.json',intervals)
    chosen={}
    def add(q,reason):
        assert len(q)>=1;row=q.row(0,named=True);chosen.setdefault(row['row_id'],[]).append(reason)
    for pid,y in [(592450,2024),(691026,2023),(668715,2022),(670541,2024),(458015,2021)]:
        q=common.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y))
        if len(q):add(q,'fixed source diagnostic')
    q=common.filter(pl.col('next_pa')>0).with_columns((pl.col('next_pa')*((pl.col('steamer_rate')-pl.col('next_batting_rate'))**2-(pl.col('binary_rate')-pl.col('next_batting_rate'))**2)).alias('rate_gain'))
    for label,ordered in [('largest PA-weighted rate gain',q.sort('rate_gain',descending=True)),('largest PA-weighted rate harm',q.sort('rate_gain'))]:add(ordered,label)
    q=common.with_columns((pl.col('binary_value')-pl.col('next_value')).alias('error'))
    add(q.sort('error',descending=True),'false high contribution');add(q.sort('error'),'false low contribution')
    add(q.filter(pl.col('next_pa').is_between(200,600)).sort(pl.col('error').abs()),'ordinary contribution')
    add(q.filter(pl.col('elapsed')>=6).sort(pl.col('error').abs()),'ordinary established elapsed 6plus')
    counts_source=pl.read_parquet(ROOT/'reports/generated/practical-hitter-v31/counts.parquet');cases=[]
    for rid,reasons in chosen.items():
        row=common.filter(pl.col('row_id')==rid).row(0,named=True)
        peers=common.filter((pl.col('origin_year')==row['origin_year'])&(pl.col('player_id')!=row['player_id'])).with_columns(
            (((pl.col('age')-row['age'])/3)**2+((pl.col('elapsed')-row['elapsed'])/3)**2+((pl.col('pa_0')-row['pa_0'])/200)**2).alias('distance')).sort('distance','player_id').head(4)
        cases.append(dict(origin=row,selection=reasons,public_counts={a:raw_lookup[a,row['target_year']][row['player_id']] for a in ['steamer','zips']},
            source_history=counts_source.filter((pl.col('player_id')==row['player_id'])&pl.col('season').is_between(row['origin_year']-2,row['origin_year'])).sort('season','bucket').to_dicts(),
            peers=peers.select('player_id','player_name','age','elapsed','pa_0','binary_rate','steamer_rate','zips_rate','next_batting_rate','binary_pa','steamer_pa','next_pa','binary_value','steamer_value','next_value','distance').to_dicts()))
    write('cases.json',cases)
    assert all(sha256_file(Path(p))==h for p,h in hashes.items())
    write('audit.json',dict(input_hashes=hashes,locked_rows=len(f),common_current_rows=len(common),legacy_rows=len(legacy),intake=intake,coverage=coverage,
        raw_count_sums_and_rate_reconstruction=True,common_units_verified=True,no_model_fits=True,no_forecast_calibration=True,
        forecasts_use_origin_environment_only=True,player_walkthrough_status='pending',cases=len(cases),protected_outcomes_used=False,frozen_forecast_changed=False))
    print(json.dumps(scores[:3],indent=2));print('Actual cases prepared:',len(cases),flush=True)


if __name__=='__main__':prepare()
