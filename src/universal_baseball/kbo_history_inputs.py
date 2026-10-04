"""Origin-bounded raw KBO history; missing league coverage is never zero talent."""
from .kbo_history import FIELDS1,FIELDS2


def history_at(rows,kbo_id,origin,coverage_seasons):
    if not kbo_id or not isinstance(kbo_id,str):
        raise ValueError('A verified string KBO ID is required')
    coverage={int(y) for y in coverage_seasons if int(y)<=origin}
    known=[r for r in rows if r['kbo_id']==kbo_id and r['season']<=origin]
    if any(r['season'] not in coverage for r in known):
        raise ValueError('Observed source row in an unqualified season')
    if len({r['season'] for r in known})!=len(known):
        raise ValueError('Duplicate aggregated KBO player-season')
    expected=list(range(origin-2,origin+1))
    missing=[y for y in expected if y not in coverage]
    recent=[r for r in known if r['season'] in expected]
    counts={field:sum(r[field] for r in recent) for field in FIELDS1+FIELDS2}
    complete=not missing
    pa=counts['pa']; bip=counts['ab']-counts['so']-counts['hr']+counts['sf']
    # A partial observed subtotal is useful to display, not a complete three-year feature.
    rates=dict(ubb_rate=(counts['bb']-counts['ibb'])/pa if pa and complete else None,
               k_rate=counts['so']/pa if pa and complete else None,
               hr_rate=counts['hr']/pa if pa and complete else None,
               babip=(counts['hits']-counts['hr'])/bip if bip and complete else None)
    return dict(kbo_id=kbo_id,origin_year=origin,observed_history_pa=sum(r['pa'] for r in known),
                observed_positive_pa_seasons=sorted(r['season'] for r in known if r['pa']>0),
                recent_expected_seasons=expected,recent_missing_coverage=missing,
                recent_window_complete=complete,observed_recent_counts=counts,
                recent_counts=counts if complete else None,
                certified_recent_first_team_zero_pa_seasons=[y for y in expected if y in coverage
                    and not any(r['season']==y and r['pa']>0 for r in recent)],
                experience_left_truncated=True,minor_Futures_history_known=False,
                source_scope='KBO first-team batting only',MLB_translation_fitted=False,
                **rates)
