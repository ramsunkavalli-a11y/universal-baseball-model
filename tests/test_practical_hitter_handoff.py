import importlib
from pathlib import Path
import polars as pl
import pytest


@pytest.fixture
def handoff(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]/'scripts'))
    return importlib.import_module('build_practical_hitter_handoff_v64')


def test_fixed_probability_edges_preserve_every_forecast(handoff):
    probabilities=[0.,.01,.05,.10,.25,.50,.75,.90,1.]
    f=pl.DataFrame(dict(player_id=list(range(9)),target_year=[2025]*9,repaired_p=probabilities,next_pa=[0,0,0,0,0,1,1,1,1]))
    result=handoff.probability(f)
    assert sum(b['rows'] for b in result['bands'])==9
    assert result['bands'][0]['rows']==1
    assert result['bands'][-1]['rows']==2
    assert result['bands'][-1]['upper_inclusive']
    assert sum(b['actual_appearances'] for b in result['bands'])==4
    assert sum(b['expected_appearances'] for b in result['bands'])==pytest.approx(sum(probabilities))


def test_probability_loss_weights_years_not_population(handoff):
    f=pl.DataFrame(dict(player_id=[1,2,3,4],target_year=[2024,2025,2025,2025],repaired_p=[.5,0.,0.,0.],next_pa=[1,0,0,0]))
    result=handoff.probability(f)
    assert result['brier']==pytest.approx(.125)
    assert result['equal_year_observed']==pytest.approx(.5)
    assert result['equal_year_predicted']==pytest.approx(.25)


def test_probability_rejects_invalid_means(handoff):
    f=pl.DataFrame(dict(player_id=[1],target_year=[2025],repaired_p=[1.1],next_pa=[1]))
    with pytest.raises(AssertionError):handoff.probability(f)
