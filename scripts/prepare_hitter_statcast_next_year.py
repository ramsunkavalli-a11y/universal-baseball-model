"""Freeze historical launch predictors and all profile checks before fitting."""
from pathlib import Path
import json
import numpy as np
import polars as pl
from universal_baseball.forecast_validation import preflight
from universal_baseball.storage import sha256_file
from prepare_practical_hitter_v33 import safe_matrix
import materialize_hitter_statcast_full_history as source

ROOT=source.ROOT; OUT=ROOT/'reports/generated/hitter-statcast-next-year'
CONTRACT=ROOT/'docs/hitter-statcast-next-year-contract.md'
METRICS={'mean_ev':(90.,10.),'ev95':(105.,10.),'hard_hit_fraction':(0.,1.),
         'mean_la':(0.,20.),'la_sd':(0.,20.),'sweet_spot_fraction':(0.,1.),'hard_air_fraction':(0.,1.)}


def read(p):return json.loads(Path(p).read_text(encoding='utf8'))


def write(name,v):
    p=OUT/name; assert not p.exists(),f'Preserve {p}'
    p.write_text(json.dumps(v,indent=2,allow_nan=False,default=str)+'\n',encoding='utf8',newline='\n')


def materialize(f,annual):
    lookup={(r['player_id'],r['season']):r for r in annual.iter_rows(named=True)}
    control=[]; measure=[]
    for lag in range(3):
        control += [f'sc_{lag}_{s}' for s in ['ev_sample','la_sample','pair_sample','pair_coverage','source_year_available']]
        control += [f'sc_{lag}_{m}_known' for m in METRICS]
        measure += [f'sc_{lag}_{m}' for m in METRICS]+[f'sc_{lag}_ev95_sample',f'sc_{lag}_hard_air_sample']
    rows=[]
    for o in f.iter_rows(named=True):
        pid,year=o['player_id'],o['origin_year']; r=dict(row_id=o['row_id']); ev_total=0; pair_total=0
        for lag in range(3):
            y=year-lag; a=lookup.get((pid,y)); available=2015<=y<=2024
            assert a is None or a['last_date'].year<=year
            prefix=f'sc_{lag}_'
            r[prefix+'source_year_available']=float(available)
            for kind in ['ev','la','pair']:
                n=int(a[f'measured_{kind}_contacts']) if a else 0
                r[prefix+kind+'_n']=n; r[prefix+kind+'_sample']=float(np.log1p(n)/np.log(601))
            ev_total+=r[prefix+'ev_n']; pair_total+=r[prefix+'pair_n']
            r[prefix+'pair_coverage']=a['pair_coverage'] if a else 0.
            for m,(center,scale) in METRICS.items():
                v=a[m] if a else None
                r[prefix+m+'_known']=float(v is not None)
                r[prefix+m]=float((v-center)/scale) if v is not None else 0.
            r[prefix+'ev95_sample']=r[prefix+'ev95']*r[prefix+'ev_sample']
            r[prefix+'hard_air_sample']=r[prefix+'hard_air_fraction']*r[prefix+'pair_sample']
        r['sc_own_ev_n']=ev_total; r['sc_own_pair_n']=pair_total; r['sc_tracked']=ev_total>0
        rows.append(r)
    return f.join(pl.DataFrame(rows),on='row_id',validate='1:1'),control,measure


def profile(g):
    return g.with_columns((pl.col('age')//5).cast(pl.Int64).alias('sc_age_band'),
        pl.when(pl.col('sc_own_ev_n')==0).then(pl.lit('untracked')).when(pl.col('sc_own_ev_n')<50).then(pl.lit('under50'))
        .when(pl.col('sc_own_ev_n')<200).then(pl.lit('50to199')).otherwise(pl.lit('200plus')).alias('sc_sample_band'))


def main():
    assert not (OUT/'preflight.json').exists(),'Preserve preflight'
    approval=read(source.OUT/'final-source-review.json')
    assert approval['source_walkthrough_status']=='complete' and approval['qualified_MLB_source_approved_for_bounded_experiment']
    assert sha256_file(source.OUT/'source-report.json')==approval['source_report_sha256']
    source.checked_report(source.OUT/'source-report.json')
    OUT.mkdir(parents=True,exist_ok=True)
    original=pl.read_parquet(source.old.CURRENT/'features.parquet'); annual=pl.read_parquet(source.OUT/'annual-launch-features.parquet')
    f,control,measure=materialize(original,annual); assert len(f)==63282
    assert f.select(original.columns).equals(original)
    names=read(ROOT/'reports/generated/practical-hitter-numeric-repair-v53/preflight.json')['rate_features']
    assert len(names)==199
    arms=dict(ridge_coverage=names+control,ridge_measurements=names+control+measure,
        hist_coverage=names+control,hist_measurements=names+control+measure)
    assert np.isfinite(safe_matrix(f,arms['ridge_measurements'])).all()
    f.write_parquet(OUT/'features.parquet'); current=pl.read_parquet(source.old.CURRENT/'scored-predictions.parquet')
    assert len(current)==30506
    parent=read(source.old.CURRENT/'preflight.json'); cells=[]; supports=[]; profiles=[]; ranges=[]
    keys=['stage','sc_age_band','sc_sample_band']
    for c in parent['cells']:
        tr=f.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id'); te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
        active=tr.filter(pl.col('next_pa')>0)
        assert set(current.filter(pl.col('row_id').is_in(c['test_row_ids']))['row_id'])==set(te['row_id'])
        sup,note=preflight(active,te,cutoff=c['year'],fold=c['fold'],features=arms['ridge_measurements'],expected_keys=te.select('row_id','horizon').iter_rows())
        supports.append(sup.with_columns(pl.lit(c['year']).alias('sc_origin'),pl.lit(c['fold']).alias('sc_fold')))
        tracked=profile(active).filter(pl.col('sc_tracked'))
        counts=tracked.group_by(keys).agg(pl.col('player_id').n_unique().alias('tracked_profile_people'))
        p=profile(te).select('row_id','sc_tracked',*keys).join(counts,on=keys,how='left',validate='m:1').with_columns(
            pl.col('tracked_profile_people').fill_null(0),pl.lit(c['year']).alias('origin'),pl.lit(c['fold']).alias('fold'))
        profiles.append(p)
        x=safe_matrix(tracked,control+measure); tx=safe_matrix(te.filter(pl.col('sc_tracked')),control+measure)
        ranges.extend(dict(origin=c['year'],fold=c['fold'],feature=n,train_min=float(x[:,j].min()),train_max=float(x[:,j].max()),
            test_outside=int(((tx[:,j]<x[:,j].min())|(tx[:,j]>x[:,j].max())).sum())) for j,n in enumerate(control+measure))
        cells.append(dict(year=c['year'],fold=c['fold'],training_row_ids=c['training_row_ids'],test_row_ids=c['test_row_ids'],
            rate_preflight=note,tracked_training_people=tracked['player_id'].n_unique(),
            tracked_test_rows=int(te['sc_tracked'].sum()),tracked_profile_sparse=int(p.filter(pl.col('sc_tracked')&(pl.col('tracked_profile_people')<20)).height)))
    pl.concat(supports).write_parquet(OUT/'support.parquet');pl.concat(profiles).write_parquet(OUT/'tracked-profile-support.parquet')
    write('feature-ranges.json',dict(ranges=ranges))
    paths=[CONTRACT,Path(__file__),source.OUT/'final-source-review.json',source.OUT/'annual-launch-features.parquet',
        source.old.CURRENT/'features.parquet',source.old.CURRENT/'scored-predictions.parquet',source.old.CURRENT/'preflight.json',
        ROOT/'scripts/prepare_practical_hitter_v33.py',ROOT/'scripts/fit_practical_hitter_v31.py',ROOT/'src/universal_baseball/forecast_validation.py',
        OUT/'features.parquet',OUT/'support.parquet',OUT/'tracked-profile-support.parquet',OUT/'feature-ranges.json']
    write('preflight.json',dict(before_fitting=True,arms=arms,control_features=control,measurement_features=measure,cells=cells,
        ridge_alpha=100,hist_settings=dict(max_iter=150,max_depth=2,min_samples_leaf=30,learning_rate=.05,l2_regularization=20,early_stopping=False,random_state=724),
        current_anchor=str(source.old.CURRENT/'scored-predictions.parquet'),row_membership_unchanged=True,protected_outcomes_used=False,
        input_hashes={str(p):sha256_file(p) for p in paths}))
    print('Frozen:',len(current),'forecasts;',len(cells),'cells;',len(control),'coverage and',len(measure),'measurement features; no fits.')


if __name__=='__main__':main()
