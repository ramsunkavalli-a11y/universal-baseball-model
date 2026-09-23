"""Independently check frozen artifact bytes and dated population/ledger identities."""
import json
from pathlib import Path
import numpy as np
import polars as pl
from build_historical_projection_state_v1 import hashes, YEARS, REFERENCE
from audit_player_path_population_v1 import panel_data
from audit_historical_projection_state_v1 import PACKAGE, CUTOFFS, snapshots, support, query_support
from universal_baseball.historical_projection_state import validate_states, residual_ledger, mature_vectors, KEYS
from universal_baseball.storage import sha256_file


def main():
    meta=json.loads((PACKAGE/'manifest.json').read_text())
    for n,sha in meta['files'].items():assert sha256_file(PACKAGE/n)==sha,n
    for p,sha in meta['audit_code'].items():assert sha256_file(Path(p))==sha,p
    pre=json.loads((PACKAGE/'prefit-manifest.json').read_text());assert pre['hashes']==hashes()
    build=json.loads((PACKAGE/'build-manifest.json').read_text())
    assert build['prefit_sha256']==sha256_file(PACKAGE/'prefit-manifest.json')
    for n,sha in build['files'].items():assert sha256_file(PACKAGE/n)==sha,n
    states=pl.read_parquet(PACKAGE/'states.parquet');validate_states(states)
    ledger=pl.read_parquet(PACKAGE/'residual-ledger.parquet');panel=panel_data()
    assert residual_ledger(states,panel).equals(ledger)
    expected=panel.filter(pl.col('origin_year').is_in(YEARS)).select('origin_year','player_id')
    assert expected.height*3==states.height
    for h in (1,2,3):
        assert states.filter(pl.col('horizon')==h).select('origin_year','player_id').sort('origin_year','player_id').equals(expected.sort('origin_year','player_id'))
    ref=pl.read_parquet(REFERENCE).filter(~pl.col('cold')&(pl.col('horizon')<=3)&pl.col('origin_year').is_in(YEARS)).sort(KEYS)
    reused=states.filter(pl.col('origin_year')>=2016).sort(KEYS)
    assert ref.select(KEYS).equals(reused.select(KEYS))
    for old,new in [('C2_p','delivered_p'),('C2_pa','delivered_pa'),('C2_value','delivered_value'),('rate','research_conditional_rate')]:
        np.testing.assert_array_equal(ref[old],reused[new])
    future=ledger.filter(pl.col('outcome_year')>2025)
    assert future.height>0
    for c in ('actual_value','actual_pa','observed_active_rate','value_residual','pa_residual'):
        assert future[c].null_count()==future.height,c
    assert ledger.filter(pl.col('actual_pa')==0)['observed_active_rate'].drop_nulls().is_empty()
    queries=pl.read_parquet(PACKAGE/'query-support.parquet')
    audit=json.loads((PACKAGE/'support-audit.json').read_text())
    for cutoff in CUTOFFS:
        f=snapshots(ledger,cutoff)
        if f.height:
            assert f['origin_year'].max()+3<=cutoff
            assert not f.filter((pl.col('origin_year')<2020)&(pl.col('origin_year')+3>=2020)).height
            np.testing.assert_allclose(f.group_by('player_id').agg(pl.col('identity_weight').sum())['identity_weight'],1)
        saved=next(r for r in audit['support'] if r['cutoff']==cutoff)['rebuilt']
        for k,v in support(f).items():np.testing.assert_allclose(saved[k],v,rtol=1e-12,atol=1e-10)
        q=panel.filter(pl.col('origin_year')==cutoff)
        calculated=query_support(f,q,cutoff).sort('player_id')
        archived=queries.filter(pl.col('cutoff')==cutoff).sort('player_id')
        assert calculated.drop('effective_players').equals(archived.drop('effective_players'))
        np.testing.assert_allclose(calculated['effective_players'],archived['effective_players'],rtol=1e-12,atol=1e-10)
        # Independently enumerate a few query pools, rather than only recomputing summary algebra.
        for row in calculated.head(12).to_dicts():
            g=f.filter((pl.col('stage')==row['stage'])&(pl.col('age_band')==row['age_band'])&(pl.col('player_id')!=row['player_id']))
            s=support(g)
            assert (s['snapshots'],s['players'])==(row['snapshots'],row['players'])
            np.testing.assert_allclose(s['effective_players'],row['effective_players'],atol=1e-8)
        if q.height:
            pid=q['player_id'][0]
            assert pid not in set(mature_vectors(ledger,cutoff,[pid])['player_id'])
    assert json.loads((PACKAGE/'overlap-checks.json').read_text())['passed']
    mutation=json.loads((PACKAGE/'future-mutation-check.json').read_text())
    assert mutation['passed'] and max(mutation['maximum_differences'].values())==0
    print(json.dumps({'verified':True,'forecast_rows':states.height,'reconstructed_rows':build['backfilled_rows'],
        'query_support_rows':queries.height,'production_forecasts_changed':False,'protected_outcomes_used':False}))


if __name__=='__main__':main()
