"""Equal-tree empirical paired-outcome distributions for non-bootstrap forests."""
import numpy as np


def leaf_weights(tree,train_x,sample_weights):
    leaves=tree.apply(train_x);n=tree.tree_.node_count
    totals=np.bincount(leaves,weights=sample_weights,minlength=n)
    return leaves,totals


def predictions(forest,train_x,test_x,pa,value,sample_weights):
    """Exact discrete PA CDF, paired marginal moments/events; no invented draws."""
    pa=np.asarray(pa);value=np.asarray(value);w=np.asarray(sample_weights)
    assert np.all(pa==np.floor(pa)) and np.all(pa>=0) and np.all(pa<=800)
    assert np.all(value[pa==0]==0)
    n=len(test_x);cdf=np.zeros((n,801));p=np.zeros((n,4));means=np.zeros((n,2))
    events=np.column_stack([pa>0,pa>=400,value<0,value>=2]).astype(float)
    for tree in forest.estimators_:
        leaves,totals=leaf_weights(tree,train_x,w);test_leaves=tree.apply(test_x);assert (totals[test_leaves]>0).all()
        counts=np.zeros((tree.tree_.node_count,801));np.add.at(counts,(leaves,pa.astype(int)),w)
        cdf+=np.cumsum(counts[test_leaves],axis=1)/totals[test_leaves,None]
        for j in range(4):p[:,j]+=np.bincount(leaves,weights=w*events[:,j],minlength=len(totals))[test_leaves]/totals[test_leaves]
        for j,outcome in enumerate([pa,value]):means[:,j]+=np.bincount(leaves,weights=w*outcome,minlength=len(totals))[test_leaves]/totals[test_leaves]
    t=len(forest.estimators_);cdf/=t;p/=t;means/=t
    assert np.allclose(cdf[:,-1],1,atol=1e-10) and np.all(np.diff(cdf,axis=1)>=-1e-10)
    assert ((p>=-1e-10)&(p<=1+1e-10)).all()
    means_expected=forest.predict(test_x)*np.array([600,2])
    assert np.allclose(means,means_expected,atol=1e-8,rtol=0)
    quantiles=np.column_stack([np.argmax(cdf>=q-1e-12,axis=1) for q in [.1,.5,.9]])
    return means,p,quantiles


def observation_weights(forest,train_x,x,sample_weights):
    """Complete paired-neighbor weights for a single reviewed forecast."""
    result=np.zeros(len(train_x));w=np.asarray(sample_weights)
    for tree in forest.estimators_:
        leaves,totals=leaf_weights(tree,train_x,w);leaf=int(tree.apply(x.reshape(1,-1))[0])
        use=leaves==leaf;result[use]+=w[use]/totals[leaf]
    result/=len(forest.estimators_)
    assert np.isclose(result.sum(),1,atol=1e-10)
    return result
