"""Conservative observation warnings, never legal reinstatement or new forecasts."""


def old_restriction_with_later_mlb_use(row, absence):
    active = absence.get('active_restrictions', {})
    if absence.get('hard_unavailable') or any(
            r['kind'] in {'deceased', 'permanent_ineligible'} for r in active.values()):
        return False
    if not active or row['pa_0'] <= 0:
        return False
    # Annual PA can establish chronology only when the event precedes that year.
    return max(r['event_date'] for r in active.values()) < f"{row['origin_year']}-01-01"
