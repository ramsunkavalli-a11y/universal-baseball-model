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

COTS_VALUATION_TERM_SCHEMA: dict[str, pl.DataType] = {
    "source_record_id": pl.String,
    "player_id": pl.Int64,
    "payroll_year": pl.Int64,
    "source_value": pl.String,
    "source_amount_dollars": pl.Int64,
    "accepted_salary_dollars": pl.Int64,
    "contract_status": pl.String,
    "valuation_treatment": pl.String,
    "evidence_status": pl.String,
    "review_reason": pl.String,
    "source_snapshot_id": pl.String,
}


CONTRACT_RANGE_PATTERN = re.compile(
    r"\b\d+\s*(?:y|yr|yrs|year|years)\s*/?\s*\$[^()]+"
    r"\(\s*(?P<start>\d{2}|20\d{2})\s*"
    r"(?:-\s*(?P<end>\d{2}|20\d{2}))?\s*\)",
    re.IGNORECASE,
)
OPTION_RANGE_PATTERN = re.compile(
    r"\+?\s*(?P<start>\d{2}|20\d{2})\s*"
    r"(?:-\s*(?P<end>\d{2}|20\d{2}))?\s*"
    r"(?:(?P<kind>cl|club|pl|player|m|mutual|v|vesting|cond|conditional)\.?\s*)?"
    r"(?:opt|opts|option|options)\b",
    re.IGNORECASE,
)
OPTION_LIST_PATTERN = re.compile(
    r"\+?\s*(?P<first>\d{2}|20\d{2})\s*,\s*"
    r"(?P<second>\d{2}|20\d{2})\s*(?:opt|opts|option|options)\b",
    re.IGNORECASE,
)


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


def _full_contract_year(value: str, *, reference_year: int) -> int:
    year = int(value)
    return year if year >= 2000 else (reference_year // 100) * 100 + year


def _year_ranges(pattern: re.Pattern[str], text: str, *, reference_year: int) -> set[int]:
    years: set[int] = set()
    for match in pattern.finditer(text):
        start = _full_contract_year(match.group("start"), reference_year=reference_year)
        end_text = match.group("end")
        end = (
            start
            if end_text is None
            else _full_contract_year(end_text, reference_year=start)
        )
        if end < start or end - start > 20:
            continue
        years.update(range(start, end + 1))
    return years


def _option_years(text: str, *, reference_year: int) -> set[int]:
    years = _year_ranges(OPTION_RANGE_PATTERN, text, reference_year=reference_year)
    for match in OPTION_LIST_PATTERN.finditer(text):
        years.add(
            _full_contract_year(match.group("first"), reference_year=reference_year)
        )
        years.add(
            _full_contract_year(match.group("second"), reference_year=reference_year)
        )
    return years


def build_cots_valuation_terms(
    players: pl.DataFrame,
    terms: pl.DataFrame,
    identities: pl.DataFrame,
) -> pl.DataFrame:
    """Classify Cot's annual cells without treating every payroll amount as salary."""

    player_required = set(COTS_PLAYER_SCHEMA)
    term_required = set(COTS_YEAR_TERM_SCHEMA)
    identity_required = set(COTS_IDENTITY_SCHEMA)
    if missing := sorted(player_required - set(players.columns)):
        raise ValueError(f"Cot's players missing valuation fields: {missing}")
    if missing := sorted(term_required - set(terms.columns)):
        raise ValueError(f"Cot's terms missing valuation fields: {missing}")
    if missing := sorted(identity_required - set(identities.columns)):
        raise ValueError(f"Cot's identities missing valuation fields: {missing}")
    if players.group_by("source_record_id").len().filter(pl.col("len") != 1).height:
        raise ValueError("Cot's players violate source-record grain")
    if identities.group_by("source_record_id").len().filter(pl.col("len") != 1).height:
        raise ValueError("Cot's identities violate source-record grain")
    if terms.group_by("source_record_id", "payroll_year").len().filter(
        pl.col("len") != 1
    ).height:
        raise ValueError("Cot's terms violate source-record-year grain")

    joined = terms.join(
        players.select(
            "source_record_id", "season", "contract_text", "source_snapshot_id"
        ),
        on="source_record_id",
        how="inner",
        validate="m:1",
    ).join(
        identities.select("source_record_id", "player_id", "match_status"),
        on="source_record_id",
        how="inner",
        validate="m:1",
    )
    if joined.height != terms.height:
        raise ValueError("Cot's valuation inputs do not cover every annual term")

    output: list[dict[str, object]] = []
    for row in joined.iter_rows(named=True):
        payroll_year = int(row["payroll_year"])
        contract_text = str(row["contract_text"])
        guaranteed_years = _year_ranges(
            CONTRACT_RANGE_PATTERN, contract_text, reference_year=int(row["season"])
        )
        option_years = _option_years(contract_text, reference_year=int(row["season"]))
        amount = row["amount_dollars"]
        control_state = str(row["control_state"])
        term_status = str(row["term_status"])
        match_status = str(row["match_status"])

        accepted_amount = None
        review_reason = ""
        if match_status != "accepted_team_name_exact_service":
            contract_status = "identity_unresolved"
            treatment = "review_not_valuation_ready"
            evidence = "blocked_identity_gate"
            review_reason = match_status
        elif control_state in {"a1", "a2", "a3", "a4"}:
            contract_status = "arbitration_eligible"
            treatment = "calculate_arbitration_from_cba_path"
            evidence = f"explicit_{control_state}"
        elif control_state == "free_agent":
            contract_status = "free_agent"
            treatment = "end_incumbent_control"
            evidence = "explicit_free_agent"
        elif control_state == "option" or payroll_year in option_years:
            contract_status = "option_unresolved"
            treatment = "review_not_valuation_ready"
            evidence = "explicit_option_year"
            review_reason = "option_salary_and_buyout_not_separately_proven"
        elif amount is not None and payroll_year in guaranteed_years:
            contract_status = "guaranteed_contract"
            treatment = "use_known_guaranteed_salary"
            evidence = "amount_within_explicit_guaranteed_range"
            accepted_amount = int(amount)
        elif amount is not None:
            contract_status = "contract_amount_unresolved"
            treatment = "review_not_valuation_ready"
            evidence = "numeric_amount_without_guaranteed_year_evidence"
            review_reason = "contract_text_does_not_prove_guaranteed_year"
        elif term_status == "missing":
            contract_status = "not_stated"
            treatment = "defer_to_cba_control_path"
            evidence = "blank_source_cell"
        else:
            contract_status = "unparsed"
            treatment = "review_not_valuation_ready"
            evidence = "unparsed_source_cell"
            review_reason = "annual_source_value_unparsed"

        output.append(
            {
                "source_record_id": row["source_record_id"],
                "player_id": row["player_id"],
                "payroll_year": payroll_year,
                "source_value": row["source_value"],
                "source_amount_dollars": amount,
                "accepted_salary_dollars": accepted_amount,
                "contract_status": contract_status,
                "valuation_treatment": treatment,
                "evidence_status": evidence,
                "review_reason": review_reason,
                "source_snapshot_id": row["source_snapshot_id"],
            }
        )
    return pl.DataFrame(output, schema=COTS_VALUATION_TERM_SCHEMA).sort(
        ["source_record_id", "payroll_year"]
    )


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
