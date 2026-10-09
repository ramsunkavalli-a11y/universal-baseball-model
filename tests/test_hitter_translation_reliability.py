import numpy as np
import polars as pl
import pytest
from universal_baseball.hitter_talent_bridge import PROFILE_FEATURES
from universal_baseball.hitter_translation_reliability import reliable_translation


def frame(n):
    return pl.DataFrame({'translation_supported_pa':[float(n)],'translated_reliability':[n/(n+1200)],
        **{c:[1. if i==0 else -1/7] for i,c in enumerate(PROFILE_FEATURES[:8])},'unrelated':[42.]})


@pytest.mark.parametrize('n',[0,26,600,6000])
def test_event_signal_scales_without_changing_other_inputs(n):
    f=frame(n);r=reliable_translation(f)
    assert r[PROFILE_FEATURES[0]][0]==pytest.approx(n/(n+1200))
    assert r['unrelated'].equals(f['unrelated'])
    assert abs(r.select(PROFILE_FEATURES[:8]).to_numpy().sum())<1e-12


def test_bad_reliability_rejected():
    with pytest.raises(ValueError):
        reliable_translation(frame(26).with_columns(pl.lit(1.).alias('translated_reliability')))
