"""Post-fit accounting and calibration diagnostics, never a new forecast."""
import json
from pathlib import Path
import numpy as np
import polars as pl
from evaluate_hitter_prospect_workload_specialization import OUT, read, write, verify, NEW
from universal_baseball.storage import sha256_file


def account(g, arm):
    active = g['next_pa'].to_numpy()>0
    c = g[arm+'_conditional_pa'].to_numpy()
    p = g['preseason_p'].to_numpy()
    y = g['next_pa'].to_numpy()
    conditional_error = float(np.sum(c[active]-y[active]))
    active_probability_discount = float(np.sum((1-p[active])*c[active]))
    nonarrival_allocation = float(np.sum(p[~active]*c[~active]))
    forecast_error = float(np.sum(p*c)-np.sum(y))
    assert np.isclose(conditional_error-active_probability_discount+nonarrival_allocation,forecast_error,atol=1e-8,rtol=0)
    return dict(rows=len(g),people=g['player_id'].n_unique(),actual_arrivals=int(active.sum()),expected_arrivals=float(p.sum()),
        actual_pa=float(y.sum()),expected_pa=float(np.sum(p*c)),
        conditional_pa_for_actual_arrivals=float(c[active].sum()),conditional_error=conditional_error,
        active_probability_discount=active_probability_discount,nonarrival_allocation=nonarrival_allocation,
        total_forecast_error=forecast_error,
        interpretation='Exact retrospective accounting, not causal attribution or a model using future arrival information.')


def main():
    assert not (OUT/'allocation-diagnostic.json').exists(), 'Preserve diagnostic evidence'
    check = read(OUT/'verification.json')
    verify(check['hashes'])
    q = pl.read_parquet(OUT/'scored-predictions.parquet').filter(pl.col('prior_debut')==0)
    scopes = [('never_debut',q),('upper_never_debut',q.filter(pl.col('stage')=='Upper minors')),
        ('lower_never_debut',q.filter(pl.col('stage')=='Lower minors'))]
    scopes += [('origin_'+str(y),q.filter(pl.col('origin_year')==y)) for y in sorted(q['origin_year'].unique())]
    scopes += [('rank_'+str(b),q.filter(pl.col('rank_band')==b)) for b in sorted(q['rank_band'].unique())]
    scopes += [('thin_pro',q.filter(pl.col('thin_pro'))),('new_draftees',q.filter(pl.col('new_draftee')))]
    accounting = [dict(scope=name,arms={a:account(g,a) for a in ['preseason','pooled_extended',*NEW]}) for name,g in scopes if len(g)]
    # Fixed readable probability and conditional-mean bins explain the saved
    # model. They are not candidate features, training gates or tuning choices.
    bands = []
    p = q['preseason_p'].to_numpy()
    c = q['preseason_conditional_pa'].to_numpy()
    groups = [('probability',np.digitize(p,[.01,.1,.5,.8])),('conditional_mean',np.digitize(c,[100,200,400]))]
    for name,values in groups:
        g = q.with_columns(pl.Series('diagnostic_band',values))
        for b in sorted(g['diagnostic_band'].unique()):
            sub = g.filter(pl.col('diagnostic_band')==b)
            active = sub.filter(pl.col('next_pa')>0)
            bands.append(dict(kind=name,band=int(b),origins=sorted(sub['origin_year'].unique().to_list()),
                mean_predicted_probability=float(sub['preseason_p'].mean()),observed_arrival_fraction=len(active)/len(sub),
                mean_conditional_forecast_for_actual_arrivals=float(active['preseason_conditional_pa'].mean()) if len(active) else None,
                actual_mean_pa_for_arrivals=float(active['next_pa'].mean()) if len(active) else None,
                **account(sub,'preseason')))
    out = dict(post_fit_diagnostic=True,changes_to_forecasts=False,accounting=accounting,bands=bands,
        probability_edges=[.01,.1,.5,.8],conditional_mean_edges=[100,200,400],
        caveat='Raw summed retrospective accounting. Conditional totals can cancel allocation errors; near-zero bias does not establish calibration, dependence correctness or accurate individual forecasts.',
        hashes={str(p):sha256_file(p) for p in [OUT/'scored-predictions.parquet',OUT/'verification.json']},
        code_sha256=sha256_file(Path(__file__)),protected_outcomes_used=False)
    write('allocation-diagnostic.json',out)
    print(json.dumps(accounting[:3],indent=2))
    print(json.dumps(bands,indent=2))


if __name__=='__main__':
    main()
