"""Replay fixed heads, unchanged targets and broad/matched candidate scores."""
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
import prepare_practical_hitter_v31 as r
import prepare_practical_hitter_v33 as s
from score_practical_hitter_v31 import paired,rate_score
from universal_baseball.practical_hitter_v30 import score
from universal_baseball.storage import sha256_file

ARMS=['pooled','pedigree','pooled_product','pedigree_product','safe_ridge']

def main():
    import sys
    repaired='--repaired' in sys.argv
    if repaired:s.OUT=r.ROOT/'reports/generated/practical-hitter-v33b'
    pre=r.read(s.OUT/'preflight.json');f=pl.read_parquet(s.OUT/'predictions.parquet');source=pl.read_parquet(s.OUT/'features.parquet')
    assert len(f)==30506 and f['row_id'].n_unique()==len(f)
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    replays=0
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            te=f.filter((pl.col('origin_year')==c['year'])&(pl.col('outer_fold')==c['fold'])).sort('player_id')
            raw=source.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            training=source.filter(pl.col('row_id').is_in(c['training_row_ids']))
            assert not set(training['player_id']) & set(te['player_id'])
            assert training['target_year'].max()<=c['year'] and (training['target_year']!=2020).all()
            if repaired:assert (training['origin_year']!=2020).all()
            assert te.select('row_id','next_pa','next_value').equals(raw.select('row_id','next_pa','next_value'))
            for n in r.read(s.OUT/f"fits-{c['year']}-{c['fold']}.json")['models']:
                assert sha256_file(Path(n['path']))==n['sha256']
                m=joblib.load(n['path']);x=s.safe_matrix(te,n['features']) if n['arm']=='safe_ridge' else te.select(n['features']).to_numpy()
                pred=m.predict(x)
                if n['metric']=='pa':pred=np.clip(pred,0,800)
                if n['metric']!='rate':
                    pred[te['hard_unavailable'].to_numpy()]=0
                    if n['metric']=='value':pred[te[n['arm']+'_pa'].to_numpy()==0]=0
                assert np.allclose(pred,te[n['arm']+'_'+n['metric']].to_numpy(),atol=1e-10,rtol=0)
                replays+=1
    old=pl.read_parquet(r.OUT/'scored-predictions.parquet')
    refs=['row_id',*[a+'_'+v for a in ['v24','legacy_n','direct_detail','detail_hurdle','base_hurdle','steamer'] for v in ['pa','value']],
        'steamer_rate','zips_rate','v24_rate']
    f=f.join(old.select(refs),on='row_id',validate='1:1')
    assert f.select('row_id','next_pa','next_value').sort('row_id').equals(old.select('row_id','next_pa','next_value').sort('row_id'))
    f=f.with_columns(pl.sum_horizontal([pl.col(f'{b}_{lag}_pa') for b in r.BUCKETS for lag in range(3)]).alias('recent_all_pa'))
    f.write_parquet(s.OUT/'scored-predictions.parquet')
    v24=f.filter(pl.col('v24_pa').is_not_null());n=f.filter(pl.col('legacy_n_pa').is_not_null())
    public=v24.filter((pl.col('pa_0')>0)&pl.col('steamer_pa').is_not_null()&pl.col('zips_rate').is_not_null());assert len(public)==1789
    assert len(v24)==4396 and len(n)==21819
    control='repaired_direct' if repaired else 'direct_detail'
    scopes=[('all',f,[control]),('v24_matched',v24,['v24']),('legacy_n_matched',n,['legacy_n']),
        ('public_active',public,['v24','steamer']),('public_legacy_n',public.filter(pl.col('legacy_n_pa').is_not_null()),['legacy_n','steamer'])]
    scopes.extend(('origin_'+str(y),f.filter(pl.col('origin_year')==y),[control]) for y in r.YEARS)
    scopes.extend(('stage_'+level,f.filter(pl.col('stage')==level),[control]) for level in sorted(f['stage'].unique()))
    for label,condition in [('never_debut',pl.col('prior_debut')==0),('current_regular',pl.col('pa_0')>=400),
        ('current_partial',pl.col('pa_0').is_between(1,399)),('current_absent',pl.col('pa_0')==0),
        ('thin_entry',pl.col('recent_all_pa')<100),('thin_draft', (pl.col('recent_all_pa')<100)&(pl.col('draft_known')==1)),
        ('draft_unmatched',pl.col('draft_known')==0),('dsl_current',pl.col('DSL_0_pa')>0)]:scopes.append((label,f.filter(condition),[control]))
    scores=[];intervals=[]
    for label,g,benchmarks in scopes:
        if not len(g):continue
        scores.append(dict(scope=label,rows=len(g),players=g['player_id'].n_unique(),actual_pa=float(g['next_pa'].sum()),actual_value=float(g['next_value'].sum()),
            scores={a:score(g,a) for a in ARMS+benchmarks},rate_scores={a:rate_score(g,a+'_rate') for a in ['pooled','pedigree','safe_ridge']+(['steamer','zips','v24'] if label.startswith('public_') else [])}))
        if label in ['all','v24_matched','legacy_n_matched','public_active','public_legacy_n']:
            benchmark=benchmarks[0]
            for arm in ARMS:
                for metric in ['pa','value']:intervals.append(dict(scope=label,**paired(g,arm,benchmark,metric)))
            if label=='all':
                for metric in ['pa','value']:intervals.append(dict(scope=label,**paired(g,'pedigree','pooled',metric)))
    s.write('scores.json',scores);s.write('intervals.json',intervals)
    s.write('verification.json',dict(saved_heads_replayed=replays,all_targets_and_membership_unchanged=True,
        source_hashes_unchanged=True,original_public_nonreturns_preserved=True,
        rate_ranges={a:[float(f[a+'_rate'].min()),float(f[a+'_rate'].max())] for a in ['pooled','pedigree','safe_ridge']},
        player_walkthrough_status='pending',predictive_certification=False,origin_2020_excluded=repaired))
    for g in scores[:5]:print(g['scope'],g['rows'],{a:(round(v['pa_rmse'],3),round(v['value_rmse'],5)) for a,v in g['scores'].items()})

if __name__=='__main__':main()
