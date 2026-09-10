from datetime import date

import pytest

from scripts.materialize_career_debut_dates import project_debut_people


def test_project_debut_people_preserves_missing_and_exact_dates() -> None:
    result = project_debut_people(
        {
            "people": [
                {"id": 2, "mlbDebutDate": None},
                {"id": 1, "mlbDebutDate": "2012-04-05"},
            ]
        }
    )
    assert result["player_id"].to_list() == [1, 2]
    assert result.item(0, "mlb_debut_date") == date(2012, 4, 5)
    assert result.item(1, "mlb_debut_date") is None
    with pytest.raises(ValueError, match="people list"):
        project_debut_people({})
