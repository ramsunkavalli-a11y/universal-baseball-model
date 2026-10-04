from datetime import date
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import audit_hitter_older_origins as audit
from review_hitter_older_origins import birth_age


def test_protected_and_unplanned_seasons_cannot_be_captured():
    for year in [2003,2005,2008,2025,2026]:
        with pytest.raises(AssertionError): audit.capture(year)


def test_age_at_season_cutoff_not_current_age():
    assert birth_age(date(1992,10,16),2010)==17
    assert birth_age(date(1992,6,30),2010)==18
    assert birth_age(date(1992,7,1),2010)==17
