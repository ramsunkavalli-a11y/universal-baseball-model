"""Common event units with a single schedule normalization of replacement."""
import numpy as np
from universal_baseball.mlb_event_logit import VALUES,NEUTRAL_WOBA_SCALE

UNIT=600/(10*NEUTRAL_WOBA_SCALE)


def replacement(league_pa,fraction):
    pa=np.asarray(league_pa,dtype=float);f=np.asarray(fraction,dtype=float)
    if not np.isfinite(pa).all()or not np.isfinite(f).all()or(pa<=0).any()or(f<=0).any():
        raise ValueError('Unknown or invalid completed origin-season exposure')
    return 570*f/pa


def labels(counts,origin,target,rep):
    counts=np.asarray(counts,dtype=float);origin=np.asarray(origin,dtype=float);target=np.asarray(target,dtype=float)
    rep=np.asarray(rep,dtype=float)
    if counts.ndim!=2 or counts.shape[1]!=8 or counts.shape!=origin.shape or counts.shape!=target.shape:
        raise ValueError('Paired eight-event vectors required')
    if not np.isfinite(counts).all()or(counts<0).any():raise ValueError('Invalid actual events')
    for env in [origin,target]:
        if not np.isfinite(env).all()or(env<0).any()or not np.allclose(env.sum(1),1):raise ValueError('Invalid environment')
    if rep.shape!=(len(counts),)or not np.isfinite(rep).all()or(rep<=0).any():raise ValueError('Invalid replacement reference')
    pa=counts.sum(1);active=pa>0
    index=np.divide(counts@VALUES,pa,out=np.zeros(len(counts)),where=active)
    common=np.where(active,(index-origin@VALUES)*UNIT,0.)
    relative=np.where(active,(index-target@VALUES)*UNIT,0.)
    return dict(pa=pa,actual_index=index,common_rate=common,relative_rate=relative,
        common_value=pa*(common/600+rep),relative_value=pa*(relative/600+rep))


def envelope(pa,origin_index,rep):
    pa=np.asarray(pa,dtype=float)
    return pa*((VALUES.min()-origin_index)*UNIT/600+rep),pa*((VALUES.max()-origin_index)*UNIT/600+rep)
