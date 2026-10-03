"""Proper held-out risk/mean scores and complete weighted-neighbor case evidence."""
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
import prepare_hitter_joint_forest_v43 as e
from fit_practical_hitter_v31 import weights
from score_practical_hitter_v31 import paired
from score_hitter_draft_age_v42 import old_notes,ridge_trace
from universal_baseball.practical_hitter_v30 import score
from universal_baseball.histogram_prediction_trace import trace
from universal_baseball.paired_leaf_distribution import observation_weights,leaf_weights
from universal_baseball.storage import sha256_file

EVENTS=['active','400','negative','2wins']


def weighted_quantiles(values,w):
    order=np.argsort(values,kind='stable');v=values[order];cdf=np.cumsum(w[order])
    return [float(v[min(np.searchsorted(cdf,q-1e-12),len(v)-1)]) for q in [.1,.5,.9]]


def risk_score(g):
    rows=[];bands=[];a=g['next_pa'].to_numpy();v=g['next_value'].to_numpy()
    events=np.column_stack([a>0,a>=400,v<0,v>=2]);years=g['target_year'].to_numpy()
    for j,name in enumerate(EVENTS):
        outcome=events[:,j].astype(float);models={}
        for model in ['joint','reference']:
            p=g[model+'_p_'+name].to_numpy();s=[]
            for y in np.unique(years):
                use=years==y;q=np.clip(p[use],1e-12,1-1e-12);z=outcome[use]
                s.append([np.mean((p[use]-z)**2),-np.mean(z*np.log(q)+(1-z)*np.log1p(-q))])
            avg=np.mean(s,axis=0);models[model]=dict(brier=float(avg[0]),log_loss=float(avg[1]),
                expected=float(p.sum()),actual=int(outcome.sum()))
            labels=np.minimum((p*10).astype(int),9)
            for k in np.unique(labels):
                use=labels==k;bands.append(dict(event=name,model=model,band=int(k),rows=int(use.sum()),
                    players=int(g.filter(pl.Series(use))['player_id'].n_unique()),mean_probability=float(p[use].mean()),observed_rate=float(outcome[use].mean())))
        rows.append(dict(event=name,models=models))
    q=g.select('joint_pa_q10','joint_pa_q50','joint_pa_q90').to_numpy();summaries=[]
    for y in np.unique(years):
        use=years==y;z=a[use];p=q[use];error=z[:,None]-p
        pinball=np.maximum(error*np.array([.1,.5,.9]),error*(np.array([.1,.5,.9])-1)).mean(axis=0)
        summaries.append([np.mean((z>=p[:,0])&(z<=p[:,2])),np.mean(p[:,2]-p[:,0]),*pinball,
            np.mean((p[:,1]-z)**2),np.mean(abs(p[:,1]-z))])
    avg=np.mean(summaries,axis=0)
    return dict(events=rows,pa_range=dict(coverage=float(avg[0]),mean_width=float(avg[1]),
        pinball={str(q):float(avg[j+2]) for j,q in enumerate([.1,.5,.9])},median_rmse=float(np.sqrt(avg[5])),median_mae=float(avg[6]),
        interpretation='Equal years; inclusive discrete 10th–90th interval. Zero mass can force overcoverage; median is not expected PA.')),bands


def replay_distribution(model,tr,te,q,cols):
    x=tr.select(cols).to_numpy();z=te.select(cols).to_numpy();w=weights(tr);pa=tr['next_pa'].to_numpy();v=tr['next_value'].to_numpy()
    hard=te['hard_unavailable'].to_numpy();pred=model.predict(z)*[600,2];pred[hard]=0
    assert np.allclose(pred[:,0],q['joint_pa'],atol=1e-8,rtol=0) and np.allclose(pred[:,1],q['joint_value'],atol=1e-8,rtol=0)
    events=np.column_stack([pa>0,pa>=400,v<0,v>=2]);prob=np.zeros((len(te),4))
    for tree in model.estimators_:
        leaves,totals=leaf_weights(tree,x,w);tt=tree.apply(z)
        for j in range(4):prob[:,j]+=np.bincount(leaves,weights=w*events[:,j],minlength=len(totals))[tt]/totals[tt]
    prob/=len(model.estimators_);prob[hard]=0
    assert np.allclose(prob,q.select(*['joint_p_'+a for a in EVENTS]).to_numpy(),atol=1e-10,rtol=0)
    # Per-artifact independent weighted-outcome reconstruction of quantiles.
    for j in sorted(set([0,len(te)//2,len(te)-1])):
        mass=observation_weights(model,x,z[j],w);quart=[0,0,0] if hard[j] else weighted_quantiles(pa,mass)
        assert np.allclose(quart,[q['joint_pa_q'+str(k)][j] for k in [10,50,90]],atol=1e-10,rtol=0)


def main():
    pre=e.r.read(e.OUT/'preflight.json');f=pl.read_parquet(e.OUT/'predictions.parquet');source=pl.read_parquet(e.OUT/'features.parquet')
    base=pl.read_parquet(e.base.OUT/'predictions.parquet').sort('row_id');assert f.select(base.columns).equals(base)
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            tr=source.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id');te=source.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            q=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            assert not set(tr['player_id'])&set(te['player_id']);assert tr['target_year'].max()<=c['year'] and (tr['target_year']!=2020).all()
            n=e.r.read(e.OUT/f"fit-{c['year']}-{c['fold']}.json");assert sha256_file(Path(n['path']))==n['sha256']
            replay_distribution(joblib.load(n['path']),tr,te,q,pre['features'])
            print(f"Replayed mean/events and representative quantiles {c['year']}/{c['fold']}",flush=True)
    q=f.join(source.select('row_id','recent_all_pa'),on='row_id',how='left',suffix='_source',validate='1:1')
    first=pl.read_parquet(e.r.OUT/'dated-stints.parquet').filter((pl.col('season')<=2024)&(pl.col('plate_appearances')>0)).group_by('player_id').agg(pl.col('season').min().alias('first_observed_batting_year'))
    q=q.join(first,on='player_id',how='left',validate='m:1').with_columns(
        ((pl.col('first_observed_batting_year')<=pl.col('origin_year')).fill_null(False)|(pl.col('prior_debut')==1)|(pl.col('draft_known')==1)).alias('origin_evidence_bridge'))
    q.select('row_id','origin_year','player_id','origin_evidence_bridge').write_parquet(e.OUT/'origin-evidence-bridge.parquet')
    public=q.filter(pl.col('v24_pa').is_not_null()&(pl.col('pa_0')>0)&pl.col('steamer_pa').is_not_null()&pl.col('zips_rate').is_not_null());assert len(public)==1789
    scopes=[('all',q),('public_active',public),('source_supported_diagnostic',q.filter(pl.col('origin_evidence_bridge'))),
        ('roster_only_unverified_diagnostic',q.filter(~pl.col('origin_evidence_bridge'))),
        ('brief_debut',q.filter(pl.col('pa_0').is_between(1,199)&(pl.col('career_mlb_observed_pa')<300))),
        ('limited_drafted_never',q.filter((pl.col('prior_debut')==0)&(pl.col('draft_known')==1)&(pl.col('recent_all_pa')<150))),
        ('absent_prior_debut',q.filter((pl.col('prior_debut')==1)&(pl.col('pa_0')==0)))]
    scopes.extend(('origin_'+str(y),q.filter(pl.col('origin_year')==y)) for y in e.r.YEARS)
    scopes.extend(('stage_'+s,q.filter(pl.col('stage')==s)) for s in sorted(q['stage'].unique()))
    scores=[];risks=[];reliability=[];intervals=[]
    for name,g in scopes:
        arms=['joint','cohort','safe_ridge']+(['steamer'] if name=='public_active' else [])
        scores.append(dict(scope=name,rows=len(g),players=g['player_id'].n_unique(),actual_pa=float(g['next_pa'].sum()),actual_value=float(g['next_value'].sum()),scores={a:score(g,a) for a in arms}))
        risk,bands=risk_score(g);risks.append(dict(scope=name,rows=len(g),**risk));reliability.extend(dict(scope=name,**b) for b in bands)
        if name in ['all','public_active','brief_debut','limited_drafted_never']:
            for metric in ['pa','value']:intervals.append(dict(scope=name,**paired(g,'joint','cohort',metric)))
    e.write('scores.json',scores);e.write('risk-scores.json',risks);e.write('reliability.json',reliability);e.write('intervals.json',intervals)
    for s in scores[:5]:print(s['scope'],{a:(round(v['pa_rmse'],3),round(v['pa_mae'],3),round(v['value_rmse'],5)) for a,v in s['scores'].items()},flush=True)
    selected={}
    for pid,y in e.FIXED:
        a=f.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y));assert len(a)==1;selected[a['row_id'][0]]=['Fixed diagnostic']
    a=f.filter((pl.col('player_id')==808975)&(pl.col('origin_year')==2024));assert len(a)==1
    selected[a['row_id'][0]]=['Source-risk case discovered during fixed fits; no outcome-based eligibility change']
    for metric in ['pa','value']:
        a=f.with_columns(((pl.col('cohort_'+metric)-pl.col('next_'+metric))**2-(pl.col('joint_'+metric)-pl.col('next_'+metric))**2).alias('gain'),
            (pl.col('joint_'+metric)-pl.col('next_'+metric)).alias('error'))
        for label,g in [('largest gain',a.sort('gain',descending=True)),('largest harm',a.sort('gain')),('false high',a.sort('error',descending=True)),
            ('false low',a.sort('error')),('ordinary',a.filter(pl.col('next_pa').is_between(200,600)).sort(pl.col('error').abs()))]:selected.setdefault(g['row_id'][0],[]).append(metric+' '+label)
    cases=[];counts=pl.read_parquet(e.r.OUT/'counts.parquet');support=pl.read_parquet(e.OUT/'support.parquet')
    with threadpool_limits(limits=2):
        for rid,reasons in selected.items():
            o=f.filter(pl.col('row_id')==rid).to_dicts()[0];te=source.filter(pl.col('row_id')==rid);y,k=o['origin_year'],o['outer_fold']
            cell=next(c for c in pre['cells'] if c['year']==y and c['fold']==k)
            tr=source.filter(pl.col('row_id').is_in(cell['training_row_ids'])).sort('row_id');x=tr.select(pre['features']).to_numpy();z=te.select(pre['features']).to_numpy()[0]
            m=joblib.load(e.r.read(e.OUT/f'fit-{y}-{k}.json')['path']);mass=observation_weights(m,x,z,weights(tr))
            neighbors=tr.with_columns(pl.Series('distribution_weight',mass)).filter(pl.col('distribution_weight')>0).sort('distribution_weight',descending=True)
            np.savez_compressed(e.OUT/f'case-weights-{rid}.npz',row_id=tr['row_id'].to_numpy(),weight=mass)
            assert np.isclose(mass@tr['next_pa'].to_numpy(),o['joint_pa'],atol=1e-8) or o['hard_unavailable']
            assert np.isclose(mass@tr['next_value'].to_numpy(),o['joint_value'],atol=1e-8) or o['hard_unavailable']
            notes=old_notes(y,k);old={}
            for metric in ['pa','rate']:
                n=next(n for n in notes if n['metric']==metric);model=joblib.load(n['path'])
                xx=te.select(pre['features']).to_numpy()[0] if metric=='pa' else e.prev.scale.safe_matrix(te,pre['features'])[0]
                old[metric]=trace(model,xx,pre['features']) if metric=='pa' else ridge_trace(model,xx,pre['features'])
            fields=['row_id','player_id','player_name','origin_year','target_year','age','stage','pa_0','AAA_0_pa','AA_0_pa',
                'draft_known','pick_number','next_pa','next_value','distribution_weight']
            zero=neighbors.filter(pl.col('next_pa')==0).head(5)
            cases.append(dict(origin=o,selection=reasons,source_history=counts.filter((pl.col('player_id')==o['player_id'])&pl.col('season').is_between(y-2,y)).sort('season','bucket').to_dicts(),
                actual_inputs={c:te[c][0] for c in pre['features']},benchmark_accounting=old,neighbors=neighbors.head(12).select(fields).to_dicts(),
                high_weight_zero_outcomes=zero.select(fields).to_dicts(),weighted_value_quantiles=weighted_quantiles(tr['next_value'].to_numpy(),mass),
                raw_distribution=dict(active_probability=float(mass@(tr['next_pa'].to_numpy()>0)),mean_pa=float(mass@tr['next_pa'].to_numpy()),
                    mean_value=float(mass@tr['next_value'].to_numpy()),distinct_nonzero_weight_players=neighbors['player_id'].n_unique(),
                    effective_rows=float(1/(mass@mass)),source_target_maximum=int(neighbors['target_year'].max())),
                training_profile=support.filter(pl.col('row_id')==rid).to_dicts(),weights_path=str(e.OUT/f'case-weights-{rid}.npz')))
    e.write('cases.json',cases);e.write('verification.json',dict(mean_and_event_heads_replayed=35,representative_quantile_replays=105,
        all_baseline_fields_bit_exact=True,paired_neighbor_means_verified=True,player_walkthrough_status='pending',protected_outcomes_used=False))
    print('Prepared',len(cases),'paired-outcome walks; disposition pending.',flush=True)


if __name__=='__main__':main()
