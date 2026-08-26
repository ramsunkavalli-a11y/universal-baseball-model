from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_historical_milb_materializer_is_frozen_to_2019_source_only() -> None:
    text = (
        ROOT / "scripts" / "materialize_hitter_v2_historical_milb.py"
    ).read_text(encoding="utf-8")
    assert "SEASON = 2019" in text
    assert '"candidate_fit": False' in text
    assert '"candidate_scored": False' in text
    assert '"protected_2026_opened": False' in text
    assert '"model_use_authorized": False' in text
    assert "the frozen historical materialization gate authorizes 2019 only" in text
