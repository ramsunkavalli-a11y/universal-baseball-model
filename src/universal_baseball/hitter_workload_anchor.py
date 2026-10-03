"""Observed workload is a reference, not guaranteed future playing time."""
import numpy as np


def reference(pa, season_games):
    pa=np.asarray(pa,dtype=float)
    games=np.asarray(season_games,dtype=float)
    if pa.shape!=games.shape or pa.ndim!=2 or pa.shape[1]!=3:
        raise ValueError('Three paired history years required')
    if not np.isfinite(pa).all()or not np.isfinite(games).all()or (pa<0).any()or (games<=0).any():
        raise ValueError('Unknown or invalid workload history')
    annual=np.minimum(800,pa*162/games)
    return np.maximum(100,annual.max(axis=1)),annual


def forecast(raw,hard):
    raw=np.asarray(raw,dtype=float)
    if not np.isfinite(raw).all():raise ValueError('Nonfinite workload')
    p=np.clip(raw,0,800)
    p[np.asarray(hard,dtype=bool)]=0
    return p
