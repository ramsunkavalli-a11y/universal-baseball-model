"""Locked matched-label experiment; no opportunity refit or protected outcomes."""
from pathlib import Path
import json
import sys
import joblib
import numpy as np
import polars as pl
from sklearn.linear_model import Ridge
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits
from fit_practical_hitter_v31 import weights
from prepare_practical_hitter_v33 import safe_matrix
from universal_baseball.forecast_validation import preflight
from universal_baseball.hitter_compatible_value import replacement, labels, UNIT
from universal_baseball.mlb_event_logit import EVENTS, VALUES
from universal_baseball.storage import sha256_file

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reports/generated/practical-hitter-numeric-repair-v53'
OUT=ROOT/'reports/generated/hitter-compatible-value-v63'
ARMS={'common_rate':'common_rate_label','relative_direct':'relative_value_label','common_direct':'common_value_label'}


def read(path):return json.loads(Path(path).read_text(encoding='utf8'))


def write(name,obj):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf8')


def prepare():
    assert not (OUT/'preflight.json').exists(), 'Preserve locked preparation'
    b=read(BASE/'preflight.json');old=pl.read_parquet(BASE/'features.parquet').sort('row_id')
    count_path=ROOT/'reports/generated/practical-hitter-v31/counts.parquet'
    env_path=ROOT/'reports/generated/practical-hitter-reliability-v50/features.parquet'
    ref_path=ROOT/'reports/generated/multiyear-hitter-v1/targets.parquet'
    hist=pl.read_parquet(count_path)
    env=pl.read_parquet(env_path).select('row_id',*[s+'_'+v for s in ['count','origin_env','target_env'] for v in EVENTS])
    f=old.join(env,on='row_id',validate='1:1').sort('row_id')
    assert len(f)==63282 and f.select(old.columns).equals(old)
    dated=hist.filter(pl.col('bucket')=='MLB').with_columns(
        (pl.col('babip_hits')-pl.col('doubles')-pl.col('triples')).alias('raw_1B'),
        pl.col('strike_outs').alias('raw_K'),pl.col('unintentional_walks').alias('raw_UBB'),
        pl.col('hit_by_pitch').alias('raw_HBP'),pl.col('doubles').alias('raw_2B'),
        pl.col('triples').alias('raw_3B'),pl.col('home_runs').alias('raw_HR'))
    dated=dated.with_columns((pl.col('plate_appearances')-pl.sum_horizontal(['raw_'+v for v in EVENTS[1:]])).alias('raw_other'))
    assert dated.unique(['player_id','season']).height==dated.height
    check=f.select('row_id','player_id','target_year','next_pa').join(dated.select('player_id',pl.col('season').alias('target_year'),'plate_appearances',*['raw_'+v for v in EVENTS]),on=['player_id','target_year'],how='left',validate='m:1')
    assert check.filter(pl.col('plate_appearances').is_null()&(pl.col('next_pa')>0)).is_empty()
    actual=check.select([pl.col('raw_'+v).fill_null(0) for v in EVENTS]).to_numpy()
    assert np.array_equal(actual,f.select(['count_'+v for v in EVENTS]).to_numpy())
    assert np.array_equal(actual.sum(1),f['next_pa'].to_numpy())
    ref=pl.read_parquet(ref_path).select('season','schedule_fraction','league_pa').unique().sort('season')
    f=f.join(ref.rename({'season':'origin_year'}),on='origin_year',validate='m:1').sort('row_id')
    rep=replacement(f['league_pa'],f['schedule_fraction'])
    z=labels(actual,f.select(['origin_env_'+v for v in EVENTS]).to_numpy(),f.select(['target_env_'+v for v in EVENTS]).to_numpy(),rep)
    assert np.allclose(z['relative_rate'],f['next_batting_rate'],atol=1e-10)
    assert np.allclose(f['origin_replacement_rate'],570/f['league_pa'].to_numpy(),atol=1e-12)
    f=f.with_columns(pl.col('origin_replacement_rate').alias('old_origin_replacement_rate'),
        pl.col('next_batting_rate').alias('old_relative_rate_label'),pl.col('next_value').alias('old_relative_value_label'),
        pl.Series('origin_replacement_rate',rep),pl.Series('origin_index',f.select(['origin_env_'+v for v in EVENTS]).to_numpy()@VALUES),
        pl.Series('actual_index',z['actual_index']),*[pl.Series(k+'_label',z[k]) for k in ['common_rate','relative_rate','common_value','relative_value']],
        pl.Series('next_value',z['common_value']))
    assert not set(['origin_replacement_rate','league_pa','schedule_fraction','origin_index','actual_index'])&set(b['rate_features']+b['pa_features'])
    q=pl.read_parquet(BASE/'scored-predictions.parquet').sort('row_id')
    ev=f.filter(pl.col('row_id').is_in(q['row_id'])).sort('row_id')
    assert ev['row_id'].equals(q['row_id']) and len(ev)==30506
    assert np.allclose(q['next_batting_rate'],ev['common_rate_label'],atol=1e-10)
    expected_delta=ev['next_pa'].to_numpy()*(ev['origin_replacement_rate'].to_numpy()-ev['old_origin_replacement_rate'].to_numpy())
    assert np.allclose(ev['common_value_label'].to_numpy()-q['next_value'].to_numpy(),expected_delta,atol=1e-10)
    OUT.mkdir(parents=True,exist_ok=True);f.write_parquet(OUT/'features.parquet')
    cases=[]
    for pid,y in [(543760,2020),(518692,2020),(665489,2020),(592450,2024),(592450,2016),(665742,2017),(680574,2024)]:
        a=f.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y))
        if a.is_empty():raise ValueError((pid,y))
        o=a.row(0,named=True)
        cases.append(dict(player=o['player_name'],player_id=pid,origin_year=y,next_pa=o['next_pa'],
            league_pa=o['league_pa'],schedule_fraction=o['schedule_fraction'],old_reference=o['old_origin_replacement_rate'],corrected_reference=o['origin_replacement_rate'],
            old_common_value=o['next_pa']*(o['common_rate_label']/600+o['old_origin_replacement_rate']),corrected_common_value=o['common_value_label'],
            old_relative_rate=o['old_relative_rate_label'],common_rate=o['common_rate_label'],
            target_event_counts=dict(zip(EVENTS,actual[np.where(f['row_id'].to_numpy()==o['row_id'])[0][0]].tolist())),
            source_history=hist.filter((pl.col('player_id')==pid)&pl.col('season').is_between(y-2,y)).sort('season','bucket').to_dicts(),
            included_in_evaluation=bool(o['row_id'] in q['row_id']),
            interpretation='Only the value reference changes here; neither forecast PA nor fitted talent is repaired by this arithmetic correction. Zero future PA supplies no observed batting rate.'))
    write('source-reconciliation.json',dict(source_rows=len(f),evaluation_rows=len(q),independent_event_reconstruction_exact=True,
        relative_rate_labels_exact=True,existing_common_rate_labels_exact=True,only_declared_reference_value_difference=True,
        source_case_review_status='pending',cases=cases,season_references=ref.with_columns(pl.Series('corrected_reference',replacement(ref['league_pa'],ref['schedule_fraction']))).to_dicts()))
    supports=[];profiles=[];cells=[]
    keys=['stage','prior_debut','age_band','workload_band','quality_band']
    def profile(g):return g.with_columns((pl.col('age')//5).alias('age_band'),(pl.col('pa_0')//100).alias('workload_band'),(pl.col('quality_0')//1).alias('quality_band'))
    for c in b['cells']:
        tr=f.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id');te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id');notes={}
        for arm,target in ARMS.items():
            sub=tr.filter(pl.col('next_pa')>0) if arm=='common_rate' else tr
            names=b['rate_features'] if arm=='common_rate' else b['pa_features']
            s,n=preflight(sub,te,cutoff=c['year'],fold=c['fold'],features=names,expected_keys=te.select('row_id','horizon').iter_rows())
            assert np.isfinite(sub[target].to_numpy()).all()
            supports.append(s.with_columns(pl.lit(arm).alias('head')));notes[arm]=n
            groups=profile(sub).group_by(keys).agg(pl.col('player_id').n_unique().alias('profile_players'))
            profiles.append(profile(te).select('row_id',*keys).join(groups,on=keys,how='left',validate='m:1').with_columns(pl.col('profile_players').fill_null(0),pl.lit(arm).alias('head')))
        cells.append(dict(**c,compatible_preflight=notes))
        print('Preflight',c['year'],c['fold'],flush=True)
    pl.concat(supports).write_parquet(OUT/'support.parquet');pl.concat(profiles).write_parquet(OUT/'profile-support.parquet')
    paths=[BASE/'features.parquet',BASE/'preflight.json',BASE/'scored-predictions.parquet',count_path,env_path,ref_path,OUT/'features.parquet',OUT/'support.parquet',OUT/'profile-support.parquet',Path(__file__),ROOT/'src/universal_baseball/hitter_compatible_value.py',ROOT/'scripts/prepare_practical_hitter_v33.py',ROOT/'scripts/fit_practical_hitter_v31.py',ROOT/'docs/hitter-compatible-value-v63-contract.md']
    write('preflight.json',dict(before_fitting=True,cells=cells,rate_features=b['rate_features'],pa_features=b['pa_features'],settings=b['settings'],ridge_alpha=100,arms=ARMS,input_hashes={str(p):sha256_file(p) for p in paths},protected_outcomes_used=False))


def fit():
    pre=read(OUT/'preflight.json')
    assert read(OUT/'source-reconciliation.json')['source_case_review_status']=='complete'
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    f=pl.read_parquet(OUT/'features.parquet');base=pl.read_parquet(BASE/'scored-predictions.parquet');fits=[]
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y,k=c['year'],c['fold'];path=OUT/f'forecast-{y}-{k}.parquet'
            if path.exists():
                note=read(OUT/f'fit-{y}-{k}.json');assert sha256_file(path)==note['prediction_sha256']
                for h in note['heads']:assert sha256_file(Path(h['path']))==h['sha256']
                fits.append(note);continue
            tr=f.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id');te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            q=base.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id');assert q['row_id'].equals(te['row_id'])
            q=q.with_columns(pl.col('next_value').alias('legacy_actual_value'),pl.col('origin_replacement_rate').alias('legacy_origin_replacement_rate'),
                te['origin_replacement_rate'],te['common_value_label'].alias('next_value'),te['relative_value_label'],te['common_rate_label'].alias('next_batting_rate'))
            q=q.with_columns(pl.col('repaired_pa').alias('baseline_pa'),pl.col('repaired_rate').alias('baseline_rate'),
                (pl.col('repaired_pa')*(pl.col('repaired_rate')/600+pl.col('origin_replacement_rate'))).alias('baseline_value'),
                (pl.col('steamer_pa')*(pl.col('steamer_rate')/600+pl.col('origin_replacement_rate'))).alias('steamer_value'))
            heads=[]
            for arm,target in pre['arms'].items():
                sub=tr.filter(pl.col('next_pa')>0) if arm=='common_rate' else tr
                names=pre['rate_features'] if arm=='common_rate' else pre['pa_features']
                w=weights(sub)
                if arm=='common_rate':w*=sub['next_pa'].to_numpy();w*=len(w)/w.sum()
                x=safe_matrix(sub,names) if arm=='common_rate' else sub.select(names).to_numpy()
                tx=safe_matrix(te,names) if arm=='common_rate' else te.select(names).to_numpy()
                model=Ridge(alpha=pre['ridge_alpha']) if arm=='common_rate' else HistGradientBoostingRegressor(**pre['settings'])
                model.fit(x,sub[target].to_numpy(),sample_weight=w);pred=model.predict(tx);assert np.isfinite(pred).all()
                mp=OUT/f'{arm}-{y}-{k}.joblib';joblib.dump(model,mp,compress=3)
                assert np.allclose(joblib.load(mp).predict(tx),pred,rtol=0,atol=1e-10)
                value=q['baseline_pa'].to_numpy()*(pred/600+q['origin_replacement_rate'].to_numpy()) if arm=='common_rate' else pred.copy()
                value[q['hard_unavailable'].to_numpy()|q['reported_retired'].to_numpy()]=0
                q=q.with_columns(pl.Series(arm+'_raw',pred),pl.Series(arm+'_value',value),pl.col('baseline_pa').alias(arm+'_pa'))
                if arm=='common_rate':q=q.with_columns(pl.Series(arm+'_rate',pred))
                heads.append(dict(head=arm,path=str(mp),sha256=sha256_file(mp),training_rows=len(sub),training_players=sub['player_id'].n_unique(),max_target_year=int(sub['target_year'].max()),saved_replay_pass=True))
            q.write_parquet(path);note=dict(year=y,fold=k,heads=heads,prediction_sha256=sha256_file(path));write(f'fit-{y}-{k}.json',note);fits.append(note)
            print('Saved and replayed',y,k,flush=True)
    q=pl.concat([pl.read_parquet(OUT/f"forecast-{c['year']}-{c['fold']}.parquet") for c in pre['cells']]).sort('row_id')
    assert len(q)==30506 and q['baseline_pa'].equals(base.sort('row_id')['repaired_pa']) and q['baseline_rate'].equals(base.sort('row_id')['repaired_rate'])
    q.write_parquet(OUT/'predictions.parquet');write('fits.json',fits)
    write('fit-report.json',dict(heads=105,all_saved_heads_replayed=True,baseline_pa_rate_exact=True,player_walkthrough_status='pending',protected_outcomes_used=False,frozen_forecast_changed=False))


if __name__=='__main__':{'prepare':prepare,'fit':fit}[sys.argv[1]]()
