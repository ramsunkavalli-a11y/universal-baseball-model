"""Public FanGraphs free-agent tracker source adapter."""

from __future__ import annotations

from html.parser import HTMLParser
import math
import re

import polars as pl


FREE_AGENT_TRACKER_SCHEMA: dict[str, pl.DataType] = {
    "free_agent_year": pl.Int64,
    "source_row_sequence": pl.Int64,
    "fangraphs_id": pl.String,
    "player_name": pl.String,
    "position": pl.String,
    "previous_team": pl.String,
    "age": pl.Int64,
    "service_time": pl.String,
    "previous_war": pl.Float64,
    "projected_war": pl.Float64,
    "crowd_years": pl.Float64,
    "crowd_total_dollars": pl.Int64,
    "crowd_aav_dollars": pl.Int64,
    "signing_team": pl.String,
    "contract_years": pl.Int64,
    "contract_total_dollars": pl.Int64,
    "contract_aav_dollars": pl.Int64,
    "contract_effective_total_dollars": pl.Int64,
    "contract_value_status": pl.String,
    "contract_note_present": pl.Boolean,
    "source_url": pl.String,
    "source_snapshot_id": pl.String,
}

_PLAYER_LINK = re.compile(r"^/players/[^/]+/([^/]+)/stats/")


class _TrackerParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[dict[str, str]] = []
        self._row: dict[str, str] | None = None
        self._cell_key: str | None = None
        self._cell_text: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        attributes = dict(attrs)
        if tag == "tr":
            self._row = {}
        elif tag == "td" and self._row is not None:
            self._cell_key = attributes.get("data-col-id") or attributes.get("data-stat")
            self._cell_key = {
                "contract_years": "YearsTotal",
                "contract_total": "ContractTotal",
            }.get(self._cell_key, self._cell_key)
            self._cell_text = []
        elif tag == "a" and self._row is not None and self._cell_key == "Name":
            href = attributes.get("href") or ""
            match = _PLAYER_LINK.match(href)
            if match is not None:
                self._row["fangraphs_id"] = match.group(1)

    def handle_data(self, data: str) -> None:
        if self._cell_key is not None:
            self._cell_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "td" and self._row is not None and self._cell_key is not None:
            self._row[self._cell_key] = " ".join(
                " ".join(self._cell_text).split()
            )
            self._cell_key = None
            self._cell_text = []
        elif tag == "tr" and self._row is not None:
            if self._row.get("Name") and self._row.get("fangraphs_id"):
                self.rows.append(self._row)
            self._row = None
            self._cell_key = None
            self._cell_text = []


def _integer(value: str) -> int | None:
    cleaned = value.strip().replace(",", "")
    if not cleaned:
        return None
    try:
        numeric = int(cleaned)
    except ValueError as exc:
        raise ValueError(f"invalid integer in free-agent tracker: {value!r}") from exc
    return numeric


def _float(value: str) -> float | None:
    cleaned = value.strip()
    if not cleaned:
        return None
    try:
        numeric = float(cleaned)
    except ValueError as exc:
        raise ValueError(f"invalid number in free-agent tracker: {value!r}") from exc
    if not math.isfinite(numeric):
        raise ValueError("free-agent tracker number must be finite")
    return numeric


def _money(value: str) -> int | None:
    cleaned = value.strip().replace(",", "")
    if not cleaned or cleaned in {"MiLB", "Minors"}:
        return None
    match = re.fullmatch(r"\$([0-9]+(?:\.[0-9]+)?)([Mk])?", cleaned)
    if match is None:
        raise ValueError(f"invalid money in free-agent tracker: {value!r}")
    multiplier = {None: 1.0, "k": 1_000.0, "M": 1_000_000.0}[match.group(2)]
    return int(round(float(match.group(1)) * multiplier))


def parse_fangraphs_free_agent_tracker_html(
    html: str,
    *,
    free_agent_year: int,
    source_url: str,
    source_snapshot_id: str,
) -> pl.DataFrame:
    """Parse and exact-deduplicate the tracker tables without name matching."""

    if free_agent_year < 1976 or not source_url or not source_snapshot_id:
        raise ValueError("free-agent tracker source identity is invalid")
    parser = _TrackerParser()
    parser.feed(html)
    if not parser.rows:
        raise ValueError("free-agent tracker page contains no player rows")

    seen: set[tuple[tuple[str, str], ...]] = set()
    rows: list[dict[str, object]] = []
    for raw in parser.rows:
        identity = tuple(sorted(raw.items()))
        if identity in seen:
            continue
        seen.add(identity)
        contract_total = _money(raw.get("ContractTotal", ""))
        contract_years = _integer(raw.get("YearsTotal", ""))
        contract_aav = _money(raw.get("aav", ""))
        effective_total = (
            contract_years * contract_aav
            if contract_years is not None and contract_aav is not None
            else contract_total
        )
        signing_team = raw.get("Signing Team", "")
        raw_total = raw.get("ContractTotal", "").strip()
        if raw_total in {"MiLB", "Minors"}:
            contract_value_status = "minor_league_contract"
        elif effective_total is not None and contract_years is not None:
            contract_value_status = "reported_guaranteed_terms"
        elif signing_team:
            contract_value_status = "signed_terms_unreported"
        else:
            contract_value_status = "unsigned"
        rows.append(
            {
                "free_agent_year": int(free_agent_year),
                "source_row_sequence": len(rows) + 1,
                "fangraphs_id": raw["fangraphs_id"],
                "player_name": raw["Name"],
                "position": raw.get("position", ""),
                "previous_team": raw.get("Prev Team", ""),
                "age": _integer(raw.get("age", "")),
                "service_time": raw.get("servicetime", ""),
                "previous_war": _float(raw.get("war_prev", "")),
                "projected_war": _float(raw.get("war_proj", "")),
                "crowd_years": _float(raw.get("med_years", "")),
                "crowd_total_dollars": _money(raw.get("med_total", "")),
                "crowd_aav_dollars": _money(raw.get("med_aav", "")),
                "signing_team": signing_team,
                "contract_years": contract_years,
                "contract_total_dollars": contract_total,
                "contract_aav_dollars": contract_aav,
                "contract_effective_total_dollars": effective_total,
                "contract_value_status": contract_value_status,
                "contract_note_present": bool(raw.get("contract_link", "")),
                "source_url": source_url,
                "source_snapshot_id": source_snapshot_id,
            }
        )
    return pl.DataFrame(rows, schema=FREE_AGENT_TRACKER_SCHEMA).sort(
        "source_row_sequence"
    )
