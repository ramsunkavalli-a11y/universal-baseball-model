"""Describe calibration bounds, residual bias and numerical comparison limits."""
import numpy as np
import polars as pl
from pathlib import Path

from universal_baseball.storage import sha256_file
from fit_practical_hitter_v31 import weights
from score_hitter_event_count_risk import equal_year, public
import evaluate_hitter_event_count_risk as e


def main():
    assert not (e.OUT/'limits.json').exists(), 'Preserve the descriptive review'
    scored = e.read(e.OUT/'scoring-verification.json'); e.old.check_hashes(scored['artifact_hashes'])
    audit = e.read(e.OUT/'monte-carlo-audit.json'); e.old.check_hashes(audit['source_hashes'])
    assert sha256_file(e.WORK/'monte-carlo-audit.parquet') == audit['artifact_sha256']
    q = pl.read_parquet(e.WORK/'scored-predictions.parquet')
    a = pl.read_parquet(e.WORK/'monte-carlo-audit.parquet')
    fits = e.read(e.OUT/'fit-report.json')['cells']; pre = e.read(e.OUT/'preflight.json')['cells']
    calibration = []
    for c, origin in zip(fits, pre):
        assert (c['year'], c['fold']) == (origin['year'], origin['fold'])
        cal = pl.read_parquet(origin['calibration_path'])
        beta = c['parameters']['associated']['beta']
        cal = cal.with_columns((pl.col('common_rate_label')-pl.col('nested_rate')).alias('independent_residual'),
            (pl.col('common_rate_label')-pl.col('nested_rate')-beta*(pl.col('next_pa').log()-pl.col('workload_log_center'))).alias('associated_residual'))
        for band, expr in [('1to49', pl.col('next_pa') < 50),
                           ('50to299', pl.col('next_pa').is_between(50, 300, closed='left')),
                           ('300plus', pl.col('next_pa') >= 300)]:
            g = cal.filter(expr)
            if not len(g): continue
            w = weights(g); w = w/w.sum()
            calibration.append(dict(year=c['year'], fold=c['fold'], actual_pa_band=band,
                rows=len(g), people=g['player_id'].n_unique(),
                independent_mean_residual=float(w @ g['independent_residual'].to_numpy()),
                associated_mean_residual=float(w @ g['associated_residual'].to_numpy()),
                qualification='Realized PA diagnostic, never forecast-time routing'))
    comparisons = []
    for arm, ref in [('associated', 'normal'), ('independent', 'normal'), ('associated', 'independent')]:
        main = q.filter(public()); check = a.filter(public())
        first = equal_year(main, arm+'_pinball')-equal_year(main, ref+'_pinball')
        second = equal_year(check, arm+'_pinball')-equal_year(check, ref+'_pinball')
        comparisons.append(dict(arm=arm, reference=ref, main_difference=first, audit_difference=second,
            direction_stable=bool(np.sign(first) == np.sign(second)),
            qualification='Additional matched public direction check, not a tuned model-selection threshold'))
    points = q.filter(public()).with_columns((pl.col('preseason_pa')-pl.col('next_pa')).abs().alias('pa_abs'),
        ((pl.col('preseason_pa')-pl.col('next_pa'))**2).alias('pa_squared'))
    e.write(e.OUT/'limits.json', dict(associated_beta_bound_cells=sum(c['parameters']['associated_beta_at_bound'] for c in fits),
        cells=len(fits), beta_restriction_preserved=True, point_PA_RMSE=float(np.sqrt(equal_year(points, 'pa_squared'))),
        point_PA_MAE=equal_year(points, 'pa_abs'), public_rows=len(points),
        paired_monte_carlo_directions=comparisons, calibration_bias_diagnostics=calibration,
        numerical_ranking_stable=audit['numerical_ranking_stable'] and all(c['direction_stable'] for c in comparisons),
        finite_simulation_event_probability_limit='Rare-event Brier/log scores use finite Monte Carlo probabilities, not exact Dirichlet-multinomial tail sums',
        working_event_profile_limit='Origin MLB reference tilted to scalar rate, not own-player K/BB/HR or park-neutral forecast',
        calibration_support_limit='Global borrowing remains for sparse and absent refined profiles',
        mean_forecast_and_readiness_unchanged=True, player_walkthrough_status='pending', protected_outcomes_used=False,
        source_hashes={str(e.OUT/'scoring-verification.json'): sha256_file(e.OUT/'scoring-verification.json'),
            str(e.OUT/'monte-carlo-audit.json'): sha256_file(e.OUT/'monte-carlo-audit.json'), str(__file__): sha256_file(Path(__file__))}))
    print('All beta bounds:', sum(c['parameters']['associated_beta_at_bound'] for c in fits), '/', len(fits), flush=True)
    print('Matched Monte Carlo directions:', comparisons, flush=True)


if __name__ == '__main__':
    main()
