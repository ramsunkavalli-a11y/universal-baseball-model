#!/usr/bin/env python
"""Out-of-year 2023 replication of the fixed pitch-sequence fidelity audit.

This wrapper intentionally reuses the 2024 diagnostic implementation unchanged
and swaps only the Rookie/complex and Single-A inventory assets. The older 2023
release spellings (``leauge_id``/``leauge_name``) are normalized through the
already-certified explicit schema-alias helper before the unchanged inventory
sampler runs. Diagnostic signatures, game sampling, official-feed parsing, and
report logic therefore remain identical to the original gate.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import audit_milb_bin_value_stability as stability
import audit_pitch_sequence_fidelity as audit
from universal_baseball.armstjc_schema import normalize_known_schema_aliases
from universal_baseball.certification import download_file, read_quarantined_csv


def _load_2023_inventory(asset: str, work_dir: Path, max_games: int) -> dict[str, Any]:
    path = work_dir / asset
    metadata = download_file(f"{audit.BASE_URL}/{asset}", path, timeout_seconds=240)
    frame = read_quarantined_csv(path)
    if frame.is_empty():
        raise RuntimeError(f"source inventory asset is empty: {asset}")
    frame, schema_report = normalize_known_schema_aliases(frame)
    orders = stability._inventory_orders(frame, asset, max_games=max_games)
    if not orders:
        raise RuntimeError(f"source inventory has no leagues/games: {asset}")
    return {"metadata": metadata, "orders": orders, "schema_report": schema_report}


audit.ROOKIE_ASSET = "2023_8_rk_pbp.csv"
audit.SINGLE_A_ASSET = "2023_8_a_pbp.csv"
audit._load_inventory = _load_2023_inventory


if __name__ == "__main__":
    raise SystemExit(audit.main())
