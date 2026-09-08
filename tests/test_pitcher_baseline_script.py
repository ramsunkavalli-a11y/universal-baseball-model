from __future__ import annotations

from pathlib import Path

import pytest

from scripts.score_pitcher_component_baseline import score_history


def test_pitcher_baseline_runner_rejects_protected_target_before_read(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="protected development boundary"):
        score_history(
            tmp_path / "missing.parquet",
            first_target=2024,
            last_target=2025,
            output_dir=tmp_path / "out",
        )
