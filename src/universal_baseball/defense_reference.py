"""Explicit talent/value coordinates; no fits or silent unknown-skill imputation."""
import math

OUTFIELD = (7, 8, 9)


def center(records):
    """An exposure-weighted native center, never an average of annualized rates."""
    rows = list(records)
    assert all(r['range_valid'] and r['native_outs'] > 0 and
               r['range_runs'] is not None and math.isfinite(r['range_runs']) for r in rows)
    n = sum(r['native_outs'] for r in rows)
    return dict(people=len({r['player_id'] for r in rows}), records=len(rows),
                outs=n, runs=sum(r['range_runs'] for r in rows),
                rate=None if n == 0 else 1500 * sum(r['range_runs'] for r in rows) / n)


def cutoff_center(records, origin, fold, position):
    assert position in OUTFIELD and 0 <= fold < 5
    rows = [r for r in records if origin - 2 <= r['season'] <= origin and
            r['position'] == position and r['range_valid'] and r['player_id'] % 5 != fold]
    n = sum(2. ** (r['season'] - origin) * r['native_outs'] for r in rows)
    runs = sum(2. ** (r['season'] - origin) * r['range_runs'] for r in rows)
    return dict(origin=origin, fold=fold, position=position,
                seasons=sorted({r['season'] for r in rows}),
                people=len({r['player_id'] for r in rows}), records=len(rows),
                weighted_outs=n, weighted_runs=runs,
                rate=None if n == 0 else 1500 * runs / n,
                held_people_excluded=all(r['player_id'] % 5 != fold for r in rows))


def relative_rate(intrinsic_rate, position, reference_rate):
    if intrinsic_rate is None:
        return None
    assert math.isfinite(intrinsic_rate)
    if position not in OUTFIELD:
        return intrinsic_rate
    if reference_rate is None:
        return None
    assert math.isfinite(reference_rate)
    return intrinsic_rate - reference_rate


def reference_offset(position, outs, reference_rate):
    assert math.isfinite(outs) and outs >= 0
    if position not in OUTFIELD or outs == 0:
        return 0.
    if reference_rate is None:
        return None
    assert math.isfinite(reference_rate)
    return outs * reference_rate / 1500.


def relative_runs(intrinsic_runs, position, outs, reference_rate):
    """Certified zero opportunity is delivered zero, not measured neutral skill."""
    if outs == 0:
        assert intrinsic_runs is None or intrinsic_runs == 0
        return 0.
    if intrinsic_runs is None:
        return None
    assert math.isfinite(intrinsic_runs)
    offset = reference_offset(position, outs, reference_rate)
    return None if offset is None else intrinsic_runs - offset


def neutral_position_prior(position, reference_rate):
    """Numerical prior means in both coordinate systems; ability remains unknown."""
    if position in OUTFIELD and reference_rate is None:
        return dict(intrinsic_mean=None, relative_mean=None, measured_skill=False)
    return dict(intrinsic_mean=reference_rate if position in OUTFIELD else 0.,
                relative_mean=0., measured_skill=False)
