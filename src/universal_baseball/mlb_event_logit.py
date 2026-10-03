"""Count-likelihood batting model with explicit league-environment offsets."""
import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp
from universal_baseball.hitter_v2_evaluation import NEUTRAL_WOBA_WEIGHTS,NEUTRAL_WOBA_SCALE

EVENTS=['other','K','UBB','HBP','1B','2B','3B','HR']
VALUES=np.array([0.,0.,*[NEUTRAL_WOBA_WEIGHTS[e] for e in EVENTS[2:]]])


def probabilities(beta,x,environment):
    x=np.column_stack([np.ones(len(x)),x])
    logits=np.log(environment.copy());logits[:,1:]+=x@beta
    return np.exp(logits-logsumexp(logits,axis=1,keepdims=True))


def objective(flat,x,counts,environment,penalty=.001):
    beta=flat.reshape(x.shape[1]+1,7);aug=np.column_stack([np.ones(len(x)),x])
    logits=np.log(environment.copy());logits[:,1:]+=aug@beta
    logp=logits-logsumexp(logits,axis=1,keepdims=True);p=np.exp(logp)
    scale=counts.sum()
    value=-np.sum(counts*logp)/scale+penalty*np.sum(beta[1:]**2)/2
    grad=aug.T@((p*counts.sum(axis=1,keepdims=True)-counts)[:,1:])/scale
    grad[1:]+=penalty*beta[1:]
    return float(value),grad.ravel()


def fit(x,counts,environment,weights):
    if not np.isfinite(x).all() or (counts<0).any():raise ValueError('Invalid model inputs')
    if (environment<=0).any() or not np.allclose(environment.sum(1),1):raise ValueError('Invalid league offsets')
    weighted=counts*weights[:,None]
    res=minimize(objective,np.zeros((x.shape[1]+1)*7),args=(x,weighted,environment),jac=True,
        method='L-BFGS-B',options={'maxiter':500,'gtol':1e-6,'ftol':1e-11})
    if not res.success:raise RuntimeError(f'Event fit did not converge: {res.message}')
    return dict(beta=res.x.reshape(x.shape[1]+1,7),optimizer=dict(success=bool(res.success),message=str(res.message),
        iterations=int(res.nit),objective=float(res.fun),maximum_gradient=float(abs(res.jac).max())))


def batting_rate(p,environment):
    if (p<0).any() or not np.allclose(p.sum(1),1):raise ValueError('Incoherent probability forecast')
    return ((p-environment)@VALUES)*600/NEUTRAL_WOBA_SCALE/10
