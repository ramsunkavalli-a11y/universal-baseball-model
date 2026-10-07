"""Explicit count coverage and later MLB quality, never a fielding-value fit."""
import math

COUNT_FIELDS = ('putOuts','assists','errors','chances','throwingErrors','doublePlays',
    'caughtStealing','stolenBases','passedBall','wildPitches','catchersInterference','pickoffs')
CATCHER_FIELDS = ('caughtStealing','stolenBases','passedBall','wildPitches','catchersInterference','pickoffs')


def count(value):
    if value is None or str(value).strip() == '':
        return None, 'missing'
    try:
        x = float(value)
    except (ValueError,TypeError):
        return None, 'invalid'
    if not math.isfinite(x) or x < 0 or not x.is_integer():
        return None, 'invalid'
    return int(x), 'recorded'


def extract(stat):
    out = {}
    for field in COUNT_FIELDS:
        out[field], out[field+'_status'] = count(stat.get(field))
    c,p,a,e = [out[k] for k in ('chances','putOuts','assists','errors')]
    out['chances_identity'] = None if None in (c,p,a,e) else c == p+a+e
    t = out['throwingErrors']
    out['throwing_subset_identity'] = None if None in (t,e) else t <= e
    return out


def age_band(age):
    return 'unknown' if age is None else '<=19' if age <= 19 else '20-22' if age <= 22 else '23-25' if age <= 25 else '26+'


def sample_band(outs):
    return '25-299' if outs < 300 else '300-1499' if outs < 1500 else '1500+'


def pool_quality(origin, window, component, position, official, measurements, end=2025):
    """official: year -> outs at this position; measurements: year -> valid row.

    Positive official exposure without a valid measurement is unknown, including
    years before tracking started. No recorded exposure needs no fabricated row.
    Nonarrival is unknown quality; its separate delivered value can be zero.
    """
    if window not in (3,5) or component not in ('range','throwing','blocking') or not 2 <= position <= 9:
        raise ValueError('Unsupported quality window/component/position')
    if (component == 'range' and position == 2) or (component != 'range' and position != 2):
        raise ValueError('Incomparable measurement position')
    years = list(range(origin+1,min(origin+window,end)+1))
    measured = []
    missing = 0
    for y in years:
        r = measurements.get(y)
        if r is not None and r['valid']:
            if r['opportunities'] <= 0 or not math.isfinite(r['runs']):
                raise ValueError('Invalid certified measurement')
            measured.append(r)
        elif official.get(y,0) > 0:
            missing += official[y]
    opportunities = sum(r['opportunities'] for r in measured)
    runs = sum(r['runs'] for r in measured)
    unit, minimum = (1500,1500) if component == 'range' else (100,100) if component == 'throwing' else (1000,3000)
    mature = origin+window <= end
    valid = mature and len(measured) >= 2 and opportunities >= minimum and missing == 0
    return dict(window_end=origin+window,window_mature=mature,
        future_opportunities=opportunities,future_runs=runs,future_measured_seasons=len(measured),
        future_official_position_outs=sum(official.get(y,0) for y in years),
        unmeasured_official_outs=missing,quality_rate=unit*runs/opportunities if valid else None,
        quality_status='measured' if valid else 'window_incomplete' if not mature else
            'missing_measurement' if missing else 'no_same_position_exposure' if not any(official.get(y,0)>0 for y in years) else 'insufficient_measurement',
        unit=unit,window_has_2020=2020 in years)
