"""Apply fully held-person nuisance tuning without editing the sealed source runner."""
from pathlib import Path
import json

import numpy as np

import run_minor_range_correction_v21 as original
from universal_baseball.nuisance_range_tuning import plans
from universal_baseball.minor_range_talent import person_weights,design,ridge_fit,ridge_predict,BASE_NAMES
from universal_baseball.storage import sha256_file


def main():
    original.protections();original.check_preflight()
    assert not (original.PUBLIC/'nuisance-tuning-preflight.json.gz').exists()
    assert not (original.OUT/'nuisance-fits.json.gz').exists() and not (original.PUBLIC/'fit-report.json.gz').exists()
    cells=original.read(original.PUBLIC/'cells-preflight.json.gz');pool=original.population();rowsby={original.key(r):r for r in pool}
    nested={};nuisances=[]
    for cell in cells:
        for n in cell['nuisance']:
            excluded=sorted({cell['fold'],n['held']});these=plans(pool,cell['origin'],excluded);tags=[]
            for p in these:
                # The parent retains its outer cutoff. Identical inner cells can
                # be shared across parents once each parent's maturity is checked.
                p=dict(p);p.pop('outer_cutoff')
                a=p['audit'];tag=f"{p['validation_origin']}-{'-'.join(map(str,a['excluded_folds']))}-v{p['validation_fold']}"
                if tag in nested:assert nested[tag]==p
                else:nested[tag]=p
                tags.append(tag)
            nuisances.append(dict(origin=cell['origin'],fold=cell['fold'],held=n['held'],nested_tags=tags,
                                  nuisance_audit=n['audit']))
    paths=[Path(__file__),original.ROOT/'src/universal_baseball/nuisance_range_tuning.py',original.ROOT/'tests/test_nuisance_range_tuning.py',
        original.ROOT/'docs/defense-minor-correction-v21-nuisance-amendment.md',original.PUBLIC/'preflight.json.gz',
        original.PUBLIC/'sources-complete.json.gz',original.PUBLIC/'cells-preflight.json.gz']
    original.write(original.PUBLIC/'nuisance-tuning-preflight.json.gz',dict(before_any_quality_fit=True,nested=nested,nuisances=nuisances,
        original_outer_baseline_unchanged=True,count_penalty_fixed=100,hashes={str(p.resolve()):sha256_file(p) for p in paths}))
    nested_fits={};values={}
    for tag,p in nested.items():
        a=p['audit'];tr=[rowsby[tuple(k)] for k in a['training_keys']];te=[rowsby[tuple(k)] for k in a['test_keys']]
        note=dict(tag=tag,fit_supported=a['fit_supported'],fits={},age_median=None)
        if a['fit_supported']:
            ages=[r['age'] for r in tr if r['age'] is not None];median=float(np.median(ages)) if ages else 23.
            x=design(tr,np.zeros((len(tr),4)),median,False);tx=design(te,np.zeros((len(te),4)),median,False);note['age_median']=median
            for alpha in (10,100):
                model=ridge_fit(x,np.array([r['quality_rate'] for r in tr]),person_weights(tr),alpha,BASE_NAMES)
                pred=ridge_predict(model,tx);note['fits'][str(alpha)]=model
                values[tag,alpha]=[dict(**r,prediction=float(v)) for r,v in zip(te,pred,strict=True)]
        nested_fits[tag]=note
    selected=[]
    for n in nuisances:
        scores={};valid_counts={}
        for alpha in (10,100):
            q=[r for tag in n['nested_tags'] for r in values.get((tag,alpha),[]) if r['quality_rate'] is not None]
            if q:
                w=person_weights(q);errors=np.array([r['prediction']-r['quality_rate'] for r in q]);scores[str(alpha)]=float(np.sqrt(np.average(errors**2,weights=w)))
            else:scores[str(alpha)]=None
            valid_counts[str(alpha)]=dict(rows=len(q),people=len({r['player_id'] for r in q}))
        alpha=100 if scores['10'] is None or scores['100']<=scores['10'] else 10
        selected.append(dict(**n,selected_alpha=alpha,scores=scores,validation_support=valid_counts,
                             no_supported_measured_validation=scores['10'] is None))
    original.write(original.OUT/'nuisance-tuning-fits.json.gz',dict(nested_fits=nested_fits,selected=selected,
        hashes={str(original.PUBLIC/'nuisance-tuning-preflight.json.gz'):sha256_file(original.PUBLIC/'nuisance-tuning-preflight.json.gz')}))
    queue=iter(n for n in selected if n['nuisance_audit']['fit_supported']);used=[]

    def nuisance_fit(x,y,w,ignored_outer_alpha,names):
        n=next(queue);tr=[rowsby[tuple(k)] for k in n['nuisance_audit']['training_keys']]
        ages=[r['age'] for r in tr if r['age'] is not None];median=float(np.median(ages)) if ages else 23.
        expected=design(tr,np.zeros((len(tr),4)),median,False)
        assert tuple(names)==BASE_NAMES and np.allclose(x,expected,rtol=0,atol=1e-12)
        assert np.array_equal(y,np.array([r['quality_rate'] for r in tr])) and np.array_equal(w,person_weights(tr))
        used.append(dict(origin=n['origin'],fold=n['fold'],held=n['held'],selected_alpha=n['selected_alpha']))
        return ridge_fit(x,y,w,n['selected_alpha'],names)

    original.ridge_fit=nuisance_fit
    original_write=original.write

    def write(path,value):
        if path==original.PUBLIC/'fit-report.json.gz':
            assert next(queue,None) is None and len(used)==sum(n['nuisance_audit']['fit_supported'] for n in selected)
            value=dict(value,nuisance_penalty_selection_fully_player_separated=True,nuisance_penalties=used)
            value['hashes'].update({str(p.resolve()):sha256_file(p) for p in [Path(__file__),
                original.PUBLIC/'nuisance-tuning-preflight.json.gz',original.OUT/'nuisance-tuning-fits.json.gz',
                original.ROOT/'docs/defense-minor-correction-v21-nuisance-amendment.md']})
        original_write(path,value)

    original.write=write
    original.quality()
    print(json.dumps(dict(fully_held_nuisance_penalties=used,nested_cells=len(nested),
         nested_fits=sum(n['fit_supported'] for n in nested_fits.values())),indent=2),flush=True)


if __name__=='__main__':main()
