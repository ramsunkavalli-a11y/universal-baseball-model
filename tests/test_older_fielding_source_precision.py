import pytest
from universal_baseball.older_fielding_source_precision import normalized_with_precision


def row():
    return dict(Season=2009,Position='CF',xMLBAMID=429711,playerid=3255,PlayerName='Example',
        Inn=1353.1,TInn=1353.3299560546875,RngR=30.,ErrR=0.,ARM=1.,DPR=None,UZR=31.00005)


def test_legacy_precision_keeps_baseball_outs_and_original_flag():
    n=normalized_with_precision(row())
    assert n['fielding_outs']==4060 and n['decimal_innings_check']
    assert not n['original_decimal_innings_check']
    assert n['decimal_innings_gap_outs']==pytest.approx(-.0101318359375)


@pytest.mark.parametrize('change',[dict(TInn=1353.0),dict(TInn=None),dict(UZR=31.01)])
def test_material_innings_or_credit_gaps_still_fail(change):
    with pytest.raises(ValueError):normalized_with_precision(dict(row(),**change))
