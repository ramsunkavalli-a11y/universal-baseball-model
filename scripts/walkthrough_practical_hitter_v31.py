"""Persist fixed and outcome-selected cases, actual vectors and saved-fit probes."""
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
import prepare_practical_hitter_v31 as r
from universal_baseball.practical_hitter_v30 import EVENTS
from universal_baseball.storage import sha256_file

CORE=['base_hurdle','detail_hurdle','direct_detail']
RATE=['floor','rate_ridge_equal','rate_ridge_pa','rate_hist_equal','rate_hist_pa']
FIXED=[(592450,2016),(592450,2021),(668715,2022),(691026,2023),(667670,2022),
    (621566,2017),(666158,2023),(680574,2024),(665487,2021),(665487,2022),
    (677551,2023),(672779,2024),(519346,2016),(805811,2024),(815908,2024),(815888,2024)]


def select(f):
    chosen={}
    def add(g,reason):
        if len(g):
            s=g.row(0,named=True);chosen.setdefault(s['row_id'],[]).append(reason)
    for pid,year in FIXED:add(f.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==year)),'fixed predeclared diagnostic')
    for arm in CORE:
        g=f.filter(pl.col('v24_row_id').is_not_null()).with_columns(((pl.col(arm+'_value')-pl.col('next_value'))**2-(pl.col('v24_value')-pl.col('next_value'))**2).alias('_change'))
        add(g.sort('_change'),arm+' largest value gain vs V24');add(g.sort('_change',descending=True),arm+' largest value harm vs V24')
    n=f.filter(pl.col('legacy_n_pa').is_not_null()).with_columns(((pl.col('detail_hurdle_value')-pl.col('next_value'))**2-(pl.col('legacy_n_value')-pl.col('next_value'))**2).alias('_change'))
    add(n.sort('_change'),'detailed hurdle largest gain vs older N');add(n.sort('_change',descending=True),'detailed hurdle largest harm vs older N')
    g=f.with_columns((pl.col('detail_hurdle_value')-pl.col('next_value')).alias('_error'))
    add(g.sort('_error',descending=True),'largest detailed-hurdle false high');add(g.sort('_error'),'largest detailed-hurdle false low')
    add(g.filter((pl.col('next_pa')>=200)&(pl.col('next_pa')<400)).sort(pl.col('_error').abs()),'ordinary well-predicted partial workload')
    add(g.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Upper minors')).sort('_error'),'largest missed pre-debut upper-minor contribution')
    for arm in ['rate_ridge_equal','rate_ridge_pa','rate_hist_equal','rate_hist_pa']:
        add(f.sort(pl.col(arm+'_rate').abs(),descending=True),arm+' largest absolute conditional rating')
    return chosen


def main():
    assert r.read(r.OUT/'verification.json')['saved_heads_replayed']==700
    pre=r.read(r.OUT/'preflight-ready.json');f=pl.read_parquet(r.OUT/'scored-predictions.parquet');allsource=pl.read_parquet(pre['ready_features'])
    counts=pl.read_parquet(r.OUT/'counts.parquet');support=pl.read_parquet(r.OUT/'conditional-head-support.parquet');chosen=select(f);cases=[]
    with threadpool_limits(limits=2):
        for rid,reasons in chosen.items():
            o=f.filter(pl.col('row_id')==rid).row(0,named=True);year,fold=o['origin_year'],o['outer_fold'];pid=o['player_id']
            cell=next(c for c in pre['cells'] if c['year']==year and c['fold']==fold)
            tr=allsource.filter(pl.col('row_id').is_in(cell['training_row_ids']))
            x=np.array([[o[c] for c in pre['detail_features']]],dtype=float);neutral=x.copy()
            for i,c in enumerate(pre['detail_features']):
                if not c.startswith('MLB_') and c.rsplit('_',1)[-1] in EVENTS:neutral[0,i]=EVENTS[c.rsplit('_',1)[-1]][2]
            arms={}
            for arm in CORE:
                v=dict(pa=o[arm+'_pa'],value=o[arm+'_value']);arms[arm]=v
                features=pre['base_features'] if arm=='base_hurdle' else pre['detail_features'];z=np.array([[o[c] for c in features]])
                nz=z if arm=='base_hurdle' else neutral
                if arm.endswith('hurdle'):
                    model=joblib.load(r.OUT/f'{arm}-state-{year}-{fold}.joblib');p=model.predict_proba(nz)[0]
                    if o['hard_unavailable']:p=np.array([1,0,0,0])
                    v['probabilities']=[o[arm+f'_p{i}'] for i in range(4)]
                    v['conditional_pa']=[o[arm+f'_conditional_pa{i}'] for i in [1,2,3]]
                    v['conditional_value']=[o[arm+f'_conditional_value{i}'] for i in [1,2,3]]
                    pa=0;value=0
                    for state in [1,2,3]:
                        lower,upper=[(1,199),(200,399),(400,800)][state-1]
                        pa+=p[state]*float(np.clip(joblib.load(r.OUT/f'{arm}-pa{state}-{year}-{fold}.joblib').predict(nz)[0],lower,upper))
                        value+=p[state]*float(joblib.load(r.OUT/f'{arm}-value{state}-{year}-{fold}.joblib').predict(nz)[0])
                    v['neutral_minor_rate_probe']=dict(pa=pa,value=value,probabilities=p.tolist())
                else:
                    pa=float(np.clip(joblib.load(r.OUT/f'{arm}-pa-{year}-{fold}.joblib').predict(nz)[0],0,800))
                    value=float(joblib.load(r.OUT/f'{arm}-value-{year}-{fold}.joblib').predict(nz)[0])
                    if o['hard_unavailable'] or pa==0: value=0
                    if o['hard_unavailable']:pa=0
                    v['neutral_minor_rate_probe']=dict(pa=pa,value=value)
            rates={a:o[a+'_rate'] for a in RATE};terms={}
            for arm in ['rate_ridge_equal','rate_ridge_pa']:
                model=joblib.load(r.OUT/f'{arm}-{year}-{fold}.joblib');scaler=model.named_steps['standardscaler'];ridge=model.named_steps['ridge']
                standardized=scaler.transform(x)[0];contributions=standardized*ridge.coef_
                assert np.isclose(contributions.sum()+ridge.intercept_,rates[arm],atol=1e-9)
                inds=np.argsort(abs(contributions))[::-1][:8]
                terms[arm]=dict(intercept=float(ridge.intercept_),terms=[dict(feature=pre['detail_features'][i],input=float(x[0,i]),
                    training_mean=float(scaler.mean_[i]),training_sd=float(np.sqrt(scaler.var_[i])),standardized_input=float(standardized[i]),contribution=float(contributions[i])) for i in inds])
            peerpool=f.filter((pl.col('origin_year')==year)&(pl.col('row_id')!=rid)&(pl.col('stage')==o['stage'])&(pl.col('prior_debut')==o['prior_debut']))
            # No next-year outcomes or candidate errors are used in distances.
            distance=sum(((pl.col(k)-o[k])/scale)**2 for k,scale in [('age',5),('elapsed',5),('pa_0',200),('AAA_0_pa',200),('AA_0_pa',200),('minor_pa_0',300),('quality_0',1)])
            peers=peerpool.with_columns(distance.alias('origin_distance')).sort('origin_distance','player_id').head(3).select(
                'player_id','player_name','age','stage','source_position','pa_0','AAA_0_pa','AA_0_pa','DSL_0_pa','quality_0','on_40man',
                'detail_hurdle_pa','detail_hurdle_value','next_pa','next_value','origin_distance').to_dicts()
            context=tr.filter((pl.col('stage')==o['stage'])&(pl.col('prior_debut')==o['prior_debut'])&((pl.col('age')//5)==int(o['age']//5)))
            history=counts.filter((pl.col('player_id')==pid)&pl.col('season').is_between(year-2,year)).sort('season','bucket').to_dicts()
            cases.append(dict(origin={k:v for k,v in o.items() if k not in pre['detail_features']},selection=reasons,
                raw_level_history=history,actual_features={k:o[k] for k in pre['detail_features']},arms=arms,rates=rates,ridge_terms=terms,
                training_profile=dict(players=context['player_id'].n_unique(),rows=len(context),mean_pa=float(context['next_pa'].mean()) if len(context) else None,
                    zero_fraction=float((context['next_pa']==0).mean()) if len(context) else None),
                conditional_support=support.filter(pl.col('row_id')==rid).select('head','conditional_profile_players').to_dicts(),comparisons=peers))
    r.write('cases.json',cases);r.write('case-manifest.json',dict(cases=len(cases),selection='Predeclared identities plus each core arm value gain/harm, older N gain/harm, false high/low, ordinary case, pre-debut miss and rate extremes.',
        comparison_rule='Same origin/source stage/prior debut, nearest standardized origin age/elapsed/MLB/AAA/AA/minor exposure/observed quality; no outcomes in distance.',
        probe='All minor event rates moved to their fixed priors, exposures and MLB quality unchanged; saved parameters only. Artificial combinations, not causal or replacement forecasts.',
        cases_sha256=sha256_file(r.OUT/'cases.json'),player_walkthrough_status='pending'))
    for c in cases:
        o=c['origin'];print(f"{o['player_name']} {o['origin_year']}: actual {o['next_pa']} PA / {o['next_value']:.2f} value; base {c['arms']['base_hurdle']['pa']:.0f}/{c['arms']['base_hurdle']['value']:.2f}; detail {c['arms']['detail_hurdle']['pa']:.0f}/{c['arms']['detail_hurdle']['value']:.2f}; direct {c['arms']['direct_detail']['pa']:.0f}/{c['arms']['direct_detail']['value']:.2f}; rates ridge/weighted tree {c['rates']['rate_ridge_pa']:.2f}/{c['rates']['rate_hist_pa']:.2f}; selected {c['selection']}")


if __name__=='__main__':main()
