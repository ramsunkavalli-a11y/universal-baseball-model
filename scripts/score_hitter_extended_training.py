"""Replay matched heads; score unchanged cohorts and persist diagnostic cases."""
from pathlib import Path
import sys
import json

import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

from universal_baseball.practical_hitter_v30 import score
from universal_baseball.storage import sha256_file
from prepare_practical_hitter_v33 import safe_matrix
from score_practical_hitter_v31 import paired,rate_score
from score_hitter_reliability_v50 import rate_interval
from prepare_hitter_extended_training import ROOT,OUT,CURRENT,read,write,verify,profile,BUCKETS

FIXED = [(701762,2024),(694671,2023),(624413,2018),(660670,2017),
         (677594,2021),(702616,2023),(592450,2024)]
ARMS = ['preseason','translated_ridge','restricted','extended','extended_pa_only','extended_rate_only']


def probability(g,arm):
    per = []
    for _,s in g.group_by('target_year'):
        p = s[arm+'_p'].to_numpy()
        y = (s['next_pa'].to_numpy()>0).astype(float)
        per.append([np.mean((p-y)**2),-np.mean(y*np.log(np.clip(p,1e-12,1))+(1-y)*np.log(np.clip(1-p,1e-12,1)))])
    v = np.mean(per,axis=0)
    return dict(brier=float(v[0]),log_loss=float(v[1]),expected_active=float(g[arm+'_p'].sum()),actual_active=int((g['next_pa']>0).sum()))


def main():
    assert not (OUT/'verification.json').exists(), 'Preserve completed scoring'
    pre = read(OUT/'preflight.json')
    verify(pre['input_hashes'])
    q = pl.read_parquet(OUT/'predictions.parquet').sort('row_id')
    anchor = pl.read_parquet(CURRENT/'scored-predictions.parquet').sort('row_id')
    assert q.select(anchor.columns).equals(anchor)
    source = pl.read_parquet(OUT/'features.parquet')
    verification = []
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            te = source.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            saved = q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            note = read(OUT/f"fit-{c['year']}-{c['fold']}.json")
            verify({str(OUT/f"forecast-{c['year']}-{c['fold']}.parquet"):note['prediction_sha256']})
            for h in note['heads']:
                verify({h['path']:h['sha256']})
                m = joblib.load(h['path'])
                x = safe_matrix(te,h['features']) if h['head']=='rate' else te.select(h['features']).to_numpy()
                pred = m.predict_proba(x)[:,1] if h['head']=='participation' else m.predict(x)
                suffix = 'raw_p' if h['head']=='participation' else 'raw_conditional_pa' if h['head']=='conditional_pa' else 'rate'
                error = float(np.max(abs(pred-saved[h['arm']+'_'+suffix].to_numpy())))
                assert error < 1e-10
                verification.append(dict(year=c['year'],fold=c['fold'],arm=h['arm'],head=h['head'],max_replay_error=error))
    restricted_diffs = {}
    for old,new in [('preseason_raw_p','restricted_raw_p'),('preseason_raw_conditional_pa','restricted_raw_conditional_pa'),('baseline_rate','restricted_rate')]:
        error = float(np.max(abs(q[old].to_numpy()-q[new].to_numpy())))
        restricted_diffs[old] = error
        assert error < 1e-8, 'Restricted control must reproduce the unchanged recipe'
    for arm in ['restricted','extended']:
        assert np.allclose(q[arm+'_pa'],q[arm+'_p']*q[arm+'_conditional_pa'],atol=1e-10,rtol=0)
        assert np.allclose(q[arm+'_value'],q[arm+'_pa']*(q[arm+'_rate']/600+q['origin_replacement_rate']),atol=1e-10,rtol=0)
    bridge = pl.read_parquet(ROOT/'reports/generated/hitter-talent-bridge-v74/predictions.parquet').sort('row_id')
    assert bridge.select(anchor.columns).equals(anchor)
    names = ['translated_ridge_'+v for v in ['pa','rate','value']]
    q = q.join(bridge.select('row_id',*names),on='row_id',validate='1:1')
    tags = profile(source)
    q = q.join(tags.select('row_id','dominant_level','age_band','rank_band','thin_pro','new_draftee'),on='row_id',validate='1:1')
    actual_rates = source.filter(pl.col('row_id').is_in(q['row_id'].to_list())).select('row_id',pl.col('next_batting_rate').alias('realized_season_rate'))
    q = q.join(actual_rates,on='row_id',validate='1:1')
    assert np.isfinite(q['realized_season_rate'].to_numpy()).all()
    never = q.filter(pl.col('prior_debut')==0)
    public = q.filter((pl.col('pa_0')>0)&pl.col('steamer_index').is_not_null()&pl.col('zips_index').is_not_null())
    assert len(public)==2627
    scopes = [('all',q),('never_debut',never),('upper_never_debut',never.filter(pl.col('stage')=='Upper minors')),
        ('lower_never_debut',never.filter(pl.col('stage')=='Lower minors')),('public',public),
        ('established',q.filter(pl.col('prior_debut')==1)),('new_draftees',never.filter(pl.col('new_draftee'))),
        ('thin_pro',never.filter(pl.col('thin_pro'))),('teenage_dsl',never.filter((pl.col('DSL_0_pa')>0)&(pl.col('age')<=17)))]
    scopes += [('origin_'+str(y),q.filter(pl.col('origin_year')==y)) for y in sorted(q['origin_year'].unique())]
    scopes += [('never_origin_'+str(y),never.filter(pl.col('origin_year')==y)) for y in sorted(q['origin_year'].unique())]
    scores = []
    for name,g in scopes:
        if not len(g):
            continue
        rates = g.with_columns(pl.col('realized_season_rate').alias('next_batting_rate'))
        scores.append(dict(scope=name,rows=len(g),people=g['player_id'].n_unique(),actual_pa=int(g['next_pa'].sum()),actual_value=float(g['next_value'].sum()),
            scores={a:score(g,a) for a in ARMS+(['steamer'] if name=='public' else [])},
            probability={a:probability(g,a) for a in ['preseason','restricted','extended']},
            rates={a:rate_score(rates,a+'_rate') for a in ['preseason','translated_ridge','restricted','extended']},
            unweighted_rates={a:rate_score(rates,a+'_rate',False) for a in ['preseason','translated_ridge','restricted','extended']}))
    intervals = []
    for name,g in scopes:
        if name not in ['all','never_debut','upper_never_debut','lower_never_debut','public']:
            continue
        for arm,benchmark in [('extended','restricted'),('extended','preseason'),('extended','translated_ridge')]:
            for metric in ['pa','value']:
                intervals.append(dict(scope=name,**paired(g,arm,benchmark,metric)))
        if (g['next_pa']>0).any():
            rates = g.with_columns(pl.col('realized_season_rate').alias('next_batting_rate'))
            intervals.append(dict(scope=name,**rate_interval(rates,'extended','restricted')))
    selected = {}
    def choose(f,reason):
        assert len(f), reason
        selected.setdefault(f['row_id'][0],[]).append(reason)
    for pid,y in FIXED:
        choose(q.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y)),'fixed before fit')
    choose(q.filter((pl.col('DSL_0_pa')>0)&(pl.col('age')<=17)).sort('row_id'),'first eligible teenage DSL by row ID')
    error = q.with_columns(((pl.col('restricted_value')-pl.col('next_value'))**2-(pl.col('extended_value')-pl.col('next_value'))**2).alias('gain'),
        (pl.col('extended_value')-pl.col('next_value')).alias('error'))
    for reason,g in [('largest value gain',error.sort('gain',descending=True)),('largest value harm',error.sort('gain')),
        ('largest false high',error.sort('error',descending=True)),('largest false low',error.sort('error')),
        ('ordinary active',error.filter(pl.col('next_pa').is_between(100,600)).sort(pl.col('error').abs()))]:
        choose(g,reason)
    for reason,g in [('largest prospect gain',error.filter(pl.col('prior_debut')==0).sort('gain',descending=True)),
        ('largest prospect harm',error.filter(pl.col('prior_debut')==0).sort('gain'))]:
        choose(g,reason)
    selection = [dict(row_id=rid,reasons=reasons,**q.filter(pl.col('row_id')==rid).select('player_id','player_name','origin_year','outer_fold').row(0,named=True))
                 for rid,reasons in selected.items()]
    q.write_parquet(OUT/'scored-predictions.parquet')
    write('scores.json',scores)
    write('intervals.json',intervals)
    write('selected-cases.json',selection)
    write('verification.json',dict(new_heads_replayed=len(verification),replays=verification,restricted_anchor_differences=restricted_diffs,
        all_prior_columns_exact=True,all_evaluation_rows_retained=True,rate_label='realized target-season average; inactive has no observed rate',
        value_label='unchanged common-origin batting plus replacement',
        player_walkthrough_status='pending',deployment_approved=False,protected_outcomes_used=False,
        hashes={str(OUT/n):sha256_file(OUT/n) for n in ['predictions.parquet','scored-predictions.parquet','scores.json','intervals.json','selected-cases.json','fits.json','preflight.json']}))
    print(json.dumps([s for s in scores if s['scope'] in ['all','never_debut','upper_never_debut','lower_never_debut','public']],indent=2),flush=True)


if __name__=='__main__':
    if sys.argv[1:]==['show']:
        check=read(OUT/'verification.json')
        verify(check['hashes'])
        print(json.dumps([s for s in read(OUT/'scores.json') if s['scope'] in ['all','never_debut','public']],indent=2),flush=True)
    else:
        with threadpool_limits(limits=2):
            main()
