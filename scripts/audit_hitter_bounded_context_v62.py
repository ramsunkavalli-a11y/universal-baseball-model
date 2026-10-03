"""Explain shared calendar terms without refitting or inventing causal probes."""
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.storage import sha256_file
import evaluate_hitter_bounded_workload_v62 as e


def main():
    pre=e.read(e.OUT/'preflight.json');f=pl.read_parquet(e.SOURCE/'features.parquet');rows=[]
    for p,h in pre['input_hashes'].items():assert sha256_file(e.previous.Path(p))==h,p
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            tr=f.filter(pl.col('row_id').is_in(c['training_row_ids']))
            te=f.filter(pl.col('row_id').is_in(c['test_row_ids']))
            heads=e.read(e.OUT/f"fit-{c['year']}-{c['fold']}.json")['heads']
            for a in e.ARMS:
                h=next(h for h in heads if h['arm']==a);assert sha256_file(e.previous.Path(h['path']))==h['sha256']
                m=joblib.load(h['path'])
                b=m.basis(te.select(m.names).to_numpy())[:,m.active];names=np.array(m.basis_names)[m.active]
                terms=b*m.beta[1:]
                for n in ['reorganized','milb_canceled_0','milb_canceled_1','milb_canceled_2']:
                    indices=np.where(names==n)[0];active=bool(len(indices))
                    rows.append(dict(year=c['year'],fold=c['fold'],arm=a,feature=n,
                        training_values=sorted(tr[n].unique().to_list()),test_values=sorted(te[n].unique().to_list()),
                        active=active,coefficient=float(m.beta[1:][indices[0]])if active else None,
                        mean_fitted_term=float(terms[:,indices[0]].mean())if active else 0.,
                        unit='fraction predictor'if a=='smooth62'else'logit fraction predictor',
                        no_counterfactual_forecast=True))
    e.write('context-term-audit.json',dict(cells=rows,interpretation=
        'Actual additive terms only. Reorganization has no within-origin variation; early positive coefficients extrapolate a calendar contrast to every player. This is not a causal policy effect or a replacement forecast.',
        source_changed=False,refitted=False))
    for y in [2021,2022,2023,2024]:
        for a in e.ARMS:
            z=[r for r in rows if r['year']==y and r['arm']==a and r['feature']=='reorganized']
            print(y,a,'reorganization term range',min(r['mean_fitted_term']for r in z),max(r['mean_fitted_term']for r in z),flush=True)


if __name__=='__main__':main()
