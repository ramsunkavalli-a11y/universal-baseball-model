"""Actual pre-fit membership/support audit for a paired-outcome forest."""
import json
from pathlib import Path
import numpy as np
import polars as pl
import prepare_hitter_draft_age_v42 as prev
from universal_baseball.forecast_validation import preflight
from universal_baseball.storage import sha256_file

r=prev.r;base=prev.base
OUT=r.ROOT/'reports/generated/practical-hitter-joint-forest-v43'
FIXED=prev.FIXED


def write(name,obj):
    (OUT/name).write_text(json.dumps(obj,indent=2,allow_nan=False,default=str),encoding='utf8')


def profile(f):
    return f.with_columns((pl.col('age')//5).alias('age_band'),
        pl.when(pl.col('pa_0')==0).then(pl.lit('absent')).when(pl.col('pa_0')<200).then(pl.lit('brief'))
        .when(pl.col('pa_0')<400).then(pl.lit('partial')).otherwise(pl.lit('400plus')).alias('current_work_band'))


def main():
    assert r.read(prev.OUT/'report.json')['player_walkthrough_status']=='complete'
    assert not (OUT/'preflight.json').exists();OUT.mkdir(parents=True,exist_ok=True)
    prior=r.read(base.OUT/'preflight.json');original=pl.read_parquet(prev.SOURCE);f=prev.materialize(original)
    for c in original.columns:assert f[c].equals(original[c])
    assert f['target_year'].max()==2025 and f['origin_year'].max()==2024
    assert f.filter(pl.col('next_pa')==0)['next_value'].abs().sum()==0
    assert f['next_pa'].min()>=0 and f['next_pa'].max()<=800
    assert np.isfinite(f.select(prior['features']).to_numpy()).all()
    f.write_parquet(OUT/'features.parquet');supports=[];cells=[]
    keys=['stage','prior_debut','age_band','current_work_band','draft_known']
    for c in prior['cells']:
        tr=f.filter(pl.col('row_id').is_in(c['training_row_ids']));te=f.filter(pl.col('row_id').is_in(c['test_row_ids']))
        _,note=preflight(tr,te,cutoff=c['year'],fold=c['fold'],features=prior['features'],expected_keys=te.select('row_id','horizon').iter_rows())
        counts=profile(tr).group_by(keys).agg(pl.col('player_id').n_unique().alias('profile_players'))
        supports.append(profile(te).select('row_id',*keys).join(counts,on=keys,how='left',validate='m:1').with_columns(pl.col('profile_players').fill_null(0)))
        cells.append(dict(**c,joint_preflight=note))
    pl.concat(supports).write_parquet(OUT/'support.parquet')
    settings=dict(n_estimators=200,min_samples_leaf=20,max_features=.7,bootstrap=False,max_depth=None,
        criterion='squared_error',random_state=43,n_jobs=2,output_scales=[600,2],equal_origin_weights=True)
    paths=[prev.SOURCE,base.OUT/'preflight.json',base.OUT/'predictions.parquet',base.OUT/'report.json',prev.OUT/'report.json',
        prev.OUT/'source-review.json',prev.OUT/'source-walkthrough.md',OUT/'features.parquet',OUT/'support.parquet',
        r.ROOT/'docs/practical-hitter-joint-forest-v43-contract.md',Path(__file__),
        r.ROOT/'scripts/evaluate_hitter_joint_forest_v43.py',r.ROOT/'src/universal_baseball/paired_leaf_distribution.py',
        r.ROOT/'scripts/fit_practical_hitter_v31.py']
    write('preflight.json',dict(before_fitting=True,features=prior['features'],cells=cells,settings=settings,
        input_hashes={str(p):sha256_file(p) for p in paths},source_walkthrough_status='complete',source_review=prev.r.read(prev.OUT/'source-review.json'),
        source_review_scope='Same preserved official histories/targets, exact original 199 inputs; V42 fixed source walks reused, not claimed as new joint forecast validation.',
        target_scale_limits=dict(maximum_pa=int(f['next_pa'].max()),minimum_value=float(f['next_value'].min()),maximum_value=float(f['next_value'].max())),
        protected_outcomes_used=False))
    print('35 actual source/support folds ready; paired future MLB PA/contribution targets, not an independent talent grade.',flush=True)


if __name__=='__main__':main()
