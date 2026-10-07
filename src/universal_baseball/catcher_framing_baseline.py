"""Tested transparent framing recipe and separately repaired dated age context."""
import math


def history(sources, origin):
    past=[s for s in sources if origin-2<=s['season']<=origin and s['framing_measurement_valid'] and s['pitches']>0]
    n=sum(s['pitches']*2.**(s['season']-origin) for s in past)
    runs=sum(s['framing_runs']*2.**(s['season']-origin) for s in past)
    return dict(history_pitches=n,history_runs=runs,history_rate=1000*runs/(6000+n),
                reliability=n/(6000+n),history_seasons=len(past),
                quality_evidence_observed=n>0)


def recover_unknown_age(origin, snapshots):
    past=[s for s in snapshots if origin-3<=s['snapshot_year']<=origin and s['age_years'] is not None
          and math.isfinite(s['age_years']) and 15<=s['age_years']<=55]
    implied={float(s['age_years']+origin-s['snapshot_year']) for s in past}
    if not past or len(implied)!=1:
        return dict(age=None,age_basis='unknown',conflict=len(implied)>1,evidence=past)
    latest=max(past,key=lambda s:s['snapshot_year'])
    return dict(age=next(iter(implied)),age_basis='dated_snapshot_carried',conflict=False,
                evidence=past,source_year=latest['snapshot_year'],source_age=latest['age_years'])
