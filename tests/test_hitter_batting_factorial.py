import numpy as np
import polars as pl
from universal_baseball.hitter_batting_factorial import assemble_cells, CELLS, residual_loss_identity


def test_factorial_residual_independent_of_new_workload():
    f=pl.DataFrame({'B_value':[1.],'B_pa':[300.],'E_pa':[400.],'H_pa':[0.],
        'performance_anchor':[3.],'rate':[2.],'E_other_runs':[2.],'H_other_runs':[1.]})
    z=assemble_cells(f)
    for r,rate in [('anchor',3.),('horizon',2.)]:
        for w in ('E','H'):
            assert np.isclose(z[f'{w}_{r}_marginal'].item()-z[f'{w}_{r}_product'].item(),1-300*rate/600)
    assert z['H_anchor_product'].item()==0
    assert z['H_anchor_marginal'].item()==-.5
    for name in CELLS:
        assert np.isclose((z[name+'_expanded']-z[name]).item(),.2 if name.startswith('E_') else .1)
    assert assemble_cells(f.with_columns(pl.lit(999.).alias('actual_value'))).select(CELLS).equals(z.select(CELLS))


def test_inherited_residual_can_hurt_or_help():
    assert residual_loss_identity([0],[1],[0])['mse_change']==1
    assert residual_loss_identity([0],[1],[1])['mse_change']==-1
