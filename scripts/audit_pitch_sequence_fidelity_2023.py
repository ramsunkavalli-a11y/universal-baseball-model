#!/usr/bin/env python
"""Out-of-year 2023 replication of the fixed pitch-sequence fidelity audit.

This wrapper intentionally reuses the 2024 diagnostic implementation unchanged
and swaps only the Rookie/complex and Single-A inventory assets. Diagnostic
signatures, game sampling, official-feed parsing, and report logic therefore
remain identical to the original gate.
"""

from __future__ import annotations

import audit_pitch_sequence_fidelity as audit


audit.ROOKIE_ASSET = "2023_8_rk_pbp.csv"
audit.SINGLE_A_ASSET = "2023_8_a_pbp.csv"


if __name__ == "__main__":
    raise SystemExit(audit.main())
