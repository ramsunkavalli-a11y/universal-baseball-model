"""Reuse exact accounting, explicitly labeling fixed rather than learned units."""
import evaluate_hitter_prospect_pooling_v54 as runner
import score_hitter_prospect_pooling_v54 as scoring
import evaluate_hitter_prospect_units_v55 as e
import polars as pl
import shutil
from universal_baseball.practical_hitter_v30 import score
from score_practical_hitter_v31 import rate_score,paired


def main():
    runner.OUT=e.OUT
    # Exact previously checked subsets; no new or filtered support calculation.
    for name in ['profile-support.parquet','support.parquet']:
        shutil.copy2(e.PRIOR/name,e.OUT/name)
    scoring.main()
    cases=runner.read(e.OUT/'cases.json')
    for c in cases:
        for h in c['heads'].values():
            h['interpretation']='Exact linear sum using fixed baseball references and scales, not training standard deviations. Sparse-profile extrapolation remains; not causal.'
            for z in h['feature_effects']:
                z['fixed_reference']=z.pop('training_mean');z['fixed_scale']=z.pop('training_scale')
    runner.write('cases.json',cases)
    q=pl.read_parquet(e.OUT/'predictions.parquet')
    old=pl.read_parquet(e.PRIOR/'predictions.parquet').select('row_id',
        *[pl.col('shared_'+c).alias('standardized_'+c) for c in ['p','conditional_pa','pa','rate','value']])
    q=q.join(old,on='row_id',validate='1:1')
    comparisons=[]
    for label,g in [('all',q),('never_debut',q.filter(pl.col('prior_debut')==0)),
        ('upper_never_debut',q.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Upper minors'))),
        ('lower_never_debut',q.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Lower minors')))]:
        comparisons.append(dict(scope=label,rows=len(g),scores={a:score(g,a) for a in ['repaired','standardized','shared']},
            rates={a:rate_score(g,a+'_rate') for a in ['repaired','standardized','shared']},
            intervals=[paired(g,'shared','standardized',metric) for metric in ['pa','value']]))
    runner.write('standardized-comparison.json',comparisons)


if __name__=='__main__':main()
