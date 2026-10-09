"""Mechanical historical accounting corrections; never refit predictions."""
from copy import deepcopy
import math


def recenter_positive_pa(rows, origin_pa):
    """Reconcile above-average runs on positive origin-MLB-PA membership."""
    result = deepcopy(rows)
    receipt = []
    for year in sorted({r['origin_year'] for r in result}):
        group = [r for r in result if r['origin_year'] == year]
        reference = [r for r in group if origin_pa.get((year, r['player_id']), 0) > 0]
        def above(r):
            return math.fsum(v for k, v in r.items() if k.endswith('_runs')
                             and k not in ('replacement_runs', 'park_runs', 'league_runs'))
        exposure = math.fsum(r['expected_PA'] for r in reference)
        if exposure <= 0:
            raise ValueError('Reference has no forecast exposure')
        center = -math.fsum(above(r) for r in reference) / exposure
        changes = []
        for row in group:
            old = row['combined']
            row['league_runs'] = center * row['expected_PA']
            row['combined'] = math.fsum(v for k, v in row.items()
                                        if k.endswith('_runs')) / row['runs_per_win']
            changes.append(row['combined'] - old)
        assert abs(math.fsum(above(r) + r['league_runs'] for r in reference)) < 1e-8
        receipt.append(dict(origin=year, reference_people=len(reference),
                            reference_projected_PA=exposure,
                            centering_runs_per600=center * 600,
                            maximum_absolute_WAR_change=max(map(abs, changes)),
                            total_WAR_change=math.fsum(changes)))
    return result, receipt


def forecast_pa_column(arm):
    return arm + '_PA' if arm in ('steamer', 'zips') else 'expected_PA'
