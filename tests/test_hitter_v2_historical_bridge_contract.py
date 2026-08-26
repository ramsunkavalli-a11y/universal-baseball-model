from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_historical_bridge_authorization_is_descriptive_only() -> None:
    payload = json.loads(
        (
            ROOT / "docs" / "hitter-v2-historical-bridge-audit-authorization.json"
        ).read_text(encoding="utf-8")
    )
    assert payload["parent_commit"] == "2657992029bd0075e37a2817a3f82d500acd85aa"
    assert "fitting or scoring a model candidate" in payload["not_authorized"]
    assert "treating 2019-to-2021 as an adjacent-season pair" in payload["not_authorized"]
    assert "opening or using protected 2026 outcome or participant data" in payload["not_authorized"]


def test_historical_bridge_contract_keeps_gap_and_metrics_frozen() -> None:
    text = (
        ROOT / "docs" / "hitter-v2-historical-bridge-audit-contract.md"
    ).read_text(encoding="utf-8")
    assert "2019 -> 2020" in text
    assert "2020 -> 2021" in text
    assert "2019 -> 2021" in text
    assert "may never be supplied to an adjacent-season fitter" in text
    assert "no arbitrary" in text
    assert "Presence proves support, not predictive usefulness" in text
