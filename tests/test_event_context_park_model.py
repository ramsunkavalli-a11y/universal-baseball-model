from __future__ import annotations

from datetime import date, timedelta

import polars as pl

from universal_baseball.event_context_park_model import fit_event_context_park_factors


def test_event_model_emits_centered_venue_outcome_effects() -> None:
    rows = []
    start = date(2024, 4, 1)
    for index in range(240):
        venue = 1 if index % 2 == 0 else 2
        outcome = "hit" if (venue == 1 and index % 5 != 0) else "out"
        rows.append(
            {
                "game_date": start + timedelta(days=index // 8),
                "batter_id": index % 12,
                "pitcher_id": index % 10,
                "batter_side": "L" if index % 3 == 0 else "R",
                "pitcher_hand": "L" if index % 4 == 0 else "R",
                "venue_id": venue,
                "outcome": outcome,
            }
        )
    result = fit_event_context_park_factors(pl.DataFrame(rows), regularization_c=0.2)
    effects = result.factors.pivot(
        on="component", index="venue_id", values="park_clr_effect"
    )
    assert effects.filter(pl.col("venue_id") == 1).item(0, "hit") > 0
    assert effects.filter(pl.col("venue_id") == 2).item(0, "hit") < 0
    assert result.validation["validation_events"] > 0
