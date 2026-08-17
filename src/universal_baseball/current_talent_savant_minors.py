"""Thin request semantics for tracked Minor League Baseball Savant detail data.

This module contains no downloader and performs no network I/O.  It freezes the
small request surface needed by the first richer Current Talent challenger while
leaving provenance-aware capture/materialization to explicit manual workflows.
"""

from __future__ import annotations

from datetime import date
from urllib.parse import urlencode


SAVANT_MINORS_CSV_ROOT = "https://baseballsavant.mlb.com/statcast-search-minors/csv"


def build_tracked_minor_savant_url(start_date: date, end_date: date) -> str:
    """Build the tracked-only batter detail request used for EV/LA evidence."""

    if end_date < start_date:
        raise ValueError("Minor Savant end_date must be on or after start_date")
    params = {
        "all": "true",
        "player_type": "batter",
        "game_date_gt": start_date.isoformat(),
        "game_date_lt": end_date.isoformat(),
        "type": "details",
        "minors": "true",
        "hfFlag": "is..tracked|",
        "chk_is..tracked": "on",
    }
    return SAVANT_MINORS_CSV_ROOT + "?" + urlencode(params)
