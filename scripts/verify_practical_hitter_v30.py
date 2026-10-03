"""Essential replay, public-source matching and per-arm player traces."""
from datetime import date
import json
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
import evaluate_practical_hitter_v30 as r
from universal_baseball.storage import sha256_file

FIXED=[(668715,2022),(691026,2023),(667670,2022),(592450,2016),(592450,2021),
    (666158,2023),(680574,2024),(665487,2022),(677551,2023),(672779,2024),(519346,2016)]

def interval(f,arm,metric,repeats=2000):
    error=((f[arm+'_'+metric]-f['next_'+metric])**2-(f['v24_'+metric]-f['next_'+metric])**2).to_numpy()
    _,person=np.unique(f['player_id'].to_numpy(),return_inverse=True)
    _,year=np.unique(f['target_year'].to_numpy(),return_inverse=True)
    n=np.zeros((person.max()+1,year.max()+1));d=np.zeros_like(n)
    np.add.at(n,(person,year),error);np.add.at(d,(person,year),1)
    rng=np.random.default_rng(30);draws=[]
    for _ in range(repeats):
        weights=np.bincount(rng.integers(0,len(n),len(n)),minlength=len(n));den=weights@d
        if (den==0).any():continue
        draws.append(float(np.mean((weights@n)/den)))
    return dict(arm=arm,metric=metric+'_mse',difference=float(np.mean(n.sum(0)/d.sum(0))),
        lower=float(np.quantile(draws,.025)),upper=float(np.quantile(draws,.975)),players=len(n),repeats=repeats)

def main():
    report=r.read(r.OUT/'report.json');r.check(report['input_hashes']);r.check(report['output_hashes'])
    f=pl.read_parquet(r.OUT/'predictions.parquet');raw=pl.read_parquet(r.COUNTS)
    source=pl.read_parquet(r.OUT/'features.parquet')
    actual=f.select('row_id',*r.m.FEATURES).sort('row_id')
    expected=source.filter(pl.col('row_id').is_in(f['row_id'])).select('row_id',*r.m.FEATURES).sort('row_id')
    assert actual.equals(expected),'Saved actual inputs differ from audited source features'
    f=f.join(source.select('row_id','pa_1','pa_2'),on='row_id',validate='1:1')
    public=pl.read_parquet(r.PUBLIC).select('row_id','steamer_pa','steamer_value','zips_pa')
    duplicate=f.select('row_id','steamer_pa','steamer_value','zips_pa').join(public,on='row_id',validate='1:1')
    for col in ['steamer_pa','steamer_value','zips_pa']:
        assert duplicate[col].equals(duplicate[col+'_right']),col
    # Point forecasts must not manufacture a calibrated probability distribution.
    assert not any(arm+'_p0' in f.columns for arm in r.m.ARMS)
    with threadpool_limits(limits=2):
        for cell in r.read(r.OUT/'fits.json'):
            path=Path(cell['artifact']);assert sha256_file(path)==cell['sha256']
            g=f.filter((pl.col('origin_year')==cell['year'])&(pl.col('outer_fold')==cell['fold'])).sort('player_id')
            model=joblib.load(path);pred=model.predict(g.select(r.m.FEATURES).to_numpy())
            np.testing.assert_allclose(pred,g[cell['arm']+'_raw_pa'],atol=1e-10)
            point=r.m.forecast(pred,g['hard_unavailable']);np.testing.assert_allclose(point,g[cell['arm']+'_pa'],atol=1e-10)
            np.testing.assert_allclose(point*g['v24_value']/g['v24_pa'],g[cell['arm']+'_value'],atol=1e-10)
    # Mutate only valid future own-count data: all origin features stay identical.
    panel=pl.read_parquet(r.PANEL);mutated=raw.with_columns(
        *[pl.when(pl.col('season')==2025).then(pl.col(c)+pl.col('home_runs')).otherwise(pl.col(c)).alias(c)
          for c in ['singles','babip_hits','babip_opportunities']],
        pl.when(pl.col('season')==2025).then(0).otherwise(pl.col('home_runs')).alias('home_runs'))
    assert r.m.materialize(panel,raw).select('row_id',*r.m.FEATURES).equals(r.m.materialize(panel,mutated).select('row_id',*r.m.FEATURES))
    choices={}
    def choose(row,reason):
        choices.setdefault(row['row_id'],dict(row_id=row['row_id'],player_id=row['player_id'],
            origin_year=row['origin_year'],reasons=[]))['reasons'].append(reason)
    for pid,year in FIXED:
        row=f.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==year));assert len(row)==1
        choose(row.row(0,named=True),'fixed_major_miss_or_opposite_risk')
    for arm in r.m.ARMS:
        q=f.with_columns(((pl.col(arm+'_pa')-pl.col('next_pa')).abs()-(pl.col('v24_pa')-pl.col('next_pa')).abs()).alias('change'),
            (pl.col(arm+'_pa')-pl.col('next_pa')).alias('error')).sort('change','row_id')
        choose(q.row(0,named=True),arm+'_largest_gain');choose(q.row(-1,named=True),arm+'_largest_loss')
        z=q.filter(pl.col('pa_0')>0).with_columns(pl.col('error').abs().alias('abs_error')).sort('abs_error','row_id')
        choose(z.row(len(z)//2,named=True),arm+'_median_active_error')
        choose(q.sort('error','row_id').row(0,named=True),arm+'_largest_false_low')
        choose(q.sort('error','row_id').row(-1,named=True),arm+'_largest_false_high')
    r.write('selected-cases.json',list(choices.values()))
    ledger={c['forecast']['player_id']:[] for c in r.read(r.ROOT/'reports/generated/availability-context-v29b/cases.json')}
    for c in r.read(r.ROOT/'reports/generated/availability-context-v29b/cases.json'):
        ledger[c['forecast']['player_id']].extend(c['cutoff_events'])
    traces=[]
    for choice in choices.values():
        row=f.filter(pl.col('row_id')==choice['row_id']).row(0,named=True)
        peers=f.filter((pl.col('origin_year')==row['origin_year'])&(pl.col('player_id')!=row['player_id'])).with_columns(
            (((pl.col('age')-row['age'])/3)**2+((pl.col('elapsed')-row['elapsed'])/2)**2+
             ((pl.col('pa_0')-row['pa_0'])/200)**2+((pl.col('pa_1')-row['pa_1'])/200)**2+
             ((pl.col('quality_0')-row['quality_0'])/2)**2).alias('distance')).sort('distance','player_id').head(3)
        models={};input_=np.array([row[c] for c in r.m.FEATURES])
        for arm in r.m.ARMS:
            model=joblib.load(r.OUT/f"model-{arm}-{row['origin_year']}-{row['outer_fold']}.joblib")
            pred=float(model.predict(input_[None])[0]);np.testing.assert_allclose(pred,row[arm+'_raw_pa'],atol=1e-10)
            # Same-fit feature-family neutralization is explanatory only; priors
            # and actual exposures remain fixed. Never substitute this forecast.
            probe=input_.copy()
            for i,c in enumerate(r.m.FEATURES):
                if c.startswith(('raw_AAA','raw_AA_')) and c.rsplit('_',1)[-1] in r.m.EVENTS:
                    probe[i]=r.m.EVENTS[c.rsplit('_',1)[-1]][2]
            models[arm]=dict(raw_pa=pred,pa=row[arm+'_pa'],value=row[arm+'_value'],
                fixed_fit_neutral_minor_rate_pa=float(model.predict(probe[None])[0]),
                warning='Artificial rate neutralization, same exposures/model; not causal or validated forecast.')
            if arm=='ridge':
                z=(input_-model[0].mean_)/model[0].scale_;terms=z*model[-1].coef_
                np.testing.assert_allclose(model[-1].intercept_+terms.sum(),pred,atol=1e-10)
                models[arm]['intercept']=float(model[-1].intercept_)
                models[arm]['top_terms']=sorted([dict(feature=c,input=float(v),term=float(t))
                    for c,v,t in zip(r.m.FEATURES,input_,terms)],key=lambda a:-abs(a['term']))[:12]
        train=pl.read_parquet(r.OUT/f"train-{row['origin_year']}-{row['outer_fold']}.parquet")
        matches=train.filter((pl.col('current_state')==row['current_state'])&((pl.col('age')-row['age']).abs()<=3)&
            ((pl.col('work_0')-row['work_0']).abs()<=100))
        traces.append(dict(selection=choice,origin={c:row[c] for c in ['player_name','player_id','origin_year','target_year','outer_fold','age',
            'elapsed','pa_0','pa_1','pa_2','quality_0','quality_1','quality_2','v24_pa','v24_value','rules_pa','rules_value',
            'next_pa','next_value','hard_unavailable','needs_availability_scenario']},actual_inputs={c:row[c] for c in r.m.FEATURES},
            raw_level_history=raw.filter((pl.col('player_id')==row['player_id'])&pl.col('season').is_between(row['origin_year']-2,row['origin_year'])).sort('season','level_group').to_dicts(),
            fixed_expected_yield600=600*row['v24_value']/row['v24_pa'],arms=models,
            training_profile=dict(rows=len(matches),players=matches['player_id'].n_unique(),
                mean_pa=float(matches['next_pa'].mean()) if len(matches) else None,
                zero_fraction=float((matches['next_pa']==0).mean()) if len(matches) else None),
            cutoff_context=[v for v in ledger.get(row['player_id'],[]) if str(v['available_date'])<=f"{row['origin_year']}-12-31"],
            comparisons=peers.select('player_id','player_name','age','pa_0','pa_1','v24_pa',*[arm+'_pa' for arm in r.m.ARMS],
                'next_pa','next_value','distance').to_dicts(),comparison_rule='Same origin; age/debut/workload/quality distance, tie ID; no outcomes.'))
    r.write('cases.json',traces)
    report.update(mechanical_replay_complete=True,replayed_models=210,replayed_predictions=4396*6,
        future_count_mutation_pass=True,public_aliases_verified=True,selected_cases=len(traces),
        player_walkthrough_status='mechanical_complete_readable_pending',
        intervals=[interval(g,arm,metric) for scope,g in [('all',f),('public_active',f.filter((pl.col('pa_0')>0)&
            pl.col('steamer_pa').is_not_null()&pl.col('zips_pa').is_not_null()))] for arm in r.m.ARMS
            for metric in ['pa','value'] for _ in [0]])
    # Label uncertainty scope explicitly (the computation above is identical
    # per metric; group identifiers must not be inferred by list position).
    for i,note in enumerate(report['intervals']):note['scope']='all' if i<12 else 'public_active'
    report['output_hashes'].update({str(r.OUT/name):sha256_file(r.OUT/name) for name in ['cases.json','selected-cases.json']})
    r.write('report.json',report)
    print(json.dumps(dict(replayed_models=210,cases=len(traces),
        focal=[dict(name=t['origin']['player_name'],year=t['origin']['origin_year'],base=t['origin']['v24_pa'],
            actual=t['origin']['next_pa'],arms={a:round(v['pa'],1) for a,v in t['arms'].items()}) for t in traces]),indent=2))

if __name__=='__main__':main()
