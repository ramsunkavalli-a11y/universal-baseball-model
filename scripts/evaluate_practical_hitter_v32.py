"""Fixed, unfitted opportunity/contribution reconnection and review evidence."""
import json
from pathlib import Path
import numpy as np
import polars as pl
import prepare_practical_hitter_v31 as r
from score_practical_hitter_v31 import paired
from universal_baseball.practical_hitter_v30 import score
from universal_baseball.storage import sha256_file

OUT=r.ROOT/'reports/generated/practical-hitter-v32'
ANCHORS=['v24','legacy_n']
FIXED=[(621566,2017),(643446,2018),(668715,2022),(691026,2023),
       (592450,2016),(592450,2021),(667670,2022),(680574,2024),
       (665487,2022),(805811,2024),(701762,2024)]

def write(name,obj):
    (OUT/name).write_text(json.dumps(obj,indent=2,allow_nan=False,default=str),encoding='utf8')

def assemble(f):
    flags={}
    for anchor in ANCHORS:
        available=pl.col(anchor+'_pa').is_not_null()
        q=f.filter(available & (pl.col(anchor+'_pa')<=0))
        assert np.allclose(q[anchor+'_value'].to_numpy(),0,atol=1e-10),anchor
        flags[anchor]=dict(zero_denominator_rows=len(q),missing_rows=f[anchor+'_pa'].null_count())
        f=f.with_columns(pl.when(~available).then(None).when(pl.col(anchor+'_pa')>0)
            .then(pl.col(anchor+'_value')/pl.col(anchor+'_pa')).otherwise(0).alias(anchor+'_yield'))
        for stem,new in [('base','base_hurdle'),('detail','detail_hurdle')]:
            arm=stem+'_'+anchor
            f=f.with_columns(pl.when(available).then(pl.col(new+'_pa')).otherwise(None).alias(arm+'_pa'),
                (pl.col(new+'_pa')*pl.col(anchor+'_yield')).alias(arm+'_value'))
            assert np.isfinite(f[arm+'_value'].drop_nulls().to_numpy()).all()
    f=f.with_columns(pl.col('detail_hurdle_pa').alias('detail_weighted_rate_pa'),
        (pl.col('detail_hurdle_pa')*(pl.col('rate_hist_pa_rate')/600+pl.col('origin_replacement_rate'))).alias('detail_weighted_rate_value'))
    return f,flags

def main():
    assert r.read(r.OUT/'score-report.json')['player_walkthrough_status']=='complete'
    OUT.mkdir(parents=True,exist_ok=True)
    contract=r.ROOT/'docs/practical-hitter-v32-contract.md'
    source=r.OUT/'scored-predictions.parquet'
    write('contract.json',dict(contract_sha256=sha256_file(contract),source_sha256=sha256_file(source),
        verification_sha256=sha256_file(r.OUT/'verification.json'),no_fits=True))
    f,flags=assemble(pl.read_parquet(source));assert len(f)==30506
    f.write_parquet(OUT/'predictions.parquet')
    scopes=[('all',f,None),('v24_matched',f.filter(pl.col('v24_pa').is_not_null()),'v24'),
        ('legacy_n_matched',f.filter(pl.col('legacy_n_pa').is_not_null()),'legacy_n')]
    public=f.filter((pl.col('pa_0')>0)&pl.col('v24_pa').is_not_null()&pl.col('steamer_pa').is_not_null()&pl.col('zips_pa').is_not_null())
    assert len(public)==1789
    scopes.extend([('public_active',public,'v24'),('public_legacy_n',public.filter(pl.col('legacy_n_pa').is_not_null()),'legacy_n')])
    for anchor in ANCHORS:
        g=f.filter(pl.col(anchor+'_pa').is_not_null())
        assert len(g)=={'v24':4396,'legacy_n':21819}[anchor]
        scopes.extend((anchor+'_origin_'+str(y),g.filter(pl.col('origin_year')==y),anchor) for y in sorted(g['origin_year'].unique()))
        scopes.extend((anchor+'_stage_'+s,g.filter(pl.col('stage')==s),anchor) for s in sorted(g['stage'].unique()))
        for label,condition in [('current_regular',pl.col('pa_0')>=400),('current_partial',pl.col('pa_0').is_between(1,399)),
            ('current_absent',pl.col('pa_0')==0),('never_debut',pl.col('prior_debut')==0)]:
            if len(g.filter(condition)):scopes.append((anchor+'_'+label,g.filter(condition),anchor))
    scores=[];intervals=[]
    for label,g,anchor in scopes:
        arms=['detail_weighted_rate','detail_hurdle','base_hurdle']
        if anchor:arms.extend([anchor,'base_'+anchor,'detail_'+anchor])
        if label.startswith('public_'):arms.append('steamer')
        scores.append(dict(scope=label,rows=len(g),players=g['player_id'].n_unique(),
            actual_pa=float(g['next_pa'].sum()),actual_value=float(g['next_value'].sum()),
            scores={a:score(g,a) for a in arms}))
        if label in ['v24_matched','legacy_n_matched','public_active','public_legacy_n']:
            for arm in ['base_'+anchor,'detail_'+anchor,'detail_weighted_rate']:
                intervals.append(dict(scope=label,**paired(g,arm,anchor)))
    write('scores.json',scores);write('intervals.json',intervals)
    chosen={}
    def add(g,reason):
        if len(g):chosen.setdefault(g['row_id'][0],[]).append(reason)
    for pid,year in FIXED:add(f.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==year)),'fixed diagnostic')
    for anchor in ANCHORS:
        g=f.filter(pl.col(anchor+'_pa').is_not_null())
        for arm in ['base_'+anchor,'detail_'+anchor,'detail_weighted_rate']:
            q=g.with_columns(((pl.col(arm+'_value')-pl.col('next_value'))**2-(pl.col(anchor+'_value')-pl.col('next_value'))**2).alias('_change'),
                (pl.col(arm+'_value')-pl.col('next_value')).alias('_error'))
            add(q.sort('_change'),arm+' largest gain vs '+anchor);add(q.sort('_change',descending=True),arm+' largest harm vs '+anchor)
            add(q.sort('_error'),arm+' false low');add(q.sort('_error',descending=True),arm+' false high')
            add(q.filter(pl.col('next_pa').is_between(200,399)).sort(pl.col('_error').abs()),arm+' ordinary partial workload')
    counts=pl.read_parquet(r.OUT/'counts.parquet');oldcases={c['origin']['row_id']:c for c in r.read(r.OUT/'cases.json')}
    pre=r.read(r.OUT/'preflight-ready.json');support=pl.read_parquet(r.OUT/'conditional-head-support.parquet')
    cases=[]
    for rid,reasons in chosen.items():
        o=f.filter(pl.col('row_id')==rid).row(0,named=True);year=o['origin_year']
        pool=f.filter((pl.col('origin_year')==year)&(pl.col('row_id')!=rid)&(pl.col('stage')==o['stage'])&(pl.col('prior_debut')==o['prior_debut']))
        distance=sum(((pl.col(k)-o[k])/s)**2 for k,s in [('age',5),('elapsed',5),('pa_0',200),('AAA_0_pa',200),('AA_0_pa',200),('minor_pa_0',300),('quality_0',1)])
        peers=pool.with_columns(distance.alias('origin_distance')).sort('origin_distance','player_id').head(3).select(
            'player_id','player_name','age','pa_0','AAA_0_pa','AA_0_pa','minor_pa_0','quality_0','on_40man','v24_pa','v24_value',
            'legacy_n_pa','legacy_n_value','detail_hurdle_pa','detail_hurdle_value','next_pa','next_value','origin_distance').to_dicts()
        cases.append(dict(origin=o,selection=reasons,raw_level_history=counts.filter((pl.col('player_id')==o['player_id'])&pl.col('season').is_between(year-2,year)).sort('season','bucket').to_dicts(),
            actual_features={k:o[k] for k in pre['detail_features']},comparisons=peers,
            conditional_support=support.filter(pl.col('row_id')==rid).select('head','conditional_profile_players').to_dicts(),
            inherited_v31_case=oldcases.get(rid),mechanism='Deterministic expected-PA replacement with unchanged contribution yield; no refits or causal attribution.'))
    write('cases.json',cases)
    write('report.json',dict(no_fits=True,rows=len(f),fallbacks=flags,cases=len(cases),player_walkthrough_status='pending',
        frozen_forecast_changed=False,practical_model_goal_complete=False))
    for s in scores[:5]:print(json.dumps(s,indent=2))
    for c in cases:
        o=c['origin'];print(o['player_name'],o['origin_year'],o['next_value'],o['v24_value'],o['detail_v24_value'],o['legacy_n_value'],o['detail_legacy_n_value'])

if __name__=='__main__':main()
