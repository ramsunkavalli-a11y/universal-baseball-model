"""Predictive skill-specific shrinkage, not a claimed conjugate posterior."""
import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp


def transported_counts(history,history_environment,environment,recency=np.array([1.,.8,.6])):
    if (history<0).any() or (history_environment<=0).any() or (environment<=0).any():
        raise ValueError('Invalid historical count/environment inputs')
    if not np.allclose(history_environment.sum(2),1) or not np.allclose(environment.sum(1),1):
        raise ValueError('Environment probabilities must sum to one')
    n=history.sum(2);raw=history*environment[:,None,:]/history_environment
    total=raw.sum(2);scaled=raw*np.divide(n,total,out=np.zeros_like(n),where=total>0)[:,:,None]
    pooled=(scaled*recency[None,:,None]).sum(1)
    assert np.allclose(pooled.sum(1),n@recency)
    return pooled


def predict(beta,alpha,x,own_counts,environment):
    augmented=np.column_stack([np.ones(len(x)),x]);logits=np.log(environment.copy())
    logits[:,1:]+=augmented@beta;prior=np.exp(logits-logsumexp(logits,axis=1,keepdims=True))
    exposure=own_counts.sum(1,keepdims=True)
    blend=(own_counts+alpha[None,:]*prior)/(exposure+alpha[None,:])
    probabilities=blend/blend.sum(1,keepdims=True)
    return dict(prior=prior,blend=blend,probabilities=probabilities,
        pre_normalization_own_influence=exposure/(exposure+alpha[None,:]))


def objective(flat,x,own_counts,counts,environment,adaptive,penalty=.001):
    size=(x.shape[1]+1)*7;beta=flat[:size].reshape(x.shape[1]+1,7)
    alpha=np.exp(flat[size:]) if adaptive else np.full(8,100.)
    result=predict(beta,alpha,x,own_counts,environment)
    prior,blend,p=result['prior'],result['blend'],result['probabilities']
    scale=counts.sum();totals=counts.sum(1,keepdims=True);exposure=own_counts.sum(1,keepdims=True)
    loss=-np.sum(counts*np.log(p))/scale+penalty*np.sum(beta[1:]**2)/2
    dblend=(-counts/blend+totals/blend.sum(1,keepdims=True))/scale
    dprior=dblend*alpha[None,:]/(exposure+alpha[None,:])
    dlogits=prior*(dprior-(dprior*prior).sum(1,keepdims=True))
    augmented=np.column_stack([np.ones(len(x)),x]);dbeta=augmented.T@dlogits[:,1:]
    dbeta[1:]+=penalty*beta[1:];gradient=dbeta.ravel()
    if adaptive:
        dalpha=(dblend*alpha[None,:]*(prior*exposure-own_counts)/(exposure+alpha[None,:])**2).sum(0)
        gradient=np.concatenate([gradient,dalpha])
    return float(loss),gradient


def fit(x,own_counts,counts,environment,weights,adaptive):
    if not np.isfinite(x).all() or (counts<0).any() or not counts.sum():raise ValueError('Invalid fitting inputs')
    size=(x.shape[1]+1)*7;initial=np.zeros(size)
    bounds=None
    if adaptive:
        initial=np.r_[initial,np.full(8,np.log(100.))]
        bounds=[(None,None)]*size+[(np.log(20.),np.log(5000.))]*8
    result=minimize(objective,initial,args=(x,own_counts,counts*weights[:,None],environment,adaptive),jac=True,
        method='L-BFGS-B',bounds=bounds,options={'maxiter':700,'gtol':1e-6,'ftol':1e-11})
    if not result.success:raise RuntimeError('Reliability fit failed: '+str(result.message))
    alpha=np.exp(result.x[size:]) if adaptive else np.full(8,100.)
    return dict(beta=result.x[:size].reshape(x.shape[1]+1,7),alpha=alpha,adaptive=adaptive,
        optimizer=dict(success=bool(result.success),iterations=int(result.nit),objective=float(result.fun),
            message=str(result.message),maximum_raw_gradient=float(np.abs(result.jac).max()),
            alpha_boundary_events=np.where(np.isclose(alpha,20.)|np.isclose(alpha,5000.))[0].tolist()))
