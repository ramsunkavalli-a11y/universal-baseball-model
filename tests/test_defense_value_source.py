import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from verify_defense_value_v11 import weighted_history


@pytest.mark.parametrize('channel,prior,unit', [
    ('range_6', 3000, 1500), ('framing', 6000, 1000),
    ('throwing', 100, 100), ('blocking', 3000, 1000),
    ('arm', 300, 100), ('receiving', 600, 100)])
def test_no_history_is_unknown_not_observed_average(channel, prior, unit):
    h = weighted_history(channel, [], 2022)
    assert h['rate'] == 0 and h['measured'] is False
    assert h['prior'] == prior and h['unit'] == unit


def test_direct_shrinkage_and_calendar_cutoff():
    rows = [dict(season=2022, position=6, range_valid=True, native_outs=10, range_runs=2),
            dict(season=2021, position=6, range_valid=True, native_outs=20, range_runs=-2),
            dict(season=2023, position=6, range_valid=True, native_outs=1000, range_runs=100),
            dict(season=2022, position=5, range_valid=True, native_outs=1000, range_runs=100)]
    h = weighted_history('range_6', rows, 2022)
    assert h['opportunities'] == 20 and h['runs'] == 1
    assert h['rate'] == pytest.approx(1500/3020)
    assert len(h['eligible_sources']) == 2


def test_mixed_position_arm_count_not_imported_as_OF_skill():
    rows = [dict(season=2022, kind='arm', isolated_outfield_quality_valid=False,
                 opportunities=100, runs=10)]
    h = weighted_history('arm', rows, 2022)
    assert not h['measured'] and h['rate'] == 0
