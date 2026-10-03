import pytest
from universal_baseball.historical_prospect_rank import project, features

def test_protected_year_cannot_be_enabled():
    with pytest.raises(ValueError):project('',2026,allow_2025=True)
    with pytest.raises(ValueError):project('',2025)

def test_latest_list_uses_forecast_season_and_preserves_unknown_absence():
    lookup={(2024,694671):6,(2021,1):1};capacity={2024:100,2023:100,2021:99}
    f=features(694671,2024,lookup,capacity)
    assert f['scout_listed_0']==1 and f['scout_rank_score_0']==.95
    assert f['scout_listed_1']==0 and f['scout_listed_2'] is None
    g=features(2,2021,lookup,capacity)
    assert g['scout_listed_0'] is None and g['scout_list_available_0']==1
