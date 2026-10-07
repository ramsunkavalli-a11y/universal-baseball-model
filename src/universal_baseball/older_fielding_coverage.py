"""Coverage only: older conversion credit never becomes a native skill label."""
import math


def exposure_valid(measured_outs, official_outs):
    if official_outs is None or measured_outs <= 0 or official_outs <= 0:
        return False
    gap = abs(measured_outs - official_outs)
    return gap <= 5 and gap <= .01 * max(measured_outs, official_outs)


def older_valid(row, official_outs):
    return (exposure_valid(row['fielding_outs'], official_outs)
            and row['older_conversion_runs'] is not None
            and math.isfinite(row['older_conversion_runs']))


def coverage(origin, window, official, older, native, end=2025):
    if window not in (3, 5):
        raise ValueError('Only the existing three/five year windows')
    years = range(origin + 1, min(origin + window, end) + 1)
    native_outs = native_seasons = native_missing = 0
    old_outs = old_seasons = remaining_missing = official_total = 0
    for year in years:
        official_outs = official.get(year, 0)
        official_total += official_outs
        n = native.get(year)
        native_known = n is not None and n['range_valid']
        if native_known:
            native_outs += n['native_outs']
            native_seasons += 1
        elif official_outs > 0:
            native_missing += official_outs
        # Older credit can fill only the contracted pre-tracking boundary.
        # Never cherry-pick the better of two overlapping measurements.
        o = older.get(year) if year < 2016 else None
        older_known = o is not None and o['older_conversion_valid']
        if older_known:
            old_outs += o['fielding_outs']
            old_seasons += 1
        if not native_known and not older_known and official_outs > 0:
            remaining_missing += official_outs
    mature = origin + window <= end
    current = mature and native_outs >= 1500 and native_seasons >= 2 and native_missing == 0
    potential = (mature and native_outs + old_outs >= 1500
                 and native_seasons + old_seasons >= 2 and remaining_missing == 0)
    return dict(native_observed_outs=native_outs, native_measured_seasons=native_seasons,
                native_missing_official_outs=native_missing, native_quality_available=current,
                older_pre2016_observed_outs=old_outs, older_pre2016_measured_seasons=old_seasons,
                potential_observed_outs=native_outs + old_outs,
                potential_measured_seasons=native_seasons + old_seasons,
                remaining_unmeasured_official_outs=remaining_missing,
                future_same_position_official_outs=official_total,
                potential_coverage_available=potential, potential_new_coverage=potential and not current,
                window_mature=mature)
