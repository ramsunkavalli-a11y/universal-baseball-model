"""Read-only-inference diagnostics of fixed hitter playing-time predictions."""
import math
import numpy as np
import polars as pl

PATH='path0__level_path__'


def cohort(frame):
    return frame.with_columns(pl.when(pl.col('prospect')&(pl.col('stage')=='Upper minors')).then(pl.lit('Prospect upper'))
        .when(pl.col('prospect')).then(pl.lit('Prospect lower'))
        .when(pl.col('minor_returner')).then(pl.lit('Former MLB in minors'))
        .when(pl.col('stage')=='Current MLB').then(pl.lit('Current MLB'))
        .when(pl.col('stage')=='Inactive / unknown').then(pl.lit('Inactive / unknown'))
        .otherwise(pl.lit('Other')).alias('audit_cohort'))


def decompose(f):
    p,q,y=[f[c].to_numpy() for c in ('probability','conditional','actual_pa')]
    if not np.isfinite(p).all() or not np.isfinite(q).all() or ((p<0)|(p>1)).any() or (q<=0).any():
        raise ValueError('Invalid hurdle predictions')
    if not np.isfinite(y).all() or (y<0).any():raise ValueError('Invalid PA outcome')
    active=(y>0).astype(int)
    return f.with_columns(pl.Series('active',active),pl.Series('expected_pa',p*q),
        pl.Series('participation_pa_error',q*(active-p)),pl.Series('workload_pa_error',active*(y-q)),
        pl.Series('pa_error',y-p*q))


def profiles():
    prospect=pl.col('prospect');upper=prospect&(pl.col('stage')=='Upper minors')
    current=pl.col('stage')=='Current MLB';supported=pl.col('pa_lag0')>=200
    protected=pl.col('on_40man')==1;path=pl.col('path0__available')==1
    high_hr=supported&(pl.col('home_run_rate_lag0')>=.04)
    low_k=supported&(pl.col('strikeout_rate_lag0')<=.18)
    g={'All hitters':pl.lit(True),'All prospects':prospect}
    g.update({n:pl.col('audit_cohort')==n for n in ('Prospect upper','Prospect lower','Former MLB in minors','Current MLB','Inactive / unknown')})
    g.update({f'Prospect level {l}':prospect&(pl.col('level')==l) for l in ('AAA','AA','A+','A','A-','RK')})
    g.update({
        'Prospect age <=21':prospect&(pl.col('age')<=21),
        'Prospect age 22-24':prospect&pl.col('age').is_between(22,24),
        'Prospect age >=25':prospect&(pl.col('age')>=25),
        'Prospect PA <100':prospect&(pl.col('pa_lag0')<100),
        'Prospect PA 100-299':prospect&pl.col('pa_lag0').is_between(100,299),
        'Prospect PA >=300':prospect&(pl.col('pa_lag0')>=300),
        'Prospect on 40-man':prospect&protected,
        'Prospect off 40-man':prospect&~protected,
        'Upper age <23':upper&(pl.col('age')<23),
        'Upper age >=25':upper&(pl.col('age')>=25),
        'Upper on 40-man':upper&protected,
        'Upper off 40-man':upper&~protected,
        'Upper protected PA >=300':upper&protected&(pl.col('pa_lag0')>=300),
        'Upper protected low K':upper&protected&low_k,
        'Upper protected high HR':upper&protected&high_hr,
        'Prospect promoted primary':prospect&path&(pl.col(PATH+'primary_level_change')>0),
        'Prospect substantial repeat':prospect&path&(pl.col(PATH+'substantial_same_level_repeat')==1),
        'Prospect third-plus at level':prospect&path&(pl.col(PATH+'third_or_later_at_primary')==1),
        'Prospect partial-promotion return':prospect&path&(pl.col(PATH+'returned_after_partial_promotion')==1),
        'Upper substantial repeat':upper&path&(pl.col(PATH+'substantial_same_level_repeat')==1),
        'Upper promoted primary':upper&path&(pl.col(PATH+'primary_level_change')>0),
        'Upper partial-promotion return':upper&path&(pl.col(PATH+'returned_after_partial_promotion')==1),
        'Prospect low K <=18%':prospect&low_k,
        'Prospect high K >=30%':prospect&supported&(pl.col('strikeout_rate_lag0')>=.30),
        'Prospect HR >=4%':prospect&high_hr,
        'Prospect BB >=12%':prospect&supported&(pl.col('ubb_rate_lag0')>=.12),
        'Upper low K <=18%':upper&low_k,
        'Upper HR >=4%':upper&high_hr,
        'Upper BB >=12%':upper&supported&(pl.col('ubb_rate_lag0')>=.12),
        'Prospect no current contact':prospect&(pl.col('raw0__available')==0),
        'Prospect current contact':prospect&(pl.col('raw0__available')==1),
        'Prospect Mexican share >=50%':prospect&(pl.col('league_mexican_pa_share_lag0')>=.5),
        'Prospect draft matched':prospect&(pl.col('pedigree_matched')==1),
        'Prospect draft unmatched':prospect&(pl.col('pedigree_matched')==0),
        'Prospect high draft quality >=.5':prospect&(pl.col('pedigree_pick_quality')>=.5),
        'Current MLB PA <100':current&(pl.col('mlb_pa_lag0')<100),
        'Current MLB PA 100-399':current&pl.col('mlb_pa_lag0').is_between(100,399),
        'Current MLB PA >=400':current&(pl.col('mlb_pa_lag0')>=400),
        'Current MLB age <=25':current&(pl.col('age')<=25),
        'Current MLB age 26-31':current&pl.col('age').is_between(26,31),
        'Current MLB age >=32':current&(pl.col('age')>=32),
        'Current MLB older regular':current&(pl.col('age')>=32)&(pl.col('mlb_pa_lag0')>=400),
        'Current MLB recent debut':current&pl.col('recent_debut'),
        'Former MLB in minors on 40-man':pl.col('minor_returner')&protected,
        'Former MLB in minors off 40-man':pl.col('minor_returner')&~protected,
    })
    g.update({f'Prospect talent quintile {i}':prospect&(pl.col('talent_quintile')==i) for i in range(1,6)})
    return g


def metrics(f, workload=True):
    if not f.height:return None
    actual=f['active'].to_numpy();prob=f['probability'].to_numpy()
    result={'rows':f.height,'players':f['player_id'].n_unique(),'actual_active':int(actual.sum()),
        'expected_active':float(prob.sum()),'active_error':float((actual-prob).sum()),
        'brier':float(np.mean((actual-prob)**2))}
    if workload:
        y=f['actual_pa'].to_numpy();pred=f['expected_pa'].to_numpy();a=actual>0
        result.update(actual_pa=float(y.sum()),expected_pa=float(pred.sum()),pa_error=float((y-pred).sum()),
            bias=float((y-pred).mean()),rmse=float(np.mean((y-pred)**2)**.5),
            participation_pa_error=float(f['participation_pa_error'].sum()),
            workload_pa_error=float(f['workload_pa_error'].sum()),
            actual_conditional=float(y[a].mean()) if a.any() else None,
            predicted_conditional_among_active=float(f.filter(pl.col('active')==1)['conditional'].mean()) if a.any() else None)
    return result


def describe(f, workload=True):
    if not f.height:return None
    by={str(y):metrics(g,workload) for (y,),g in f.partition_by('origin_year',as_dict=True).items()}
    non=[v for y,v in by.items() if int(y)!=2021];support=[v for y,v in by.items() if int(y)!=2021 and v['rows']>=100 and v['actual_active']>=5]
    metric='bias' if workload else 'active_error'
    signs=sum(v[metric]>0 for v in support)
    flag=None
    if len(support)>=3:
        if signs>=math.ceil(.75*len(support)):flag='recurring underprediction'
        elif len(support)-signs>=math.ceil(.75*len(support)):flag='recurring overprediction'
    result={'pooled':metrics(f,workload),'by_origin':by,'non2021_supported_origins':len(support),
        'non2021_underprediction_origins':signs,'descriptive_flag':flag,
        'non2021_mean_active_error':float(np.mean([v['active_error'] for v in non])) if non else None}
    if workload:result['non2021_equal_origin_bias']=float(np.mean([v['bias'] for v in non])) if non else None
    return result
