"""Phase 2 Model FV benchmarks and external validation evidence."""

from __future__ import annotations

from html.parser import HTMLParser
from math import floor
import re
import unicodedata

import polars as pl


FANGRAPHS_2026_PROSPECT_VALUE_URL = (
    "https://blogs.fangraphs.com/introducing-an-updated-method-for-prospect-valuation/"
)
FANGRAPHS_2026_TOP100_URL = (
    "https://blogs.fangraphs.com/2026-pre-trade-deadline-top-100-prospects-update/"
)
FANGRAPHS_2026_PROSPECT_VALUE_ID = "fangraphs_clemens_2026_prospect_surplus_by_fv"

# Published 2026 expected team-control results. Values already include players who
# never reach MLB, so they must not be probability-discounted a second time.
PROSPECT_VALUE_REFERENCE: dict[tuple[str, str], tuple[float, float, float]] = {
    ("70", "hitter"): (195_000_000.0, 27.5, 0.875),
    ("70", "pitcher"): (195_000_000.0, 27.0, 0.875),
    ("65", "hitter"): (95_000_000.0, 13.5, 0.400),
    ("65", "pitcher"): (95_000_000.0, 13.5, 0.400),
    ("60", "hitter"): (82_000_000.0, 12.5, 0.330),
    ("60", "pitcher"): (70_000_000.0, 11.0, 0.210),
    ("55", "hitter"): (55_000_000.0, 8.0, 0.175),
    ("55", "pitcher"): (45_000_000.0, 7.0, 0.070),
    ("50", "hitter"): (45_000_000.0, 7.0, 0.135),
    ("50", "pitcher"): (33_500_000.0, 5.0, 0.070),
    ("45+", "hitter"): (18_500_000.0, 3.2, 0.060),
    ("45+", "pitcher"): (15_000_000.0, 2.6, 0.030),
    ("45", "hitter"): (14_500_000.0, 2.5, 0.035),
    ("45", "pitcher"): (9_500_000.0, 1.6, 0.015),
    ("40+", "hitter"): (8_000_000.0, 1.2, 0.018),
    ("40+", "pitcher"): (7_000_000.0, 1.0, 0.010),
    ("40", "hitter"): (5_500_000.0, 0.75, 0.008),
    ("40", "pitcher"): (4_000_000.0, 0.55, 0.004),
    ("35+", "hitter"): (2_000_000.0, 0.3, 0.004),
    ("35+", "pitcher"): (1_500_000.0, 0.25, 0.004),
}


def numeric_fv(label: str) -> float:
    return float(label.removesuffix("+")) + (2.5 if label.endswith("+") else 0.0)


def _linear_interpolate(x: float, anchors: list[tuple[float, float]]) -> float:
    if x <= anchors[0][0]:
        return anchors[0][1] * max(x, 0.0) / anchors[0][0]
    if x >= anchors[-1][0]:
        return anchors[-1][1]
    for (x0, y0), (x1, y1) in zip(anchors, anchors[1:], strict=True):
        if x <= x1:
            share = (x - x0) / (x1 - x0)
            return y0 + share * (y1 - y0)
    raise AssertionError("unreachable interpolation interval")


def model_fv_from_expected_war(expected_six_year_war: float, player_type: str) -> float:
    """Infer granular internal FV from our expected outcome, never a player grade."""

    anchors = sorted(
        (war, numeric_fv(label))
        for (label, kind), (_, war, _) in PROSPECT_VALUE_REFERENCE.items()
        if kind == player_type
    )
    return min(80.0, max(20.0, _linear_interpolate(expected_six_year_war, anchors)))


def display_fv(granular_fv: float) -> int:
    """Return the nearest conventional five-point grade (half rounds upward)."""

    return int(5 * floor((granular_fv + 2.5) / 5))


def benchmark_value_from_model_fv(granular_fv: float, player_type: str) -> float:
    """Interpolate the current FV-to-dollar benchmark with our granular score."""

    anchors = sorted(
        (numeric_fv(label), value)
        for (label, kind), (value, _, _) in PROSPECT_VALUE_REFERENCE.items()
        if kind == player_type
    )
    return _linear_interpolate(granular_fv, anchors)

ORG_ID_BY_ABBREVIATION = {
    "LAA": 108, "ARI": 109, "BAL": 110, "BOS": 111, "CHC": 112,
    "CIN": 113, "CLE": 114, "COL": 115, "DET": 116, "HOU": 117,
    "KCR": 118, "LAD": 119, "WSN": 120, "NYM": 121, "ATH": 133,
    "OAK": 133, "PIT": 134, "SDP": 135, "SEA": 136, "SFG": 137,
    "STL": 138, "TBR": 139, "TEX": 140, "TOR": 141, "MIN": 142,
    "PHI": 143, "ATL": 144, "CHW": 145, "MIA": 146, "NYY": 147,
    "MIL": 158,
}

PROSPECT_RANKING_SCHEMA = {
    "rank": pl.Int64,
    "player_name": pl.String,
    "position": pl.String,
    "organization_abbreviation": pl.String,
    "organization_id": pl.Int64,
    "age": pl.Float64,
    "future_value": pl.String,
    "eta_year": pl.Int64,
    "fangraphs_player_url": pl.String,
    "prospect_type": pl.String,
    "expected_surplus_value_dollars": pl.Float64,
    "expected_controlled_war": pl.Float64,
    "star_probability": pl.Float64,
    "valuation_source_id": pl.String,
}


class _TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tables: list[list[list[tuple[str, str]]]] = []
        self._table: list[list[tuple[str, str]]] | None = None
        self._row: list[tuple[str, str]] | None = None
        self._cell_text: list[str] | None = None
        self._cell_href = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self._table = []
        elif tag == "tr" and self._table is not None:
            self._row = []
        elif tag in {"td", "th"} and self._row is not None:
            self._cell_text = []
            self._cell_href = ""
        elif tag == "a" and self._cell_text is not None:
            self._cell_href = dict(attrs).get("href") or ""

    def handle_data(self, data: str) -> None:
        if self._cell_text is not None:
            self._cell_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self._cell_text is not None and self._row is not None:
            text = re.sub(r"\s+", " ", "".join(self._cell_text)).strip()
            self._row.append((text, self._cell_href))
            self._cell_text = None
        elif tag == "tr" and self._row is not None and self._table is not None:
            if self._row:
                self._table.append(self._row)
            self._row = None
        elif tag == "table" and self._table is not None:
            if self._table:
                self.tables.append(self._table)
            self._table = None


def _prospect_type(position: str) -> str:
    return "pitcher" if position.upper() in {"P", "SP", "RP", "RHP", "LHP"} else "hitter"


def parse_fangraphs_top100_html(raw_html: str) -> pl.DataFrame:
    """Parse the public ranked table while ignoring unrelated article tables."""
    parser = _TableParser()
    parser.feed(raw_html)
    candidate_tables: list[list[dict[str, object]]] = []
    for table in parser.tables:
        rows: list[dict[str, object]] = []
        for cells in table:
            values = [cell[0] for cell in cells]
            if len(values) < 8 or not values[0].isdigit():
                continue
            rank = int(values[0])
            fv = values[5].replace(" FV", "").strip()
            if not 1 <= rank <= 100 or (fv, _prospect_type(values[2])) not in PROSPECT_VALUE_REFERENCE:
                continue
            if not values[7].isdigit():
                continue
            organization = values[3].upper()
            if organization not in ORG_ID_BY_ABBREVIATION:
                raise ValueError(f"unknown FanGraphs prospect organization: {organization}")
            prospect_type = _prospect_type(values[2])
            value, war, star = PROSPECT_VALUE_REFERENCE[(fv, prospect_type)]
            rows.append(
                {
                    "rank": rank,
                    "player_name": values[1],
                    "position": values[2],
                    "organization_abbreviation": organization,
                    "organization_id": ORG_ID_BY_ABBREVIATION[organization],
                    "age": float(values[4]),
                    "future_value": fv,
                    "eta_year": int(values[7]),
                    "fangraphs_player_url": cells[1][1],
                    "prospect_type": prospect_type,
                    "expected_surplus_value_dollars": value,
                    "expected_controlled_war": war,
                    "star_probability": star,
                    "valuation_source_id": FANGRAPHS_2026_PROSPECT_VALUE_ID,
                }
            )
        if len(rows) == 100 and {int(row["rank"]) for row in rows} == set(range(1, 101)):
            candidate_tables.append(rows)
    if len(candidate_tables) != 1:
        raise ValueError(
            f"expected one complete FanGraphs Top 100 table, found {len(candidate_tables)}"
        )
    result = pl.DataFrame(candidate_tables[0], schema=PROSPECT_RANKING_SCHEMA)
    return result.sort("rank")


def normalized_person_name(value: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", ascii_name.lower()).split())


def attach_mlbam_ids(rankings: pl.DataFrame, players: pl.DataFrame) -> pl.DataFrame:
    """Use exact normalized name plus current organization; ambiguous rows fail."""
    required = {"player_id", "player_name", "organization_id"}
    if missing := sorted(required - set(players.columns)):
        raise ValueError(f"prospect identity players missing fields: {missing}")
    lookup: dict[tuple[str, int], list[int]] = {}
    for row in players.select(*sorted(required)).iter_rows(named=True):
        if row["organization_id"] is None:
            continue
        key = (normalized_person_name(str(row["player_name"])), int(row["organization_id"]))
        lookup.setdefault(key, []).append(int(row["player_id"]))
    ids: list[int | None] = []
    statuses: list[str] = []
    for row in rankings.iter_rows(named=True):
        key = (normalized_person_name(str(row["player_name"])), int(row["organization_id"]))
        matches = sorted(set(lookup.get(key, [])))
        ids.append(matches[0] if len(matches) == 1 else None)
        statuses.append(
            "exact_name_and_organization"
            if len(matches) == 1
            else "ambiguous_name_and_organization"
            if matches
            else "unmatched"
        )
    return rankings.with_columns(
        pl.Series("player_id", ids, dtype=pl.Int64),
        pl.Series("identity_status", statuses, dtype=pl.String),
    )
