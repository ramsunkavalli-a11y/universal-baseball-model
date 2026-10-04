"""Count actual origin-safe prospect tracking support without fitting forecasts."""
import json
from pathlib import Path
import numpy as np
import polars as pl
from universal_baseball.storage import sha256_file
import materialize_hitter_minor_statcast_source as source

ROOT=source.ROOT;OUT=source.OUT;CURRENT=ROOT/'reports/generated/hitter-preseason-readiness-v68'


def main():
    report=json.loads((OUT/'source-report.json').read_text(encoding='utf8'))
    for group in ['input_hashes','output_hashes']:
        for p,h in report[group].items():assert sha256_file(Path(p))==h
    annual=pl.read_parquet(OUT/'annual-launch-features.parquet')
    f=pl.read_parquet(CURRENT/'features.parquet');pre=json.loads((CURRENT/'preflight.json').read_text(encoding='utf8'))
    rows=[]
    for lag in range(3):
        dates=f.select('row_id','player_id',(pl.col('origin_year')-lag).alias('season'))
        matched=dates.join(annual.select('player_id','season','league_id','measured_ev_contacts','measured_pair_contacts','last_date'),
            on=['player_id','season'],how='inner',validate='m:m')
        assert matched.select((pl.col('last_date').dt.year()==pl.col('season')).all()).item()
        rows.append(matched)
    counts=pl.concat(rows).group_by('row_id','league_id').agg(pl.col('measured_ev_contacts').sum().alias('ev_n'),
        pl.col('measured_pair_contacts').sum().alias('pair_n'))
    q=f.select('row_id','player_id','origin_year','outer_fold','prior_debut','snapshot_level','age','next_pa').join(counts,on='row_id',how='inner')
    q=q.filter(pl.col('ev_n')>0).with_columns((pl.col('age')//5).cast(pl.Int64).alias('age_band'),
        pl.when(pl.col('ev_n')<50).then(pl.lit('under50')).when(pl.col('ev_n')<200).then(pl.lit('50to199')).otherwise(pl.lit('200plus')).alias('sample_band'))
    q.write_parquet(OUT/'origin-tracking-support-features.parquet')
    folds=[];profiles=[]
    for cell in pre['cells']:
        tr=q.filter(pl.col('row_id').is_in(cell['training_row_ids'])&(pl.col('next_pa')>0))
        te=q.filter(pl.col('row_id').is_in(cell['test_row_ids']))
        # Every participant in conditional-rate training must already have a mature
        # future MLB observation at this outer cutoff and exclude the whole group.
        assert tr.filter((pl.col('origin_year')+1>cell['year'])|(pl.col('outer_fold')==cell['fold'])).is_empty()
        per=[]
        for league in [112,117,123]:
            a=tr.filter(pl.col('league_id')==league);b=te.filter(pl.col('league_id')==league)
            per.append(dict(league_id=league,active_training_rows=len(a),active_training_people=a['player_id'].n_unique(),
                predebut_active_training_people=a.filter(pl.col('prior_debut')==0)['player_id'].n_unique(),
                test_rows=len(b),test_people=b['player_id'].n_unique(),predebut_test_rows=b.filter(pl.col('prior_debut')==0).height))
        folds.append(dict(origin=cell['year'],fold=cell['fold'],by_league=per))
        keys=['league_id','prior_debut','age_band','sample_band']
        training=tr.group_by(keys).agg(pl.col('player_id').n_unique().alias('active_training_profile_people'))
        x=te.join(training,on=keys,how='left').with_columns(pl.col('active_training_profile_people').fill_null(0),
            pl.lit(cell['year']).alias('test_origin'),pl.lit(cell['fold']).alias('test_fold'))
        profiles.append(x)
    profiles=pl.concat(profiles);profiles.write_parquet(OUT/'tracked-profile-support.parquet')
    summary=profiles.group_by('test_origin','league_id').agg(pl.len().alias('test_rows'),
        pl.col('active_training_profile_people').min().alias('minimum_profile_people'),
        (pl.col('active_training_profile_people')<20).sum().alias('sparse_profile_rows'),
        (pl.col('active_training_profile_people')==0).sum().alias('absent_profile_rows')).sort('test_origin','league_id')
    source.write('training-support-review.json',dict(folds=folds,profile_summary=summary.to_dicts(),
        warning_threshold=20,threshold_is_not_proof_of_sufficiency=True,models_fitted=0,
        profile_support_approved=False,all_evaluation_identities_retained=True,
        source_report_sha256=sha256_file(OUT/'source-report.json'),input_hashes={str(p):sha256_file(p) for p in
            [Path(__file__),CURRENT/'features.parquet',CURRENT/'preflight.json',OUT/'annual-launch-features.parquet']},
        output_hashes={str(p):sha256_file(p) for p in [OUT/'origin-tracking-support-features.parquet',OUT/'tracked-profile-support.parquet']}))
    print(summary)


if __name__=='__main__':main()
