"""Origin-only experience summaries and exact, noncausal PA accounting."""
import numpy as np

ROOKIE = ('DSL', 'RK120', 'RK121', 'RK124', 'RK128', 'RK134', 'RKother')
LEVELS = ('ROOKIE', 'Aminus', 'A', 'Aplus', 'AA', 'AAA', 'MLB')


def exposure(row):
    counts = {'ROOKIE': sum(row[f'{b}_0_pa'] for b in ROOKIE)}
    counts.update({b: row[f'{b}_0_pa'] for b in LEVELS[1:]})
    if any(not np.isfinite(x) or x < 0 for x in counts.values()):
        raise ValueError('Invalid origin exposure')
    occupied = [b for b in LEVELS if counts[b] > 0]
    highest = occupied[-1] if occupied else 'NONE'
    primary = max(occupied, key=lambda b: (counts[b], LEVELS.index(b))) if occupied else 'NONE'
    total = sum(counts.values())
    at_highest = counts.get(highest, 0)
    return dict(primary_level=primary, highest_level=highest,
                primary_share=counts.get(primary, 0) / total if total else 0.,
                highest_pa=at_highest, affiliated_pa=total,
                highest_exposure_band=('none' if not total else '1to29' if at_highest < 30
                                       else '30to199' if at_highest < 200 else '200plus'),
                promotion_mismatch=highest != primary,
                rank_band=('unknown' if row['scout_listed_0'] < 0 else 'unlisted'
                           if row['scout_listed_0'] == 0 else 'top20'
                           if row['scout_rank_score_0'] >= .81 else 'other_top100'))


def pa_accounting(probability, conditional_pa, actual_pa):
    p, c, y = [np.asarray(a, dtype=float) for a in (probability, conditional_pa, actual_pa)]
    if p.ndim != 1 or p.shape != c.shape or p.shape != y.shape or not len(p):
        raise ValueError('Nonempty paired arrays required')
    if not all(np.isfinite(a).all() for a in (p, c, y)):
        raise ValueError('Nonfinite data')
    if ((p < 0) | (p > 1)).any() or (c < 0).any() or (y < 0).any():
        raise ValueError('Invalid physical bounds')
    active = y > 0
    conditional_error = float((c[active] - y[active]).sum())
    discount = float(((1 - p[active]) * c[active]).sum())
    wasted = float((p[~active] * c[~active]).sum())
    error = float((p * c - y).sum())
    if not np.isclose(conditional_error - discount + wasted, error, atol=1e-7, rtol=0):
        raise AssertionError('PA accounting does not reconcile')
    return dict(rows=len(p), actual_arrivals=int(active.sum()), expected_arrivals=float(p.sum()),
                actual_pa=float(y.sum()), expected_pa=float((p*c).sum()),
                conditional_pa_for_actual_arrivals=float(c[active].sum()),
                conditional_error=conditional_error, active_probability_discount=discount,
                nonarrival_allocation=wasted, total_forecast_error=error,
                pa_rmse=float(np.sqrt(np.mean((p*c-y)**2))),
                pa_mae=float(np.mean(abs(p*c-y))),
                brier=float(np.mean((p-active)**2)),
                log_loss=float(-np.mean(active*np.log(np.clip(p,1e-15,1-1e-15))+
                    (~active)*np.log(np.clip(1-p,1e-15,1-1e-15)))))
