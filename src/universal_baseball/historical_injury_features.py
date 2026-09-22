"""Chronology-safe offseason injury-history features from MLB transactions."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, timedelta
import json
from pathlib import Path
import re

import polars as pl


_LIST_PATTERN = re.compile(
    r"(?:(?P<days>7|10|15|60)-day|(?P<covid>covid-19)) "
    r"(?P<label>injured|disabled) list",
    re.IGNORECASE,
)
FEATURE_COLUMNS = (
    "injury__placements_365",
    "injury__placements_730",
    "injury__days_365",
    "injury__days_730",
    "injury__long_placements_730",
    "injury__covid_placements_730",
    "injury__activations_365",
    "injury__on_list_at_cutoff",
    "injury__current_spell_days",
)


def parse_injury_event(description: object) -> tuple[str, int, int] | None:
    """Return event kind, nominal list days, and COVID flag when recognized."""

    text = str(description or "").strip().lower()
    match = _LIST_PATTERN.search(text)
    if match is None:
        return None
    list_days = int(match.group("days")) if match.group("days") else 0
    covid = int(match.group("covid") is not None)
    padded = f" {text} "
    if " placed " in padded and " on the " in text:
        return "placement", list_days, covid
    if (
        (" activated " in padded or " reinstated " in padded)
        and " from the " in text
    ):
        return "activation", list_days, covid
    if " transferred " in padded and " to the " in text:
        return "transfer", list_days, covid
    return None


def load_injury_events(paths: Iterable[Path]) -> pl.DataFrame:
    """Load and normalize dated injury events from saved StatsAPI captures."""

    rows: dict[tuple[int, int], dict[str, object]] = {}
    for path in sorted(paths):
        payload = json.loads(path.read_text(encoding="utf-8"))
        transactions = payload.get("transactions")
        if not isinstance(transactions, list):
            raise ValueError(f"transaction capture has no transaction list: {path}")
        for raw in transactions:
            if not isinstance(raw, dict):
                continue
            parsed = parse_injury_event(raw.get("description"))
            person = raw.get("person") or {}
            if parsed is None or raw.get("id") is None or person.get("id") is None:
                continue
            transaction_text = str(raw.get("date") or "")[:10]
            effective_text = str(raw.get("effectiveDate") or transaction_text)[:10]
            if not transaction_text:
                continue
            if effective_text[:4] != transaction_text[:4]:
                effective_text = transaction_text
            try:
                event_date = date.fromisoformat(effective_text)
            except ValueError:
                continue
            kind, list_days, covid = parsed
            row = {
                "transaction_id": int(raw["id"]),
                "player_id": int(person["id"]),
                "event_date": event_date,
                "event_kind": kind,
                "list_days": list_days,
                "covid_list": covid,
                "source_path": path.as_posix(),
            }
            key = (int(raw["id"]), int(person["id"]))
            previous = rows.get(key)
            if previous is None or event_date >= previous["event_date"]:
                rows[key] = row
    schema = {
        "transaction_id": pl.Int64,
        "player_id": pl.Int64,
        "event_date": pl.Date,
        "event_kind": pl.String,
        "list_days": pl.Int64,
        "covid_list": pl.Int8,
        "source_path": pl.String,
    }
    return (
        pl.DataFrame(list(rows.values()), schema=schema)
        if rows
        else pl.DataFrame(schema=schema)
    ).sort(["player_id", "event_date", "transaction_id"])


def _overlap_days(
    start: date,
    end: date,
    window_start: date,
    window_end: date,
) -> int:
    left = max(start, window_start)
    right = min(end, window_end)
    return max(0, (right - left).days + 1)


def _player_features(
    rows: list[dict[str, object]], *, cutoff: date
) -> dict[str, int]:
    eligible = [row for row in rows if row["event_date"] <= cutoff]
    intervals: list[tuple[date, date]] = []
    open_start: date | None = None
    open_year: int | None = None
    placements: list[dict[str, object]] = []
    activations: list[date] = []
    for row in eligible:
        event_date = row["event_date"]
        assert isinstance(event_date, date)
        if open_start is not None and open_year != event_date.year:
            intervals.append((open_start, date(open_year, 12, 31)))
            open_start = None
            open_year = None
        kind = str(row["event_kind"])
        if kind == "placement":
            placements.append(row)
            if open_start is None:
                open_start = event_date
                open_year = event_date.year
        elif kind == "activation":
            activations.append(event_date)
            if open_start is not None:
                intervals.append((open_start, event_date))
                open_start = None
                open_year = None
    on_list = int(open_start is not None and open_year == cutoff.year)
    current_spell_days = (
        (cutoff - open_start).days + 1 if on_list and open_start is not None else 0
    )
    if open_start is not None:
        intervals.append((open_start, cutoff))

    start_365 = cutoff - timedelta(days=364)
    start_730 = cutoff - timedelta(days=729)
    return {
        "injury__placements_365": sum(
            start_365 <= row["event_date"] <= cutoff for row in placements
        ),
        "injury__placements_730": sum(
            start_730 <= row["event_date"] <= cutoff for row in placements
        ),
        "injury__days_365": sum(
            _overlap_days(start, end, start_365, cutoff) for start, end in intervals
        ),
        "injury__days_730": sum(
            _overlap_days(start, end, start_730, cutoff) for start, end in intervals
        ),
        "injury__long_placements_730": sum(
            start_730 <= row["event_date"] <= cutoff
            and int(row["list_days"]) == 60
            for row in placements
        ),
        "injury__covid_placements_730": sum(
            start_730 <= row["event_date"] <= cutoff
            and int(row["covid_list"]) == 1
            for row in placements
        ),
        "injury__activations_365": sum(
            start_365 <= event_date <= cutoff for event_date in activations
        ),
        "injury__on_list_at_cutoff": on_list,
        "injury__current_spell_days": current_spell_days,
    }


def build_historical_injury_features(
    events: pl.DataFrame,
    *,
    origin_years: Iterable[int],
    cutoff_month: int = 10,
    cutoff_day: int = 15,
) -> pl.DataFrame:
    """Build player-origin features using events known by each cutoff."""

    required = {
        "transaction_id",
        "player_id",
        "event_date",
        "event_kind",
        "list_days",
        "covid_list",
    }
    missing = sorted(required - set(events.columns))
    if missing:
        raise ValueError(f"injury event frame missing {missing}")
    player_rows = {
        int(part.item(0, "player_id")): part.to_dicts()
        for part in events.partition_by("player_id", maintain_order=True)
    }
    output: list[dict[str, object]] = []
    for origin_year in sorted(set(int(year) for year in origin_years)):
        cutoff = date(origin_year, cutoff_month, cutoff_day)
        for player_id, rows in player_rows.items():
            if rows[0]["event_date"] > cutoff:
                continue
            output.append(
                {
                    "origin_year": origin_year,
                    "player_id": player_id,
                    **_player_features(rows, cutoff=cutoff),
                }
            )
    schema = {
        "origin_year": pl.Int64,
        "player_id": pl.Int64,
        **{column: pl.Int64 for column in FEATURE_COLUMNS},
    }
    return (
        pl.DataFrame(output, schema=schema)
        if output
        else pl.DataFrame(schema=schema)
    ).sort(["origin_year", "player_id"])
