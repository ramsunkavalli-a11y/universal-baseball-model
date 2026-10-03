"""Exact log-link path accounting, kept separate from identity-link traces."""
import numpy as np
from universal_baseball.histogram_prediction_trace import trace


def log_trace(model,x,names):
    if model.loss!='poisson':raise ValueError('Only the declared Poisson log link is supported')
    class RawView:
        _baseline_prediction=model._baseline_prediction
        _predictors=model._predictors
        def predict(self,xx):return model._raw_predict(np.asarray(xx,dtype=float)).reshape(-1)
    t=trace(RawView(),x,names)
    t['raw_log_prediction']=t.pop('raw_prediction')
    t['unbounded_mean_pa']=float(np.exp(t['raw_log_prediction']))
    assert np.isclose(t['unbounded_mean_pa'],model.predict(np.asarray(x)[None,:])[0],atol=1e-8,rtol=1e-12)
    t['interpretation']='Exact additive log-mean path accounting followed by exponentiation. Terms are not additive PA effects, causal effects, SHAP or validated alternative forecasts.'
    return t
