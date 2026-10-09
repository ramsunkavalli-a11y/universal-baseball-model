"""Replay refreshed heads and walk source evidence into the 2027 forecast."""
import gzip
import json
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.storage import sha256_file
from prepare_practical_hitter_v33 import safe_matrix
from fit_hitter_2027_refresh import ROOT,OUT,PUBLIC
from capture_hitter_2027_origin_counts import write_once


def main():
    receipt=PUBLIC/'batting-refresh-player-review.json';assert not receipt.exists()
    fit=json.loads((PUBLIC/'batting-refresh-fit.json').read_text());assert sha256_file(Path(fit['forecast_path']))==fit['forecast_sha256']
    f=pl.read_parquet(fit['forecast_path']);pre=json.loads((OUT/'preflight.json').read_text())
    source=json.loads(gzip.decompress((PUBLIC/'base-input-player-walks.json.gz').read_bytes()))
    cases=source['cases'];ids={w['player_id'] for c in cases for w in [c['primary'],*c['peers']]}
    extremes=f.sort('hitting_wins_per_600',descending=True).head(8)['player_id'].to_list()+f.sort('hitting_wins_per_600').head(8)['player_id'].to_list()
    old=pl.read_parquet(ROOT/'model_artifacts/hitter-selected-2026-frozen-2026-10-05/forecast.parquet')
    paired=f.select('player_id','hitting_wins_per_600','expected_pa').join(old.select('player_id',pl.col('hitting_wins_per_600').alias('old_rate'),pl.col('expected_pa').alias('old_pa')),on='player_id')
    paired=paired.with_columns((pl.col('hitting_wins_per_600')-pl.col('old_rate')).alias('rate_change'),(pl.col('expected_pa')-pl.col('old_pa')).alias('pa_change'))
    changes=paired.sort('rate_change').head(4)['player_id'].to_list()+paired.sort('rate_change',descending=True).head(4)['player_id'].to_list()+paired.sort('pa_change').head(4)['player_id'].to_list()+paired.sort('pa_change',descending=True).head(4)['player_id'].to_list()
    ids.update(extremes+changes);details={}
    with threadpool_limits(limits=2):
        for fold in range(5):
            q=f.filter(pl.col('outer_fold')==fold);r=json.loads((OUT/f'fit-{fold}.json').read_text())
            for h in r['heads']:
                model=joblib.load(h['path']);cols=h['features'];israte=h['head'].startswith('rate')
                x=safe_matrix(q,cols) if israte else q.select(cols).to_numpy()
                pred=model.predict_proba(x)[:,1] if h['head']=='participation' else model.predict(x)
                assert np.allclose(pred,q['raw_'+h['head']].to_numpy(),rtol=0,atol=1e-12)
                if israte:
                    contributions=x*model.coef_
                    assert np.allclose(contributions.sum(axis=1)+model.intercept_,pred,rtol=0,atol=1e-10)
                    for i,o in enumerate(q.iter_rows(named=True)):
                        if o['player_id'] not in ids:continue
                        values=contributions[i]
                        top=np.argsort(abs(values))[::-1][:12]
                        groups={prefix:float(sum(values[j] for j,c in enumerate(cols) if c.startswith(prefix))) for prefix in ['translated_','sc_','scout_','pooled_DSL_','pooled_MLB_','draft_','position_']}
                        details.setdefault(o['player_id'],{})[h['head']]=dict(prediction=float(pred[i]),intercept=float(model.intercept_),grouped_contributions=groups,
                            largest_terms=[dict(feature=cols[j],input=float(x[i,j]),coefficient=float(model.coef_[j]),contribution=float(values[j])) for j in top])
    assert np.allclose(f['expected_pa'].to_numpy(),f['participation_probability'].to_numpy()*f['conditional_pa'].to_numpy(),rtol=0,atol=1e-12)
    assert np.allclose(f['batting_contribution'].to_numpy(),f['expected_pa'].to_numpy()*(f['hitting_wins_per_600'].to_numpy()/600+570/183849),rtol=0,atol=1e-12)
    for c in cases:
        for w in [c['primary'],*c['peers']]:
            o=f.filter(pl.col('player_id')==w['player_id']).row(0,named=True)
            w['forecast']={k:o[k] for k in ['talent_route','raw_participation','raw_conditional_pa','participation_probability','conditional_pa',
                'expected_pa','hitting_wins_per_600','batting_contribution','reported_retired','hard_unavailable','nonmedical_reason']}
            w['linear_head_trace']=details[w['player_id']]
            w['comparison_2026_forecast']=old.filter(pl.col('player_id')==w['player_id']).select('expected_pa','hitting_wins_per_600').to_dicts()
            w['observed_2027']=None
            w['interpretation']='New season, new evidence and one added training year; change from the 2026 forecast is not an accuracy improvement. Batting contribution includes replacement but excludes all nonbatting components.'
    support=pl.read_parquet(OUT/'profile-support.parquet')
    groups=f.group_by('stage').agg(pl.len().alias('players'),pl.col('expected_pa').sum(),pl.col('pa_0').sum().alias('observed_2026_PA'),
        pl.col('participation_probability').sum(),pl.col('batting_contribution').sum()).to_dicts()
    additional=[dict(player=f.filter(pl.col('player_id')==pid).select('player_id','player_name','stage','age','pa_0','minor_pa_0','talent_route',
        'expected_pa','hitting_wins_per_600','batting_contribution','reported_retired','nonmedical_reason').to_dicts()[0],
        contribution_trace=details[pid],selection='Highest/lowest rate or largest signed year-to-year forecast change; diagnostic, not validation') for pid in sorted(set(extremes+changes))]
    path=PUBLIC/'batting-refresh-player-walks.json.gz';assert not path.exists()
    path.write_bytes(gzip.compress(json.dumps(dict(cases=cases,additional=additional),allow_nan=False,default=str).encode(),mtime=0))
    write_once(receipt,dict(forecast_year=2027,player_walkthrough='complete',fixed_cases=8,peers=24,additional_extreme_cases=len(additional),
        replayed_heads=25,replayed_players=len(f),arithmetic_pass=True,groups=groups,
        sparse_support=support.filter(pl.col('training_people')<20).group_by('head').agg(pl.col('row_id').n_unique()).to_dicts(),
        open_limits=['2027 preseason ranking unavailable at this cutoff','New prospects and uncertain availability retain sparse-support warnings',
            'No 2027 accuracy can be measured yet','Nonbatting value and organization rights are still not integrated'],
        current_named_forecasts=[c['primary']['forecast']|{'player_id':c['player_id'],'name':c['primary']['name']} for c in cases],
        source_fit_sha256=sha256_file(PUBLIC/'batting-refresh-fit.json'),walk_sha256=sha256_file(path),
        predictive_improvement_claim=False,full_model_release_approved=False,runner_sha256=sha256_file(Path(__file__))))
    print(json.dumps(groups,indent=2),flush=True)


if __name__=='__main__':main()
