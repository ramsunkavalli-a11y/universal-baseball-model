"""Affirmative dated reports supplement existing reversible retirement state."""
from datetime import date

from .retirement_availability import state

KINDS = {"announced_retirement", "announced_medical_career_end", "announced_playing_return"}
PLAYING_RETURN_CODES = {"SFA", "PUR", "CP", "CU", "SE"}


def departure(reports, captured_events, *, player_id, cutoff):
    """No future effective event, release inference or bare rights-transfer return."""
    applicable = []
    seen = set()
    for r in reports:
        known = date.fromisoformat(r["known_date"])
        effective = date.fromisoformat(r["event_date"])
        # Date gate before using a report's semantic contents.
        if known > cutoff or effective > cutoff:
            continue
        if int(r["player_id"]) != player_id:
            continue
        if r["departure_kind"] not in KINDS or not r["source_url"].startswith("https://"):
            raise ValueError("Departure requires affirmative dated source and recognized kind")
        tid = -int(r["report_id"])
        if tid >= 0 or tid in seen:
            raise ValueError("Public report IDs must be positive and unique")
        seen.add(tid)
        applicable.append(dict(transaction_id=tid, player_id=player_id,
            known_date=known, event_date=effective,
            kind="return" if r["departure_kind"] == "announced_playing_return" else "retired",
            departure_kind=r["departure_kind"], type_code="PUBLIC_REPORT",
            source_url=r["source_url"], description=r["fact"]))
    if not applicable:
        return dict(reported_departure=False, evidence=None, return_evidence=None)
    records = applicable[:]
    for r in captured_events:
        if r["player_id"] != player_id or r["known_date"] > cutoff or r["event_date"] > cutoff:
            continue
        if r["kind"] == "return" and r.get("type_code") not in PLAYING_RETURN_CODES:
            continue
        records.append(r)
    s = state(records, cutoff)
    evidence = s["retirement"]
    return dict(reported_departure=s["reported_retired"], evidence=evidence,
                return_evidence=s["return_evidence"], qualifying_public_reports=applicable)


def forecast(old, status):
    """Leave talent and conditional workload intact; reversible departure gate."""
    result = dict(old)
    if status["reported_departure"]:
        for field in ["p", "pa", "value"]:
            result[field] = 0.0
    return result
