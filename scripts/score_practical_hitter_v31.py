"""Matched losses, probability calibration, coverage and allocation checks."""
import json
import numpy as np
import polars as pl
import prepare_practical_hitter_v31 as r
from universal_baseball.practical_hitter_v30 import score
from universal_baseball.storage import sha256_file

CORE=['base_hurdle','detail_hurdle','direct_detail']
RATE=['floor','rate_ridge_equal','rate_ridge_pa','rate_hist_equal','rate_hist_pa']
def probability(g,arm):
    p=g.select([f'{arm}_p{i}' for i in range(4)]).to_numpy();y=g['next_state'].to_numpy();out=[]
    for year in sorted(g['target_year'].unique()):
        w=g['target_year'].to_numpy()==year;q=p[w];z=y[w];active=(z>0).astype(float);regular=(z==3).astype(float)
        out.append([np.mean((1-q[:,0]-active)**2),np.mean((q[:,3]-regular)**2),-np.mean(np.log(np.clip(q[np.arange(len(q)),z],1e-12,1))),
            np.sum(1-q[:,0]),sum(active),np.sum(q[:,3]),sum(regular)])
    v=np.mean(out,axis=0)
    return dict(active_brier=float(v[0]),regular_brier=float(v[1]),state_log_loss=float(v[2]),
        expected_active_total=float((1-p[:,0]).sum()),actual_active_total=int((y>0).sum()),expected_regular_total=float(p[:,3].sum()),actual_regular_total=int((y==3).sum()))
def rate_score(g,col,pa_weight=True):
    g=g.filter(pl.col('next_pa')>0);values=[]
    if not len(g):return dict(rows=0,players=0,rmse=None,mae=None,bias=None,interpretation='No active MLB outcomes in this group; conditional rate cannot be scored.')
    for year,sub in g.group_by('target_year'):
        error=(sub[col]-sub['next_batting_rate']).to_numpy();w=sub['next_pa'].to_numpy() if pa_weight else np.ones(len(sub))
        assert np.isfinite(error).all()
        values.append([np.average(error**2,weights=w),np.average(abs(error),weights=w),np.average(error,weights=w)])
    v=np.mean(values,axis=0)
    return dict(rows=len(g),players=g['player_id'].n_unique(),rmse=float(np.sqrt(v[0])),mae=float(v[1]),bias=float(v[2]),
        unit='batting wins above target-season MLB average per 600 PA',weighting='equal years; actual PA within year' if pa_weight else 'equal years; equal active observations within year')
def paired(g,a,b,metric='value',repeats=1000):
    e=((g[a+'_'+metric]-g['next_'+metric])**2-(g[b+'_'+metric]-g['next_'+metric])**2).to_numpy()
    _,ids=np.unique(g['player_id'].to_numpy(),return_inverse=True);_,years=np.unique(g['target_year'].to_numpy(),return_inverse=True)
    n=np.zeros((ids.max()+1,years.max()+1));d=np.zeros_like(n);np.add.at(n,(ids,years),e);np.add.at(d,(ids,years),1)
    rng=np.random.default_rng(31);draw=[]
    for _ in range(repeats):
        w=np.bincount(rng.integers(0,len(n),len(n)),minlength=len(n));den=w@d
        if (den==0).any():continue
        draw.append(float(np.mean((w@n)/den)))
    return dict(candidate=a,benchmark=b,metric=metric+'_mse',difference=float(np.mean(n.sum(0)/d.sum(0))),
        lower=float(np.quantile(draw,.025)),upper=float(np.quantile(draw,.975)),repeats=repeats,nominal_development_interval=True)
def joined():
    f=pl.read_parquet(r.OUT/'predictions-coherent.parquet')
    old=pl.read_parquet(r.ROOT/'reports/generated/opportunity-shrinkage-v24/predictions.parquet').select('origin_year','player_id',
        pl.col('row_id').alias('v24_row_id'),*[f'v24_{c}' for c in ['pa','value','p0','p1','p2','p3']])
    f=f.join(old,on=['origin_year','player_id'],how='left',validate='1:1')
    assert f['v24_row_id'].drop_nulls().len()==4396
    public=pl.read_parquet(r.ROOT/'reports/generated/public-benchmark-v2/matched-public.parquet').select('origin_year','player_id',
        'steamer_pa','steamer_value','steamer_yield600','zips_pa','zips_yield600')
    f=f.join(public,on=['origin_year','player_id'],how='left',validate='1:1')
    for a in RATE:f=f.with_columns((pl.col('v24_pa')*(pl.col(a+'_rate')/600+pl.col('origin_replacement_rate'))).alias(a+'_v24_value'),pl.col('v24_pa').alias(a+'_v24_pa'))
    f=f.with_columns((600*(pl.col('v24_value')/pl.col('v24_pa')-pl.col('origin_replacement_rate'))).alias('v24_rate'),
        (pl.col('steamer_yield600')-600*pl.col('origin_replacement_rate')).alias('steamer_rate'),
        (pl.col('zips_yield600')-600*pl.col('origin_replacement_rate')).alias('zips_rate'))
    n=pl.scan_parquet(r.ROOT/'reports/generated/hitter-integrated-opportunity-value-v1/predictions.parquet').filter(pl.col('horizon')==1).select(
        'origin_year','player_id',pl.col('N_pa').alias('legacy_n_pa'),pl.col('N_value').alias('legacy_n_value'),
        pl.col('actual_pa').alias('legacy_actual_pa'),pl.col('actual_value').alias('legacy_actual_value')).collect()
    f=f.join(n,on=['origin_year','player_id'],how='left',validate='1:1')
    q=f.filter(pl.col('legacy_n_pa').is_not_null());assert len(q)==21819
    assert q['next_pa'].equals(q['legacy_actual_pa']) and np.allclose(q['next_value'],q['legacy_actual_value'],atol=1e-10,rtol=0)
    return f
def main():
    report=r.read(r.OUT/'fit-report.json');assert report['player_walkthrough_status']=='pending'
    f=joined();f.write_parquet(r.OUT/'scored-predictions.parquet')
    old=f.filter(pl.col('v24_row_id').is_not_null());public=old.filter((pl.col('pa_0')>0)&pl.col('steamer_pa').is_not_null()&pl.col('zips_pa').is_not_null());assert len(public)==1789
    public_n=public.filter(pl.col('legacy_n_pa').is_not_null())
    scopes=[('all',f),('v24_matched',old),('public_active',public),('public_legacy_n_matched',public_n),
        ('legacy_n_matched',f.filter(pl.col('legacy_n_pa').is_not_null())),
        ('legacy_n_current_mlb',f.filter(pl.col('legacy_n_pa').is_not_null()&(pl.col('pa_0')>0)))]
    scopes += [('origin_'+str(y),f.filter(pl.col('origin_year')==y)) for y in r.YEARS]
    scopes += [('stage_'+s,f.filter(pl.col('stage')==s)) for s in sorted(f['stage'].unique())]
    scopes += [('never_debut',f.filter(pl.col('prior_debut')==0)),('established_6plus',f.filter(pl.col('elapsed')>=6)),
        ('current_brief',f.filter(pl.col('pa_0').is_between(1,199))),('current_partial',f.filter(pl.col('pa_0').is_between(200,399))),
        ('current_regular',f.filter(pl.col('pa_0')>=400)),('debut_brief',f.filter((pl.col('elapsed')==0)&pl.col('pa_0').is_between(1,199))),
        ('dsl_current',f.filter(pl.col('DSL_0_pa')>0)),('age_unknown',f.filter(pl.col('age_unknown')==1))]
    scores=[]
    for scope,g in scopes:
        if not len(g):continue
        arms=CORE+(['v24',*[a+'_v24' for a in RATE]] if scope in ['v24_matched','public_active','public_legacy_n_matched'] else [])+(['steamer'] if scope.startswith('public_') else [])+(['legacy_n'] if scope.startswith('legacy_n_') or scope=='public_legacy_n_matched' else [])
        scores.append(dict(scope=scope,rows=len(g),players=g['player_id'].n_unique(),actual_pa=int(g['next_pa'].sum()),actual_value=float(g['next_value'].sum()),
            scores={a:score(g,a) for a in arms},probabilities={a:probability(g,a) for a in ['base_hurdle','detail_hurdle']},
            rate_scores={a:rate_score(g,a+'_rate') for a in RATE+(['v24','steamer','zips'] if scope.startswith('public_') else ['v24'] if scope=='v24_matched' else [])}))
    intervals=[]
    for label,g,a,b in [('all',f,'detail_hurdle','base_hurdle'),('all',f,'direct_detail','base_hurdle'),
        *[('v24_matched',old,a,'v24') for a in CORE],*[('public_active',public,a,'v24') for a in CORE],
        *[('legacy_n_matched',f.filter(pl.col('legacy_n_pa').is_not_null()),a,'legacy_n') for a in CORE],
        *[('public_legacy_n_matched',public_n,a,'legacy_n') for a in CORE]]:
        for metric in ['pa','value']:intervals.append(dict(scope=label,**paired(g,a,b,metric)))
    report.update(scores=scores,intervals=intervals,qualified_public_timing=True,
        supplementary_reference_hashes={str(p):sha256_file(p) for p in [r.ROOT/'reports/generated/hitter-integrated-opportunity-value-v1/predictions.parquet',
            r.ROOT/'docs/practical-hitter-v31-reference-supplement.md',r.OUT/'conditional-head-support.parquet']},
        public_mapping='Raw public counts converted with origin environment; target uses realized environment. No retrospective score recentering. Talent-superiority claims prohibited.',
        uncertainty='Player-clustered, equal-year, 1,000 paired draws; nominal development evidence, no multiplicity/selection correction.')
    raw=pl.read_parquet(r.OUT/'predictions.parquet')
    report['raw_coherence_diagnostic']={a:score(raw,a) for a in CORE}
    r.write('score-report.json',report)
    print(json.dumps([s for s in scores if s['scope'] in ['v24_matched','public_active','legacy_n_matched']],indent=2))

if __name__=='__main__':main()
