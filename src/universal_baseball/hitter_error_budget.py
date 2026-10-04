"""Exact retrospective error identities, not causal or selectable forecasts."""
import numpy as np


def components(p, c, y, forecast_yield, actual_yield):
    p,c,y,g,t = [np.asarray(v,dtype=float) for v in [p,c,y,forecast_yield,actual_yield]]
    assert p.shape == c.shape == y.shape == g.shape == t.shape
    assert np.isfinite(p).all() and np.isfinite(c).all() and np.isfinite(y).all() and np.isfinite(g).all()
    assert ((p>=0)&(p<=1)).all() and ((c>=1)&(c<=800)).all() and (y>=0).all()
    active = y>0
    assert np.isfinite(t[active]).all()
    # Never evaluate a hypothetical nonparticipant's observed batting talent.
    production = np.zeros(len(p)); actual_value = np.zeros(len(p))
    production[active] = y[active]*(g[active]-t[active])
    actual_value[active] = y[active]*t[active]
    arrival = (p-active)*c
    workload = active*(c-y)
    pa_parts = np.column_stack((arrival,workload))
    value_parts = np.column_stack((arrival*g,workload*g,production))
    assert np.allclose(pa_parts.sum(1),p*c-y,atol=1e-10,rtol=0)
    assert np.allclose(value_parts.sum(1),p*c*g-actual_value,atol=1e-10,rtol=0)
    return pa_parts,value_parts


def summary(parts, years, names):
    parts=np.asarray(parts,dtype=float); years=np.asarray(years)
    assert parts.shape[0]==len(years) and parts.shape[1]==len(names)
    total=parts.sum(1); matrices=[]; biases=[]; absolutes=[]; cancellation=[]; allocations=[]
    for year in np.unique(years):
        x=parts[years==year]; e=x.sum(1)
        matrices.append(x.T@x/len(x)); biases.append(x.mean(0)); absolutes.append(abs(x).mean(0))
        cancellation.append(float(np.mean(abs(x).sum(1)-abs(e))))
        allocations.append((x*np.sign(e)[:,None]).mean(0))
    matrix=np.mean(matrices,axis=0); bias=np.mean(biases,axis=0)
    mse=float(matrix.sum()); mse_alloc=matrix.sum(1); mae_alloc=np.mean(allocations,axis=0)
    # The lower-case arrays are accounting terms, not independent blame fractions.
    mse_direct=float(np.mean([np.mean(total[years==year]**2) for year in np.unique(years)]))
    mae_direct=float(np.mean([np.mean(abs(total[years==year])) for year in np.unique(years)]))
    assert np.isclose(mse,mse_direct,atol=1e-9,rtol=0)
    assert np.isclose(mae_alloc.sum(),mae_direct,atol=1e-10,rtol=0)
    return dict(mse=mse,rmse=float(np.sqrt(mse)),mae=mae_direct,bias=float(bias.sum()),
        cross_product_matrix=matrix.tolist(),mean_cancellation=float(np.mean(cancellation)),
        components={name:dict(bias=float(bias[i]),mean_absolute=float(np.mean(absolutes,axis=0)[i]),
            own_square=float(matrix[i,i]),mse_allocation=float(mse_alloc[i]),mae_allocation=float(mae_alloc[i]),
            raw_sum=float(parts[:,i].sum())) for i,name in enumerate(names)},
        limit='An exact signed-error allocation; negative terms and offsets are not causal removable error')
