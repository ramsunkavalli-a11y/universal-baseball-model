"""Resume saved nested tuning after the JSON identity-container assertion failure."""
from pathlib import Path
import json

import numpy as np

import run_minor_range_correction_v21 as original
from universal_baseball.minor_range_talent import person_weights,design,ridge_fit,BASE_NAMES
from universal_baseball.storage import sha256_file


def normalized_audit(audit,*args,**kwargs):
    # Validation still executes and raises; JSON changes containers, not values.
    return json.loads(json.dumps(audit(*args,**kwargs),allow_nan=False))


def main():
    original.protections();original.check_preflight()
    for name in ('nuisance-fits.json.gz','features.json.gz','correction-fits.json.gz','predictions.parquet'):
        assert not (original.OUT/name).exists(),name
    assert not (original.PUBLIC/'fit-report.json.gz').exists()
    tuning_pre=original.read(original.PUBLIC/'nuisance-tuning-preflight.json.gz')
    tuning=original.read(original.OUT/'nuisance-tuning-fits.json.gz')
    for record in (tuning_pre,tuning):
        for p,h in record['hashes'].items():assert sha256_file(Path(p))==h,p
    cells=original.read(original.PUBLIC/'cells-preflight.json.gz')
    rowsby={original.key(r):r for r in original.population()}
    saved_audit=original.audit
    for cell in cells:
        for n in cell['nuisance']:
            a=n['audit'];tr=[rowsby[tuple(k)] for k in a['training_keys']];te=[rowsby[tuple(k)] for k in a['test_keys']]
            assert normalized_audit(saved_audit,tr,te,cell['origin'],a['excluded_folds'])==a
    selected=tuning['selected']
    assert len(selected)==40
    for cell in cells:
        for n in cell['nuisance']:
            matches=[s for s in selected if (s['origin'],s['fold'],s['held'])==(cell['origin'],cell['fold'],n['held'])]
            assert len(matches)==1 and matches[0]['nuisance_audit']==n['audit']
    paths=[Path(__file__),original.ROOT/'docs/defense-minor-correction-v21-resume-amendment.md',
           original.ROOT/'scripts/run_minor_range_correction_v21_quality.py',
           original.PUBLIC/'nuisance-tuning-preflight.json.gz',original.OUT/'nuisance-tuning-fits.json.gz',
           original.PUBLIC/'preflight.json.gz',original.PUBLIC/'sources-complete.json.gz']
    resume=original.PUBLIC/'resume-preflight.json.gz'
    original.write(resume,dict(before_nuisance_and_correction_fits=True,all_40_audits_equal_after_JSON_normalization=True,
        completed_nested_cells_reused=len(tuning['nested_fits']),nested_fits_not_repeated=True,
        baseline_and_statistical_rules_unchanged=True,hashes={str(p.resolve()):sha256_file(p) for p in paths}))
    queue=iter(s for s in selected if s['nuisance_audit']['fit_supported']);used=[]

    def nuisance_fit(x,y,w,ignored_outer_alpha,names):
        n=next(queue);tr=[rowsby[tuple(k)] for k in n['nuisance_audit']['training_keys']]
        ages=[r['age'] for r in tr if r['age'] is not None];median=float(np.median(ages)) if ages else 23.
        expected=design(tr,np.zeros((len(tr),4)),median,False)
        assert tuple(names)==BASE_NAMES and np.allclose(x,expected,rtol=0,atol=1e-12)
        assert np.array_equal(y,np.array([r['quality_rate'] for r in tr])) and np.array_equal(w,person_weights(tr))
        used.append(dict(origin=n['origin'],fold=n['fold'],held=n['held'],selected_alpha=n['selected_alpha']))
        return ridge_fit(x,y,w,n['selected_alpha'],names)

    original.ridge_fit=nuisance_fit
    original.audit=lambda *args,**kwargs:normalized_audit(saved_audit,*args,**kwargs)
    saved_write=original.write

    def write(path,value):
        if path==original.PUBLIC/'fit-report.json.gz':
            assert next(queue,None) is None and len(used)==sum(n['nuisance_audit']['fit_supported'] for n in selected)
            value=dict(value,nuisance_penalty_selection_fully_player_separated=True,nuisance_penalties=used,
                       resumed_without_nested_refits=True)
            value['hashes'].update({str(p.resolve()):sha256_file(p) for p in [*paths,resume]})
        saved_write(path,value)

    original.write=write
    original.quality()


if __name__=='__main__':main()
