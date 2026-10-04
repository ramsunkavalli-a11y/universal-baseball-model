import numpy as np
import polars as pl
import pytest
from universal_baseball import hitter_repaired_contact_information as c


def source():
    rows = []
    for year, pid, league, bucket in [(2016, 1, 111, 'AA'), (2017, 1, 125, 'MEX'),
                                      (2018, 2, 130, 'DSL'), (2021, 3, 120, 'RK120')]:
        rows.append(dict(season=year, player_id=pid, league_id=league, bucket=bucket,
                         physical_contacts=12, classified_contacts=10,
                         **{k: 10 if i == 0 else 0 for i, k in enumerate(c.CELLS)}))
    return pl.DataFrame(rows)


def frame():
    return pl.DataFrame(dict(row_id=[1, 2, 3, 4], player_id=[1, 1, 2, 3],
                             origin_year=[2015, 2016, 2018, 2021]))


def test_accounting_and_zero_sum_detail():
    q = c.materialize(frame(), source())
    assert q['dc_classified_exposure'].to_list() == [0, 10, 10, 10]
    detail = q.select(c.DETAIL).to_numpy().reshape(4, 10, 9)
    assert np.allclose(detail.sum(2), 0, atol=1e-14)
    assert np.allclose(q.select(c.SHAPE).to_numpy().sum(1), 0, atol=1e-14)


def test_future_mutation_cannot_change_earlier_inputs():
    a = c.materialize(frame().head(2), source())
    b = source().with_columns(*[pl.when(pl.col('season') > 2016).then(0).otherwise(pl.col(k)).alias(k) for k in c.CELLS])
    b = b.with_columns(pl.when(pl.col('season') > 2016).then(0).otherwise(pl.col('classified_contacts')).alias('classified_contacts'))
    assert a.equals(c.materialize(frame().head(2), b))


def test_missing_is_flagged_not_hitting_measurement():
    q = c.materialize(frame(), source()).head(1)
    assert q['dc_available'][0] == 0
    assert not q.select(c.SHAPE + c.DETAIL).to_numpy().any()
    assert q['dc_source_year_available_0'][0] == 0


def test_canceled_season_is_separate():
    q = c.materialize(frame(), source()).tail(1)
    assert q['dc_canceled_1'][0] == 1 and q['dc_source_year_available_1'][0] == 0


def test_mexico_and_actual_league_preserved():
    f = pl.DataFrame(dict(row_id=[1], player_id=[1], origin_year=[2017]))
    q = c.materialize(f, source())
    assert q['dc_actual_leagues'][0] == '111,125'
    assert q['dc_log_MEX'][0] > 0 and q['dc_log_AAA'][0] == 0


@pytest.mark.parametrize('bad', ['duplicate', 'cells', 'physical', 'future', 'mexico'])
def test_bad_source_rejected(bad):
    s = source()
    if bad == 'duplicate': s = pl.concat([s, s.head(1)])
    if bad == 'cells': s = s.with_columns(pl.lit(1).alias(c.CELLS[1]))
    if bad == 'physical': s = s.with_columns(pl.lit(9).alias('physical_contacts'))
    if bad == 'future': s = s.with_columns(pl.lit(2026).alias('season'))
    if bad == 'mexico': s = s.with_columns(pl.when(pl.col('league_id') == 125).then(pl.lit('AAA')).otherwise(pl.col('bucket')).alias('bucket'))
    with pytest.raises(ValueError): c.validate(s)


def test_exact_fallback_and_primary_route():
    raw, anchor, available, debut = [3, 3, 3], [1, 2, 4], [True, False, True], [0, 0, 1]
    assert c.assembly(raw, anchor, available, prior_debut=debut, primary=True, supported=True).tolist() == [3, 2, 4]
    assert c.assembly(raw, anchor, available, prior_debut=debut, primary=False, supported=True).tolist() == [3, 2, 3]
    assert c.assembly(raw, anchor, available, prior_debut=debut, primary=False, supported=False).tolist() == anchor
