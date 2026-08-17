"""Thin request semantics for tracked Minor League Baseball Savant detail data.

This module performs no network I/O. It freezes the small request surface needed
by the first richer Current Talent challenger and provides deterministic request
chunk planning for the later provenance-aware materializer. Actual capture stays
inside explicit manual workflows so raw response bytes and source metadata remain
auditable.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from urllib.parse import urlencode


SAVANT_MINORS_CSV_ROOT = "https://baseballsavant.mlb.com/statcast-search-minors/csv"
DEFAULT_TRACKED_MINOR_CHUNK_DAYS = 7


@dataclass(frozen=True, slots=True)
class TrackedMinorSavantRequest:
    """One inclusive date chunk for a tracked-only Minor Savant capture."""

    start_date: date
    end_date: date
    request_url: str
    raw_filename: str


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


def plan_tracked_minor_savant_requests(
    start_date: date,
    end_date: date,
    *,
    chunk_days: int = DEFAULT_TRACKED_MINOR_CHUNK_DAYS,
) -> tuple[TrackedMinorSavantRequest, ...]:
    """Plan contiguous non-overlapping inclusive source chunks without I/O.

    The materializer intentionally uses small fixed date chunks rather than one
    season-scale request. That keeps exact raw responses bounded and makes source
    drift/failure attributable to a narrow date range. The request helper already
    supports same-day inclusive probes, so adjacent chunks advance by one calendar
    day and never overlap.
    """

    if end_date < start_date:
        raise ValueError("Minor Savant end_date must be on or after start_date")
    if chunk_days < 1:
        raise ValueError("Minor Savant chunk_days must be at least one")

    requests: list[TrackedMinorSavantRequest] = []
    cursor = start_date
    while cursor <= end_date:
        chunk_end = min(cursor + timedelta(days=chunk_days - 1), end_date)
        requests.append(
            TrackedMinorSavantRequest(
                start_date=cursor,
                end_date=chunk_end,
                request_url=build_tracked_minor_savant_url(cursor, chunk_end),
                raw_filename=(
                    "savant-minors-tracked-"
                    f"{cursor.isoformat()}_{chunk_end.isoformat()}.csv"
                ),
            )
        )
        cursor = chunk_end + timedelta(days=1)
    return tuple(requests)
