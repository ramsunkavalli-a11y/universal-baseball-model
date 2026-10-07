import importlib.util
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from resume_minor_range_correction_v21 import normalized_audit
from universal_baseball.minor_range_correction import audit


def row(pid,year=2015,end=2018):
    return dict(player_id=pid,origin_year=year,position=6,window_end=end,quality_rate=1.)


def test_json_containers_preserve_identity_and_support():
    result=normalized_audit(audit,[row(1),row(2,2016)],[row(5,2022,2025)],2022,[0])
    assert result['training_keys']==[[2015,1,6],[2016,2,6]]
    assert result['people']==2 and not result['fit_supported']


@pytest.mark.parametrize('train,test',[
    ([row(5)],[row(10)]),
    ([row(1,end=2023)],[row(5)]),
    ([row(1),row(1)],[row(5)]),
    ([row(1)],[row(1,2022,2025)]),
])
def test_normalization_does_not_bypass_validation(train,test):
    with pytest.raises(ValueError):normalized_audit(audit,train,test,2022,[0])
