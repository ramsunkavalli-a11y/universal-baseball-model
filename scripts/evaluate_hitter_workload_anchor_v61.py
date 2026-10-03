"""Matched direct and reference-plus-adjustment playing-time models."""
from pathlib import Path
import json
import sys
import joblib
import numpy as np
import polars as pl
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits
from universal_baseball.forecast_validation import preflight
from universal_baseball.hitter_workload_anchor import reference,forecast
from universal_baseball.storage import sha256_file

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reports/generated/practical-hitter-numeric-repair-v53'
STATUS=ROOT/'reports/generated/practical-hitter-opportunity-status-v59'
RETURN=ROOT/'reports/generated/hitter-observed-return-v60'
WIN=ROOT/'reports/generated/practical-hitter-late-role-v46'
OUT=ROOT/'reports/generated/hitter-workload-anchor-v61'
ADDED=['workload_reference','op_medical_scope','op_recorded_unresolved',
       'op_log_possible_days_upper','op_observed_returns','op_roster_returns',
       'op_nonmedical_unresolved']
ARMS=['direct61','anchor61']


def read(p):return json.loads(Path(p).read_text(encoding='utf8'))


def write(n,obj):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/n).write_text(json.dumps(obj,indent=2,default=str,allow_nan=False)+'\n',encoding='utf8')


def weights(frame):
    years=frame['origin_year'].to_numpy();u,c=np.unique(years,return_counts=True)
    return np.array([len(frame)/(len(u)*c[np.where(u==y)[0][0]])for y in years])


def profile(frame):
    return frame.with_columns((pl.col('age')//5).alias('age_band61'),
        pl.when(pl.col('pa_0')==0).then(pl.lit('absent')).when(pl.col('pa_0')<200)
        .then(pl.lit('brief')).when(pl.col('pa_0')<600).then(pl.lit('partial'))
        .otherwise(pl.lit('large')).alias('current_workload61'),
        pl.when(pl.col('workload_reference')<200).then(pl.lit('small'))
        .when(pl.col('workload_reference')<600).then(pl.lit('partial'))
        .otherwise(pl.lit('large')).alias('demonstrated_workload61'),
        ((pl.col('pa_0')==0)&((pl.col('pa_1')>=300)|(pl.col('pa_2')>=300)))
        .alias('absent_prior_regular61'))


def prepare():
    assert read(BASE/'report.json')['player_walkthrough_status']=='complete'
    assert read(RETURN/'report.json')['player_walkthrough_status']=='complete'
    assert not (OUT/'preflight.json').exists(),'Preserve completed preflight'
    for p,h in read(RETURN/'report.json')['input_hashes'].items():assert sha256_file(Path(p))==h,p
    source=pl.read_parquet(BASE/'features.parquet')
    state=pl.read_parquet(RETURN/'observation-states.parquet')
    context=pl.read_parquet(STATUS/'features.parquet').select('row_id','status_nonmedical_unresolved')
    f=source.join(state.select('row_id','medical_scope','recorded_unresolved',
        'possible_absence_days730_upper','observed_return_intervals730','reported_roster_returns730'),
        on='row_id',validate='1:1').join(context,on='row_id',validate='1:1')
    assert f.select(source.columns).equals(source)
    manifest=read(WIN/'source-manifest.json')
    # Verified completed/deduplicated games, not scheduled games or pitcher PA.
    games={c['season']:c['unique_completed_games']*2/30 for c in manifest['checks']}
    assert set(range(2010,2025))<=set(games)
    # Earliest source origins also need 2009; the completed-state capture
    # supplies game identities, unlike the older abstract-Final-only capture.
    early_path=ROOT/'reports/generated/multiyear-hitter-v1/raw/schedule-2009-completed.json'
    early={};teams=set()
    for d in read(early_path)['dates']:
        assert d['date'].startswith('2009-')
        for g in d['games']:
            assert g['gameType']=='R'
            if g['status']['codedGameState']not in ['F','O']:continue
            assert g['status']['abstractGameState']=='Final'
            pair=(g['teams']['home']['team']['id'],g['teams']['away']['team']['id'])
            assert g['gamePk']not in early or early[g['gamePk']]==pair
            early[g['gamePk']]=pair;teams.update(pair)
    assert len(teams)==30 and 2400<=len(early)<=2430
    games[2009]=len(early)*2/30
    counts=f.select('pa_0','pa_1','pa_2').to_numpy()
    seasons=np.array([[games[y-lag]for lag in range(3)]for y in f['origin_year']])
    ref,annual=reference(counts,seasons)
    f=f.with_columns(pl.Series('workload_reference',ref),
        pl.col('medical_scope').cast(pl.Float64).alias('op_medical_scope'),
        pl.col('recorded_unresolved').fill_null(0).alias('op_recorded_unresolved'),
        (pl.col('possible_absence_days730_upper').fill_null(0)+1).log().alias('op_log_possible_days_upper'),
        pl.col('observed_return_intervals730').fill_null(0).cast(pl.Float64).alias('op_observed_returns'),
        pl.col('reported_roster_returns730').fill_null(0).cast(pl.Float64).alias('op_roster_returns'),
        pl.col('status_nonmedical_unresolved').alias('op_nonmedical_unresolved'),
        *[pl.Series(f'annual_workload_reference_{lag}',annual[:,lag])for lag in range(3)])
    f=f.with_columns((pl.col('next_pa')-pl.col('workload_reference')).alias('adjustment_target'))
    OUT.mkdir(parents=True,exist_ok=True);f.write_parquet(OUT/'features.parquet')
    previous=read(BASE/'preflight.json');cells=[];support=[];profiles=[]
    keys=['stage','prior_debut','age_band61','current_workload61',
          'demonstrated_workload61','absent_prior_regular61']
    for c in previous['cells']:
        tr=f.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id')
        te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
        exposed={n:tr.filter(pl.col(n)>0)['player_id'].n_unique()for n in ADDED}
        names=previous['pa_features']+[n for n in ADDED if n in ADDED[:2]or exposed[n]>=20]
        sp,note=preflight(tr,te,cutoff=c['year'],fold=c['fold'],features=names,
            expected_keys=te.select('row_id','horizon').iter_rows())
        support.append(sp)
        n=profile(tr).group_by(keys).agg(pl.col('player_id').n_unique().alias('workload_profile_players'))
        profiles.append(profile(te).select('row_id',*keys).join(n,on=keys,how='left',validate='m:1')
            .with_columns(pl.col('workload_profile_players').fill_null(0)))
        cells.append(dict(**c,features61=names,exposed_players=exposed,
            actual_heads={a:note for a in ARMS},
            adjustment_target_range=[float(tr['adjustment_target'].min()),float(tr['adjustment_target'].max())]))
    pl.concat(support).write_parquet(OUT/'support.parquet')
    pl.concat(profiles).write_parquet(OUT/'profile-support.parquet')
    paths=[BASE/'features.parquet',BASE/'scored-predictions.parquet',BASE/'preflight.json',
        RETURN/'report.json',RETURN/'observation-states.parquet',STATUS/'features.parquet',
        WIN/'source-manifest.json',early_path,OUT/'features.parquet',Path(__file__),
        ROOT/'src/universal_baseball/hitter_workload_anchor.py',
        ROOT/'docs/hitter-workload-anchor-v61-contract.md']
    write('preflight.json',dict(before_fitting=True,cells=cells,settings=previous['settings'],
        arms=ARMS,source_rows=len(f),season_average_completed_games=games,
        input_hashes={str(p):sha256_file(p)for p in paths},
        protected_outcomes_used=False,historical_publication_vintage_verified=False))
    print('All 35 cells / 70 actual direct and adjustment heads preflighted.',flush=True)


def fit():
    pre=read(OUT/'preflight.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    f=pl.read_parquet(OUT/'features.parquet')
    base=pl.read_parquet(BASE/'scored-predictions.parquet');fits=[]
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y,k=c['year'],c['fold'];fp=OUT/f'forecast-{y}-{k}.parquet'
            if fp.exists():
                n=read(OUT/f'fit-{y}-{k}.json');assert sha256_file(fp)==n['prediction_sha256']
                for h in n['heads']:assert sha256_file(Path(h['path']))==h['sha256']
                fits.append(n);continue
            tr=f.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id')
            te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            q=base.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            assert q['row_id'].equals(te['row_id'])
            heads=[];names=c['features61'];x=tr.select(names).to_numpy();tx=te.select(names).to_numpy()
            for arm,target in [('direct61','next_pa'),('anchor61','adjustment_target')]:
                m=HistGradientBoostingRegressor(**pre['settings'])
                m.fit(x,tr[target].to_numpy(),sample_weight=weights(tr))
                output=m.predict(tx);raw=output+(te['workload_reference'].to_numpy()if arm=='anchor61'else 0)
                pa=forecast(raw,q['hard_unavailable'].to_numpy()|q['reported_retired'].to_numpy())
                q=q.with_columns(pl.Series(arm+'_head_output',output),pl.Series(arm+'_raw_pa',raw),
                    pl.Series(arm+'_pa',pa),pl.col('repaired_rate').alias(arm+'_rate'))
                q=q.with_columns((pl.col(arm+'_pa')*(pl.col(arm+'_rate')/600+pl.col('origin_replacement_rate'))).alias(arm+'_value'))
                path=OUT/f'{arm}-{y}-{k}.joblib';joblib.dump(m,path,compress=3)
                heads.append(dict(arm=arm,target=target,path=str(path),sha256=sha256_file(path),features=names,
                    training_rows=len(tr),training_players=tr['player_id'].n_unique(),
                    clip_low=int((raw<0).sum()),clip_high=int((raw>800).sum())))
            q.write_parquet(fp);note=dict(year=y,fold=k,heads=heads,prediction_sha256=sha256_file(fp))
            write(f'fit-{y}-{k}.json',note);fits.append(note)
            print(f'Workload reference {y}/{k}: saved direct and adjustment heads.',flush=True)
    q=pl.concat([pl.read_parquet(OUT/f"forecast-{c['year']}-{c['fold']}.parquet")for c in pre['cells']]).sort('row_id')
    assert len(q)==30506 and q.select(base.columns).equals(base.sort('row_id'))
    assert q['anchor61_rate'].equals(q['repaired_rate'])and q['direct61_rate'].equals(q['repaired_rate'])
    q.write_parquet(OUT/'predictions.parquet');write('fits.json',fits)
    write('fit-report.json',dict(heads=70,baseline_columns_exact=True,batting_rate_exact=True,
        player_walkthrough_status='pending',protected_outcomes_used=False,frozen_forecast_changed=False))


if __name__=='__main__':
    {'prepare':prepare,'fit':fit}[sys.argv[1]]()
