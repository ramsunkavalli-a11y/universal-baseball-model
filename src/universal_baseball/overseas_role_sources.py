"""Day-qualified diagnostic reports are not guaranteed jobs or modeling coverage."""
from datetime import date


def reports_at_origin(reports, player_id, target_year, information_day):
    cutoff = date.fromisoformat(information_day)
    eligible, excluded = [], []
    for r in reports:
        if r['player_id'] != player_id:
            continue
        published = date.fromisoformat(r['publication_day'])
        if r['target_year'] != target_year:
            excluded.append(dict(report_id=r['report_id'], reason='different_target_season'))
        elif published > cutoff:
            excluded.append(dict(report_id=r['report_id'], reason='published_after_cutoff'))
        else:
            eligible.append(dict(**r, same_day_precision_warning=published == cutoff,
                                 original_publication_vintage_independently_certified=False))
    return dict(reports=eligible, excluded=excluded,
                role_coverage='observed_report' if any(r['reported_role'] for r in eligible) else 'unknown',
                source_pilot_not_population_complete=True, current_rights_certified=False)
