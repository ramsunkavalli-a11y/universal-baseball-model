from __future__ import annotations

from pathlib import Path

import pytest

from scripts.materialize_career_mlb_outcome_inventory import materialize_inventory


def test_inventory_rejects_protected_or_incomplete_outcome_year(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="authorized completed outcome boundary"):
        materialize_inventory(
            start_season=2025,
            end_season=2026,
            output_dir=tmp_path,
        )


def test_inventory_rejects_reversed_years_before_source_access(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="cannot exceed"):
        materialize_inventory(
            start_season=2024,
            end_season=2023,
            output_dir=tmp_path,
        )
