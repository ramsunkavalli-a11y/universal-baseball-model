from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_historical_materialization_authorization_remains_source_only() -> None:
    payload = json.loads(
        (
            ROOT
            / "docs"
            / "hitter-v2-historical-materialization-authorization.json"
        ).read_text(encoding="utf-8")
    )
    assert payload["parent_commit"] == "fd73ee9667185e7db6ce79062989e1568e627ee6"
    assert "fitting or scoring any candidate" in payload["not_authorized"]
    assert "using historical artifacts as model predictors" in payload["not_authorized"]
    assert "opening or using protected 2026 outcome or participant data" in payload["not_authorized"]


def test_historical_materialization_execution_contract_keeps_lanes_separate() -> None:
    text = (
        ROOT
        / "docs"
        / "hitter-v2-historical-materialization-execution-contract.md"
    ).read_text(encoding="utf-8")
    assert "## 2019 MiLB execution" in text
    assert "## 2020 MLB execution" in text
    assert "absence of 2020 MiLB remains an observation gap" in text
    assert "One lane cannot certify" in text
    assert "Historical model use requires a new" in text
