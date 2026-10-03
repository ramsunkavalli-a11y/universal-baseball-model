"""Independent count-to-input reconciliation and exact saved-head replay."""
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
import prepare_practical_hitter_v31 as r
from universal_baseball.post_arrival_history import player_fold
from universal_baseball.practical_hitter_v30 import EVENTS
from universal_baseball.hitter_v2_evaluation import NEUTRAL_WOBA_SCALE,NEUTRAL_WOBA_WEIGHTS
from universal_baseball.storage import sha256_file


def main():
    pre=r.read(r.OUT/'preflight-ready.json'); raw=pl.read_parquet(r.OUT/'predictions.parquet')
    f=pl.read_parquet(pre['ready_features']);counts=pl.read_parquet(r.OUT/'counts.parquet')
    for p,h in pre['input_hashes'].items(): assert sha256_file(Path(p))==h,p
    assert f['target_year'].max()==2025 and raw['target_year'].max()==2025
    assert f['outer_fold'].to_list()==[player_fold(p) for p in f['player_id']]
    assert len(raw)==sum(c['test_rows'] for c in pre['cells'])
    assert raw['row_id'].n_unique()==len(raw)
    targets=pl.read_parquet(r.ROOT/'reports/generated/multiyear-hitter-v1/targets.parquet')
    stint=pl.read_parquet(r.OUT/'dated-stints.parquet').filter((pl.col('bucket')=='MLB')&(pl.col('season')>=2009))
    weights={'unintentional_walks':'UBB','hit_by_pitch':'HBP','singles':'1B','doubles':'2B','triples':'3B','home_runs':'HR'}
    totals=stint.group_by('season','player_id').agg(pl.col(['plate_appearances',*weights]).sum()).with_columns(
        sum(pl.col(c)*NEUTRAL_WOBA_WEIGHTS[w] for c,w in weights.items()).alias('_weighted'))
    env=totals.group_by('season').agg(pl.col('_weighted').sum().alias('_league_weighted'),pl.col('plate_appearances').sum().alias('_league_pa'))
    q=targets.join(totals,on=['season','player_id'],validate='1:1').join(env,on='season',validate='m:1')
    expected=(q['_weighted'].to_numpy()-q['plate_appearances'].to_numpy()*q['_league_weighted'].to_numpy()/q['_league_pa'].to_numpy())/(NEUTRAL_WOBA_SCALE*10)
    expected+=570*q['schedule_fraction'].to_numpy()*q['plate_appearances'].to_numpy()/q['_league_pa'].to_numpy()
    assert len(q)==len(targets) and np.allclose(expected,q['component_war'].to_numpy(),atol=1e-10,rtol=0)
    for lag in range(3):
        own=targets.select((pl.col('season')+lag).alias('origin_year'),'player_id',pl.col('mlb_pa').alias('_pa'),pl.col('component_war').alias('_v'),
            'schedule_fraction','league_pa')
        z=f.join(own,on=['origin_year','player_id'],how='left',validate='1:1')
        # The environment exists independently of whether the player appeared.
        known=targets.unique('season').select((pl.col('season')+lag).alias('origin_year'),
            pl.col('schedule_fraction').alias('_fraction'),pl.col('league_pa').alias('_league'))
        z=z.join(known,on='origin_year',how='left',validate='m:1').with_columns(pl.col('_pa','_v').fill_null(0))
        rate=570*z['_fraction'].to_numpy()/z['_league'].to_numpy()
        quality=600*(z['_v'].to_numpy()-rate*z['_pa'].to_numpy())/(z['_pa'].to_numpy()+1200)
        assert np.allclose(quality,z[f'quality_{lag}'].to_numpy(),atol=1e-10,rtol=0)
        assert np.allclose(z['_pa'].to_numpy()/z['_fraction'].to_numpy(),z[f'work_{lag}'].to_numpy(),atol=1e-10,rtol=0)
    # These joins do not call the feature builder. All event numerators and
    # denominators are re-derived from the preserved raw counts for each lag.
    feature_checks=0
    for lag in range(3):
        for bucket in r.BUCKETS:
            key=f'{bucket}_{lag}_'; columns=list(dict.fromkeys(['plate_appearances',*[v[0] for v in EVENTS.values()],*[v[1] for v in EVENTS.values()]]))
            c=counts.filter(pl.col('bucket')==bucket).select((pl.col('season')+lag).alias('origin_year'),'player_id',*[pl.col(n).alias('_'+n) for n in columns])
            q=f.join(c,on=['origin_year','player_id'],how='left',validate='1:1').with_columns(pl.col(['_'+n for n in columns]).fill_null(0))
            assert np.array_equal(q[key+'pa'].to_numpy(),q['_plate_appearances'].to_numpy())
            assert np.array_equal(q[key+'present'].to_numpy(),(q['_plate_appearances']>0).to_numpy())
            for event,(num,den,prior) in EVENTS.items():
                expect=(q['_'+num].to_numpy()+100*prior)/(q['_'+den].to_numpy()+100)
                assert np.allclose(expect,q[key+event].to_numpy(),atol=1e-12,rtol=0),(lag,bucket,event)
                feature_checks+=1
    mlb=counts.filter(pl.col('bucket')=='MLB').group_by('season','player_id').agg(pl.col('plate_appearances').sum())
    career=mlb.sort('player_id','season').with_columns(pl.col('plate_appearances').cum_sum().over('player_id').alias('_career'))
    for year,g in f.group_by('origin_year'):
        cutoff=year[0];q=g.join(career.filter(pl.col('season')<=cutoff).sort('season').unique('player_id',keep='last').select('player_id','_career'),on='player_id',how='left',validate='1:1')
        assert q['career_mlb_observed_pa'].equals(q['_career'].fill_null(0).cast(q['career_mlb_observed_pa'].dtype))
    # Cutoff invariance: all raw 2025 batting counts may be replaced without
    # changing any <=2024 observed feature lookup. Labels remain separate.
    changed=counts.with_columns(pl.when(pl.col('season')==2025).then(999999).otherwise(pl.col('plate_appearances')).alias('plate_appearances'))
    assert counts.filter(pl.col('season')<=2024).equals(changed.filter(pl.col('season')<=2024))
    prohibited={'row_id','player_id','origin_year','target_year','next_pa','next_value','next_state','next_batting_rate'}
    assert not prohibited.intersection(pre['detail_features'])
    replayed=0
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            year,fold=c['year'],c['fold'];tr=f.filter(pl.col('row_id').is_in(c['training_row_ids']));te=raw.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            assert tr['target_year'].max()<=year and 2020 not in tr['target_year']
            assert not set(tr['player_id']).intersection(te['player_id'])
            assert set(te['outer_fold'])=={fold} and fold not in tr['outer_fold']
            note=r.read(r.OUT/f'fits-{year}-{fold}.json')
            assert note['prediction_hash']==sha256_file(r.OUT/f'forecast-{year}-{fold}.parquet')
            assert len(note['models'])==20
            for n in note['models']:
                assert sha256_file(Path(n['path']))==n['sha256']
                sub=tr
                if n['head'][-1:] in ['1','2','3'] and n['arm'].endswith('hurdle'): sub=tr.filter(pl.col('next_state')==int(n['head'][-1]))
                elif n['head']=='batting_rate': sub=tr.filter(pl.col('next_pa')>0)
                assert len(sub)==n['training_rows'] and sub['player_id'].n_unique()==n['training_players']
                assert sub['target_year'].max()==n['maximum_target_year'] and sub['target_year'].min()==n['minimum_target_year']
                model=joblib.load(n['path']);x=te.select(n['features']).to_numpy()
                if n['head']=='state':
                    assert model.classes_.tolist()==[0,1,2,3];pred=model.predict_proba(x);pred[te['hard_unavailable'].to_numpy()]=[1,0,0,0]
                    assert np.allclose(pred,te.select([n['arm']+f'_p{i}' for i in range(4)]).to_numpy(),atol=1e-10,rtol=0)
                else:
                    pred=model.predict(x)
                    if n['target']=='next_pa': pred=np.clip(pred,0,800)
                    if n['arm']=='direct_detail': pred[te['hard_unavailable'].to_numpy()]=0
                    col=n['arm']+('_rate' if n['head']=='batting_rate' else '_conditional_'+n['head'] if n['arm'].endswith('hurdle') else '_'+n['head'])
                    assert np.allclose(pred,te[col].to_numpy(),atol=1e-10,rtol=0),(year,fold,col)
                replayed+=1
            for arm in ['base_hurdle','detail_hurdle']:
                for metric in ['pa','value']:
                    expect=sum(te[arm+f'_p{i}'].to_numpy()*te[arm+f'_conditional_{metric}{i}'].to_numpy() for i in [1,2,3])
                    assert np.allclose(expect,te[arm+'_'+metric].to_numpy(),atol=1e-10,rtol=0)
            print(f'Replayed {year} / group {fold}: 20 heads',flush=True)
    scored=pl.read_parquet(r.OUT/'scored-predictions.parquet')
    q=scored.filter((pl.col('pa_0')>0)&pl.col('steamer_pa').is_not_null()&pl.col('zips_pa').is_not_null()&pl.col('v24_row_id').is_not_null())
    assert len(q)==1789 and q.filter(pl.col('next_pa')==0).height==339
    coherent=pl.read_parquet(r.OUT/'predictions-coherent.parquet')
    assert coherent.select('row_id','next_pa','next_value').equals(raw.select('row_id','next_pa','next_value'))
    r.write('verification.json',dict(saved_heads_replayed=replayed,observed_feature_columns_reconciled=feature_checks+84,
        source_rows=len(f),forecast_rows=len(raw),mlb_value_labels_independently_rebuilt=len(targets),all_future_labels_excluded_from_features=True,held_players_excluded=True,
        maximum_outcome_year=2025,public_rows=len(q),public_non_arrivals=339,player_walkthrough_status='pending',
        limitation='Raw event rates not park-neutral; conditional-head support documented separately; public snapshot timing not exact Dec 31.',
        output_hashes={str(r.OUT/n):sha256_file(r.OUT/n) for n in ['predictions.parquet','predictions-coherent.parquet','scored-predictions.parquet']}))


if __name__=='__main__': main()
