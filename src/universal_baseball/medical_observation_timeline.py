"""Replay observed roster interruption, without inventing clinical recovery."""

from collections import defaultdict
from copy import deepcopy
from datetime import date

from .availability_context_v29 import as_of

BOUNDARIES = {
    "scope_exit",
    "retired",
    "deceased",
    "restricted",
    "administrative_leave",
    "ineligible_unspecified",
    "suspended_unspecified",
    "permanent_ineligible",
    "finite_ineligible",
    "foreign_departure",
}


def day(value):
    return value if isinstance(value, date) else date.fromisoformat(value)


def union_days(intervals, start, end):
    """Half-open calendar intervals; end is exclusive and overlaps count once."""
    parts = sorted((max(day(a), start), min(day(b), end)) for a, b in intervals)
    total, latest = 0, start
    for a, b in parts:
        a = max(a, latest)
        if b > a:
            total += (b - a).days
            latest = b
    return total


def rebuild(
    player_id,
    records,
    appearances,
    windows,
    cutoff,
    origin,
    covered_years=range(2015, 2025),
):
    cutoff = day(cutoff)
    if cutoff.year != origin + 1:
        raise ValueError("Wrong information year")
    if any(r["player_id"] != player_id for r in records):
        raise ValueError("Medical identity mismatch")
    eligible = as_of(records, cutoff)
    events = defaultdict(lambda: dict(records=[], use=[]))
    for r in eligible:
        if r["event_date"] > cutoff:
            raise ValueError("Future effective event")
        events[r["event_date"]]["records"].append(r)
    for r in appearances:
        if r["player_id"] != player_id:
            raise ValueError("Appearance identity mismatch")
        occurred, known = (
            day(r["game_date"]),
            day(r.get("available_date", r["game_date"])),
        )
        if known < occurred:
            raise ValueError("Appearance known before play")
        if known <= cutoff and occurred <= cutoff:
            events[occurred]["use"].append(
                dict(
                    kind="dated_MLB_contact",
                    start=occurred,
                    end=occurred,
                    game_pk=r["game_pk"],
                )
            )
    for r in windows:
        if r["player_id"] != player_id:
            raise ValueError("Window identity mismatch")
        start, end = day(r["start"]), day(r["end"])
        known = day(r.get("available_date", r["end"]))
        if start > end or known < end or r["pa"] < 0 or int(r["pa"]) != r["pa"]:
            raise ValueError("Invalid positive window")
        if known <= cutoff and end <= cutoff and r["pa"] > 0:
            events[end]["use"].append(
                dict(
                    kind="positive_MLB_PA_window",
                    start=start,
                    end=end,
                    pa=r["pa"],
                    source_path=r["source_path"],
                )
            )
    spells, returns, current = [], [], None
    state, last_entry, last_boundary = "no_captured_medical_entry", None, None
    ambiguous = []

    def close(when, kind, evidence=None):
        nonlocal current
        current["observation_end_upper"] = when
        current["closure_kind"] = kind
        current["return_evidence"] = evidence
        current = None

    for occurred, group in sorted(events.items()):
        rs = group["records"]
        entries = [r for r in rs if r.get("il_kind") in {"placement", "transfer"}]
        acts = [
            r
            for r in rs
            if r.get("il_kind") in {"activation", "unqualified_activation"}
            or r["kind"] == "mlb_return"
        ]
        boundaries = [r for r in rs if r["kind"] in BOUNDARIES]
        if entries and (acts or boundaries):
            ambiguous.append(occurred)
        if acts and current is not None:
            explicit = any(r.get("il_kind") == "activation" for r in acts)
            kind = "reported_IL_activation" if explicit else "unqualified_roster_return"
            close(
                occurred,
                kind,
                dict(transaction_ids=[r["transaction_id"] for r in acts]),
            )
            state = kind
        for r in entries:
            if current is None:
                current = dict(
                    start=occurred,
                    observation_end_upper=cutoff,
                    closure_kind="pending_at_cutoff",
                    categories=[],
                    surgery=False,
                    transaction_ids=[],
                    placement_reports=0,
                    placement_report_dates=[],
                    surgery_report_dates=[],
                    entry_is_transfer=r["il_kind"] == "transfer",
                    return_evidence=None,
                )
                spells.append(current)
            current["transaction_ids"].append(r["transaction_id"])
            current["placement_reports"] += r["il_kind"] == "placement"
            if r["il_kind"] == "placement":
                current["placement_report_dates"].append(occurred)
            if r["surgery"]:
                current["surgery_report_dates"].append(occurred)
            if r["category"] not in current["categories"]:
                current["categories"].append(r["category"])
            current["surgery"] |= r["surgery"]
            last_entry = occurred
            state = "captured_IL_unresolved"
        if boundaries and last_entry is not None:
            last_boundary = occurred
            if current is not None:
                close(
                    occurred,
                    "medical_followup_censored",
                    dict(transaction_ids=[r["transaction_id"] for r in boundaries]),
                )
                state = "medical_followup_censored"
        for use in sorted(
            group["use"], key=lambda u: (u["kind"] != "dated_MLB_contact", u["start"])
        ):
            if last_entry is None or use["start"] <= last_entry:
                continue  # Same-day play can precede the injury; period totals can straddle it.
            if last_boundary is not None and use["start"] <= last_boundary:
                continue  # A straddling window cannot certify participation after scope exit.
            if current is not None and use["start"] <= current["start"]:
                continue
            if current is not None:
                close(occurred, "observed_MLB_use", deepcopy(use))
            if state != "observed_MLB_use":
                returns.append(deepcopy(use))
            state = "observed_MLB_use"
    recent_start = date(origin - 1, 1, 1)
    recent_end = date(origin + 1, 1, 1)
    recent = [s for s in spells if s["observation_end_upper"] >= recent_start]
    intervals = [(s["start"], s["observation_end_upper"]) for s in recent]
    censored = [s for s in recent if s["closure_kind"] == "medical_followup_censored"]
    complete = {origin - 1, origin} <= set(covered_years)
    return dict(
        player_id=player_id,
        origin_year=origin,
        information_date=cutoff,
        observation_state=state,
        recent_history_coverage_complete=complete,
        missing_recent_source_years=sorted({origin - 1, origin} - set(covered_years)),
        recent_episode_count=len(recent) if complete else None,
        recent_placement_reports=sum(
            recent_start <= d < recent_end
            for s in recent
            for d in s["placement_report_dates"]
        )
        if complete
        else None,
        recent_surgery_report_count=sum(
            recent_start <= d < recent_end
            for s in recent
            for d in s["surgery_report_dates"]
        )
        if complete
        else None,
        recent_followup_calendar_upper_days=union_days(
            intervals, recent_start, recent_end
        )
        if complete
        else None,
        recent_censored_followup_upper_days=union_days(
            [(s["start"], s["observation_end_upper"]) for s in censored],
            recent_start,
            recent_end,
        )
        if complete
        else None,
        pending_observation=current is not None,
        same_day_timing_ambiguous=ambiguous,
        spells=spells,
        observed_returns=returns,
        true_injury_days=None,
        medical_recovery_certified=False,
        legal_or_employment_status_changed=False,
    )
