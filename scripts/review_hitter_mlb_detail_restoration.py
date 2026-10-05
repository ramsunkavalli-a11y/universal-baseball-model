"""Replay four-input restoration, score unchanged forecasts, explain actual cases."""
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

from universal_baseball.hitter_count_baseline import past_profile, assemble
from universal_baseball.hitter_mlb_detail import DETAIL, reconstruct
from universal_baseball.hitter_compatible_value import labels, UNIT
from universal_baseball.mlb_event_logit import VALUES
from universal_baseball.storage import sha256_file
from prepare_hitter_overseas_integration import annual_labels
from review_hitter_evidence_representation import rate_interval
from review_hitter_past_direct_value import summary, value_interval
from run_hitter_count_baseline import ROOT, GEN, OUT as COUNT, SHARED, FEATURES, REF, read, verify, matrix, source_data
from run_hitter_past_direct_value import OUT as DIRECT, past_rate
from run_hitter_mlb_detail_restoration import OUT, save
from supplement_hitter_overseas_scores import rate_score


def main():
    assert not (OUT/'review-receipt.json').exists()
    pre=read(OUT/'preflight.json'); verify(pre['source_hashes']); verify(read(OUT/'source-review.json')['hashes'])
    fit=read(OUT/'fit-report.json'); assert fit['predictions_sha256']==sha256_file(OUT/'predictions.parquet')
    q=pl.read_parquet(OUT/'predictions.parquet').sort('row_id'); previous=pl.read_parquet(DIRECT/'predictions.parquet').sort('row_id')
    assert q.select(previous.columns).equals(previous) and q['restored_pa'].equals(q['scalar_pa'])
    actual,env=annual_labels(pl.read_parquet(GEN/'practical-hitter-v31/dated-stints.parquet'))
    raw=np.array([actual.get((r['target_year'],r['player_id']),np.zeros(8)) for r in q.iter_rows(named=True)])
    lab=labels(raw,np.array([env[y] for y in q['origin_year']]),np.array([env[y] for y in q['target_year']]),q['origin_replacement_rate'].to_numpy())
    assert np.allclose(lab['relative_rate'],q['actual_relative_rate'],atol=1e-10) and np.allclose(lab['relative_value'],q['actual_relative_value'],atol=1e-10)
    q=q.with_columns(pl.Series('actual_common_rate',lab['common_rate']))
    frames={k:pl.read_parquet(COUNT/f'features-{k}.parquet') for k in range(5)}; models={}; replays=0; physical=[]
    with threadpool_limits(limits=2):
        for c in fit['cells']:
            y,k=c['origin'],c['fold']; verify(c['hashes']); g=q.filter((pl.col('origin_year')==y)&(pl.col('outer_fold')==k)).sort('row_id')
            f=frames[k].filter(pl.col('row_id').is_in(g['row_id'].to_list())).sort('row_id'); assert f['row_id'].equals(g['row_id']); b=past_rate(f); ps={}
            for h in c['heads']:
                m=joblib.load(h['path']); models[y,k,h['arm']]=(m,h['features']); ps[h['arm']]=b+m.predict(matrix(f,h['features']));replays+=1
            rate=np.where(f['prior_debut'].to_numpy()==0,ps['prospect'],np.where(f['sc_tracked'].to_numpy(),ps['tracking'],ps['base']))
            assert np.allclose(rate,g['restored_rate'],atol=1e-10) and np.allclose(b,g['scalar_baseline_rate'],atol=1e-10)
            assert np.allclose(g['restored_value'],g['restored_pa']*(g['restored_rate']/600+g['origin_replacement_rate']),atol=1e-10)
            origin_index=f.select(REF).to_numpy()@VALUES
            bad=(rate<(VALUES.min()-origin_index)*UNIT)|(rate>(VALUES.max()-origin_index)*UNIT); physical += g.filter(pl.Series(bad))['row_id'].to_list()
    assert replays==105
    diagnostics=pl.read_parquet(GEN/'hitter-count-error-diagnosis/diagnostic-rows.parquet').select('row_id','recent_observed_MLB_mass','overseas_source')
    public=pl.read_parquet(GEN/'hitter-minor-statcast-precision/scored-predictions.parquet').select('row_id','steamer_rate','steamer_index','common_zips_rate','zips_index')
    q=q.join(diagnostics,on='row_id',validate='1:1').join(public,on='row_id',how='left',validate='1:1')
    original=q.filter(~pl.col('source_addition')); added=q.filter(pl.col('source_addition')); pub=original.filter((pl.col('pa_0')>0)&pl.col('steamer_index').is_not_null()&pl.col('zips_index').is_not_null())
    assert original.height==30506 and added.height==13 and pub.height==2627
    scopes=[('all',original),('public',pub),('current_MLB',original.filter(pl.col('pa_0')>0)),
        ('upper_never_debut',original.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Upper minors'))),('lower_never_debut',original.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Lower minors'))),
        ('no_arrival',original.filter(pl.col('next_pa')==0)),('recent_MLB_600plus',original.filter(pl.col('recent_observed_MLB_mass')>=600)),('foreign',original.filter(pl.col('overseas_source')!='none')),('additions',added)]
    scopes += [(f'origin_{y}',original.filter(pl.col('origin_year')==y)) for y in sorted(original['origin_year'].unique())]
    scores=[]; triggers=[]
    for name,g in scopes:
        arms=['scalar','count','restored'] if name=='additions' else ['current','scalar','count','restored']
        scores.append(dict(scope=name,rows=g.height,players=g['player_id'].n_unique(),active_rows=int((g['next_pa']>0).sum()),actual_PA=int(g['next_pa'].sum()),actual_value=float(g['actual_relative_value'].sum()),scores={a:summary(g,a) for a in arms}))
        for baseline in ['scalar']+([] if name=='additions' else ['current']):
            for metric in ['rate_rmse','value_rmse']:
                a,b=scores[-1]['scores']['restored'][metric],scores[-1]['scores'][baseline][metric]
                if a is not None and b is not None and a>1.05*b:triggers.append(dict(scope=name,baseline=baseline,metric=metric,relative_worsening=a/b-1))
    # Scoring wrapper replaces only a temporary scalar-value column for generic interval arithmetic.
    interval_frame=original.with_columns(pl.col('restored_value').alias('scalar_value'))
    save('scores.json',dict(scopes=scores,intervals={a:dict(rate=rate_interval(original,'restored',a),value=value_interval(interval_frame,a)) for a in ['current','count']},
        matched_direct_interval=dict(rate=rate_interval(original,'restored','scalar'),value=value_interval(original.with_columns(pl.col('scalar_value').alias('direct_anchor_value'),pl.col('restored_value').alias('scalar_value')),'direct_anchor')),
        public_common_rate=dict(rows=pub.height,active_rows=int((pub['next_pa']>0).sum()),scores={a:rate_score(pub.filter(pl.col('next_pa')>0),col,'actual_common_rate',True) for a,col in [('current','current_rate'),('scalar','scalar_rate'),('count','count_rate'),('restored','restored_rate'),('steamer','steamer_rate'),('zips','common_zips_rate')]},qualification='Unchanged public origin-centered reference; vintage/park/environment differences remain; no certified ZiPS workload comparison.'),
        physical_envelope_violations=physical,review_triggers=triggers,player_walkthrough_status='pending'))
    allscore=scores[0]['scores']; checks=0
    for arm in ['current','scalar','count','restored']:
        mse=[]; rates=[]
        for y in sorted(original['origin_year'].unique()):
            g=original.filter(pl.col('origin_year')==y);e=(g[arm+'_value']-g['actual_relative_value']).to_numpy();mse.append(np.mean(e*e))
            g=g.filter(pl.col('next_pa')>0);e=(g[arm+'_rate']-g['actual_relative_rate']).to_numpy();pa=g['next_pa'].to_numpy();rates.append(np.sum(pa*e*e)/pa.sum())
        assert np.isclose(np.sqrt(np.mean(mse)),allscore[arm]['value_rmse'],atol=1e-12) and np.isclose(np.sqrt(np.mean(rates)),allscore[arm]['rate_rmse'],atol=1e-12);checks+=2
    chosen={rid:['fixed before fitting'] for rid in pre['fixed_case_row_ids']}
    ranked=original.with_columns(((pl.col('restored_value')-pl.col('actual_relative_value'))**2-(pl.col('current_value')-pl.col('actual_relative_value'))**2).alias('change'),(pl.col('restored_value')-pl.col('actual_relative_value')).alias('error'))
    for rows,why in [(ranked.sort('change'),'largest gain'),(ranked.sort('change',descending=True),'largest harm'),(ranked.sort('error'),'false low'),(ranked.sort('error',descending=True),'false high'),(ranked.filter(pl.col('next_pa').is_between(200,399)).sort(pl.col('error').abs()),'ordinary')]:chosen.setdefault(int(rows['row_id'][0]),[]).append(why)
    _,history,sources,foreign=source_data(); support=pl.read_parquet(OUT/'profile-support.parquet'); ranges=read(OUT/'feature-ranges.json'); cases=[]
    oldpre=read(DIRECT/'preflight.json');oldwalks={r['row_id']:r for r in read(DIRECT/'player-walks.json')['cases']}
    with threadpool_limits(limits=2):
        for rid,why in chosen.items():
            o=q.filter(pl.col('row_id')==rid).row(0,named=True);y,k,pid=o['origin_year'],o['outer_fold'],o['player_id'];f=frames[k];one=f.filter(pl.col('row_id')==rid);a=one.row(0,named=True)
            graph=read(SHARED/f'graphs-{k}.json')[f'{y}:{k}'];key=f'{y}:{pid}';v,note=past_profile(history[pid],graph,sources.get(key),foreign.get((key,k)),origin=y,outer_fold=k,own_fold=k)
            assert all(np.isclose(v[n],a[n],atol=1e-12) for n in v)
            detail,mlbsource=reconstruct(pid,y,actual,env); assert all(np.isclose(detail[n],a[n],atol=1e-10) for n in DETAIL)
            arm=o['count_branch'];m,names=models[y,k,arm];x=matrix(one,names)[0];effects=x*m.coef_;b=float(past_rate(one)[0]);residual=float(m.intercept_+effects.sum());assert np.isclose(b+residual,o['restored_rate'],atol=1e-10)
            oldmodel=joblib.load(DIRECT/f'{arm}-rate-{y}-{k}.joblib');oldnames=oldpre['arms'][arm];assert names==oldnames+DETAIL
            added_effect=float(effects[-4:].sum());other_change=float(m.intercept_-oldmodel.intercept_+x[:-4]@(m.coef_[:-4]-oldmodel.coef_))
            assert np.isclose(added_effect+other_change,o['restored_rate']-o['scalar_rate'],atol=1e-10)
            probes={}
            for family in ['minor','foreign']:
                vv,pp=assemble(note['contributions'],note['reference'],note['observed_precision_PA'],remove=family)
                changed=one.with_columns(*[pl.lit(value).alias(n) for n,value in vv.items()]); assert changed.select(DETAIL).equals(one.select(DETAIL))
                rr=float(past_rate(changed)[0]+m.predict(matrix(changed,names))[0]);probes[family]=dict(rate=rr,change=rr-o['restored_rate'],MLB_summaries_unchanged=True,artificial_not_causal=True)
            changed=one.with_columns(*[pl.lit(0.).alias(n) for n in DETAIL]);rr=float(b+m.predict(matrix(changed,names))[0]);probes['zero_four_MLB_summaries']=dict(rate=rr,change=rr-o['restored_rate'],common_MLB_production_retained=True,artificial_not_causal=True)
            if rid in oldwalks:peers=oldwalks[rid]['origin_production_selected_comparisons']
            else:
                cell=next(c for c in pre['cells'] if c['year']==y and c['fold']==k); pool=f.filter(pl.col('row_id').is_in(cell['training_row_ids'])&(pl.col('prior_debut')==a['prior_debut'])&(pl.col('stage')==a['stage']))
                if a['count_NPB_share']+a['count_KBO_share']>0:pool=pool.filter(((pl.col('count_NPB_share')>0)==(a['count_NPB_share']>0))&((pl.col('count_KBO_share')>0)==(a['count_KBO_share']>0)))
                dist=pl.sum_horizontal([(pl.col(n)-a[n])**2 for n in FEATURES[:8]]).sqrt()+(pl.col('age')-a['age']).abs()/5+(pl.col('pa_0')-a['pa_0']).abs()/600+(pl.col('draft_rank')-a['draft_rank']).abs()+(pl.col('scout_rank_score_0')-a['scout_rank_score_0']).abs()
                pool=pool.with_columns(dist.alias('origin_production_distance')).sort('origin_production_distance','player_id','origin_year').unique('player_id',maintain_order=True).head(3)
                peers=pool.select('row_id','player_id','player_name','origin_year','age','pa_0','minor_pa_0','next_pa','actual_relative_rate','origin_production_distance',*FEATURES).to_dicts()
            cases.append(dict(row_id=rid,why=why,forecast=o,information_date=a['ctx_information_date'],age=a['age'],source=note,raw_history=[r for r in history[pid] if y-2<=r['season']<=y],MLB_source=mlbsource,
                past_baseline_rate=b,fitted_intercept=float(m.intercept_),fitted_residual=residual,added_MLB_term_effect=added_effect,other_coefficient_change=other_change,
                feature_terms=[dict(feature=n,input=float(xx),coefficient=float(cc),effect=float(ee)) for n,xx,cc,ee in zip(names,x,m.coef_,effects,strict=True)],
                actual_counts=actual.get((o['target_year'],pid),np.zeros(8)).tolist(),probes=probes,
                joint_MLB_quality_support=support.filter(pl.col('row_id')==rid).to_dicts(),added_feature_extrapolations=[r for r in ranges if r['origin']==y and r['fold']==k and r['arm']==arm and rid in r['row_ids']],origin_production_selected_comparisons=peers))
    save('player-walks.json',dict(cases=cases,fixed_cases_retained=16,walkthrough_status='pending_readable_review'))
    paths=[Path(__file__),OUT/'preflight.json',OUT/'source-review.json',OUT/'fit-report.json',OUT/'predictions.parquet',OUT/'scores.json',OUT/'player-walks.json',DIRECT/'player-walks.json',GEN/'hitter-minor-statcast-precision/scored-predictions.parquet']
    save('review-receipt.json',dict(heads_replayed=replays,independent_headline_equations=checks,original_columns_preserved=True,PA_exactly_fixed=True,labels_independently_reconstructed=True,
         cases=len(cases),player_walkthrough_status='pending_readable_review',protected_outcomes_used=False,deployment_approved=False,hashes={str(p):sha256_file(p) for p in paths}))
    print(str(allscore)); print(f'Replayed 105 candidate heads; {len(cases)} actual source/model walks await readable review.',flush=True)


if __name__=='__main__':main()
