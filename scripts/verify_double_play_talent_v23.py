"""Independent forecast, support, person-score and bootstrap replay."""
from collections import Counter, defaultdict
from pathlib import Path
import json

import numpy as np
import polars as pl
from universal_baseball.storage import sha256_file
from verify_double_play_support_v22 import ROOT, read, write

PUBLIC=ROOT/'reports/model-evidence/defense-double-play-talent-v23'
V22=ROOT/'reports/model-evidence/defense-double-play-source-v22'


def scores(rows, arm):
    counts=Counter(r['player_id'] for r in rows)
    weights=np.array([1/counts[r['player_id']] for r in rows])
    error=np.array([r[arm]-r['quality_rate'] for r in rows])
    return dict(rows=len(rows),people=len(counts),rmse=float(np.sqrt(np.average(error**2,weights=weights))),
        mae=float(np.average(abs(error),weights=weights)),bias=float(np.average(error,weights=weights)),
        oracle_exposure_predicted_runs=sum(r[arm]*r['future_outs']/1500 for r in rows),
        oracle_exposure_actual_runs=sum(r['future_runs'] for r in rows))


def close(a,b):
    if isinstance(a,dict):
        assert a.keys()==b.keys()
        for k in a:close(a[k],b[k])
    elif isinstance(a,list):
        assert len(a)==len(b)
        for x,y in zip(a,b,strict=True):close(x,y)
    elif isinstance(a,(float,int)) and not isinstance(a,bool):
        np.testing.assert_allclose(a,b,rtol=1e-10,atol=1e-11)
    else:assert a==b,(a,b)


def profile(r):
    a=r['age']; n=r['dp_history_outs']
    return r['position'],'unknown' if a is None else '<=24' if a<=24 else '25-29' if a<=29 else '30+','<1500' if n<1500 else '1500-4499' if n<4500 else '4500+'


def main():
    report=read(PUBLIC/'report.json.gz');pre=read(PUBLIC/'preflight.json.gz')
    for r in (pre,report,read(V22/'final-review.json.gz')):
        for p,d in r['hashes'].items():assert sha256_file(Path(p))==d,p
    assert pre['learned_parameters']==report['learned_parameters']==0
    native=defaultdict(list)
    for n in pl.read_parquet(ROOT/'reports/generated/defense-native-range-v3/component-ledger.parquet').to_dicts():native[n['player_id']].append(n)
    originrows=[r for r in read(V22/'labels.json.gz') if r['population']=='MLB_history']; derived=[]
    for r in originrows:
        y=r['origin_year']; pos=r['position'];trace=[]; runs=0.;outs=0.;unknown=0
        for n in sorted((n for n in native[r['player_id']] if y-2<=n['season']<=y and n['position']==pos),key=lambda n:n['season']):
            valid=n['exposure_valid'] and n['dp_runs'] is not None and n['native_outs']>0
            weight=2.**(n['season']-y)
            trace.append(dict(source=n,recency_weight=weight,used=valid,weighted_outs=n['native_outs']*weight if valid else 0.,
                weighted_runs=n['dp_runs']*weight if valid else None))
            if valid:runs+=n['dp_runs']*weight;outs+=n['native_outs']*weight
            else:unknown+=n['official_outs']
        derived.append(dict(r,dp_history_runs=runs,dp_history_outs=outs,dp_history_seasons=sum(t['used'] for t in trace),
            dp_missing_history_official_outs=unknown,dp_history_left_truncated=y-2<2016,dp_raw_rate=1500*runs/outs if outs else None,
            dp_reliability=outs/(outs+3000),neutral=0.,candidate=1500*runs/(outs+3000),dp_prior_outs=3000.,fallback=outs==0,trace=trace))
    preds=read(PUBLIC/'predictions.json.gz');support=read(PUBLIC/'support.json.gz');actualkeys=set()
    for cell in support:
        year=cell['origin'];fold=cell['held_fold']
        tr=[r for r in derived if r['quality_rate'] is not None and r['window_end']<=year and r['player_id']%5!=fold]
        te=[r for r in derived if r['origin_year']==year and r['player_id']%5==fold]
        assert cell['training_people']==len({r['player_id'] for r in tr})
        assert cell['training_keys']==[[r['origin_year'],r['player_id'],r['position']] for r in tr]
        assert cell['training_origins']==sorted({r['origin_year'] for r in tr})
        assert cell['training_windows_with_2020']==sum(r['origin_year']<2020<=r['window_end'] for r in tr)
        assert cell['test_rows']==len(te) and cell['model_fits']==0
        assert {r['player_id'] for r in tr}.isdisjoint(r['player_id'] for r in te)
        neighborhoods=defaultdict(set)
        for r in tr:neighborhoods[profile(r)].add(r['player_id'])
        expected=[]
        for r in te:
            k=(year,r['player_id'],r['position']);assert k not in actualkeys;actualkeys.add(k)
            n=len(neighborhoods[profile(r)])
            expected.append(dict(identity=list(k),profile=list(profile(r)),distinct_training_people=n))
            p=next(p for p in preds if (p['origin_year'],p['player_id'],p['position'])==k)
            close(dict(r,fold=fold,distinct_profile_training_people=n,sparse_profile=n<10),p)
        assert expected==cell['profile_counts']
    assert len(preds)==len(actualkeys)==sum(r['origin_year'] in (2021,2022) for r in derived)
    mse=[]
    for result in report['results']:
        year=result['origin'];measured=[r for r in preds if r['origin_year']==year and r['quality_rate'] is not None]
        for arm in ('neutral','candidate'):close(scores(measured,arm),result[arm])
        for group in result['groups']:
            j={'position':0,'age':1,'history_exposure':2}[group['kind']]
            subset=[r for r in measured if profile(r)[j]==group['group']]
            for arm in ('neutral','candidate'):close(scores(subset,arm),group[arm])
        persons=defaultdict(list)
        for r in measured:persons[r['player_id']].append(r)
        loss=np.array([[np.mean([(r[a]-r['quality_rate'])**2 for r in rs]) for a in ('candidate','neutral')] for rs in persons.values()])
        seed=23023 if year==2022 else 23022;rng=np.random.default_rng(seed);samples=[]
        for _ in range(2000):
            picked=loss[rng.integers(len(loss),size=len(loss))]
            samples.append(float(np.sqrt(picked[:,0].mean())-np.sqrt(picked[:,1].mean())))
        close(dict(seed=seed,draws=2000,difference=float(np.sqrt(loss[:,0].mean())-np.sqrt(loss[:,1].mean())),
            interval_95=np.quantile(samples,[.025,.975]).tolist()),result['paired_RMSE'])
        counts=Counter(r['player_id'] for r in measured);w=np.array([1/counts[r['player_id']] for r in measured]);p=np.array([r['candidate'] for r in measured]);t=np.array([r['quality_rate'] for r in measured])
        variance=float(np.average(p*p,weights=w));cross=float(2*np.average(p*t,weights=w))
        close(variance-cross,result['candidate']['rmse']**2-result['neutral']['rmse']**2)
        mse.append(dict(origin=year,forecast_square=variance,twice_forecast_target_product=cross,MSE_change=variance-cross,
            interpretation='Historic forecast magnitude exceeds its alignment with later quality; not a causal traffic attribution'))
        assert result['eligible_rows']==sum(r['origin_year']==year for r in preds)
        assert result['fallback_rows']==sum(r['origin_year']==year and r['fallback'] for r in preds)
        assert result['sparse_rows']==sum(r['origin_year']==year and r['sparse_profile'] for r in preds)
        assert result['unknown_quality_rows']==sum(r['origin_year']==year and r['quality_rate'] is None for r in preds)
        failures=[]
        if result['paired_RMSE']['interval_95'][1]>=0:failures.append('no_supported_RMSE_gain')
        if result['candidate']['mae']>result['neutral']['mae']:failures.append('MAE_worsens')
        if abs(result['candidate']['bias'])>max(.15,abs(result['neutral']['bias'])+.05):failures.append('bias_limit')
        for g in result['groups']:
            if g['kind']=='position' and g['neutral']['people']>=10 and g['candidate']['rmse']>1.05*g['neutral']['rmse']:failures.append(f"position_{g['group']}_RMSE_harm")
        assert failures==result['quality_screen_failures']
    out=dict(status='pass',all_forecasts_replayed=len(preds),origin_rows_reconstructed=len(derived),support_cells=len(support),
        scores_and_bootstrap_replayed=True,MSE_diagnostics=mse,model_refits=0,no_2026_selection=True,
        predictive_screen_not_deployment=True,hashes={str(p):sha256_file(p) for p in
            (Path(__file__),PUBLIC/'preflight.json.gz',PUBLIC/'report.json.gz',PUBLIC/'predictions.json.gz',PUBLIC/'support.json.gz')})
    write(PUBLIC/'independent-review.json.gz',out)
    print(json.dumps({k:v for k,v in out.items() if k!='hashes'},indent=2),flush=True)


if __name__=='__main__':main()
