"""Fail-closed parser and identity gate for the private 2025 Cot's extract."""

from __future__ import annotations

import csv
from io import StringIO
import re
import unicodedata

import polars as pl

from universal_baseball.team_control import SERVICE_DAYS_PER_YEAR


COTS_PLAYER_SCHEMA: dict[str, pl.DataType] = {
    "source_record_id": pl.String,
    "season": pl.Int64,
    "team_abbreviation": pl.String,
    "source_player_name": pl.String,
    "player_name": pl.String,
    "position": pl.String,
    "service_time": pl.String,
    "service_days": pl.Int64,
    "options_remaining": pl.Int64,
    "contract_text": pl.String,
    "source_snapshot_id": pl.String,
}

COTS_YEAR_TERM_SCHEMA: dict[str, pl.DataType] = {
    "source_record_id": pl.String,
    "payroll_year": pl.Int64,
    "source_value": pl.String,
    "amount_dollars": pl.Int64,
    "control_state": pl.String,
    "term_status": pl.String,
}

COTS_IDENTITY_SCHEMA: dict[str, pl.DataType] = {
    "source_record_id": pl.String,
    "player_id": pl.Int64,
    "match_status": pl.String,
    "match_method": pl.String,
    "service_day_difference": pl.Int64,
}


def normalized_person_name(value: str) -> str:
    text = value.replace("*", "").strip()
    if "," in text:
        last, first = (part.strip() for part in text.split(",", 1))
        text = f"{first} {last}"
    ascii_name = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    normalized = re.sub(r"[^a-z0-9]", "", ascii_name.lower())
    return re.sub(r"(jr|sr|ii|iii|iv)$", "", normalized)


def display_person_name(value: str) -> str:
    text = value.replace("*", "").strip()
    if "," not in text:
        return text
    last, first = (part.strip() for part in text.split(",", 1))
    return f"{first} {last}".strip()


def _options(value: str) -> int | None:
    match = re.fullmatch(r"\s*(\d+)\s*/\s*\d+\s*", value)
    return int(match.group(1)) if match else None


def _cots_service_days(value: str) -> int:
    """Restore trailing zeroes lost when Cot's service cells became CSV numbers."""

    text = value.strip()
    if "." not in text:
        if not text.isdigit():
            raise ValueError(f"invalid Cot's service time: {value}")
        return int(text) * SERVICE_DAYS_PER_YEAR
    years, remainder = text.split(".", 1)
    if not years.isdigit() or not remainder.isdigit() or len(remainder) > 3:
        raise ValueError(f"invalid Cot's service time: {value}")
    restored = int(remainder.ljust(3, "0"))
    if restored >= SERVICE_DAYS_PER_YEAR:
        raise ValueError(f"invalid Cot's service-day remainder: {value}")
    return int(years) * SERVICE_DAYS_PER_YEAR + restored


def _term(value: str) -> tuple[int | None, str, str]:
    text = value.strip()
    if not text:
        return None, "", "missing"
    compact = text.replace("$", "").replace(",", "").strip()
    try:
        amount = float(compact)
    except ValueError:
        state = text.upper()
        if re.fullmatch(r"A[1-4]", state):
            return None, state.lower(), "control_state"
        if state == "FA":
            return None, "free_agent", "control_state"
        if state == "OPT":
            return None, "option", "control_state"
        return None, "", "review_unparsed"
    if abs(amount) < 10_000 and "." in compact:
        amount *= 1_000_000
    return round(amount), "contract_amount", "available"


def parse_cots_team_csv(
    content: str,
    *,
    season: int,
    team_abbreviation: str,
    source_snapshot_id: str,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Parse player rows and long annual labor-payroll cells from one team file."""

    rows = list(csv.reader(StringIO(content)))
    header_index = next(
        (index for index, row in enumerate(rows) if len(row) > 2 and row[1].strip() == "Player"),
        None,
    )
    if header_index is None:
        raise ValueError("Cot's team file lacks Player header")
    players: list[dict[str, object]] = []
    terms: list[dict[str, object]] = []
    ordinal = 0
    for row in rows[header_index + 2 :]:
        padded = row + [""] * (24 - len(row))
        source_name = padded[1].strip()
        position = padded[2].strip()
        service = padded[7].strip()
        if not source_name or not position or not service:
            continue
        try:
            service_days = _cots_service_days(service)
        except ValueError:
            continue
        ordinal += 1
        record_id = f"{team_abbreviation}:{season}:{ordinal:03d}"
        players.append(
            {
                "source_record_id": record_id,
                "season": season,
                "team_abbreviation": team_abbreviation,
                "source_player_name": source_name,
                "player_name": display_person_name(source_name),
                "position": position,
                "service_time": service,
                "service_days": service_days,
                "options_remaining": _options(padded[8]),
                "contract_text": padded[11].strip(),
                "source_snapshot_id": source_snapshot_id,
            }
        )
        for offset, payroll_year in enumerate(range(season, season + 5)):
            source_value = padded[13 + offset].strip()
            amount, state, status = _term(source_value)
            terms.append(
                {
                    "source_record_id": record_id,
                    "payroll_year": payroll_year,
                    "source_value": source_value,
                    "amount_dollars": amount,
                    "control_state": state,
                    "term_status": status,
                }
            )
    return (
        pl.DataFrame(players, schema=COTS_PLAYER_SCHEMA),
        pl.DataFrame(terms, schema=COTS_YEAR_TERM_SCHEMA),
    )


def match_cots_players_to_opening_day(
    players: pl.DataFrame, opening_day: pl.DataFrame
) -> pl.DataFrame:
    """Attach MLBAM only through unique same-team name and exact service evidence."""

    candidates: dict[tuple[str, str], list[dict[str, object]]] = {}
    for row in opening_day.iter_rows(named=True):
        key = (str(row["team_abbreviation"]), normalized_person_name(str(row["player_name"])))
        candidates.setdefault(key, []).append(row)
    matches: list[dict[str, object]] = []
    for row in players.iter_rows(named=True):
        key = (str(row["team_abbreviation"]), normalized_person_name(str(row["player_name"])))
        name_matches = candidates.get(key, [])
        exact = [candidate for candidate in name_matches if candidate["service_days"] == row["service_days"]]
        if len(exact) == 1:
            player_id = int(exact[0]["player_id"])
            status = "accepted_team_name_exact_service"
            method = "team_normalized_name_plus_exact_service"
            difference = 0
        elif len(name_matches) == 1:
            player_id = None
            status = "review_service_disagreement"
            method = "team_normalized_name_only"
            candidate_service = name_matches[0]["service_days"]
            difference = (
                None
                if candidate_service is None
                else int(row["service_days"]) - int(candidate_service)
            )
        elif len(name_matches) > 1:
            player_id = None
            status = "review_ambiguous_team_name"
            method = "team_normalized_name_only"
            difference = None
        else:
            player_id = None
            status = "review_unmatched_team_name"
            method = "none"
            difference = None
        matches.append(
            {
                "source_record_id": row["source_record_id"],
                "player_id": player_id,
                "match_status": status,
                "match_method": method,
                "service_day_difference": difference,
            }
        )
    return pl.DataFrame(matches, schema=COTS_IDENTITY_SCHEMA).sort("source_record_id")
