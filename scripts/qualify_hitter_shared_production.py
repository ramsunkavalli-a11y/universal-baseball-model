"""Qualify partial event signs and sparse foreign peers, without another fit."""
from pathlib import Path
import numpy as np
import polars as pl
from universal_baseball.hitter_shared_production import FEATURES
from universal_baseball.hitter_compatible_value import UNIT
from universal_baseball.mlb_event_logit import VALUES
from universal_baseball.storage import sha256_file
from run_hitter_shared_production import OUT,read,save,verify


def main():
    receipt=read(OUT/'review-receipt.json');verify(receipt['hashes'])
    pre=read(OUT/'preflight.json');walks=read(OUT/'player-walks.json')['cases'];frames={k:pl.read_parquet(OUT/f'features-{k}.parquet') for k in range(5)}
    rows=[]
    for c in walks:
        o=c['forecast'];y,k=o['origin_year'],o['outer_fold'];f=frames[k];a=f.filter(pl.col('row_id')==o['row_id']).row(0,named=True)
        cell=next(t for t in pre['cells'] if t['year']==y and t['fold']==k);tr=f.filter(pl.col('row_id').is_in(cell['training_row_ids']))
        p=np.array(c['source']['reference'])+.1*np.array([a[n] for n in FEATURES[:8]])
        strict=tr.filter((pl.col('prior_debut')==a['prior_debut'])&(pl.col('stage')==a['stage'])&
            ((pl.col('shared_foreign_share')>0)==(a['shared_foreign_share']>0))).with_columns(
            ((pl.col('age')-a['age']).abs()/5+(pl.col('pa_0')-a['pa_0']).abs()/600+
             (pl.col('draft_rank')-a['draft_rank']).abs()+(pl.col('scout_rank_score_0')-a['scout_rank_score_0']).abs()).alias('distance'))
        peers=strict.sort('distance','player_id','origin_year').unique('player_id',maintain_order=True).head(3)
        peers=peers.with_columns(pl.when(pl.col('next_pa')>0).then(pl.col('actual_relative_rate')).otherwise(None).alias('observed_rate'))
        rows.append(dict(row_id=o['row_id'],player_name=o['player_name'],origin_year=y,
            constructed_historical_event_value=float((p-np.array(c['source']['reference']))@VALUES*UNIT),
            constructed_value_is_not_future_projection=True,
            fitted_event_terms=float(sum(t['effect'] for t in c['linear_trace']['feature_effects'] if t['feature'].startswith('shared_event_'))),
            strict_foreign_route_people=strict['player_id'].n_unique(),
            strict_comparisons=peers.select('player_id','player_name','origin_year','age','pa_0','minor_pa_0','shared_foreign_share','distance','next_pa','observed_rate').to_dicts()))
    save('review-qualification.json',dict(cases=rows,new_fits=0,
        interpretation='Event coefficients are partial effects after retained MLB quality/tracking. They are not full transferable production slopes. An out-to-K exchange holds hits fixed and changes implied BABIP, so the 95 K warnings are not a demonstrated physical violation. All HR exchanges are positive.',
        peer_interpretation='Original broad comparisons remain; additional matching on origin-known foreign production prevents presenting US no-MLB peers as foreign-professional analogues. Sparse exact age/exposure support still controls claims.',
        proposed_next_question='A shared production baseline with consistent quality representation, rather than applying MLB residual relationships as the full foreign/minor talent relationship. This remains a hypothesis, not a proven repair.',
        hashes={str(p):sha256_file(p) for p in [Path(__file__),OUT/'review-receipt.json',OUT/'player-walks.json',OUT/'event-directions.json']}))
    print('Partial-sign interpretation and stricter origin-known comparison peers recorded; no forecasts changed.')


if __name__=='__main__':main()
