"""Fixed neutral-prior history reduces the performance signal itself."""
import numpy as np

PRIOR={'arm':300.,'receiving':600.}


def history(kind,sources,origin):
    valid_key='isolated_outfield_quality_valid' if kind=='arm' else 'quality_valid'
    eligible=[r for r in sources if r['kind']==kind and origin-2<=r['season']<=origin and r[valid_key]]
    n=sum(r['opportunities']*2.**(r['season']-origin) for r in eligible)
    runs=sum(r['runs']*2.**(r['season']-origin) for r in eligible)
    return dict(history_opportunities=n,history_runs=runs,history=100*runs/(n+PRIOR[kind]),
                reliability=n/(n+PRIOR[kind]),quality_evidence_observed=n>0,
                research_only=True)


def score(rows,key):
    y=np.array([r['quality_rate'] for r in rows]);pred=np.array([r[key] for r in rows]);e=pred-y
    return dict(people=len(rows),rmse=float(np.sqrt(np.mean(e**2))),mae=float(np.mean(abs(e))),bias=float(np.mean(e)),
        predicted_runs_actual_exposure=sum(r[key]*r['future_opportunities']/100 for r in rows),
        actual_runs=sum(r['future_runs'] for r in rows))


def interval(rows):
    y=np.array([r['quality_rate'] for r in rows]);pred=np.array([r['history'] for r in rows])
    rng=np.random.default_rng(70633647);idx=rng.integers(0,len(rows),size=(2000,len(rows)))
    d=np.sqrt(np.mean((pred[idx]-y[idx])**2,axis=1))-np.sqrt(np.mean(y[idx]**2,axis=1))
    return dict(difference=float(np.sqrt(np.mean((pred-y)**2))-np.sqrt(np.mean(y**2))),
                low=float(np.quantile(d,.025)),high=float(np.quantile(d,.975)),draws=2000,person_clustered=True)
