"""Direct expected-workload alternatives using origin-known own count histories."""
import numpy as np
import polars as pl

EVENTS={'K':('strike_outs','plate_appearances',.23),
    'BB':('unintentional_walks','plate_appearances',.08),
    'HBP':('hit_by_pitch','plate_appearances',.01),
    'HR':('home_runs','plate_appearances',.03),
    'BABIP':('babip_hits','babip_opportunities',.30),
    '2B':('doubles','plate_appearances',.05),'3B':('triples','plate_appearances',.005)}
LEVELS=['MLB','AAA','AA']
BASIC=['age_centered','age_squared','elapsed_scaled','regular_window_scaled','absence_window_scaled',
    *[f'{stem}_{lag}' for lag in range(3) for stem in ['work','quality','minor_pa','fraction','league_rate']]]
RAW=[f'raw_{level}_{lag}_{field}' for level in LEVELS for lag in range(3)
    for field in ['pa','present',*EVENTS]]
FLAGS=[f'milb_canceled_{lag}' for lag in range(3)]
FEATURES=BASIC+RAW+FLAGS
ARMS=['ridge','extra_trees','hist_gb','xgboost','lightgbm','catboost']


def materialize(panel,counts):
    # Rookie-complex combines multiple sport IDs in the raw inventory; this
    # first post-debut contrast uses MLB/AAA/AA only, which have unique totals.
    counts=counts.filter(pl.col('level_group').is_in(LEVELS))
    if counts.unique(['player_id','season','level_group']).height!=counts.height:
        raise ValueError('Duplicate raw season-level totals')
    if counts.filter((pl.col('plate_appearances')<0)|(pl.col('strike_outs')>pl.col('plate_appearances'))).height:
        raise ValueError('Invalid component counts')
    # Complete existing windows only. Never fetch a source season after origin.
    f=panel.filter(pl.col('window_complete'))
    lookup={(x['player_id'],x['season'],x['level_group']):x for x in counts.iter_rows(named=True)}
    rows=[]
    for row in f.iter_rows(named=True):
        new={'row_id':row['row_id']}
        for lag in range(3):
            year=row['origin_year']-lag;new[f'milb_canceled_{lag}']=float(year==2020)
            for level in LEVELS:
                raw=lookup.get((row['player_id'],year,level));pa=raw['plate_appearances'] if raw else 0
                new[f'raw_{level}_{lag}_pa']=float(pa)
                new[f'raw_{level}_{lag}_present']=float(pa>0)
                for event,(num,den,prior) in EVENTS.items():
                    n=raw[den] if raw else 0;value=raw[num] if raw else 0
                    new[f'raw_{level}_{lag}_{event}']=(value+100*prior)/(n+100)
                if level=='MLB':assert pa==row[f'pa_{lag}'],(row['row_id'],year,pa,row[f'pa_{lag}'])
        rows.append(new)
    result=f.join(pl.DataFrame(rows),on='row_id',validate='1:1')
    if not np.isfinite(result.select(FEATURES).to_numpy()).all():raise ValueError('Unknown complete-window inputs')
    return result


def learner(name):
    if name=='ridge':
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
        from sklearn.linear_model import Ridge
        return make_pipeline(StandardScaler(),Ridge(alpha=100))
    if name=='extra_trees':
        from sklearn.ensemble import ExtraTreesRegressor
        return ExtraTreesRegressor(n_estimators=200,min_samples_leaf=20,max_features=.7,n_jobs=2,random_state=30)
    if name=='hist_gb':
        from sklearn.ensemble import HistGradientBoostingRegressor
        return HistGradientBoostingRegressor(max_iter=250,max_depth=3,min_samples_leaf=30,
            learning_rate=.05,l2_regularization=10,early_stopping=False,random_state=30)
    if name=='xgboost':
        from xgboost import XGBRegressor
        return XGBRegressor(n_estimators=250,max_depth=3,learning_rate=.05,min_child_weight=30,
            reg_lambda=10,subsample=1,colsample_bytree=1,tree_method='hist',objective='reg:squarederror',n_jobs=2,random_state=30)
    if name=='lightgbm':
        from lightgbm import LGBMRegressor
        return LGBMRegressor(n_estimators=250,max_depth=3,num_leaves=8,min_child_samples=30,
            learning_rate=.05,reg_lambda=10,subsample=1,colsample_bytree=1,n_jobs=2,random_state=30,
            deterministic=True,force_col_wise=True,verbosity=-1)
    if name=='catboost':
        from catboost import CatBoostRegressor
        return CatBoostRegressor(iterations=250,depth=4,learning_rate=.05,l2_leaf_reg=10,
            bootstrap_type='No',random_strength=0,thread_count=2,random_seed=30,
            allow_writing_files=False,verbose=False,loss_function='RMSE')
    raise ValueError(name)


def fit(model,name,x,y,years):
    unique,counts=np.unique(years,return_counts=True)
    weights=np.array([len(y)/(len(unique)*counts[np.where(unique==v)[0][0]]) for v in years])
    model.fit(x,y,**({'ridge__sample_weight':weights} if name=='ridge' else {'sample_weight':weights}))
    return model


def forecast(raw,hard):
    raw=np.asarray(raw,float)
    if not np.isfinite(raw).all():raise ValueError('Nonfinite workload prediction')
    out=np.clip(raw,0,800);out[np.asarray(hard,bool)]=0
    return out


def score(frame,prefix):
    per=[]
    for _,g in frame.group_by('target_year'):
        pa=(g[prefix+'_pa']-g['next_pa']).to_numpy();value=(g[prefix+'_value']-g['next_value']).to_numpy()
        per.append([np.mean(pa**2),np.mean(abs(pa)),np.mean(pa),np.mean(value**2),np.mean(abs(value)),np.mean(value)])
    z=np.mean(per,axis=0)
    return dict(pa_rmse=float(np.sqrt(z[0])),pa_mae=float(z[1]),pa_bias=float(z[2]),
        value_rmse=float(np.sqrt(z[3])),value_mae=float(z[4]),value_bias=float(z[5]),
        pa_total=float(frame[prefix+'_pa'].sum()),value_total=float(frame[prefix+'_value'].sum()))
