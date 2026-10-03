"""One fixed historical rank extension; complete identical preflights before fits."""
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from sklearn.ensemble import HistGradientBoostingRegressor
from fit_practical_hitter_v31 import weights
from universal_baseball.forecast_validation import preflight
from universal_baseball.historical_prospect_rank import features
from universal_baseball.storage import sha256_file
import evaluate_hitter_late_role_v46 as previous
from prepare_historical_scouting_v47 import ROOT,OUT,FIXED,write

BASE=previous.BASE
r=previous.r


def tag(frame):
    return frame.with_columns((pl.col('age')/5).floor().alias('age_band'),
        pl.when(pl.col('scout_listed_0')<0).then(pl.lit('unknown')).when(pl.col('scout_listed_0')==0).then(pl.lit('not_listed')).when(pl.col('scout_rank_score_0')>=.81).then(pl.lit('top20')).otherwise(pl.lit('21plus')).alias('rank_band'))


def prepare():
    review=r.read(OUT/'source-review.json');assert review['player_walkthrough_status']=='complete' and review['rank_source_usable']
    assert not (OUT/'preflight.json').exists()
    old=r.read(BASE/'preflight.json');source=pl.read_parquet(BASE/'features.parquet');assert len(source)==63282
    ranks=pl.read_parquet(OUT/'ranks.parquet');audit=r.read(OUT/'source-audit.json')
    assert sha256_file(OUT/'ranks.parquet')==audit['ranking_sha256']
    lookup={(o['season'],o['player_id']):o['rank'] for o in ranks.iter_rows(named=True)}
    coverage={int(y):n for y,n in audit['observed_lists'].items()}
    addedrows=[]
    for o in source.select('row_id','player_id','origin_year').iter_rows(named=True):
        inputs=features(o['player_id'],o['origin_year'],lookup,coverage)
        addedrows.append(dict(row_id=o['row_id'],**{k:(-1. if v is None else v) for k,v in inputs.items()}))
    extra=pl.DataFrame(addedrows);added=[c for c in extra.columns if c!='row_id'];assert len(added)==12
    source=source.join(extra,on='row_id',validate='1:1');assert source.select(pl.read_parquet(BASE/'features.parquet').columns).sort('row_id').equals(pl.read_parquet(BASE/'features.parquet').sort('row_id'))
    source.write_parquet(OUT/'features.parquet');names=old['features']+added;assert len(names)==251
    cells=[];supports=[];profiles=[];keys=['stage','prior_debut','age_band','rank_band']
    for c in old['cells']:
        tr=source.filter(pl.col('row_id').is_in(c['training_row_ids']));te=source.filter(pl.col('row_id').is_in(c['test_row_ids']))
        support,note=preflight(tr,te,cutoff=c['year'],fold=c['fold'],features=names,expected_keys=te.select('row_id','horizon').iter_rows());supports.append(support)
        n=tag(tr).group_by(keys).agg(pl.col('player_id').n_unique().alias('rank_profile_players'))
        profiles.append(tag(te).select('row_id',*keys).join(n,on=keys,how='left',validate='m:1').with_columns(pl.col('rank_profile_players').fill_null(0)))
        cells.append(dict(**c,rank_preflight=note,ranked_training_players=tr.filter(pl.col('scout_listed_0')==1)['player_id'].n_unique()))
    pl.concat(supports).write_parquet(OUT/'support.parquet');pl.concat(profiles).sort('row_id').write_parquet(OUT/'profile-support.parquet')
    paths=[OUT/'features.parquet',OUT/'ranks.parquet',OUT/'source-audit.json',OUT/'source-review.json',OUT/'source-walkthrough.md',OUT/'source-cases.json',
        r.OUT/'predictions.parquet',BASE/'preflight.json',ROOT/'docs/practical-hitter-scouting-v47-model-contract.md',Path(__file__),
        ROOT/'src/universal_baseball/historical_prospect_rank.py',ROOT/'config/practical_hitter_scouting_v47_source_notes.json',ROOT/'scripts/fit_practical_hitter_v31.py']
    write('preflight.json',dict(before_fitting=True,features=names,added_features=added,cells=cells,input_hashes={str(p):sha256_file(p) for p in paths},
        raw_source_hashes={str(OUT/f'captures/mlb-top100-{y}.html'):r.read(OUT/f'captures/mlb-top100-{y}.html.metadata.json')['sha256'] for y in range(2011,2025)},
        source_eligibility_qualified=True,protected_outcomes_used=False,
        settings=dict(loss='squared_error',max_iter=250,max_depth=3,min_samples_leaf=30,learning_rate=.05,l2_regularization=10,early_stopping=False,random_state=31)))
    print('All 35 cells checked before fits; 251 inputs, unchanged population and batting rate.',flush=True)


def fit():
    pre=r.read(OUT/'preflight.json')
    for p,h in {**pre['input_hashes'],**pre['raw_source_hashes']}.items():assert sha256_file(Path(p))==h,p
    source=pl.read_parquet(OUT/'features.parquet');base=pl.read_parquet(r.OUT/'predictions.parquet');fits=[]
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y,k=c['year'],c['fold'];forecast=OUT/f'forecast-{y}-{k}.parquet';note=OUT/f'fit-{y}-{k}.json'
            if forecast.exists():
                n=r.read(note);assert sha256_file(forecast)==n['prediction_sha256'] and sha256_file(Path(n['path']))==n['sha256'];fits.append(n);continue
            tr=source.filter(pl.col('row_id').is_in(c['training_row_ids']));te=source.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            q=base.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id');assert q['row_id'].equals(te['row_id'])
            model=HistGradientBoostingRegressor(**pre['settings']);model.fit(tr.select(pre['features']).to_numpy(),tr['next_pa'].to_numpy(),sample_weight=weights(tr))
            raw=model.predict(te.select(pre['features']).to_numpy());assert np.isfinite(raw).all()
            p=np.clip(raw,0,800);p[q['hard_unavailable'].to_numpy()|q['reported_retired'].to_numpy()]=0
            q=q.with_columns(pl.Series('scout_raw_pa',raw),pl.Series('scout_pa',p),pl.col('cohort_rate').alias('scout_rate'))
            q=q.with_columns((pl.col('scout_pa')*(pl.col('scout_rate')/600+pl.col('origin_replacement_rate'))).alias('scout_value'))
            path=OUT/f'scout-{y}-{k}.joblib';joblib.dump(model,path,compress=3);q.write_parquet(forecast)
            n=dict(year=y,fold=k,path=str(path),sha256=sha256_file(path),prediction_sha256=sha256_file(forecast),training_rows=len(tr),training_players=tr['player_id'].n_unique(),max_target_year=int(tr['target_year'].max()),clipped_over_800=int((raw>800).sum()),clipped_under_zero=int((raw<0).sum()))
            write(note.name,n);fits.append(n);print(f'Fitted rank extension {y}/{k}',flush=True)
    q=pl.concat([pl.read_parquet(OUT/f"forecast-{c['year']}-{c['fold']}.parquet") for c in pre['cells']]).sort('row_id');assert q.select(base.columns).equals(base.sort('row_id')) and len(q)==30506
    q.write_parquet(OUT/'predictions.parquet');write('fits.json',fits);write('fit-report.json',dict(heads=35,player_walkthrough_status='pending',all_old_columns_exact=True,rate_model_unchanged=True,protected_outcomes_used=False))


if __name__=='__main__':
    import sys
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='fit':fit()
    else:raise ValueError('Choose prepare or fit')
