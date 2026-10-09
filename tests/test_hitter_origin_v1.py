from datetime import date
import polars as pl
import pytest
from test_hitter_forecast_base_tested import sources
from test_hitter_forecast_inputs import fixtures
from test_hitter_forecast_tracking import raw
from universal_baseball.hitter_forecast_base_tested import tested_base_inputs as old_base
from universal_baseball.hitter_forecast_inputs import pooled_inputs as old_pooled
from universal_baseball.hitter_forecast_tracking import materialize_tracking as old_tracking
from universal_baseball.hitter_origin_base_v1 import base_inputs
from universal_baseball.hitter_origin_inputs_v1 import pooled_inputs
from universal_baseball.hitter_origin_tracking_v1 import project_measurements,materialize_tracking
from universal_baseball.hitter_statcast_history import annual_launch_features


def test_old_base_is_identical_and_career_correction_stays():
    assert base_inputs(*sources(),source_cutoff=2025).equals(old_base(*sources(),source_cutoff=2025))


def test_2026_source_predicts_2027_and_uses_all_mlb_stints():
    args=list(sources())
    for i,f in enumerate(args):
        if 'season' in f.columns:args[i]=f.with_columns(pl.col('season')+1)
        elif 'origin_year' in f.columns:args[i]=f.with_columns(pl.col('origin_year')+1)
        else:args[i]=f.with_columns(pl.col('mlb_debut_date').dt.offset_by('1y'))
    r=base_inputs(*args,source_cutoff=2026).row(0,named=True)
    assert r['target_year']==2027 and r['career_mlb_observed_pa']==300
    assert r['pa_0']==100 and r['minor_pa_0']==200 and r['elapsed']==2
    with pytest.raises(ValueError):base_inputs(*args,source_cutoff=2025)


def test_pooled_input_extension_keeps_old_arithmetic():
    f,c,d=fixtures()
    assert pooled_inputs(f,c,d,source_cutoff=2025).equals(old_pooled(f,c,d,source_cutoff=2025))
    f=f.with_columns(pl.lit(2026).alias('origin_year'));c=c.with_columns(pl.lit(2026).alias('season'))
    r=pooled_inputs(f,c,d,source_cutoff=2026).row(0,named=True)
    assert r['pooled_MLB_pa']==100 and r['draft_elapsed']==.1
    with pytest.raises(ValueError):pooled_inputs(f,c,d,source_cutoff=2025)


def test_tracking_extension_preserves_definitions_and_missingness():
    q,_=project_measurements(raw(2025),2025,source_cutoff=2025);a=annual_launch_features(q)
    f=pl.DataFrame(dict(row_id=[1,2],origin_year=[2025,2025],player_id=[2,99]))
    assert materialize_tracking(f,a,source_cutoff=2025)[0].equals(old_tracking(f,a,source_cutoff=2025)[0])
    q,ex=project_measurements(raw(2026),2026,source_cutoff=2026);a=annual_launch_features(q)
    f=f.with_columns(pl.lit(2026).alias('origin_year'))
    out,_,_=materialize_tracking(f,a,source_cutoff=2026)
    assert len(q)==2 and len(ex)==2 and out['sc_0_ev_n'].to_list()==[2,0]
    with pytest.raises(ValueError):project_measurements(raw(2027),2027,source_cutoff=2026)
    with pytest.raises(ValueError):materialize_tracking(f,pl.concat([a,a]),source_cutoff=2026)


def test_canceled_origin_and_future_debut_still_rejected():
    args=list(sources());args[0]=args[0].with_columns(pl.lit(2020).alias('origin_year'))
    with pytest.raises(ValueError,match='Canceled-origin'):base_inputs(*args,source_cutoff=2026)
    args=list(sources());args[4]=args[4].with_columns(pl.lit(date(2027,4,1)).alias('mlb_debut_date'))
    with pytest.raises(ValueError,match='Future'):base_inputs(*args,source_cutoff=2026)


def test_translation_extension_preserves_graph_and_blocks_future_inputs():
    from test_hitter_forecast_translation import sources as translation_sources
    from universal_baseball.hitter_forecast_translation import translation_inputs as old_translation
    from universal_baseball.hitter_origin_translation_v1 import translation_inputs
    c,f,k=translation_sources()
    old,old_notes=old_translation(c,f,held_fold=k,source_cutoff=2025)
    new,notes=translation_inputs(c,f,held_fold=k,source_cutoff=2025)
    assert old.equals(new) and old_notes==notes
    c=c.with_columns(pl.col('season')+1);f=f.with_columns(pl.col('origin_year')+1)
    new,notes=translation_inputs(c,f,held_fold=k,source_cutoff=2026)
    assert new['translation_supported_pa'].to_list()==old['translation_supported_pa'].to_list()
    assert notes[-1]['max_source_year']==2026
    with pytest.raises(ValueError):translation_inputs(c,f,held_fold=k,source_cutoff=2025)
    with pytest.raises(ValueError):translation_inputs(c,f,held_fold=k,source_cutoff=2027)
