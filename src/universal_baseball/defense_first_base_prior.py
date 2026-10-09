"""One cutoff-known empirical prior; native first-base units stay unchanged."""
import math


def reference(records, origin, fold):
    rows = [r for r in records if r['position'] == 3 and r['range_valid']
            and origin - 2 <= r['season'] <= origin and r['player_id'] % 5 != fold]
    people = len({r['player_id'] for r in rows})
    seasons = len({r['season'] for r in rows})
    outs = sum(r['native_outs'] * 2. ** (r['season'] - origin) for r in rows)
    runs = sum(r['range_runs'] * 2. ** (r['season'] - origin) for r in rows)
    supported = people >= 20 and seasons >= 2 and outs > 0
    return dict(origin=origin, excluded_fold=fold, people=people, seasons=seasons,
                outs=outs, runs=runs, rate=1500 * runs / outs if supported else 0.,
                supported=supported, fallback=not supported,
                annual=[dict(season=y, people=len({r['player_id'] for r in rows if r['season']==y}),
                    outs=sum(r['native_outs'] for r in rows if r['season']==y),
                    runs=sum(r['range_runs'] for r in rows if r['season']==y),
                    weight=2. ** (y-origin)) for y in sorted({r['season'] for r in rows})])


def estimate(weighted_runs, weighted_outs, prior_rate):
    assert weighted_outs >= 0 and all(math.isfinite(x) for x in (weighted_runs, weighted_outs, prior_rate))
    return (1500 * weighted_runs + 3000 * prior_rate) / (weighted_outs + 3000)
