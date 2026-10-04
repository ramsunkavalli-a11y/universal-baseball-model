"""Observed employment context, not guaranteed future jobs or current deals."""
FEATURES=['employment_capture_scope','employment_year_known','employment_year_fa']


def features(year,state,roster_conflict=False):
    covered=year>=2015
    dated=state.get('latest_employment_date')
    known=bool(covered and dated and dated[:4]==str(year) and state['recorded_open_fa']>=0 and not roster_conflict)
    return dict(employment_capture_scope=int(covered),employment_year_known=int(known),
        employment_year_fa=int(known and state['recorded_open_fa']==1))
