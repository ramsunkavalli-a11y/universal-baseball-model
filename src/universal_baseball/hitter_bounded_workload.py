"""Smooth fractional conditional means, not MLB appearance probabilities."""
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from sklearn.preprocessing import SplineTransformer

SMOOTH=['age_centered','elapsed_scaled','career_mlb_observed_pa','last_stat_gap',
        'workload_reference',*[f'{level}_{lag}_pa' for level in ['MLB','AAA','AA'] for lag in range(3)],
        'pooled_mlb_quality','draft_rank']
INTERACT=['age_centered','elapsed_scaled','draft_rank','scout_rank_score_0',
          *[f'pooled_{level}_{stat}'for level in ['AAA','AA']for stat in ['pa','K','HR','BABIP']]]


def scale(n):
    if n=='age_centered':return 4.
    if n=='age_squared':return 16.
    if n=='elapsed_scaled':return 3.
    if n=='draft_elapsed':return 2.
    if n=='career_mlb_observed_pa':return 10000.
    if n=='last_stat_gap':return 5.
    if n=='workload_reference' or n.startswith('work_'):return 800.
    if n.startswith('pooled_')and n.endswith('_pa'):return 2000.
    if n.endswith('_pa'):return 800.
    if n.startswith('games_pool_'):return 400.
    if n.startswith('games_'):return 170.
    if n.startswith('role_'):return 5.
    if n.startswith('quality_')and not n.startswith('quality_present_')or n=='pooled_mlb_quality':return 3.
    if n.startswith('pooled_'):
        return {'K':.5,'BB':.3,'HBP':.1,'HR':.1,'BABIP':.5,'2B':.12,'3B':.06}[n.rsplit('_',1)[-1]]
    if n.startswith('scout_list_capacity_'):return 100.
    if n=='op_log_possible_days_upper':return 7.
    if n in ['op_observed_returns','op_roster_returns']:return 5.
    return 1.


def objective(beta,x,y,w,link,penalty):
    eta=beta[0]+x@beta[1:]
    if link=='logit':
        loss=np.logaddexp(0,eta)-y*eta; residual=expit(eta)-y
    elif link=='identity':
        residual=eta-y;loss=.5*residual**2
    else:raise ValueError('Unknown link')
    residual=residual*w/w.sum()
    grad=np.r_[residual.sum(),x.T@residual+penalty*beta[1:]]
    return float(w@loss/w.sum()+penalty*.5*(beta[1:]@beta[1:])),grad


class SmoothWorkload:
    def __init__(self,names,link):
        self.names=list(names);self.link=link
        self.scales=np.array([scale(n)for n in self.names])
        self.smooth=[self.names.index(n)for n in SMOOTH if n in self.names]
        self.interact=[self.names.index(n)for n in INTERACT if n in self.names]
        self.prior=self.names.index('prior_debut')
        self.spline=SplineTransformer(degree=2,knots=np.tile(np.array([-1.,0.,1.])[:,None],(1,len(self.smooth))),
                                     include_bias=False,extrapolation='constant')
        self.spline.fit(np.zeros((2,len(self.smooth))))
        self.zero=self.spline.transform(np.zeros((1,len(self.smooth))))[0]
        self.basis_names=self.names+[f'{self.names[i]}_smooth{j}'for i in self.smooth for j in range(3)]+[
            'prior_debut_x_'+self.names[i]for i in self.interact]

    def basis(self,x):
        x=np.asarray(x,dtype=float)
        if x.ndim!=2 or x.shape[1]!=len(self.names)or not np.isfinite(x).all():
            raise ValueError('Invalid or unavailable model inputs')
        z=np.clip(x/self.scales,-1,1)
        return np.c_[z,self.spline.transform(z[:,self.smooth])-self.zero,z[:,self.prior,None]*z[:,self.interact]]

    def fit(self,x,pa,w):
        pa=np.asarray(pa,dtype=float);w=np.asarray(w,dtype=float)
        if not np.isfinite(pa).all()or(pa<0).any()or(pa>800).any()or not np.isfinite(w).all()or(w<=0).any():
            raise ValueError('Invalid fraction label or weights')
        b=self.basis(x);self.active=np.ptp(b,axis=0)>1e-12;b=b[:,self.active]
        y=pa/800;start=np.zeros(b.shape[1]+1);mean=float(w@y/w.sum())
        start[0]=np.log(mean/(1-mean))if self.link=='logit'else mean
        r=minimize(objective,start,args=(b,y,w,self.link,.0001),jac=True,method='L-BFGS-B',
                   options={'maxiter':2000,'ftol':1e-12,'gtol':1e-7,'maxls':50})
        self.beta=r.x
        self.solver=dict(success=bool(r.success),iterations=int(r.nit),message=str(r.message),
            loss=float(r.fun),gradient_max=float(np.max(np.abs(r.jac))),basis_active=int(b.shape[1]))
        if not r.success or self.solver['gradient_max']>1e-5:raise RuntimeError(self.solver)
        return self

    def predict(self,x):
        eta=self.beta[0]+self.basis(x)[:,self.active]@self.beta[1:]
        return 800*(expit(eta)if self.link=='logit'else eta)

    def trace(self,x):
        terms=self.basis(np.asarray(x).reshape(1,-1))[0,self.active]*self.beta[1:]
        names=np.array(self.basis_names)[self.active];eta=float(self.beta[0]+terms.sum())
        return dict(intercept=float(self.beta[0]),eta=eta,raw_pa=float(800*(expit(eta)if self.link=='logit'else eta)),
            link=self.link,all_terms=[dict(feature=str(n),term=float(t))for n,t in zip(names,terms)],
            scaled_inputs=dict(zip(self.names,map(float,np.clip(np.asarray(x)/self.scales,-1,1)))))
