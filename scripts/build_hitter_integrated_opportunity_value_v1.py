"""Freeze inputs, then assemble fixed predictions without fitting or scoring."""
import argparse
import json
from pathlib import Path

import numpy as np
import polars as pl

from fit_hitter_arrival_coherence_v1 import save
from universal_baseball.hitter_arrival_value_transfer import FOLDS
from universal_baseball.hitter_integrated_opportunity_value import KEY, INPUTS, assemble
from universal_baseball.storage import sha256_file

OUT=Path('reports/generated/hitter-integrated-opportunity-value-v1')
PACKAGE=Path('model_artifacts/hitter-integrated-opportunity-value-v1-2026-09-25')
PLAN=Path('docs/hitter-integrated-opportunity-value-v1-plan.md')
VALUE=Path('model_artifacts/hitter-arrival-value-transfer-v1-2026-09-23')
WORK=Path('model_artifacts/hitter-conditional-workload-v1-2026-09-23')
COMP=Path('model_artifacts/multiyear-hitter-components-v1-2026-09-22')
E=Path('model_artifacts/hitter-three-year-opportunity-v1-2026-09-22')
PANEL=Path('reports/generated/hitter-arrival-source-repair-v1/repaired-panel.parquet')
CODE=[Path(__file__),Path('src/universal_baseball/hitter_integrated_opportunity_value.py'),
      Path('scripts/score_hitter_integrated_opportunity_value_v1.py'),
      Path('tests/test_hitter_integrated_opportunity_value.py')]


def hashes():
    return {str(p):sha256_file(p) for p in [PLAN,*CODE,PANEL,
        VALUE/'predictions.parquet',VALUE/'fit-manifest.json',WORK/'predictions.parquet',WORK/'fit-manifest.json',
        COMP/'component-predictions.parquet',COMP/'fit-manifest.json',E/'fit-manifest.json']}


def sources():
    v=pl.read_parquet(VALUE/'predictions.parquet').sort(KEY)
    w=pl.read_parquet(WORK/'predictions.parquet').sort(KEY)
    assert set(v.select('origin_year','horizon').unique().iter_rows())==set(FOLDS)
    for c in [*KEY,'prospect','prior_debut','B_pa','E_pa','actual_pa']:
        assert v[c].equals(w[c]),c
    x=v.join(w.select(*KEY,'D_pa','fixed_p'),on=KEY,validate='1:1',maintain_order='left')
    p=pl.read_parquet(PANEL).select('origin_year','player_id','mlb_pa_lag1','mlb_pa_lag2','pa_lag0')
    x=x.join(p,on=['origin_year','player_id'],how='left',validate='m:1',maintain_order='left')
    labels=x.select(*KEY,'actual_pa','actual_value','complete_components',
        pl.when(pl.col('complete_components')).then(pl.col('actual_expanded')).otherwise(None).alias('actual_expanded'),
        pl.col('component_old_total').alias('original_expanded'))
    return x.select(INPUTS),pl.read_parquet(COMP/'component-predictions.parquet'),labels


def provenance():
    notes={}
    for name,root in [('value',VALUE),('workload',WORK),('components',COMP),('ensemble',E)]:
        m=json.loads((root/'fit-manifest.json').read_text())
        for n in m['fits']:
            cutoff=n.get('year',n.get('origin'))
            latest=n.get('latest_label',n.get('latest_label_year',n.get('last_target')))
            if latest is not None:assert latest<=cutoff,(name,n)
            if name=='components':
                assert all(y+n['horizon']<=cutoff for y in n['selection']['origins'])
        notes[name]={'fits':len(m['fits']),'manifest_sha256':sha256_file(root/'fit-manifest.json')}
    return notes


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--freeze',action='store_true');args=ap.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    if args.freeze:
        if (OUT/'prefit-manifest.json').exists():raise ValueError('Contract already frozen')
        save(OUT/'prefit-manifest.json',{'hashes':hashes(),'folds':FOLDS,'inherited_provenance':provenance(),
             'protected_outcomes_used':False,'production_forecasts_changed':False})
        print('Input and analysis contract sealed before assembly/scoring');return
    pre=json.loads((OUT/'prefit-manifest.json').read_text());assert hashes()==pre['hashes']
    x,c,labels=sources();f,components=assemble(x,c)
    # Outcome mutations cannot change assembly; future labels are never inputs.
    changed=c.with_columns(pl.lit(-99999.).alias('actual'),pl.lit(99999.).alias('actual_batting'))
    replay,rc=assemble(x.with_columns(pl.lit(99999.).alias('actual_pa')),changed)
    assert replay.equals(f) and rc.equals(components)
    f=f.join(labels,on=KEY,validate='1:1',maintain_order='left')
    np.testing.assert_allclose(f['L_expanded'],f['original_expanded'],atol=1e-10)
    # Independently reconstruct the expanded measurement from seven native labels.
    ct=c.join(f.select(KEY),on=KEY,how='inner').group_by(KEY).agg(
        pl.col('actual').is_finite().fill_null(False).all().alias('complete'),
        pl.col('actual').sum().alias('actual_runs'))
    check=f.join(ct,on=KEY,validate='1:1')
    np.testing.assert_array_equal(check['complete'],check['complete_components'])
    good=check.filter(pl.col('complete'))
    np.testing.assert_allclose(good['actual_expanded'],good['actual_value']+good['actual_runs']/10,atol=1e-10)
    f.write_parquet(OUT/'predictions.parquet');components.write_parquet(OUT/'component-predictions.parquet')
    assert pre['hashes']==hashes()
    save(OUT/'build-manifest.json',{'prefit_sha256':sha256_file(OUT/'prefit-manifest.json'),
        'files':{n:sha256_file(OUT/n) for n in ('predictions.parquet','component-predictions.parquet')},
        'rows':f.height,'component_rows':components.height,'new_fits':0,'outcome_mutation_max_difference':0.,
        'original_release_replayed':True,'protected_outcomes_used':False,'production_forecasts_changed':False})
    print(json.dumps({'rows':f.height,'routes':f.group_by('route').len().to_dicts(),'new_fits':0}))


if __name__=='__main__':main()
