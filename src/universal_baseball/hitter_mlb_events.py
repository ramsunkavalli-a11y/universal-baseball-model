"""Reconstruct legacy MLB pooled event inputs, preserving actual denominators."""
import numpy as np

EVENTS = {
    'K': ('strike_outs', 'plate_appearances', .23),
    'BB': ('unintentional_walks', 'plate_appearances', .08),
    'HBP': ('hit_by_pitch', 'plate_appearances', .01),
    'HR': ('home_runs', 'plate_appearances', .03),
    'BABIP': ('babip_hits', 'babip_opportunities', .30),
    '2B': ('doubles', 'plate_appearances', .05),
    '3B': ('triples', 'plate_appearances', .005),
}
DETAIL = [f'pooled_MLB_{e}' for e in EVENTS]


def reconstruct(pid, origin, counts, covered_seasons):
    yearly = []
    for lag, weight in enumerate([1., .8, .6]):
        year = origin - lag
        if year not in covered_seasons:
            raise ValueError(f'Unknown MLB count coverage in {year}')
        row = counts.get((year, pid))
        yearly.append(dict(season=year, weight=weight, covered_absence=row is None,
                           counts={n: float(row[n]) if row else 0.
                                   for n in {f for definition in EVENTS.values() for f in definition[:2]}}))
    features, events = {}, {}
    for event, (num, den, prior) in EVENTS.items():
        annual = []
        for r in yearly:
            n, d = r['counts'][num], r['counts'][den]
            if not np.isfinite([n, d]).all() or n < 0 or d < 0 or n > d:
                raise ValueError(f'Invalid {event} counts in {r["season"]}')
            annual.append(dict(season=r['season'], weight=r['weight'], numerator=n,
                               denominator=d, covered_absence=r['covered_absence']))
        n = sum(r['weight'] * r['numerator'] for r in annual)
        d = sum(r['weight'] * r['denominator'] for r in annual)
        rate = (n + 100. * prior) / (d + 100.)
        features[f'pooled_MLB_{event}'] = rate
        events[event] = dict(annual=annual, numerator=n, denominator=d,
                             prior_center=prior, prior_opportunities=100.,
                             observed_share=d / (d + 100.),
                             unshrunk_rate=n / d if d else None,
                             shrunk_rate=rate, model_coordinate=(rate - prior) / .1)
    return features, dict(cutoff=origin, events=events)
