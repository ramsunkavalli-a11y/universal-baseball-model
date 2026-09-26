"""Explicitly post-scan checks of existing benchmarks and example-led profiles."""
import polars as pl
from fit_hitter_arrival_coherence_v1 import save
from audit_hitter_cohort_profiles_v1 import OUT,PA,PANEL
from universal_baseball.storage import sha256_file


def table(q):
    return q.group_by('horizon','origin_year').agg(pl.len().alias('rows'),
        (pl.col('actual_pa')>0).sum().alias('active'),pl.col('actual_pa').sum(),
        *[pl.col(c).sum() for c in ('D_pa','E_pa','D_universal_pa')],
        *[(pl.col('actual_pa')-pl.col(c)).mean().alias(c+'_bias') for c in ('D_pa','E_pa','D_universal_pa')],
        *[((pl.col('actual_pa')-pl.col(c))**2).mean().sqrt().alias(c+'_rmse') for c in ('D_pa','E_pa','D_universal_pa')])\
        .sort('horizon','origin_year').to_dicts()


def main():
    f=pl.read_parquet(PA).join(pl.read_parquet(PANEL).select('origin_year','player_id','mlb_pa_lag1','mlb_pa_lag2','pa_lag0'),
        on=['origin_year','player_id'],validate='m:1')
    current=pl.col('stage')=='Current MLB'
    groups={'MLB 100-399':current&pl.col('mlb_pa_lag0').is_between(100,399),
        'MLB 400+':current&(pl.col('mlb_pa_lag0')>=400),
        'MLB under100':current&(pl.col('mlb_pa_lag0')<100),
        'All current MLB':current,
        'Brief MLB full workload young':current&(pl.col('mlb_pa_lag0')<100)&(pl.col('pa_lag0')>=400)&(pl.col('age')<=25),
        'Minor returner with recent400':pl.col('minor_returner')&(pl.max_horizontal('mlb_pa_lag1','mlb_pa_lag2')>=400)}
    result={'post_scan_exploratory':True,'no_model_selected':True,'forecasts_changed':False,
        'definitions':{'Brief MLB full workload young':'current MLB PA <100, all-level PA >=400, age <=25',
                       'Minor returner with recent400':'prior MLB debut, current minors, MLB PA >=400 in either previous two calendar years'},
        'tables':{n:table(f.filter(e)) for n,e in groups.items()},
        'returner_cases':f.filter(groups['Minor returner with recent400']&(pl.col('horizon')==1)).select(
            'origin_year','player_id','player_name','mlb_pa_lag1','mlb_pa_lag2','D_pa','E_pa','D_universal_pa','actual_pa').to_dicts(),
        'hashes':{str(p):sha256_file(p) for p in (PA,PANEL)}}
    save(OUT/'supplement.json',result)
    print('Saved exploratory benchmark and career-state checks; no forecasts changed')


if __name__=='__main__':main()
