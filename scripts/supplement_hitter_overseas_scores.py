"""Finish predeclared precision/public/cohort diagnostics without refitting."""
import numpy as np
import polars as pl

from prepare_hitter_overseas_integration import OUT,ANCHOR,read,write,ROOT,annual_labels
from universal_baseball.hitter_compatible_value import labels
from universal_baseball.mlb_event_logit import VALUES
from review_hitter_overseas_integration import score,origin_weights
from universal_baseball.storage import sha256_file


def rate_score(g,prediction,actual,pa_weighted):
    result=[]
    for y in sorted(g['origin_year'].unique()):
        part=g.filter(pl.col('origin_year')==y);err=(part[prediction]-part[actual]).to_numpy()
        w=part['next_pa'].to_numpy().astype(float) if pa_weighted else np.ones(part.height)
        result.append(np.average(err**2,weights=w))
    return float(np.sqrt(np.mean(result)))


def main():
    receipt=read(OUT/'review-receipt.json');q=pl.read_parquet(OUT/'predictions.parquet')
    anchor=pl.read_parquet(ANCHOR).select('row_id','steamer_index','zips_index','origin_index','steamer_rate','common_zips_rate')
    q=q.join(anchor,on='row_id',how='left',validate='1:1')
    a,e=annual_labels(pl.read_parquet(ROOT/'reports/generated/practical-hitter-v31/dated-stints.parquet'))
    raw=np.array([a.get((r['target_year'],r['player_id']),np.zeros(8)) for r in q.to_dicts()])
    lab=labels(raw,np.array([e[y] for y in q['origin_year']]),np.array([e[y] for y in q['target_year']]),q['origin_replacement_rate'].to_numpy())
    q=q.with_columns(pl.Series('actual_common_rate',lab['common_rate']))
    original=q.filter(~pl.col('source_addition'));pub=original.filter((pl.col('pa_0')>0)&pl.col('steamer_index').is_not_null()&pl.col('zips_index').is_not_null())
    assert pub.height==2627
    rate=[]
    for scope,g in [('original_active',original.filter(pl.col('next_pa')>0)),('public_active',pub.filter(pl.col('next_pa')>0)),
        ('added_active',q.filter(pl.col('source_addition')&(pl.col('next_pa')>0)))]:
        arms=['domestic','overseas']+([] if scope=='added_active' else ['current'])
        relative={arm:rate_score(g,arm+'_rate','actual_relative_rate',True) for arm in arms}
        common={arm:rate_score(g,arm+'_rate','actual_common_rate',True) for arm in arms}
        if scope=='public_active':
            for arm,column in [('steamer','steamer_rate'),('zips','common_zips_rate')]:common[arm]=rate_score(g,column,'actual_common_rate',True)
        rate.append(dict(scope=scope,rows=g.height,PA_weighted_relative_rmse=relative,PA_weighted_common_rmse=common,
            public_qualification='Raw public forecasts and origin-centered actual events; no forecast recentered using future means; park and vintage differences remain',
            zips_PA_not_tested='Named ZiPS archives are rate/comparable-PA projections, not a certified workload estimate'))
    groups=[]
    for name,cond in [('current_regular',pl.col('pa_0')>=400),('current_partial',pl.col('pa_0').is_between(1,399)),
        ('absent_prior_debut',(pl.col('pa_0')==0)&(pl.col('prior_debut')==1)),('young',(pl.col('age')<=22)),
        ('all_never_debut',pl.col('prior_debut')==0)]:
        g=original.filter(cond)
        groups.append(dict(scope=name,rows=g.height,actual_pa=int(g['next_pa'].sum()),actual_value=float(g['actual_relative_value'].sum()),scores={arm:score(g,arm) for arm in ['current','domestic','overseas']}))
    write('score-supplement.json',dict(predeclared_diagnostics_no_new_fits=True,rates=rate,groups=groups,
        original_score_artifacts_preserved=True,source_hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in [__import__('pathlib').Path(__file__),OUT/'predictions.parquet',OUT/'review-receipt.json',ANCHOR]}))
    print(rate,flush=True)


if __name__=='__main__':main()
