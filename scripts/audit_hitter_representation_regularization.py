"""Inspect saved design precision and shrinkage geometry without new model fits."""
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from prepare_hitter_evidence_representation import ROOT, GEN, OUT, read, save
from prepare_practical_hitter_v33 import safe_matrix
from fit_practical_hitter_v31 import weights
from universal_baseball.storage import sha256_file


def main():
    assert read(OUT/'final-review.json')['player_walkthrough_status']=='complete'
    pre=read(OUT/'preflight.json');fit=read(OUT/'fit-report.json');rows=[]
    with threadpool_limits(limits=2):
        for k in range(5):
            frame=pl.read_parquet(OUT/f'features-{k}.parquet')
            active=frame.filter((pl.col('next_pa')>0)&~pl.col('source_addition'))
            assert np.allclose(active['next_batting_rate'],active['actual_relative_rate'],atol=1e-10,rtol=0)
            for cell in [c for c in pre['cells'] if c['fold']==k]:
                y=cell['year'];tr=frame.filter(pl.col('row_id').is_in(cell['training_row_ids'])&(pl.col('next_pa')>0)).sort('row_id')
                names=pre['arms']['overseas'];x=safe_matrix(tr,names);w=weights(tr)*tr['next_pa'].to_numpy();w*=len(w)/w.sum()
                xm=np.average(x,axis=0,weights=w);centered=x-xm
                gram=centered.T@(w[:,None]*centered);system=gram+100*np.eye(len(names));inverse=np.linalg.inv(system)
                yc=tr['actual_relative_rate'].to_numpy();ym=np.average(yc,weights=w)
                coef=np.linalg.solve(system,centered.T@(w*(yc-ym)))
                head=next(h for c in fit['cells'] if c['origin']==y and c['fold']==k for h in c['heads'] if h['arm']=='overseas')
                assert sha256_file(Path(head['path']))==head['sha256'];m=joblib.load(head['path'])
                assert np.allclose(coef,m.coef_,atol=1e-7,rtol=0)
                assert np.isclose(ym-xm@coef,m.intercept_,atol=1e-7)
                families={}
                for family in ['minor','foreign']:
                    selected=[i for i,n in enumerate(names) if n.startswith('evidence_'+family+'_') and n.rsplit('_',1)[-1] in ['K','UBB','HBP','1B','2B','3B','HR']]
                    details=[]
                    for i in selected:
                        conditional_information=max(0.,float(1/inverse[i,i]-100))
                        details.append(dict(feature=names[i],weighted_centered_sum_squares=float(gram[i,i]),
                            conditional_regularized_design_information=conditional_information,
                            design_information_fraction=conditional_information/(conditional_information+100),coefficient=float(m.coef_[i])))
                    active_source=tr.filter(pl.col(f'evidence_{family}_share')>0)
                    families[family]=dict(active_training_rows=active_source.height,active_training_people=active_source['player_id'].n_unique(),
                        actual_PA_weight_fraction=float(w[tr[f'evidence_{family}_share'].to_numpy()>0].sum()/w.sum()),features=details)
                rows.append(dict(origin=y,fold=k,active_training_rows=tr.height,active_training_people=tr['player_id'].n_unique(),families=families))
    source_cases=read(OUT/'source-cases.json');contrast=[]
    for pid,y in [(670541,2018),(701762,2024),(643217,2017)]:
        r=next(c for c in source_cases if c['player_id']==pid and c['origin_year']==y);k=r['fold']
        preold=read(GEN/'hitter-talent-bridge-v74/preflight.json');names=preold['features']['translated_ridge']
        note=read(GEN/f'hitter-talent-bridge-v74/fit-{y}-{k}.json');h=next(h for h in note['heads'] if h['arm']=='translated_ridge')
        assert sha256_file(Path(h['path']))==h['sha256'];m=joblib.load(h['path']);other=m.coef_[names.index('translated_other')]
        old={e:float(m.coef_[names.index('translated_'+e)]-other) for e in ['K','UBB','HBP','1B','2B','3B','HR']}
        contrast.append(dict(player_id=pid,origin=y,minor_share=r['minor']['information_share'],
            incumbent_equivalent_seven_coordinate_coefficients=old,
            qualification='Eight centered coordinates sum to zero, so subtracting the other coefficient preserves the old predicted sum. It does not preserve an ordinary seven-coordinate Ridge penalty.'))
    summary={}
    for family in ['minor','foreign']:
        data=[r['families'][family] for r in rows]
        fractions=[x['design_information_fraction'] for a in data for x in a['features']]
        summary[family]=dict(training_people_min=min(a['active_training_people'] for a in data),training_people_max=max(a['active_training_people'] for a in data),
                             median_design_information_fraction=float(np.median(fractions)),maximum_design_information_fraction=float(max(fractions)),
                             PA_weight_fraction_min=min(a['actual_PA_weight_fraction'] for a in data),PA_weight_fraction_max=max(a['actual_PA_weight_fraction'] for a in data))
    save('regularization-audit.json',dict(new_fits=0,all_35_Ridge_coefficients_independently_reconstructed=True,
        incumbent_feature_training_rate_labels_match_compatible_relative_target=True,summary=summary,cells=rows,incumbent_coordinate_accounting=contrast,
        interpretation='Regularized centered design diagnostics, not exact multivariate shrinkage relative to OLS, posterior precision, predictive validation or a selected replacement penalty',
        local_geometry='If every row of an input were multiplied by the same share r, alpha 100 would impose effective raw-coefficient penalty 100/r squared. Actual shares vary, so no single effective alpha applies.',
        protected_outcomes_used=False,deployment_approved=False,hashes={str(p):sha256_file(p) for p in [Path(__file__),OUT/'preflight.json',OUT/'fit-report.json',OUT/'final-review.json']}))
    print(summary);print(contrast)


if __name__=='__main__':main()
