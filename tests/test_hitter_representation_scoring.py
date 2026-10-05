import importlib.util
from pathlib import Path
import sys
import numpy as np
import polars as pl

path=Path(__file__).resolve().parents[1]/'scripts/review_hitter_evidence_representation.py'
sys.path.insert(0,str(path.parent))
spec=importlib.util.spec_from_file_location('representation_review',path)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def test_equal_origins_and_actual_PA_rate_weighting():
    f=pl.DataFrame({'origin_year':[2016,2016,2017], 'next_pa':[10,90,100],
                    'a_rate':[0.,2.,1.],'actual_relative_rate':[0.,0.,0.]})
    assert np.isclose(m.rate_score(f,'a_rate','actual_relative_rate',True),np.sqrt((3.6+1)/2))


def test_cluster_rate_interval_point_matches_declared_score():
    f=pl.DataFrame({'origin_year':[2016,2016,2017], 'player_id':[1,2,1], 'next_pa':[10,90,100],
                    'a_rate':[0.,2.,1.],'b_rate':[1.,1.,1.],'actual_relative_rate':[0.,0.,0.]})
    note=m.rate_interval(f,'a','b')
    assert np.isclose(note['change'],1.3)
    assert note['lower']<=note['change']<=note['upper']
