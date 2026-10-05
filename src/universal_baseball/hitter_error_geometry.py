"""Exact delivered-value error decomposition without nonexistent hitting labels."""
import numpy as np


def decompose(expected_pa, actual_pa, rate, actual_rate, replacement):
    pa,n,r,a,rep=[np.asarray(x,float) for x in [expected_pa,actual_pa,rate,actual_rate,replacement]]
    if not (pa.shape==n.shape==r.shape==a.shape==rep.shape) or pa.ndim!=1:
        raise ValueError('Paired one-dimensional forecast rows required')
    active=n>0
    if (n<0).any() or (pa<0).any() or not all(np.isfinite(x).all() for x in [pa,n,r,rep]) or not np.isfinite(a[active]).all():
        raise ValueError('Invalid forecasts or observed active hitting')
    t=np.full(len(pa),np.nan);o=t.copy()
    t[active]=pa[active]*(r[active]-a[active])/600
    o[active]=(pa[active]-n[active])*(a[active]/600+rep[active])
    actual=np.zeros(len(pa));actual[active]=n[active]*(a[active]/600+rep[active])
    error=pa*(r/600+rep)-actual
    assert np.allclose(t[active]+o[active],error[active],atol=1e-10)
    return dict(active=active,hitting=t,opportunity=o,error=error)


def change(expected_pa, actual_pa, old_rate, new_rate, actual_rate, replacement):
    old=decompose(expected_pa,actual_pa,old_rate,actual_rate,replacement)
    new=decompose(expected_pa,actual_pa,new_rate,actual_rate,replacement)
    active=old['active'];talent=np.zeros(len(active));interaction=talent.copy();absent=talent.copy()
    talent[active]=new['hitting'][active]**2-old['hitting'][active]**2
    interaction[active]=2*old['opportunity'][active]*(new['hitting'][active]-old['hitting'][active])
    absent[~active]=new['error'][~active]**2-old['error'][~active]**2
    delta=new['error']**2-old['error']**2
    if not np.allclose(talent+interaction+absent,delta,atol=1e-10):
        raise ValueError('Error-change identity failed')
    return dict(delta=delta,active_hitting_squared=talent,active_interaction=interaction,nonarrival=absent,
        old_hitting_error=old['hitting'],new_hitting_error=new['hitting'],opportunity_error=old['opportunity'])
