"""Exact numerical tree-path accounting, not SHAP or causal attribution."""
import numpy as np


def trace(model,x,names):
    x=np.asarray(x,dtype=float);effects=np.zeros(len(names));reference=float(model._baseline_prediction[0,0]);paths=[]
    for t,predictors in enumerate(model._predictors):
        assert len(predictors)==1
        nodes=predictors[0].nodes;means={}
        def expectation(i):
            n=nodes[i]
            if n['is_leaf']:v=float(n['value'])
            else:
                l,h=int(n['left']),int(n['right']);a,b=int(nodes[l]['count']),int(nodes[h]['count'])
                v=(a*expectation(l)+b*expectation(h))/(a+b)
            means[i]=v;return v
        reference+=expectation(0);i=0;path=[]
        while not nodes[i]['is_leaf']:
            n=nodes[i];assert not n['is_categorical']
            j=int(n['feature_idx']);threshold=float(n['num_threshold'])
            left=bool(n['missing_go_to_left']) if np.isnan(x[j]) else bool(x[j]<=threshold)
            child=int(n['left'] if left else n['right']);effect=means[child]-means[i];effects[j]+=effect
            path.append(dict(feature=names[j],input=float(x[j]),threshold=threshold,left=left,path_effect=effect));i=child
        paths.append(dict(tree=t,leaf_value=float(nodes[i]['value']),splits=path))
    prediction=reference+effects.sum()
    assert np.isclose(prediction,float(model.predict(x[None,:])[0]),rtol=0,atol=1e-8)
    order=np.argsort(-abs(effects));selected=[dict(feature=names[i],input=float(x[i]),path_effect=float(effects[i])) for i in order if effects[i]!=0]
    return dict(reference=reference,raw_prediction=float(prediction),feature_effects=selected,
        game_feature_effect=float(sum(effects[i] for i,c in enumerate(names) if c.startswith(('games_','role_')))),
        largest_trees=sorted(paths,key=lambda p:abs(p['leaf_value']),reverse=True)[:3],
        interpretation='Exact count-weighted node-path decomposition. Correlated features/order affect attribution; not SHAP, causal effects, game-feature ablation, or an independent forecast.')
