"""Apply existing exposure reliability to the event evidence, not just a flag."""
import numpy as np
import polars as pl

from universal_baseball.hitter_talent_bridge import PROFILE_FEATURES


def reliable_translation(frame):
    required = [*PROFILE_FEATURES[:8], 'translated_reliability', 'translation_supported_pa']
    if set(required)-set(frame.columns):
        raise ValueError('Missing translated event or reliability evidence')
    r=frame['translated_reliability'].to_numpy().astype(float)
    n=frame['translation_supported_pa'].to_numpy().astype(float)
    if not np.isfinite(frame.select(required).to_numpy().astype(float)).all() or (n<0).any() or not np.allclose(r,n/(n+1200),atol=1e-12,rtol=0):
        raise ValueError('Invalid or inconsistent fixed exposure reliability')
    return frame.with_columns((pl.col(c)*pl.col('translated_reliability')).alias(c) for c in PROFILE_FEATURES[:8])
