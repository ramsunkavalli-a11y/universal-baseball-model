import numpy as np
import polars as pl
import pytest
from universal_baseball.hitter_forecast_translation import translation_inputs
from universal_baseball.hitter_talent_bridge import materialize, PROFILE_FEATURES
from universal_baseball.post_arrival_history import player_fold


def sources():
    # Explicitly find different held groups; no identity assumptions in the test.
    held=player_fold(1); reference=next(p for p in range(2,100) if player_fold(p)!=held)
    c=pl.DataFrame([dict(season=y,player_id=pid,bucket=b,plate_appearances=100,
        strike_outs=20,unintentional_walks=10,hit_by_pitch=1,babip_hits=25,
        doubles=5,triples=1,home_runs=(5 if b=='MLB' else 10))
        for y in [2024,2025] for pid in [1,reference] for b in ['MLB','AAA']])
    f=pl.DataFrame([dict(row_id=1,player_id=1,origin_year=2024),dict(row_id=2,player_id=1,origin_year=2025)])
    return c,f,held


def test_prior_origins_exact_and_new_origin_uses_current_production():
    c,f,k=sources();old=c.filter(pl.col('season')<=2024);frame=f.head(1)
    a,notes=materialize(old,frame,held_fold=k)
    b,graphs=translation_inputs(c,f,held_fold=k,source_cutoff=2025)
    assert np.allclose(a.select(PROFILE_FEATURES).to_numpy(),b.head(1).select(PROFILE_FEATURES).to_numpy(),rtol=0,atol=1e-12)
    assert notes==graphs[:-1]
    assert b['translation_total_pa'][1]==360 and b['translation_supported_pa'][1]==360
    assert all(player_fold(p)!=k for p in graphs[-1]['people']+graphs[-1]['mlb_reference_people'])


def test_held_fold_never_sets_graph_even_if_its_cross_level_performance_changes():
    c,f,k=sources();_,a=translation_inputs(c,f,held_fold=k,source_cutoff=2025)
    c=c.with_columns(pl.when(pl.col('player_id')==1).then(30).otherwise(pl.col('home_runs')).alias('home_runs'))
    _,b=translation_inputs(c,f,held_fold=k,source_cutoff=2025)
    assert a==b


def test_no_supported_production_is_missing_not_invented_own_history():
    c,f,k=sources();f=f.tail(1).with_columns(pl.lit(999).alias('player_id'))
    r,_=translation_inputs(c,f,held_fold=k,source_cutoff=2025)
    assert r['translated_missing'][0]==1 and r['translation_total_pa'][0]==0
    assert np.allclose(r.select(PROFILE_FEATURES[:8]).to_numpy(),0)


def test_future_and_duplicate_sources_rejected():
    c,f,k=sources()
    with pytest.raises(ValueError):translation_inputs(c,f,held_fold=k,source_cutoff=2024)
    with pytest.raises(ValueError):translation_inputs(pl.concat([c,c.head(1)]),f,held_fold=k,source_cutoff=2025)
    with pytest.raises(ValueError):translation_inputs(c,pl.concat([f,f.head(1)]),held_fold=k,source_cutoff=2025)
    with pytest.raises(ValueError):translation_inputs(c,f,held_fold=5,source_cutoff=2025)
