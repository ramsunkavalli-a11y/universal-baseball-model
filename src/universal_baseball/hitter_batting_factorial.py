"""Eight fixed accounting cells, using archived forecasts only."""
import numpy as np
import polars as pl

CELLS=tuple(f'{w}_{r}_{a}' for w in ('E','H') for r in ('anchor','horizon') for a in ('product','marginal'))


def assemble_cells(f):
    fields=['B_value','B_pa','E_pa','H_pa','performance_anchor','rate','E_other_runs','H_other_runs']
    if any(f[c].null_count() or not f[c].is_finite().all() for c in fields):
        raise ValueError('Missing/nonfinite archived inputs')
    expressions=[]
    for w in ('E','H'):
        for r,column in [('anchor','performance_anchor'),('horizon','rate')]:
            product=pl.col(w+'_pa')*pl.col(column)/600
            marginal=pl.col('B_value')+(pl.col(w+'_pa')-pl.col('B_pa'))*pl.col(column)/600
            for a,e in [('product',product),('marginal',marginal)]:
                name=f'{w}_{r}_{a}'
                expressions.extend([e.alias(name),(e+pl.col(w+'_other_runs')/10).alias(name+'_expanded')])
    return f.with_columns(expressions)


def residual_loss_identity(product,marginal,actual):
    p,m,y=[np.asarray(z,float) for z in (product,marginal,actual)]
    if p.shape!=m.shape or m.shape!=y.shape or not np.isfinite([p,m,y]).all() or not p.size:
        raise ValueError('Invalid paired error arrays')
    residual=m-p
    cross=float(np.mean(2*(p-y)*residual));square=float(np.mean(residual**2))
    change=float(np.mean((m-y)**2-(p-y)**2))
    np.testing.assert_allclose(change,cross+square,atol=1e-10)
    return {'mse_change':change,'cross_term':cross,'residual_square':square}
