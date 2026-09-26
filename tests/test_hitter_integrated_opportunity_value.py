import numpy as np
import polars as pl
import pytest

from universal_baseball.hitter_integrated_opportunity_value import (
    ARMS, KEY, assemble, cumulative, profiles)
from universal_baseball.multiyear_hitter_components import COMPONENTS


def fixture():
    x=pl.DataFrame({'origin_year':[2021]*3,'player_id':[1,2,3],'horizon':[1]*3,
        'player_name':['Prospect','Veteran','Unknown'],'age':[22.,33.,25.],
        'stage':['Upper minors','Current MLB','Inactive'],'prospect':[True,False,False],
        'prior_debut':[False,True,False],'minor_returner':[False]*3,'recent_debut':[False]*3,
        'mlb_pa_lag0':[0,500,0],'mlb_pa_lag1':[0,500,0],'mlb_pa_lag2':[0,500,0],
        'pa_lag0':[500,500,0],'old_pa':[.001,400.,1.],'old_value':[0.,2.,0.],
        'B_pa':[.01,350.,1.],'B_p':[.001,.8,.01],'B_value':[0.,2.,0.],
        'E_pa':[20.,500.,5.],'E_p':[.1,.95,.02],'E_value':[.1,3.,0.],
        'D_pa':[50.,350.,1.],'fixed_p':[.3,.8,.01],'rate':[1.,3.,0.]})
    parts=[]
    for i,c in enumerate(COMPONENTS):
        mode=('direct','benchmark','neutral')[i%3]
        base=x.select(*KEY,pl.col('old_pa').alias('expected_pa'),pl.col('old_value').alias('batting'))
        base=base.with_columns(pl.lit(c).alias('component'),pl.lit(mode).alias('selected_model'),
            pl.lit(2.).alias('benchmark_rate'),pl.lit(.2).alias('direct'),
            (2*pl.col('expected_pa')/600).alias('benchmark'))
        base=base.with_columns(pl.col(mode).alias('selected') if mode!='neutral' else pl.lit(0.).alias('selected'))
        parts.append(base)
    return x,pl.concat(parts)


def test_fixed_routing():
    x,c=fixture();f,_=assemble(x,c)
    np.testing.assert_array_equal(f['H_pa'],[50,500,1])
    np.testing.assert_array_equal(f['H_p'],[.3,.95,.01])
    assert f['route'].to_list()==['prospect_F_D','prior_MLB_E','remaining_B']


def test_direct_total_never_scaled_by_tiny_denominator():
    x,c=fixture();f,components=assemble(x,c)
    direct=components.filter(pl.col('selected_model')=='direct')
    for a in ARMS:np.testing.assert_array_equal(direct[a+'_runs'],direct['direct'])
    assert f['H_other_runs'][0]<2


def test_only_rate_heads_change_exposure():
    x,c=fixture();f,components=assemble(x,c)
    rate=components.filter(pl.col('selected_model')=='benchmark')
    np.testing.assert_allclose(rate['H_runs'],rate['benchmark_rate']*rate['H_pa']/600)
    neutral=components.filter(pl.col('selected_model')=='neutral')
    assert (neutral['H_runs']==0).all()
    np.testing.assert_allclose(f['H_value'],f['B_value']+(f['H_pa']-f['B_pa'])*f['rate']/600)


def test_assembly_ignores_outcomes():
    x,c=fixture();a,ac=assemble(x,c)
    b,bc=assemble(x.with_columns(pl.lit(1e10).alias('actual_pa')),
                   c.with_columns(pl.lit(-1e10).alias('actual')))
    assert a.equals(b) and ac.equals(bc)


@pytest.mark.parametrize('bad',['duplicate','missing','unknown','replay','nan','protected','overlap'])
def test_rejects_invalid_inputs(bad):
    x,c=fixture()
    if bad=='duplicate':x=pl.concat([x,x.head(1)])
    if bad=='missing':c=c.slice(1)
    if bad=='unknown':c=c.with_columns(pl.lit('invented').alias('selected_model'))
    if bad=='replay':c=c.with_columns(pl.lit(123.).alias('selected'))
    if bad=='nan':x=x.with_columns(pl.lit(float('nan')).alias('E_pa'))
    if bad=='protected':x=x.with_columns(pl.lit(2025).alias('origin_year'))
    if bad=='overlap':x=x.with_columns(pl.lit(True).alias('prior_debut'))
    with pytest.raises((ValueError,AssertionError)):assemble(x,c)


def test_cumulative_requires_all_horizons_and_preserves_missing():
    x,c=fixture();f,_=assemble(x,c)
    f=f.with_columns(pl.lit(10.).alias('actual_pa'),pl.lit(1.).alias('actual_value'),
        pl.lit(True).alias('complete_components'),pl.lit(1.).alias('actual_expanded'))
    assert cumulative(f).is_empty()
    f=pl.concat([f.with_columns(pl.lit(h).alias('horizon')) for h in (1,2,3)])
    f=f.with_columns((pl.col('horizon')!=1).alias('complete_components'),
        pl.when(pl.col('horizon')!=1).then(pl.col('actual_expanded')).otherwise(None).alias('actual_expanded'))
    out=cumulative(f)
    assert out.height==3 and out['actual_expanded'].null_count()==3
    np.testing.assert_array_equal(out['actual_pa'],[30]*3)


def test_profile_definitions_use_only_cutoff_inputs():
    x,c=fixture();f,_=assemble(x,c)
    assert f.filter(profiles()['MLB_400plus'])['player_id'].to_list()==[2]
    assert f.filter(profiles()['age_under23'])['player_id'].to_list()==[1]
    assert f.filter(profiles()['young_brief_debut']).is_empty()
