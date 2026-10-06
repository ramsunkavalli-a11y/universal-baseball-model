"""Independent fit replay and mandatory named-player trace, no new fits."""

import json
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from run_minor_infield_play_share import OUT, PUBLIC, BASE, FIXED, ARMS, read, verify, scores
from run_hitter_finite_return_baseline import protections, save
from universal_baseball.minor_infield_play_share import pooled, POSITIONS
from universal_baseball.storage import sha256_file


def main():
    protections()
    report=read(OUT/'fit-report.json'); verify(report['hashes'])
    q=pl.read_parquet(OUT/'predictions.parquet')
    f=pl.read_parquet(OUT/'features.parquet')
    a=pl.read_parquet(OUT/'annual.parquet')
    assert q['row_id'].n_unique()==q.height
    fits={(m['origin'],m['fold'],m['target'],m['arm']):m for m in report['fits']}
    replay=[]
    for meta in report['fits']:
        assert sha256_file(Path(meta['path']))==meta['sha256']
        model=joblib.load(meta['path'])
        test=q.filter((pl.col('origin_year')==meta['origin'])&(pl.col('player_id')%5==meta['fold']))
        pred=model.predict(test.select(meta['features']).to_numpy())
        err=float(np.max(abs(pred-test[f"{meta['target']}_{meta['arm']}"].to_numpy())))
        assert err<1e-12
        replay.append(dict(origin=meta['origin'],fold=meta['fold'],target=meta['target'],arm=meta['arm'],rows=test.height,max_error=err))
    # Independently reconstruct every pooled numerator and rate from saved annual evidence.
    for origin in f['origin_year'].unique():
        p=pooled(a,origin)
        for pos in POSITIONS:
            z=f.filter(pl.col('origin_year')==origin).join(p.filter(pl.col('position')==pos).select('player_id','ground_balls','credits','expected_credits','complete_rate','legacy_rate'),on='player_id',how='left')
            for source, feature in [('ground_balls',f'gb_{pos}'),('credits',f'credits_{pos}'),('expected_credits',f'expected_{pos}'),('complete_rate',f'complete_{pos}'),('legacy_rate',f'legacy_{pos}')]:
                assert np.max(abs(z[source].fill_null(0).to_numpy()-z[feature].to_numpy()))<1e-10
    recent=q.filter(pl.col('origin_year')>=2022)
    for target in ['delivered','quality']:
        assert scores(recent,target)==report[f'recent_{target}']
    scored=recent.filter(pl.col('delivered').is_not_null()).with_columns(
        ((pl.col('delivered_complete')-pl.col('delivered'))**2-(pl.col('delivered_benchmark')-pl.col('delivered'))**2).alias('loss_change'),
        (pl.col('delivered_complete')-pl.col('delivered')).alias('error'),
    )
    selection={}
    for pid,origin in FIXED:
        selection.setdefault((pid,origin),[]).append('fixed diagnostic')
    rules={
        'largest squared-loss improvement':scored.sort('loss_change').head(1),
        'largest squared-loss deterioration':scored.sort('loss_change',descending=True).head(1),
        'largest false high':scored.sort('error',descending=True).head(1),
        'largest false low':scored.sort('error').head(1),
        'ordinary active well-predicted':scored.filter((pl.col('future_official_outs')>0)&(pl.col('delivered').abs()<1)).with_columns(pl.col('error').abs().alias('abs_error')).sort('abs_error','player_id').head(1),
        'non-arrival largest absolute quality forecast':scored.filter((pl.col('prior_mlb_defense')==0)&(pl.col('future_official_outs').fill_null(0)==0)).with_columns(pl.col('quality_complete').abs().alias('abs_quality')).sort('abs_quality',descending=True).head(1),
    }
    for reason, chosen in rules.items():
        for row in chosen.iter_rows(named=True):
            selection.setdefault((row['player_id'],row['origin_year']),[]).append(reason)
    cases=[]
    for (pid,origin),reason in selection.items():
        chosen=q.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==origin))
        if not chosen.height:
            cases.append(dict(player_id=pid,origin=origin,selection=reason,status='not eligible under unchanged contract',annual=a.filter((pl.col('player_id')==pid)&pl.col('season').is_between(origin-2,origin)).to_dicts()))
            continue
        row=chosen.row(0,named=True)
        peers=q.filter((pl.col('origin_year')==origin)&(pl.col('level')==row['level'])&(pl.col('player_id')!=pid))
        age=row['age'] if row['age'] is not None else 25
        peers=peers.with_columns(((pl.col('age').fill_null(25)-age).abs()/5+(pl.col('log_gb')-row['log_gb']).abs()).alias('origin_distance')).sort('origin_distance','player_id').head(3)
        sensitivities={}
        for target in ['delivered','quality']:
            meta=fits[origin,pid%5,target,'complete']
            model=joblib.load(meta['path'])
            x=chosen.select(meta['features']).to_numpy()
            altered=x.copy()
            for pos in POSITIONS:
                altered[0,meta['features'].index(f'complete_{pos}')]=0
            sensitivities[target]=dict(full=float(model.predict(x)[0]),same_fit_zero_signal=float(model.predict(altered)[0]),signal_contribution=float(model.predict(x)[0]-model.predict(altered)[0]),scope='fixed-parameter mechanics, not a causal or replacement forecast')
        cases.append(dict(player_id=pid,origin=origin,selection=reason,status='walked',inputs_and_forecasts=row,
            source_annual=a.filter((pl.col('player_id')==pid)&pl.col('season').is_between(origin-2,origin)).sort('season','position','league_id').to_dicts(),
            origin_known_peers=peers.to_dicts(),peer_selection='same origin/level; closest abs(age difference)/5 + abs(log exposure difference), ID ties; no outcome filter',
            fixed_parameter_sensitivity=sensitivities))
    diagnostics=[]
    for level in sorted(recent['level'].unique()):
        z=recent.filter(pl.col('level')==level)
        known=z.filter(pl.col('quality').is_not_null())
        diagnostics.append(dict(level=level,starting=z.height,substantial_future_MLB_infield=known.height,
            conditional_no_profile=int((known['quality_support']==0).sum()), conditional_under20_profile=int((known['quality_support']<20).sum()),
            delivered_no_profile=int((z['delivered_support']==0).sum()),delivered_under20_profile=int((z['delivered_support']<20).sum())))
    result={'player_walkthrough_status':'pending_human_review','cases':cases,'fit_replays':replay,
        'annual_pooling_verified':True,'scores_independently_recomputed':True,'profile_by_level':diagnostics,
        'production_changed':False,'hashes':{str(OUT/'fit-report.json'):sha256_file(OUT/'fit-report.json'),str(Path(__file__).resolve()):sha256_file(Path(__file__).resolve())}}
    save(OUT/'player-traces.json',result); save(PUBLIC/'player-traces.json',result)
    print(json.dumps({'profile':diagnostics,'cases':[dict(player_id=c['player_id'],origin=c['origin'],reason=c['selection'],status=c['status'],name=c.get('inputs_and_forecasts',{}).get('player_name'),level=c.get('inputs_and_forecasts',{}).get('level'),prior=c.get('inputs_and_forecasts',{}).get('prior_mlb_defense'),GB=c.get('inputs_and_forecasts',{}).get('weighted_gb'),rate_SS=c.get('inputs_and_forecasts',{}).get('complete_6'),pred=c.get('inputs_and_forecasts',{}).get('delivered_complete'),base=c.get('inputs_and_forecasts',{}).get('delivered_benchmark'),actual=c.get('inputs_and_forecasts',{}).get('delivered'),quality=c.get('inputs_and_forecasts',{}).get('quality'),quality_pred=c.get('inputs_and_forecasts',{}).get('quality_complete'),signal=c.get('fixed_parameter_sensitivity',{}).get('quality')) for c in cases]},indent=2))


if __name__=='__main__':
    main()
