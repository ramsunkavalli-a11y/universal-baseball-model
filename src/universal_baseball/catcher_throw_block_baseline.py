"""Single predeclared opportunity-shrunk history estimate, not an age learner."""
import numpy as np

PRIOR={'throwing':100.,'blocking':3000.}
UNIT={'throwing':100.,'blocking':1000.}


def history(kind,sources,origin):
    past=[s for s in sources if s['component']==kind and origin-2<=s['season']<=origin and s['measurement_valid']]
    n=sum(s['opportunities']*2.**(s['season']-origin) for s in past)
    runs=sum(s['runs']*2.**(s['season']-origin) for s in past)
    return dict(history_opportunities=n,history_runs=runs,history=UNIT[kind]*runs/(n+PRIOR[kind]),
                reliability=n/(n+PRIOR[kind]),quality_evidence_observed=n>0)


def score(rows,field):
    y=np.array([r['quality_rate'] for r in rows]);p=np.array([r[field] for r in rows]);e=p-y
    unit=UNIT[rows[0]['component']]
    return dict(people=len(rows),rmse=float(np.sqrt(np.mean(e**2))),mae=float(np.mean(abs(e))),bias=float(np.mean(e)),
                predicted_runs_actual_exposure=float(sum(r[field]*r['future_opportunities']/unit for r in rows)),
                actual_runs=float(sum(r['future_runs'] for r in rows)))


def interval(rows):
    rng=np.random.default_rng(7053257);y=np.array([r['quality_rate'] for r in rows]);p=np.array([r['history'] for r in rows])
    idx=rng.integers(0,len(rows),size=(2000,len(rows)))
    changes=np.sqrt(np.mean((p[idx]-y[idx])**2,axis=1))-np.sqrt(np.mean(y[idx]**2,axis=1))
    return dict(difference=float(np.sqrt(np.mean((p-y)**2))-np.sqrt(np.mean(y**2))),
                low=float(np.quantile(changes,.025)),high=float(np.quantile(changes,.975)),draws=2000,person_clustered=True)
