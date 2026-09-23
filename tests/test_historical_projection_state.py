import numpy as np
import polars as pl
import pytest
from universal_baseball.historical_projection_state import (
    conditional_workload, validate_states, residual_ledger, mature_vectors,
)


def states(origin=2015, player=1):
    return pl.DataFrame({'origin_year':[origin]*3,'player_id':[player]*3,'horizon':[1,2,3],
        'source_cutoff':[origin]*3,'opportunity_latest_label':[origin]*3,
        'rate_latest_label':[origin]*3,'anchor_latest_label':[origin]*3,'value_latest_label':[origin]*3,
        'h1_rate_anchor':[2.]*3,'research_conditional_rate':[1.]*3,
        'delivered_value':[.1]*3,'delivered_p':[.5]*3,'delivered_pa':[100.]*3,
        'delivered_conditional_pa':[200.]*3})


def test_conditional_workload_preserves_hurdle_identity():
    np.testing.assert_allclose(conditional_workload([.5,1],[100,250]),[200,250])
    assert np.isnan(conditional_workload([0],[0])[0])


@pytest.mark.parametrize('p,pa', [([0],[1]),([-1],[0]),([1.1],[0]),([.5],[-1]),([np.nan],[0])])
def test_invalid_opportunity_rejected(p,pa):
    with pytest.raises(ValueError):conditional_workload(p,pa)


def test_complete_states_validate():
    validate_states(states())


@pytest.mark.parametrize('column,value', [('source_cutoff',2016),('rate_latest_label',2016),
    ('value_latest_label',None),('h1_rate_anchor',float('nan'))])
def test_future_or_missing_state_rejected(column,value):
    with pytest.raises(ValueError):validate_states(states().with_columns(pl.lit(value).alias(column)))


def test_duplicate_and_incomplete_vectors_rejected():
    with pytest.raises(ValueError):validate_states(pl.concat([states(),states().head(1)]))
    with pytest.raises(ValueError):validate_states(states().head(2))


def test_product_mismatch_rejected():
    with pytest.raises(AssertionError):validate_states(states().with_columns(pl.lit(1.).alias('delivered_conditional_pa')))


def test_no_play_is_not_zero_talent_and_future_not_zero_outcome():
    panel=pl.DataFrame({'origin_year':[2015],'player_id':[1],
        'war_h1':[0.],'pa_h1':[0.],'war_h2':[1.],'pa_h2':[300.],
        'war_h3':[None],'pa_h3':[None]})
    ledger=residual_ledger(states(),panel)
    assert ledger['observed_active_rate'].to_list()==[None,2.,None]
    assert ledger['value_residual'].to_list()==[-.1,.9,None]
    assert mature_vectors(ledger,2018).is_empty()


def test_whole_vector_maturity_pandemic_and_query_exclusion():
    rows=[]
    for year,player in [(2012,1),(2013,1),(2015,2),(2017,3),(2021,4)]:
        rows.append(states(year,player).with_columns(pl.lit(0.).alias('actual_value'),pl.lit(0.).alias('actual_pa')))
    ledger=pl.concat(rows)
    assert mature_vectors(ledger,2015).height==3
    assert mature_vectors(ledger,2018,excluded_ids=[1])['player_id'].unique().to_list()==[2]
    assert set(mature_vectors(ledger,2025)['player_id'])=={1,2,4}
    with pytest.raises(ValueError):mature_vectors(ledger,2026)
    with pytest.raises(ValueError):mature_vectors(pl.concat([ledger,ledger.head(1)]),2025)


def test_nonfinite_outcome_not_mature():
    ledger=states().with_columns(pl.lit(float('nan')).alias('actual_value'),pl.lit(0.).alias('actual_pa'))
    assert mature_vectors(ledger,2018).is_empty()
